"""
Routes Module - Flask Blueprints

This module contains all route handlers organized into blueprints for:
- auth: Authentication (login, logout, session management)
- main: Dashboard, calendar, profile, notifications
- tasks: Task CRUD, status changes, evidence, comments
- admin: User, entity, team, template management
- api: JSON API endpoints
- presets: Task preset management, import/export
"""

from routes.auth import auth_bp
from routes.main import main_bp
from routes.tasks import tasks_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.presets import presets_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'tasks_bp',
    'admin_bp',
    'api_bp',
    'presets_bp',
]
