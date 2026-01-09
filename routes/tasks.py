"""
Tasks Routes Blueprint

Handles all task-related routes:
- Task list with filters
- Task CRUD (create, read, update, delete)
- Status transitions and multi-stage approval workflow
- Archive and restore
- Evidence (file uploads and links)
- Comments
"""

import os
import uuid
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify, send_file, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    Task, TaskTemplate, TaskCategory, TaskEvidence, TaskPreset, TaskReviewer,
    Entity, User, Team, Comment, Notification, AuditLog
)
from services import NotificationService, ApprovalService, ApprovalResult, build_task_query
from translations import TRANSLATIONS
from middleware.tenant import (
    get_task_or_404_scoped, get_evidence_or_404_scoped, get_comment_or_404_scoped
)

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


def log_action(action, entity_type, entity_id, entity_name, old_value=None, new_value=None):
    """Helper to log actions to audit log.
    
    Note: Does NOT commit - caller should commit after main operation completes
    to ensure transactional integrity.
    """
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


def emit_notifications_to_users(notifications, lang='de'):
    """Emit socket notifications via app-level function"""
    if hasattr(current_app, 'emit_notifications_to_users'):
        current_app.emit_notifications_to_users(notifications, lang)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())


# ============================================================================
# TASK LIST & DETAIL
# ============================================================================

@tasks_bp.route('')
@login_required
def task_list():
    """Task list with filters"""
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if session.get('lang', 'de') == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    entity_filter = request.args.get('entity', type=int)
    tax_type_filter = request.args.get('tax_type', type=int)
    year_filter = request.args.get('year', type=int, default=date.today().year)
    show_archived = request.args.get('show_archived', 'false') == 'true'
    
    # Build access-scoped query using shared helper
    filters = {
        'status': status_filter or None,
        'entity_id': entity_filter,
        'tax_type_id': tax_type_filter,
        'year': year_filter
    }
    query = build_task_query(current_user, filters=filters, show_archived=show_archived)
    
    # Order by due date
    tasks = query.order_by(Task.due_date).all()
    
    # Get filter options - show only accessible entities for non-admins
    if current_user.is_admin() or current_user.is_manager():
        entities = Entity.query.filter_by(is_active=True).order_by(Entity.name).all()
    else:
        entities = current_user.get_accessible_entities('view')
    
    categories = TaskCategory.query.filter_by(is_active=True).order_by(TaskCategory.code).all()
    years = db.session.query(Task.year).distinct().order_by(Task.year.desc()).all()
    years = [y[0] for y in years]
    
    # Get users for bulk assign modal
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    
    return render_template('tasks/list.html', 
                         tasks=tasks, 
                         entities=entities,
                         categories=categories,
                         tax_types=categories,  # Legacy alias
                         years=years,
                         users=users,
                         current_filters={
                             'status': status_filter,
                             'entity': entity_filter,
                             'category': tax_type_filter,
                             'tax_type': tax_type_filter  # Legacy alias
                         })


@tasks_bp.route('/<int:task_id>')
@login_required
def task_detail(task_id):
    """Task detail view"""
    task = get_task_or_404_scoped(task_id)
    
    # Check access (admin, manager, owner, or any assigned reviewer)
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    # Get audit log for this task
    audit_logs = AuditLog.query.filter_by(
        entity_type='Task', 
        entity_id=task.id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return render_template('tasks/detail.html', task=task, audit_logs=audit_logs)


# ============================================================================
# TASK CREATE & EDIT
# ============================================================================

@tasks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def task_create():
    """Create a new task"""
    from services import email_service
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        entity_id = request.form.get('entity_id', type=int)
        template_id = request.form.get('template_id', type=int) or None
        due_date_str = request.form.get('due_date', '')
        year = request.form.get('year', type=int, default=date.today().year)
        period = request.form.get('period', '').strip()
        owner_id = request.form.get('owner_id', type=int) or None
        owner_team_id = request.form.get('owner_team_id', type=int) or None
        reviewer_ids = request.form.getlist('reviewer_ids', type=int)
        reviewer_team_id = request.form.get('reviewer_team_id', type=int) or None
        
        # Validate required fields
        errors = []
        if not title:
            errors.append('Titel ist erforderlich.')
        if not entity_id:
            errors.append('Gesellschaft ist erforderlich.')
        if not due_date_str:
            errors.append('Fälligkeitsdatum ist erforderlich.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                
                task = Task(
                    title=title,
                    description=description,
                    entity_id=entity_id,
                    template_id=template_id,
                    due_date=due_date,
                    year=year,
                    period=period,
                    owner_id=owner_id,
                    owner_team_id=owner_team_id,
                    reviewer_team_id=reviewer_team_id,
                    status='draft'
                )
                db.session.add(task)
                db.session.flush()  # Get task ID for reviewers
                
                # Add multiple reviewers
                if reviewer_ids:
                    task.set_reviewers(reviewer_ids)
                
                db.session.commit()
                
                log_action('CREATE', 'Task', task.id, task.title)
                db.session.commit()
                
                # Send notifications
                lang = session.get('lang', 'de')
                notifications = []
                
                # Notify owner if assigned
                if owner_id and owner_id != current_user.id:
                    notifications.append(
                        NotificationService.notify_task_assigned(task, owner_id, current_user.id)
                    )
                
                # Notify reviewers
                for reviewer_id in reviewer_ids:
                    if reviewer_id != current_user.id:
                        notifications.append(
                            NotificationService.notify_reviewer_added(task, reviewer_id, current_user.id)
                        )
                
                if notifications:
                    db.session.commit()
                    emit_notifications_to_users(notifications, lang)
                
                # Send email notifications (async-safe, won't block if email disabled)
                if owner_id and owner_id != current_user.id:
                    owner = User.query.get(owner_id)
                    if owner:
                        email_service.send_task_assigned(task, owner, current_user, lang)
                
                for reviewer_id in reviewer_ids:
                    if reviewer_id != current_user.id:
                        reviewer = User.query.get(reviewer_id)
                        if reviewer:
                            email_service.send_task_assigned(task, reviewer, current_user, lang)
                
                flash('Aufgabe erfolgreich erstellt.', 'success')
                return redirect(url_for('tasks.task_detail', task_id=task.id))
                
            except ValueError:
                flash('Ungültiges Datumsformat.', 'danger')
    
    # GET request - show form
    entities = Entity.query.filter_by(is_active=True).order_by(Entity.name).all()
    templates = TaskTemplate.query.filter_by(is_active=True).order_by(TaskTemplate.keyword).all()
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    presets = TaskPreset.query.filter_by(is_active=True).order_by(TaskPreset.category, TaskPreset.title).all()
    
    return render_template('tasks/form.html',
                         task=None,
                         entities=entities,
                         templates=templates,
                         users=users,
                         teams=teams,
                         presets=presets,
                         current_year=date.today().year)


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def task_edit(task_id):
    """Edit an existing task"""
    
    task = get_task_or_404_scoped(task_id)
    
    # Check permission
    if not (current_user.is_admin() or current_user.is_manager() or task.owner_id == current_user.id):
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if request.method == 'POST':
        old_values = f"title={task.title}, due_date={task.due_date}"
        
        task.title = request.form.get('title', '').strip()
        task.description = request.form.get('description', '').strip()
        task.entity_id = request.form.get('entity_id', type=int)
        task.template_id = request.form.get('template_id', type=int) or None
        task.year = request.form.get('year', type=int, default=date.today().year)
        task.period = request.form.get('period', '').strip()
        task.owner_id = request.form.get('owner_id', type=int) or None
        task.owner_team_id = request.form.get('owner_team_id', type=int) or None
        task.reviewer_team_id = request.form.get('reviewer_team_id', type=int) or None
        
        # Handle multiple reviewers
        old_reviewer_ids = set(tr.user_id for tr in task.reviewers)
        reviewer_ids = request.form.getlist('reviewer_ids', type=int)
        new_reviewer_ids = set(reviewer_ids)
        task.set_reviewers(reviewer_ids)
        
        due_date_str = request.form.get('due_date', '')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ungültiges Datumsformat.', 'danger')
                return redirect(url_for('tasks.task_edit', task_id=task_id))
        
        db.session.commit()
        
        new_values = f"title={task.title}, due_date={task.due_date}"
        log_action('UPDATE', 'Task', task.id, task.title, old_values, new_values)
        db.session.commit()
        
        # Notify newly added reviewers
        lang = session.get('lang', 'de')
        notifications = []
        added_reviewer_ids = new_reviewer_ids - old_reviewer_ids
        for reviewer_id in added_reviewer_ids:
            if reviewer_id != current_user.id:
                notifications.append(
                    NotificationService.notify_reviewer_added(task, reviewer_id, current_user.id)
                )
        
        if notifications:
            db.session.commit()
            emit_notifications_to_users(notifications, lang)
        
        flash('Aufgabe erfolgreich aktualisiert.', 'success')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    # GET request
    entities = Entity.query.filter_by(is_active=True).order_by(Entity.name).all()
    templates = TaskTemplate.query.filter_by(is_active=True).order_by(TaskTemplate.keyword).all()
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    teams = Team.query.filter_by(is_active=True).order_by(Team.name).all()
    
    return render_template('tasks/form.html',
                         task=task,
                         entities=entities,
                         templates=templates,
                         users=users,
                         teams=teams,
                         current_year=date.today().year)


# ============================================================================
# STATUS & APPROVAL WORKFLOW
# ============================================================================

@tasks_bp.route('/<int:task_id>/status', methods=['POST'])
@login_required
def task_change_status(task_id):
    """Change task status with multi-stage approval workflow"""
    from services import email_service
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if session.get('lang', 'de') == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))
    
    task = get_task_or_404_scoped(task_id)
    new_status = request.form.get('status')
    note = request.form.get('note', '').strip()
    
    # Check if transition is allowed
    if not task.can_transition_to(new_status, current_user):
        flash('Diese Statusänderung ist nicht erlaubt.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    try:
        old_status = task.transition_to(new_status, current_user, note)
        db.session.commit()
        log_action('STATUS_CHANGE', 'Task', task.id, task.title, old_status, new_status)
        db.session.commit()
        
        # Send notifications for status change
        lang = session.get('lang', 'de')
        notifications = []
        
        # Notify owner about status changes (if not the one who made the change)
        if task.owner_id and task.owner_id != current_user.id:
            notifications.append(
                NotificationService.notify_status_changed(task, task.owner_id, old_status, new_status, current_user.id)
            )
        
        # Notify reviewers when task is submitted for review
        if new_status == 'submitted':
            for tr in task.reviewers:
                if tr.user_id != current_user.id:
                    notifications.append(
                        NotificationService.create(
                            user_id=tr.user_id,
                            notification_type='review_requested',
                            title_de=f'Review angefordert: {task.title}',
                            title_en=f'Review requested: {task.title}',
                            message_de='Die Aufgabe wurde zur Prüfung eingereicht.',
                            message_en='The task has been submitted for review.',
                            entity_type='task',
                            entity_id=task.id,
                            actor_id=current_user.id
                        )
                    )
        
        if notifications:
            db.session.commit()
            emit_notifications_to_users(notifications, lang)
        
        # Send email notifications for status change
        if task.owner_id and task.owner_id != current_user.id:
            owner = User.query.get(task.owner_id)
            if owner:
                email_service.send_status_changed(task, owner, old_status, new_status, lang)
        
        # Email reviewers when task is submitted for review
        if new_status == 'submitted':
            for tr in task.reviewers:
                if tr.user_id != current_user.id:
                    email_service.send_status_changed(task, tr.user, old_status, new_status, lang)
        
        # Status-specific messages
        status_messages = {
            'submitted': 'Aufgabe eingereicht. Wartet auf Prüfung.',
            'in_review': 'Aufgabe wird geprüft.',
            'approved': 'Aufgabe genehmigt. Kann abgeschlossen werden.',
            'completed': 'Aufgabe erfolgreich abgeschlossen.',
            'rejected': 'Aufgabe zur Überarbeitung zurückgewiesen.',
            'draft': 'Aufgabe zurück in Bearbeitung.',
        }
        flash(status_messages.get(new_status, f'Status geändert: {old_status} → {new_status}'), 'success')
        
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id))


@tasks_bp.route('/<int:task_id>/reviewer-action', methods=['POST'])
@login_required
def task_reviewer_action(task_id):
    """Handle individual reviewer approval/rejection using ApprovalService"""
    from services import email_service
    
    task = get_task_or_404_scoped(task_id)
    action = request.form.get('action')
    note = request.form.get('note', '').strip()
    
    lang = session.get('lang', 'de')
    
    if action == 'approve':
        result, message = ApprovalService.approve(task, current_user, note)
        db.session.commit()
        
        if result == ApprovalResult.ALL_APPROVED:
            log_action('REVIEWER_APPROVE', 'Task', task.id, task.title, 
                       f'Reviewer: {current_user.name}', 'Final approval')
            log_action('STATUS_CHANGE', 'Task', task.id, task.title, 'in_review', 'approved')
            db.session.commit()
            
            # Notify owner that task is fully approved
            if task.owner_id and task.owner_id != current_user.id:
                notification = NotificationService.notify_task_approved(task, task.owner_id, current_user.id, note)
                db.session.commit()
                emit_notifications_to_users([notification], lang)
                
                # Send email notification
                owner = User.query.get(task.owner_id)
                if owner:
                    email_service.send_status_changed(task, owner, 'in_review', 'approved', lang)
            
            flash('Alle Prüfer haben genehmigt. Aufgabe ist nun genehmigt.', 'success')
        elif result == ApprovalResult.SUCCESS:
            log_action('REVIEWER_APPROVE', 'Task', task.id, task.title, 
                       f'Reviewer: {current_user.name}', note or 'No note')
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'danger')
    
    elif action == 'reject':
        result, message = ApprovalService.reject(task, current_user, note)
        db.session.commit()
        
        if result == ApprovalResult.TASK_REJECTED:
            log_action('REVIEWER_REJECT', 'Task', task.id, task.title, 
                       f'Reviewer: {current_user.name}', note or 'No note')
            log_action('STATUS_CHANGE', 'Task', task.id, task.title, 'in_review', 'rejected')
            db.session.commit()
            
            # Notify owner that task was rejected
            if task.owner_id and task.owner_id != current_user.id:
                notification = NotificationService.notify_task_rejected(task, task.owner_id, current_user.id, note)
                db.session.commit()
                emit_notifications_to_users([notification], lang)
                
                # Send email notification
                owner = User.query.get(task.owner_id)
                if owner:
                    email_service.send_status_changed(task, owner, 'in_review', 'rejected', lang)
            
            flash('Aufgabe wurde von Ihnen abgelehnt und zur Überarbeitung zurückgewiesen.', 'warning')
        else:
            flash(message, 'danger')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id))


# ============================================================================
# ARCHIVE & RESTORE
# ============================================================================

@tasks_bp.route('/<int:task_id>/archive', methods=['POST'])
@login_required
def task_archive(task_id):
    """Archive a task (soft-delete)"""
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if session.get('lang', 'de') == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))

    task = get_task_or_404_scoped(task_id)
    lang = session.get('lang', 'de')
    
    # Only admin, manager, or owner can archive
    if not (current_user.is_admin() or current_user.is_manager() or current_user.id == task.owner_id):
        flash('Keine Berechtigung zum Archivieren.' if lang == 'de' else 'No permission to archive.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if task.is_archived:
        flash('Aufgabe ist bereits archiviert.' if lang == 'de' else 'Task is already archived.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    reason = request.form.get('reason', '')
    task.archive(current_user, reason)
    db.session.commit()
    
    log_action('ARCHIVE', 'Task', task.id, task.title, 'active', 'archived')
    db.session.commit()
    
    flash('Aufgabe wurde archiviert.' if lang == 'de' else 'Task has been archived.', 'success')
    return redirect(url_for('tasks.task_list'))


@tasks_bp.route('/<int:task_id>/restore', methods=['POST'])
@login_required
def task_restore(task_id):
    """Restore a task from archive"""
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if session.get('lang', 'de') == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))

    task = get_task_or_404_scoped(task_id)
    lang = session.get('lang', 'de')
    
    # Only admin or manager can restore
    if not (current_user.is_admin() or current_user.is_manager()):
        flash('Keine Berechtigung zum Wiederherstellen.' if lang == 'de' else 'No permission to restore.', 'danger')
        return redirect(url_for('tasks.task_archive_list'))
    
    if not task.is_archived:
        flash('Aufgabe ist nicht archiviert.' if lang == 'de' else 'Task is not archived.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    task.restore()
    db.session.commit()
    
    log_action('RESTORE', 'Task', task.id, task.title, 'archived', 'active')
    db.session.commit()
    
    flash('Aufgabe wurde wiederhergestellt.' if lang == 'de' else 'Task has been restored.', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task_id))


@tasks_bp.route('/archive')
@login_required
def task_archive_list():
    """View archived tasks"""
    lang = session.get('lang', 'de')
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if lang == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))
    
    # Build query for archived tasks - scoped to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    query = Task.query.filter(tenant_filter, Task.is_archived == True)
    
    # Non-admin/manager users only see their own archived tasks
    if not (current_user.is_admin() or current_user.is_manager()):
        accessible_entity_ids = current_user.get_accessible_entity_ids()
        query = query.filter(Task.entity_id.in_(accessible_entity_ids))
    
    # Filters
    entity_id = request.args.get('entity_id', type=int)
    year = request.args.get('year', type=int)
    status = request.args.get('status')
    
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    if year:
        query = query.filter_by(year=year)
    if status:
        query = query.filter_by(status=status)
    
    # Order by archived date, most recent first
    query = query.order_by(Task.archived_at.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items
    
    # Get filter options
    entities = Entity.query.order_by(Entity.name).all()
    years = db.session.query(Task.year).filter_by(is_archived=True).distinct().order_by(Task.year.desc()).all()
    years = [y[0] for y in years]
    
    return render_template('tasks/archive.html',
                           tasks=tasks,
                           pagination=pagination,
                           entities=entities,
                           years=years,
                           current_filters={
                               'entity_id': entity_id,
                               'year': year,
                               'status': status
                           },
                           t=lambda key: TRANSLATIONS.get(key, {}).get(lang, key),
                           lang=lang)


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def task_permanent_delete(task_id):
    """Permanently delete an archived task (admin only)"""
    lang = session.get('lang', 'de')
    if not g.tenant:
        flash('Bitte wählen Sie zuerst einen Mandanten.' if lang == 'de' else 'Please select a tenant first.', 'warning')
        return redirect(url_for('auth.select_tenant'))
    
    if not current_user.is_admin():
        flash('Nur Administratoren können Aufgaben endgültig löschen.' if lang == 'de' else 'Only administrators can permanently delete tasks.', 'danger')
        return redirect(url_for('tasks.task_archive_list'))
    
    task = get_task_or_404_scoped(task_id)
    
    if not task.is_archived:
        flash('Nur archivierte Aufgaben können endgültig gelöscht werden.' if lang == 'de' else 'Only archived tasks can be permanently deleted.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    task_title = task.title
    task_id_log = task.id
    
    # Delete related records first
    TaskEvidence.query.filter_by(task_id=task_id).delete()
    Comment.query.filter_by(task_id=task_id).delete()
    TaskReviewer.query.filter_by(task_id=task_id).delete()
    Notification.query.filter(Notification.entity_type == 'task', Notification.entity_id == task_id).delete()
    
    db.session.delete(task)
    db.session.commit()
    
    log_action('DELETE', 'Task', task_id_log, task_title, 'archived', 'deleted')
    db.session.commit()
    
    flash(f'Aufgabe "{task_title}" wurde endgültig gelöscht.' if lang == 'de' else f'Task "{task_title}" has been permanently deleted.', 'success')
    return redirect(url_for('tasks.task_archive_list'))


# ============================================================================
# EVIDENCE (File Upload & Links)
# ============================================================================

@tasks_bp.route('/<int:task_id>/evidence/upload', methods=['POST'])
@login_required
def task_upload_evidence(task_id):
    """Upload file evidence to a task"""
    task = get_task_or_404_scoped(task_id)
    
    # Check permission (admin, manager, owner, or any assigned reviewer)
    if not (current_user.is_admin() or current_user.is_manager() or 
            current_user.id == task.owner_id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung zum Hochladen.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if 'file' not in request.files:
        flash('Keine Datei ausgewählt.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('Keine Datei ausgewählt.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if file and allowed_file(file.filename):
        # Secure the filename and make it unique
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Create task-specific folder
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'task_{task_id}')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create evidence record
        evidence = TaskEvidence(
            task_id=task_id,
            evidence_type='file',
            filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            uploaded_by_id=current_user.id
        )
        db.session.add(evidence)
        db.session.commit()
        
        log_action('UPLOAD', 'Task', task_id, task.title, None, f'Datei: {original_filename}')
        db.session.commit()
        flash(f'Datei "{original_filename}" erfolgreich hochgeladen.', 'success')
    else:
        allowed = ', '.join(current_app.config.get('ALLOWED_EXTENSIONS', []))
        flash(f'Dateityp nicht erlaubt. Erlaubte Formate: {allowed}', 'danger')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id) + '#evidence')


@tasks_bp.route('/<int:task_id>/evidence/link', methods=['POST'])
@login_required
def task_add_link(task_id):
    """Add link evidence to a task"""
    task = get_task_or_404_scoped(task_id)
    
    # Check permission (admin, manager, owner, or any assigned reviewer)
    if not (current_user.is_admin() or current_user.is_manager() or 
            current_user.id == task.owner_id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    url = request.form.get('url', '').strip()
    link_title = request.form.get('link_title', '').strip()
    
    if not url:
        flash('URL ist erforderlich.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    evidence = TaskEvidence(
        task_id=task_id,
        evidence_type='link',
        url=url,
        link_title=link_title or url[:100],
        uploaded_by_id=current_user.id
    )
    db.session.add(evidence)
    db.session.commit()
    
    log_action('LINK_ADD', 'Task', task_id, task.title, None, f'Link: {link_title or url[:50]}')
    db.session.commit()
    flash('Link erfolgreich hinzugefügt.', 'success')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id) + '#evidence')


@tasks_bp.route('/<int:task_id>/evidence/<int:evidence_id>/download')
@login_required
def task_download_evidence(task_id, evidence_id):
    """Download file evidence"""
    task = get_task_or_404_scoped(task_id)
    evidence = get_evidence_or_404_scoped(evidence_id, task_id=task_id)
    
    # Check access - admin, manager, owner, or reviewer only
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung für diesen Download.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    if evidence.evidence_type != 'file':
        flash('Nur Dateien können heruntergeladen werden.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if not os.path.exists(evidence.file_path):
        flash('Datei nicht gefunden.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    return send_file(evidence.file_path, as_attachment=True, download_name=evidence.filename)


@tasks_bp.route('/<int:task_id>/evidence/<int:evidence_id>/preview')
@login_required
def task_preview_evidence(task_id, evidence_id):
    """Preview file evidence inline (for images, PDFs, text files)"""
    task = get_task_or_404_scoped(task_id)
    evidence = get_evidence_or_404_scoped(evidence_id, task_id=task_id)
    
    # Check access - admin, manager, owner, or reviewer only
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung für diese Vorschau.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    if evidence.evidence_type != 'file':
        flash('Nur Dateien können angezeigt werden.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    if not os.path.exists(evidence.file_path):
        flash('Datei nicht gefunden.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    # Determine mimetype for inline display
    mimetype = evidence.mime_type or 'application/octet-stream'
    
    return send_file(evidence.file_path, mimetype=mimetype, as_attachment=False, download_name=evidence.filename)


@tasks_bp.route('/<int:task_id>/evidence/<int:evidence_id>/delete', methods=['POST'])
@login_required
def task_delete_evidence(task_id, evidence_id):
    """Delete evidence from a task"""
    task = get_task_or_404_scoped(task_id)
    evidence = get_evidence_or_404_scoped(evidence_id, task_id=task_id)
    
    # Check permission - only uploader, owner, or admin can delete
    if not (current_user.is_admin() or current_user.id == evidence.uploaded_by_id or 
            current_user.id == task.owner_id):
        flash('Keine Berechtigung zum Löschen.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    # Delete file if exists
    if evidence.evidence_type == 'file' and evidence.file_path:
        if os.path.exists(evidence.file_path):
            os.remove(evidence.file_path)
    
    description = evidence.filename or evidence.url
    db.session.delete(evidence)
    db.session.commit()
    
    log_action('EVIDENCE_DELETE', 'Task', task_id, task.title, f'Nachweis: {description[:50]}', None)
    db.session.commit()
    flash('Nachweis gelöscht.', 'success')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id) + '#evidence')


# ============================================================================
# COMMENTS
# ============================================================================

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@login_required
def task_add_comment(task_id):
    """Add a comment to a task"""
    task = get_task_or_404_scoped(task_id)
    
    # Check access - admin, manager, owner, or reviewer only
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung zum Kommentieren dieser Aufgabe.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    text = request.form.get('text', '').strip()
    
    if not text:
        flash('Kommentar darf nicht leer sein.', 'warning')
        return redirect(url_for('tasks.task_detail', task_id=task_id) + '#comments')
    
    comment = Comment(
        task_id=task_id,
        text=text,
        created_by_id=current_user.id
    )
    db.session.add(comment)
    db.session.commit()
    
    log_action('COMMENT', 'Task', task_id, task.title, None, text[:100] + ('...' if len(text) > 100 else ''))
    db.session.commit()
    
    # Notify relevant users about the comment
    lang = session.get('lang', 'de')
    notifications = []
    notified_users = set()
    
    # Notify task owner
    if task.owner_id and task.owner_id != current_user.id:
        notifications.append(
            NotificationService.notify_comment_added(task, comment, task.owner_id, current_user.id)
        )
        notified_users.add(task.owner_id)
    
    # Notify reviewers
    for tr in task.reviewers:
        if tr.user_id != current_user.id and tr.user_id not in notified_users:
            notifications.append(
                NotificationService.notify_comment_added(task, comment, tr.user_id, current_user.id)
            )
            notified_users.add(tr.user_id)
    
    if notifications:
        db.session.commit()
        emit_notifications_to_users(notifications, lang)
    
    flash('Kommentar hinzugefügt.', 'success')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id) + '#comments')


@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def task_delete_comment(task_id, comment_id):
    """Delete a comment from a task"""
    task = get_task_or_404_scoped(task_id)
    
    # First check task access - admin, manager, owner, or reviewer only
    # (prevents leaking comment existence to unauthorized users)
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung für diese Aufgabe.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    comment = get_comment_or_404_scoped(comment_id, task_id=task_id)
    
    # Then check delete permission - only comment author, task owner, or admin can delete
    if not (current_user.is_admin() or current_user.id == comment.created_by_id or 
            current_user.id == task.owner_id):
        flash('Keine Berechtigung zum Löschen.', 'danger')
        return redirect(url_for('tasks.task_detail', task_id=task_id))
    
    # Save text before deletion for audit log
    comment_text = comment.text[:50] + ('...' if len(comment.text) > 50 else '')
    
    db.session.delete(comment)
    db.session.commit()
    
    log_action('COMMENT_DELETE', 'Task', task_id, task.title, comment_text, None)
    db.session.commit()
    flash('Kommentar gelöscht.', 'success')
    
    return redirect(url_for('tasks.task_detail', task_id=task_id) + '#comments')


# ============================================================================
# EXPORT ROUTES
# ============================================================================

@tasks_bp.route('/export/excel')
@login_required
def export_excel():
    """Export filtered task list to Excel"""
    from flask import Response
    from services import ExportService
    
    lang = session.get('lang', 'de')
    
    # Get filter parameters (same as task_list)
    status_filter = request.args.get('status', '')
    entity_filter = request.args.get('entity', type=int)
    tax_type_filter = request.args.get('tax_type', type=int)
    year_filter = request.args.get('year', type=int, default=date.today().year)
    
    # Build access-scoped query using shared helper
    filters = {
        'status': status_filter or None,
        'entity_id': entity_filter,
        'tax_type_id': tax_type_filter,
        'year': year_filter
    }
    query = build_task_query(current_user, filters=filters, show_archived=True)
    
    tasks = query.order_by(Task.due_date).all()
    
    # Generate Excel
    excel_bytes = ExportService.export_tasks_to_excel(tasks, lang)
    
    filename = f"aufgaben_{date.today().strftime('%Y%m%d')}.xlsx" if lang == 'de' else f"tasks_{date.today().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@tasks_bp.route('/export/summary')
@login_required
def export_summary():
    """Export summary report to Excel"""
    from flask import Response
    from services import ExportService
    
    lang = session.get('lang', 'de')
    
    # Apply year filter if provided
    year_filter = request.args.get('year', type=int, default=date.today().year)
    
    # Build access-scoped query using shared helper
    filters = {'year': year_filter} if year_filter else {}
    query = build_task_query(current_user, filters=filters, show_archived=True)
    
    tasks = query.all()
    
    # Generate report
    excel_bytes = ExportService.export_summary_report(tasks, lang)
    
    filename = f"bericht_{year_filter}.xlsx" if lang == 'de' else f"report_{year_filter}.xlsx"
    
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@tasks_bp.route('/<int:task_id>/export/pdf')
@login_required
def export_pdf(task_id):
    """Export single task to PDF"""
    from flask import Response
    from services import ExportService
    
    task = get_task_or_404_scoped(task_id)
    lang = session.get('lang', 'de')
    
    # Check access
    if not (current_user.is_admin() or current_user.is_manager() or 
            task.owner_id == current_user.id or task.is_reviewer(current_user)):
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('tasks.task_list'))
    
    # Generate PDF
    pdf_bytes = ExportService.export_task_to_pdf(task, lang)
    
    # Sanitize filename
    safe_title = "".join(c for c in task.title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    filename = f"{safe_title}_{date.today().strftime('%Y%m%d')}.pdf"
    
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
