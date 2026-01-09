"""
Flask Extensions
Central initialization of all Flask extensions.
"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Database
db = SQLAlchemy()

# CSRF Protection
csrf = CSRFProtect()


# Rate Limiting - Exempt ZAP scanner for pen testing
def rate_limit_key_func():
    """Custom key function that exempts ZAP scanner from rate limits."""
    from flask import request, session
    from flask_login import current_user
    
    # Exempt ZAP scanner by User-Agent
    user_agent = request.headers.get('User-Agent', '')
    if 'ZAP' in user_agent or 'zap' in user_agent.lower():
        return None  # None = exempt from rate limiting
    
    # Exempt pentest user by form data (for login)
    if request.method == 'POST' and request.form:
        email = request.form.get('email', '')
        if email == 'pentest@zap.local':
            return None
    
    # Exempt authenticated pentest user (for all requests after login)
    try:
        if current_user.is_authenticated and current_user.email == 'pentest@zap.local':
            return None
    except Exception:
        pass  # current_user not available outside app context
    
    return get_remote_address()


limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=["200 per minute"],  # Default rate limit
    storage_uri="memory://",  # Use in-memory storage
)

# Migrations
migrate = Migrate()

# SocketIO for real-time features
socketio = SocketIO()

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an.'
login_manager.login_message_category = 'warning'
