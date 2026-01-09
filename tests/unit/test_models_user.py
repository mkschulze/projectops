"""
Unit tests for User model.
"""
import pytest
from werkzeug.security import check_password_hash


@pytest.mark.unit
@pytest.mark.models
class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self, user):
        """Test user is created correctly."""
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.is_active is True
    
    def test_password_hashing(self, user):
        """Test password is hashed correctly."""
        assert user.password_hash is not None
        assert user.password_hash != 'testpassword123'
        assert user.check_password('testpassword123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_set_password(self, db, user):
        """Test setting a new password."""
        user.set_password('newpassword456')
        db.session.commit()
        
        assert user.check_password('newpassword456') is True
        assert user.check_password('testpassword123') is False
    
    def test_user_roles(self, user, admin_user):
        """Test user role differences."""
        assert user.role == 'preparer'
        assert admin_user.role == 'admin'
    
    def test_user_repr(self, user):
        """Test user string representation."""
        repr_str = repr(user)
        assert 'test@example.com' in repr_str or 'User' in repr_str


@pytest.mark.unit
@pytest.mark.models
class TestUserAuthentication:
    """Tests for user authentication."""
    
    def test_user_is_authenticated(self, user):
        """Test Flask-Login is_authenticated property."""
        assert user.is_authenticated is True
    
    def test_user_is_active(self, user):
        """Test Flask-Login is_active property."""
        assert user.is_active is True
    
    def test_inactive_user(self, db, user):
        """Test inactive user."""
        user.is_active = False
        db.session.commit()
        
        assert user.is_active is False
    
    def test_user_get_id(self, user):
        """Test Flask-Login get_id method."""
        assert user.get_id() == str(user.id)
