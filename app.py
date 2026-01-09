"""
ProjectOps
Project & Task Management Platform for enterprises.
"""
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, redirect, url_for, flash, request, session, g, current_app
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room

from config import config
from extensions import db, migrate, socketio, login_manager, csrf, limiter
from models import User, AuditLog
from translations import get_translation as t
from services import ApprovalService, WorkflowService, email_service
from modules import ModuleRegistry
from middleware import load_tenant_context
from middleware.tenant import inject_tenant_context

# Import modules to register them
import modules.core
import modules.tasks
import modules.projects

# Import project models for migrations
from modules.projects.models import (
    Project, ProjectMember, ProjectRole,
    IssueType, IssueStatus, Issue, Sprint,
    StatusCategory, ProjectMethodology,
    create_default_issue_types, create_default_issue_statuses
)


# ============================================================================
# WSGI MIDDLEWARE
# ============================================================================

class ServerHeaderMiddleware:
    """WSGI middleware to mask the Server header after Werkzeug sets it."""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Filter out Server header and add our own
            headers = [(name, value) for name, value in headers if name.lower() != 'server']
            headers.append(('Server', 'ProjectOps'))
            return start_response(status, headers, exc_info)
        return self.app(environ, custom_start_response)


# ============================================================================
# APP INITIALIZATION
# ============================================================================

def get_file_icon(filename):
    """Return Bootstrap icon class based on file extension"""
    if not filename or '.' not in filename:
        return 'bi-file-earmark'
    ext = filename.rsplit('.', 1)[1].lower()
    icons = {
        'pdf': 'bi-file-earmark-pdf text-danger',
        'doc': 'bi-file-earmark-word text-primary',
        'docx': 'bi-file-earmark-word text-primary',
        'xls': 'bi-file-earmark-excel text-success',
        'xlsx': 'bi-file-earmark-excel text-success',
        'csv': 'bi-file-earmark-spreadsheet text-success',
        'txt': 'bi-file-earmark-text',
        'png': 'bi-file-earmark-image text-info',
        'jpg': 'bi-file-earmark-image text-info',
        'jpeg': 'bi-file-earmark-image text-info',
        'gif': 'bi-file-earmark-image text-info',
        'zip': 'bi-file-earmark-zip text-warning',
    }
    return icons.get(ext, 'bi-file-earmark')


def inject_globals():
    """Inject global variables into all templates"""
    lang = session.get('lang', current_app.config.get('DEFAULT_LANGUAGE', 'de'))
    
    # Get user's accessible modules for navigation
    user_modules = []
    if current_user.is_authenticated:
        user_modules = ModuleRegistry.get_user_modules(current_user)
    
    return {
        'app_name': current_app.config.get('APP_NAME', 'MyApp'),
        'app_version': current_app.config.get('APP_VERSION', '1.0.0'),
        'current_year': datetime.now().year,
        'lang': lang,
        't': lambda key: t(key, lang),
        'get_file_icon': get_file_icon,
        'ApprovalService': ApprovalService,
        'WorkflowService': WorkflowService,
        'user_modules': user_modules,
        'ModuleRegistry': ModuleRegistry
    }


def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize SocketIO with CORS restrictions
    # Production: same-origin only; Development: allow all for local testing
    if app.config.get('DEBUG'):
        cors_origins = "*"
    else:
        cors_origins_env = app.config.get('CORS_ORIGINS', '')
        if cors_origins_env:
            cors_origins = [origin.strip() for origin in cors_origins_env.split(',')]
        else:
            cors_origins = None  # Same-origin only
    socketio.init_app(app, cors_allowed_origins=cors_origins, async_mode='threading')
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize rate limiting
    limiter.init_app(app)
    
    # Initialize Login Manager
    login_manager.init_app(app)

    @app.before_request
    def generate_csp_nonce():
        """Generate a unique nonce for each request for CSP."""
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.context_processor
    def inject_csp_nonce():
        """Make csp_nonce available in all templates."""
        return {'csp_nonce': getattr(g, 'csp_nonce', '')}

    # Register tenant middleware and context processors
    app.before_request(load_tenant_context)
    app.context_processor(inject_tenant_context)
    app.context_processor(inject_globals)

    @app.after_request
    def add_security_headers(response):
        """Apply baseline security headers to all responses."""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            # Note: Server header is masked by ServerHeaderMiddleware at WSGI level
        }
        for header, value in security_headers.items():
            response.headers[header] = value  # Force set to override defaults

        csp = app.config.get('CONTENT_SECURITY_POLICY')
        if csp is None:
            # Fallback nonce generation for error/abort paths that skip before_request
            nonce = getattr(g, 'csp_nonce', None)
            if not nonce:
                nonce = secrets.token_urlsafe(16)
                g.csp_nonce = nonce
            csp = (
                "default-src 'self'; "
                "img-src 'self' data:; "
                f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                "style-src-attr 'unsafe-inline'; "
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://cdn.socket.io; "
                "script-src-attr 'unsafe-inline'; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self' ws://localhost:* ws://127.0.0.1:* wss://localhost:* wss://127.0.0.1:* https://cdn.jsdelivr.net https://cdn.socket.io; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "object-src 'none'"
            )
        if csp:
            response.headers.setdefault('Content-Security-Policy', csp)

        return response
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Initialize module system
    ModuleRegistry.init_app(app)
    
    # Wire notification helper to app for access via current_app in blueprints
    app.emit_notifications_to_users = lambda notifications, lang='de': emit_notifications_to_users(notifications, lang)
    
    # Register admin blueprints
    from admin import admin_tenants
    app.register_blueprint(admin_tenants)
    
    # Register route blueprints (Phase 4 refactoring)
    from routes import auth_bp, main_bp, tasks_bp, admin_bp, api_bp, presets_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(presets_bp)
    
    # Add legacy route aliases for template compatibility
    @app.endpoint('index')
    def index_alias():
        return redirect(url_for('main.index'))
    
    @app.endpoint('login')
    def login_alias():
        return redirect(url_for('auth.login'))
    
    @app.endpoint('logout')
    def logout_alias():
        return redirect(url_for('auth.logout'))
    
    return app


app = create_app()

# Apply WSGI middleware to mask server version
app.wsgi_app = ServerHeaderMiddleware(app.wsgi_app)

# Initialize email service
email_service.init_app(app)


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection - join user's personal room"""
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('connected', {'user_id': current_user.id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')


def emit_notification(user_id: int, notification, lang: str = 'de'):
    """
    Emit real-time notification to user via WebSocket.
    
    Args:
        user_id: Target user ID
        notification: Notification object
        lang: Language for localized content
    """
    socketio.emit('notification', notification.to_dict(lang), room=f'user_{user_id}')


def emit_notifications_to_users(notifications: list, lang: str = 'de'):
    """
    Emit notifications to multiple users.
    
    Args:
        notifications: List of Notification objects
        lang: Language for localized content
    """
    for notification in notifications:
        emit_notification(notification.user_id, notification, lang)


# ============================================================================
# DECORATORS
# ============================================================================

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Keine Berechtigung für diese Aktion.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


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
# RUN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Use socketio.run() for WebSocket support with threading mode
    # Hot reload works with use_reloader=True in threading mode
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=True, allow_unsafe_werkzeug=True)
