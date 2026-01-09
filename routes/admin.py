"""
Admin Routes Blueprint

Handles administrative routes:
- Admin dashboard
- User management
- Entity management
- Team management
- Category management
- Module management
- Presets management

Note: This blueprint contains the core admin functionality.
Additional admin routes remain in app.py for gradual migration.
"""

from datetime import date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from flask_login import login_required, current_user

from extensions import db
from models import (
    User, Entity, Team, TaskCategory, TaskPreset, Task,
    Module, UserModule, UserEntity, EntityAccessLevel, UserRole, AuditLog
)
from translations import get_translation as t

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Administrator-Berechtigung erforderlich.' if session.get('lang', 'de') == 'de' else 'Administrator permission required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


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
# ADMIN DASHBOARD
# ============================================================================

@admin_bp.route('')
@admin_required
def dashboard():
    """Admin dashboard with system statistics"""
    # Scope task queries to current tenant
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    
    stats = {
        'users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'entities': Entity.query.filter_by(is_active=True).count(),
        'categories': TaskCategory.query.filter_by(is_active=True).count(),
        'tax_types': TaskCategory.query.filter_by(is_active=True).count(),  # Legacy alias
        'tasks_total': Task.query.filter(tenant_filter).count(),
        'tasks_overdue': Task.query.filter(tenant_filter, Task.due_date < date.today(), Task.status != 'completed').count(),
        'tasks_completed': Task.query.filter(tenant_filter, Task.status == 'completed').count(),
        'presets': TaskPreset.query.filter_by(is_active=True).count(),
        'modules': Module.query.filter_by(is_active=True).count(),
    }
    return render_template('admin/dashboard.html', stats=stats)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_bp.route('/users')
@admin_required
def users():
    """User management list"""
    users = User.query.order_by(User.name).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def user_new():
    """Create new user"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        role = request.form.get('role', 'preparer')
        password = request.form.get('password', '')
        
        if User.query.filter_by(email=email).first():
            flash('E-Mail-Adresse bereits vorhanden.', 'danger')
        elif not email or not name or not password:
            flash('Bitte füllen Sie alle Pflichtfelder aus.', 'warning')
        else:
            user = User(email=email, name=name, role=role, is_active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            log_action('CREATE', 'User', user.id, user.email)
            flash(f'Benutzer {name} wurde erstellt.', 'success')
            return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', user=None, roles=UserRole)


@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        user.role = request.form.get('role', 'preparer')
        user.is_active = request.form.get('is_active') == 'on'
        
        new_password = request.form.get('password', '')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        log_action('UPDATE', 'User', user.id, user.email)
        flash(f'Benutzer {user.name} wurde aktualisiert.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', user=user, roles=UserRole)


# ============================================================================
# ENTITY MANAGEMENT
# ============================================================================

@admin_bp.route('/entities')
@admin_required
def entities():
    """Entity management list"""
    entities = Entity.query.order_by(Entity.name).all()
    return render_template('admin/entities.html', entities=entities)


@admin_bp.route('/entities/new', methods=['GET', 'POST'])
@admin_required
def entity_new():
    """Create new entity"""
    if request.method == 'POST':
        name_de = request.form.get('name_de', '').strip()
        name_en = request.form.get('name_en', '').strip()
        short_name = request.form.get('short_name', '').strip()
        country = request.form.get('country', 'DE').strip().upper()
        group_id = request.form.get('group_id', type=int)
        
        if not name_de or not name_en:
            flash('Name (DE/EN) ist erforderlich.', 'warning')
        else:
            entity = Entity(
                name=name_de,
                name_de=name_de,
                name_en=name_en,
                short_name=short_name or None,
                country=country, 
                group_id=group_id if group_id else None,
                is_active=True
            )
            db.session.add(entity)
            db.session.commit()
            log_action('CREATE', 'Entity', entity.id, entity.name)
            flash(f'Gesellschaft {name_de} wurde erstellt.', 'success')
            return redirect(url_for('admin.entities'))
    
    parent_entities = Entity.query.filter_by(is_active=True).order_by(Entity.name).all()
    return render_template('admin/entity_form.html', entity=None, parent_entities=parent_entities)


@admin_bp.route('/entities/<int:entity_id>', methods=['GET', 'POST'])
@admin_required
def entity_edit(entity_id):
    """Edit entity"""
    entity = Entity.query.get_or_404(entity_id)
    
    if request.method == 'POST':
        entity.name_de = request.form.get('name_de', '').strip()
        entity.name_en = request.form.get('name_en', '').strip()
        entity.name = entity.name_de
        entity.short_name = request.form.get('short_name', '').strip() or None
        entity.country = request.form.get('country', 'DE').strip().upper()
        group_id = request.form.get('group_id', type=int)
        entity.group_id = group_id if group_id and group_id != entity.id else None
        entity.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        log_action('UPDATE', 'Entity', entity.id, entity.name)
        flash(f'Gesellschaft {entity.name} wurde aktualisiert.', 'success')
        return redirect(url_for('admin.entities'))
    
    parent_entities = Entity.query.filter(Entity.id != entity_id, Entity.is_active == True).order_by(Entity.name).all()
    return render_template('admin/entity_form.html', entity=entity, parent_entities=parent_entities)


@admin_bp.route('/entities/<int:entity_id>/delete', methods=['POST'])
@admin_required
def entity_delete(entity_id):
    """Delete entity (soft delete)"""
    entity = Entity.query.get_or_404(entity_id)
    entity.is_active = False
    db.session.commit()
    log_action('DELETE', 'Entity', entity.id, entity.name)
    flash(f'Gesellschaft {entity.name} wurde deaktiviert.', 'success')
    return redirect(url_for('admin.entities'))


# ============================================================================
# TEAM MANAGEMENT
# ============================================================================

@admin_bp.route('/teams')
@admin_required
def teams():
    """Team management list"""
    teams = Team.query.order_by(Team.name).all()
    return render_template('admin/teams.html', teams=teams)


@admin_bp.route('/teams/new', methods=['GET', 'POST'])
@admin_required
def team_new():
    """Create new team"""
    if request.method == 'POST':
        name_de = request.form.get('name_de', '').strip()
        name_en = request.form.get('name_en', '').strip()
        description_de = request.form.get('description_de', '').strip()
        description_en = request.form.get('description_en', '').strip()
        color = request.form.get('color', '#4A90D9').strip()
        manager_id = request.form.get('manager_id', type=int)
        member_ids = request.form.getlist('members', type=int)
        
        if Team.query.filter_by(name=name_de).first():
            flash('Teamname bereits vorhanden.', 'danger')
        elif not name_de or not name_en:
            flash('Teamname (DE/EN) ist erforderlich.', 'warning')
        else:
            team = Team(
                name=name_de,
                name_de=name_de,
                name_en=name_en,
                description=description_de or None,
                description_de=description_de or None,
                description_en=description_en or None,
                color=color,
                manager_id=manager_id if manager_id else None,
                is_active=True
            )
            db.session.add(team)
            db.session.flush()
            
            for user_id in member_ids:
                user = User.query.get(user_id)
                if user:
                    team.add_member(user)
            
            db.session.commit()
            log_action('CREATE', 'Team', team.id, team.name)
            flash(f'Team "{name_de}" wurde erstellt.', 'success')
            return redirect(url_for('admin.teams'))
    
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return render_template('admin/team_form.html', team=None, users=users)


@admin_bp.route('/teams/<int:team_id>', methods=['GET', 'POST'])
@admin_required
def team_edit(team_id):
    """Edit team"""
    team = Team.query.get_or_404(team_id)
    
    if request.method == 'POST':
        name_de = request.form.get('name_de', '').strip()
        name_en = request.form.get('name_en', '').strip()
        
        existing = Team.query.filter(Team.name == name_de, Team.id != team_id).first()
        if existing:
            flash('Teamname bereits vorhanden.', 'danger')
        elif not name_de or not name_en:
            flash('Teamname (DE/EN) ist erforderlich.', 'warning')
        else:
            team.name = name_de
            team.name_de = name_de
            team.name_en = name_en
            team.description = request.form.get('description_de', '').strip() or None
            team.description_de = request.form.get('description_de', '').strip() or None
            team.description_en = request.form.get('description_en', '').strip() or None
            team.color = request.form.get('color', '#4A90D9').strip()
            team.manager_id = request.form.get('manager_id', type=int) or None
            team.is_active = request.form.get('is_active') == 'on'
            
            new_member_ids = set(request.form.getlist('members', type=int))
            current_member_ids = set(m.id for m in team.members.all())
            
            for user_id in current_member_ids - new_member_ids:
                user = User.query.get(user_id)
                if user:
                    team.remove_member(user)
            
            for user_id in new_member_ids - current_member_ids:
                user = User.query.get(user_id)
                if user:
                    team.add_member(user)
            
            db.session.commit()
            log_action('UPDATE', 'Team', team.id, team.name)
            flash(f'Team "{team.name}" wurde aktualisiert.', 'success')
            return redirect(url_for('admin.teams'))
    
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return render_template('admin/team_form.html', team=team, users=users)


@admin_bp.route('/teams/<int:team_id>/delete', methods=['POST'])
@admin_required
def team_delete(team_id):
    """Delete team (soft delete)"""
    team = Team.query.get_or_404(team_id)
    team.is_active = False
    db.session.commit()
    log_action('DELETE', 'Team', team.id, team.name)
    flash(f'Team "{team.name}" wurde deaktiviert.', 'success')
    return redirect(url_for('admin.teams'))


# ============================================================================
# CATEGORY MANAGEMENT
# ============================================================================

@admin_bp.route('/categories')
@admin_required
def categories():
    """Category management list"""
    categories = TaskCategory.query.order_by(TaskCategory.code).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/tax-types')
@admin_required
def tax_types():
    """Legacy redirect to categories"""
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def category_new():
    """Create new category"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name_de = request.form.get('name_de', '').strip()
        name_en = request.form.get('name_en', '').strip()
        description_de = request.form.get('description_de', '').strip()
        description_en = request.form.get('description_en', '').strip()
        color = request.form.get('color', '#6c757d').strip()
        icon = request.form.get('icon', 'bi-folder').strip()
        
        if TaskCategory.query.filter_by(code=code).first():
            flash('Code bereits vorhanden.', 'danger')
        elif not code or not name_de or not name_en:
            flash('Code und Name (DE/EN) sind erforderlich.', 'warning')
        else:
            category = TaskCategory(
                code=code, 
                name=name_de,
                name_de=name_de,
                name_en=name_en,
                description=description_de or None,
                description_de=description_de or None,
                description_en=description_en or None,
                color=color,
                icon=icon,
                is_active=True
            )
            db.session.add(category)
            db.session.commit()
            log_action('CREATE', 'TaskCategory', category.id, category.code)
            flash(f'Kategorie {code} wurde erstellt.', 'success')
            return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', category=None)


@admin_bp.route('/categories/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def category_edit(category_id):
    """Edit category"""
    category = TaskCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name_de = request.form.get('name_de', '').strip()
        category.name_en = request.form.get('name_en', '').strip()
        category.name = category.name_de
        category.description_de = request.form.get('description_de', '').strip() or None
        category.description_en = request.form.get('description_en', '').strip() or None
        category.description = category.description_de
        category.color = request.form.get('color', '#6c757d').strip()
        category.icon = request.form.get('icon', 'bi-folder').strip()
        category.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        log_action('UPDATE', 'Category', category.id, category.code)
        flash(f'Kategorie {category.code} wurde aktualisiert.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', category=category)


# ============================================================================
# MODULE MANAGEMENT
# ============================================================================

@admin_bp.route('/modules')
@admin_required
def modules():
    """Module management"""
    modules = Module.query.order_by(Module.nav_order, Module.code).all()
    lang = session.get('lang', 'de')
    return render_template('admin/modules.html', modules=modules, lang=lang)


@admin_bp.route('/modules/<int:module_id>/toggle', methods=['POST'])
@admin_required
def module_toggle(module_id):
    """Toggle module active status"""
    module = Module.query.get_or_404(module_id)
    lang = session.get('lang', 'de')
    
    if module.is_core:
        flash('Kernmodule können nicht deaktiviert werden.' if lang == 'de' else 'Core modules cannot be disabled.', 'warning')
        return redirect(url_for('admin.modules'))
    
    module.is_active = not module.is_active
    db.session.commit()
    
    status = 'aktiviert' if module.is_active else 'deaktiviert'
    status_en = 'enabled' if module.is_active else 'disabled'
    flash(f'Modul {module.get_name(lang)} {status if lang == "de" else status_en}.', 'success')
    return redirect(url_for('admin.modules'))


# ============================================================================
# USER MODULE MANAGEMENT
# ============================================================================

@admin_bp.route('/users/<int:user_id>/modules')
@admin_required
def user_modules(user_id):
    """Manage user module assignments"""
    user = User.query.get_or_404(user_id)
    modules = Module.query.filter_by(is_active=True).order_by(Module.nav_order).all()
    lang = session.get('lang', 'de')
    
    # Get user's assigned module IDs
    assigned_module_ids = {um.module_id for um in user.user_modules}
    
    return render_template('admin/user_modules.html', 
                          user=user, 
                          modules=modules, 
                          assigned_module_ids=assigned_module_ids,
                          lang=lang)


@admin_bp.route('/users/<int:user_id>/modules', methods=['POST'])
@admin_required
def user_modules_save(user_id):
    """Save user module assignments"""
    user = User.query.get_or_404(user_id)
    lang = session.get('lang', 'de')
    
    # Get selected module IDs from form
    selected_module_ids = set(map(int, request.form.getlist('modules')))
    
    # Get current assignments
    current_module_ids = {um.module_id for um in user.user_modules}
    
    # Remove unselected modules
    for um in list(user.user_modules):
        if um.module_id not in selected_module_ids and not um.module.is_core:
            db.session.delete(um)
    
    # Add new modules
    for module_id in selected_module_ids:
        if module_id not in current_module_ids:
            module = Module.query.get(module_id)
            if module and module.is_active:
                um = UserModule(
                    user_id=user_id,
                    module_id=module_id,
                    granted_by_id=current_user.id
                )
                db.session.add(um)
    
    db.session.commit()
    
    flash('Modulzuweisungen gespeichert.' if lang == 'de' else 'Module assignments saved.', 'success')
    return redirect(url_for('admin.user_modules', user_id=user_id))


# ============================================================================
# USER ENTITY PERMISSIONS
# ============================================================================

@admin_bp.route('/users/<int:user_id>/entities')
@admin_required
def user_entities(user_id):
    """Manage entity access for a user"""
    user = User.query.get_or_404(user_id)
    entities = Entity.query.filter_by(is_active=True).order_by(Entity.name).all()
    lang = session.get('lang', 'de')
    
    # Get current permissions as dict for easy lookup
    current_perms = {p.entity_id: p for p in user.entity_permissions}
    
    return render_template('admin/user_entities.html', 
                           user=user, 
                           entities=entities,
                           current_perms=current_perms,
                           access_levels=EntityAccessLevel,
                           lang=lang,
                           t=t)


@admin_bp.route('/users/<int:user_id>/entities', methods=['POST'])
@admin_required
def user_entities_save(user_id):
    """Save entity permissions for a user"""
    user = User.query.get_or_404(user_id)
    
    # Get all entity IDs that were submitted
    entity_ids = request.form.getlist('entity_ids', type=int)
    
    # Get existing permissions
    existing_perms = {p.entity_id: p for p in user.entity_permissions}
    
    # Track which entities we've processed
    processed_ids = set()
    
    for entity_id in entity_ids:
        access_level = request.form.get(f'access_level_{entity_id}', 'view')
        inherit = request.form.get(f'inherit_{entity_id}') == 'on'
        
        if entity_id in existing_perms:
            # Update existing permission
            perm = existing_perms[entity_id]
            perm.access_level = access_level
            perm.inherit_to_children = inherit
        else:
            # Create new permission
            perm = UserEntity(
                user_id=user.id,
                entity_id=entity_id,
                access_level=access_level,
                inherit_to_children=inherit,
                granted_by_id=current_user.id
            )
            db.session.add(perm)
        
        processed_ids.add(entity_id)
    
    # Remove permissions that weren't in the form (unchecked)
    for entity_id, perm in existing_perms.items():
        if entity_id not in processed_ids:
            db.session.delete(perm)
    
    db.session.commit()
    log_action('UPDATE', 'UserEntity', user.id, f'Entity permissions for {user.email}')
    
    lang = session.get('lang', 'de')
    if lang == 'de':
        flash(f'Berechtigungen für {user.name} wurden gespeichert.', 'success')
    else:
        flash(f'Permissions for {user.name} saved.', 'success')
    
    return redirect(url_for('admin.user_entities', user_id=user_id))


@admin_bp.route('/entities/<int:entity_id>/users')
@admin_required
def entity_users(entity_id):
    """View users with access to an entity"""
    entity = Entity.query.get_or_404(entity_id)
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    lang = session.get('lang', 'de')
    
    # Get current permissions as dict for easy lookup
    current_perms = {p.user_id: p for p in entity.user_permissions}
    
    return render_template('admin/entity_users.html',
                           entity=entity,
                           users=users,
                           current_perms=current_perms,
                           access_levels=EntityAccessLevel,
                           lang=lang,
                           t=t)


@admin_bp.route('/entities/<int:entity_id>/users', methods=['POST'])
@admin_required
def entity_users_save(entity_id):
    """Save user permissions for an entity"""
    entity = Entity.query.get_or_404(entity_id)
    
    # Get all user IDs that were submitted
    user_ids = request.form.getlist('user_ids', type=int)
    
    # Get existing permissions
    existing_perms = {p.user_id: p for p in entity.user_permissions}
    
    # Track which users we've processed
    processed_ids = set()
    
    for user_id in user_ids:
        access_level = request.form.get(f'access_level_{user_id}', 'view')
        inherit = request.form.get(f'inherit_{user_id}') == 'on'
        
        if user_id in existing_perms:
            # Update existing permission
            perm = existing_perms[user_id]
            perm.access_level = access_level
            perm.inherit_to_children = inherit
        else:
            # Create new permission
            perm = UserEntity(
                user_id=user_id,
                entity_id=entity.id,
                access_level=access_level,
                inherit_to_children=inherit,
                granted_by_id=current_user.id
            )
            db.session.add(perm)
        
        processed_ids.add(user_id)
    
    # Remove permissions that weren't in the form (unchecked)
    for user_id, perm in existing_perms.items():
        if user_id not in processed_ids:
            db.session.delete(perm)
    
    db.session.commit()
    log_action('UPDATE', 'UserEntity', entity.id, f'User permissions for {entity.name}')
    
    lang = session.get('lang', 'de')
    if lang == 'de':
        flash(f'Berechtigungen für {entity.name} wurden gespeichert.', 'success')
    else:
        flash(f'Permissions for {entity.name} saved.', 'success')
    
    return redirect(url_for('admin.entity_users', entity_id=entity_id))
