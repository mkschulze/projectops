"""
Core Module
Provides essential functionality: authentication, admin dashboard, base templates.
This module is always active and cannot be disabled.
"""
from flask import Blueprint
from modules import BaseModule, ModuleRegistry


@ModuleRegistry.register
class CoreModule(BaseModule):
    """Core application functionality"""
    
    code = 'core'
    name_de = 'Kern'
    name_en = 'Core'
    description_de = 'Grundlegende Anwendungsfunktionen'
    description_en = 'Core application functionality'
    icon = 'bi-gear'
    nav_order = 0
    is_core = True  # Cannot be disabled
    
    @classmethod
    def get_blueprint(cls):
        """Core routes are registered directly in app.py for now"""
        return None
    
    @classmethod
    def get_nav_items(cls, user, lang='de'):
        """Core doesn't add top-level nav items (handled by base template)"""
        return []
