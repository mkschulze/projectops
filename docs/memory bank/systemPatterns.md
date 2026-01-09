# System Patterns

> Architecture patterns, conventions, and implementation guidelines for Company ProjectOps

## Architecture Overview

### Application Factory Pattern

The application uses Flask's application factory pattern for flexibility and testability:

```python
# app.py
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    # from blueprints.auth import auth_bp
    # app.register_blueprint(auth_bp)
    
    return app

app = create_app()
```

### Blueprint Structure (Planned)

```python
# blueprints/tasks.py
from flask import Blueprint

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_bp.route('/')
@login_required
def task_list():
    # ...

@tasks_bp.route('/<int:task_id>')
@login_required
def task_detail(task_id):
    # ...
```

---

## Design Patterns

### Decorator Pattern for Authorization

```python
# Current implementation in app.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator that requires admin role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Zugriff verweigert.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Usage
@app.route('/admin/users')
@admin_required
def admin_users():
    # ...
```

### Extended RBAC Decorators (Planned)

```python
# utils/decorators.py
def role_required(*roles):
    """Decorator requiring one of the specified roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('Zugriff verweigert.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
@role_required('admin', 'reviewer', 'manager')
def complete_task(task_id):
    # ...
```

### Service Layer Pattern

```python
# services/task_service.py
class TaskService:
    """Business logic for task operations."""
    
    @staticmethod
    def change_status(task_id, new_status, user):
        """Change task status with validation and audit logging."""
        task = Task.query.get_or_404(task_id)
        
        # Validate transition
        if not TaskService._is_valid_transition(task.status, new_status):
            raise ValueError(f"Invalid transition: {task.status} → {new_status}")
        
        old_status = task.status
        task.status = new_status
        
        # Update timestamps
        if new_status == 'submitted':
            task.submitted_at = datetime.utcnow()
        elif new_status == 'completed':
            task.completed_at = datetime.utcnow()
        
        # Audit log
        AuditService.log_change(
            user=user,
            action='STATUS_CHANGE',
            object_type='task',
            object_id=task.id,
            old_value=old_status,
            new_value=new_status
        )
        
        db.session.commit()
        return task
```

---

## URL Structure

### Current Routes

| URL | Method | View Function | Auth |
|-----|--------|---------------|------|
| `/` | GET | `index` | No |
| `/login` | GET, POST | `login` | No |
| `/logout` | GET | `logout` | Yes |
| `/set_language/<lang>` | GET | `set_language` | No |
| `/admin/dashboard` | GET | `admin_dashboard` | Admin |
| `/admin/users` | GET | `admin_users` | Admin |

### Planned URL Structure

```
Authentication
  /login                    GET, POST   Login form
  /logout                   GET         Logout

Main
  /                         GET         Dashboard
  /calendar                 GET         Calendar view
  /calendar/<int:year>/<int:month>

Tasks
  /tasks                    GET         Task list
  /tasks/<int:id>           GET         Task detail
  /tasks/<int:id>/edit      GET, POST   Edit task
  /tasks/<int:id>/status    POST        Change status
  /tasks/<int:id>/evidence  POST        Upload evidence
  /tasks/<int:id>/comment   POST        Add comment

Admin
  /admin                    GET         Admin dashboard
  /admin/users              GET         User list
  /admin/users/new          GET, POST   Create user
  /admin/users/<int:id>     GET, POST   Edit user
  /admin/entities           GET         Entity list
  /admin/entities/new       GET, POST   Create entity
  /admin/entities/<int:id>  GET, POST   Edit entity
  /admin/tax-types          GET         Tax type list
  /admin/templates          GET         Template list
  /admin/import             GET, POST   Excel import

API (optional)
  /api/tasks                GET         Task list (JSON)
  /api/tasks/<int:id>       GET, PUT    Task operations
  /api/calendar-data        GET         Calendar events (JSON)
```

---

## Template Inheritance

### Hierarchy

```
base.html
├── index.html
├── login.html
├── dashboard.html (new)
├── calendar.html (new)
├── tasks/
│   ├── list.html
│   └── detail.html
├── admin/
│   ├── dashboard.html
│   ├── users.html
│   ├── entities.html
│   ├── tax_types.html
│   ├── templates.html
│   └── import.html
└── errors/
    ├── 404.html
    └── 500.html
```

### Base Template Blocks

```jinja2
{# base.html provides these blocks #}
{% block title %}{% endblock %}      {# Page title #}
{% block extra_css %}{% endblock %}  {# Additional CSS #}
{% block content %}{% endblock %}    {# Main content #}
{% block extra_js %}{% endblock %}   {# Additional JavaScript #}
```

### Example Child Template

```jinja2
{# templates/tasks/list.html #}
{% extends "base.html" %}

{% block title %}{{ t('tasks') }} - {{ app_name }}{% endblock %}

{% block extra_css %}
<style>
    .task-row:hover { background-color: var(--dtt-green-pale); }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <h1>{{ t('tasks') }}</h1>
    {# Task list content #}
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Task-specific JavaScript
</script>
{% endblock %}
```

---

## Database Relationships

### Current Models

```python
# models.py
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50))
    object_type = db.Column(db.String(50))
    object_id = db.Column(db.Integer)
    entity_name = db.Column(db.String(200))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
```

### Planned Model Relationships

```python
# Planned relationships for ProjectOps models

Entity (1) ─────< (N) Task
    │
    └── entity_id FK in tasks table

TaskTemplate (1) ─────< (N) Task
    │
    └── template_id FK in tasks table

TaxType (1) ─────< (N) TaskTemplate
    │
    └── tax_type_id FK in task_templates table

User (1) ─────< (N) Task (as owner)
    │
    └── owner_id FK in tasks table

User (1) ─────< (N) Task (as reviewer)
    │
    └── reviewer_id FK in tasks table

Task (1) ─────< (N) TaskEvidence
    │
    └── task_id FK in task_evidence table

Task (1) ─────< (N) Comment
    │
    └── task_id FK in comments table
```

---

## Session Management

### Language Preference

```python
# Stored in Flask session
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in app.config.get('SUPPORTED_LANGUAGES', ['de', 'en']):
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

# Accessed via context processor
@app.context_processor
def inject_globals():
    lang = session.get('lang', 'de')
    return {
        'lang': lang,
        't': lambda key: get_translation(key, lang)
    }
```

### User Session (Flask-Login)

```python
# Login manager configuration
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Bitte melden Sie sich an.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login action
login_user(user, remember=form.remember.data)

# Logout action
logout_user()
```

---

## Flash Message Pattern

### Categories Used

| Category | Bootstrap Class | Usage |
|----------|-----------------|-------|
| `success` | `alert-success` | Action completed successfully |
| `danger` | `alert-danger` | Error or access denied |
| `warning` | `alert-warning` | Caution or login required |
| `info` | `alert-info` | Informational message |

### Template Implementation

```jinja2
{# In base.html #}
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

### Usage in Views

```python
# Success message
flash('Aufgabe erfolgreich aktualisiert.', 'success')

# Error message
flash('Fehler beim Speichern.', 'danger')

# Warning message
flash('Bitte füllen Sie alle Pflichtfelder aus.', 'warning')
```

---

## Error Handling

### HTTP Error Handlers

```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
```

### Form Validation Errors

```jinja2
{# Display field errors #}
{% if form.email.errors %}
    {% for error in form.email.errors %}
    <span class="text-danger">{{ error }}</span>
    {% endfor %}
{% endif %}
```

### Business Logic Errors

```python
# In services, raise exceptions
class TaskService:
    @staticmethod
    def change_status(task_id, new_status, user):
        task = Task.query.get_or_404(task_id)
        
        if not TaskService._can_change_status(task, user):
            raise PermissionError("User cannot change this task's status")
        
        if not TaskService._is_valid_transition(task.status, new_status):
            raise ValueError(f"Invalid status transition")
        
        # ... proceed with change

# In views, catch and flash
@tasks_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def change_status(id):
    try:
        TaskService.change_status(id, request.form['status'], current_user)
        flash('Status aktualisiert.', 'success')
    except PermissionError as e:
        flash('Keine Berechtigung.', 'danger')
    except ValueError as e:
        flash(str(e), 'warning')
    return redirect(url_for('tasks.task_detail', id=id))
```

---

## Security Patterns

### Content Security Policy (CSP) with Nonces

The application uses a nonce-based CSP to protect against XSS attacks while allowing necessary inline scripts and styles.

```python
# app.py - Nonce generation per request
@app.before_request
def generate_csp_nonce():
    """Generate a unique nonce for each request for CSP."""
    g.csp_nonce = secrets.token_urlsafe(16)

@app.context_processor
def inject_csp_nonce():
    """Make csp_nonce available in all templates."""
    return {'csp_nonce': getattr(g, 'csp_nonce', '')}
```

**Template Usage:**
```jinja2
{# Inline scripts require nonce attribute #}
<script nonce="{{ csp_nonce }}">
    // JavaScript code here
</script>

{# Inline styles require nonce attribute #}
<style nonce="{{ csp_nonce }}">
    .my-class { color: red; }
</style>
```

### Security Headers Middleware

```python
@app.after_request
def add_security_headers(response):
    """Apply baseline security headers to all responses."""
    security_headers = {
        'X-Content-Type-Options': 'nosniff',       # Prevent MIME sniffing
        'X-Frame-Options': 'SAMEORIGIN',           # Clickjacking protection
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    }
    for header, value in security_headers.items():
        response.headers.setdefault(header, value)
    
    # CSP with nonces
    nonce = getattr(g, 'csp_nonce', '')
    csp = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        "script-src-attr 'unsafe-inline'; "  # For onclick, onsubmit
        "style-src-attr 'unsafe-inline'; "   # For style="" attributes
        # ... additional directives
    )
    response.headers.setdefault('Content-Security-Policy', csp)
    return response
```

### CSRF Protection Pattern

```python
# extensions.py
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

# In templates - hidden field
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- form fields -->
</form>

# AJAX requests - meta tag + header
<meta name="csrf-token" content="{{ csrf_token() }}">

<script nonce="{{ csp_nonce }}">
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
    }
});
</script>
```

#### ⚠️ CSRF Troubleshooting - Common Issue

**Symptom:** JavaScript-basierte Features (Drag & Drop, AJAX-Buttons) funktionieren nicht - keine Fehlermeldung im UI, aber POST-Requests werden mit 400 abgelehnt.

**Root Cause:** `fetch()` Requests ohne `X-CSRFToken` Header werden vom CSRF-Schutz blockiert.

**Diagnose:**
1. Browser DevTools → Network Tab öffnen
2. Aktion ausführen (z.B. Karte ziehen)
3. POST-Request prüfen: Status 400 = CSRF-Problem

**Lösung:**
```javascript
// In base.html ist window.csrfToken bereits gesetzt via:
// <script>window.csrfToken = "{{ csrf_token() }}";</script>

// Bei JEDEM fetch() POST/PUT/DELETE Request:
const headers = {
    'Content-Type': 'application/json',
};
if (window.csrfToken) {
    headers['X-CSRFToken'] = window.csrfToken;
}

fetch(url, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data)
});
```

**Betroffene Features (bereits gefixt):**
- Backlog Reorder (Session 25) - `backlog.html`
- Estimation Story Points (Session 25) - `estimation.html`
- **Kanban Board Move + Quick Create (Session 26)** - `board.html`
- Sprint Board Move (Session 26) - `sprints/board.html`
- Iteration Board Move (Session 26) - `iterations/board.html`
- Workflow Status Transitions (Session 26) - `issue_statuses.html`

**Merke:** Bei JEDEM neuen `fetch()` mit `method: 'POST'` immer `X-CSRFToken` Header hinzufügen!

### Rate Limiting Pattern

```python
# extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Usage on routes
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Brute-force protection
def login():
    # ...

@auth_bp.route('/switch-tenant/<int:tenant_id>', methods=['POST'])
@limiter.limit("30 per minute")  # Abuse prevention
def switch_tenant(tenant_id):
    # ...
```

### Tenant Isolation Pattern

```python
# middleware/tenant.py
def load_tenant_context():
    """Load tenant context for each request."""
    g.tenant = None
    g.tenant_role = None
    
    if not current_user.is_authenticated:
        return
    
    tenant_id = session.get('current_tenant_id')
    if tenant_id and current_user.can_access_tenant(tenant_id):
        g.tenant = Tenant.query.get(tenant_id)
        g.tenant_role = current_user.get_role_in_tenant(tenant_id)

# Query scoping in routes
def get_tasks():
    tenant_filter = (Task.tenant_id == g.tenant.id) if g.tenant else False
    return Task.query.filter(tenant_filter).all()
```

### File Upload Security

```python
from werkzeug.utils import secure_filename
import uuid

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@tasks_bp.route('/<int:id>/upload', methods=['POST'])
def upload_file(id):
    file = request.files['file']
    if file and allowed_file(file.filename):
        # Secure filename + UUID prefix to prevent collisions
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
```

---

## Audit Logging Pattern

### Helper Function

```python
def log_audit(action, entity_type, entity_id, entity_name=None, 
              old_value=None, new_value=None):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        object_type=entity_type,
        object_id=entity_id,
        entity_name=entity_name,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:500]
    )
    db.session.add(log)
    # Note: commit happens with the main transaction
```

### Action Types

| Action | Description |
|--------|-------------|
| `CREATE` | New record created |
| `UPDATE` | Record modified |
| `DELETE` | Record removed |
| `STATUS_CHANGE` | Task status changed |
| `LOGIN` | User logged in |
| `LOGOUT` | User logged out |
| `UPLOAD` | File uploaded |
| `IMPORT` | Excel data imported |

---

## Testing Patterns

> Added in v1.13.0 - Unit test infrastructure with pytest

### Test Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings = 
    ignore::DeprecationWarning
```

### Factory Pattern for Test Data

```python
# tests/factories.py
import factory
from models import User, Tenant, Project, Task

class TenantFactory(factory.Factory):
    class Meta:
        model = Tenant
    
    name = factory.Sequence(lambda n: f'Test Tenant {n}')
    subdomain = factory.Sequence(lambda n: f'tenant{n}')

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    name = factory.Faker('name')
    role = 'user'
    tenant = factory.SubFactory(TenantFactory)
```

### Test Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from app import create_app
from extensions import db

@pytest.fixture
def app():
    """Create test application."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost'
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def db_session(app):
    """Provide database session."""
    with app.app_context():
        yield db.session

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
```

### Test Categories

| Category | Purpose | Example Tests |
|----------|---------|---------------|
| **Unit Tests** | Individual functions/methods | Model validation, service logic |
| **Integration Tests** | Component interactions | Database operations, workflows |
| **Feature Tests** | End-to-end features | Multi-tenant isolation, approvals |

### Current Coverage (v1.20.4)

**Overall: 68%** (6,775 statements, 2,143 missed)

| Module | Coverage | Notes |
|--------|----------|-------|
| config.py | 100% | ✅ |
| extensions.py | 100% | ✅ |
| translations.py | 100% | ✅ |
| routes/__init__.py | 100% | ✅ |
| routes/auth.py | 100% | ✅ |
| modules/core/__init__.py | 100% | ✅ |
| routes/presets.py | 99% | |
| middleware/tenant.py | 98% | ✅ |
| routes/admin.py | 97% | |
| modules/__init__.py | 88% | |
| routes/api.py | 88% | |
| app.py | 78% | |
| models.py | 76% | |
| routes/tasks.py | 69% | |
| routes/main.py | 68% | |
| modules/projects/models.py | 69% | |
| services.py | 65% | |
| admin/tenants.py | 63% | |
| modules/projects/routes.py | 42% | |
| **Total** | **68%** | **892 tests** |

> See [testCoveragePlan.md](testCoveragePlan.md) for the roadmap to 100% coverage.

### Running Tests

```bash
# Full test suite
pytest

# With coverage report
pytest --cov=. --cov-report=term-missing

# Specific test file
pytest tests/unit/test_models.py

# Specific test function
pytest tests/unit/test_models.py::TestTask::test_task_creation
```
