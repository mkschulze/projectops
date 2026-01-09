"""
Tests for service classes - NotificationService, ExportService, EmailService, etc.
"""
import pytest


class TestNotificationService:
    """Tests for NotificationService class."""
    
    def test_notification_service_exists(self, app, db):
        """Test NotificationService exists."""
        from services import NotificationService
        assert NotificationService is not None
    
    def test_has_get_unread_count_method(self, app, db):
        """Test has get_unread_count method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'get_unread_count')
    
    def test_has_notify_task_assigned_method(self, app, db):
        """Test has notify_task_assigned method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'notify_task_assigned')
    
    def test_has_notify_status_changed_method(self, app, db):
        """Test has notify_status_changed method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'notify_status_changed')
    
    def test_has_notify_task_approved_method(self, app, db):
        """Test has notify_task_approved method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'notify_task_approved')
    
    def test_has_notify_task_rejected_method(self, app, db):
        """Test has notify_task_rejected method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'notify_task_rejected')
    
    def test_has_notify_reviewer_added_method(self, app, db):
        """Test has notify_reviewer_added method."""
        from services import NotificationService
        assert hasattr(NotificationService, 'notify_reviewer_added')


class TestExportService:
    """Tests for ExportService class."""
    
    def test_export_service_exists(self, app, db):
        """Test ExportService exists."""
        from services import ExportService
        assert ExportService is not None
    
    def test_has_export_tasks_to_excel_method(self, app, db):
        """Test has export_tasks_to_excel method."""
        from services import ExportService
        assert hasattr(ExportService, 'export_tasks_to_excel')


class TestCalendarService:
    """Tests for CalendarService class."""
    
    def test_calendar_service_exists(self, app, db):
        """Test CalendarService exists."""
        from services import CalendarService
        assert CalendarService is not None
    
    def test_has_generate_user_token_method(self, app, db):
        """Test has generate_user_token method."""
        from services import CalendarService
        assert hasattr(CalendarService, 'generate_user_token')
    
    def test_has_generate_ical_feed_method(self, app, db):
        """Test has generate_ical_feed method."""
        from services import CalendarService
        assert hasattr(CalendarService, 'generate_ical_feed')


class TestEmailService:
    """Tests for EmailService class."""
    
    def test_email_service_exists(self, app, db):
        """Test EmailService exists."""
        from services import EmailService
        assert EmailService is not None
    
    def test_has_is_enabled_property(self, app, db):
        """Test has is_enabled property."""
        from services import EmailService
        service = EmailService(app)
        assert hasattr(service, 'is_enabled')
    
    def test_has_send_email_method(self, app, db):
        """Test has send_email method."""
        from services import EmailService
        assert hasattr(EmailService, 'send_email')
    
    def test_has_init_app_method(self, app, db):
        """Test has init_app method."""
        from services import EmailService
        assert hasattr(EmailService, 'init_app')
    
    def test_has_provider_property(self, app, db):
        """Test has provider property."""
        from services import EmailService
        service = EmailService(app)
        assert hasattr(service, 'provider')


class TestRecurrenceService:
    """Tests for RecurrenceService class."""
    
    def test_recurrence_service_exists(self, app, db):
        """Test RecurrenceService exists."""
        from services import RecurrenceService
        assert RecurrenceService is not None
    
    def test_has_get_period_dates_method(self, app, db):
        """Test has get_period_dates method."""
        from services import RecurrenceService
        assert hasattr(RecurrenceService, 'get_period_dates')


class TestWorkflowService:
    """Tests for WorkflowService class."""
    
    def test_workflow_service_exists(self, app, db):
        """Test WorkflowService exists."""
        from services import WorkflowService
        assert WorkflowService is not None
    
    def test_has_submit_for_review_method(self, app, db):
        """Test has submit_for_review method."""
        from services import WorkflowService
        assert hasattr(WorkflowService, 'submit_for_review')
    
    def test_has_start_review_method(self, app, db):
        """Test has start_review method."""
        from services import WorkflowService
        assert hasattr(WorkflowService, 'start_review')
    
    def test_has_complete_task_method(self, app, db):
        """Test has complete_task method."""
        from services import WorkflowService
        assert hasattr(WorkflowService, 'complete_task')
    
    def test_has_restart_task_method(self, app, db):
        """Test has restart_task method."""
        from services import WorkflowService
        assert hasattr(WorkflowService, 'restart_task')


class TestApprovalService:
    """Additional tests for ApprovalService class."""
    
    def test_approval_service_exists(self, app, db):
        """Test ApprovalService exists."""
        from services import ApprovalService
        assert ApprovalService is not None
    
    def test_has_get_approval_status_method(self, app, db):
        """Test has get_approval_status method."""
        from services import ApprovalService
        assert hasattr(ApprovalService, 'get_approval_status')
    
    def test_has_can_user_review_method(self, app, db):
        """Test has can_user_review method."""
        from services import ApprovalService
        assert hasattr(ApprovalService, 'can_user_review')
    
    def test_has_approve_method(self, app, db):
        """Test has approve method."""
        from services import ApprovalService
        assert hasattr(ApprovalService, 'approve')
    
    def test_has_reject_method(self, app, db):
        """Test has reject method."""
        from services import ApprovalService
        assert hasattr(ApprovalService, 'reject')
    
    def test_has_reset_approvals_method(self, app, db):
        """Test has reset_approvals method."""
        from services import ApprovalService
        assert hasattr(ApprovalService, 'reset_approvals')


class TestApprovalResultEnum:
    """Tests for ApprovalResult enum."""
    
    def test_approval_result_exists(self, app, db):
        """Test ApprovalResult exists."""
        from services import ApprovalResult
        assert ApprovalResult is not None
    
    def test_has_success_value(self, app, db):
        """Test has SUCCESS value."""
        from services import ApprovalResult
        assert hasattr(ApprovalResult, 'SUCCESS')
    
    def test_has_already_approved_value(self, app, db):
        """Test has ALREADY_APPROVED value."""
        from services import ApprovalResult
        assert hasattr(ApprovalResult, 'ALREADY_APPROVED')
    
    def test_has_already_rejected_value(self, app, db):
        """Test has ALREADY_REJECTED value."""
        from services import ApprovalResult
        assert hasattr(ApprovalResult, 'ALREADY_REJECTED')
    
    def test_has_not_a_reviewer_value(self, app, db):
        """Test has NOT_A_REVIEWER value."""
        from services import ApprovalResult
        assert hasattr(ApprovalResult, 'NOT_A_REVIEWER')
    
    def test_has_wrong_status_value(self, app, db):
        """Test has WRONG_STATUS value."""
        from services import ApprovalResult
        assert hasattr(ApprovalResult, 'WRONG_STATUS')


class TestApprovalStatusDataclass:
    """Tests for ApprovalStatus dataclass."""
    
    def test_approval_status_exists(self, app, db):
        """Test ApprovalStatus exists."""
        from services import ApprovalStatus
        assert ApprovalStatus is not None
    
    def test_approval_status_is_dataclass(self, app, db):
        """Test ApprovalStatus is a dataclass."""
        from services import ApprovalStatus
        from dataclasses import is_dataclass
        assert is_dataclass(ApprovalStatus)
    
    def test_approval_status_has_total_reviewers(self, app, db):
        """Test ApprovalStatus has total_reviewers field."""
        from services import ApprovalStatus
        # Create instance to test
        status = ApprovalStatus(
            total_reviewers=2,
            approved_count=1,
            rejected_count=0,
            pending_count=1,
            is_complete=False,
            is_rejected=False,
            progress_percent=50,
            pending_reviewers=[],
            approved_reviewers=[],
            rejected_reviewers=[]
        )
        assert status.total_reviewers == 2
        assert status.approved_count == 1
        assert status.progress_percent == 50
