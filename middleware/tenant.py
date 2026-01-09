"""
Multi-Tenancy Middleware

Handles tenant context loading, access control, and query scoping.
"""
from functools import wraps
from flask import g, session, redirect, url_for, flash, request, current_app
from flask_login import current_user


def get_current_tenant():
    """Get the current tenant from Flask g object"""
    return getattr(g, 'tenant', None)


def get_current_tenant_role():
    """Get the current user's role in the active tenant"""
    return getattr(g, 'tenant_role', None)


def load_tenant_context():
    """
    Load tenant context for each request.
    Call this in before_request hook.
    
    Sets:
        g.tenant - Current Tenant object or None
        g.tenant_role - User's role in current tenant ('admin', 'manager', 'member', 'viewer')
        g.is_superadmin_mode - True if super-admin is viewing another tenant
    """
    from models import Tenant, TenantMembership
    
    g.tenant = None
    g.tenant_role = None
    g.is_superadmin_mode = False
    
    # Skip for unauthenticated users
    if not current_user.is_authenticated:
        return
    
    # Super-Admin handling
    if current_user.is_superadmin:
        tenant_id = session.get('current_tenant_id') or current_user.current_tenant_id
        if tenant_id:
            g.tenant = Tenant.query.get(tenant_id)
            if g.tenant:
                # Super-admin always has 'admin' role equivalent
                g.tenant_role = 'admin'
                g.is_superadmin_mode = True
        return
    
    # Regular user: Get tenant from session or default
    tenant_id = session.get('current_tenant_id')
    
    if tenant_id:
        # Verify user still has access to this tenant
        if current_user.can_access_tenant(tenant_id):
            tenant = Tenant.query.get(tenant_id)
            if tenant and tenant.is_active:
                g.tenant = tenant
                g.tenant_role = current_user.get_role_in_tenant(tenant_id)
            else:
                # Tenant deactivated, clear session
                session.pop('current_tenant_id', None)
                tenant_id = None
        else:
            # No longer has access, clear session
            session.pop('current_tenant_id', None)
            tenant_id = None
    
    # Fallback to default tenant if none set
    if not tenant_id and not g.tenant:
        default = current_user.default_tenant
        if default and default.is_active:
            g.tenant = default
            session['current_tenant_id'] = default.id
            g.tenant_role = current_user.get_role_in_tenant(default.id)


def tenant_required(f):
    """
    Decorator: Route requires an active tenant context.
    
    Redirects to tenant selection if no tenant is active.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not g.tenant:
            # Check if user has any tenants
            if current_user.is_superadmin:
                flash('Bitte wählen Sie einen Mandanten aus.', 'warning')
                return redirect(url_for('admin.tenant_list'))
            
            if not current_user.tenants:
                flash('Sie sind keinem Mandanten zugeordnet. Bitte kontaktieren Sie den Administrator.', 'error')
                return redirect(url_for('logout'))
            
            flash('Bitte wählen Sie einen Mandanten aus.', 'warning')
            return redirect(url_for('select_tenant'))
        
        if not g.tenant.is_active and not current_user.is_superadmin:
            flash('Dieser Mandant ist deaktiviert.', 'error')
            session.pop('current_tenant_id', None)
            return redirect(url_for('select_tenant'))
        
        return f(*args, **kwargs)
    return decorated_function


def tenant_admin_required(f):
    """
    Decorator: Route requires tenant admin role.
    
    User must be admin in the current tenant, or a super-admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not g.tenant:
            flash('Kein Mandant ausgewählt.', 'warning')
            return redirect(url_for('select_tenant'))
        
        if g.tenant_role != 'admin' and not current_user.is_superadmin:
            flash('Sie benötigen Admin-Rechte für diese Aktion.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def tenant_manager_required(f):
    """
    Decorator: Route requires tenant manager or admin role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not g.tenant:
            flash('Kein Mandant ausgewählt.', 'warning')
            return redirect(url_for('select_tenant'))
        
        if g.tenant_role not in ('admin', 'manager') and not current_user.is_superadmin:
            flash('Sie benötigen Manager-Rechte für diese Aktion.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    """
    Decorator: Route only for super-admins.
    
    Used for system-wide administration like tenant management.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not current_user.is_superadmin:
            flash('Diese Funktion ist nur für System-Administratoren.', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def can_edit_in_tenant():
    """Check if current user can edit (not viewer) in current tenant"""
    if current_user.is_superadmin:
        return True
    return g.tenant_role in ('admin', 'manager', 'member')


def can_manage_in_tenant():
    """Check if current user can manage (admin/manager) in current tenant"""
    if current_user.is_superadmin:
        return True
    return g.tenant_role in ('admin', 'manager')


def is_tenant_admin():
    """Check if current user is admin in current tenant"""
    if current_user.is_superadmin:
        return True
    return g.tenant_role == 'admin'


# =============================================================================
# QUERY SCOPING HELPERS
# =============================================================================

def get_task_or_404_scoped(task_id):
    """
    Fetch a Task by ID, enforcing tenant scope.
    
    Returns 404 if task doesn't exist OR belongs to different tenant.
    This prevents cross-tenant data leakage.
    
    Usage:
        task = get_task_or_404_scoped(task_id)
    """
    from flask import abort
    from models import Task
    
    if not g.tenant:
        abort(404)
    
    task = Task.query.filter_by(id=task_id, tenant_id=g.tenant.id).first()
    if not task:
        abort(404)
    return task


def get_task_scoped(task_id):
    """
    Fetch a Task by ID, enforcing tenant scope.
    
    Returns None if task doesn't exist OR belongs to different tenant.
    Use this in loops where 404 would be inappropriate.
    
    Usage:
        task = get_task_scoped(task_id)
        if task:
            # process task
    """
    from models import Task
    
    if not g.tenant:
        return None
    
    return Task.query.filter_by(id=task_id, tenant_id=g.tenant.id).first()


def get_evidence_or_404_scoped(evidence_id, task_id=None):
    """
    Fetch TaskEvidence by ID, enforcing tenant scope via task relationship.
    
    Optionally verifies evidence belongs to specific task.
    Returns 404 if evidence doesn't exist OR task belongs to different tenant.
    
    Usage:
        evidence = get_evidence_or_404_scoped(evidence_id)
        evidence = get_evidence_or_404_scoped(evidence_id, task_id=task.id)
    """
    from flask import abort
    from models import TaskEvidence, Task
    
    if not g.tenant:
        abort(404)
    
    # Join to Task to enforce tenant scoping
    query = TaskEvidence.query.join(Task).filter(
        TaskEvidence.id == evidence_id,
        Task.tenant_id == g.tenant.id
    )
    
    if task_id:
        query = query.filter(TaskEvidence.task_id == task_id)
    
    evidence = query.first()
    if not evidence:
        abort(404)
    return evidence


def get_comment_or_404_scoped(comment_id, task_id=None):
    """
    Fetch Comment by ID, enforcing tenant scope via task relationship.
    
    Optionally verifies comment belongs to specific task.
    Returns 404 if comment doesn't exist OR task belongs to different tenant.
    
    Usage:
        comment = get_comment_or_404_scoped(comment_id)
        comment = get_comment_or_404_scoped(comment_id, task_id=task.id)
    """
    from flask import abort
    from models import Comment, Task
    
    if not g.tenant:
        abort(404)
    
    # Join to Task to enforce tenant scoping
    query = Comment.query.join(Task).filter(
        Comment.id == comment_id,
        Task.tenant_id == g.tenant.id
    )
    
    if task_id:
        query = query.filter(Comment.task_id == task_id)
    
    comment = query.first()
    if not comment:
        abort(404)
    return comment


def get_project_or_404_scoped(project_id):
    """
    Fetch a Project by ID, enforcing tenant scope.
    
    Returns 404 if project doesn't exist OR belongs to different tenant.
    
    Usage:
        project = get_project_or_404_scoped(project_id)
    """
    from flask import abort
    from models import Project
    
    if not g.tenant:
        abort(404)
    
    project = Project.query.filter_by(id=project_id, tenant_id=g.tenant.id).first()
    if not project:
        abort(404)
    return project

def scope_query_to_tenant(query, model):
    """
    Filter a SQLAlchemy query to the current tenant.
    
    Usage:
        query = scope_query_to_tenant(Model.query, Model)
        
    Args:
        query: SQLAlchemy query object
        model: Model class with tenant_id column
    
    Returns:
        Filtered query
    """
    if not hasattr(model, 'tenant_id'):
        return query
    
    if not g.tenant:
        # No tenant context - return empty result
        return query.filter(False)
    
    return query.filter(model.tenant_id == g.tenant.id)


def get_tenant_filtered_query(model):
    """
    Get a query pre-filtered to current tenant.
    
    Usage:
        projects = get_tenant_filtered_query(Project).all()
    """
    return scope_query_to_tenant(model.query, model)


class TenantQueryMixin:
    """
    Mixin for models that adds tenant-scoped query methods.
    
    Usage:
        class Project(db.Model, TenantQueryMixin):
            tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
            ...
        
        # In routes:
        projects = Project.for_tenant().all()
    """
    
    @classmethod
    def for_tenant(cls, tenant_id=None):
        """Get query scoped to specified or current tenant"""
        tid = tenant_id or (g.tenant.id if g.tenant else None)
        if not tid:
            return cls.query.filter(False)
        return cls.query.filter(cls.tenant_id == tid)
    
    @classmethod
    def for_current_tenant(cls):
        """Get query scoped to current tenant (from g.tenant)"""
        if not g.tenant:
            return cls.query.filter(False)
        return cls.query.filter(cls.tenant_id == g.tenant.id)


# =============================================================================
# TEMPLATE HELPERS
# =============================================================================

def inject_tenant_context():
    """
    Template context processor for tenant information.
    
    Register with: app.context_processor(inject_tenant_context)
    
    Makes available in templates:
        - current_tenant: Current Tenant object
        - tenant_role: User's role in tenant
        - is_superadmin_mode: Super-admin viewing mode
        - can_edit: User can create/edit items
        - can_manage: User can manage settings
        - is_tenant_admin: User is tenant admin
    """
    return {
        'current_tenant': getattr(g, 'tenant', None),
        'tenant_role': getattr(g, 'tenant_role', None),
        'is_superadmin_mode': getattr(g, 'is_superadmin_mode', False),
        'can_edit': can_edit_in_tenant() if current_user.is_authenticated else False,
        'can_manage': can_manage_in_tenant() if current_user.is_authenticated else False,
        'is_tenant_admin': is_tenant_admin() if current_user.is_authenticated else False,
    }
