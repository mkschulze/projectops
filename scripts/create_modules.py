#!/usr/bin/env python3
"""Create modules in the database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Module

app = create_app()
with app.app_context():
    # Create the projects module
    if not Module.query.filter_by(code='projects').first():
        module = Module(
            code='projects',
            name_de='Projekte',
            name_en='Projects',
            description_de='Projektmanagement mit Scrum, Kanban, Waterfall',
            description_en='Project management with Scrum, Kanban, Waterfall',
            icon='bi-kanban',
            nav_order=10,
            is_core=False,
            is_active=True
        )
        db.session.add(module)
        print(f'✅ Created module: projects')
    else:
        print('ℹ️  Module projects already exists')
    
    # Create core module
    if not Module.query.filter_by(code='core').first():
        core = Module(
            code='core',
            name_de='Kern',
            name_en='Core',
            description_de='Kernfunktionen',
            description_en='Core functions',
            icon='bi-house',
            nav_order=0,
            is_core=True,
            is_active=True
        )
        db.session.add(core)
        print(f'✅ Created module: core')
    else:
        print('ℹ️  Module core already exists')
    
    db.session.commit()
    
    print()
    print('All modules:')
    for m in Module.query.all():
        print(f'  - {m.id}: {m.code} (active={m.is_active}, core={m.is_core})')
