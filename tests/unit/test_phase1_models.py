"""
Phase 1 Tests: Extended model coverage for User, Team, TaskReviewer, UserEntity.
Target: Increase models.py coverage from 63% to 80%+
"""
import pytest
from datetime import datetime, timedelta
from models import (
    User, Team, TaskReviewer, UserEntity, EntityAccessLevel,
    TenantMembership, Task, Entity, db
)


@pytest.mark.unit
@pytest.mark.models
class TestUserTenantMethods:
    """Tests for User multi-tenancy methods."""
    
    def test_user_tenants_property(self, db, user, tenant):
        """Test tenants property returns active tenants."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        tenants = user.tenants
        assert len(tenants) >= 1
        assert tenant in tenants
    
    def test_user_tenants_excludes_inactive(self, db, user, tenant):
        """Test tenants property excludes inactive tenants."""
        tenant.is_active = False
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        tenants = user.tenants
        assert tenant not in tenants
    
    def test_user_all_tenants_includes_inactive(self, db, user, tenant):
        """Test all_tenants includes inactive tenants."""
        tenant.is_active = False
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        all_tenants = user.all_tenants
        assert tenant in all_tenants
    
    def test_user_default_tenant(self, db, user, tenant):
        """Test default_tenant returns default or first active."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member',
            is_default=True
        )
        db.session.add(membership)
        db.session.commit()
        
        assert user.default_tenant == tenant
    
    def test_user_default_tenant_fallback(self, db, user, tenant):
        """Test default_tenant fallback when no default set."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member',
            is_default=False
        )
        db.session.add(membership)
        db.session.commit()
        
        # Should fall back to first active tenant
        default = user.default_tenant
        assert default is not None
    
    def test_get_role_in_tenant(self, db, user, tenant):
        """Test get_role_in_tenant returns correct role."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        role = user.get_role_in_tenant(tenant.id)
        assert role == 'admin'
    
    def test_get_role_in_tenant_none(self, db, user):
        """Test get_role_in_tenant returns None if not member."""
        role = user.get_role_in_tenant(99999)
        assert role is None
    
    def test_is_tenant_admin(self, db, user, tenant):
        """Test is_tenant_admin check."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert user.is_tenant_admin(tenant.id) is True
    
    def test_is_tenant_manager_or_above(self, db, user, tenant):
        """Test is_tenant_manager_or_above check."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='manager'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert user.is_tenant_manager_or_above(tenant.id) is True
    
    def test_can_access_tenant(self, db, user, tenant):
        """Test can_access_tenant check."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert user.can_access_tenant(tenant.id) is True
        assert user.can_access_tenant(99999) is False
    
    def test_superadmin_can_access_any_tenant(self, db, admin_user, tenant):
        """Test superadmin can access any tenant."""
        admin_user.is_superadmin = True
        db.session.commit()
        
        assert admin_user.can_access_tenant(tenant.id) is True
    
    def test_set_current_tenant(self, db, user, tenant):
        """Test set_current_tenant method."""
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        result = user.set_current_tenant(tenant.id)
        assert result is True
        assert user.current_tenant_id == tenant.id
    
    def test_set_current_tenant_no_access(self, db, user, tenant):
        """Test set_current_tenant fails without access."""
        result = user.set_current_tenant(tenant.id)
        assert result is False


@pytest.mark.unit
@pytest.mark.models
class TestUserCalendarToken:
    """Tests for User calendar token methods."""
    
    def test_get_or_create_calendar_token_creates(self, db, user):
        """Test get_or_create_calendar_token creates token."""
        user.calendar_token = None
        db.session.commit()
        
        token = user.get_or_create_calendar_token()
        assert token is not None
        assert len(token) > 20
    
    def test_get_or_create_calendar_token_returns_existing(self, db, user):
        """Test get_or_create_calendar_token returns existing token."""
        user.calendar_token = 'existing_token_12345'
        db.session.commit()
        
        token = user.get_or_create_calendar_token()
        assert token == 'existing_token_12345'
    
    def test_regenerate_calendar_token(self, db, user):
        """Test regenerate_calendar_token creates new token."""
        old_token = 'old_token_abc123'
        user.calendar_token = old_token
        db.session.commit()
        
        new_token = user.regenerate_calendar_token()
        assert new_token != old_token
        assert len(new_token) > 20


@pytest.mark.unit
@pytest.mark.models
class TestUserTeamMethods:
    """Tests for User team-related methods."""
    
    def test_get_teams(self, db, user, tenant):
        """Test get_teams returns user's teams."""
        team = Team(name='Test Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        team.add_member(user)
        db.session.commit()
        
        teams = user.get_teams()
        assert len(teams) >= 1


@pytest.mark.unit
@pytest.mark.models
class TestTeamModel:
    """Tests for Team model."""
    
    def test_team_creation(self, db, tenant):
        """Test team is created correctly."""
        team = Team(
            name='Engineering',
            name_de='Technik',
            name_en='Engineering',
            tenant_id=tenant.id,
            color='#FF5733'
        )
        db.session.add(team)
        db.session.commit()
        
        assert team.id is not None
        assert team.name == 'Engineering'
        assert team.is_active is True
    
    def test_add_member(self, db, user, tenant):
        """Test adding member to team."""
        team = Team(name='Test Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        team.add_member(user)
        db.session.commit()
        
        assert team.is_member(user) is True
    
    def test_add_member_idempotent(self, db, user, tenant):
        """Test adding same member twice is idempotent."""
        team = Team(name='Test Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        team.add_member(user)
        team.add_member(user)  # Should not raise error
        db.session.commit()
        
        assert team.get_member_count() == 1
    
    def test_remove_member(self, db, user, tenant):
        """Test removing member from team."""
        team = Team(name='Test Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        team.add_member(user)
        db.session.commit()
        
        team.remove_member(user)
        db.session.commit()
        
        assert team.is_member(user) is False
    
    def test_is_member(self, db, user, tenant):
        """Test is_member check."""
        team = Team(name='Test Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        assert team.is_member(user) is False
        
        team.add_member(user)
        db.session.commit()
        
        assert team.is_member(user) is True
    
    def test_get_member_count(self, db, tenant):
        """Test get_member_count returns correct count."""
        # Create fresh users for this test to avoid fixture interference
        user1 = User(email='member1@test.com', name='Member 1', role='preparer')
        user1.set_password('test123')
        user2 = User(email='member2@test.com', name='Member 2', role='preparer')
        user2.set_password('test123')
        db.session.add_all([user1, user2])
        db.session.commit()
        
        team = Team(name='Count Team', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        # Fresh team should have 0 members
        assert team.get_member_count() == 0
        
        team.add_member(user1)
        team.add_member(user2)
        db.session.commit()
        
        assert team.get_member_count() == 2
    
    def test_get_name_german(self, db, tenant):
        """Test get_name returns German name."""
        team = Team(
            name='team-1',
            name_de='Deutsches Team',
            name_en='English Team',
            tenant_id=tenant.id
        )
        db.session.add(team)
        db.session.commit()
        
        assert team.get_name('de') == 'Deutsches Team'
    
    def test_get_name_english(self, db, tenant):
        """Test get_name returns English name."""
        team = Team(
            name='team-1',
            name_de='Deutsches Team',
            name_en='English Team',
            tenant_id=tenant.id
        )
        db.session.add(team)
        db.session.commit()
        
        assert team.get_name('en') == 'English Team'
    
    def test_get_name_fallback(self, db, tenant):
        """Test get_name fallback when translation missing."""
        team = Team(
            name='team-1',
            name_de='Deutsches Team',
            tenant_id=tenant.id
        )
        db.session.add(team)
        db.session.commit()
        
        # English not set, should fallback to German
        assert team.get_name('en') == 'Deutsches Team'
    
    def test_get_description_german(self, db, tenant):
        """Test get_description returns German description."""
        team = Team(
            name='team-1',
            description_de='Deutsche Beschreibung',
            description_en='English Description',
            tenant_id=tenant.id
        )
        db.session.add(team)
        db.session.commit()
        
        assert team.get_description('de') == 'Deutsche Beschreibung'
    
    def test_get_description_english(self, db, tenant):
        """Test get_description returns English description."""
        team = Team(
            name='team-1',
            description_de='Deutsche Beschreibung',
            description_en='English Description',
            tenant_id=tenant.id
        )
        db.session.add(team)
        db.session.commit()
        
        assert team.get_description('en') == 'English Description'
    
    def test_get_description_fallback(self, db, tenant):
        """Test get_description fallback to empty string."""
        team = Team(name='team-1', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        assert team.get_description('de') == ''
    
    def test_team_repr(self, db, tenant):
        """Test team string representation."""
        team = Team(name='Engineering', tenant_id=tenant.id)
        db.session.add(team)
        db.session.commit()
        
        assert 'Engineering' in repr(team)


@pytest.mark.unit
@pytest.mark.models
class TestTaskReviewerModel:
    """Tests for TaskReviewer model."""
    
    def test_task_reviewer_creation(self, db, user, task):
        """Test TaskReviewer is created correctly."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        assert reviewer.id is not None
        assert reviewer.has_approved is False
        assert reviewer.has_rejected is False
    
    def test_approve(self, db, user, task):
        """Test approve method."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        reviewer.approve(note='Looks good!')
        db.session.commit()
        
        assert reviewer.has_approved is True
        assert reviewer.approved_at is not None
        assert reviewer.approval_note == 'Looks good!'
        assert reviewer.has_rejected is False
    
    def test_reject(self, db, user, task):
        """Test reject method."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        reviewer.reject(note='Needs revision')
        db.session.commit()
        
        assert reviewer.has_rejected is True
        assert reviewer.rejected_at is not None
        assert reviewer.rejection_note == 'Needs revision'
        assert reviewer.has_approved is False
    
    def test_reset(self, db, user, task):
        """Test reset method clears approval/rejection."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        reviewer.approve(note='Approved')
        db.session.commit()
        
        reviewer.reset()
        db.session.commit()
        
        assert reviewer.has_approved is False
        assert reviewer.approved_at is None
        assert reviewer.approval_note is None
        assert reviewer.has_rejected is False
    
    def test_approve_clears_rejection(self, db, user, task):
        """Test approve clears previous rejection."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        reviewer.reject(note='Bad')
        db.session.commit()
        
        reviewer.approve(note='Fixed now')
        db.session.commit()
        
        assert reviewer.has_approved is True
        assert reviewer.has_rejected is False
        assert reviewer.rejected_at is None
    
    def test_reject_clears_approval(self, db, user, task):
        """Test reject clears previous approval."""
        reviewer = TaskReviewer(
            task_id=task.id,
            user_id=user.id,
            order=1
        )
        db.session.add(reviewer)
        db.session.commit()
        
        reviewer.approve(note='Good')
        db.session.commit()
        
        reviewer.reject(note='Actually, not good')
        db.session.commit()
        
        assert reviewer.has_rejected is True
        assert reviewer.has_approved is False
        assert reviewer.approved_at is None


@pytest.mark.unit
@pytest.mark.models
class TestUserEntityModel:
    """Tests for UserEntity permission model."""
    
    def test_user_entity_creation(self, db, user, tenant):
        """Test UserEntity is created correctly."""
        entity = Entity(name='Test Entity', tenant_id=tenant.id)
        db.session.add(entity)
        db.session.commit()
        
        user_entity = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='edit'
        )
        db.session.add(user_entity)
        db.session.commit()
        
        assert user_entity.id is not None
        assert user_entity.access_level == 'edit'
    
    def test_can_view(self, db, user, tenant):
        """Test can_view for different access levels."""
        entity = Entity(name='Test Entity', tenant_id=tenant.id)
        db.session.add(entity)
        db.session.commit()
        
        # View level
        perm_view = UserEntity(user_id=user.id, entity_id=entity.id, access_level='view')
        assert perm_view.can_view() is True
        
        # Edit level can also view
        perm_edit = UserEntity(user_id=user.id, entity_id=entity.id, access_level='edit')
        assert perm_edit.can_view() is True
        
        # Manage level can also view
        perm_manage = UserEntity(user_id=user.id, entity_id=entity.id, access_level='manage')
        assert perm_manage.can_view() is True
    
    def test_can_edit(self, db, user, tenant):
        """Test can_edit for different access levels."""
        entity = Entity(name='Test Entity', tenant_id=tenant.id)
        db.session.add(entity)
        db.session.commit()
        
        # View level cannot edit
        perm_view = UserEntity(user_id=user.id, entity_id=entity.id, access_level='view')
        assert perm_view.can_edit() is False
        
        # Edit level can edit
        perm_edit = UserEntity(user_id=user.id, entity_id=entity.id, access_level='edit')
        assert perm_edit.can_edit() is True
        
        # Manage level can edit
        perm_manage = UserEntity(user_id=user.id, entity_id=entity.id, access_level='manage')
        assert perm_manage.can_edit() is True
    
    def test_can_manage(self, db, user, tenant):
        """Test can_manage for different access levels."""
        entity = Entity(name='Test Entity', tenant_id=tenant.id)
        db.session.add(entity)
        db.session.commit()
        
        # View level cannot manage
        perm_view = UserEntity(user_id=user.id, entity_id=entity.id, access_level='view')
        assert perm_view.can_manage() is False
        
        # Edit level cannot manage
        perm_edit = UserEntity(user_id=user.id, entity_id=entity.id, access_level='edit')
        assert perm_edit.can_manage() is False
        
        # Manage level can manage
        perm_manage = UserEntity(user_id=user.id, entity_id=entity.id, access_level='manage')
        assert perm_manage.can_manage() is True
    
    def test_user_entity_repr(self, db, user, tenant):
        """Test UserEntity string representation."""
        entity = Entity(name='Test Entity', tenant_id=tenant.id)
        db.session.add(entity)
        db.session.commit()
        
        user_entity = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='edit'
        )
        db.session.add(user_entity)
        db.session.commit()
        
        repr_str = repr(user_entity)
        assert 'UserEntity' in repr_str


@pytest.mark.unit
@pytest.mark.models
class TestEntityAccessLevelEnum:
    """Tests for EntityAccessLevel enum."""
    
    def test_access_level_values(self):
        """Test EntityAccessLevel enum values."""
        assert EntityAccessLevel.VIEW.value == 'view'
        assert EntityAccessLevel.EDIT.value == 'edit'
        assert EntityAccessLevel.MANAGE.value == 'manage'
    
    def test_access_level_choices(self):
        """Test EntityAccessLevel choices method."""
        choices = EntityAccessLevel.choices()
        assert len(choices) == 3
        assert ('view', 'View') in choices
        assert ('edit', 'Edit') in choices
        assert ('manage', 'Manage') in choices
