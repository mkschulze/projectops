# Technical Context

> Development environment, dependencies, and project structure for Company ProjectOps

## Tech Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Flask 3.x | Web application framework |
| **ORM** | SQLAlchemy (Flask-SQLAlchemy) | Database abstraction |
| **Migrations** | Alembic (Flask-Migrate) | Schema version control |
| **Authentication** | Flask-Login | Session management |
| **Forms** | Flask-WTF + WTForms | Form handling & CSRF |
| **Password Hashing** | Werkzeug | Secure password storage (pbkdf2:sha256) |
| **Rate Limiting** | Flask-Limiter | Brute-force protection |
| **Excel Processing** | openpyxl | Import/export Excel files |
| **PDF Export** | WeasyPrint | HTML to PDF conversion |
| **Environment** | python-dotenv | Configuration management |
| **WebSocket** | Flask-SocketIO + eventlet | Real-time notifications |
| **Date Handling** | python-dateutil | RRULE parsing, date calculations |
| **iCal Generation** | icalendar | Calendar feed generation |

### Security

| Component | Technology | Purpose |
|-----------|------------|---------|
| **CSP** | Nonce-based | XSS protection for inline scripts/styles |
| **Security Headers** | Custom middleware | X-Frame-Options, X-Content-Type-Options |
| **CSRF Protection** | Flask-WTF | Cross-site request forgery prevention |
| **Rate Limiting** | Flask-Limiter | Brute-force & abuse prevention |
| **Session Security** | Flask (production) | HttpOnly, Secure, SameSite cookies |
| **Tenant Isolation** | Query-level filtering | Data separation per tenant |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **CSS Framework** | Bootstrap 5.3 | Responsive UI components |
| **Icons** | Bootstrap Icons + Custom Icons | UI iconography |
| **Templating** | Jinja2 | Server-side rendering |
| **JavaScript** | Vanilla JS + Socket.IO Client | Interactivity, WebSocket |
| **Charts** | Chart.js 4.x (CDN) | Dashboard visualizations |

### Database

| Environment | Database | Notes |
|-------------|----------|-------|
| Development | SQLite | File-based, no setup |
| Production | PostgreSQL | Recommended for enterprise |

### Internationalization

| Component | Implementation |
|-----------|----------------|
| **Translation System** | Custom `translations.py` dictionary |
| **Supported Languages** | German (de), English (en) |
| **Default Language** | German (de) |
| **Language Storage** | Flask session (`session['lang']`) |
| **Template Access** | `{{ t('key') }}` via context processor |

---

## Project Structure

```
company-projectops-calendar/
├── app.py                  # Application factory & routes (~3100 lines)
├── config.py               # Configuration classes
├── models.py               # SQLAlchemy models (~850 lines)
├── services.py             # Business logic services (~650 lines)
├── translations.py         # i18n dictionary (DE/EN)
├── init_db.py              # Database initialization
├── Pipfile                 # Dependencies (Pipenv)
├── Pipfile.lock            # Locked dependencies
├── .env                    # Environment variables (not in git)
├── .flaskenv               # Flask CLI configuration
│
├── instance/               # Instance-specific files
│   └── app.db              # SQLite database (dev)
│
├── migrations/             # Alembic migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       ├── ff00c7cfda61_add_projectops_calendar_models.py
│       ├── ebe34cad8512_add_multi_stage_approval_workflow_fields.py
│       ├── 76fd77636f22_add_taskpreset_model_for_predefined_.py
│       ├── f34a3101bc19_add_taskreviewer_many_to_many_table_for_.py
│       ├── 76a36e71cb1c_add_team_model_and_task_team_assignments.py
│       ├── bc78eb8f008d_add_multilingual_name_fields_to_team_.py
│       └── c3d4e5f6g7h8_add_recurring_task_fields.py
│
├── docs/                   # Memory Bank documentation
│   ├── technicalConcept.md
│   ├── techContext.md
│   ├── systemPatterns.md
│   ├── productContext.md
│   ├── progress.md
│   └── activeContext.md
│
├── tests/                  # Unit test suite
│   ├── conftest.py         # Pytest fixtures & test app
│   ├── factories.py        # Factory Boy model factories
│   └── unit/               # Unit tests (536 tests)
│       ├── test_models.py
│       ├── test_task_model.py
│       ├── test_project_methods.py
│       ├── test_services.py
│       ├── test_all_services.py
│       ├── test_middleware.py
│       ├── test_translations.py
│       └── ...
│
├── data/                   # JSON data files for presets
│   ├── steuerarten_aufgaben.json
│   └── Antraege.json
│
├── scripts/                # Development & release scripts
│   ├── check_memory_bank.py    # Memory Bank reader for releases
│   ├── release.py              # Release automation (commit, tag, push)
│   ├── create_demo_tenants.py  # Demo tenant creation
│   ├── create_full_demo_data.py
│   ├── create_sample_issues.py
│   ├── create_sample_projects.py
│   ├── create_sample_sprints.py
│   ├── update_memory_bank.py   # AI-assisted Memory Bank updates
│   └── memory_bank_prompt.md   # Prompt template for AI updates
│
├── static/                 # Static assets
│   ├── Color Guide/        # Company color documentation
│   ├── Company Special Case Web Icons/
│   │   ├── SVG files/
│   │   └── Web font/
│   ├── Company-Master-Logo/
│   │   └── DIGITAL/
│   ├── favicon/
│   └── Mobile App Icons/
│
├── templates/              # Jinja2 templates
│   ├── base.html           # Master layout
│   ├── index.html          # Home page
│   ├── login.html          # Authentication
│   ├── dashboard.html      # Main dashboard
│   ├── calendar.html       # Month calendar
│   ├── calendar_year.html  # Year calendar
│   ├── calendar_week.html  # Week calendar
│   ├── tasks/
│   │   ├── list.html       # Task list with filters
│   │   ├── detail.html     # Task detail with tabs
│   │   └── form.html       # Create/edit form
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── user_form.html
│   │   ├── entities.html
│   │   ├── entity_form.html
│   │   ├── tax_types.html
│   │   ├── tax_type_form.html
│   │   ├── presets.html
│   │   └── preset_form.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
└── uploads/                # User uploads (evidence files)
    └── task_*/             # Per-task folders with unique filenames
```

### Planned Structure Additions

```
├── blueprints/             # Modular route handlers
│   ├── __init__.py
│   ├── auth.py             # Login/logout routes
│   ├── main.py             # Dashboard, calendar
│   ├── tasks.py            # Task CRUD, status changes
│   ├── admin.py            # Entity, user, template management
│   └── api.py              # REST endpoints (optional)
│
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── task_service.py     # Task lifecycle management
│   ├── import_service.py   # Excel import logic
│   ├── export_service.py   # Excel export logic
│   └── audit_service.py    # Audit logging
│
├── forms/                  # WTForms form classes
│   ├── __init__.py
│   ├── auth_forms.py
│   ├── task_forms.py
│   ├── entity_forms.py
│   └── import_forms.py
│
└── utils/                  # Helper utilities
    ├── __init__.py
    ├── decorators.py       # Custom decorators
    ├── helpers.py          # Utility functions
    └── validators.py       # Custom validators
```

---

## Dependencies

### Current (Installed)

```toml
[packages]
flask = "*"
flask-sqlalchemy = "*"
flask-login = "*"
flask-wtf = "*"
flask-migrate = "*"
flask-socketio = "*"
werkzeug = "*"
python-dotenv = "*"
openpyxl = "*"
python-dateutil = "*"
weasyprint = "*"
eventlet = "*"
icalendar = "*"

[dev-packages]
pytest = "*"              # Testing framework
pytest-cov = "*"          # Coverage reporting
pytest-flask = "*"        # Flask test helpers
factory-boy = "*"         # Test data factories

[requires]
python_version = "3.14"
```

### Production Additions (Deployment)

```toml
[packages]
# Production database
psycopg2-binary = "*"        # PostgreSQL adapter

# Production server
gunicorn = "*"

# Background jobs (Phase 2)
apscheduler = "*"            # Simple scheduler
# OR
# celery = "*"               # Distributed tasks
# redis = "*"                # Message broker
```

---

## Development Setup

### Prerequisites

- Python 3.9+
- Pipenv (`pip install pipenv`)
- Git

### Initial Setup

```bash
# Clone repository
git clone https://github.com/mkschulze/company-projectops.git
cd company-projectops

# Install dependencies
pipenv install

# Activate virtual environment
pipenv shell

# Create .env file
cat > .env << EOF
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/app.db
EOF

# Initialize database
flask initdb

# Create admin user
flask createadmin

# Run development server
flask run
```

### Database Migrations (Alembic)

```bash
# Initialize migrations (first time only)
flask db init

# Create migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback one version
flask db downgrade
```

### Running Tests

```bash
# Run all tests (598 tests, ~35% coverage as of v1.18.0)
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── conftest.py           # App, db, user fixtures
├── factories.py          # Factory Boy factories for models
└── unit/
    ├── test_models.py          # Model tests
    ├── test_services.py        # Business logic tests
    ├── test_translations.py    # i18n tests
    ├── test_config.py          # Configuration tests
    ├── test_methodology.py     # Project methodology tests
    ├── test_sprint_board.py    # Sprint & board tests
    ├── test_issue_workflow.py  # Issue workflow tests
    ├── test_tenancy.py         # Multi-tenant tests
    ├── test_permissions.py     # RBAC tests
    └── test_calendar.py        # Calendar feature tests
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Application entry point | `app.py` |
| `FLASK_ENV` | Environment mode | `development` |
| `SECRET_KEY` | Session encryption key | (required) |
| `DATABASE_URL` | Database connection string | SQLite |
| `UPLOAD_FOLDER` | Path for file uploads | `uploads/` |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | 16MB |

---

## Brand Integration

### CSS Variables Available

The base template includes the brand color palette:

```css
/* Primary */
--dtt-green: #86BC25;
--dtt-black: #000000;

/* Status Colors */
--dtt-danger-red: #DA291C;      /* Overdue */
--dtt-warning-orange: #ED8B00;  /* Due Soon */
--dtt-sec-blue-4: #0076A8;      /* Submitted */
--dtt-sec-teal-6: #007680;      /* In Review */
--dtt-sec-green-5: #009A44;     /* Completed */

/* Bootstrap Mapped */
--bs-primary: var(--dtt-green);
--bs-danger: var(--dtt-danger-red);
--bs-success: var(--dtt-sec-green-5);
```

### Status Badge Classes (Implemented)

```css
/* Status colors using Deloitte palette */
.badge-status--draft { background-color: var(--dtt-cool-gray-6); }
.badge-status--due-soon { background-color: var(--dtt-warning-orange); }
.badge-status--overdue { background-color: var(--dtt-danger-red); }
.badge-status--submitted { background-color: var(--dtt-sec-blue-4); }
.badge-status--in-review { background-color: var(--dtt-sec-teal-6); }
.badge-status--approved { background-color: var(--dtt-sec-green-5); }
.badge-status--completed { background-color: var(--dtt-sec-green-5); }
.badge-status--rejected { background-color: var(--dtt-danger-red); }
```

---

## Database Models

### Core Models (models.py ~650 lines)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `User` | User accounts | email, name, role, password_hash |
| `Entity` | Legal entities | name, country, group_id, is_active |
| `TaxType` | Tax categories | code, name, description |
| `TaskTemplate` | Reusable templates | keyword, tax_type_id, description |
| `Task` | Core tasks | title, entity_id, due_date, status, owner_id |
| `TaskReviewer` | Multi-reviewer tracking | task_id, user_id, has_approved, approved_at |
| `TaskEvidence` | File/link attachments | task_id, evidence_type, file_path, url |
| `Comment` | Discussion threads | task_id, text, created_by_id |
| `TaskPreset` | Predefined templates | title, category, tax_type, description |
| `AuditLog` | Activity logging | action, entity_type, entity_id, user_id |
| `Team` | User grouping | name, description, color, manager_id, is_active |

### TaskReviewer Model (Multi-Reviewer Support)

```python
class TaskReviewer(db.Model):
    __tablename__ = 'task_reviewer'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order = db.Column(db.Integer, default=1)
    has_approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    approval_note = db.Column(db.Text)
    has_rejected = db.Column(db.Boolean, default=False)
    rejected_at = db.Column(db.DateTime)
    rejection_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    
    # Unique constraint: one reviewer per task
    __table_args__ = (db.UniqueConstraint('task_id', 'user_id', name='unique_task_reviewer'),)
```

### Team Model (User Grouping)

```python
# Association table for team members
team_members = db.Table('team_members',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow),
    db.Column('is_team_lead', db.Boolean, default=False)
)

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#86BC25')  # Deloitte Green
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    manager = db.relationship('User', foreign_keys=[manager_id])
    members = db.relationship('User', secondary=team_members, lazy='dynamic',
                             backref=db.backref('teams', lazy='dynamic'))
    owned_tasks = db.relationship('Task', back_populates='owner_team', 
                                  foreign_keys='Task.owner_team_id')
    
    # Methods
    def add_member(self, user, is_lead=False): ...
    def remove_member(self, user): ...
    def is_member(self, user): ...
    def get_member_count(self): ...
```

### Task Team Fields

```python
# Added to Task model
owner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True, index=True)
reviewer_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

owner_team = db.relationship('Team', back_populates='owned_tasks', foreign_keys=[owner_team_id])
reviewer_team = db.relationship('Team', foreign_keys=[reviewer_team_id])

# Methods
def is_reviewer(self, user):
    """Check if user is a direct reviewer OR member of reviewer_team"""
def is_reviewer_via_team(self, user):
    """Check if user can review via team membership"""
def get_owner_display(self):
    """Return owner user name or team name"""
def is_assigned_to_user(self, user):
    """Check if user is assigned directly or via team"""
```

---

## IDE Configuration

### VSCode Recommended Extensions

- Python (Microsoft)
- Pylance
- Flask Snippets
- Jinja2 Snippet Kit
- SQLite Viewer
- GitLens

### VSCode Settings (`.vscode/settings.json`)

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.associations": {
    "*.html": "jinja-html"
  }
}
```
