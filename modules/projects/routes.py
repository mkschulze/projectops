"""
Project Management Module - Routes
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app, g, abort
from flask_login import login_required, current_user

from extensions import db
from models import User
from translations import get_translation as t
from .models import (
    Project, ProjectMember, ProjectRole,
    IssueType, IssueStatus, Issue, Sprint,
    IssueComment, IssueAttachment, IssueLink, IssueLinkType, Worklog, IssueReviewer,
    IssueActivity, create_default_issue_types, create_default_issue_statuses
)

# Create blueprint
bp = Blueprint('projects', __name__, template_folder='templates', url_prefix='/projects')


def project_access_required(f):
    """Decorator to check project access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        project_id = kwargs.get('project_id')
        if project_id:
            project = Project.query.get_or_404(project_id)
            if g.tenant and project.tenant_id != g.tenant.id:
                abort(404)
            if not project.is_member(current_user):
                flash('Kein Zugriff auf dieses Projekt.' if session.get('lang', 'de') == 'de' else 'No access to this project.', 'danger')
                return redirect(url_for('projects.project_list'))
            kwargs['project'] = project
        return f(*args, **kwargs)
    return decorated_function


def projects_module_required(f):
    """Decorator to check if user has access to projects module"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import Module, UserModule
        
        # Admins always have access
        if current_user.role == 'admin':
            return f(*args, **kwargs)
        
        # Check if projects module is active
        module = Module.query.filter_by(code='projects', is_active=True).first()
        if not module:
            flash('Projektmanagement-Modul ist nicht aktiv.' if session.get('lang', 'de') == 'de' else 'Project management module is not active.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Check if user has module assignment
        user_module = UserModule.query.filter_by(user_id=current_user.id, module_id=module.id).first()
        if not user_module:
            flash('Sie haben keinen Zugriff auf das Projektmanagement-Modul.' if session.get('lang', 'de') == 'de' else 'You do not have access to the project management module.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ACTIVITY TRACKING HELPER
# ============================================================================

def log_activity(issue, activity_type, user=None, field_name=None, 
                 old_value=None, new_value=None, details=None):
    """Log an activity for an issue
    
    Args:
        issue: The Issue object
        activity_type: Type of activity (status_change, comment, etc.)
        user: User who performed the action (defaults to current_user)
        field_name: Name of field changed (for field_update)
        old_value: Previous value (string)
        new_value: New value (string)
        details: Additional details
    """
    if user is None:
        user = current_user
    
    activity = IssueActivity(
        issue_id=issue.id,
        user_id=user.id if hasattr(user, 'id') else user,
        activity_type=activity_type,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        details=details
    )
    db.session.add(activity)
    return activity


# ============================================================================
# PROJECT LIST & DASHBOARD
# ============================================================================

@bp.route('/')
@login_required
@projects_module_required
def project_list():
    """List all projects the user has access to"""
    lang = session.get('lang', 'de')
    
    # Get projects based on role
    if current_user.role == 'admin':
        projects = Project.query.filter_by(is_archived=False).order_by(Project.name).all()
    else:
        # Get projects where user is a member
        member_project_ids = [m.project_id for m in current_user.project_memberships]
        projects = Project.query.filter(
            Project.id.in_(member_project_ids),
            Project.is_archived == False
        ).order_by(Project.name).all()
    
    return render_template('projects/list.html', projects=projects, lang=lang)


# ============================================================================
# PROJECT CRUD
# ============================================================================

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@projects_module_required
def project_new():
    """Create a new project"""
    lang = session.get('lang', 'de')
    
    # Only admins and managers can create projects
    if current_user.role not in ['admin', 'manager']:
        flash('Keine Berechtigung zum Erstellen von Projekten.' if lang == 'de' else 'No permission to create projects.', 'danger')
        return redirect(url_for('projects.project_list'))
    
    if request.method == 'POST':
        key = request.form.get('key', '').upper().strip()
        name = request.form.get('name', '').strip()
        name_en = request.form.get('name_en', '').strip()
        description = request.form.get('description', '').strip()
        description_en = request.form.get('description_en', '').strip()
        lead_id = request.form.get('lead_id', type=int)
        category = request.form.get('category', '').strip()
        icon = request.form.get('icon', 'bi-folder').strip()
        color = request.form.get('color', '#4A90D9').strip()
        
        # Validation
        if not key or not name:
            flash('Projektschlüssel und Name sind erforderlich.' if lang == 'de' else 'Project key and name are required.', 'danger')
            return redirect(url_for('projects.project_new'))
        
        if len(key) > 10:
            flash('Projektschlüssel darf maximal 10 Zeichen lang sein.' if lang == 'de' else 'Project key must be at most 10 characters.', 'danger')
            return redirect(url_for('projects.project_new'))
        
        # Check if key already exists
        if Project.query.filter_by(key=key).first():
            flash('Projektschlüssel existiert bereits.' if lang == 'de' else 'Project key already exists.', 'danger')
            return redirect(url_for('projects.project_new'))
        
        project = Project(
            key=key,
            name=name,
            name_en=name_en or None,
            description=description or None,
            description_en=description_en or None,
            lead_id=lead_id,
            category=category or None,
            icon=icon,
            color=color,
            created_by_id=current_user.id
        )
        db.session.add(project)
        db.session.flush()  # Get project ID
        
        # Add creator as admin member
        member = ProjectMember(
            project_id=project.id,
            user_id=current_user.id,
            role='admin',
            added_by_id=current_user.id
        )
        db.session.add(member)
        
        # Add lead as member if different from creator
        if lead_id and lead_id != current_user.id:
            lead_member = ProjectMember(
                project_id=project.id,
                user_id=lead_id,
                role='lead',
                added_by_id=current_user.id
            )
            db.session.add(lead_member)
        
        db.session.commit()
        
        flash(f'Projekt {project.key} erstellt.' if lang == 'de' else f'Project {project.key} created.', 'success')
        return redirect(url_for('projects.project_detail', project_id=project.id))
    
    # GET request
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return render_template('projects/form.html', project=None, users=users, lang=lang)


@bp.route('/<int:project_id>')
@login_required
@projects_module_required
@project_access_required
def project_detail(project_id, project=None):
    """Project detail/dashboard view"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Get member list
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    
    # Get issue count
    issue_count = Issue.query.filter_by(project_id=project_id).count()
    
    # Get sprints
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.start_date.desc()).all()
    
    # Get recent activities from all issues in this project
    from sqlalchemy import desc
    recent_activities = IssueActivity.query.join(Issue).filter(
        Issue.project_id == project_id
    ).order_by(desc(IssueActivity.created_at)).limit(20).all()
    
    return render_template('projects/detail.html', project=project, members=members, 
                          sprints=sprints, issue_count=issue_count,
                          recent_activities=recent_activities, lang=lang)


@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def project_edit(project_id, project=None):
    """Edit project settings"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Check edit permission
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung zum Bearbeiten.' if lang == 'de' else 'No permission to edit.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    if request.method == 'POST':
        project.name = request.form.get('name', '').strip()
        project.name_en = request.form.get('name_en', '').strip() or None
        project.description = request.form.get('description', '').strip() or None
        project.description_en = request.form.get('description_en', '').strip() or None
        project.lead_id = request.form.get('lead_id', type=int)
        project.category = request.form.get('category', '').strip() or None
        project.icon = request.form.get('icon', 'bi-folder').strip()
        project.color = request.form.get('color', '#4A90D9').strip()
        project.methodology = request.form.get('methodology', 'scrum').strip()
        
        db.session.commit()
        
        flash('Projekt aktualisiert.' if lang == 'de' else 'Project updated.', 'success')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    from modules.projects.models import METHODOLOGY_CONFIG
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return render_template('projects/form.html', 
        project=project, 
        users=users, 
        methodology_config=METHODOLOGY_CONFIG,
        lang=lang
    )


@bp.route('/<int:project_id>/archive', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_archive(project_id, project=None):
    """Archive a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Only admins can archive
    if project.get_member_role(current_user) != 'admin':
        flash('Keine Berechtigung zum Archivieren.' if lang == 'de' else 'No permission to archive.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    from datetime import datetime
    project.is_archived = True
    project.archived_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Projekt {project.key} archiviert.' if lang == 'de' else f'Project {project.key} archived.', 'success')
    return redirect(url_for('projects.project_list'))


# ============================================================================
# PROJECT MEMBERS
# ============================================================================

@bp.route('/<int:project_id>/members')
@login_required
@projects_module_required
@project_access_required
def project_members(project_id, project=None):
    """Manage project members"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    member_user_ids = [m.user_id for m in members]
    
    # Only show users who have the projects module enabled
    from models import UserModule, Module
    projects_module = Module.query.filter_by(code='projects').first()
    if projects_module:
        users_with_module = db.session.query(UserModule.user_id).filter_by(
            module_id=projects_module.id
        ).subquery()
        available_users = User.query.filter(
            User.is_active == True,
            ~User.id.in_(member_user_ids),
            User.id.in_(users_with_module)
        ).order_by(User.name).all()
    else:
        available_users = User.query.filter(
            User.is_active == True,
            ~User.id.in_(member_user_ids)
        ).order_by(User.name).all()
    
    can_edit = project.can_user_edit(current_user)
    
    return render_template('projects/members.html', 
                          project=project, 
                          members=members, 
                          available_users=available_users,
                          can_edit=can_edit,
                          lang=lang)


@bp.route('/<int:project_id>/members/add', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_member_add(project_id, project=None):
    """Add a member to the project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    user_id = request.form.get('user_id', type=int)
    role = request.form.get('role', 'member')
    
    if not user_id:
        flash('Benutzer erforderlich.' if lang == 'de' else 'User required.', 'danger')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    # Check if user has projects module enabled
    from models import UserModule, Module
    projects_module = Module.query.filter_by(code='projects').first()
    if projects_module:
        has_access = UserModule.query.filter_by(
            user_id=user_id, 
            module_id=projects_module.id
        ).first()
        if not has_access:
            flash('Dieser Benutzer hat keinen Zugriff auf das Projektmanagement-Modul.' if lang == 'de' else 'This user does not have access to the Project Management module.', 'warning')
            return redirect(url_for('projects.project_members', project_id=project_id))
    
    # Check if already member
    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing:
        flash('Benutzer ist bereits Mitglied.' if lang == 'de' else 'User is already a member.', 'warning')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
        added_by_id=current_user.id
    )
    db.session.add(member)
    db.session.commit()
    
    flash('Mitglied hinzugefügt.' if lang == 'de' else 'Member added.', 'success')
    return redirect(url_for('projects.project_members', project_id=project_id))


@bp.route('/<int:project_id>/members/<int:member_id>/remove', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_member_remove(project_id, member_id, project=None):
    """Remove a member from the project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    member = ProjectMember.query.get_or_404(member_id)
    
    # Can't remove last admin
    admin_count = ProjectMember.query.filter_by(project_id=project_id, role='admin').count()
    if member.role == 'admin' and admin_count <= 1:
        flash('Kann letzten Administrator nicht entfernen.' if lang == 'de' else 'Cannot remove last administrator.', 'danger')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    db.session.delete(member)
    db.session.commit()
    
    flash('Mitglied entfernt.' if lang == 'de' else 'Member removed.', 'success')
    return redirect(url_for('projects.project_members', project_id=project_id))


@bp.route('/<int:project_id>/members/<int:member_id>/role', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_member_role(project_id, member_id, project=None):
    """Change member role"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_members', project_id=project_id))
    
    member = ProjectMember.query.get_or_404(member_id)
    new_role = request.form.get('role', 'member')
    
    # Can't demote last admin
    if member.role == 'admin' and new_role != 'admin':
        admin_count = ProjectMember.query.filter_by(project_id=project_id, role='admin').count()
        if admin_count <= 1:
            flash('Kann letzten Administrator nicht herabstufen.' if lang == 'de' else 'Cannot demote last administrator.', 'danger')
            return redirect(url_for('projects.project_members', project_id=project_id))
    
    member.role = new_role
    db.session.commit()
    
    flash('Rolle aktualisiert.' if lang == 'de' else 'Role updated.', 'success')
    return redirect(url_for('projects.project_members', project_id=project_id))


# ============================================================================
# ISSUE MANAGEMENT
# ============================================================================

@bp.route('/<int:project_id>/items', strict_slashes=False)
@login_required
@projects_module_required
@project_access_required
def item_list(project_id, project=None):
    """List all issues in a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Get filter parameters
    status_id = request.args.get('status', type=int)
    type_id = request.args.get('type', type=int)
    assignee_id = request.args.get('assignee', type=int)
    priority = request.args.get('priority', type=int)
    search = request.args.get('search', '').strip()
    
    # Build query
    query = Issue.query.filter_by(project_id=project_id, is_archived=False)
    
    if status_id:
        query = query.filter_by(status_id=status_id)
    if type_id:
        query = query.filter_by(type_id=type_id)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if priority:
        query = query.filter_by(priority=priority)
    if search:
        query = query.filter(
            db.or_(
                Issue.key.ilike(f'%{search}%'),
                Issue.summary.ilike(f'%{search}%')
            )
        )
    
    issues = query.order_by(Issue.created_at.desc()).all()
    
    # Get filter options
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    
    return render_template('projects/items/list.html',
        project=project,
        issues=issues,
        issue_types=issue_types,
        issue_statuses=issue_statuses,
        members=members,
        filters={
            'status': status_id,
            'type': type_id,
            'assignee': assignee_id,
            'priority': priority,
            'search': search
        },
        lang=lang
    )


@bp.route('/<int:project_id>/items/new', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def item_new(project_id, project=None):
    """Create a new issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Check permission
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung zum Erstellen von Issues.' if lang == 'de' else 'No permission to create issues.', 'danger')
        return redirect(url_for('projects.item_list', project_id=project_id))
    
    # Get issue types and statuses for this project
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    # If no types/statuses exist, create defaults
    if not issue_types:
        create_default_issue_types(project)
        db.session.commit()
        issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    
    if not issue_statuses:
        create_default_issue_statuses(project)
        db.session.commit()
        issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    sprints = Sprint.query.filter_by(project_id=project_id).filter(Sprint.state != 'closed').all()
    
    # Get parent issues (for sub-tasks)
    parent_issues = Issue.query.filter_by(project_id=project_id, is_archived=False).filter(
        Issue.type_id.in_([t.id for t in issue_types if t.can_have_children])
    ).all()
    
    if request.method == 'POST':
        type_id = request.form.get('type_id', type=int)
        summary = request.form.get('summary', '').strip()
        description = request.form.get('description', '').strip()
        assignee_id = request.form.get('assignee_id', type=int)
        priority = request.form.get('priority', 3, type=int)
        parent_id = request.form.get('parent_id', type=int)
        sprint_id = request.form.get('sprint_id', type=int)
        story_points = request.form.get('story_points', type=float)
        due_date = request.form.get('due_date')
        labels = request.form.get('labels', '').strip()
        
        # Validation
        if not type_id or not summary:
            flash('Typ und Zusammenfassung sind erforderlich.' if lang == 'de' else 'Type and summary are required.', 'danger')
            return redirect(url_for('projects.item_new', project_id=project_id))
        
        # Get initial status
        initial_status = IssueStatus.query.filter_by(project_id=project_id, is_initial=True).first()
        if not initial_status:
            initial_status = issue_statuses[0] if issue_statuses else None
        
        if not initial_status:
            flash('Keine Status konfiguriert.' if lang == 'de' else 'No statuses configured.', 'danger')
            return redirect(url_for('projects.item_new', project_id=project_id))
        
        # Generate issue key
        issue_key = project.get_next_issue_key()
        
        # Parse labels
        label_list = [l.strip() for l in labels.split(',') if l.strip()] if labels else []
        
        # Parse due date
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        issue = Issue(
            project_id=project_id,
            key=issue_key,
            type_id=type_id,
            status_id=initial_status.id,
            summary=summary,
            description=description or None,
            assignee_id=assignee_id or None,
            reporter_id=current_user.id,
            priority=priority,
            parent_id=parent_id or None,
            sprint_id=sprint_id or None,
            story_points=story_points,
            due_date=parsed_due_date,
            labels=label_list
        )
        db.session.add(issue)
        db.session.flush()  # Get issue.id before commit
        
        # Log activity - issue created
        log_activity(issue, 'created')
        
        db.session.commit()
        
        flash(f'Issue {issue.key} erstellt.' if lang == 'de' else f'Issue {issue.key} created.', 'success')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue.key))
    
    # GET request
    return render_template('projects/items/form.html',
        project=project,
        issue=None,
        issue_types=issue_types,
        issue_statuses=issue_statuses,
        members=members,
        sprints=sprints,
        parent_issues=parent_issues,
        lang=lang
    )


@bp.route('/<int:project_id>/items/<issue_key>')
@login_required
@projects_module_required
@project_access_required
def item_detail(project_id, issue_key, project=None):
    """Issue detail view"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Get all statuses for display
    all_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    # Filter to only allowed transitions based on current status
    current_status = issue.status
    if current_status and current_status.allowed_transitions:
        # Has workflow restrictions - filter to allowed statuses + current
        allowed_ids = set(current_status.allowed_transitions)
        allowed_ids.add(current_status.id)  # Always include current status
        available_statuses = [s for s in all_statuses if s.id in allowed_ids]
    else:
        # No restrictions - all statuses available
        available_statuses = all_statuses
    
    # Get child issues (sub-tasks)
    children = Issue.query.filter_by(parent_id=issue.id, is_archived=False).all()
    
    from datetime import datetime
    from extensions import db
    
    return render_template('projects/items/detail.html',
        project=project,
        issue=issue,
        available_statuses=available_statuses,
        children=children,
        lang=lang,
        db=db,
        now=datetime.now()
    )


@bp.route('/<int:project_id>/items/<issue_key>/edit', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def item_edit(project_id, issue_key, project=None):
    """Edit an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check permission
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    sprints = Sprint.query.filter_by(project_id=project_id).filter(Sprint.state != 'closed').all()
    parent_issues = Issue.query.filter_by(project_id=project_id, is_archived=False).filter(
        Issue.id != issue.id,
        Issue.type_id.in_([t.id for t in issue_types if t.can_have_children])
    ).all()
    
    if request.method == 'POST':
        issue.type_id = request.form.get('type_id', type=int)
        issue.summary = request.form.get('summary', '').strip()
        issue.description = request.form.get('description', '').strip() or None
        issue.assignee_id = request.form.get('assignee_id', type=int) or None
        issue.priority = request.form.get('priority', 3, type=int)
        issue.parent_id = request.form.get('parent_id', type=int) or None
        issue.sprint_id = request.form.get('sprint_id', type=int) or None
        issue.story_points = request.form.get('story_points', type=float)
        
        due_date = request.form.get('due_date')
        if due_date:
            try:
                issue.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            issue.due_date = None
        
        labels = request.form.get('labels', '').strip()
        issue.labels = [l.strip() for l in labels.split(',') if l.strip()] if labels else []
        
        db.session.commit()
        
        flash('Issue aktualisiert.' if lang == 'de' else 'Issue updated.', 'success')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    return render_template('projects/items/form.html',
        project=project,
        issue=issue,
        issue_types=issue_types,
        issue_statuses=issue_statuses,
        members=members,
        sprints=sprints,
        parent_issues=parent_issues,
        lang=lang
    )


@bp.route('/<int:project_id>/items/<issue_key>/transition', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_transition(project_id, issue_key, project=None):
    """Change issue status"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    new_status_id = request.form.get('status_id', type=int)
    if not new_status_id:
        flash('Kein Status angegeben.' if lang == 'de' else 'No status specified.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    new_status = IssueStatus.query.get_or_404(new_status_id)
    
    # Check if transition is allowed
    if issue.status and not issue.status.can_transition_to(new_status_id):
        flash('Dieser Statusübergang ist nicht erlaubt.' if lang == 'de' else 'This status transition is not allowed.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    old_status = issue.status
    issue.status_id = new_status_id
    
    # Log activity - status change
    log_activity(issue, 'status_change', 
                 old_value=old_status.get_name(lang) if old_status else None,
                 new_value=new_status.get_name(lang))
    
    # Set resolution date if moving to final status
    if new_status.is_final and not issue.resolution_date:
        issue.resolution_date = datetime.utcnow()
    elif not new_status.is_final:
        issue.resolution_date = None
    
    db.session.commit()
    
    flash(f'Status geändert: {old_status.get_name(lang)} → {new_status.get_name(lang)}' if lang == 'de' 
          else f'Status changed: {old_status.get_name(lang)} → {new_status.get_name(lang)}', 'success')
    
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_delete(project_id, issue_key, project=None):
    """Delete (archive) an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check permission
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    issue.is_archived = True
    issue.archived_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Issue {issue.key} archiviert.' if lang == 'de' else f'Issue {issue.key} archived.', 'success')
    return redirect(url_for('projects.item_list', project_id=project_id))


# ============================================================================
# PROJECT CONFIGURATION (Issue Types & Statuses)
# ============================================================================

@bp.route('/<int:project_id>/settings/types')
@login_required
@projects_module_required
@project_access_required
def project_issue_types(project_id, project=None):
    """Manage issue types for a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    
    # Create defaults if none exist
    if not issue_types:
        create_default_issue_types(project)
        db.session.commit()
        issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    
    return render_template('projects/settings/issue_types.html',
        project=project,
        issue_types=issue_types,
        lang=lang
    )


@bp.route('/<int:project_id>/settings/statuses')
@login_required
@projects_module_required
@project_access_required
def project_issue_statuses(project_id, project=None):
    """Manage workflow statuses for a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    # Create defaults if none exist
    if not issue_statuses:
        create_default_issue_statuses(project)
        db.session.commit()
        issue_statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    return render_template('projects/settings/issue_statuses.html',
        project=project,
        issue_statuses=issue_statuses,
        lang=lang
    )


@bp.route('/<int:project_id>/settings/types/add', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_issue_type_add(project_id, project=None):
    """Add a new issue type"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    name = request.form.get('name', '').strip()
    name_en = request.form.get('name_en', '').strip()
    icon = request.form.get('icon', 'bi-card-checklist').strip()
    color = request.form.get('color', '#4A90D9').strip()
    hierarchy_level = request.form.get('hierarchy_level', 1, type=int)
    can_have_children = request.form.get('can_have_children') == 'on'
    is_subtask = request.form.get('is_subtask') == 'on'
    
    if not name:
        flash('Name ist erforderlich.' if lang == 'de' else 'Name is required.', 'danger')
        return redirect(url_for('projects.project_issue_types', project_id=project_id))
    
    # Get max sort order
    max_order = db.session.query(db.func.max(IssueType.sort_order)).filter_by(project_id=project_id).scalar() or 0
    
    issue_type = IssueType(
        project_id=project_id,
        name=name,
        name_en=name_en or None,
        icon=icon,
        color=color,
        hierarchy_level=hierarchy_level,
        can_have_children=can_have_children,
        is_subtask=is_subtask,
        sort_order=max_order + 1
    )
    db.session.add(issue_type)
    db.session.commit()
    
    flash('Issue-Typ hinzugefügt.' if lang == 'de' else 'Issue type added.', 'success')
    return redirect(url_for('projects.project_issue_types', project_id=project_id))


@bp.route('/<int:project_id>/settings/statuses/add', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def project_issue_status_add(project_id, project=None):
    """Add a new workflow status"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    name = request.form.get('name', '').strip()
    name_en = request.form.get('name_en', '').strip()
    category = request.form.get('category', 'todo')
    color = request.form.get('color', '#75787B').strip()
    is_initial = request.form.get('is_initial') == 'on'
    is_final = request.form.get('is_final') == 'on'
    
    if not name:
        flash('Name ist erforderlich.' if lang == 'de' else 'Name is required.', 'danger')
        return redirect(url_for('projects.project_issue_statuses', project_id=project_id))
    
    # If this is initial, remove initial from others
    if is_initial:
        IssueStatus.query.filter_by(project_id=project_id, is_initial=True).update({'is_initial': False})
    
    # Get max sort order
    max_order = db.session.query(db.func.max(IssueStatus.sort_order)).filter_by(project_id=project_id).scalar() or 0
    
    status = IssueStatus(
        project_id=project_id,
        name=name,
        name_en=name_en or None,
        category=category,
        color=color,
        is_initial=is_initial,
        is_final=is_final,
        sort_order=max_order + 1
    )
    db.session.add(status)
    db.session.commit()
    
    flash('Status hinzugefügt.' if lang == 'de' else 'Status added.', 'success')
    return redirect(url_for('projects.project_issue_statuses', project_id=project_id))


@bp.route('/<int:project_id>/settings/workflow/transitions', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def save_workflow_transitions(project_id, project=None):
    """Save workflow transitions (allowed status changes)"""
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    if not data or 'transitions' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    transitions = data['transitions']
    
    # Update each status with its allowed transitions
    for status_id_str, allowed_to_ids in transitions.items():
        status_id = int(status_id_str)
        status = IssueStatus.query.filter_by(id=status_id, project_id=project_id).first()
        if status:
            # Store empty list if all transitions for this status should be blocked
            # Store list of IDs for specific allowed transitions
            status.allowed_transitions = allowed_to_ids if allowed_to_ids else []
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Transitions saved'})


@bp.route('/<int:project_id>/settings/methodology', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def project_methodology(project_id, project=None):
    """Configure project methodology and terminology"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    from modules.projects.models import METHODOLOGY_CONFIG
    
    if request.method == 'POST':
        # Update methodology
        new_methodology = request.form.get('methodology', 'scrum')
        old_methodology = project.methodology
        project.methodology = new_methodology
        
        # Reset estimation scale to default when methodology changes
        if old_methodology != new_methodology:
            project.estimation_scale = None  # Will use methodology-based default
        
        # Update custom terminology overrides
        terminology = {}
        term_keys = ['sprint', 'backlog', 'epic', 'story', 'task', 'bug', 
                     'story_points', 'velocity', 'burndown', 'board', 
                     'done', 'in_progress', 'todo', 'release']
        
        for key in term_keys:
            custom_de = request.form.get(f'term_{key}_de', '').strip()
            custom_en = request.form.get(f'term_{key}_en', '').strip()
            
            # Only store if different from default
            default_de = METHODOLOGY_CONFIG.get(new_methodology, {}).get('terminology', {}).get('de', {}).get(key, '')
            default_en = METHODOLOGY_CONFIG.get(new_methodology, {}).get('terminology', {}).get('en', {}).get(key, '')
            
            if custom_de and custom_de != default_de or custom_en and custom_en != default_en:
                terminology[key] = {'de': custom_de or default_de, 'en': custom_en or default_en}
        
        project.terminology = terminology if terminology else None
        db.session.commit()
        
        flash('Methodologie aktualisiert.' if lang == 'de' else 'Methodology updated.', 'success')
        return redirect(url_for('projects.project_methodology', project_id=project_id))
    
    return render_template('projects/settings/methodology.html',
        project=project,
        methodology_config=METHODOLOGY_CONFIG,
        lang=lang
    )


@bp.route('/<int:project_id>/settings/methodology/reset', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def reset_terminology(project_id, project=None):
    """Reset terminology to methodology defaults"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    project.terminology = None
    db.session.commit()
    
    flash('Terminologie zurückgesetzt.' if lang == 'de' else 'Terminology reset.', 'success')
    return redirect(url_for('projects.project_methodology', project_id=project_id))


# ============================================================================
# KANBAN BOARD
# ============================================================================

@bp.route('/<int:project_id>/board')
@login_required
@projects_module_required
@project_access_required
def kanban_board(project_id, project=None):
    """Kanban board view for a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Get statuses (columns) ordered by sort_order
    statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    # Create defaults if none exist
    if not statuses:
        create_default_issue_statuses(project)
        db.session.commit()
        statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    # Get all active issues grouped by status
    issues_by_status = {}
    for status in statuses:
        issues_by_status[status.id] = Issue.query.filter_by(
            project_id=project_id,
            status_id=status.id,
            is_archived=False
        ).order_by(Issue.board_position, Issue.created_at.desc()).all()
    
    # Get issue types for quick create
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    if not issue_types:
        create_default_issue_types(project)
        db.session.commit()
        issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    
    # Get members for assignment
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    
    return render_template('projects/board.html',
        project=project,
        statuses=statuses,
        issues_by_status=issues_by_status,
        issue_types=issue_types,
        members=members,
        lang=lang
    )


@bp.route('/<int:project_id>/board/move', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def kanban_move_issue(project_id, project=None):
    """API endpoint to move an issue on the board"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Check permission
    if not project.can_user_manage_issues(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    issue_id = data.get('issue_id')
    new_status_id = data.get('status_id')
    new_position = data.get('position', 0)
    
    if not issue_id or not new_status_id:
        return jsonify({'error': 'Missing issue_id or status_id'}), 400
    
    issue = Issue.query.filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        return jsonify({'error': 'Issue not found'}), 404
    
    new_status = IssueStatus.query.filter_by(id=new_status_id, project_id=project_id).first()
    if not new_status:
        return jsonify({'error': 'Status not found'}), 404
    
    old_status_id = issue.status_id
    old_status = issue.status
    
    # Validate workflow transition
    if old_status and old_status.id != new_status_id:
        if not old_status.can_transition_to(new_status_id):
            error_msg = 'Übergang nicht erlaubt' if lang == 'de' else 'Transition not allowed'
            return jsonify({'error': error_msg, 'transition_blocked': True}), 400
    
    # Update status
    issue.status_id = new_status_id
    issue.board_position = new_position
    
    # Set resolution date if moving to final status
    if new_status.is_final and not issue.resolution_date:
        issue.resolution_date = datetime.utcnow()
    elif not new_status.is_final:
        issue.resolution_date = None
    
    # Reorder other issues in the target column
    issues_in_column = Issue.query.filter(
        Issue.project_id == project_id,
        Issue.status_id == new_status_id,
        Issue.id != issue_id,
        Issue.is_archived == False
    ).order_by(Issue.board_position).all()
    
    # Insert at new position
    for i, other_issue in enumerate(issues_in_column):
        if i >= new_position:
            other_issue.board_position = i + 1
        else:
            other_issue.board_position = i
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'issue_key': issue.key,
        'old_status': old_status.get_name('de') if old_status else None,
        'new_status': new_status.get_name('de'),
        'is_final': new_status.is_final
    })


@bp.route('/<int:project_id>/board/quick-create', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def kanban_quick_create(project_id, project=None):
    """Quick create an issue from the board"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_manage_issues(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    summary = data.get('summary', '').strip()
    type_id = data.get('type_id')
    status_id = data.get('status_id')
    
    if not summary:
        return jsonify({'error': 'Summary is required'}), 400
    
    # Get or default type
    if type_id:
        issue_type = IssueType.query.filter_by(id=type_id, project_id=project_id).first()
    else:
        issue_type = IssueType.query.filter_by(project_id=project_id, is_default=True).first()
        if not issue_type:
            issue_type = IssueType.query.filter_by(project_id=project_id).first()
    
    if not issue_type:
        return jsonify({'error': 'No issue type found'}), 400
    
    # Get or default status
    if status_id:
        status = IssueStatus.query.filter_by(id=status_id, project_id=project_id).first()
    else:
        status = IssueStatus.query.filter_by(project_id=project_id, is_initial=True).first()
        if not status:
            status = IssueStatus.query.filter_by(project_id=project_id).first()
    
    if not status:
        return jsonify({'error': 'No status found'}), 400
    
    # Generate key
    issue_key = project.get_next_issue_key()
    
    # Get max position in target column
    max_pos = db.session.query(db.func.max(Issue.board_position)).filter_by(
        project_id=project_id,
        status_id=status.id,
        is_archived=False
    ).scalar() or 0
    
    issue = Issue(
        project_id=project_id,
        key=issue_key,
        type_id=issue_type.id,
        status_id=status.id,
        summary=summary,
        reporter_id=current_user.id,
        priority=3,
        board_position=max_pos + 1
    )
    db.session.add(issue)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'issue': {
            'id': issue.id,
            'key': issue.key,
            'summary': issue.summary,
            'type': {
                'name': issue_type.get_name(lang),
                'icon': issue_type.icon,
                'color': issue_type.color
            },
            'status_id': status.id,
            'priority': issue.priority,
            'url': url_for('projects.item_detail', project_id=project_id, issue_key=issue.key)
        }
    })


# ==================== PM-4: Backlog ====================

@bp.route('/<int:project_id>/backlog')
@login_required
@projects_module_required
@project_access_required
def backlog(project_id, project=None):
    """Backlog view - prioritized list of all issues"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Get filter parameters
    type_filter = request.args.get('type', type=int)
    status_filter = request.args.get('status', type=int)
    assignee_filter = request.args.get('assignee', type=int)
    priority_filter = request.args.get('priority', type=int)
    search_filter = request.args.get('search', '').strip()
    
    # Build query - exclude completed issues (is_final status)
    # Join with IssueStatus to filter out final statuses
    query = Issue.query.filter_by(project_id=project_id, is_archived=False)\
        .join(IssueStatus, Issue.status_id == IssueStatus.id)\
        .filter(IssueStatus.is_final == False)
    
    if type_filter:
        query = query.filter(Issue.type_id == type_filter)
    if status_filter:
        query = query.filter(Issue.status_id == status_filter)
    if assignee_filter:
        if assignee_filter == -1:  # Unassigned
            query = query.filter(Issue.assignee_id.is_(None))
        else:
            query = query.filter(Issue.assignee_id == assignee_filter)
    if priority_filter:
        query = query.filter(Issue.priority == priority_filter)
    if search_filter:
        query = query.filter(
            db.or_(
                Issue.key.ilike(f'%{search_filter}%'),
                Issue.summary.ilike(f'%{search_filter}%')
            )
        )
    
    # Order by backlog_position (null last), then by created_at desc
    issues = query.order_by(
        Issue.backlog_position.asc().nullslast(),
        Issue.created_at.desc()
    ).all()
    
    # Get filter options
    issue_types = IssueType.query.filter_by(project_id=project_id).order_by(IssueType.sort_order).all()
    statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    
    # Calculate total story points
    total_story_points = sum(i.story_points or 0 for i in issues)
    
    return render_template('projects/backlog.html',
        project=project,
        issues=issues,
        issue_types=issue_types,
        statuses=statuses,
        members=members,
        total_story_points=total_story_points,
        filters={
            'type': type_filter,
            'status': status_filter,
            'assignee': assignee_filter,
            'priority': priority_filter,
            'search': search_filter
        },
        lang=lang
    )


@bp.route('/<int:project_id>/backlog/reorder', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def backlog_reorder(project_id, project=None):
    """API endpoint to reorder issues in the backlog"""
    try:
        if project is None:
            project = Project.query.get_or_404(project_id)

        if not project.can_user_manage_issues(current_user):
            return jsonify({'error': 'No permission'}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'error': 'Invalid JSON data',
                'content_type': request.content_type
            }), 400

        issue_ids = data.get('issue_ids')

        if not isinstance(issue_ids, list) or not issue_ids:
            return jsonify({'error': 'No issue_ids provided'}), 400

        # Update positions based on array order
        for position, issue_id in enumerate(issue_ids):
            issue = Issue.query.filter_by(id=issue_id, project_id=project_id).first()
            if issue:
                issue.backlog_position = position

        db.session.commit()

        return jsonify({'success': True, 'count': len(issue_ids)})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            'Backlog reorder failed',
            extra={'project_id': project_id, 'user_id': current_user.id}
        )
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/<int:project_id>/backlog/bulk', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def backlog_bulk_action(project_id, project=None):
    """Bulk actions on issues"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_manage_issues(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    action = data.get('action')
    issue_ids = data.get('issue_ids', [])
    
    if not issue_ids:
        return jsonify({'error': 'No issues selected'}), 400
    
    issues = Issue.query.filter(
        Issue.id.in_(issue_ids),
        Issue.project_id == project_id
    ).all()
    
    if not issues:
        return jsonify({'error': 'No valid issues found'}), 404
    
    count = len(issues)
    
    if action == 'change_status':
        new_status_id = data.get('status_id')
        if not new_status_id:
            return jsonify({'error': 'No status_id provided'}), 400
        
        new_status = IssueStatus.query.filter_by(id=new_status_id, project_id=project_id).first()
        if not new_status:
            return jsonify({'error': 'Status not found'}), 404
        
        for issue in issues:
            issue.status_id = new_status_id
            if new_status.is_final and not issue.resolution_date:
                issue.resolution_date = datetime.utcnow()
            elif not new_status.is_final:
                issue.resolution_date = None
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{count} {"Issues aktualisiert" if lang == "de" else "issues updated"}'
        })
    
    elif action == 'assign':
        assignee_id = data.get('assignee_id')
        # assignee_id can be None to unassign
        
        if assignee_id:
            # Verify user is a member
            member = ProjectMember.query.filter_by(
                project_id=project_id, 
                user_id=assignee_id
            ).first()
            if not member:
                return jsonify({'error': 'User is not a project member'}), 400
        
        for issue in issues:
            issue.assignee_id = assignee_id if assignee_id else None
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{count} {"Issues zugewiesen" if lang == "de" else "issues assigned"}'
        })
    
    elif action == 'change_priority':
        new_priority = data.get('priority')
        if new_priority is None or new_priority not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Invalid priority'}), 400
        
        for issue in issues:
            issue.priority = new_priority
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{count} {"Issues aktualisiert" if lang == "de" else "issues updated"}'
        })
    
    elif action == 'archive':
        for issue in issues:
            issue.is_archived = True
            issue.archived_at = datetime.utcnow()
            issue.archived_by_id = current_user.id
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{count} {"Issues archiviert" if lang == "de" else "issues archived"}'
        })
    
    elif action == 'delete':
        for issue in issues:
            db.session.delete(issue)
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'{count} {"Issues gelöscht" if lang == "de" else "issues deleted"}'
        })
    
    else:
        return jsonify({'error': 'Unknown action'}), 400


# ==================== PM-5: Sprint Management ====================

@bp.route('/<int:project_id>/iterations')
@login_required
@projects_module_required
@project_access_required
def iteration_list(project_id, project=None):
    """List all sprints for a project"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(
        db.case(
            (Sprint.state == 'active', 0),
            (Sprint.state == 'future', 1),
            (Sprint.state == 'closed', 2)
        ),
        Sprint.start_date.desc().nullslast(),
        Sprint.created_at.desc()
    ).all()
    
    # Calculate average velocity from closed sprints
    closed_sprints = [s for s in sprints if s.state == 'closed']
    average_velocity = 0
    if closed_sprints:
        total_completed = sum(s.completed_points for s in closed_sprints)
        average_velocity = round(total_completed / len(closed_sprints), 1)
    
    return render_template(
        'projects/iterations/list.html',
        project=project,
        sprints=sprints,
        average_velocity=average_velocity,
        lang=lang
    )


@bp.route('/<int:project_id>/iterations/new', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_create(project_id, project=None):
    """Create a new sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        goal = request.form.get('goal', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        
        if not name:
            flash('Name ist erforderlich.' if lang == 'de' else 'Name is required.', 'danger')
            return redirect(url_for('projects.iteration_create', project_id=project_id))
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ungültiges Startdatum.' if lang == 'de' else 'Invalid start date.', 'danger')
                return redirect(url_for('projects.iteration_create', project_id=project_id))
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ungültiges Enddatum.' if lang == 'de' else 'Invalid end date.', 'danger')
                return redirect(url_for('projects.iteration_create', project_id=project_id))
        
        if start_date and end_date and end_date < start_date:
            flash('Enddatum muss nach Startdatum liegen.' if lang == 'de' else 'End date must be after start date.', 'danger')
            return redirect(url_for('projects.iteration_create', project_id=project_id))
        
        sprint = Sprint(
            project_id=project_id,
            name=name,
            goal=goal or None,
            start_date=start_date,
            end_date=end_date,
            state='future'
        )
        db.session.add(sprint)
        db.session.commit()
        
        flash('Sprint erstellt.' if lang == 'de' else 'Sprint created.', 'success')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    # Load existing iterations for timeline preview
    existing_iterations = Sprint.query.filter_by(project_id=project_id).order_by(
        Sprint.start_date.asc().nullslast(),
        Sprint.created_at.asc()
    ).all()
    
    return render_template(
        'projects/iterations/form.html',
        project=project,
        sprint=None,
        existing_iterations=existing_iterations,
        lang=lang
    )


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/edit', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_edit(project_id, sprint_id, project=None):
    """Edit an existing sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        goal = request.form.get('goal', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        
        if not name:
            flash('Name ist erforderlich.' if lang == 'de' else 'Name is required.', 'danger')
            return redirect(url_for('projects.iteration_edit', project_id=project_id, sprint_id=sprint_id))
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ungültiges Startdatum.' if lang == 'de' else 'Invalid start date.', 'danger')
                return redirect(url_for('projects.iteration_edit', project_id=project_id, sprint_id=sprint_id))
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ungültiges Enddatum.' if lang == 'de' else 'Invalid end date.', 'danger')
                return redirect(url_for('projects.iteration_edit', project_id=project_id, sprint_id=sprint_id))
        
        if start_date and end_date and end_date < start_date:
            flash('Enddatum muss nach Startdatum liegen.' if lang == 'de' else 'End date must be after start date.', 'danger')
            return redirect(url_for('projects.iteration_edit', project_id=project_id, sprint_id=sprint_id))
        
        sprint.name = name
        sprint.goal = goal or None
        sprint.start_date = start_date
        sprint.end_date = end_date
        db.session.commit()
        
        flash('Sprint aktualisiert.' if lang == 'de' else 'Sprint updated.', 'success')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    return render_template(
        'projects/iterations/form.html',
        project=project,
        sprint=sprint,
        lang=lang
    )


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/start', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_start(project_id, sprint_id, project=None):
    """Start a sprint (change state from future to active)"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    if sprint.state != 'future':
        flash('Nur zukünftige Sprints können gestartet werden.' if lang == 'de' else 'Only future sprints can be started.', 'warning')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    # Check for existing active sprint
    active_sprint = Sprint.query.filter_by(project_id=project_id, state='active').first()
    if active_sprint:
        flash(f'Sprint "{active_sprint.name}" ist bereits aktiv. Bitte zuerst abschließen.' if lang == 'de' 
              else f'Sprint "{active_sprint.name}" is already active. Please complete it first.', 'warning')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    sprint.state = 'active'
    sprint.started_at = datetime.utcnow()
    if not sprint.start_date:
        sprint.start_date = datetime.utcnow().date()
    db.session.commit()
    
    flash(f'Sprint "{sprint.name}" gestartet.' if lang == 'de' else f'Sprint "{sprint.name}" started.', 'success')
    return redirect(url_for('projects.iteration_board', project_id=project_id, sprint_id=sprint_id))


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/complete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_complete(project_id, sprint_id, project=None):
    """Complete a sprint (change state from active to closed)"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    if sprint.state != 'active':
        flash('Nur aktive Sprints können abgeschlossen werden.' if lang == 'de' else 'Only active sprints can be completed.', 'warning')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    # Handle incomplete issues - move them back to backlog (remove sprint assignment)
    move_to_backlog = request.form.get('move_incomplete', 'true') == 'true'
    incomplete_count = 0
    
    for issue in sprint.issues:
        if not issue.status.is_final:
            incomplete_count += 1
            if move_to_backlog:
                issue.sprint_id = None
    
    sprint.state = 'closed'
    sprint.completed_at = datetime.utcnow()
    if not sprint.end_date:
        sprint.end_date = datetime.utcnow().date()
    db.session.commit()
    
    if incomplete_count > 0 and move_to_backlog:
        flash(f'Sprint "{sprint.name}" abgeschlossen. {incomplete_count} offene Issues ins Backlog verschoben.' if lang == 'de' 
              else f'Sprint "{sprint.name}" completed. {incomplete_count} incomplete issues moved to backlog.', 'success')
    else:
        flash(f'Sprint "{sprint.name}" abgeschlossen.' if lang == 'de' else f'Sprint "{sprint.name}" completed.', 'success')
    
    return redirect(url_for('projects.iteration_list', project_id=project_id))


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_delete(project_id, sprint_id, project=None):
    """Delete a sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.iteration_list', project_id=project_id))
    
    # Move all issues back to backlog before deleting
    for issue in sprint.issues:
        issue.sprint_id = None
    
    sprint_name = sprint.name
    db.session.delete(sprint)
    db.session.commit()
    
    flash(f'Sprint "{sprint_name}" gelöscht.' if lang == 'de' else f'Sprint "{sprint_name}" deleted.', 'success')
    return redirect(url_for('projects.iteration_list', project_id=project_id))


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/board')
@login_required
@projects_module_required
@project_access_required
def iteration_board(project_id, sprint_id, project=None):
    """Sprint board view - Kanban board for a specific sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    # Get statuses and issues for this sprint
    statuses = IssueStatus.query.filter_by(project_id=project_id).order_by(IssueStatus.sort_order).all()
    
    issues_by_status = {}
    for status in statuses:
        issues_by_status[status.id] = Issue.query.filter_by(
            project_id=project_id,
            sprint_id=sprint_id,
            status_id=status.id,
            is_archived=False
        ).order_by(Issue.board_position).all()
    
    return render_template(
        'projects/iterations/board.html',
        project=project,
        sprint=sprint,
        statuses=statuses,
        issues_by_status=issues_by_status,
        lang=lang
    )


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/add-issues', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_add_issues(project_id, sprint_id, project=None):
    """Add issues to a sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    if sprint.state == 'closed':
        return jsonify({'error': 'Cannot add issues to a closed sprint'}), 400
    
    data = request.get_json()
    issue_ids = data.get('issue_ids', [])
    
    if not issue_ids:
        return jsonify({'error': 'No issues provided'}), 400
    
    count = 0
    for issue_id in issue_ids:
        issue = Issue.query.filter_by(id=issue_id, project_id=project_id).first()
        if issue and issue.sprint_id != sprint_id:
            issue.sprint_id = sprint_id
            count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{count} {"Issues zum Sprint hinzugefügt" if lang == "de" else "issues added to sprint"}'
    })


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/remove-issue', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def iteration_remove_issue(project_id, sprint_id, project=None):
    """Remove an issue from a sprint"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    if not project.can_user_manage_issues(current_user):
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    issue_id = data.get('issue_id')
    
    if not issue_id:
        return jsonify({'error': 'No issue provided'}), 400
    
    issue = Issue.query.filter_by(id=issue_id, project_id=project_id, sprint_id=sprint_id).first()
    if not issue:
        return jsonify({'error': 'Issue not found in sprint'}), 404
    
    issue.sprint_id = None
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Issue aus Sprint entfernt' if lang == 'de' else 'Issue removed from sprint'
    })


@bp.route('/<int:project_id>/iterations/<int:sprint_id>/report')
@login_required
@projects_module_required
@project_access_required
def iteration_report(project_id, sprint_id, project=None):
    """Sprint report with burndown chart and statistics"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    sprint = Sprint.query.filter_by(id=sprint_id, project_id=project_id).first_or_404()
    
    # Collect sprint statistics
    issues = list(sprint.issues)
    total_issues = len(issues)
    completed_issues = [i for i in issues if i.status and i.status.is_final]
    in_progress_issues = [i for i in issues if i.status and i.status.category == 'in_progress']
    todo_issues = [i for i in issues if i.status and i.status.category == 'todo']
    
    total_points = sprint.total_points
    completed_points = sprint.completed_points
    
    # Calculate burndown data
    burndown_data = calculate_burndown_data(sprint, issues)
    
    # Calculate velocity for this sprint and previous sprints
    velocity_data = calculate_velocity_data(project)
    
    # Issue breakdown by type
    issues_by_type = {}
    for issue in issues:
        type_name = issue.issue_type.get_name(lang) if issue.issue_type else 'Unknown'
        if type_name not in issues_by_type:
            issues_by_type[type_name] = {'total': 0, 'completed': 0, 'color': issue.issue_type.color if issue.issue_type else '#666'}
        issues_by_type[type_name]['total'] += 1
        if issue.status and issue.status.is_final:
            issues_by_type[type_name]['completed'] += 1
    
    # Issue breakdown by assignee
    issues_by_assignee = {}
    for issue in issues:
        assignee_name = issue.assignee.name if issue.assignee else ('Nicht zugewiesen' if lang == 'de' else 'Unassigned')
        if assignee_name not in issues_by_assignee:
            issues_by_assignee[assignee_name] = {'total': 0, 'completed': 0, 'points': 0}
        issues_by_assignee[assignee_name]['total'] += 1
        issues_by_assignee[assignee_name]['points'] += issue.story_points or 0
        if issue.status and issue.status.is_final:
            issues_by_assignee[assignee_name]['completed'] += 1
    
    return render_template(
        'projects/iterations/report.html',
        project=project,
        sprint=sprint,
        total_issues=total_issues,
        completed_issues=len(completed_issues),
        in_progress_issues=len(in_progress_issues),
        todo_issues=len(todo_issues),
        total_points=total_points,
        completed_points=completed_points,
        burndown_data=burndown_data,
        velocity_data=velocity_data,
        issues_by_type=issues_by_type,
        issues_by_assignee=issues_by_assignee,
        completed_issue_list=completed_issues,
        lang=lang
    )


def calculate_burndown_data(sprint, issues):
    """Calculate burndown chart data for a sprint"""
    from datetime import timedelta
    
    if not sprint.start_date or not sprint.end_date:
        return {'labels': [], 'ideal': [], 'actual': [], 'remaining': []}
    
    start = sprint.start_date
    end = sprint.end_date
    days = (end - start).days + 1
    
    if days <= 0:
        return {'labels': [], 'ideal': [], 'actual': [], 'remaining': []}
    
    # Total story points at sprint start
    total_points = sum(i.story_points or 0 for i in issues)
    
    # Ideal burndown (linear)
    ideal = []
    labels = []
    for i in range(days):
        current_date = start + timedelta(days=i)
        labels.append(current_date.strftime('%d.%m'))
        ideal.append(round(total_points - (total_points / (days - 1) * i) if days > 1 else 0, 1))
    
    # Actual burndown based on when issues were completed
    actual = []
    today = datetime.now().date()
    
    for i in range(days):
        current_date = start + timedelta(days=i)
        
        if current_date > today:
            # Future dates - no actual data
            actual.append(None)
        else:
            # Count remaining points as of this date
            remaining = 0
            for issue in issues:
                points = issue.story_points or 0
                # Issue is remaining if not completed or completed after this date
                if issue.status and issue.status.is_final:
                    # Check if completed after this date
                    if issue.resolution_date and issue.resolution_date.date() > current_date:
                        remaining += points
                    elif not issue.resolution_date:
                        # No resolution_date but marked done - assume completed at sprint end
                        pass  # Count as completed
                else:
                    remaining += points
            actual.append(remaining)
    
    return {
        'labels': labels,
        'ideal': ideal,
        'actual': actual
    }


def calculate_velocity_data(project):
    """Calculate velocity data for closed sprints"""
    closed_sprints = Sprint.query.filter_by(
        project_id=project.id,
        state='closed'
    ).order_by(Sprint.completed_at.desc()).limit(10).all()
    
    # Reverse to show chronologically
    closed_sprints = list(reversed(closed_sprints))
    
    velocity_data = {
        'labels': [],
        'committed': [],
        'completed': [],
        'average': 0
    }
    
    total_completed = 0
    for sprint in closed_sprints:
        velocity_data['labels'].append(sprint.name)
        committed = sum(i.story_points or 0 for i in sprint.issues)
        completed = sprint.completed_points
        velocity_data['committed'].append(committed)
        velocity_data['completed'].append(completed)
        total_completed += completed
    
    if closed_sprints:
        velocity_data['average'] = round(total_completed / len(closed_sprints), 1)
    
    return velocity_data


# ============================================================================
# ISSUE COMMENTS
# ============================================================================

@bp.route('/<int:project_id>/items/<issue_key>/comments', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def comment_add(project_id, issue_key, project=None):
    """Add a comment to an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Kommentar darf nicht leer sein.' if lang == 'de' else 'Comment cannot be empty.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    comment = IssueComment(
        issue_id=issue.id,
        author_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    
    # Log activity - comment added
    log_activity(issue, 'comment', details=content[:100] if len(content) > 100 else content)
    
    # Update issue updated_at
    issue.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Kommentar hinzugefügt.' if lang == 'de' else 'Comment added.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/comments/<int:comment_id>/edit', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def comment_edit(project_id, issue_key, comment_id, project=None):
    """Edit a comment"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    comment = IssueComment.query.filter_by(id=comment_id, issue_id=issue.id).first_or_404()
    
    # Only author or admin can edit
    if comment.author_id != current_user.id and not project.is_admin(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Kommentar darf nicht leer sein.' if lang == 'de' else 'Comment cannot be empty.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    comment.content = content
    comment.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Kommentar aktualisiert.' if lang == 'de' else 'Comment updated.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def comment_delete(project_id, issue_key, comment_id, project=None):
    """Delete a comment"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    comment = IssueComment.query.filter_by(id=comment_id, issue_id=issue.id).first_or_404()
    
    # Only author or admin can delete
    if comment.author_id != current_user.id and not project.is_admin(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Kommentar gelöscht.' if lang == 'de' else 'Comment deleted.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


# ============================================================================
# ISSUE ATTACHMENTS
# ============================================================================

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/issues'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/<int:project_id>/items/<issue_key>/attachments', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def attachment_upload(project_id, issue_key, project=None):
    """Upload an attachment to an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    if 'file' not in request.files:
        flash('Keine Datei ausgewählt.' if lang == 'de' else 'No file selected.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Keine Datei ausgewählt.' if lang == 'de' else 'No file selected.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    if not allowed_file(file.filename):
        flash('Dateityp nicht erlaubt.' if lang == 'de' else 'File type not allowed.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        flash('Datei zu groß (max. 10 MB).' if lang == 'de' else 'File too large (max. 10 MB).', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Create upload directory
    upload_dir = os.path.join(UPLOAD_FOLDER, f'project_{project_id}', issue_key)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Secure filename with timestamp
    original_filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'{timestamp}_{original_filename}'
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    file.save(filepath)
    
    # Get MIME type
    import mimetypes
    mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
    
    # Create attachment record
    attachment = IssueAttachment(
        issue_id=issue.id,
        uploaded_by_id=current_user.id,
        filename=original_filename,
        filepath=filepath,
        filesize=size,
        mimetype=mimetype
    )
    db.session.add(attachment)
    
    # Log activity - attachment added
    log_activity(issue, 'attachment', details=original_filename)
    
    # Update issue
    issue.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Datei hochgeladen.' if lang == 'de' else 'File uploaded.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/attachments/<int:attachment_id>/download')
@login_required
@projects_module_required
@project_access_required
def attachment_download(project_id, issue_key, attachment_id, project=None):
    """Download an attachment"""
    from flask import send_file
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    attachment = IssueAttachment.query.filter_by(id=attachment_id, issue_id=issue.id).first_or_404()
    
    if not os.path.exists(attachment.filepath):
        flash('Datei nicht gefunden.' if session.get('lang', 'de') == 'de' else 'File not found.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    return send_file(
        attachment.filepath,
        download_name=attachment.filename,
        as_attachment=True
    )


@bp.route('/<int:project_id>/items/<issue_key>/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def attachment_delete(project_id, issue_key, attachment_id, project=None):
    """Delete an attachment"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    attachment = IssueAttachment.query.filter_by(id=attachment_id, issue_id=issue.id).first_or_404()
    
    # Only uploader or admin can delete
    if attachment.uploaded_by_id != current_user.id and not project.is_admin(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Delete file from disk
    if os.path.exists(attachment.filepath):
        os.remove(attachment.filepath)
    
    db.session.delete(attachment)
    db.session.commit()
    
    flash('Datei gelöscht.' if lang == 'de' else 'File deleted.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


# ============================================================================
# ISSUE LINKS
# ============================================================================

@bp.route('/<int:project_id>/items/<issue_key>/links', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def link_add(project_id, issue_key, project=None):
    """Add a link between issues"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    link_type = request.form.get('link_type')
    target_key = request.form.get('target_key', '').strip().upper()
    
    if not link_type or not target_key:
        flash('Bitte Linktyp und Ziel-Issue angeben.' if lang == 'de' else 'Please specify link type and target issue.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Find target issue
    target_issue = Issue.query.filter_by(key=target_key).first()
    if not target_issue:
        flash(f'Issue {target_key} nicht gefunden.' if lang == 'de' else f'Issue {target_key} not found.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    if target_issue.id == issue.id:
        flash('Issue kann nicht mit sich selbst verknüpft werden.' if lang == 'de' else 'Issue cannot be linked to itself.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check if link already exists
    existing = IssueLink.query.filter_by(
        source_issue_id=issue.id,
        target_issue_id=target_issue.id,
        link_type=link_type
    ).first()
    
    if existing:
        flash('Link existiert bereits.' if lang == 'de' else 'Link already exists.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Create link
    link = IssueLink(
        source_issue_id=issue.id,
        target_issue_id=target_issue.id,
        link_type=link_type,
        created_by_id=current_user.id
    )
    db.session.add(link)
    
    # Log activity - link added
    log_activity(issue, 'link', details=f'{link_type}: {target_key}')
    
    # Update issue
    issue.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Link hinzugefügt.' if lang == 'de' else 'Link added.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/links/<int:link_id>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def link_delete(project_id, issue_key, link_id, project=None):
    """Delete an issue link"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Link can be on either side
    link = IssueLink.query.filter(
        IssueLink.id == link_id,
        db.or_(
            IssueLink.source_issue_id == issue.id,
            IssueLink.target_issue_id == issue.id
        )
    ).first_or_404()
    
    db.session.delete(link)
    db.session.commit()
    
    flash('Link entfernt.' if lang == 'de' else 'Link removed.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


# ============================================================================
# WORKLOG (Time Tracking)
# ============================================================================

@bp.route('/<int:project_id>/items/<issue_key>/worklog', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def worklog_add(project_id, issue_key, project=None):
    """Log time on an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    time_input = request.form.get('time_spent', '').strip()
    description = request.form.get('description', '').strip()
    work_date_str = request.form.get('work_date')
    
    if not time_input:
        flash('Bitte Zeit angeben.' if lang == 'de' else 'Please specify time.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Parse time input (e.g., "2h", "30m", "1h 30m", "90")
    minutes = parse_time_input(time_input)
    if minutes <= 0:
        flash('Ungültige Zeitangabe. Verwende z.B. "2h", "30m", "1h 30m".' if lang == 'de' else 'Invalid time format. Use e.g. "2h", "30m", "1h 30m".', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Parse work date
    work_date = datetime.utcnow().date()
    if work_date_str:
        try:
            work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Create worklog entry
    worklog = Worklog(
        issue_id=issue.id,
        author_id=current_user.id,
        time_spent=minutes,
        work_date=work_date,
        description=description
    )
    db.session.add(worklog)
    
    # Log activity - worklog added
    log_activity(issue, 'worklog', details=worklog.time_spent_display)
    
    # Update issue time tracking
    issue.time_spent = (issue.time_spent or 0) + minutes
    issue.updated_at = datetime.utcnow()
    
    # Update remaining estimate if set
    if issue.remaining_estimate:
        issue.remaining_estimate = max(0, issue.remaining_estimate - minutes)
    
    db.session.commit()
    
    flash(f'{worklog.time_spent_display} protokolliert.' if lang == 'de' else f'{worklog.time_spent_display} logged.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/worklog/<int:worklog_id>/delete', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def worklog_delete(project_id, issue_key, worklog_id, project=None):
    """Delete a worklog entry"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    worklog = Worklog.query.filter_by(id=worklog_id, issue_id=issue.id).first_or_404()
    
    # Only author or admin can delete
    if worklog.author_id != current_user.id and not project.is_admin(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Subtract time from issue
    issue.time_spent = max(0, (issue.time_spent or 0) - worklog.time_spent)
    
    db.session.delete(worklog)
    db.session.commit()
    
    flash('Arbeitsprotokoll gelöscht.' if lang == 'de' else 'Worklog deleted.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


def parse_time_input(time_str):
    """Parse time input like '2h', '30m', '1h 30m', '90' (minutes)"""
    import re
    
    time_str = time_str.strip().lower()
    
    # Try hours and minutes pattern (1h 30m, 1h30m)
    match = re.match(r'(\d+)\s*h\s*(\d+)\s*m?', time_str)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    
    # Try hours only (2h)
    match = re.match(r'(\d+)\s*h', time_str)
    if match:
        return int(match.group(1)) * 60
    
    # Try minutes only (30m)
    match = re.match(r'(\d+)\s*m', time_str)
    if match:
        return int(match.group(1))
    
    # Try plain number (minutes)
    match = re.match(r'^(\d+)$', time_str)
    if match:
        return int(match.group(1))
    
    return 0


# =============================================================================
# ISSUE APPROVAL WORKFLOW ROUTES
# =============================================================================

@bp.route('/<int:project_id>/items/<issue_key>/reviewers', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def item_reviewers(project_id, issue_key, project=None):
    """Manage reviewers for an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check permission - only project admins/leads or issue reporter can add reviewers
    if not project.is_admin(current_user) and issue.reporter_id != current_user.id:
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    if request.method == 'POST':
        reviewer_ids = request.form.getlist('reviewer_ids')
        
        # Remove existing reviewers not in new list
        existing_reviewers = {r.user_id for r in issue.reviewers}
        new_reviewers = {int(id) for id in reviewer_ids if id}
        
        # Remove deselected reviewers
        for reviewer in issue.reviewers.all():
            if reviewer.user_id not in new_reviewers:
                removed_user = User.query.get(reviewer.user_id)
                log_activity(issue, 'reviewer_removed', 
                             details=removed_user.name if removed_user else str(reviewer.user_id))
                db.session.delete(reviewer)
        
        # Add new reviewers
        order = issue.reviewers.count() + 1
        for user_id in new_reviewers:
            if user_id not in existing_reviewers:
                reviewer = IssueReviewer(
                    issue_id=issue.id,
                    user_id=user_id,
                    order=order
                )
                db.session.add(reviewer)
                added_user = User.query.get(user_id)
                log_activity(issue, 'reviewer_added', 
                             details=added_user.name if added_user else str(user_id))
                order += 1
        
        db.session.commit()
        flash('Reviewer aktualisiert.' if lang == 'de' else 'Reviewers updated.', 'success')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Get project members for selection
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    current_reviewer_ids = [r.user_id for r in issue.reviewers]
    
    return render_template('projects/items/reviewers.html',
        project=project,
        issue=issue,
        members=members,
        current_reviewer_ids=current_reviewer_ids,
        lang=lang
    )


@bp.route('/<int:project_id>/items/<issue_key>/approve', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_approve(project_id, issue_key, project=None):
    """Approve an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check if issue is in review status
    if issue.status and issue.status.name not in ['In Prüfung', 'In Review'] and issue.status.name_en not in ['In Review']:
        flash('Issue muss sich im Status "In Prüfung" befinden, um genehmigt zu werden.' if lang == 'de' else 'Issue must be in "In Review" status to be approved.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check if user can review
    can_review, reason = issue.can_user_review(current_user)
    if not can_review:
        flash(reason, 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Get or create reviewer record
    reviewer = issue.reviewers.filter_by(user_id=current_user.id).first()
    if not reviewer:
        flash('Sie sind kein Reviewer für dieses Issue.' if lang == 'de' else 'You are not a reviewer for this issue.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    note = request.form.get('note', '')
    reviewer.approve(note)
    
    # Log the approval activity
    log_activity(issue, 'approved', details=note if note else None)
    
    # Check if all reviewers have approved
    status = issue.get_approval_status()
    if status['is_complete']:
        # Automatically set issue to Done status
        done_status = IssueStatus.query.filter_by(project_id=project_id, is_final=True).first()
        if done_status and issue.status_id != done_status.id:
            old_status_name = issue.status.get_name(lang) if issue.status else 'N/A'
            issue.status_id = done_status.id
            log_activity(issue, 'status_change', 
                        old_value=old_status_name, 
                        new_value=done_status.get_name(lang))
        flash('Alle Reviewer haben genehmigt! Issue wurde auf "Erledigt" gesetzt.' if lang == 'de' else 'All reviewers approved! Issue has been set to "Done".', 'success')
    else:
        flash(f"Ihre Genehmigung wurde gespeichert. Noch {status['pending_count']} Reviewer ausstehend." if lang == 'de' else f"Your approval was recorded. {status['pending_count']} reviewer(s) still pending.", 'success')
    
    db.session.commit()
    
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/reject', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_reject(project_id, issue_key, project=None):
    """Reject an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check if issue is in review status
    if issue.status and issue.status.name not in ['In Prüfung', 'In Review'] and issue.status.name_en not in ['In Review']:
        flash('Issue muss sich im Status "In Prüfung" befinden, um abgelehnt zu werden.' if lang == 'de' else 'Issue must be in "In Review" status to be rejected.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check if user can review
    can_review, reason = issue.can_user_review(current_user)
    if not can_review:
        flash(reason, 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Get reviewer record
    reviewer = issue.reviewers.filter_by(user_id=current_user.id).first()
    if not reviewer:
        flash('Sie sind kein Reviewer für dieses Issue.' if lang == 'de' else 'You are not a reviewer for this issue.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    note = request.form.get('note', '')
    if not note:
        flash('Bitte geben Sie einen Ablehnungsgrund an.' if lang == 'de' else 'Please provide a rejection reason.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    reviewer.reject(note)
    
    # Log the rejection activity
    log_activity(issue, 'rejected', details=note)
    
    db.session.commit()
    
    flash('Issue wurde abgelehnt.' if lang == 'de' else 'Issue has been rejected.', 'warning')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/reviewer/<int:reviewer_id>/remove', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_reviewer_remove(project_id, issue_key, reviewer_id, project=None):
    """Remove a reviewer from an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check permission
    if not project.is_admin(current_user) and issue.reporter_id != current_user.id:
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    reviewer = IssueReviewer.query.get_or_404(reviewer_id)
    if reviewer.issue_id != issue.id:
        flash('Ungültiger Reviewer.' if lang == 'de' else 'Invalid reviewer.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    removed_user = User.query.get(reviewer.user_id)
    log_activity(issue, 'reviewer_removed', 
                 details=removed_user.name if removed_user else str(reviewer.user_id))
    
    db.session.delete(reviewer)
    db.session.commit()
    
    flash('Reviewer entfernt.' if lang == 'de' else 'Reviewer removed.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


@bp.route('/<int:project_id>/items/<issue_key>/reviewer/add', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def item_reviewer_add(project_id, issue_key, project=None):
    """Add a reviewer to an issue"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    issue = Issue.query.filter_by(project_id=project_id, key=issue_key).first_or_404()
    
    # Check permission
    if not project.is_admin(current_user) and issue.reporter_id != current_user.id:
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    user_id = request.form.get('user_id')
    if not user_id:
        flash('Bitte wählen Sie einen Benutzer.' if lang == 'de' else 'Please select a user.', 'warning')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check if user has projects module enabled
    from models import UserModule, Module
    user_to_add = User.query.get(int(user_id))
    if user_to_add:
        projects_module = Module.query.filter_by(code='projects').first()
        if projects_module:
            has_access = UserModule.query.filter_by(
                user_id=int(user_id), 
                module_id=projects_module.id
            ).first()
            if not has_access:
                flash('Dieser Benutzer hat keinen Zugriff auf das Projektmanagement-Modul.' if lang == 'de' else 'This user does not have access to the Project Management module.', 'warning')
                return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Check if already a reviewer
    existing = issue.reviewers.filter_by(user_id=user_id).first()
    if existing:
        flash('Dieser Benutzer ist bereits Reviewer.' if lang == 'de' else 'This user is already a reviewer.', 'info')
        return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))
    
    # Add reviewer
    order = issue.reviewers.count() + 1
    reviewer = IssueReviewer(
        issue_id=issue.id,
        user_id=int(user_id),
        order=order
    )
    db.session.add(reviewer)
    
    # Log the activity
    added_user = User.query.get(int(user_id))
    log_activity(issue, 'reviewer_added', 
                 details=added_user.name if added_user else str(user_id))
    
    db.session.commit()
    
    flash('Reviewer hinzugefügt.' if lang == 'de' else 'Reviewer added.', 'success')
    return redirect(url_for('projects.item_detail', project_id=project_id, issue_key=issue_key))


# ============================================================================
# PM-8: Global Search API
# ============================================================================

@bp.route('/api/search')
@login_required
@projects_module_required
def api_search():
    """Global search API for issues across all accessible projects"""
    lang = session.get('lang', 'de')
    query = request.args.get('q', '').strip()
    project_id = request.args.get('project_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    if len(query) < 2:
        return jsonify({'results': [], 'total': 0})
    
    # Build base query - only search in projects user has access to
    if current_user.role == 'admin':
        accessible_projects = Project.query.filter_by(is_archived=False).all()
    else:
        accessible_projects = Project.query.filter(
            Project.id.in_(
                db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id)
            ),
            Project.is_archived == False
        ).all()
    
    project_ids = [p.id for p in accessible_projects]
    
    if not project_ids:
        return jsonify({'results': [], 'total': 0})
    
    # Build search query
    search_query = Issue.query.filter(
        Issue.project_id.in_(project_ids),
        Issue.is_archived == False
    )
    
    # Filter by specific project if provided
    if project_id and project_id in project_ids:
        search_query = search_query.filter(Issue.project_id == project_id)
    
    # Search in key, summary, description
    search_term = f'%{query}%'
    search_query = search_query.filter(
        db.or_(
            Issue.key.ilike(search_term),
            Issue.summary.ilike(search_term),
            Issue.description.ilike(search_term)
        )
    )
    
    # Get total count
    total = search_query.count()
    
    # Get results with limit
    issues = search_query.order_by(Issue.updated_at.desc()).limit(limit).all()
    
    # Format results
    results = []
    for issue in issues:
        results.append({
            'id': issue.id,
            'key': issue.key,
            'summary': issue.summary,
            'project_id': issue.project_id,
            'project_key': issue.project.key,
            'project_name': issue.project.name,
            'type': {
                'name': issue.item_type.name if issue.item_type else 'Task',
                'icon': issue.item_type.icon if issue.item_type else 'bi-check2-square',
                'color': issue.item_type.color if issue.item_type else '#0076A8'
            },
            'status': {
                'name': issue.status.name if issue.status else 'Open',
                'color': issue.status.color if issue.status else '#6c757d'
            },
            'priority': issue.priority,
            'assignee': {
                'id': issue.assignee.id if issue.assignee else None,
                'name': issue.assignee.name if issue.assignee else None
            },
            'url': url_for('projects.item_detail', project_id=issue.project_id, issue_key=issue.key)
        })
    
    return jsonify({
        'results': results,
        'total': total,
        'query': query
    })


@bp.route('/api/search/recent')
@login_required
@projects_module_required
def api_search_recent():
    """Get recently viewed/updated issues for quick access"""
    lang = session.get('lang', 'de')
    limit = request.args.get('limit', 5, type=int)
    
    # Get accessible project IDs
    if current_user.role == 'admin':
        project_ids = [p.id for p in Project.query.filter_by(is_archived=False).all()]
    else:
        project_ids = [
            m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()
        ]
    
    if not project_ids:
        return jsonify({'recent': []})
    
    # Get issues assigned to user or recently updated
    recent_issues = Issue.query.filter(
        Issue.project_id.in_(project_ids),
        Issue.is_archived == False,
        db.or_(
            Issue.assignee_id == current_user.id,
            Issue.reporter_id == current_user.id
        )
    ).order_by(Issue.updated_at.desc()).limit(limit).all()
    
    results = []
    for issue in recent_issues:
        results.append({
            'id': issue.id,
            'key': issue.key,
            'summary': issue.summary,
            'project_key': issue.project.key,
            'type_icon': issue.item_type.icon if issue.item_type else 'bi-check2-square',
            'type_color': issue.item_type.color if issue.item_type else '#0076A8',
            'url': url_for('projects.item_detail', project_id=issue.project_id, issue_key=issue.key)
        })
    
    return jsonify({'recent': results})


# =============================================================================
# ESTIMATION / SIZING
# =============================================================================

@bp.route('/<int:project_id>/estimation')
@login_required
@projects_module_required
@project_access_required
def estimation(project_id, project=None):
    """Estimation helper - size unestimated issues"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    # Get unestimated issues (no story points)
    unestimated = Issue.query.filter(
        Issue.project_id == project_id,
        Issue.is_archived == False,
        db.or_(Issue.story_points == None, Issue.story_points == 0)
    ).order_by(Issue.backlog_position, Issue.created_at.desc()).all()
    
    # Get recently estimated issues for reference
    estimated = Issue.query.filter(
        Issue.project_id == project_id,
        Issue.is_archived == False,
        Issue.story_points != None,
        Issue.story_points > 0
    ).order_by(Issue.updated_at.desc()).limit(10).all()
    
    # Get estimation scale config
    scale_config = project.get_estimation_scale_config()
    
    return render_template('projects/estimation.html',
        project=project,
        unestimated_issues=unestimated,
        estimated_issues=estimated,
        scale_config=scale_config,
        lang=lang
    )


@bp.route('/<int:project_id>/estimation/update', methods=['POST'])
@login_required
@projects_module_required
@project_access_required
def estimation_update(project_id, project=None):
    """Update story points for an issue via AJAX"""
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_manage_issues(current_user):
        return jsonify({'success': False, 'error': 'No permission'}), 403
    
    data = request.get_json()
    issue_id = data.get('issue_id')
    story_points = data.get('story_points')
    
    if not issue_id:
        return jsonify({'success': False, 'error': 'Missing issue_id'}), 400
    
    issue = Issue.query.filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        return jsonify({'success': False, 'error': 'Issue not found'}), 404
    
    try:
        issue.story_points = float(story_points) if story_points else None
        issue.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'issue_key': issue.key,
            'story_points': issue.story_points
        })
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid story points value'}), 400


@bp.route('/<int:project_id>/settings/estimation', methods=['GET', 'POST'])
@login_required
@projects_module_required
@project_access_required
def project_estimation_settings(project_id, project=None):
    """Configure project estimation scale"""
    lang = session.get('lang', 'de')
    
    if project is None:
        project = Project.query.get_or_404(project_id)
    
    if not project.can_user_edit(current_user):
        flash('Keine Berechtigung.' if lang == 'de' else 'No permission.', 'danger')
        return redirect(url_for('projects.project_detail', project_id=project_id))
    
    if request.method == 'POST':
        scale = request.form.get('estimation_scale', 'fibonacci')
        project.estimation_scale = scale
        
        # Handle custom values
        if scale == 'custom':
            custom_values = []
            labels = request.form.getlist('custom_label[]')
            points = request.form.getlist('custom_points[]')
            descriptions = request.form.getlist('custom_description[]')
            
            for i, label in enumerate(labels):
                if label.strip():
                    try:
                        pts = float(points[i]) if i < len(points) else i + 1
                    except:
                        pts = i + 1
                    custom_values.append({
                        'label': label.strip(),
                        'points': pts,
                        'description': {'de': descriptions[i] if i < len(descriptions) else '', 'en': ''}
                    })
            project.estimation_values = custom_values
        
        db.session.commit()
        flash('Schätzskala aktualisiert.' if lang == 'de' else 'Estimation scale updated.', 'success')
        return redirect(url_for('projects.project_estimation_settings', project_id=project_id))
    
    return render_template('projects/settings/estimation.html',
        project=project,
        lang=lang
    )


def register_routes(blueprint):
    """Register all routes - called from module __init__"""
    pass  # Routes are already registered via decorators
