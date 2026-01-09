"""
Pytest configuration and fixtures for ProjectOps.
"""
import os
import sys
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_login import login_user

from extensions import db as _db
from app import create_app
from config import Config


class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    SECRET_KEY = 'test-secret-key'
    LOGIN_DISABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    _app = create_app('testing')
    _app.config.from_object(TestConfig)
    
    # Create application context
    ctx = _app.app_context()
    ctx.push()
    
    yield _app
    
    ctx.pop()


@pytest.fixture(scope='session')
def db(app):
    """Create database for testing."""
    _db.app = app
    _db.create_all()
    
    yield _db
    
    _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db_session(db):
    """Ensure clean database session for each test."""
    yield
    # After each test, rollback any uncommitted changes and clear session
    try:
        db.session.rollback()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_db_tables(db):
    """Clean up all data after each test to ensure test isolation."""
    yield
    # Clean up in reverse order of dependencies
    from models import (
        User, Tenant, TenantMembership, TenantApiKey, Notification,
        Task, TaskReviewer, Team, Entity, UserEntity, TaskEvidence, Comment,
        team_members, TaskPreset, PresetCustomField, TaskCustomFieldValue, AuditLog,
        Module, UserModule, TaskCategory
    )
    from modules.projects.models import (
        Project, ProjectMember, Sprint, Issue, IssueType, IssueStatus,
        IssueComment, IssueActivity, IssueAttachment
    )
    
    try:
        # Delete in order of dependencies
        db.session.query(IssueAttachment).delete()
        db.session.query(IssueActivity).delete()
        db.session.query(IssueComment).delete()
        db.session.query(Issue).delete()
        db.session.query(IssueType).delete()
        db.session.query(IssueStatus).delete()
        db.session.query(Sprint).delete()
        db.session.query(ProjectMember).delete()
        db.session.query(Project).delete()
        db.session.query(Notification).delete()
        db.session.query(TenantApiKey).delete()
        db.session.query(TenantMembership).delete()
        db.session.query(TaskReviewer).delete()
        db.session.query(Comment).delete()
        db.session.query(TaskEvidence).delete()
        db.session.query(TaskCustomFieldValue).delete()
        db.session.query(Task).delete()
        db.session.query(UserEntity).delete()
        # Clean preset custom fields before presets
        db.session.query(PresetCustomField).delete()
        db.session.query(TaskPreset).delete()
        db.session.query(AuditLog).delete()
        # Clean team_members association table
        db.session.execute(team_members.delete())
        db.session.query(Team).delete()
        db.session.query(Entity).delete()
        # Clean modules and categories
        db.session.query(UserModule).delete()
        db.session.query(Module).delete()
        db.session.query(TaskCategory).delete()
        db.session.query(Tenant).delete()
        db.session.query(User).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create session bound to this connection
    options = dict(bind=connection, binds={})
    session = db._make_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope='function')
def client(app, db):
    """Create test client."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    from models import User
    
    user = User(
        email='test@example.com',
        name='Test User',
        role='preparer',
        is_active=True
    )
    user.set_password('testpassword123')
    
    db.session.add(user)
    db.session.commit()
    
    yield user
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from models import User
    
    admin = User(
        email='admin@example.com',
        name='Admin User',
        role='admin',
        is_active=True
    )
    admin.set_password('adminpassword123')
    
    db.session.add(admin)
    db.session.commit()
    
    yield admin
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def authenticated_client(client, user, app):
    """Client with authenticated user."""
    with app.test_request_context():
        login_user(user)
    
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id
        sess['_fresh'] = True
    
    yield client


@pytest.fixture
def authenticated_client_with_tenant(client, user, tenant, app, db):
    """Client with authenticated user AND tenant context set.
    
    This is required for routes that use tenant-scoped queries like:
    - get_task_scoped()
    - get_task_or_404_scoped()
    - Any route using g.tenant
    """
    from models import TenantMembership
    
    # Create tenant membership for user
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role='admin',
        is_default=True
    )
    db.session.add(membership)
    
    # Set user's current tenant
    user.current_tenant_id = tenant.id
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id
        sess['_fresh'] = True
        sess['current_tenant_id'] = tenant.id
    
    yield client


@pytest.fixture
def admin_client_with_tenant(client, admin_user, tenant, app, db):
    """Admin client with tenant context set.
    
    For testing admin-only routes with proper tenant context.
    """
    from models import TenantMembership
    
    # Create tenant membership for admin
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=admin_user.id,
        role='admin',
        is_default=True
    )
    db.session.add(membership)
    
    # Set admin's current tenant
    admin_user.current_tenant_id = tenant.id
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = admin_user.id
        sess['_fresh'] = True
        sess['current_tenant_id'] = tenant.id
    
    yield client


# =============================================================================
# TENANT FIXTURES
# =============================================================================

@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    from models import Tenant
    
    tenant = Tenant(
        name='Test Tenant',
        slug='test-tenant',
        is_active=True
    )
    
    db.session.add(tenant)
    db.session.commit()
    
    yield tenant
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def tenant_with_user(db, tenant, user):
    """Create tenant with user membership."""
    from models import TenantMembership
    
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role='member',
        is_default=True
    )
    
    db.session.add(membership)
    db.session.commit()
    
    yield tenant, user
    # Cleanup handled by clean_db_tables fixture


# =============================================================================
# PROJECT FIXTURES
# =============================================================================

@pytest.fixture
def project(db, tenant):
    """Create a test project."""
    from modules.projects.models import Project
    
    project = Project(
        name='Test Project',
        key='TEST',
        description='A test project',
        tenant_id=tenant.id,
        methodology='scrum'
    )
    
    db.session.add(project)
    db.session.commit()
    
    yield project
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def project_with_member(db, project, user):
    """Create project with team member."""
    from modules.projects.models import ProjectMember
    
    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role='member'
    )
    
    db.session.add(member)
    db.session.commit()
    
    yield project, user
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def sprint(db, project):
    """Create a test sprint."""
    from modules.projects.models import Sprint
    from datetime import timedelta
    
    sprint = Sprint(
        name='Sprint 1',
        project_id=project.id,
        start_date=datetime.utcnow().date(),
        end_date=(datetime.utcnow() + timedelta(days=14)).date(),
        goal='Complete sprint goals'
    )
    
    db.session.add(sprint)
    db.session.commit()
    
    yield sprint
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def issue_type(db, project):
    """Create a test issue type."""
    from modules.projects.models import IssueType
    
    issue_type = IssueType(
        name='Task',
        project_id=project.id,
        icon='bi-check-square',
        color='#0076A8'
    )
    
    db.session.add(issue_type)
    db.session.commit()
    
    yield issue_type
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def issue_status(db, project):
    """Create a test issue status."""
    from modules.projects.models import IssueStatus
    
    status = IssueStatus(
        name='To Do',
        project_id=project.id,
        category='todo',
        sort_order=1,
        is_initial=True
    )
    
    db.session.add(status)
    db.session.commit()
    
    yield status
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def issue(db, project, issue_type, issue_status, user, tenant):
    """Create a test issue."""
    from modules.projects.models import Issue
    
    issue = Issue(
        key=f'{project.key}-1',
        summary='Test Issue',
        description='Test issue description',
        project_id=project.id,
        tenant_id=tenant.id,
        type_id=issue_type.id,
        status_id=issue_status.id,
        reporter_id=user.id
    )
    
    db.session.add(issue)
    db.session.commit()
    
    yield issue
    # Cleanup handled by clean_db_tables fixture


# =============================================================================
# TASK FIXTURES (Calendar Tasks)
# =============================================================================

@pytest.fixture
def entity(db, tenant):
    """Create a test entity (legal entity for tasks)."""
    from models import Entity
    
    entity = Entity(
        name='Test GmbH',
        name_de='Test GmbH',
        name_en='Test Ltd',
        tenant_id=tenant.id,
        is_active=True
    )
    
    db.session.add(entity)
    db.session.commit()
    
    yield entity
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def task(db, tenant, entity, user):
    """Create a test task (calendar item)."""
    from models import Task
    from datetime import date, timedelta
    
    task = Task(
        tenant_id=tenant.id,
        entity_id=entity.id,
        title='Test Tax Filing',
        description='Test task description',
        year=2026,
        period='Q1',
        due_date=date.today() + timedelta(days=30),
        status='draft',
        owner_id=user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    yield task
    # Cleanup handled by clean_db_tables fixture


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@pytest.fixture
def login_as(client, app):
    """Factory fixture to log in as any user."""
    def _login_as(user):
        with client.session_transaction() as sess:
            sess['_user_id'] = user.id
            sess['_fresh'] = True
        return client
    
    return _login_as


@pytest.fixture
def set_tenant_context(app):
    """Factory fixture to set tenant context."""
    def _set_tenant(tenant):
        from flask import g
        g.current_tenant = tenant
    
    return _set_tenant


# =============================================================================
# API HELPERS
# =============================================================================

@pytest.fixture
def api_headers():
    """Standard API headers."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


# =============================================================================
# PRESET FIXTURES
# =============================================================================

@pytest.fixture
def task_preset(db):
    """Create a test task preset."""
    from models import TaskPreset
    
    preset = TaskPreset(
        title='Test Preset',
        title_de='Test Vorlage',
        title_en='Test Preset',
        category='aufgabe',
        tax_type='Umsatzsteuer',
        law_reference='§18 UStG',
        description='Test description',
        description_de='Test Beschreibung',
        description_en='Test description',
        source='manual',
        is_active=True
    )
    
    db.session.add(preset)
    db.session.commit()
    
    yield preset
    # Cleanup handled by clean_db_tables fixture


@pytest.fixture
def preset_custom_field(db, task_preset):
    """Create a test custom field for a preset."""
    from models import PresetCustomField
    
    field = PresetCustomField(
        preset_id=task_preset.id,
        name='test_field',
        label_de='Testfeld',
        label_en='Test Field',
        field_type='text',
        is_required=False,
        placeholder_de='Wert eingeben',
        placeholder_en='Enter value',
        default_value='',
        sort_order=1
    )
    
    db.session.add(field)
    db.session.commit()
    
    yield field
    # Cleanup handled by clean_db_tables fixture
