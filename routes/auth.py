"""
Authentication Routes Blueprint

Handles:
- Login/logout
- Tenant selection and switching
- Session management
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, limiter
from models import User, Tenant, AuditLog

auth_bp = Blueprint('auth', __name__)


def log_action(action, entity_type=None, entity_id=None, entity_name=None, old_value=None, new_value=None):
    """Log an action to the audit log"""
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr,
        user_agent=str(request.user_agent)[:500] if request.user_agent else None
    )
    db.session.add(log)
    db.session.commit()


# ============================================================================
# AUTH ROUTES
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limit login attempts
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Ihr Konto ist deaktiviert.', 'danger')
                return render_template('login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_action('LOGIN', 'User', user.id, user.email)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        
        flash('Ungültige Anmeldedaten.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    log_action('LOGOUT', 'User', current_user.id, current_user.email)
    logout_user()
    session.pop('current_tenant_id', None)
    flash('Sie wurden abgemeldet.', 'success')
    return redirect(url_for('main.index'))


# ============================================================================
# TENANT ROUTES
# ============================================================================

@auth_bp.route('/select-tenant')
@login_required
def select_tenant():
    """Show tenant selection page"""
    if current_user.is_superadmin:
        # Super-admins can see all tenants
        tenants = Tenant.query.filter_by(is_active=True, is_archived=False).order_by(Tenant.name).all()
    else:
        # Regular users see only their assigned tenants
        tenants = [m.tenant for m in current_user.memberships 
                   if m.tenant.is_active and not m.tenant.is_archived]
    
    return render_template('select_tenant.html', tenants=tenants)


@auth_bp.route('/switch-tenant/<int:tenant_id>', methods=['POST'])
@login_required
@limiter.limit("30 per minute")  # Rate limit tenant switching
def switch_tenant(tenant_id):
    """Switch to a different tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Verify access
    if not current_user.is_superadmin:
        if not current_user.can_access_tenant(tenant_id):
            flash('Sie haben keinen Zugriff auf diesen Mandanten.', 'error')
            return redirect(url_for('auth.select_tenant'))
    
    if not tenant.is_active and not current_user.is_superadmin:
        flash('Dieser Mandant ist deaktiviert.', 'error')
        return redirect(url_for('auth.select_tenant'))
    
    # Update session
    session['current_tenant_id'] = tenant_id
    
    # Update user's last tenant for persistence
    current_user.current_tenant_id = tenant_id
    db.session.commit()
    
    log_action('SWITCH_TENANT', 'Tenant', tenant_id, tenant.name)
    flash(f'Mandant gewechselt zu: {tenant.name}', 'success')
    
    # Redirect to dashboard or next page
    next_page = request.args.get('next') or request.form.get('next')
    return redirect(next_page or url_for('main.dashboard'))


@auth_bp.route('/api/switch-tenant/<int:tenant_id>', methods=['POST'])
@login_required
@limiter.limit("30 per minute")  # Rate limit tenant switching
def api_switch_tenant(tenant_id):
    """API endpoint for tenant switching (for AJAX calls)"""
    tenant = Tenant.query.get(tenant_id)
    
    if not tenant:
        return jsonify({'success': False, 'message': 'Mandant nicht gefunden'}), 404
    
    if not current_user.is_superadmin:
        if not current_user.can_access_tenant(tenant_id):
            return jsonify({'success': False, 'message': 'Kein Zugriff'}), 403
    
    if not tenant.is_active and not current_user.is_superadmin:
        return jsonify({'success': False, 'message': 'Mandant deaktiviert'}), 403
    
    session['current_tenant_id'] = tenant_id
    current_user.current_tenant_id = tenant_id
    db.session.commit()
    
    return jsonify({
        'success': True,
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'slug': tenant.slug
        }
    })
