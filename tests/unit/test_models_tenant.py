"""
Unit tests for Tenant and TenantMembership models.
"""
import pytest


@pytest.mark.unit
@pytest.mark.models
class TestTenantModel:
    """Tests for Tenant model."""
    
    def test_tenant_creation(self, tenant):
        """Test tenant is created correctly."""
        assert tenant.name == 'Test Tenant'
        assert tenant.slug == 'test-tenant'
        assert tenant.is_active is True
        assert tenant.is_archived is False
    
    def test_tenant_default_color(self, tenant):
        """Test tenant has default primary color."""
        assert tenant.primary_color == '#0076A8'
    
    def test_tenant_repr(self, tenant):
        """Test tenant string representation."""
        repr_str = repr(tenant)
        assert 'Test Tenant' in repr_str or 'Tenant' in repr_str
    
    def test_tenant_archive(self, db, tenant, user):
        """Test archiving a tenant."""
        tenant.archive(user)
        db.session.commit()
        
        assert tenant.is_archived is True
        assert tenant.is_active is False
        assert tenant.archived_at is not None
        assert tenant.archived_by_id == user.id
    
    def test_tenant_restore(self, db, tenant, user):
        """Test restoring an archived tenant."""
        # First archive
        tenant.archive(user)
        db.session.commit()
        
        # Then restore
        tenant.restore()
        db.session.commit()
        
        assert tenant.is_archived is False
        assert tenant.is_active is True
        assert tenant.archived_at is None


@pytest.mark.unit
@pytest.mark.models
class TestTenantMembership:
    """Tests for TenantMembership model."""
    
    def test_membership_creation(self, tenant_with_user):
        """Test membership is created correctly."""
        tenant, user = tenant_with_user
        
        from models import TenantMembership
        membership = TenantMembership.query.filter_by(
            tenant_id=tenant.id,
            user_id=user.id
        ).first()
        
        assert membership is not None
        assert membership.role == 'member'
    
    def test_tenant_has_member(self, tenant_with_user):
        """Test tenant.has_member method."""
        tenant, user = tenant_with_user
        
        assert tenant.has_member(user) is True
    
    def test_tenant_get_member_role(self, tenant_with_user):
        """Test getting member's role in tenant."""
        tenant, user = tenant_with_user
        
        role = tenant.get_member_role(user)
        assert role == 'member'
    
    def test_membership_is_admin(self, db, tenant, admin_user):
        """Test membership is_admin method."""
        from models import TenantMembership
        
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=admin_user.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        assert membership.is_admin() is True
        
        db.session.delete(membership)
        db.session.commit()
    
    def test_membership_roles(self):
        """Test available membership roles."""
        from models import TenantMembership
        
        assert 'admin' in TenantMembership.ROLES
        assert 'manager' in TenantMembership.ROLES
        assert 'member' in TenantMembership.ROLES
        assert 'viewer' in TenantMembership.ROLES


@pytest.mark.unit
@pytest.mark.models
class TestTenantMembers:
    """Tests for tenant member management."""
    
    def test_add_member(self, db, tenant, admin_user):
        """Test adding a member to tenant."""
        membership = tenant.add_member(admin_user, role='member')
        db.session.commit()
        
        assert membership is not None
        assert tenant.has_member(admin_user) is True
        
        # Cleanup
        tenant.remove_member(admin_user)
        db.session.commit()
    
    def test_add_member_with_role(self, db, tenant, admin_user):
        """Test adding a member with specific role."""
        membership = tenant.add_member(admin_user, role='manager')
        db.session.commit()
        
        assert tenant.get_member_role(admin_user) == 'manager'
        
        # Cleanup
        tenant.remove_member(admin_user)
        db.session.commit()
    
    def test_remove_member(self, db, tenant, admin_user):
        """Test removing a member from tenant."""
        tenant.add_member(admin_user)
        db.session.commit()
        
        assert tenant.has_member(admin_user) is True
        
        tenant.remove_member(admin_user)
        db.session.commit()
        
        assert tenant.has_member(admin_user) is False
    
    def test_member_count(self, tenant_with_user):
        """Test member count property."""
        tenant, user = tenant_with_user
        
        assert tenant.member_count >= 1
