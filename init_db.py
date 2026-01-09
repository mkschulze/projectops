"""
ProjectOps - Database Initialization
Run: python init_db.py
"""
from app import app
from extensions import db
from models import User, TaskCategory, Entity, Team


def init_database():
    """Initialize database with tables and default admin user"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print('✓ Database tables created')
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Administrator',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✓ Admin user created: admin@example.com / admin123')
        else:
            print('• Admin user already exists')
        
        # Create demo user
        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            user = User(
                email='user@example.com',
                name='Demo User',
                role='user',
                is_active=True
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print('✓ Demo user created: user@example.com / user123')
        else:
            print('• Demo user already exists')
        
        # Create default categories (including tax types and general categories)
        categories_data = [
            # Tax categories (Steuerarten)
            {'code': 'EST', 'name': 'Einkommensteuer', 'name_de': 'Einkommensteuer', 'name_en': 'Income Tax', 
             'description': 'Einkommensteuer für natürliche Personen', 'description_de': 'Einkommensteuer für natürliche Personen', 'description_en': 'Income tax for natural persons',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            {'code': 'KOST', 'name': 'Körperschaftsteuer', 'name_de': 'Körperschaftsteuer', 'name_en': 'Corporate Tax',
             'description': 'Körperschaftsteuer für juristische Personen', 'description_de': 'Körperschaftsteuer für juristische Personen', 'description_en': 'Corporate tax for legal entities',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            {'code': 'GEWST', 'name': 'Gewerbesteuer', 'name_de': 'Gewerbesteuer', 'name_en': 'Trade Tax',
             'description': 'Gewerbesteuer für Gewerbebetriebe', 'description_de': 'Gewerbesteuer für Gewerbebetriebe', 'description_en': 'Trade tax for businesses',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            {'code': 'UST', 'name': 'Umsatzsteuer', 'name_de': 'Umsatzsteuer', 'name_en': 'VAT',
             'description': 'Umsatzsteuer / Mehrwertsteuer', 'description_de': 'Umsatzsteuer / Mehrwertsteuer', 'description_en': 'Value Added Tax',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            {'code': 'LST', 'name': 'Lohnsteuer', 'name_de': 'Lohnsteuer', 'name_en': 'Payroll Tax',
             'description': 'Lohnsteuer für Arbeitnehmer', 'description_de': 'Lohnsteuer für Arbeitnehmer', 'description_en': 'Payroll tax for employees',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            {'code': 'KAPEST', 'name': 'Kapitalertragsteuer', 'name_de': 'Kapitalertragsteuer', 'name_en': 'Capital Gains Tax',
             'description': 'Steuer auf Kapitalerträge', 'description_de': 'Steuer auf Kapitalerträge', 'description_en': 'Tax on capital gains',
             'color': '#4A90D9', 'icon': 'bi-calculator'},
            # General categories
            {'code': 'COMPL', 'name': 'Compliance', 'name_de': 'Compliance', 'name_en': 'Compliance',
             'description': 'Regulatorische Anforderungen', 'description_de': 'Regulatorische Anforderungen', 'description_en': 'Regulatory requirements',
             'color': '#0076A8', 'icon': 'bi-shield-check'},
            {'code': 'AUDIT', 'name': 'Audit', 'name_de': 'Prüfung', 'name_en': 'Audit',
             'description': 'Interne und externe Prüfungen', 'description_de': 'Interne und externe Prüfungen', 'description_en': 'Internal and external audits',
             'color': '#62B5E5', 'icon': 'bi-clipboard-check'},
            {'code': 'REPORT', 'name': 'Reporting', 'name_de': 'Berichtswesen', 'name_en': 'Reporting',
             'description': 'Finanzberichte und Meldungen', 'description_de': 'Finanzberichte und Meldungen', 'description_en': 'Financial reports and filings',
             'color': '#43B02A', 'icon': 'bi-graph-up'},
            {'code': 'LEGAL', 'name': 'Legal', 'name_de': 'Recht', 'name_en': 'Legal',
             'description': 'Rechtliche Angelegenheiten', 'description_de': 'Rechtliche Angelegenheiten', 'description_en': 'Legal matters',
             'color': '#6F3750', 'icon': 'bi-briefcase'},
            {'code': 'OTHER', 'name': 'Sonstige', 'name_de': 'Sonstige', 'name_en': 'Other',
             'description': 'Sonstige Kategorien', 'description_de': 'Sonstige Kategorien', 'description_en': 'Other categories',
             'color': '#6c757d', 'icon': 'bi-folder'},
        ]
        
        for cat_data in categories_data:
            existing = TaskCategory.query.filter_by(code=cat_data['code']).first()
            if not existing:
                category = TaskCategory(**cat_data, is_active=True)
                db.session.add(category)
        db.session.commit()
        print('✓ Default task categories created (including tax types)')
        
        # Create default entities with multilingual names
        entities_data = [
            {'name': 'Hauptgesellschaft GmbH', 'name_de': 'Hauptgesellschaft GmbH', 'name_en': 'Main Company Ltd', 'is_active': True},
            {'name': 'Tochtergesellschaft 1 GmbH', 'name_de': 'Tochtergesellschaft 1 GmbH', 'name_en': 'Subsidiary 1 Ltd', 'is_active': True},
            {'name': 'Tochtergesellschaft 2 GmbH', 'name_de': 'Tochtergesellschaft 2 GmbH', 'name_en': 'Subsidiary 2 Ltd', 'is_active': True},
        ]
        
        for ent_data in entities_data:
            existing = Entity.query.filter_by(name=ent_data['name']).first()
            if not existing:
                entity = Entity(**ent_data)
                db.session.add(entity)
        db.session.commit()
        print('✓ Default entities created')
        
        # Create default teams with multilingual names
        teams_data = [
            {'name': 'Steuerabteilung', 'name_de': 'Steuerabteilung', 'name_en': 'Tax Department', 
             'description': 'Hauptverantwortlich für Steuererklärungen', 'description_de': 'Hauptverantwortlich für Steuererklärungen', 'description_en': 'Main responsibility for tax returns', 'is_active': True},
            {'name': 'Buchhaltung', 'name_de': 'Buchhaltung', 'name_en': 'Accounting',
             'description': 'Finanzbuchhaltung und Jahresabschluss', 'description_de': 'Finanzbuchhaltung und Jahresabschluss', 'description_en': 'Financial accounting and annual statements', 'is_active': True},
            {'name': 'Controlling', 'name_de': 'Controlling', 'name_en': 'Controlling',
             'description': 'Planung und Kostenrechnung', 'description_de': 'Planung und Kostenrechnung', 'description_en': 'Planning and cost accounting', 'is_active': True},
        ]
        
        for team_data in teams_data:
            existing = Team.query.filter_by(name=team_data['name']).first()
            if not existing:
                team = Team(**team_data)
                db.session.add(team)
        db.session.commit()
        print('✓ Default teams created')
        
        print('\n🚀 Database initialized successfully!')
        print('   Run: flask run --debug')


if __name__ == '__main__':
    init_database()
