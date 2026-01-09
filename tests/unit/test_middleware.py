"""
Tests for middleware/tenant.py module.
Tests for tenant context loading and access control functions.
"""
import pytest


class TestTenantHelpers:
    """Tests for basic tenant helper functions."""
    
    def test_get_current_tenant_function_exists(self, app, db):
        """Test get_current_tenant function exists."""
        from middleware.tenant import get_current_tenant
        assert callable(get_current_tenant)
    
    def test_get_current_tenant_role_function_exists(self, app, db):
        """Test get_current_tenant_role function exists."""
        from middleware.tenant import get_current_tenant_role
        assert callable(get_current_tenant_role)
    
    def test_get_current_tenant_no_context(self, app, db):
        """Test get_current_tenant returns None when no context."""
        from middleware.tenant import get_current_tenant
        from flask import g
        
        with app.app_context():
            # Ensure g.tenant is not set
            if hasattr(g, 'tenant'):
                delattr(g, 'tenant')
            
            result = get_current_tenant()
            assert result is None
    
    def test_get_current_tenant_with_context(self, app, db, tenant):
        """Test get_current_tenant returns tenant when set."""
        from middleware.tenant import get_current_tenant
        from flask import g
        
        with app.app_context():
            g.tenant = tenant
            result = get_current_tenant()
            assert result == tenant
    
    def test_get_current_tenant_role_no_context(self, app, db):
        """Test get_current_tenant_role returns None when no context."""
        from middleware.tenant import get_current_tenant_role
        from flask import g
        
        with app.app_context():
            if hasattr(g, 'tenant_role'):
                delattr(g, 'tenant_role')
            
            result = get_current_tenant_role()
            assert result is None
    
    def test_get_current_tenant_role_with_context(self, app, db):
        """Test get_current_tenant_role returns role when set."""
        from middleware.tenant import get_current_tenant_role
        from flask import g
        
        with app.app_context():
            g.tenant_role = 'admin'
            result = get_current_tenant_role()
            assert result == 'admin'


class TestLoadTenantContext:
    """Tests for load_tenant_context function."""
    
    def test_load_tenant_context_exists(self, app, db):
        """Test load_tenant_context function exists."""
        from middleware.tenant import load_tenant_context
        assert callable(load_tenant_context)


class TestTenantDecorators:
    """Tests for tenant-related decorators."""
    
    def test_tenant_required_decorator_exists(self, app, db):
        """Test tenant_required decorator exists."""
        from middleware.tenant import tenant_required
        assert callable(tenant_required)
    
    def test_tenant_admin_required_decorator_exists(self, app, db):
        """Test tenant_admin_required decorator exists."""
        from middleware.tenant import tenant_admin_required
        assert callable(tenant_admin_required)
    
    def test_tenant_manager_required_decorator_exists(self, app, db):
        """Test tenant_manager_required decorator exists."""
        from middleware.tenant import tenant_manager_required
        assert callable(tenant_manager_required)
    
    def test_superadmin_required_decorator_exists(self, app, db):
        """Test superadmin_required decorator exists."""
        from middleware.tenant import superadmin_required
        assert callable(superadmin_required)
    
    def test_tenant_required_wraps_function(self, app, db):
        """Test tenant_required wraps a function."""
        from middleware.tenant import tenant_required
        
        @tenant_required
        def dummy_view():
            return "OK"
        
        # Check it's wrapped
        assert callable(dummy_view)
    
    def test_tenant_admin_required_wraps_function(self, app, db):
        """Test tenant_admin_required wraps a function."""
        from middleware.tenant import tenant_admin_required
        
        @tenant_admin_required
        def dummy_admin_view():
            return "Admin OK"
        
        assert callable(dummy_admin_view)
    
    def test_tenant_manager_required_wraps_function(self, app, db):
        """Test tenant_manager_required wraps a function."""
        from middleware.tenant import tenant_manager_required
        
        @tenant_manager_required
        def dummy_manager_view():
            return "Manager OK"
        
        assert callable(dummy_manager_view)


class TestInjectTenantContext:
    """Tests for inject_tenant_context function."""
    
    def test_inject_tenant_context_exists(self, app, db):
        """Test inject_tenant_context function exists."""
        from middleware.tenant import inject_tenant_context
        assert callable(inject_tenant_context)
    
    def test_inject_tenant_context_returns_dict(self, app, db):
        """Test inject_tenant_context returns a dict."""
        from middleware.tenant import inject_tenant_context
        from flask import g
        
        with app.app_context():
            g.tenant = None
            g.tenant_role = None
            g.is_superadmin_mode = False
            
            result = inject_tenant_context()
            assert isinstance(result, dict)
    
    def test_inject_tenant_context_has_tenant_key(self, app, db, tenant):
        """Test inject_tenant_context includes tenant."""
        from middleware.tenant import inject_tenant_context
        from flask import g
        
        with app.app_context():
            g.tenant = tenant
            g.tenant_role = 'member'
            g.is_superadmin_mode = False
            
            result = inject_tenant_context()
            assert 'tenant' in result or 'current_tenant' in result


class TestMiddlewareImports:
    """Tests for middleware module imports."""
    
    def test_middleware_init_import(self, app, db):
        """Test middleware __init__ can be imported."""
        import middleware
        assert middleware is not None
    
    def test_middleware_tenant_import(self, app, db):
        """Test middleware.tenant can be imported."""
        from middleware import tenant
        assert tenant is not None
