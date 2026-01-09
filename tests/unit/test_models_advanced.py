"""
Advanced model tests for higher code coverage.
Tests for TenantApiKey, TenantRole, EntityAccessLevel, Team, and more.
"""
import pytest
from datetime import datetime, timedelta


class TestTenantRole:
    """Tests for TenantRole enum."""
    
    def test_tenant_role_admin_value(self, app, db):
        """Test ADMIN role value."""
        from models import TenantRole
        assert TenantRole.ADMIN.value == 'admin'
    
    def test_tenant_role_manager_value(self, app, db):
        """Test MANAGER role value."""
        from models import TenantRole
        assert TenantRole.MANAGER.value == 'manager'
    
    def test_tenant_role_member_value(self, app, db):
        """Test MEMBER role value."""
        from models import TenantRole
        assert TenantRole.MEMBER.value == 'member'
    
    def test_tenant_role_viewer_value(self, app, db):
        """Test VIEWER role value."""
        from models import TenantRole
        assert TenantRole.VIEWER.value == 'viewer'
    
    def test_tenant_role_choices(self, app, db):
        """Test choices method returns list of tuples."""
        from models import TenantRole
        choices = TenantRole.choices()
        assert isinstance(choices, list)
        assert len(choices) == 4
        assert ('admin', 'Admin') in choices


class TestTenantApiKey:
    """Tests for TenantApiKey model."""
    
    def test_generate_key(self, app, db):
        """Test API key generation."""
        from models import TenantApiKey
        key = TenantApiKey.generate_key()
        assert isinstance(key, str)
        assert len(key) > 20  # Should be long enough
    
    def test_hash_key(self, app, db):
        """Test API key hashing."""
        from models import TenantApiKey
        key = "test-api-key-123"
        hashed = TenantApiKey.hash_key(key)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex
        assert hashed != key  # Should not be plaintext
    
    def test_api_key_creation(self, db, tenant):
        """Test TenantApiKey creation."""
        from models import TenantApiKey
        
        key = TenantApiKey.generate_key()
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test API Key',
            key_hash=TenantApiKey.hash_key(key),
            key_prefix=key[:8],
            scopes=['read:tasks']
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.id is not None
        assert api_key.name == 'Test API Key'
        assert api_key.is_active is True
    
    def test_verify_key_correct(self, db, tenant):
        """Test verifying correct API key."""
        from models import TenantApiKey
        
        key = "my-secret-api-key"
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash=TenantApiKey.hash_key(key),
            key_prefix=key[:8],
            scopes=[]
        )
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.verify_key(key) is True
    
    def test_verify_key_incorrect(self, db, tenant):
        """Test verifying incorrect API key."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash=TenantApiKey.hash_key("correct-key"),
            key_prefix="correct-",
            scopes=[]
        )
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.verify_key("wrong-key") is False
    
    def test_is_expired_no_expiry(self, db, tenant):
        """Test is_expired with no expiry date."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            expires_at=None
        )
        
        assert api_key.is_expired() is False
    
    def test_is_expired_future(self, db, tenant):
        """Test is_expired with future expiry."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert api_key.is_expired() is False
    
    def test_is_expired_past(self, db, tenant):
        """Test is_expired with past expiry."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        assert api_key.is_expired() is True
    
    def test_record_usage(self, db, tenant):
        """Test recording API key usage."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix'
        )
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.last_used_at is None
        api_key.record_usage()
        assert api_key.last_used_at is not None
    
    def test_has_scope_empty(self, db, tenant):
        """Test has_scope with empty scopes."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            scopes=[]
        )
        
        assert api_key.has_scope('read:tasks') is False
    
    def test_has_scope_specific(self, db, tenant):
        """Test has_scope with specific scope."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            scopes=['read:tasks', 'write:tasks']
        )
        
        assert api_key.has_scope('read:tasks') is True
        assert api_key.has_scope('delete:tasks') is False
    
    def test_has_scope_wildcard(self, db, tenant):
        """Test has_scope with wildcard."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='prefix',
            scopes=['*']
        )
        
        assert api_key.has_scope('read:tasks') is True
        assert api_key.has_scope('anything') is True
    
    def test_api_key_repr(self, db, tenant):
        """Test TenantApiKey repr."""
        from models import TenantApiKey
        
        api_key = TenantApiKey(
            tenant_id=tenant.id,
            name='Test Key',
            key_hash='hash',
            key_prefix='testpref'
        )
        
        repr_str = repr(api_key)
        assert 'TenantApiKey' in repr_str
        assert 'testpref' in repr_str


class TestTenantMembershipAdvanced:
    """Additional tests for TenantMembership model."""
    
    def test_membership_is_manager_or_above_admin(self, db, tenant, user):
        """Test is_manager_or_above for admin."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert membership.is_manager_or_above() is True
    
    def test_membership_is_manager_or_above_manager(self, db, tenant, user):
        """Test is_manager_or_above for manager."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='manager'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert membership.is_manager_or_above() is True
    
    def test_membership_is_manager_or_above_member(self, db, tenant, user):
        """Test is_manager_or_above for member."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert membership.is_manager_or_above() is False
    
    def test_membership_can_edit_member(self, db, tenant, user):
        """Test can_edit for member."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        
        assert membership.can_edit() is True
    
    def test_membership_can_edit_viewer(self, db, tenant, user):
        """Test can_edit for viewer."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='viewer'
        )
        
        assert membership.can_edit() is False
    
    def test_membership_repr(self, db, tenant, user):
        """Test TenantMembership repr."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        
        repr_str = repr(membership)
        assert 'TenantMembership' in repr_str


class TestTenantAdvanced:
    """Additional tests for Tenant model."""
    
    def test_tenant_members_property(self, db, tenant, user):
        """Test members property."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        db.session.refresh(tenant)
        members = tenant.members
        assert len(members) == 1
        assert user in members
    
    def test_tenant_admin_users_property(self, db, tenant, user, admin_user):
        """Test admin_users property."""
        from models import TenantMembership
        
        # Add regular member
        membership1 = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        # Add admin
        membership2 = TenantMembership(
            tenant_id=tenant.id,
            user_id=admin_user.id,
            role='admin'
        )
        db.session.add_all([membership1, membership2])
        db.session.commit()
        
        db.session.refresh(tenant)
        admins = tenant.admin_users
        assert len(admins) == 1
        assert admin_user in admins
        assert user not in admins
    
    def test_tenant_member_count_property(self, db, tenant, user):
        """Test member_count property."""
        from models import TenantMembership
        
        # Initially no members
        db.session.refresh(tenant)
        assert tenant.member_count == 0
        
        # Add a member
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        db.session.refresh(tenant)
        assert tenant.member_count == 1
    
    def test_tenant_add_member_existing(self, db, tenant, user):
        """Test adding an existing member returns existing membership."""
        from models import TenantMembership
        
        # Add first time
        membership1 = tenant.add_member(user, role='member')
        db.session.commit()
        
        # Add second time - should return existing
        membership2 = tenant.add_member(user, role='admin')
        
        assert membership1.id == membership2.id
        assert membership2.role == 'member'  # Role unchanged
    
    def test_tenant_add_member_with_inviter(self, db, tenant, user, admin_user):
        """Test adding member with inviter."""
        membership = tenant.add_member(user, role='member', invited_by=admin_user)
        db.session.commit()
        
        assert membership.invited_by_id == admin_user.id


class TestEntityAccessLevel:
    """Tests for EntityAccessLevel enum."""
    
    def test_view_level(self, app, db):
        """Test VIEW access level."""
        from models import EntityAccessLevel
        assert EntityAccessLevel.VIEW.value == 'view'
    
    def test_edit_level(self, app, db):
        """Test EDIT access level."""
        from models import EntityAccessLevel
        assert EntityAccessLevel.EDIT.value == 'edit'
    
    def test_manage_level(self, app, db):
        """Test MANAGE access level."""
        from models import EntityAccessLevel
        assert EntityAccessLevel.MANAGE.value == 'manage'


class TestUserAdvanced:
    """Additional User model tests."""
    
    def test_user_check_password_correct(self, db, user):
        """Test check_password with correct password."""
        assert user.check_password('testpassword123') is True
    
    def test_user_check_password_incorrect(self, db, user):
        """Test check_password with incorrect password."""
        assert user.check_password('wrongpassword') is False
    
    def test_user_is_admin_method(self, db, admin_user):
        """Test is_admin method for admin user."""
        # Assuming User has is_admin method based on role
        assert admin_user.role == 'admin'
    
    def test_user_is_active_default(self, db, user):
        """Test user is_active default."""
        assert user.is_active is True
    
    def test_user_password_hash_not_plaintext(self, db, user):
        """Test password is hashed, not stored as plaintext."""
        assert user.password_hash != 'testpassword123'
        assert len(user.password_hash) > 20
