"""
Tests for Task model methods and behaviors.
Focused on improving code coverage for models.py Task class.
"""
import pytest
from datetime import datetime, date, timedelta


class TestTaskStatusConstants:
    """Tests for Task status constants."""
    
    def test_valid_statuses_defined(self, app, db):
        """Test VALID_STATUSES is defined."""
        from models import Task
        assert hasattr(Task, 'VALID_STATUSES')
        assert 'draft' in Task.VALID_STATUSES
        assert 'submitted' in Task.VALID_STATUSES
        assert 'completed' in Task.VALID_STATUSES
    
    def test_status_transitions_defined(self, app, db):
        """Test STATUS_TRANSITIONS is defined."""
        from models import Task
        assert hasattr(Task, 'STATUS_TRANSITIONS')
        assert 'draft' in Task.STATUS_TRANSITIONS
        assert 'submitted' in Task.STATUS_TRANSITIONS['draft']
    
    def test_status_permissions_defined(self, app, db):
        """Test STATUS_PERMISSIONS is defined."""
        from models import Task
        assert hasattr(Task, 'STATUS_PERMISSIONS')
        assert 'draft->submitted' in Task.STATUS_PERMISSIONS


class TestTaskArchiveMethods:
    """Tests for Task archive and restore methods."""
    
    def test_archive_method_exists(self, app, db):
        """Test Task has archive method."""
        from models import Task
        assert hasattr(Task, 'archive')
        assert callable(getattr(Task, 'archive'))
    
    def test_restore_method_exists(self, app, db):
        """Test Task has restore method."""
        from models import Task
        assert hasattr(Task, 'restore')
        assert callable(getattr(Task, 'restore'))


class TestTaskTeamMethods:
    """Tests for Task team methods."""
    
    def test_get_owner_display_method_exists(self, app, db):
        """Test get_owner_display method exists."""
        from models import Task
        assert hasattr(Task, 'get_owner_display')
    
    def test_get_all_assigned_users_method_exists(self, app, db):
        """Test get_all_assigned_users method exists."""
        from models import Task
        assert hasattr(Task, 'get_all_assigned_users')
    
    def test_is_assigned_to_user_method_exists(self, app, db):
        """Test is_assigned_to_user method exists."""
        from models import Task
        assert hasattr(Task, 'is_assigned_to_user')
    
    def test_is_reviewer_via_team_method_exists(self, app, db):
        """Test is_reviewer_via_team method exists."""
        from models import Task
        assert hasattr(Task, 'is_reviewer_via_team')


class TestTaskReviewerMethods:
    """Tests for Task multi-reviewer methods."""
    
    def test_get_reviewer_users_method_exists(self, app, db):
        """Test get_reviewer_users method exists."""
        from models import Task
        assert hasattr(Task, 'get_reviewer_users')
    
    def test_get_reviewer_ids_method_exists(self, app, db):
        """Test get_reviewer_ids method exists."""
        from models import Task
        assert hasattr(Task, 'get_reviewer_ids')
    
    def test_add_reviewer_method_exists(self, app, db):
        """Test add_reviewer method exists."""
        from models import Task
        assert hasattr(Task, 'add_reviewer')
    
    def test_remove_reviewer_method_exists(self, app, db):
        """Test remove_reviewer method exists."""
        from models import Task
        assert hasattr(Task, 'remove_reviewer')
    
    def test_set_reviewers_method_exists(self, app, db):
        """Test set_reviewers method exists."""
        from models import Task
        assert hasattr(Task, 'set_reviewers')
    
    def test_get_reviewer_status_method_exists(self, app, db):
        """Test get_reviewer_status method exists."""
        from models import Task
        assert hasattr(Task, 'get_reviewer_status')
    
    def test_approve_by_reviewer_method_exists(self, app, db):
        """Test approve_by_reviewer method exists."""
        from models import Task
        assert hasattr(Task, 'approve_by_reviewer')
    
    def test_reject_by_reviewer_method_exists(self, app, db):
        """Test reject_by_reviewer method exists."""
        from models import Task
        assert hasattr(Task, 'reject_by_reviewer')
    
    def test_reset_all_approvals_method_exists(self, app, db):
        """Test reset_all_approvals method exists."""
        from models import Task
        assert hasattr(Task, 'reset_all_approvals')
    
    def test_get_approval_count_method_exists(self, app, db):
        """Test get_approval_count method exists."""
        from models import Task
        assert hasattr(Task, 'get_approval_count')
    
    def test_all_reviewers_approved_method_exists(self, app, db):
        """Test all_reviewers_approved method exists."""
        from models import Task
        assert hasattr(Task, 'all_reviewers_approved')
    
    def test_any_reviewer_rejected_method_exists(self, app, db):
        """Test any_reviewer_rejected method exists."""
        from models import Task
        assert hasattr(Task, 'any_reviewer_rejected')
    
    def test_is_reviewer_method_exists(self, app, db):
        """Test is_reviewer method exists."""
        from models import Task
        assert hasattr(Task, 'is_reviewer')
    
    def test_get_pending_reviewers_method_exists(self, app, db):
        """Test get_pending_reviewers method exists."""
        from models import Task
        assert hasattr(Task, 'get_pending_reviewers')


class TestTaskTransitionMethods:
    """Tests for Task status transition methods."""
    
    def test_can_transition_to_method_exists(self, app, db):
        """Test can_transition_to method exists."""
        from models import Task
        assert hasattr(Task, 'can_transition_to')
    
    def test_get_allowed_transitions_method_exists(self, app, db):
        """Test get_allowed_transitions method exists."""
        from models import Task
        assert hasattr(Task, 'get_allowed_transitions')


class TestTaskReviewerModel:
    """Tests for TaskReviewer model."""
    
    def test_task_reviewer_model_exists(self, app, db):
        """Test TaskReviewer model exists."""
        from models import TaskReviewer
        assert TaskReviewer is not None
    
    def test_task_reviewer_has_approve_method(self, app, db):
        """Test TaskReviewer has approve method."""
        from models import TaskReviewer
        assert hasattr(TaskReviewer, 'approve')
    
    def test_task_reviewer_has_reject_method(self, app, db):
        """Test TaskReviewer has reject method."""
        from models import TaskReviewer
        assert hasattr(TaskReviewer, 'reject')
    
    def test_task_reviewer_has_reset_method(self, app, db):
        """Test TaskReviewer has reset method."""
        from models import TaskReviewer
        assert hasattr(TaskReviewer, 'reset')


class TestUserModelMethods:
    """Tests for User model methods."""
    
    def test_user_set_password_method(self, db, user):
        """Test User set_password method."""
        user.set_password('newpassword123')
        db.session.commit()
        
        assert user.check_password('newpassword123')
    
    def test_user_check_password_method(self, db, user):
        """Test User check_password method."""
        user.set_password('testpass123')
        db.session.commit()
        
        assert user.check_password('testpass123') is True
        assert user.check_password('wrongpass') is False
    
    def test_user_is_authenticated(self, db, user):
        """Test User is_authenticated property."""
        assert user.is_authenticated is True
    
    def test_user_is_active_property(self, db, user):
        """Test User is_active property."""
        assert user.is_active is True
    
    def test_user_get_id_method(self, db, user):
        """Test User get_id method."""
        user_id = user.get_id()
        assert user_id == str(user.id)


class TestTenantModelMethods:
    """Tests for Tenant model methods."""
    
    def test_tenant_archive_method(self, db, tenant, user):
        """Test Tenant archive method."""
        assert hasattr(tenant, 'archive')
        
        tenant.archive(user=user)
        db.session.commit()
        
        assert tenant.is_archived is True
    
    def test_tenant_restore_method(self, db, tenant):
        """Test Tenant restore method."""
        tenant.is_archived = True
        db.session.commit()
        
        tenant.restore()
        db.session.commit()
        
        assert tenant.is_archived is False


class TestTenantMembershipModel:
    """Tests for TenantMembership model."""
    
    def test_membership_has_is_manager_or_above(self, app, db):
        """Test TenantMembership has is_manager_or_above method."""
        from models import TenantMembership
        assert hasattr(TenantMembership, 'is_manager_or_above')
    
    def test_membership_has_can_edit(self, app, db):
        """Test TenantMembership has can_edit method."""
        from models import TenantMembership
        assert hasattr(TenantMembership, 'can_edit')
    
    def test_membership_has_is_admin_property(self, app, db):
        """Test TenantMembership has is_admin property."""
        from models import TenantMembership
        assert 'is_admin' in dir(TenantMembership)


class TestNotificationModel:
    """Tests for Notification model."""
    
    def test_notification_type_enum_exists(self, app, db):
        """Test NotificationType enum exists."""
        from models import NotificationType
        assert NotificationType is not None
    
    def test_notification_model_exists(self, app, db):
        """Test Notification model exists."""
        from models import Notification
        assert Notification is not None
    
    def test_notification_has_mark_as_read_method(self, app, db):
        """Test Notification has mark_as_read method."""
        from models import Notification
        assert hasattr(Notification, 'mark_as_read')


class TestTaskCategoryModel:
    """Tests for TaskCategory model."""
    
    def test_task_category_exists(self, app, db):
        """Test TaskCategory model exists."""
        from models import TaskCategory
        assert TaskCategory is not None
    
    def test_task_category_has_name_field(self, app, db):
        """Test TaskCategory has name field."""
        from models import TaskCategory
        assert hasattr(TaskCategory, 'name')


class TestTaskTemplateModel:
    """Tests for TaskTemplate model."""
    
    def test_task_template_exists(self, app, db):
        """Test TaskTemplate model exists."""
        from models import TaskTemplate
        assert TaskTemplate is not None
    
    def test_task_template_has_keyword_field(self, app, db):
        """Test TaskTemplate has keyword field."""
        from models import TaskTemplate
        assert hasattr(TaskTemplate, 'keyword')


class TestTaskPresetModel:
    """Tests for TaskPreset model."""
    
    def test_task_preset_exists(self, app, db):
        """Test TaskPreset model exists."""
        from models import TaskPreset
        assert TaskPreset is not None
    
    def test_task_preset_has_title_field(self, app, db):
        """Test TaskPreset has title field."""
        from models import TaskPreset
        assert hasattr(TaskPreset, 'title')
    
    def test_task_preset_has_recurrence_frequency_field(self, app, db):
        """Test TaskPreset has recurrence_frequency field."""
        from models import TaskPreset
        assert hasattr(TaskPreset, 'recurrence_frequency')


class TestTeamModel:
    """Tests for Team model."""
    
    def test_team_model_exists(self, app, db):
        """Test Team model exists."""
        from models import Team
        assert Team is not None
    
    def test_team_has_name_field(self, app, db):
        """Test Team has name field."""
        from models import Team
        assert hasattr(Team, 'name')
    
    def test_team_has_is_member_method(self, app, db):
        """Test Team has is_member method."""
        from models import Team
        assert hasattr(Team, 'is_member')


class TestUserEntityModel:
    """Tests for UserEntity model."""
    
    def test_user_entity_exists(self, app, db):
        """Test UserEntity model exists."""
        from models import UserEntity
        assert UserEntity is not None
    
    def test_user_entity_has_access_level(self, app, db):
        """Test UserEntity has access_level field."""
        from models import UserEntity
        assert hasattr(UserEntity, 'access_level')


class TestEntityAccessLevel:
    """Tests for EntityAccessLevel enum."""
    
    def test_entity_access_level_exists(self, app, db):
        """Test EntityAccessLevel enum exists."""
        from models import EntityAccessLevel
        assert EntityAccessLevel is not None
    
    def test_access_level_values(self, app, db):
        """Test EntityAccessLevel has expected values."""
        from models import EntityAccessLevel
        assert hasattr(EntityAccessLevel, 'VIEW')
        assert hasattr(EntityAccessLevel, 'EDIT')
        assert hasattr(EntityAccessLevel, 'MANAGE')
