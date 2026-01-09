"""
API Routes Blueprint

Handles JSON API endpoints:
- Dashboard chart data
- Task bulk operations
- Preset management API
- Approval status API

Note: This blueprint contains core API functionality.
Additional API routes remain in app.py for gradual migration.
"""

from datetime import date, timedelta
from flask import Blueprint, jsonify, request, session, g
from flask_login import login_required, current_user

from extensions import db
from models import Task, TaskPreset, TaskReviewer, TaskEvidence, Comment, Notification, AuditLog
from modules.projects.models import Project
from middleware.tenant import (
    get_task_or_404_scoped, get_task_scoped, get_project_or_404_scoped
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


def log_action(action, entity_type, entity_id, entity_name, old_value=None, new_value=None):
    """Helper to log actions to audit log"""
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name[:200] if entity_name else None,
        old_value=str(old_value)[:500] if old_value else None,
        new_value=str(new_value)[:500] if new_value else None
    )
    db.session.add(log)
    db.session.commit()


# ============================================================================
# TASK BULK OPERATIONS
# ============================================================================

@api_bp.route('/tasks/bulk-archive', methods=['POST'])
@login_required
def bulk_archive():
    """Bulk archive multiple tasks"""
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    reason = data.get('reason', '')
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        tasks_to_process.append(task)
    
    archived_count = 0
    for task in tasks_to_process:
        if not task.is_archived:
            task.archive(current_user, reason)
            log_action('ARCHIVE', 'Task', task.id, task.title, 'active', 'archived')
            archived_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'archived_count': archived_count,
        'message': f'{archived_count} Aufgabe(n) archiviert.' if lang == 'de' else f'{archived_count} task(s) archived.'
    })


@api_bp.route('/tasks/bulk-restore', methods=['POST'])
@login_required
def bulk_restore():
    """Bulk restore multiple tasks from archive"""
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        tasks_to_process.append(task)
    
    restored_count = 0
    for task in tasks_to_process:
        if task.is_archived:
            task.restore()
            log_action('RESTORE', 'Task', task.id, task.title, 'archived', 'active')
            restored_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'restored_count': restored_count,
        'message': f'{restored_count} Aufgabe(n) wiederhergestellt.' if lang == 'de' else f'{restored_count} task(s) restored.'
    })


@api_bp.route('/tasks/archive/bulk-delete', methods=['POST'])
@login_required
def bulk_permanent_delete():
    """Bulk permanently delete multiple archived tasks (admin only)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Permission denied - admin only'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        if not task.is_archived:
            return jsonify({'success': False, 'error': f'Task {task_id} is not archived'}), 400
        tasks_to_process.append(task)
    
    deleted_count = 0
    for task in tasks_to_process:
        task_title = task.title
        task_id = task.id
        
        # Delete related records first
        TaskEvidence.query.filter_by(task_id=task_id).delete()
        Comment.query.filter_by(task_id=task_id).delete()
        TaskReviewer.query.filter_by(task_id=task_id).delete()
        Notification.query.filter(Notification.entity_type == 'task', Notification.entity_id == task_id).delete()
        
        db.session.delete(task)
        log_action('DELETE', 'Task', task_id, task_title, 'archived', 'deleted')
        deleted_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'message': f'{deleted_count} Aufgabe(n) endgültig gelöscht.' if lang == 'de' else f'{deleted_count} task(s) permanently deleted.'
    })


@api_bp.route('/tasks/bulk-status', methods=['POST'])
@login_required
def bulk_status():
    """Bulk change status for multiple tasks"""
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    new_status = data.get('status', '')
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    if not new_status:
        return jsonify({'success': False, 'error': 'No status specified'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        tasks_to_process.append(task)
    
    updated_count = 0
    for task in tasks_to_process:
        if task.status != new_status:
            old_status = task.status
            task.status = new_status
            log_action('STATUS_CHANGE', 'Task', task.id, task.title, old_status, new_status)
            updated_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'message': f'{updated_count} Aufgabe(n) aktualisiert.' if lang == 'de' else f'{updated_count} task(s) updated.'
    })


@api_bp.route('/tasks/bulk-assign-owner', methods=['POST'])
@login_required
def bulk_assign_owner():
    """Bulk assign owner to multiple tasks"""
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    owner_id = data.get('owner_id')
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        tasks_to_process.append(task)
    
    updated_count = 0
    for task in tasks_to_process:
        old_owner = task.owner_id
        task.owner_id = owner_id
        log_action('ASSIGN', 'Task', task.id, task.title, f'owner_id={old_owner}', f'owner_id={owner_id}')
        updated_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'message': f'{updated_count} Aufgabe(n) zugewiesen.' if lang == 'de' else f'{updated_count} task(s) assigned.'
    })


@api_bp.route('/tasks/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Bulk delete multiple tasks"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Permission denied - admin only'}), 403
    
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'error': 'No tasks selected'}), 400
    
    # Verify all task IDs belong to current tenant before processing
    tasks_to_process = []
    for task_id in task_ids:
        task = get_task_scoped(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'Task {task_id} not found or access denied'}), 403
        tasks_to_process.append(task)
    
    deleted_count = 0
    for task in tasks_to_process:
        task_title = task.title
        task_id = task.id
        
        # Delete related records first
        TaskEvidence.query.filter_by(task_id=task_id).delete()
        Comment.query.filter_by(task_id=task_id).delete()
        TaskReviewer.query.filter_by(task_id=task_id).delete()
        Notification.query.filter(Notification.entity_type == 'task', Notification.entity_id == task_id).delete()
        
        db.session.delete(task)
        log_action('DELETE', 'Task', task_id, task_title, '', 'deleted')
        deleted_count += 1
    
    db.session.commit()
    
    lang = session.get('lang', 'de')
    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'message': f'{deleted_count} Aufgabe(n) gelöscht.' if lang == 'de' else f'{deleted_count} task(s) deleted.'
    })


# ============================================================================
# TASK APPROVAL STATUS
# ============================================================================

@api_bp.route('/tasks/<int:task_id>/approval-status')
@login_required
def task_approval_status(task_id):
    """Get approval status for a task"""
    task = get_task_or_404_scoped(task_id)
    
    reviewers = []
    for tr in task.reviewers:
        reviewers.append({
            'user_id': tr.user_id,
            'name': tr.user.name if tr.user else 'Unknown',
            'decision': tr.decision,
            'decided_at': tr.decided_at.isoformat() if tr.decided_at else None,
            'note': tr.note
        })
    
    return jsonify({
        'task_id': task.id,
        'status': task.status,
        'reviewers': reviewers,
        'all_approved': all(tr.decision == 'approved' for tr in task.reviewers),
        'any_rejected': any(tr.decision == 'rejected' for tr in task.reviewers)
    })


@api_bp.route('/tasks/<int:task_id>/workflow-timeline')
@login_required
def task_workflow_timeline(task_id):
    """Get workflow timeline for a task"""
    task = get_task_or_404_scoped(task_id)
    
    # Get audit logs for this task
    logs = AuditLog.query.filter_by(
        entity_type='Task',
        entity_id=task_id
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()
    
    timeline = []
    for log in logs:
        timeline.append({
            'action': log.action,
            'user_name': log.user.name if log.user else 'System',
            'timestamp': log.timestamp.isoformat(),
            'old_value': log.old_value,
            'new_value': log.new_value
        })
    
    return jsonify({
        'task_id': task.id,
        'timeline': timeline
    })


# ============================================================================
# DASHBOARD CHART DATA
# ============================================================================

@api_bp.route('/dashboard/status-chart')
@login_required
def dashboard_status_chart():
    """Get task status data for dashboard chart"""
    # Build base query - scoped to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(tenant_filter, (Task.is_archived == False) | (Task.is_archived == None))
    
    if not (current_user.is_admin() or current_user.is_manager()):
        accessible_entity_ids = current_user.get_accessible_entity_ids('view')
        if accessible_entity_ids:
            query = query.filter(
                (Task.owner_id == current_user.id) | 
                (Task.reviewer_id == current_user.id) |
                (Task.entity_id.in_(accessible_entity_ids))
            )
        else:
            query = query.filter(
                (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
            )
    
    # Count by status
    status_counts = {}
    for status in ['draft', 'submitted', 'in_review', 'approved', 'completed', 'rejected']:
        status_counts[status] = query.filter_by(status=status).count()
    
    # Count overdue
    today = date.today()
    status_counts['overdue'] = query.filter(
        Task.due_date < today,
        Task.status != 'completed'
    ).count()
    
    return jsonify(status_counts)


@api_bp.route('/dashboard/monthly-chart')
@login_required
def dashboard_monthly_chart():
    """Get monthly task data for dashboard chart"""
    year = request.args.get('year', type=int, default=date.today().year)
    
    # Build base query - scoped to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(
        tenant_filter,
        Task.year == year,
        (Task.is_archived == False) | (Task.is_archived == None)
    )
    
    if not (current_user.is_admin() or current_user.is_manager()):
        accessible_entity_ids = current_user.get_accessible_entity_ids('view')
        if accessible_entity_ids:
            query = query.filter(
                (Task.owner_id == current_user.id) | 
                (Task.reviewer_id == current_user.id) |
                (Task.entity_id.in_(accessible_entity_ids))
            )
        else:
            query = query.filter(
                (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
            )
    
    # Count by month
    monthly_data = []
    for month in range(1, 13):
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        month_query = query.filter(Task.due_date >= month_start, Task.due_date <= month_end)
        
        monthly_data.append({
            'month': month,
            'total': month_query.count(),
            'completed': month_query.filter_by(status='completed').count()
        })
    
    return jsonify({
        'year': year,
        'months': monthly_data
    })


# ============================================================================
# PRESETS API
# ============================================================================

@api_bp.route('/presets')
@login_required
def presets_list():
    """Get list of active presets"""
    presets = TaskPreset.query.filter_by(is_active=True).order_by(TaskPreset.category, TaskPreset.title).all()
    
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'description': p.description,
        'default_period': p.default_period,
        'estimation_hours': p.estimation_hours
    } for p in presets])


@api_bp.route('/presets/<int:preset_id>')
@login_required
def preset_get(preset_id):
    """Get a single preset by ID"""
    preset = TaskPreset.query.get_or_404(preset_id)
    
    return jsonify({
        'id': preset.id,
        'title': preset.title,
        'category': preset.category,
        'description': preset.description,
        'default_period': preset.default_period,
        'estimation_hours': preset.estimation_hours,
        'is_active': preset.is_active
    })


# ============================================================================
# DASHBOARD API - TEAM & PROJECTS
# ============================================================================

@api_bp.route('/dashboard/team-chart')
@login_required
def dashboard_team_chart():
    """Get workload by team/owner for bar chart"""
    from collections import Counter
    
    # Only admins and managers can see team workload
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({'labels': [], 'data': [], 'colors': []})
    
    lang = session.get('lang', 'de')
    
    # Get active tasks (not completed) - scoped to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    tasks = Task.query.filter(tenant_filter, Task.status != 'completed').all()
    
    # Count by team
    team_counts = Counter()
    for task in tasks:
        if task.owner_team:
            team_name = task.owner_team.get_name(lang)
        elif task.owner:
            team_name = task.owner.name
        else:
            team_name = 'Nicht zugewiesen' if lang == 'de' else 'Unassigned'
        team_counts[team_name] += 1
    
    # Sort by count (top 10)
    sorted_teams = team_counts.most_common(10)
    
    labels = [t[0] for t in sorted_teams]
    data = [t[1] for t in sorted_teams]
    
    # Generate colors (brand palette variations)
    base_colors = ['#4A90D9', '#0D6EFD', '#0DCAF0', '#198754', '#FFC107', '#6C757D', '#DC3545', '#6610F2', '#D63384', '#20C997']
    colors = [base_colors[i % len(base_colors)] for i in range(len(labels))]
    
    return jsonify({
        'labels': labels,
        'data': data,
        'colors': colors
    })


@api_bp.route('/dashboard/project-velocity/<int:project_id>')
@login_required
def dashboard_project_velocity(project_id):
    """Get velocity chart data for a project (last 6 sprints)"""
    from modules.projects.models import Project, Sprint, Issue
    
    project = get_project_or_404_scoped(project_id)
    
    # Check access
    if not project.is_member(current_user):
        return jsonify({'error': 'Access denied'}), 403
    
    lang = session.get('lang', 'de')
    
    # Get last 6 completed sprints
    sprints = Sprint.query.filter_by(
        project_id=project_id,
        state='closed'
    ).order_by(Sprint.completed_at.desc()).limit(6).all()
    
    sprints.reverse()  # Oldest first
    
    labels = []
    committed = []
    completed = []
    
    for sprint in sprints:
        labels.append(sprint.name)
        committed.append(sprint.total_points or 0)
        completed.append(sprint.completed_points or 0)
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Geplant' if lang == 'de' else 'Committed',
                'data': committed,
                'backgroundColor': 'rgba(13, 110, 253, 0.5)',
                'borderColor': '#0D6EFD',
                'borderWidth': 2
            },
            {
                'label': 'Abgeschlossen' if lang == 'de' else 'Completed',
                'data': completed,
                'backgroundColor': 'rgba(74, 144, 217, 0.5)',
                'borderColor': '#4A90D9',
                'borderWidth': 2
            }
        ]
    })


@api_bp.route('/dashboard/trends')
@login_required
def dashboard_trends():
    """Get completion trends for the last 30 days"""
    from collections import defaultdict
    
    lang = session.get('lang', 'de')
    today = date.today()
    
    # Get tasks completed in last 30 days
    days_back = 30
    start_date = today - timedelta(days=days_back)
    
    # Build daily counts
    daily_completed = defaultdict(int)
    daily_created = defaultdict(int)
    
    # Tenant scoping
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    
    # Get completed tasks
    if current_user.is_admin() or current_user.is_manager():
        completed_tasks = Task.query.filter(
            tenant_filter,
            Task.status == 'completed',
            Task.updated_at >= start_date
        ).all()
        created_tasks = Task.query.filter(
            tenant_filter,
            Task.created_at >= start_date
        ).all()
    else:
        completed_tasks = Task.query.filter(
            tenant_filter,
            Task.status == 'completed',
            Task.updated_at >= start_date,
            (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
        ).all()
        created_tasks = Task.query.filter(
            tenant_filter,
            Task.created_at >= start_date,
            (Task.owner_id == current_user.id) | (Task.reviewer_id == current_user.id)
        ).all()
    
    for task in completed_tasks:
        if task.updated_at:
            day = task.updated_at.date() if hasattr(task.updated_at, 'date') else task.updated_at
            daily_completed[day] += 1
    
    for task in created_tasks:
        if task.created_at:
            day = task.created_at.date() if hasattr(task.created_at, 'date') else task.created_at
            daily_created[day] += 1
    
    # Build arrays for last 30 days
    labels = []
    completed_data = []
    created_data = []
    
    for i in range(days_back):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime('%d.%m'))
        completed_data.append(daily_completed.get(day, 0))
        created_data.append(daily_created.get(day, 0))
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Abgeschlossen' if lang == 'de' else 'Completed',
                'data': completed_data,
                'borderColor': '#4A90D9',
                'backgroundColor': 'rgba(74, 144, 217, 0.1)',
                'fill': True,
                'tension': 0.4
            },
            {
                'label': 'Erstellt' if lang == 'de' else 'Created',
                'data': created_data,
                'borderColor': '#0D6EFD',
                'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                'fill': True,
                'tension': 0.4
            }
        ]
    })


@api_bp.route('/dashboard/project-distribution')
@login_required
def dashboard_project_distribution():
    """Get issue distribution across user's projects"""
    from modules.projects.models import Project, ProjectMember, Issue
    
    lang = session.get('lang', 'de')
    
    # Tenant scoping for projects
    tenant_filter = (Project.tenant_id == g.tenant.id) if g.tenant else False
    
    # Get user's projects
    if current_user.is_admin():
        projects = Project.query.filter(tenant_filter, Project.is_archived == False).all()
    else:
        project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).all()
        project_ids = [p[0] for p in project_ids]
        projects = Project.query.filter(tenant_filter, Project.id.in_(project_ids), Project.is_archived == False).all()
    
    labels = []
    data = []
    colors = []
    
    for project in projects:
        issue_count = Issue.query.filter_by(project_id=project.id, is_archived=False).count()
        if issue_count > 0:
            labels.append(f"{project.key}: {project.get_name(lang)}")
            data.append(issue_count)
            colors.append(project.color or '#4A90D9')
    
    return jsonify({
        'labels': labels,
        'data': data,
        'colors': colors
    })


# ============================================================================
# NOTIFICATION API
# ============================================================================

@api_bp.route('/notifications')
@login_required
def notifications_list():
    """Get recent notifications for current user"""
    from services import NotificationService
    
    lang = session.get('lang', 'de')
    limit = request.args.get('limit', 10, type=int)
    include_read = request.args.get('include_read', 'true').lower() == 'true'
    
    notifications = NotificationService.get_recent(
        current_user.id, 
        limit=min(limit, 50),  # Cap at 50
        include_read=include_read
    )
    
    return jsonify({
        'notifications': [n.to_dict(lang) for n in notifications],
        'unread_count': NotificationService.get_unread_count(current_user.id)
    })


@api_bp.route('/notifications/unread-count')
@login_required
def notifications_unread_count():
    """Get unread notification count for badge"""
    from services import NotificationService
    
    return jsonify({
        'count': NotificationService.get_unread_count(current_user.id)
    })


@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def notification_mark_read(notification_id):
    """Mark a single notification as read"""
    from services import NotificationService
    
    success = NotificationService.mark_as_read(notification_id, current_user.id)
    if success:
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def notifications_mark_all_read():
    """Mark all notifications as read"""
    from services import NotificationService
    
    count = NotificationService.mark_all_as_read(current_user.id)
    db.session.commit()
    return jsonify({'success': True, 'count': count})
