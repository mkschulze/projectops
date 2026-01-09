"""
Unit tests for services.
Tests verify that service classes exist and have expected methods.
"""
import pytest


@pytest.mark.unit
@pytest.mark.services
class TestNotificationService:
    """Tests for NotificationService."""
    
    def test_notification_service_exists(self):
        """Test NotificationService can be imported."""
        from services import NotificationService
        
        assert NotificationService is not None
    
    def test_notification_service_has_create_method(self):
        """Test NotificationService has create method."""
        from services import NotificationService
        
        assert hasattr(NotificationService, 'create')
        assert callable(NotificationService.create)
    
    def test_notification_service_has_notify_users_method(self):
        """Test NotificationService has notify_users method."""
        from services import NotificationService
        
        assert hasattr(NotificationService, 'notify_users')
        assert callable(NotificationService.notify_users)


@pytest.mark.unit
@pytest.mark.services
class TestApprovalService:
    """Tests for ApprovalService."""
    
    def test_approval_service_exists(self):
        """Test ApprovalService can be imported."""
        from services import ApprovalService
        
        assert ApprovalService is not None


@pytest.mark.unit
@pytest.mark.services
class TestCalendarService:
    """Tests for CalendarService."""
    
    def test_calendar_service_exists(self):
        """Test CalendarService can be imported."""
        from services import CalendarService
        
        assert CalendarService is not None
    
    def test_generate_user_token(self, db, user):
        """Test generating calendar subscription token."""
        from services import CalendarService
        
        token = CalendarService.generate_user_token(user.id)
        
        assert token is not None
        assert len(token) > 20  # Should be a reasonably long token
    
    def test_token_is_unique_per_call(self, db, user):
        """Test that each call generates a different token."""
        from services import CalendarService
        
        token1 = CalendarService.generate_user_token(user.id)
        token2 = CalendarService.generate_user_token(user.id)
        
        # Each call should generate a different token
        assert token1 != token2
    
    def test_has_generate_ical_feed_method(self):
        """Test CalendarService has generate_ical_feed method."""
        from services import CalendarService
        
        assert hasattr(CalendarService, 'generate_ical_feed')
        assert callable(CalendarService.generate_ical_feed)


@pytest.mark.unit
@pytest.mark.services
class TestExportService:
    """Tests for ExportService."""
    
    def test_export_service_exists(self):
        """Test ExportService can be imported."""
        from services import ExportService
        
        assert ExportService is not None


@pytest.mark.unit
@pytest.mark.services
class TestRecurrenceService:
    """Tests for RecurrenceService."""
    
    def test_recurrence_service_exists(self):
        """Test RecurrenceService can be imported."""
        from services import RecurrenceService
        
        assert RecurrenceService is not None


@pytest.mark.unit
@pytest.mark.services
class TestNotificationType:
    """Tests for NotificationType enum."""
    
    def test_notification_type_exists(self):
        """Test NotificationType can be imported."""
        from models import NotificationType
        
        assert NotificationType is not None
    
    def test_notification_type_has_task_assigned(self):
        """Test NotificationType has TASK_ASSIGNED."""
        from models import NotificationType
        
        assert hasattr(NotificationType, 'TASK_ASSIGNED')


@pytest.mark.unit
@pytest.mark.services
class TestRecurrenceService:
    """Tests for RecurrenceService."""
    
    def test_recurrence_service_exists(self):
        """Test RecurrenceService can be imported."""
        from services import RecurrenceService
        
        assert RecurrenceService is not None
