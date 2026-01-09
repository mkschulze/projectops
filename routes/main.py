"""
Main Routes Blueprint

Handles:
- Index/Home page
- Dashboard
- Calendar views (month, year, week)
- Profile and notifications
- Language switching
- Calendar subscription (iCal)
"""

from datetime import date, timedelta
import calendar
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, make_response, g
from flask_login import login_required, current_user

from extensions import db
from models import User, Task, Notification
from services import CalendarService
from modules import ModuleRegistry
from middleware.tenant import scope_query_to_tenant

main_bp = Blueprint('main', __name__)


# ============================================================================
# HOME ROUTES
# ============================================================================

@main_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Advanced Analytics Dashboard with project insights"""
    from modules.projects.models import Project, ProjectMember, Issue, Sprint
    
    # Get user's tasks based on role and entity permissions (exclude archived)
    # Always scope to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    
    if current_user.is_admin() or current_user.is_manager():
        # Admins and managers see all tasks in tenant
        base_query = Task.query.filter(tenant_filter, (Task.is_archived == False) | (Task.is_archived == None))
    else:
        # Get accessible entity IDs for this user
        accessible_entity_ids = current_user.get_accessible_entity_ids('view')
        
        # Others see their tasks + tasks for accessible entities
        if accessible_entity_ids:
            base_query = Task.query.filter(
                tenant_filter,
                ((Task.is_archived == False) | (Task.is_archived == None)),
                (Task.owner_id == current_user.id) | 
                (Task.reviewer_id == current_user.id) |
                (Task.entity_id.in_(accessible_entity_ids))
            )
        else:
            base_query = Task.query.filter(
                tenant_filter,
                ((Task.is_archived == False) | (Task.is_archived == None)),
                (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
            )
    
    today = date.today()
    soon = today + timedelta(days=7)
    
    # Task statistics
    stats = {
        'total': base_query.count(),
        'overdue': base_query.filter(Task.due_date < today, Task.status != 'completed').count(),
        'due_soon': base_query.filter(Task.due_date >= today, Task.due_date <= soon, Task.status != 'completed').count(),
        'in_review': base_query.filter_by(status='in_review').count(),
        'completed': base_query.filter_by(status='completed').count(),
    }
    
    # Calculate completion rate
    if stats['total'] > 0:
        stats['completion_rate'] = round((stats['completed'] / stats['total']) * 100, 1)
    else:
        stats['completion_rate'] = 0
    
    # My upcoming tasks
    my_tasks = base_query.filter(
        Task.status != 'completed'
    ).order_by(Task.due_date).limit(10).all()
    
    # Overdue tasks
    overdue_tasks = base_query.filter(
        Task.due_date < today,
        Task.status != 'completed'
    ).order_by(Task.due_date).limit(5).all()
    
    # ==================== PROJECT DATA ====================
    # Get projects where user is a member
    if current_user.is_admin():
        user_projects = Project.query.filter_by(is_archived=False).order_by(Project.updated_at.desc()).limit(6).all()
    else:
        user_project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).subquery()
        user_projects = Project.query.filter(
            Project.id.in_(user_project_ids),
            Project.is_archived == False
        ).order_by(Project.updated_at.desc()).limit(6).all()
    
    # Build project insights
    project_insights = []
    for project in user_projects:
        # Get issue counts
        total_issues = Issue.query.filter_by(project_id=project.id, is_archived=False).count()
        open_issues = Issue.query.join(project.issue_statuses[0].__class__).filter(
            Issue.project_id == project.id,
            Issue.is_archived == False,
            Issue.status.has(is_final=False)
        ).count() if project.issue_statuses else 0
        my_issues = Issue.query.filter_by(project_id=project.id, assignee_id=current_user.id, is_archived=False).count()
        
        # Get active sprint if scrum
        active_sprint = None
        if project.methodology == 'scrum':
            active_sprint = Sprint.query.filter_by(project_id=project.id, state='active').first()
        
        project_insights.append({
            'project': project,
            'total_issues': total_issues,
            'open_issues': open_issues,
            'my_issues': my_issues,
            'active_sprint': active_sprint,
            'completion_rate': round(((total_issues - open_issues) / total_issues * 100) if total_issues > 0 else 0, 1)
        })
    
    # Get recent issues assigned to user
    my_recent_issues = Issue.query.filter_by(
        assignee_id=current_user.id,
        is_archived=False
    ).order_by(Issue.updated_at.desc()).limit(5).all()
    
    # Calculate productivity trends (last 7 days)
    week_ago = today - timedelta(days=7)
    tasks_completed_this_week = base_query.filter(
        Task.status == 'completed',
        Task.updated_at >= week_ago
    ).count()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         my_tasks=my_tasks, 
                         overdue_tasks=overdue_tasks,
                         project_insights=project_insights,
                         my_recent_issues=my_recent_issues,
                         tasks_completed_this_week=tasks_completed_this_week,
                         today=today)


# ============================================================================
# LANGUAGE
# ============================================================================

@main_bp.route('/set-language/<lang>')
def set_language(lang):
    """Change language"""
    if lang in current_app.config.get('SUPPORTED_LANGUAGES', ['de', 'en']):
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))


# ============================================================================
# CALENDAR VIEWS
# ============================================================================

@main_bp.route('/calendar')
@login_required
def calendar_view():
    """Calendar month view of tasks"""
    # Get year and month from query params, default to current
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    
    # Validate month/year
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # Get first and last day of month
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    # Build calendar structure
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(year, month)
    
    # Get tasks for this month (exclude archived, scope to tenant)
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(
        tenant_filter,
        Task.due_date >= first_day,
        Task.due_date <= last_day,
        (Task.is_archived == False) | (Task.is_archived == None)
    )
    
    # Apply role-based filtering
    if not (current_user.is_admin() or current_user.is_manager()):
        query = query.filter(
            (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
        )
    
    tasks = query.order_by(Task.due_date).all()
    
    # Group tasks by day
    tasks_by_day = {}
    for task in tasks:
        day = task.due_date.day
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)
    
    # Calculate prev/next month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    return render_template('calendar.html',
                         year=year,
                         month=month,
                         month_name=calendar.month_name[month],
                         month_days=month_days,
                         tasks_by_day=tasks_by_day,
                         today=date.today(),
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year)


@main_bp.route('/calendar/year')
@login_required
def calendar_year_view():
    """Calendar year view of tasks"""
    year = request.args.get('year', type=int, default=date.today().year)
    
    # Get all tasks for the year (exclude archived, scope to tenant)
    first_day = date(year, 1, 1)
    last_day = date(year, 12, 31)
    
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(
        tenant_filter,
        Task.due_date >= first_day,
        Task.due_date <= last_day,
        (Task.is_archived == False) | (Task.is_archived == None)
    )
    
    if not (current_user.is_admin() or current_user.is_manager()):
        query = query.filter(
            (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
        )
    
    tasks = query.order_by(Task.due_date).all()
    
    # Group tasks by month
    tasks_by_month = {m: [] for m in range(1, 13)}
    for task in tasks:
        tasks_by_month[task.due_date.month].append(task)
    
    # Count by status per month
    month_stats = {}
    for m in range(1, 13):
        month_tasks = tasks_by_month[m]
        month_stats[m] = {
            'total': len(month_tasks),
            'completed': sum(1 for t in month_tasks if t.status == 'completed'),
            'overdue': sum(1 for t in month_tasks if t.is_overdue),
            'in_review': sum(1 for t in month_tasks if t.status == 'in_review'),
        }
    
    # German month names
    month_names = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 
                   'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    
    return render_template('calendar_year.html',
                         year=year,
                         month_names=month_names,
                         tasks_by_month=tasks_by_month,
                         month_stats=month_stats,
                         today=date.today())


@main_bp.route('/calendar/week')
@login_required
def calendar_week_view():
    """Calendar week view of tasks"""
    today = date.today()
    year = request.args.get('year', type=int, default=today.year)
    week = request.args.get('week', type=int, default=today.isocalendar()[1])
    
    # Validate week number
    if week < 1:
        week = 52
        year -= 1
    elif week > 52:
        week = 1
        year += 1
    
    # Get first day of the week (Monday)
    # ISO week: week 1 is the week containing Jan 4th
    jan4 = date(year, 1, 4)
    week_start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=week - 1)
    week_end = week_start + timedelta(days=6)
    
    # Get tasks for this week (exclude archived, scope to tenant)
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(
        tenant_filter,
        Task.due_date >= week_start,
        Task.due_date <= week_end,
        (Task.is_archived == False) | (Task.is_archived == None)
    )
    
    if not (current_user.is_admin() or current_user.is_manager()):
        query = query.filter(
            (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
        )
    
    tasks = query.order_by(Task.due_date, Task.id).all()
    
    # Build days of the week
    week_days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_tasks = [t for t in tasks if t.due_date == day_date]
        week_days.append({
            'date': day_date,
            'weekday': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][i],
            'weekday_short': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][i],
            'tasks': day_tasks,
            'is_today': day_date == today,
            'is_weekend': i >= 5
        })
    
    # Prev/next week
    prev_week = week - 1 if week > 1 else 52
    prev_year = year if week > 1 else year - 1
    next_week = week + 1 if week < 52 else 1
    next_year = year if week < 52 else year + 1
    
    return render_template('calendar_week.html',
                         year=year,
                         week=week,
                         week_start=week_start,
                         week_end=week_end,
                         week_days=week_days,
                         today=today,
                         prev_week=prev_week,
                         prev_year=prev_year,
                         next_week=next_week,
                         next_year=next_year)


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@main_bp.route('/notifications')
@login_required
def notifications():
    """View all notifications"""
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if session.get('lang', 'de') == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('notifications.html', notifications=notifications)


@main_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return {'success': False, 'message': 'Unauthorized'}, 403
    
    notification.is_read = True
    db.session.commit()
    
    return {'success': True}


@main_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    
    return {'success': True}


# ============================================================================
# PROFILE
# ============================================================================

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)


@main_bp.route('/profile/notifications')
@login_required
def profile_notifications():
    """User notification preferences"""
    return render_template('profile_notifications.html', user=current_user)


@main_bp.route('/profile/notifications', methods=['POST'])
@login_required
def update_notification_preferences():
    """Update notification preferences"""
    current_user.email_task_assigned = 'email_task_assigned' in request.form
    current_user.email_task_due_soon = 'email_task_due_soon' in request.form
    current_user.email_task_overdue = 'email_task_overdue' in request.form
    current_user.email_task_comment = 'email_task_comment' in request.form
    current_user.email_review_requested = 'email_review_requested' in request.form
    current_user.email_task_approved = 'email_task_approved' in request.form
    current_user.email_task_rejected = 'email_task_rejected' in request.form
    
    db.session.commit()
    flash('Benachrichtigungseinstellungen gespeichert.', 'success')
    return redirect(url_for('main.profile_notifications'))


# ============================================================================
# CALENDAR SUBSCRIPTION (iCal)
# ============================================================================

@main_bp.route('/calendar/subscription')
@login_required
def calendar_subscription():
    """Show calendar subscription page with iCal URL"""
    # Generate token if not exists
    if not current_user.calendar_token:
        current_user.calendar_token = CalendarService.generate_user_token(current_user.id)
        db.session.commit()
    
    return render_template('calendar_subscription.html', user=current_user)


@main_bp.route('/calendar/regenerate-token', methods=['POST'])
@login_required
def regenerate_calendar_token():
    """Regenerate calendar subscription token"""
    current_user.calendar_token = CalendarService.generate_user_token(current_user.id)
    db.session.commit()
    flash('Kalender-Token wurde neu generiert.', 'success')
    return redirect(url_for('main.calendar_subscription'))


@main_bp.route('/calendar/ical/<token>.ics')
def calendar_ical_feed(token):
    """Public iCal feed endpoint (no login required, uses token)"""
    user = User.query.filter_by(calendar_token=token).first()
    
    if not user:
        return 'Invalid token', 404
    
    # Get user's default tenant for scoping
    user_tenant_id = user.current_tenant_id or (user.default_tenant.id if user.default_tenant else None)
    
    # Get user's tasks (scoped to their tenant)
    base_filter = (
        (Task.tenant_id == user_tenant_id) if user_tenant_id else False,
        (Task.is_archived == False) | (Task.is_archived == None)
    )
    
    if user.is_admin() or user.is_manager():
        tasks = Task.query.filter(*base_filter).all()
    else:
        tasks = Task.query.filter(
            *base_filter,
            (Task.owner_id == user.id) | (Task.reviewer_id == user.id)
        ).all()
    
    lang = session.get('lang', 'de')
    ical_data = CalendarService.generate_ical_feed(tasks, lang=lang, user_name=user.name)
    
    response = make_response(ical_data)
    response.headers['Content-Type'] = 'text/calendar; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="projectops-calendar.ics"'
    return response
