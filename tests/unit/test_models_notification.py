"""
Unit tests for Notification model and related functionality.
"""
import pytest


@pytest.mark.unit
@pytest.mark.models
class TestNotificationModel:
    """Tests for Notification model."""
    
    def test_notification_model_exists(self):
        """Test Notification model can be imported."""
        from models import Notification
        
        assert Notification is not None
    
    def test_notification_creation(self, db, user):
        """Test creating a notification."""
        from models import Notification, NotificationType
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.TASK_ASSIGNED.value,
            title='Test Notification',
            title_de='Test Benachrichtigung',
            title_en='Test Notification'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        assert notification.id is not None
        assert notification.user_id == user.id
        assert notification.is_read is False
        
        db.session.delete(notification)
        db.session.commit()
    
    def test_notification_defaults(self, db, user):
        """Test notification default values."""
        from models import Notification, NotificationType
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.TASK_ASSIGNED.value,
            title='Test',
            title_de='Test',
            title_en='Test'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        assert notification.is_read is False
        assert notification.created_at is not None
        
        db.session.delete(notification)
        db.session.commit()


@pytest.mark.unit
@pytest.mark.models
class TestNotificationType:
    """Tests for NotificationType enum."""
    
    def test_notification_types_exist(self):
        """Test all expected notification types exist."""
        from models import NotificationType
        
        # Check core notification types exist
        assert hasattr(NotificationType, 'TASK_ASSIGNED')
        assert hasattr(NotificationType, 'TASK_STATUS_CHANGED')
        assert hasattr(NotificationType, 'TASK_DUE_SOON')
    
    def test_notification_type_values(self):
        """Test notification type values are strings."""
        from models import NotificationType
        
        assert isinstance(NotificationType.TASK_ASSIGNED.value, str)


@pytest.mark.unit
@pytest.mark.models
class TestUserNotificationPreferences:
    """Tests for user notification preferences."""
    
    def test_user_has_email_notifications_field(self, user):
        """Test user has email_notifications preference."""
        assert hasattr(user, 'email_notifications')
    
    def test_user_has_email_on_assignment_field(self, user):
        """Test user has email_on_assignment preference."""
        assert hasattr(user, 'email_on_assignment')
    
    def test_user_has_email_on_status_change_field(self, user):
        """Test user has email_on_status_change preference."""
        assert hasattr(user, 'email_on_status_change')
    
    def test_default_notification_preferences(self, user):
        """Test default notification preferences."""
        # Email notifications should be on by default
        assert user.email_notifications is True
        assert user.email_on_assignment is True
        assert user.email_on_status_change is True
