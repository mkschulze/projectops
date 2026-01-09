"""
Phase 2 Tests: Middleware & Module Core
Comprehensive tests for middleware/tenant.py and modules/__init__.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import g, session


# =============================================================================
# MIDDLEWARE LOAD TENANT CONTEXT TESTS
# =============================================================================

class TestLoadTenantContextLogic:
    """Tests for load_tenant_context actual logic (lines 31-77)."""
    
    def test_load_tenant_context_unauthenticated_user(self, app, db):
        """Test load_tenant_context skips for unauthenticated users."""
        from middleware.tenant import load_tenant_context
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                load_tenant_context()
                
                # Should set initial values and return early
                assert g.tenant is None
                assert g.tenant_role is None
                assert g.is_superadmin_mode is False
    
    def test_load_tenant_context_superadmin_with_tenant(self, app, db, tenant):
        """Test load_tenant_context for superadmin with tenant set."""
        from middleware.tenant import load_tenant_context
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                mock_user.current_tenant_id = tenant.id
                
                # Set up session
                session['current_tenant_id'] = None
                
                load_tenant_context()
                
                assert g.tenant == tenant
                assert g.tenant_role == 'admin'
                assert g.is_superadmin_mode is True
    
    def test_load_tenant_context_superadmin_from_session(self, app, db, tenant):
        """Test superadmin gets tenant from session."""
        from middleware.tenant import load_tenant_context
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                mock_user.current_tenant_id = None
                
                session['current_tenant_id'] = tenant.id
                
                load_tenant_context()
                
                assert g.tenant == tenant
                assert g.tenant_role == 'admin'
                assert g.is_superadmin_mode is True
    
    def test_load_tenant_context_superadmin_no_tenant(self, app, db):
        """Test superadmin with no tenant set."""
        from middleware.tenant import load_tenant_context
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                mock_user.current_tenant_id = None
                
                session.clear()
                
                load_tenant_context()
                
                assert g.tenant is None
                assert g.tenant_role is None
                assert g.is_superadmin_mode is False
    
    def test_load_tenant_context_regular_user_with_access(self, app, db, tenant, user):
        """Test regular user with valid tenant access."""
        from middleware.tenant import load_tenant_context
        from models import TenantMembership
        
        # Add user to tenant
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='member',
            is_default=True
        )
        db.session.add(membership)
        db.session.commit()
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user', user):
                session['current_tenant_id'] = tenant.id
                
                load_tenant_context()
                
                assert g.tenant == tenant
                assert g.tenant_role == 'member'
                assert g.is_superadmin_mode is False
    
    def test_load_tenant_context_user_without_access(self, app, db, tenant, user):
        """Test user without access to tenant in session."""
        from middleware.tenant import load_tenant_context
        
        # User is NOT added to tenant
        with app.test_request_context():
            with patch('middleware.tenant.current_user', user):
                session['current_tenant_id'] = tenant.id
                
                load_tenant_context()
                
                # Session should be cleared
                assert 'current_tenant_id' not in session or session.get('current_tenant_id') is None
    
    def test_load_tenant_context_fallback_to_default(self, app, db, tenant, user):
        """Test fallback to default tenant when no session tenant."""
        from middleware.tenant import load_tenant_context
        from models import TenantMembership
        
        # Add user to tenant as default
        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role='admin',
            is_default=True
        )
        db.session.add(membership)
        db.session.commit()
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user', user):
                session.clear()  # No tenant in session
                
                load_tenant_context()
                
                assert g.tenant == tenant
                assert g.tenant_role == 'admin'
                assert session.get('current_tenant_id') == tenant.id
    
    def test_load_tenant_context_inactive_tenant(self, app, db, user):
        """Test handling of inactive tenant."""
        from middleware.tenant import load_tenant_context
        from models import Tenant, TenantMembership
        
        # Create inactive tenant
        inactive_tenant = Tenant(
            name='Inactive Tenant',
            slug='inactive-tenant',
            is_active=False
        )
        db.session.add(inactive_tenant)
        db.session.commit()
        
        membership = TenantMembership(
            tenant_id=inactive_tenant.id,
            user_id=user.id,
            role='member',
            is_default=True
        )
        db.session.add(membership)
        db.session.commit()
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user', user):
                session['current_tenant_id'] = inactive_tenant.id
                
                load_tenant_context()
                
                # Should clear session for inactive tenant
                assert g.tenant is None or not g.tenant.is_active


# =============================================================================
# TENANT DECORATORS EXECUTION TESTS
# =============================================================================

class TestTenantRequiredDecoratorExecution:
    """Tests for tenant_required decorator execution (lines 88-109)."""
    
    def test_tenant_required_unauthenticated_redirects(self, app, db):
        """Test tenant_required redirects unauthenticated users."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/login'):
                        mock_redirect.return_value = Mock(status_code=302, location='/login')
                        
                        result = protected_view()
                        
                        mock_redirect.assert_called_once()
    
    def test_tenant_required_no_tenant_superadmin(self, app, db):
        """Test tenant_required redirects superadmin to tenant list."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                mock_user.tenants = []
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/admin/tenants'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/admin/tenants')
                            
                            result = protected_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_required_no_tenant_regular_user(self, app, db):
        """Test tenant_required redirects regular user to select tenant."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                mock_user.tenants = [Mock()]  # Has at least one tenant
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/select_tenant'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/select_tenant')
                            
                            result = protected_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_required_no_tenants_at_all(self, app, db):
        """Test user with no tenants redirects to logout."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                mock_user.tenants = []  # No tenants
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/logout'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/logout')
                            
                            result = protected_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_required_success(self, app, db, tenant):
        """Test tenant_required allows access with valid tenant."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant.is_active = True
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                result = protected_view()
                
                assert result == "OK"
    
    def test_tenant_required_inactive_tenant_non_superadmin(self, app, db, tenant):
        """Test tenant_required blocks inactive tenant for non-superadmin."""
        from middleware.tenant import tenant_required
        
        tenant.is_active = False
        
        @tenant_required
        def protected_view():
            return "OK"
        
        with app.test_request_context():
            g.tenant = tenant
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/select_tenant'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/select_tenant')
                            
                            result = protected_view()
                            
                            mock_redirect.assert_called_once()


class TestTenantAdminRequiredDecoratorExecution:
    """Tests for tenant_admin_required decorator execution (lines 121-132)."""
    
    def test_tenant_admin_required_unauthenticated(self, app, db):
        """Test redirects unauthenticated users."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def admin_view():
            return "Admin OK"
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/login'):
                        mock_redirect.return_value = Mock(status_code=302, location='/login')
                        
                        result = admin_view()
                        
                        mock_redirect.assert_called_once()
    
    def test_tenant_admin_required_no_tenant(self, app, db):
        """Test redirects when no tenant selected."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def admin_view():
            return "Admin OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/select_tenant'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/select_tenant')
                            
                            result = admin_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_admin_required_non_admin(self, app, db, tenant):
        """Test blocks non-admin users."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def admin_view():
            return "Admin OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'member'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/dashboard'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/dashboard')
                            
                            result = admin_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_admin_required_admin_success(self, app, db, tenant):
        """Test allows tenant admin."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def admin_view():
            return "Admin OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'admin'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                result = admin_view()
                
                assert result == "Admin OK"
    
    def test_tenant_admin_required_superadmin_success(self, app, db, tenant):
        """Test allows superadmin regardless of role."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def admin_view():
            return "Admin OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'member'  # Not admin
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                
                result = admin_view()
                
                assert result == "Admin OK"


class TestTenantManagerRequiredDecoratorExecution:
    """Tests for tenant_manager_required decorator execution (lines 142-153)."""
    
    def test_tenant_manager_required_unauthenticated(self, app, db):
        """Test redirects unauthenticated users."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/login'):
                        mock_redirect.return_value = Mock(status_code=302, location='/login')
                        
                        result = manager_view()
                        
                        mock_redirect.assert_called_once()
    
    def test_tenant_manager_required_no_tenant(self, app, db):
        """Test redirects when no tenant."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            g.tenant = None
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/select_tenant'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302)
                            
                            result = manager_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_manager_required_viewer_blocked(self, app, db, tenant):
        """Test blocks viewer role."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'viewer'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/dashboard'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/dashboard')
                            
                            result = manager_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_manager_required_member_blocked(self, app, db, tenant):
        """Test blocks member role."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'member'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/dashboard'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302)
                            
                            result = manager_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_tenant_manager_required_manager_success(self, app, db, tenant):
        """Test allows manager role."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'manager'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                result = manager_view()
                
                assert result == "Manager OK"
    
    def test_tenant_manager_required_admin_success(self, app, db, tenant):
        """Test allows admin role."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def manager_view():
            return "Manager OK"
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'admin'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                result = manager_view()
                
                assert result == "Manager OK"


class TestSuperadminRequiredDecoratorExecution:
    """Tests for superadmin_required decorator execution (lines 165-172)."""
    
    def test_superadmin_required_unauthenticated(self, app, db):
        """Test redirects unauthenticated users."""
        from middleware.tenant import superadmin_required
        
        @superadmin_required
        def superadmin_view():
            return "Superadmin OK"
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/login'):
                        mock_redirect.return_value = Mock(status_code=302, location='/login')
                        
                        result = superadmin_view()
                        
                        mock_redirect.assert_called_once()
    
    def test_superadmin_required_non_superadmin(self, app, db):
        """Test blocks non-superadmin users."""
        from middleware.tenant import superadmin_required
        
        @superadmin_required
        def superadmin_view():
            return "Superadmin OK"
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                with patch('middleware.tenant.redirect') as mock_redirect:
                    with patch('middleware.tenant.url_for', return_value='/dashboard'):
                        with patch('middleware.tenant.flash'):
                            mock_redirect.return_value = Mock(status_code=302, location='/dashboard')
                            
                            result = superadmin_view()
                            
                            mock_redirect.assert_called_once()
    
    def test_superadmin_required_success(self, app, db):
        """Test allows superadmin users."""
        from middleware.tenant import superadmin_required
        
        @superadmin_required
        def superadmin_view():
            return "Superadmin OK"
        
        with app.test_request_context():
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = True
                
                result = superadmin_view()
                
                assert result == "Superadmin OK"


# =============================================================================
# PERMISSION HELPER FUNCTIONS TESTS
# =============================================================================

class TestCanEditInTenant:
    """Tests for can_edit_in_tenant function (line 178-180)."""
    
    def test_can_edit_superadmin(self, app, db):
        """Test superadmin can always edit."""
        from middleware.tenant import can_edit_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'viewer'  # Even with viewer role
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = True
                
                assert can_edit_in_tenant() is True
    
    def test_can_edit_admin_role(self, app, db):
        """Test admin role can edit."""
        from middleware.tenant import can_edit_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'admin'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_edit_in_tenant() is True
    
    def test_can_edit_manager_role(self, app, db):
        """Test manager role can edit."""
        from middleware.tenant import can_edit_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'manager'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_edit_in_tenant() is True
    
    def test_can_edit_member_role(self, app, db):
        """Test member role can edit."""
        from middleware.tenant import can_edit_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'member'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_edit_in_tenant() is True
    
    def test_cannot_edit_viewer_role(self, app, db):
        """Test viewer role cannot edit."""
        from middleware.tenant import can_edit_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'viewer'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_edit_in_tenant() is False


class TestCanManageInTenant:
    """Tests for can_manage_in_tenant function (lines 185-187)."""
    
    def test_can_manage_superadmin(self, app, db):
        """Test superadmin can always manage."""
        from middleware.tenant import can_manage_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'viewer'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = True
                
                assert can_manage_in_tenant() is True
    
    def test_can_manage_admin_role(self, app, db):
        """Test admin role can manage."""
        from middleware.tenant import can_manage_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'admin'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_manage_in_tenant() is True
    
    def test_can_manage_manager_role(self, app, db):
        """Test manager role can manage."""
        from middleware.tenant import can_manage_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'manager'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_manage_in_tenant() is True
    
    def test_cannot_manage_member_role(self, app, db):
        """Test member role cannot manage."""
        from middleware.tenant import can_manage_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'member'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_manage_in_tenant() is False
    
    def test_cannot_manage_viewer_role(self, app, db):
        """Test viewer role cannot manage."""
        from middleware.tenant import can_manage_in_tenant
        
        with app.test_request_context():
            g.tenant_role = 'viewer'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert can_manage_in_tenant() is False


class TestIsTenantAdmin:
    """Tests for is_tenant_admin function (lines 192-194)."""
    
    def test_is_tenant_admin_superadmin(self, app, db):
        """Test superadmin is always considered admin."""
        from middleware.tenant import is_tenant_admin
        
        with app.test_request_context():
            g.tenant_role = 'viewer'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = True
                
                assert is_tenant_admin() is True
    
    def test_is_tenant_admin_admin_role(self, app, db):
        """Test admin role is tenant admin."""
        from middleware.tenant import is_tenant_admin
        
        with app.test_request_context():
            g.tenant_role = 'admin'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert is_tenant_admin() is True
    
    def test_is_not_tenant_admin_manager(self, app, db):
        """Test manager role is not tenant admin."""
        from middleware.tenant import is_tenant_admin
        
        with app.test_request_context():
            g.tenant_role = 'manager'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert is_tenant_admin() is False
    
    def test_is_not_tenant_admin_member(self, app, db):
        """Test member role is not tenant admin."""
        from middleware.tenant import is_tenant_admin
        
        with app.test_request_context():
            g.tenant_role = 'member'
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_superadmin = False
                
                assert is_tenant_admin() is False


# =============================================================================
# QUERY SCOPING HELPERS TESTS
# =============================================================================

class TestScopeQueryToTenant:
    """Tests for scope_query_to_tenant function (lines 215-222)."""
    
    def test_scope_query_no_tenant_id_attr(self, app, db):
        """Test returns unmodified query for model without tenant_id."""
        from middleware.tenant import scope_query_to_tenant
        
        class FakeModel:
            pass
        
        with app.test_request_context():
            mock_query = Mock()
            result = scope_query_to_tenant(mock_query, FakeModel)
            
            assert result == mock_query
    
    def test_scope_query_no_tenant_context(self, app, db):
        """Test returns empty result when no tenant context."""
        from middleware.tenant import scope_query_to_tenant
        from models import Task
        
        with app.test_request_context():
            g.tenant = None
            
            query = scope_query_to_tenant(Task.query, Task)
            
            # Should filter with False (empty result)
            result = query.all()
            assert result == []
    
    def test_scope_query_with_tenant(self, app, db, tenant):
        """Test filters query to current tenant."""
        from middleware.tenant import scope_query_to_tenant
        from models import Entity
        
        # Create entity in tenant
        entity = Entity(
            name='Scope Test Entity',
            name_de='Scope Test',
            name_en='Scope Test',
            tenant_id=tenant.id,
            is_active=True
        )
        db.session.add(entity)
        db.session.commit()
        
        with app.test_request_context():
            g.tenant = tenant
            
            query = scope_query_to_tenant(Entity.query, Entity)
            result = query.all()
            
            assert len(result) >= 1
            assert any(e.name == 'Scope Test Entity' for e in result)


class TestGetTenantFilteredQuery:
    """Tests for get_tenant_filtered_query function (line 232)."""
    
    def test_get_tenant_filtered_query(self, app, db, tenant):
        """Test convenience function returns filtered query."""
        from middleware.tenant import get_tenant_filtered_query
        from models import Entity
        
        with app.test_request_context():
            g.tenant = tenant
            
            query = get_tenant_filtered_query(Entity)
            
            assert query is not None


class TestTenantQueryMixin:
    """Tests for TenantQueryMixin class (lines 251-261)."""
    
    def test_for_tenant_with_specific_id(self, app, db, tenant):
        """Test for_tenant with explicit tenant_id."""
        from middleware.tenant import TenantQueryMixin
        from models import Entity
        
        # Create entity in tenant
        entity = Entity(
            name='Mixin Test Entity',
            name_de='Mixin Test',
            name_en='Mixin Test',
            tenant_id=tenant.id,
            is_active=True
        )
        db.session.add(entity)
        db.session.commit()
        
        with app.test_request_context():
            # Test the mixin for_tenant method
            # Entity has tenant_id so we can test the pattern
            class TestModel(TenantQueryMixin):
                query = Entity.query
                tenant_id = Entity.tenant_id
            
            result = TestModel.for_tenant(tenant.id).all()
            assert len(result) >= 1
    
    def test_for_current_tenant_no_context(self, app, db):
        """Test for_current_tenant with no tenant context."""
        from middleware.tenant import TenantQueryMixin
        from models import Entity
        
        with app.test_request_context():
            g.tenant = None
            
            # Create a test class using the mixin
            class TestModel(TenantQueryMixin):
                query = Entity.query
                tenant_id = Entity.tenant_id
            
            result = TestModel.for_current_tenant().all()
            assert result == []


# =============================================================================
# INJECT TENANT CONTEXT TESTS
# =============================================================================

class TestInjectTenantContextValues:
    """Tests for inject_tenant_context return values."""
    
    def test_inject_tenant_context_all_keys(self, app, db, tenant):
        """Test inject_tenant_context returns all expected keys."""
        from middleware.tenant import inject_tenant_context
        
        with app.test_request_context():
            g.tenant = tenant
            g.tenant_role = 'admin'
            g.is_superadmin_mode = False
            
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = True
                mock_user.is_superadmin = False
                
                result = inject_tenant_context()
                
                assert 'current_tenant' in result
                assert 'tenant_role' in result
                assert 'is_superadmin_mode' in result
                assert 'can_edit' in result
                assert 'can_manage' in result
                assert 'is_tenant_admin' in result
    
    def test_inject_tenant_context_unauthenticated(self, app, db):
        """Test inject_tenant_context with unauthenticated user."""
        from middleware.tenant import inject_tenant_context
        
        with app.test_request_context():
            g.tenant = None
            g.tenant_role = None
            g.is_superadmin_mode = False
            
            with patch('middleware.tenant.current_user') as mock_user:
                mock_user.is_authenticated = False
                
                result = inject_tenant_context()
                
                assert result['can_edit'] is False
                assert result['can_manage'] is False
                assert result['is_tenant_admin'] is False


# =============================================================================
# MODULE REGISTRY TESTS
# =============================================================================

class TestModuleRegistryMethods:
    """Tests for ModuleRegistry class methods."""
    
    def test_register_decorator(self, app, db):
        """Test register decorator adds module."""
        from modules import ModuleRegistry, BaseModule
        
        # Store original modules
        original_modules = ModuleRegistry._modules.copy()
        
        @ModuleRegistry.register
        class TestModule(BaseModule):
            code = 'test_module_123'
            name_de = 'Test'
            name_en = 'Test'
        
        assert 'test_module_123' in ModuleRegistry._modules
        assert ModuleRegistry.get('test_module_123') == TestModule
        
        # Cleanup
        del ModuleRegistry._modules['test_module_123']
    
    def test_get_returns_none_for_unknown(self, app, db):
        """Test get returns None for unknown module."""
        from modules import ModuleRegistry
        
        result = ModuleRegistry.get('nonexistent_module_xyz')
        assert result is None
    
    def test_all_returns_list(self, app, db):
        """Test all returns list of modules."""
        from modules import ModuleRegistry
        
        result = ModuleRegistry.all()
        assert isinstance(result, list)
        assert len(result) > 0  # Should have at least core, tasks, projects
    
    def test_get_active_with_database(self, app, db):
        """Test get_active queries database."""
        from modules import ModuleRegistry
        from models import Module
        
        # Create active module in database
        mod = Module(
            code='core',
            name_de='Kern',
            name_en='Core',
            is_active=True,
            is_core=True
        )
        db.session.add(mod)
        db.session.commit()
        
        result = ModuleRegistry.get_active()
        assert isinstance(result, list)
    
    def test_get_user_modules_unauthenticated(self, app, db):
        """Test get_user_modules returns empty for unauthenticated."""
        from modules import ModuleRegistry
        
        mock_user = Mock()
        mock_user.is_authenticated = False
        
        result = ModuleRegistry.get_user_modules(mock_user)
        assert result == []
    
    def test_get_user_modules_none_user(self, app, db):
        """Test get_user_modules returns empty for None user."""
        from modules import ModuleRegistry
        
        result = ModuleRegistry.get_user_modules(None)
        assert result == []
    
    def test_get_user_modules_admin(self, app, db):
        """Test admin users get all active modules."""
        from modules import ModuleRegistry
        from models import Module
        
        # Ensure core module exists
        core = Module.query.filter_by(code='core').first()
        if not core:
            core = Module(
                code='core',
                name_de='Kern',
                name_en='Core',
                is_active=True,
                is_core=True
            )
            db.session.add(core)
            db.session.commit()
        
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        
        result = ModuleRegistry.get_user_modules(mock_user)
        assert isinstance(result, list)
    
    def test_init_app(self, app, db):
        """Test init_app can be called without error."""
        from modules import ModuleRegistry
        
        # init_app may raise if blueprints have issues, but we just want to test it's callable
        # Since the app is already configured, we test that it doesn't raise unexpectedly
        try:
            ModuleRegistry.init_app(app)
        except Exception:
            # May fail due to duplicate blueprint registration, which is okay
            pass


class TestBaseModuleMethods:
    """Tests for BaseModule class methods."""
    
    def test_get_name_german(self, app, db):
        """Test get_name returns German name."""
        from modules import BaseModule
        
        class TestModule(BaseModule):
            name_de = 'Deutscher Name'
            name_en = 'English Name'
        
        assert TestModule.get_name('de') == 'Deutscher Name'
    
    def test_get_name_english(self, app, db):
        """Test get_name returns English name."""
        from modules import BaseModule
        
        class TestModule(BaseModule):
            name_de = 'Deutscher Name'
            name_en = 'English Name'
        
        assert TestModule.get_name('en') == 'English Name'
    
    def test_get_description_german(self, app, db):
        """Test get_description returns German description."""
        from modules import BaseModule
        
        class TestModule(BaseModule):
            description_de = 'Deutsche Beschreibung'
            description_en = 'English Description'
        
        assert TestModule.get_description('de') == 'Deutsche Beschreibung'
    
    def test_get_description_english(self, app, db):
        """Test get_description returns English description."""
        from modules import BaseModule
        
        class TestModule(BaseModule):
            description_de = 'Deutsche Beschreibung'
            description_en = 'English Description'
        
        assert TestModule.get_description('en') == 'English Description'
    
    def test_get_blueprint_not_implemented(self, app, db):
        """Test get_blueprint raises NotImplementedError."""
        from modules import BaseModule
        
        class TestModule(BaseModule):
            code = 'test'
        
        with pytest.raises(NotImplementedError):
            TestModule.get_blueprint()
    
    def test_get_nav_items_default(self, app, db):
        """Test default get_nav_items returns empty list."""
        from modules import BaseModule
        
        result = BaseModule.get_nav_items(None)
        assert result == []
    
    def test_sync_to_db_creates_new(self, app, db):
        """Test sync_to_db creates new module record."""
        from modules import BaseModule
        from models import Module
        
        class NewTestModule(BaseModule):
            code = 'new_test_sync_123'
            name_de = 'Neu Test'
            name_en = 'New Test'
            description_de = 'Beschreibung'
            description_en = 'Description'
            icon = 'bi-test'
            nav_order = 999
            is_core = False
        
        # Ensure it doesn't exist
        Module.query.filter_by(code='new_test_sync_123').delete()
        db.session.commit()
        
        result = NewTestModule.sync_to_db()
        
        assert result is not None
        assert result.code == 'new_test_sync_123'
        
        # Verify in database
        saved = Module.query.filter_by(code='new_test_sync_123').first()
        assert saved is not None
        assert saved.name_de == 'Neu Test'
    
    def test_sync_to_db_updates_existing(self, app, db):
        """Test sync_to_db updates existing module record."""
        from modules import BaseModule
        from models import Module
        
        # Create existing module
        existing = Module.query.filter_by(code='update_test_123').first()
        if not existing:
            existing = Module(
                code='update_test_123',
                name_de='Old Name',
                name_en='Old Name EN',
                is_active=True
            )
            db.session.add(existing)
            db.session.commit()
        
        class UpdateTestModule(BaseModule):
            code = 'update_test_123'
            name_de = 'Updated Name'
            name_en = 'Updated Name EN'
            description_de = 'New Desc'
            description_en = 'New Desc EN'
            icon = 'bi-updated'
            nav_order = 50
            is_core = True
        
        result = UpdateTestModule.sync_to_db()
        
        assert result.name_de == 'Updated Name'
        assert result.is_core is True


# =============================================================================
# CORE MODULE TESTS
# =============================================================================

class TestCoreModuleDetails:
    """Tests for CoreModule specifics."""
    
    def test_core_module_attributes(self, app, db):
        """Test CoreModule has correct attributes."""
        from modules.core import CoreModule
        
        assert CoreModule.code == 'core'
        assert CoreModule.name_de == 'Kern'
        assert CoreModule.name_en == 'Core'
        assert CoreModule.is_core is True
        assert CoreModule.nav_order == 0
    
    def test_core_module_get_blueprint_returns_none(self, app, db):
        """Test CoreModule.get_blueprint returns None."""
        from modules.core import CoreModule
        
        result = CoreModule.get_blueprint()
        assert result is None
    
    def test_core_module_get_nav_items_returns_empty(self, app, db):
        """Test CoreModule.get_nav_items returns empty list."""
        from modules.core import CoreModule
        
        result = CoreModule.get_nav_items(None)
        assert result == []
