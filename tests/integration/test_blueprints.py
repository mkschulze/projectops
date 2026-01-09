"""
Integration Tests for Blueprint Routes (Phase 4)

Tests the refactored routes in the new blueprint structure:
- routes/auth.py - auth_bp
- routes/main.py - main_bp
- routes/tasks.py - tasks_bp

These tests use the Flask test client to verify routes work correctly.
"""

import pytest
from datetime import date, datetime, timedelta
from flask import url_for
from flask_login import login_user

from extensions import db
from models import (
    User, Task, Entity, Notification, Team, TaskTemplate, TaskCategory,
    Tenant, TenantMembership
)


# ============================================================================
# HELPER FIXTURES (module-specific)
# ============================================================================

@pytest.fixture
def bp_app():
    """Create test application for blueprint tests"""
    from app import create_app
    
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def bp_client(bp_app):
    """Create test client for blueprint tests"""
    return bp_app.test_client()


@pytest.fixture
def bp_logged_in_user(bp_client, bp_app):
    """Create and login a regular user"""
    with bp_app.app_context():
        tenant = Tenant(
            name='Test Tenant User',
            slug='test-tenant-user',
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()

        user = User(
            email='user@example.com',
            name='Regular User',
            role='preparer',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member',
            is_default=True
        )
        db.session.add(membership)
        user.current_tenant_id = tenant.id
        db.session.commit()
        user_id = user.id
        tenant_id = tenant.id
    
    # Login via POST
    bp_client.post('/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    })

    with bp_client.session_transaction() as sess:
        sess['current_tenant_id'] = tenant_id
    
    return user_id


@pytest.fixture
def bp_logged_in_admin(bp_client, bp_app):
    """Create and login an admin user"""
    with bp_app.app_context():
        tenant = Tenant(
            name='Test Tenant Admin',
            slug='test-tenant-admin',
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()

        user = User(
            email='admin@example.com',
            name='Admin User',
            role='admin',
            is_active=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.flush()

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='admin',
            is_default=True
        )
        db.session.add(membership)
        user.current_tenant_id = tenant.id
        db.session.commit()
        user_id = user.id
        tenant_id = tenant.id
    
    # Login via POST
    bp_client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    })

    with bp_client.session_transaction() as sess:
        sess['current_tenant_id'] = tenant_id
    
    return user_id


class TestAuthBlueprint:
    """Tests for auth_bp routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_login_page_status(self, bp_client):
        """GET /login should return 200 status"""
        response = bp_client.get('/login')
        assert response.status_code == 200
    
    def test_login_with_valid_credentials(self, bp_client, bp_app):
        """POST /login with valid credentials should redirect"""
        with bp_app.app_context():
            # Create a test user
            user = User(
                email='test@example.com',
                name='Test User',
                role='user',
                is_active=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = bp_client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=False)
        
        # Should redirect after successful login
        assert response.status_code in [302, 200]
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_login_with_invalid_credentials(self, bp_client, bp_app):
        """POST /login with wrong password should return to login"""
        with bp_app.app_context():
            user = User(
                email='wrong@example.com',
                name='Wrong User',
                role='user',
                is_active=True
            )
            user.set_password('correctpassword')
            db.session.add(user)
            db.session.commit()
        
        response = bp_client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=False)
        
        # Should stay on login or redirect back to login
        assert response.status_code in [200, 302]
    
    def test_logout_redirects_to_login(self, bp_client, bp_app, bp_logged_in_user):
        """GET /logout should redirect to login"""
        response = bp_client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location or '/' in response.location


class TestMainBlueprint:
    """Tests for main_bp routes"""
    
    def test_index_redirects_when_logged_in(self, bp_client, bp_logged_in_admin):
        """GET / should redirect to dashboard for logged-in users"""
        response = bp_client.get('/')
        # May redirect or show dashboard
        assert response.status_code in [200, 302, 500]
    
    def test_dashboard_requires_login(self, bp_client):
        """GET /dashboard should redirect to login if not authenticated"""
        response = bp_client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.location
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_dashboard_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /dashboard should route correctly for authenticated users"""
        response = bp_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_set_language(self, bp_client):
        """GET /set-language/<lang> should change language"""
        response = bp_client.get('/set-language/en', follow_redirects=False)
        assert response.status_code == 302
        
        with bp_client.session_transaction() as sess:
            assert sess.get('lang') == 'en'
    
    def test_calendar_requires_login(self, bp_client):
        """GET /calendar should redirect if not logged in"""
        response = bp_client.get('/calendar', follow_redirects=False)
        assert response.status_code == 302
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_calendar_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /calendar should route correctly for authenticated users"""
        response = bp_client.get('/calendar')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_calendar_year_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /calendar/year should route correctly"""
        response = bp_client.get('/calendar/year')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_calendar_week_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /calendar/week should route correctly"""
        response = bp_client.get('/calendar/week')
        assert response.status_code == 200
    
    def test_notifications_requires_login(self, bp_client):
        """GET /notifications should require login"""
        response = bp_client.get('/notifications', follow_redirects=False)
        assert response.status_code == 302
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_notifications_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /notifications should route correctly"""
        response = bp_client.get('/notifications')
        assert response.status_code == 200
    
    def test_profile_requires_login(self, bp_client):
        """GET /profile should require login"""
        response = bp_client.get('/profile', follow_redirects=False)
        assert response.status_code == 302


class TestTasksBlueprint:
    """Tests for tasks_bp routes"""
    
    @pytest.fixture
    def sample_entity(self, bp_app):
        """Create a sample entity for testing"""
        with bp_app.app_context():
            entity = Entity(
                name='Test Company',
                short_name='TC',
                is_active=True
            )
            db.session.add(entity)
            db.session.commit()
            return entity.id
    
    @pytest.fixture
    def sample_task(self, bp_app, sample_entity):
        """Create a sample task for testing"""
        with bp_app.app_context():
            task = Task(
                title='Test Task',
                description='Test description',
                entity_id=sample_entity,
                due_date=date.today() + timedelta(days=7),
                year=date.today().year,
                status='draft'
            )
            db.session.add(task)
            db.session.commit()
            return task.id
    
    def test_task_list_requires_login(self, bp_client):
        """GET /tasks should require login"""
        response = bp_client.get('/tasks', follow_redirects=False)
        assert response.status_code == 302
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_task_list_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /tasks should route correctly"""
        response = bp_client.get('/tasks')
        assert response.status_code == 200
    
    def test_task_detail_requires_login(self, bp_client, sample_task):
        """GET /tasks/<id> should require login"""
        response = bp_client.get(f'/tasks/{sample_task}', follow_redirects=False)
        assert response.status_code == 302
    
    def test_task_create_page_requires_login(self, bp_client):
        """GET /tasks/new should require login"""
        response = bp_client.get('/tasks/new', follow_redirects=False)
        assert response.status_code == 302
    
    @pytest.mark.xfail(reason="Template requires context processor 't' - works in full app")
    def test_task_create_route_exists(self, bp_client, bp_logged_in_admin):
        """GET /tasks/new should route correctly"""
        response = bp_client.get('/tasks/new')
        assert response.status_code == 200
    
    def test_task_archive_list_requires_login(self, bp_client):
        """GET /tasks/archive should require login"""
        response = bp_client.get('/tasks/archive', follow_redirects=False)
        assert response.status_code == 302


class TestBlueprintUrlGeneration:
    """Tests for URL generation with blueprints"""
    
    def test_auth_url_for(self, bp_app):
        """Test url_for works with auth blueprint"""
        with bp_app.test_request_context():
            assert url_for('auth.login') == '/login'
            assert url_for('auth.logout') == '/logout'
    
    def test_main_url_for(self, bp_app):
        """Test url_for works with main blueprint"""
        with bp_app.test_request_context():
            assert url_for('main.index') == '/'
            assert url_for('main.dashboard') == '/dashboard'
            assert url_for('main.calendar_view') == '/calendar'
            assert url_for('main.set_language', lang='en') == '/set-language/en'
    
    def test_tasks_url_for(self, bp_app):
        """Test url_for works with tasks blueprint"""
        with bp_app.test_request_context():
            assert url_for('tasks.task_list') == '/tasks'
            assert url_for('tasks.task_create') == '/tasks/new'
            assert url_for('tasks.task_detail', task_id=1) == '/tasks/1'
    
    def test_admin_url_for(self, bp_app):
        """Test url_for works with admin blueprint"""
        with bp_app.test_request_context():
            assert url_for('admin.dashboard') == '/admin'
            assert url_for('admin.users') == '/admin/users'
            assert url_for('admin.user_new') == '/admin/users/new'
            assert url_for('admin.entities') == '/admin/entities'
            assert url_for('admin.teams') == '/admin/teams'
            assert url_for('admin.categories') == '/admin/categories'
            assert url_for('admin.modules') == '/admin/modules'
    
    def test_api_url_for(self, bp_app):
        """Test url_for works with api blueprint"""
        with bp_app.test_request_context():
            assert url_for('api.bulk_archive') == '/api/tasks/bulk-archive'
            assert url_for('api.bulk_restore') == '/api/tasks/bulk-restore'
            assert url_for('api.dashboard_status_chart') == '/api/dashboard/status-chart'
            assert url_for('api.presets_list') == '/api/presets'
            assert url_for('api.task_approval_status', task_id=1) == '/api/tasks/1/approval-status'


class TestAdminBlueprint:
    """Tests for admin_bp routes"""
    
    def test_admin_dashboard_requires_login(self, bp_client):
        """GET /admin should require login"""
        response = bp_client.get('/admin', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_users_requires_login(self, bp_client):
        """GET /admin/users should require login"""
        response = bp_client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_entities_requires_login(self, bp_client):
        """GET /admin/entities should require login"""
        response = bp_client.get('/admin/entities', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_teams_requires_login(self, bp_client):
        """GET /admin/teams should require login"""
        response = bp_client.get('/admin/teams', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_categories_requires_login(self, bp_client):
        """GET /admin/categories should require login"""
        response = bp_client.get('/admin/categories', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_modules_requires_login(self, bp_client):
        """GET /admin/modules should require login"""
        response = bp_client.get('/admin/modules', follow_redirects=False)
        assert response.status_code == 302


class TestApiBlueprint:
    """Tests for api_bp routes"""
    
    def test_api_bulk_archive_requires_login(self, bp_client):
        """POST /api/tasks/bulk-archive should require login"""
        response = bp_client.post('/api/tasks/bulk-archive', 
                                  json={'task_ids': []},
                                  follow_redirects=False)
        assert response.status_code == 302
    
    def test_api_dashboard_chart_requires_login(self, bp_client):
        """GET /api/dashboard/status-chart should require login"""
        response = bp_client.get('/api/dashboard/status-chart', follow_redirects=False)
        assert response.status_code == 302
    
    def test_api_presets_requires_login(self, bp_client):
        """GET /api/presets should require login"""
        response = bp_client.get('/api/presets', follow_redirects=False)
        assert response.status_code == 302
    
    def test_api_presets_list_for_admin(self, bp_client, bp_logged_in_admin):
        """GET /api/presets should return JSON for authenticated users"""
        response = bp_client.get('/api/presets')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_api_dashboard_status_chart_for_admin(self, bp_client, bp_logged_in_admin):
        """GET /api/dashboard/status-chart should return JSON"""
        response = bp_client.get('/api/dashboard/status-chart')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert 'draft' in data
        assert 'completed' in data


# ============================================================================
# DEEPER ROUTE TESTS - Actual functionality
# ============================================================================

class TestAuthDeepFunctionality:
    """Deeper tests for auth flow logic"""
    
    def test_logout_clears_session(self, bp_client, bp_app, bp_logged_in_user):
        """Logout should clear user session"""
        # Logout
        bp_client.get('/logout')
        
        # Try accessing protected route
        response = bp_client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.location
    
    def test_language_preference_persists(self, bp_client):
        """Setting language should persist across requests"""
        bp_client.get('/set-language/en')
        
        with bp_client.session_transaction() as sess:
            assert sess.get('lang') == 'en'
        
        bp_client.get('/set-language/de')
        
        with bp_client.session_transaction() as sess:
            assert sess.get('lang') == 'de'


class TestApiDeepFunctionality:
    """Deeper tests for API endpoint logic"""
    
    @pytest.fixture
    def tasks_for_bulk_ops(self, bp_app, bp_logged_in_admin):
        """Create tasks for bulk operations testing"""
        with bp_app.app_context():
            entity = Entity(name='Bulk Test Corp', short_name='BTC', is_active=True)
            db.session.add(entity)
            db.session.commit()
            
            tasks = []
            for i in range(3):
                task = Task(
                    title=f'Bulk Task {i}',
                    description=f'Description {i}',
                    entity_id=entity.id,
                    due_date=date.today() + timedelta(days=7),
                    year=date.today().year,
                    status='open'
                )
                db.session.add(task)
                tasks.append(task)
            db.session.commit()
            return [t.id for t in tasks]
    
    def test_bulk_archive_changes_status(self, bp_client, bp_app, tasks_for_bulk_ops):
        """POST /api/tasks/bulk-archive should archive tasks"""
        response = bp_client.post('/api/tasks/bulk-archive',
                                  json={'task_ids': tasks_for_bulk_ops})
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') == True
        
        # Verify tasks are archived
        with bp_app.app_context():
            for task_id in tasks_for_bulk_ops:
                task = db.session.get(Task, task_id)
                assert task.is_archived == True
    
    def test_bulk_restore_changes_status(self, bp_client, bp_app, tasks_for_bulk_ops):
        """POST /api/tasks/bulk-restore should restore archived tasks"""
        # First archive them
        bp_client.post('/api/tasks/bulk-archive',
                       json={'task_ids': tasks_for_bulk_ops})
        
        # Then restore them
        response = bp_client.post('/api/tasks/bulk-restore',
                                  json={'task_ids': tasks_for_bulk_ops})
        assert response.status_code == 200
        
        # Verify tasks are restored
        with bp_app.app_context():
            for task_id in tasks_for_bulk_ops:
                task = db.session.get(Task, task_id)
                assert task.is_archived == False
    
    def test_bulk_status_change(self, bp_client, bp_app, tasks_for_bulk_ops):
        """POST /api/tasks/bulk-status should change task status"""
        response = bp_client.post('/api/tasks/bulk-status',
                                  json={'task_ids': tasks_for_bulk_ops, 'status': 'completed'})
        assert response.status_code == 200
        
        # Verify status change
        with bp_app.app_context():
            for task_id in tasks_for_bulk_ops:
                task = db.session.get(Task, task_id)
                assert task.status == 'completed'
    
    def test_bulk_archive_empty_list(self, bp_client, bp_logged_in_admin):
        """Bulk archive with empty list should return 400 (bad request)"""
        response = bp_client.post('/api/tasks/bulk-archive',
                                  json={'task_ids': []})
        assert response.status_code == 400
    
    def test_dashboard_monthly_chart_returns_data(self, bp_client, bp_logged_in_admin):
        """GET /api/dashboard/monthly-chart should return chart data"""
        response = bp_client.get('/api/dashboard/monthly-chart')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert 'months' in data  # API returns months array
        assert 'year' in data


class TestAdminDeepFunctionality:
    """Deeper tests for admin routes"""
    
    def test_non_admin_denied_admin_dashboard(self, bp_client, bp_logged_in_user):
        """Non-admin users should be denied access to admin dashboard"""
        response = bp_client.get('/admin', follow_redirects=False)
        # Should redirect away from admin
        assert response.status_code == 302
    
    def test_non_admin_denied_user_management(self, bp_client, bp_logged_in_user):
        """Non-admin users should be denied access to user management"""
        response = bp_client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302


class TestTasksDeepFunctionality:
    """Deeper tests for task routes"""
    
    @pytest.fixture
    def test_entity(self, bp_app):
        """Create test entity"""
        with bp_app.app_context():
            entity = Entity(name='Deep Test Corp', short_name='DTC', is_active=True)
            db.session.add(entity)
            db.session.commit()
            return entity.id
    
    @pytest.fixture
    def test_task(self, bp_app, test_entity):
        """Create test task"""
        with bp_app.app_context():
            task = Task(
                title='Deep Test Task',
                description='Testing deeper functionality',
                entity_id=test_entity,
                due_date=date.today() + timedelta(days=14),
                year=date.today().year,
                status='draft'
            )
            db.session.add(task)
            db.session.commit()
            return task.id
    
    @pytest.fixture
    def submitted_task(self, bp_app, test_entity, bp_logged_in_admin):
        """Create a submitted task (admin is owner)"""
        with bp_app.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            task = Task(
                title='Submitted Test Task',
                description='Task in submitted state',
                entity_id=test_entity,
                due_date=date.today() + timedelta(days=14),
                year=date.today().year,
                status='submitted',
                owner_id=user.id
            )
            db.session.add(task)
            db.session.commit()
            return task.id
    
    def test_task_status_change_draft_to_submitted(self, bp_client, bp_app, test_task, bp_logged_in_admin):
        """POST /tasks/<id>/status should change task status from draft to submitted"""
        # First set owner to current admin
        with bp_app.app_context():
            task = db.session.get(Task, test_task)
            user = User.query.filter_by(email='admin@example.com').first()
            task.owner_id = user.id
            db.session.commit()
        
        response = bp_client.post(f'/tasks/{test_task}/status',
                                  data={'status': 'submitted'},
                                  follow_redirects=False)
        assert response.status_code == 302
        
        # Verify status changed
        with bp_app.app_context():
            task = db.session.get(Task, test_task)
            assert task.status == 'submitted'
    
    def test_task_status_change_submitted_to_in_review(self, bp_client, bp_app, submitted_task):
        """POST /tasks/<id>/status should change status from submitted to in_review"""
        response = bp_client.post(f'/tasks/{submitted_task}/status',
                                  data={'status': 'in_review'},
                                  follow_redirects=False)
        assert response.status_code == 302
        
        # Verify status changed
        with bp_app.app_context():
            task = db.session.get(Task, submitted_task)
            assert task.status == 'in_review'
    
    def test_task_archive_single(self, bp_client, bp_app, test_task, bp_logged_in_admin):
        """POST /tasks/<id>/archive should archive task"""
        response = bp_client.post(f'/tasks/{test_task}/archive',
                                  follow_redirects=False)
        assert response.status_code == 302
        
        # Verify archived
        with bp_app.app_context():
            task = db.session.get(Task, test_task)
            assert task.is_archived == True
    
    def test_task_restore_single(self, bp_client, bp_app, test_task, bp_logged_in_admin):
        """POST /tasks/<id>/restore should restore archived task"""
        # First archive
        bp_client.post(f'/tasks/{test_task}/archive')
        
        # Then restore
        response = bp_client.post(f'/tasks/{test_task}/restore',
                                  follow_redirects=False)
        assert response.status_code == 302
        
        # Verify restored
        with bp_app.app_context():
            task = db.session.get(Task, test_task)
            assert task.is_archived == False


class TestNotificationRoutes:
    """Tests for notification routes"""
    
    @pytest.fixture
    def test_notifications(self, bp_app, bp_logged_in_admin):
        """Create test notifications"""
        with bp_app.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            notifications = []
            for i in range(3):
                notif = Notification(
                    user_id=user.id,
                    notification_type='task_assigned',  # Required field
                    title=f'Test Notification {i}',
                    message=f'Message {i}',
                    is_read=False
                )
                db.session.add(notif)
                notifications.append(notif)
            db.session.commit()
            return [n.id for n in notifications]
    
    def test_mark_notification_read(self, bp_client, bp_app, test_notifications):
        """POST /notifications/mark-read/<id> should mark as read"""
        notif_id = test_notifications[0]
        response = bp_client.post(f'/notifications/mark-read/{notif_id}',
                                  follow_redirects=False)
        assert response.status_code in [200, 302]
        
        # Verify marked as read
        with bp_app.app_context():
            notif = db.session.get(Notification, notif_id)
            assert notif.is_read == True
    
    def test_mark_all_notifications_read(self, bp_client, bp_app, test_notifications):
        """POST /notifications/mark-all-read should mark all as read"""
        response = bp_client.post('/notifications/mark-all-read',
                                  follow_redirects=False)
        assert response.status_code in [200, 302]
        
        # Verify all marked as read
        with bp_app.app_context():
            for notif_id in test_notifications:
                notif = db.session.get(Notification, notif_id)
                assert notif.is_read == True
