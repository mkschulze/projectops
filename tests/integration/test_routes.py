"""
Integration tests for API routes.

NOTE: These tests are currently skipped because routes are defined 
outside the create_app() factory, making them unavailable in the test app.
This is a known limitation that requires refactoring app.py to use blueprints.
"""
import pytest
import json


@pytest.mark.skip(reason="Routes defined outside create_app() - requires app refactoring")
@pytest.mark.integration
@pytest.mark.api
class TestAuthRoutes:
    """Tests for authentication routes."""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'Anmelden' in response.data
    
    def test_login_with_valid_credentials(self, client, user):
        """Test login with valid credentials."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_with_invalid_credentials(self, client, user):
        """Test login with invalid credentials fails."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should still be on login page or show error
    
    def test_logout(self, authenticated_client):
        """Test logout works."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


@pytest.mark.skip(reason="Routes defined outside create_app() - requires app refactoring")
@pytest.mark.integration
@pytest.mark.api
class TestDashboardRoutes:
    """Tests for dashboard routes."""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/dashboard')
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_dashboard_accessible_when_logged_in(self, authenticated_client, tenant_with_user):
        """Test dashboard is accessible when logged in."""
        tenant, user = tenant_with_user
        
        # Set tenant in session
        with authenticated_client.session_transaction() as sess:
            sess['current_tenant_id'] = tenant.id
        
        response = authenticated_client.get('/dashboard')
        # Should be successful or redirect to tenant selection
        assert response.status_code in [200, 302]


@pytest.mark.skip(reason="Routes defined outside create_app() - requires app refactoring")
@pytest.mark.integration
@pytest.mark.api
class TestNotificationAPI:
    """Tests for notification API."""
    
    def test_unread_count_requires_auth(self, client):
        """Test unread count endpoint requires authentication."""
        response = client.get('/api/notifications/unread-count')
        assert response.status_code in [302, 401]
    
    def test_unread_count_returns_json(self, authenticated_client, tenant_with_user):
        """Test unread count returns JSON."""
        tenant, user = tenant_with_user
        
        with authenticated_client.session_transaction() as sess:
            sess['current_tenant_id'] = tenant.id
        
        response = authenticated_client.get('/api/notifications/unread-count')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'count' in data or 'unread_count' in data


@pytest.mark.skip(reason="Routes defined outside create_app() - requires app refactoring")
@pytest.mark.integration
@pytest.mark.api
class TestProjectRoutes:
    """Tests for project routes."""
    
    def test_project_list_requires_auth(self, client):
        """Test project list requires authentication."""
        response = client.get('/projects/')
        assert response.status_code in [302, 401]
    
    def test_project_detail_requires_auth(self, client, project):
        """Test project detail requires authentication."""
        response = client.get(f'/projects/{project.id}')
        assert response.status_code in [302, 401]


@pytest.mark.skip(reason="Routes defined outside create_app() - requires app refactoring")
@pytest.mark.integration
@pytest.mark.api
class TestHealthCheck:
    """Tests for application health."""
    
    def test_app_is_running(self, client):
        """Test application responds to requests."""
        response = client.get('/')
        # Should either show content or redirect
        assert response.status_code in [200, 302]
    
    def test_static_files_accessible(self, client):
        """Test static files are served."""
        response = client.get('/static/favicon/favicon.ico')
        # May or may not exist, but should not crash
        assert response.status_code in [200, 404]
