"""
CSRF Protection Tests

Verifies that CSRF protection is enforced on POST endpoints.
"""
import pytest


class TestCSRFProtection:
    """Test CSRF token validation when CSRF is enabled"""
    
    @pytest.fixture
    def csrf_enabled_app(self, app):
        """Create an app with CSRF protection enabled for testing"""
        # Store original value
        original_value = app.config.get('WTF_CSRF_ENABLED', True)
        app.config['WTF_CSRF_ENABLED'] = True
        yield app
        # Restore original value
        app.config['WTF_CSRF_ENABLED'] = original_value
    
    @pytest.fixture
    def csrf_client(self, csrf_enabled_app):
        """Test client with CSRF enabled"""
        return csrf_enabled_app.test_client()
    
    def test_login_rejects_missing_csrf(self, csrf_client):
        """POST to login without CSRF token should be rejected"""
        response = csrf_client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        # Should return 400 Bad Request due to missing CSRF token
        assert response.status_code == 400
    
    def test_login_rejects_invalid_csrf(self, csrf_client):
        """POST to login with invalid CSRF token should be rejected"""
        response = csrf_client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'csrf_token': 'invalid-token'
        })
        # Should return 400 Bad Request due to invalid CSRF token
        assert response.status_code == 400


class TestCSRFConfiguration:
    """Verify CSRF configuration exists"""
    
    def test_csrf_can_be_enabled(self, app):
        """CSRF can be enabled via config"""
        app.config['WTF_CSRF_ENABLED'] = True
        assert app.config.get('WTF_CSRF_ENABLED') == True
    
    def test_csrf_can_be_disabled(self, app):
        """CSRF can be disabled via config"""
        app.config['WTF_CSRF_ENABLED'] = False
        assert app.config.get('WTF_CSRF_ENABLED') == False
