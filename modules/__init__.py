"""
Module Registry System
Central registry for all application modules with dynamic loading.
"""
from flask import session, current_app


class ModuleRegistry:
    """Central registry for all application modules"""
    
    _modules = {}
    
    @classmethod
    def register(cls, module_class):
        """Register a module class"""
        if module_class.code:
            cls._modules[module_class.code] = module_class
        return module_class
    
    @classmethod
    def get(cls, code):
        """Get a module by code"""
        return cls._modules.get(code)
    
    @classmethod
    def all(cls):
        """Get all registered modules"""
        return list(cls._modules.values())
    
    @classmethod
    def get_active(cls):
        """Get all active modules (sorted by nav_order)"""
        from models import Module
        active_codes = {m.code for m in Module.query.filter_by(is_active=True).all()}
        modules = [m for c, m in cls._modules.items() if c in active_codes]
        return sorted(modules, key=lambda m: m.nav_order)
    
    @classmethod
    def get_user_modules(cls, user):
        """Get modules accessible by a specific user"""
        if not user or not user.is_authenticated:
            return []
        
        from models import Module, UserModule
        
        # Admins get all active modules
        if user.role == 'admin':
            return cls.get_active()
        
        # Get user's assigned module codes
        user_module_codes = set()
        for um in user.user_modules:
            if um.module and um.module.is_active:
                user_module_codes.add(um.module.code)
        
        # Also include core modules (always available)
        core_modules = Module.query.filter_by(is_core=True, is_active=True).all()
        for m in core_modules:
            user_module_codes.add(m.code)
        
        modules = [m for c, m in cls._modules.items() if c in user_module_codes]
        return sorted(modules, key=lambda m: m.nav_order)
    
    @classmethod
    def init_app(cls, app):
        """Initialize all registered modules with the Flask app"""
        for module in cls._modules.values():
            module.init_app(app)


class BaseModule:
    """Base class for all application modules"""
    
    # Module identification
    code = None          # Unique code (e.g., 'tasks', 'projects')
    name_de = None       # German display name
    name_en = None       # English display name
    description_de = ''  # German description
    description_en = ''  # English description
    icon = 'bi-puzzle'   # Bootstrap icon class
    nav_order = 100      # Navigation order (lower = earlier)
    is_core = False      # Core modules can't be disabled
    
    # Blueprint
    _blueprint = None
    
    @classmethod
    def get_name(cls, lang='de'):
        """Get localized module name"""
        return cls.name_de if lang == 'de' else cls.name_en
    
    @classmethod
    def get_description(cls, lang='de'):
        """Get localized module description"""
        return cls.description_de if lang == 'de' else cls.description_en
    
    @classmethod
    def get_blueprint(cls):
        """Return Flask Blueprint for this module (override in subclass)"""
        raise NotImplementedError(f"Module {cls.code} must implement get_blueprint()")
    
    @classmethod
    def get_nav_items(cls, user, lang='de'):
        """
        Return navigation items for this module.
        Each item: {'label': str, 'url': str, 'icon': str, 'children': []}
        Override in subclass for custom navigation.
        """
        return []
    
    @classmethod
    def init_app(cls, app):
        """Initialize module with Flask app (override for custom initialization)"""
        if cls._blueprint:
            app.register_blueprint(cls._blueprint)
    
    @classmethod
    def sync_to_db(cls):
        """Sync module definition to database"""
        from models import Module
        from extensions import db
        
        module = Module.query.filter_by(code=cls.code).first()
        if not module:
            module = Module(
                code=cls.code,
                name_de=cls.name_de,
                name_en=cls.name_en,
                description_de=cls.description_de,
                description_en=cls.description_en,
                icon=cls.icon,
                nav_order=cls.nav_order,
                is_core=cls.is_core,
                is_active=True
            )
            db.session.add(module)
        else:
            # Update existing module
            module.name_de = cls.name_de
            module.name_en = cls.name_en
            module.description_de = cls.description_de
            module.description_en = cls.description_en
            module.icon = cls.icon
            module.nav_order = cls.nav_order
            module.is_core = cls.is_core
        
        db.session.commit()
        return module
