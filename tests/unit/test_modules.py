"""
Tests for modules/__init__.py - Module registration system.
"""
import pytest


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""
    
    def test_module_registry_exists(self, app, db):
        """Test ModuleRegistry exists."""
        from modules import ModuleRegistry
        assert ModuleRegistry is not None
    
    def test_module_registry_has_register(self, app, db):
        """Test ModuleRegistry has register decorator."""
        from modules import ModuleRegistry
        assert hasattr(ModuleRegistry, 'register')
    
    def test_module_registry_has_all(self, app, db):
        """Test ModuleRegistry has all method."""
        from modules import ModuleRegistry
        assert hasattr(ModuleRegistry, 'all')
    
    def test_module_registry_has_get(self, app, db):
        """Test ModuleRegistry has get method."""
        from modules import ModuleRegistry
        assert hasattr(ModuleRegistry, 'get')
    
    def test_module_registry_has_get_user_modules(self, app, db):
        """Test ModuleRegistry has get_user_modules method."""
        from modules import ModuleRegistry
        assert hasattr(ModuleRegistry, 'get_user_modules')
    
    def test_module_registry_has_init_app(self, app, db):
        """Test ModuleRegistry has init_app method."""
        from modules import ModuleRegistry
        assert hasattr(ModuleRegistry, 'init_app')
    
    def test_module_registry_all_returns_list(self, app, db):
        """Test all() returns a list."""
        from modules import ModuleRegistry
        result = ModuleRegistry.all()
        assert isinstance(result, list)


class TestBaseModule:
    """Tests for BaseModule class."""
    
    def test_base_module_exists(self, app, db):
        """Test BaseModule exists."""
        from modules import BaseModule
        assert BaseModule is not None
    
    def test_base_module_has_code(self, app, db):
        """Test BaseModule has code attribute."""
        from modules import BaseModule
        assert hasattr(BaseModule, 'code')
    
    def test_base_module_has_name_de(self, app, db):
        """Test BaseModule has name_de attribute."""
        from modules import BaseModule
        assert hasattr(BaseModule, 'name_de')
    
    def test_base_module_has_name_en(self, app, db):
        """Test BaseModule has name_en attribute."""
        from modules import BaseModule
        assert hasattr(BaseModule, 'name_en')
    
    def test_base_module_has_icon(self, app, db):
        """Test BaseModule has icon attribute."""
        from modules import BaseModule
        assert hasattr(BaseModule, 'icon')


class TestCoreModule:
    """Tests for CoreModule."""
    
    def test_core_module_exists(self, app, db):
        """Test CoreModule exists."""
        from modules.core import CoreModule
        assert CoreModule is not None
    
    def test_core_module_code(self, app, db):
        """Test CoreModule has correct code."""
        from modules.core import CoreModule
        assert CoreModule.code == 'core'
    
    def test_core_module_is_core(self, app, db):
        """Test CoreModule is marked as core."""
        from modules.core import CoreModule
        assert CoreModule.is_core is True


class TestProjectsModule:
    """Tests for ProjectsModule."""
    
    def test_projects_module_import(self, app, db):
        """Test projects module can be imported."""
        from modules import projects
        assert projects is not None
    
    def test_projects_module_class_exists(self, app, db):
        """Test ProjectsModule class exists."""
        from modules.projects import ProjectsModule
        assert ProjectsModule is not None
    
    def test_projects_module_code(self, app, db):
        """Test ProjectsModule has correct code."""
        from modules.projects import ProjectsModule
        assert ProjectsModule.code == 'projects'


class TestTasksModule:
    """Tests for TasksModule."""
    
    def test_tasks_module_import(self, app, db):
        """Test tasks module can be imported."""
        from modules import tasks
        assert tasks is not None
    
    def test_tasks_module_class_exists(self, app, db):
        """Test TasksModule class exists."""
        from modules.tasks import TasksModule
        assert TasksModule is not None


class TestModuleImports:
    """Tests for module imports."""
    
    def test_modules_init_import(self, app, db):
        """Test modules __init__ can be imported."""
        import modules
        assert modules is not None
    
    def test_modules_core_import(self, app, db):
        """Test modules.core can be imported."""
        from modules import core
        assert core is not None
    
    def test_modules_projects_import(self, app, db):
        """Test modules.projects can be imported."""
        from modules import projects
        assert projects is not None
