"""
Unit tests for extensions module.
"""
import pytest


@pytest.mark.unit
class TestExtensions:
    """Tests for Flask extensions."""
    
    def test_db_extension_exists(self):
        """Test SQLAlchemy db instance exists."""
        from extensions import db
        
        assert db is not None
    
    def test_login_manager_exists(self):
        """Test LoginManager instance exists."""
        from extensions import login_manager
        
        assert login_manager is not None
    
    def test_migrate_exists(self):
        """Test Flask-Migrate instance exists."""
        from extensions import migrate
        
        assert migrate is not None
    
    def test_socketio_exists(self):
        """Test SocketIO instance exists."""
        from extensions import socketio
        
        assert socketio is not None


@pytest.mark.unit
class TestDatabaseSession:
    """Tests for database session functionality."""
    
    def test_db_session_add(self, db, tenant):
        """Test adding objects to session."""
        from models import Tenant
        
        new_tenant = Tenant(
            name='Session Test Tenant',
            slug='session-test'
        )
        
        db.session.add(new_tenant)
        db.session.commit()
        
        assert new_tenant.id is not None
        
        db.session.delete(new_tenant)
        db.session.commit()
    
    def test_db_session_query(self, db, user):
        """Test querying objects."""
        from models import User
        
        queried_user = User.query.get(user.id)
        
        assert queried_user is not None
        assert queried_user.id == user.id
    
    def test_db_session_filter(self, db, user):
        """Test filtering objects."""
        from models import User
        
        users = User.query.filter_by(email=user.email).all()
        
        assert len(users) >= 1
        assert users[0].email == user.email
    
    def test_db_session_rollback(self, db):
        """Test session rollback."""
        from models import Tenant
        
        tenant = Tenant(
            name='Rollback Test',
            slug='rollback-test'
        )
        
        db.session.add(tenant)
        # Don't commit, rollback instead
        db.session.rollback()
        
        # Should not be in database
        result = Tenant.query.filter_by(slug='rollback-test').first()
        assert result is None
