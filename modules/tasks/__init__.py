"""
Tasks Module
Task management, deadline tracking, and compliance calendar.
"""
from flask import Blueprint, url_for
from modules import BaseModule, ModuleRegistry


@ModuleRegistry.register
class TasksModule(BaseModule):
    """ProjectOps Tasks - Task & Deadline Management"""
    
    code = 'tasks'
    name_de = 'Aufgaben'
    name_en = 'Tasks'
    description_de = 'Aufgaben- und Fristenverwaltung'
    description_en = 'Task and deadline management'
    icon = 'bi-list-task'
    nav_order = 10
    is_core = True  # Main module, always active
    
    @classmethod
    def get_blueprint(cls):
        """Task routes are currently in app.py, will be refactored later"""
        return None
    
    @classmethod
    def get_nav_items(cls, user, lang='de'):
        """Navigation items for Tasks module"""
        t = lambda de, en: de if lang == 'de' else en
        
        items = [
            {
                'label': t('Dashboard', 'Dashboard'),
                'url': '/dashboard',
                'icon': 'bi-speedometer2',
                'children': []
            },
            {
                'label': t('Aufgaben', 'Tasks'),
                'url': '/tasks',
                'icon': 'bi-list-task',
                'children': [
                    {'label': t('Alle Aufgaben', 'All Tasks'), 'url': '/tasks'},
                    {'label': t('Neue Aufgabe', 'New Task'), 'url': '/tasks/new'},
                    {'label': t('Archiv', 'Archive'), 'url': '/tasks/archive'},
                ]
            },
            {
                'label': t('Kalender', 'Calendar'),
                'url': '/calendar',
                'icon': 'bi-calendar3',
                'children': [
                    {'label': t('Monatsansicht', 'Month View'), 'url': '/calendar'},
                    {'label': t('Wochenansicht', 'Week View'), 'url': '/calendar/week'},
                    {'label': t('Jahresansicht', 'Year View'), 'url': '/calendar/year'},
                    {'label': t('Abo', 'Subscription'), 'url': '/calendar/subscription'},
                ]
            },
        ]
        
        return items
