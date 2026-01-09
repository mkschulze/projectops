"""
Comprehensive tests for services.py to improve code coverage.
Tests ApprovalService, WorkflowService, NotificationService, and more.
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

from services import (
    ApprovalService, ApprovalResult, ApprovalStatus,
    WorkflowService, NotificationService, CalendarService,
    ExportService, RecurrenceService, EmailService
)
from models import Task, User, TaskReviewer, Team, Entity, Tenant, TenantMembership
from extensions import db


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def test_tenant(db):
    """Create a test tenant."""
    import uuid
    tenant = Tenant(
        name='Test Tenant',
        slug=f'test-tenant-{uuid.uuid4().hex[:8]}',
        is_active=True
    )
    db.session.add(tenant)
    db.session.commit()
    return tenant


@pytest.fixture
def owner_user(db, test_tenant):
    """Create an owner user."""
    import uuid
    user = User(
        email=f'owner-{uuid.uuid4().hex[:8]}@test.com',
        name='Task Owner',
        role='preparer',
        is_active=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    
    # Add to tenant
    membership = TenantMembership(tenant_id=test_tenant.id, user_id=user.id, role='member')
    db.session.add(membership)
    db.session.commit()
    
    return user


@pytest.fixture
def reviewer_user(db, test_tenant):
    """Create a reviewer user."""
    import uuid
    user = User(
        email=f'reviewer-{uuid.uuid4().hex[:8]}@test.com',
        name='Task Reviewer',
        role='reviewer',
        is_active=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    
    # Add to tenant
    membership = TenantMembership(tenant_id=test_tenant.id, user_id=user.id, role='member')
    db.session.add(membership)
    db.session.commit()
    
    return user


@pytest.fixture
def second_reviewer(db, test_tenant):
    """Create a second reviewer user."""
    import uuid
    user = User(
        email=f'reviewer2-{uuid.uuid4().hex[:8]}@test.com',
        name='Second Reviewer',
        role='reviewer',
        is_active=True
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    
    # Add to tenant
    membership = TenantMembership(tenant_id=test_tenant.id, user_id=user.id, role='member')
    db.session.add(membership)
    db.session.commit()
    
    return user


@pytest.fixture
def test_entity(db, test_tenant):
    """Create a test entity."""
    entity = Entity(
        name='Test Entity',
        tenant_id=test_tenant.id
    )
    db.session.add(entity)
    db.session.commit()
    return entity


@pytest.fixture
def draft_task(db, owner_user, reviewer_user, test_entity, test_tenant):
    """Create a task in draft status."""
    task = Task(
        title='Test Task',
        status='draft',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30)
    )
    db.session.add(task)
    db.session.commit()
    return task


@pytest.fixture
def in_review_task(db, owner_user, reviewer_user, test_entity, test_tenant):
    """Create a task in in_review status with a reviewer."""
    task = Task(
        title='In Review Task',
        status='in_review',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30),
        submitted_at=datetime.utcnow(),
        reviewed_at=datetime.utcnow()
    )
    db.session.add(task)
    db.session.commit()
    
    # Add reviewer
    tr = TaskReviewer(
        task_id=task.id,
        user_id=reviewer_user.id,
        order=1
    )
    db.session.add(tr)
    db.session.commit()
    
    return task


@pytest.fixture
def multi_reviewer_task(db, owner_user, reviewer_user, second_reviewer, test_entity, test_tenant):
    """Create a task with multiple reviewers."""
    task = Task(
        title='Multi Reviewer Task',
        status='in_review',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30),
        submitted_at=datetime.utcnow(),
        reviewed_at=datetime.utcnow()
    )
    db.session.add(task)
    db.session.commit()
    
    # Add reviewers
    tr1 = TaskReviewer(task_id=task.id, user_id=reviewer_user.id, order=1)
    tr2 = TaskReviewer(task_id=task.id, user_id=second_reviewer.id, order=2)
    db.session.add_all([tr1, tr2])
    db.session.commit()
    
    return task


@pytest.fixture
def submitted_task(db, owner_user, reviewer_user, test_entity, test_tenant):
    """Create a task in submitted status."""
    task = Task(
        title='Submitted Task',
        status='submitted',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30),
        submitted_at=datetime.utcnow()
    )
    db.session.add(task)
    db.session.commit()
    return task


@pytest.fixture
def approved_task(db, owner_user, reviewer_user, test_entity, test_tenant):
    """Create a task in approved status."""
    task = Task(
        title='Approved Task',
        status='approved',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30),
        approved_at=datetime.utcnow(),
        approved_by_id=reviewer_user.id
    )
    db.session.add(task)
    db.session.commit()
    return task


@pytest.fixture
def rejected_task(db, owner_user, reviewer_user, test_entity, test_tenant):
    """Create a task in rejected status."""
    task = Task(
        title='Rejected Task',
        status='rejected',
        owner_id=owner_user.id,
        entity_id=test_entity.id,
        tenant_id=test_tenant.id,
        year=2024,
        due_date=date.today() + timedelta(days=30),
        rejected_at=datetime.utcnow(),
        rejected_by_id=reviewer_user.id,
        rejection_reason='Missing documentation'
    )
    db.session.add(task)
    db.session.commit()
    return task


# =============================================================================
# APPROVAL SERVICE TESTS
# =============================================================================

class TestApprovalServiceGetStatus:
    """Test ApprovalService.get_approval_status method."""
    
    def test_get_status_no_reviewers(self, db, draft_task):
        """Test status with no reviewers assigned."""
        status = ApprovalService.get_approval_status(draft_task)
        
        assert status.total_reviewers == 0
        assert status.approved_count == 0
        assert status.rejected_count == 0
        assert status.pending_count == 0
        assert status.is_complete is False
        assert status.is_rejected is False
        assert status.progress_percent == 0
    
    def test_get_status_with_pending_reviewer(self, db, in_review_task):
        """Test status with pending reviewer."""
        status = ApprovalService.get_approval_status(in_review_task)
        
        assert status.total_reviewers == 1
        assert status.approved_count == 0
        assert status.pending_count == 1
        assert status.is_complete is False
        assert status.progress_percent == 0
    
    def test_get_status_with_approved_reviewer(self, db, in_review_task, reviewer_user):
        """Test status after reviewer approved."""
        tr = TaskReviewer.query.filter_by(
            task_id=in_review_task.id, 
            user_id=reviewer_user.id
        ).first()
        tr.approve("Looks good")
        db.session.commit()
        
        status = ApprovalService.get_approval_status(in_review_task)
        
        assert status.approved_count == 1
        assert status.is_complete is True
        assert status.progress_percent == 100
    
    def test_get_status_with_rejected_reviewer(self, db, in_review_task, reviewer_user):
        """Test status after reviewer rejected."""
        tr = TaskReviewer.query.filter_by(
            task_id=in_review_task.id, 
            user_id=reviewer_user.id
        ).first()
        tr.reject("Missing info")
        db.session.commit()
        
        status = ApprovalService.get_approval_status(in_review_task)
        
        assert status.rejected_count == 1
        assert status.is_rejected is True
    
    def test_get_status_partial_approval(self, db, multi_reviewer_task, reviewer_user):
        """Test status with partial approvals."""
        # Approve only first reviewer
        tr = TaskReviewer.query.filter_by(
            task_id=multi_reviewer_task.id, 
            user_id=reviewer_user.id
        ).first()
        tr.approve("Good")
        db.session.commit()
        
        status = ApprovalService.get_approval_status(multi_reviewer_task)
        
        assert status.total_reviewers == 2
        assert status.approved_count == 1
        assert status.pending_count == 1
        assert status.is_complete is False
        assert status.progress_percent == 50


class TestApprovalServiceCanUserReview:
    """Test ApprovalService.can_user_review method."""
    
    def test_cannot_review_if_not_in_review(self, db, draft_task, reviewer_user):
        """Test that review is blocked if task not in_review status."""
        can_review, reason = ApprovalService.can_user_review(draft_task, reviewer_user)
        
        assert can_review is False
        assert "in_review" in reason.lower()
    
    def test_can_review_as_assigned_reviewer(self, db, in_review_task, reviewer_user):
        """Test that assigned reviewer can review."""
        can_review, reason = ApprovalService.can_user_review(in_review_task, reviewer_user)
        
        assert can_review is True
        assert reason == "Direct reviewer"
    
    def test_cannot_review_if_not_reviewer(self, db, in_review_task, owner_user):
        """Test that non-reviewer cannot review."""
        can_review, reason = ApprovalService.can_user_review(in_review_task, owner_user)
        
        assert can_review is False
        assert "not a reviewer" in reason.lower()
    
    def test_cannot_review_if_already_approved(self, db, in_review_task, reviewer_user):
        """Test cannot review twice after approving."""
        tr = TaskReviewer.query.filter_by(
            task_id=in_review_task.id, 
            user_id=reviewer_user.id
        ).first()
        tr.approve("Done")
        db.session.commit()
        
        can_review, reason = ApprovalService.can_user_review(in_review_task, reviewer_user)
        
        assert can_review is False
        assert "already approved" in reason.lower()


class TestApprovalServiceApprove:
    """Test ApprovalService.approve method."""
    
    def test_approve_success(self, db, in_review_task, reviewer_user):
        """Test successful approval."""
        result, message = ApprovalService.approve(in_review_task, reviewer_user, "Looks great")
        db.session.commit()
        
        assert result == ApprovalResult.ALL_APPROVED
        assert "approved" in message.lower()
        
        # Task should be auto-transitioned
        db.session.refresh(in_review_task)
        assert in_review_task.status == 'approved'
    
    def test_approve_partial(self, db, multi_reviewer_task, reviewer_user):
        """Test approval with other reviewers still pending."""
        result, message = ApprovalService.approve(multi_reviewer_task, reviewer_user, "Good")
        db.session.commit()
        
        assert result == ApprovalResult.SUCCESS
        assert "pending" in message.lower()
        
        # Task should still be in_review
        db.session.refresh(multi_reviewer_task)
        assert multi_reviewer_task.status == 'in_review'
    
    def test_approve_wrong_status(self, db, draft_task, reviewer_user):
        """Test approval on wrong status task."""
        result, message = ApprovalService.approve(draft_task, reviewer_user)
        
        assert result == ApprovalResult.WRONG_STATUS


class TestApprovalServiceReject:
    """Test ApprovalService.reject method."""
    
    def test_reject_success(self, db, in_review_task, reviewer_user):
        """Test successful rejection."""
        result, message = ApprovalService.reject(in_review_task, reviewer_user, "Missing docs")
        db.session.commit()
        
        assert result == ApprovalResult.TASK_REJECTED
        
        # Task should be auto-transitioned
        db.session.refresh(in_review_task)
        assert in_review_task.status == 'rejected'
        assert in_review_task.rejection_reason == "Missing docs"


class TestApprovalServiceResetApprovals:
    """Test ApprovalService.reset_approvals method."""
    
    def test_reset_approvals(self, db, in_review_task, reviewer_user):
        """Test resetting approvals."""
        # First approve
        tr = TaskReviewer.query.filter_by(
            task_id=in_review_task.id, 
            user_id=reviewer_user.id
        ).first()
        tr.approve("Good")
        db.session.commit()
        
        # Verify approval
        db.session.refresh(tr)
        assert tr.has_approved is True
        
        # Reset
        count = ApprovalService.reset_approvals(in_review_task)
        db.session.commit()
        
        assert count == 1
        
        # Check reviewer is reset
        db.session.refresh(tr)
        assert tr.has_approved is False


class TestApprovalServiceGetNextAction:
    """Test ApprovalService.get_next_action_info method."""
    
    def test_next_action_draft(self, db, draft_task):
        """Test next action for draft task."""
        info = ApprovalService.get_next_action_info(draft_task)
        
        assert info['action'] == 'submit'
        assert info['by'] == 'owner'
    
    def test_next_action_in_review(self, db, in_review_task):
        """Test next action for in_review task."""
        info = ApprovalService.get_next_action_info(in_review_task)
        
        assert info['action'] == 'approve_or_reject'
        assert 'pending_reviewers' in info
    
    def test_next_action_approved(self, db, approved_task):
        """Test next action for approved task."""
        info = ApprovalService.get_next_action_info(approved_task)
        
        assert info['action'] == 'complete'
    
    def test_next_action_rejected(self, db, rejected_task):
        """Test next action for rejected task."""
        info = ApprovalService.get_next_action_info(rejected_task)
        
        assert info['action'] == 'revise_and_resubmit'


class TestApprovalServiceFormatSummary:
    """Test ApprovalService.format_approval_summary method."""
    
    def test_summary_no_reviewers(self, db, draft_task):
        """Test summary with no reviewers."""
        summary = ApprovalService.format_approval_summary(draft_task, 'de')
        assert "Keine Prüfer" in summary
        
        summary = ApprovalService.format_approval_summary(draft_task, 'en')
        assert "No reviewers" in summary
    
    def test_summary_pending(self, db, in_review_task):
        """Test summary with pending reviewers."""
        summary = ApprovalService.format_approval_summary(in_review_task, 'en')
        assert "pending" in summary.lower()


# =============================================================================
# WORKFLOW SERVICE TESTS
# =============================================================================

class TestWorkflowServiceSubmit:
    """Test WorkflowService.submit_for_review method."""
    
    def test_submit_success(self, db, draft_task, owner_user):
        """Test successful submission."""
        success, message = WorkflowService.submit_for_review(draft_task, owner_user)
        db.session.commit()
        
        assert success is True
        db.session.refresh(draft_task)
        assert draft_task.status == 'submitted'
        assert draft_task.submitted_at is not None
    
    def test_submit_wrong_status(self, db, in_review_task, owner_user):
        """Test submission from wrong status."""
        success, message = WorkflowService.submit_for_review(in_review_task, owner_user)
        
        assert success is False
        assert "draft" in message.lower()


class TestWorkflowServiceStartReview:
    """Test WorkflowService.start_review method."""
    
    def test_start_review_success(self, db, submitted_task, reviewer_user):
        """Test starting review."""
        success, message = WorkflowService.start_review(submitted_task, reviewer_user)
        db.session.commit()
        
        assert success is True
        db.session.refresh(submitted_task)
        assert submitted_task.status == 'in_review'
    
    def test_start_review_wrong_status(self, db, draft_task, reviewer_user):
        """Test starting review from wrong status."""
        success, message = WorkflowService.start_review(draft_task, reviewer_user)
        
        assert success is False


class TestWorkflowServiceComplete:
    """Test WorkflowService.complete_task method."""
    
    def test_complete_success(self, db, approved_task, owner_user):
        """Test completing approved task."""
        # owner_user doesn't have permission - need manager
        # Change to use a manager user
        owner_user.role = 'manager'
        db.session.commit()
        
        success, message = WorkflowService.complete_task(approved_task, owner_user, "All done")
        db.session.commit()
        
        assert success is True
        db.session.refresh(approved_task)
        assert approved_task.status == 'completed'
        assert approved_task.completed_at is not None
    
    def test_complete_wrong_status(self, db, draft_task, owner_user):
        """Test completing from wrong status."""
        success, message = WorkflowService.complete_task(draft_task, owner_user)
        
        assert success is False


class TestWorkflowServiceRestart:
    """Test WorkflowService.restart_task method."""
    
    def test_restart_success(self, db, rejected_task, owner_user):
        """Test restarting rejected task."""
        success, message = WorkflowService.restart_task(rejected_task, owner_user)
        db.session.commit()
        
        assert success is True
        db.session.refresh(rejected_task)
        assert rejected_task.status == 'draft'
        assert rejected_task.rejection_reason is None
    
    def test_restart_wrong_status(self, db, draft_task, owner_user):
        """Test restarting from wrong status."""
        success, message = WorkflowService.restart_task(draft_task, owner_user)
        
        assert success is False


class TestWorkflowServiceTimeline:
    """Test WorkflowService.get_workflow_timeline method."""
    
    def test_timeline_draft(self, db, draft_task):
        """Test timeline for draft task."""
        timeline = WorkflowService.get_workflow_timeline(draft_task)
        
        assert len(timeline) >= 1
        assert any(e['action'] == 'created' for e in timeline)
    
    def test_timeline_in_review(self, db, in_review_task):
        """Test timeline for in_review task."""
        timeline = WorkflowService.get_workflow_timeline(in_review_task)
        
        # Should have created, submitted, review_started
        assert any(e['action'] == 'submitted' for e in timeline)
        assert any(e['action'] == 'review_started' for e in timeline)


# =============================================================================
# NOTIFICATION SERVICE TESTS
# =============================================================================

class TestNotificationServiceCreate:
    """Test NotificationService.create method."""
    
    def test_create_notification(self, db, owner_user):
        """Test creating a notification."""
        notification = NotificationService.create(
            user_id=owner_user.id,
            notification_type='info',
            title_de='Test Benachrichtigung',
            title_en='Test Notification',
            message_de='Dies ist ein Test',
            message_en='This is a test'
        )
        
        db.session.commit()
        
        assert notification is not None
        assert notification.user_id == owner_user.id
        assert notification.title_de == 'Test Benachrichtigung'
    
    def test_create_notification_with_entity(self, db, owner_user, draft_task):
        """Test creating a notification linked to an entity."""
        notification = NotificationService.create(
            user_id=owner_user.id,
            notification_type='task_assigned',
            title_de='Neue Aufgabe',
            title_en='New Task',
            entity_type='task',
            entity_id=draft_task.id
        )
        
        db.session.commit()
        
        assert notification.entity_type == 'task'
        assert notification.entity_id == draft_task.id


class TestNotificationServiceNotifyUsers:
    """Test NotificationService.notify_users method."""
    
    def test_notify_multiple_users(self, db, owner_user, reviewer_user):
        """Test notifying multiple users."""
        notifications = NotificationService.notify_users(
            user_ids=[owner_user.id, reviewer_user.id],
            notification_type='announcement',
            title_de='Systemwartung',
            title_en='System Maintenance'
        )
        
        db.session.commit()
        
        assert len(notifications) == 2


# =============================================================================
# RECURRENCE SERVICE TESTS
# =============================================================================

class TestRecurrenceServicePeriodDates:
    """Test RecurrenceService.get_period_dates method."""
    
    def test_monthly_periods(self):
        """Test monthly period generation."""
        periods = RecurrenceService.get_period_dates('monthly', 2024, day_offset=10)
        
        assert len(periods) == 12
        # Check labels
        labels = [p[0] for p in periods]
        assert 'M01' in labels
        assert 'M12' in labels
    
    def test_quarterly_periods(self):
        """Test quarterly period generation."""
        periods = RecurrenceService.get_period_dates('quarterly', 2024, day_offset=10)
        
        assert len(periods) == 4
        labels = [p[0] for p in periods]
        assert 'Q1' in labels
        assert 'Q4' in labels
    
    def test_annual_periods(self):
        """Test annual period generation."""
        periods = RecurrenceService.get_period_dates('annual', 2024, day_offset=10)
        
        assert len(periods) == 1
        # The label format may be different - just check we have one period
        assert periods[0][1].year in [2024, 2025]  # Due date could be in next year


# =============================================================================
# EMAIL SERVICE TESTS
# =============================================================================

class TestEmailService:
    """Test EmailService."""
    
    def test_email_service_init(self, app):
        """Test EmailService initialization."""
        email_service = EmailService(app)
        
        assert email_service.app == app
    
    def test_email_disabled(self, app):
        """Test email when disabled."""
        app.config['MAIL_ENABLED'] = False
        email_service = EmailService(app)
        
        result = email_service.send_email(
            to_email='test@example.com',
            subject='Test',
            html_content='<p>Test</p>'
        )
        
        # Should return True even when disabled (to not block app logic)
        assert result is True
    
    def test_provider_property(self, app):
        """Test provider property."""
        app.config['MAIL_PROVIDER'] = 'sendgrid'
        email_service = EmailService(app)
        
        assert email_service.provider == 'sendgrid'


# =============================================================================
# CALENDAR SERVICE TESTS
# =============================================================================

class TestCalendarServiceAdvanced:
    """Additional tests for CalendarService."""
    
    def test_generate_user_token(self, db, owner_user):
        """Test token generation."""
        token = CalendarService.generate_user_token(owner_user.id)
        
        assert token is not None
        assert len(token) > 10
    
    def test_token_uniqueness(self, db, owner_user):
        """Test that each call generates a different token."""
        token1 = CalendarService.generate_user_token(owner_user.id)
        token2 = CalendarService.generate_user_token(owner_user.id)
        
        # Each call should generate a different token
        assert token1 != token2
