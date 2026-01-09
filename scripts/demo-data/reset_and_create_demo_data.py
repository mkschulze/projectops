#!/usr/bin/env python3
"""
Reset Database and Create Fresh Demo Data

This script:
1. Drops and recreates all tables (fresh start)
2. Creates admin users including ZAP pentest user
3. Creates comprehensive demo data

For Penetration Testing, the ZAP user is created with:
- Superadmin privileges
- No rate limiting (handled in extensions.py)

Run with: cd /path/to/project && pipenv run python scripts/demo-data/reset_and_create_demo_data.py
"""
import sys
import os
import json
import random
from datetime import datetime, date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from extensions import db
from models import (
    Tenant, TenantMembership, User, Team, Entity,
    Task, TaskPreset, TaskCategory, Notification, NotificationType,
    AuditLog, UserEntity, Comment, TaskReviewer, Module, UserModule
)
from modules.projects.models import (
    Project, ProjectMember, ProjectMethodology,
    Issue, IssueType, IssueStatus, IssueComment, IssueActivity,
    Sprint, IssueLink, IssueLinkType, Worklog
)


# =============================================================================
# DEMO DATA DEFINITIONS
# =============================================================================

DEMO_USERS = [
    # Superadmin
    {'email': 'admin@example.com', 'name': 'System Administrator', 
     'role': 'admin', 'is_superadmin': True, 'password': 'admin123'},
    
    # ZAP Pentest User (Superadmin, no rate limit - configured in extensions.py)
    {'email': 'pentest@zap.local', 'name': 'ZAP PenTest',
     'role': 'admin', 'is_superadmin': True, 'password': 'ZapTest2026!'},
    
    # Demo Corporation Admins
    {'email': 'maria.mueller@democorp.local', 'name': 'Maria Müller', 
     'role': 'admin', 'is_superadmin': False, 'password': 'Demo2026!'},
    {'email': 'thomas.schmidt@democorp.local', 'name': 'Thomas Schmidt', 
     'role': 'admin', 'is_superadmin': False, 'password': 'Demo2026!'},
    
    # Project Managers
    {'email': 'anna.weber@democorp.local', 'name': 'Anna Weber', 
     'role': 'manager', 'password': 'Demo2026!'},
    {'email': 'michael.braun@democorp.local', 'name': 'Michael Braun', 
     'role': 'manager', 'password': 'Demo2026!'},
    
    # Team Members (Reviewers)
    {'email': 'lisa.hoffmann@democorp.local', 'name': 'Lisa Hoffmann', 
     'role': 'reviewer', 'password': 'Demo2026!'},
    {'email': 'jan.fischer@democorp.local', 'name': 'Jan Fischer', 
     'role': 'reviewer', 'password': 'Demo2026!'},
    
    # Team Members (Preparers)
    {'email': 'sarah.koch@democorp.local', 'name': 'Sarah Koch', 
     'role': 'preparer', 'password': 'Demo2026!'},
    {'email': 'david.bauer@democorp.local', 'name': 'David Bauer', 
     'role': 'preparer', 'password': 'Demo2026!'},
    {'email': 'julia.wagner@democorp.local', 'name': 'Julia Wagner', 
     'role': 'preparer', 'password': 'Demo2026!'},
    {'email': 'felix.richter@democorp.local', 'name': 'Felix Richter', 
     'role': 'preparer', 'password': 'Demo2026!'},
    
    # Guest/Viewer
    {'email': 'guest@client.de', 'name': 'Gast Benutzer', 
     'role': 'readonly', 'password': 'Guest2026!'},
]

DEMO_TENANTS = [
    {
        'name': 'Demo Corporation', 
        'slug': 'democorp', 
        'settings': {
            'default_language': 'de',
            'timezone': 'Europe/Berlin',
            'date_format': 'DD.MM.YYYY',
            'fiscal_year_start': '01-01',
            'description': 'Demo Corporation GmbH - Tax & Legal'
        }
    },
    {
        'name': 'Müller & Partner Steuerberatung', 
        'slug': 'mueller-partner', 
        'settings': {
            'default_language': 'de',
            'timezone': 'Europe/Berlin',
            'description': 'Steuerberatungsgesellschaft Müller & Partner mbB'
        }
    },
    {
        'name': 'TechStart GmbH', 
        'slug': 'techstart', 
        'settings': {
            'default_language': 'de',
            'timezone': 'Europe/Berlin',
            'description': 'TechStart GmbH - Innovatives IT-Startup'
        }
    },
    {
        'name': 'Global Manufacturing AG', 
        'slug': 'global-mfg', 
        'settings': {
            'default_language': 'de',
            'timezone': 'Europe/Berlin',
            'description': 'Global Manufacturing AG - Produktionsunternehmen'
        }
    },
]

DEMO_TEAMS = [
    {'name': 'Tax Advisory Team', 'description': 'Steuerberatung und Tax Compliance'},
    {'name': 'Audit Team', 'description': 'Wirtschaftsprüfung und Assurance'},
    {'name': 'Digital Transformation', 'description': 'Digitale Transformation und IT-Beratung'},
    {'name': 'Legal Services', 'description': 'Rechtsberatung und Compliance'},
]

DEMO_ENTITIES = [
    {'name': 'Mustermann GmbH', 'short_name': 'MUST', 'country': 'DE'},
    {'name': 'Innovation AG', 'short_name': 'INNO', 'country': 'DE'},
    {'name': 'Handwerk Meier KG', 'short_name': 'MEIER', 'country': 'DE'},
    {'name': 'Digital Solutions UG', 'short_name': 'DIGI', 'country': 'DE'},
    {'name': 'Family Office Schmidt', 'short_name': 'SCHMIDT', 'country': 'DE'},
]

# Task Categories (unified - replaces old TaxType and TaskCategory)
DEMO_TASK_CATEGORIES = [
    # Tax Types (Steuerarten)
    {'code': 'UST', 'name': 'Umsatzsteuer', 'name_en': 'VAT', 'color': '#0D8ABC', 'icon': 'bi-calculator'},
    {'code': 'KST', 'name': 'Körperschaftsteuer', 'name_en': 'Corporate Tax', 'color': '#26890D', 'icon': 'bi-calculator'},
    {'code': 'GEWST', 'name': 'Gewerbesteuer', 'name_en': 'Trade Tax', 'color': '#6B3FA0', 'icon': 'bi-calculator'},
    {'code': 'LST', 'name': 'Lohnsteuer', 'name_en': 'Payroll Tax', 'color': '#DA291C', 'icon': 'bi-calculator'},
    {'code': 'ERBST', 'name': 'Erbschaftsteuer', 'name_en': 'Inheritance Tax', 'color': '#FF6B35', 'icon': 'bi-calculator'},
    {'code': 'GRUNDST', 'name': 'Grundsteuer', 'name_en': 'Property Tax', 'color': '#8B4513', 'icon': 'bi-calculator'},
    # General Categories
    {'code': 'BUCH', 'name': 'Buchhaltung', 'name_en': 'Accounting', 'color': '#75787B', 'icon': 'bi-journal-text'},
    {'code': 'JAHRES', 'name': 'Jahresabschluss', 'name_en': 'Annual Statements', 'color': '#4BADE8', 'icon': 'bi-file-earmark-text'},
    {'code': 'COMPL', 'name': 'Compliance', 'name_en': 'Compliance', 'color': '#0076A8', 'icon': 'bi-shield-check'},
    {'code': 'AUDIT', 'name': 'Prüfung', 'name_en': 'Audit', 'color': '#62B5E5', 'icon': 'bi-clipboard-check'},
    {'code': 'SONST', 'name': 'Sonstige', 'name_en': 'Other', 'color': '#6c757d', 'icon': 'bi-folder'},
]

DEMO_PROJECTS = [
    {
        'name': 'Jahresabschluss 2025',
        'name_en': 'Annual Report 2025',
        'key': 'JAB',
        'description': 'Erstellung des Jahresabschlusses für das Geschäftsjahr 2025',
        'methodology': ProjectMethodology.KANBAN,
        'category': 'Accounting',
        'icon': 'bi-file-earmark-text',
        'color': '#86BC25'
    },
    {
        'name': 'Steuer-Compliance Q1-Q4',
        'name_en': 'Tax Compliance Q1-Q4',
        'key': 'TAX',
        'description': 'Umsatzsteuer-Compliance und Reporting für Q1-Q4 2026',
        'methodology': ProjectMethodology.SCRUM,
        'category': 'Tax',
        'icon': 'bi-calculator',
        'color': '#0076A8'
    },
    {
        'name': 'ERP-Migration SAP',
        'name_en': 'ERP Migration SAP',
        'key': 'ERP',
        'description': 'Migration des ERP-Systems auf SAP S/4HANA',
        'methodology': ProjectMethodology.SCRUM,
        'category': 'IT',
        'icon': 'bi-database',
        'color': '#DA291C'
    },
    {
        'name': 'Audit 2026',
        'name_en': 'Audit 2026',
        'key': 'AUD',
        'description': 'Wirtschaftsprüfung für das Geschäftsjahr 2026',
        'methodology': ProjectMethodology.KANBAN,
        'category': 'Audit',
        'icon': 'bi-clipboard-check',
        'color': '#6B3FA0'
    },
    {
        'name': 'IT-Sicherheitsaudit',
        'name_en': 'IT Security Audit',
        'key': 'SEC',
        'description': 'Sicherheitsüberprüfung der IT-Infrastruktur',
        'methodology': ProjectMethodology.SCRUM,
        'category': 'Security',
        'icon': 'bi-shield-check',
        'color': '#62B5E5'
    },
    {
        'name': 'Interne Prozessoptimierung',
        'name_en': 'Internal Process Optimization',
        'key': 'INT',
        'description': 'Optimierung interner Arbeitsabläufe und Prozesse',
        'methodology': ProjectMethodology.KANBAN,
        'category': 'Internal',
        'icon': 'bi-gear',
        'color': '#75787B'
    },
]

DEMO_ISSUE_TYPES = [
    {'name': 'Epic', 'name_en': 'Epic', 'icon': 'bi-lightning-charge', 'color': '#6B3FA0', 'hierarchy_level': 0},
    {'name': 'Story', 'name_en': 'Story', 'icon': 'bi-bookmark', 'color': '#0076A8', 'hierarchy_level': 1},
    {'name': 'Aufgabe', 'name_en': 'Task', 'icon': 'bi-check2-square', 'color': '#86BC25', 'hierarchy_level': 2},
    {'name': 'Bug', 'name_en': 'Bug', 'icon': 'bi-bug', 'color': '#DA291C', 'hierarchy_level': 2},
    {'name': 'Verbesserung', 'name_en': 'Improvement', 'icon': 'bi-arrow-up-circle', 'color': '#26890D', 'hierarchy_level': 2},
    {'name': 'Subtask', 'name_en': 'Subtask', 'icon': 'bi-list-task', 'color': '#62B5E5', 'hierarchy_level': 3, 'is_subtask': True},
]

DEMO_ISSUE_STATUSES = [
    {'name': 'Offen', 'name_en': 'Open', 'category': 'todo', 'color': '#75787B', 'is_initial': True, 'sort_order': 1,
     'transitions_to': ['In Bearbeitung', 'Blockiert']},
    {'name': 'In Bearbeitung', 'name_en': 'In Progress', 'category': 'in_progress', 'color': '#0D8ABC', 'sort_order': 2,
     'transitions_to': ['In Review', 'Blockiert', 'Offen']},
    {'name': 'In Review', 'name_en': 'In Review', 'category': 'in_progress', 'color': '#4BADE8', 'sort_order': 3,
     'transitions_to': ['Erledigt', 'In Bearbeitung', 'Blockiert']},
    {'name': 'Blockiert', 'name_en': 'Blocked', 'category': 'in_progress', 'color': '#DA291C', 'sort_order': 4,
     'transitions_to': ['Offen', 'In Bearbeitung']},
    {'name': 'Erledigt', 'name_en': 'Done', 'category': 'done', 'color': '#26890D', 'is_final': True, 'sort_order': 5,
     'transitions_to': []},  # Final status - no transitions out
]

DEMO_ISSUES = [
    # Epics
    {'type': 'Epic', 'summary': 'Q1 2026 Steuerliche Compliance', 'description': 'Alle steuerlichen Pflichten für Q1 2026', 'priority': 1, 'labels': ['Q1-2026', 'Compliance']},
    {'type': 'Epic', 'summary': 'Digitalisierung Phase 1', 'description': 'Erste Phase der Digitalisierungsinitiative', 'priority': 2, 'labels': ['Digital', 'Phase-1']},
    {'type': 'Epic', 'summary': 'Prozessoptimierung 2026', 'description': 'Prozessverbesserungen für das Jahr 2026', 'priority': 2, 'labels': ['Optimierung', '2026']},
    
    # Stories
    {'type': 'Story', 'summary': 'USt-Voranmeldung Januar einreichen', 'priority': 1, 'story_points': 5, 'labels': ['USt', 'Monatlich'], 'due_days': 10},
    {'type': 'Story', 'summary': 'Lohnsteuer-Anmeldung Februar', 'priority': 2, 'story_points': 3, 'labels': ['LohnSt', 'Monatlich'], 'due_days': 15},
    {'type': 'Story', 'summary': 'Jahresabschluss-Unterlagen sammeln', 'priority': 2, 'story_points': 8, 'labels': ['Jahresabschluss'], 'due_days': 30},
    {'type': 'Story', 'summary': 'Dokumenten-Scanner Integration', 'priority': 3, 'story_points': 5, 'labels': ['Integration'], 'due_days': 45},
    {'type': 'Story', 'summary': 'Reporting Dashboard erstellen', 'priority': 2, 'story_points': 8, 'labels': ['Dashboard', 'Reporting'], 'due_days': 21},
    {'type': 'Story', 'summary': 'API-Anbindung Finanzamt', 'priority': 1, 'story_points': 13, 'labels': ['API', 'Finanzamt'], 'due_days': 60},
    {'type': 'Story', 'summary': 'Mitarbeiter-Schulung planen', 'priority': 3, 'story_points': 3, 'labels': ['Schulung'], 'due_days': 25},
    {'type': 'Story', 'summary': 'Buchhaltungs-Workflow automatisieren', 'priority': 2, 'story_points': 8, 'labels': ['Automation'], 'due_days': 35},
    
    # Tasks
    {'type': 'Aufgabe', 'summary': 'Belegprüfung Januar', 'priority': 2, 'story_points': 2, 'due_days': 5},
    {'type': 'Aufgabe', 'summary': 'Kontenabstimmung durchführen', 'priority': 2, 'story_points': 3, 'due_days': 7},
    {'type': 'Aufgabe', 'summary': 'Quartalsbericht erstellen', 'priority': 1, 'story_points': 5, 'due_days': 14},
    {'type': 'Aufgabe', 'summary': 'Team-Meeting organisieren', 'priority': 4, 'story_points': 1, 'due_days': 3},
    {'type': 'Aufgabe', 'summary': 'Dokumentation aktualisieren', 'priority': 3, 'story_points': 2, 'due_days': 10},
    {'type': 'Aufgabe', 'summary': 'Systemkonfiguration prüfen', 'priority': 2, 'story_points': 3, 'due_days': 8},
    {'type': 'Aufgabe', 'summary': 'Backup-Strategie überprüfen', 'priority': 2, 'story_points': 2, 'due_days': 12},
    {'type': 'Aufgabe', 'summary': 'Kundenfeedback auswerten', 'priority': 3, 'story_points': 3, 'due_days': 18},
    
    # Bugs
    {'type': 'Bug', 'summary': 'Berechnungsfehler im USt-Formular', 'priority': 1, 'labels': ['Bug', 'Urgent'], 'due_days': 1},
    {'type': 'Bug', 'summary': 'Formatierung in Export fehlerhaft', 'priority': 3, 'labels': ['Bug'], 'due_days': 7},
    {'type': 'Bug', 'summary': 'Performance-Problem bei großen Datenmengen', 'priority': 2, 'labels': ['Bug', 'Performance'], 'due_days': 5},
    {'type': 'Bug', 'summary': 'Druckvorschau zeigt falsche Daten', 'priority': 2, 'labels': ['Bug'], 'due_days': 6},
    
    # Improvements
    {'type': 'Verbesserung', 'summary': 'UI/UX Verbesserungen Dashboard', 'priority': 3, 'story_points': 5, 'labels': ['UI', 'UX'], 'due_days': 20},
    {'type': 'Verbesserung', 'summary': 'Ladezeiten optimieren', 'priority': 2, 'story_points': 3, 'labels': ['Performance'], 'due_days': 15},
]

DEMO_COMMENTS = [
    "Gute Arbeit! Das sieht sehr gut aus.",
    "Können wir das in der nächsten Iteration priorisieren?",
    "Ich habe einige Änderungen vorgenommen. Bitte reviewen.",
    "Status-Update: 80% fertig, warte auf Feedback.",
    "Habe das Problem identifiziert. Fix kommt heute.",
    "Benötige mehr Informationen zu den Anforderungen.",
    "Tests sind durchgelaufen. Ready for deployment.",
    "@Team: Bitte um kurzes Feedback bis EOD.",
    "Das Ticket ist fertig. Kann in Review gehen.",
    "Guter Fortschritt! Weiter so.",
]

# Kommentare für Tasks
DEMO_TASK_COMMENTS = [
    "Belege wurden alle geprüft und sind vollständig.",
    "Abstimmung mit Mandant erfolgt.",
    "Finanzamt hat Frist verlängert - neues Fälligkeitsdatum beachten!",
    "Steuerliche Besonderheit: Vorsteuerabzug eingeschränkt wegen gemischter Nutzung.",
    "Zahlen wurden mit DATEV abgeglichen - alles korrekt.",
    "Bitte nochmal die Kontenabstimmung für Konto 1200 prüfen.",
    "Aufgabe kann an Reviewer übergeben werden.",
    "Kleinere Korrekturen notwendig - Details im Beleg.",
    "Telefonat mit FA dokumentiert - siehe Aktennotiz.",
    "Quartalsvergleich zeigt Abweichung - muss analysiert werden.",
    "Review abgeschlossen - keine Beanstandungen.",
    "Zur Freigabe bereit.",
    "Mandant hat neue Belege nachgereicht.",
    "Rückfrage an Mandant gestellt - warte auf Antwort.",
    "Wichtig: Frist endet am 10. des Folgemonats!",
]

DEMO_TASKS = [
    {'title': 'USt-Voranmeldung Januar', 'status': 'completed', 'days_offset': -30},
    {'title': 'USt-Voranmeldung Februar', 'status': 'completed', 'days_offset': -20},
    {'title': 'USt-Voranmeldung März', 'status': 'in_review', 'days_offset': -5},
    {'title': 'USt-Voranmeldung April', 'status': 'in_progress', 'days_offset': 10},
    {'title': 'Quartalsabschluss Q1', 'status': 'completed', 'days_offset': -15},
    {'title': 'Quartalsabschluss Q2', 'status': 'draft', 'days_offset': 45},
    {'title': 'Jahresabschluss 2025 vorbereiten', 'status': 'in_progress', 'days_offset': 30},
    {'title': 'Steuerliche Gewinnermittlung', 'status': 'draft', 'days_offset': 60},
    {'title': 'Betriebsprüfung vorbereiten', 'status': 'draft', 'days_offset': 90},
    {'title': 'Lohnsteuerbescheinigungen erstellen', 'status': 'completed', 'days_offset': -45},
    {'title': 'GewSt-Erklärung 2025', 'status': 'draft', 'days_offset': 120},
    {'title': 'KSt-Erklärung 2025', 'status': 'draft', 'days_offset': 120},
]

DEMO_TASK_PRESETS = [
    # Umsatzsteuer-Vorlagen
    {'category': 'USt', 'title_de': 'USt-Voranmeldung (monatlich)', 'title_en': 'VAT Return (monthly)',
     'description_de': 'Monatliche Umsatzsteuer-Voranmeldung gemäß § 18 UStG', 
     'law_reference': '§ 18 UStG', 'is_recurring': True, 'recurrence_frequency': 'monthly'},
    {'category': 'USt', 'title_de': 'USt-Voranmeldung (vierteljährlich)', 'title_en': 'VAT Return (quarterly)',
     'description_de': 'Vierteljährliche Umsatzsteuer-Voranmeldung', 
     'law_reference': '§ 18 UStG', 'is_recurring': True, 'recurrence_frequency': 'quarterly'},
    {'category': 'USt', 'title_de': 'Zusammenfassende Meldung (ZM)', 'title_en': 'EC Sales List',
     'description_de': 'Zusammenfassende Meldung für innergemeinschaftliche Lieferungen', 
     'law_reference': '§ 18a UStG', 'is_recurring': True, 'recurrence_frequency': 'monthly'},
    {'category': 'USt', 'title_de': 'USt-Jahreserklärung', 'title_en': 'Annual VAT Return',
     'description_de': 'Jährliche Umsatzsteuererklärung', 
     'law_reference': '§ 18 Abs. 3 UStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    
    # Körperschaftsteuer-Vorlagen
    {'category': 'KSt', 'title_de': 'KSt-Vorauszahlung', 'title_en': 'Corporate Tax Prepayment',
     'description_de': 'Vierteljährliche Körperschaftsteuer-Vorauszahlung', 
     'law_reference': '§ 31 KStG', 'is_recurring': True, 'recurrence_frequency': 'quarterly'},
    {'category': 'KSt', 'title_de': 'KSt-Jahreserklärung', 'title_en': 'Annual Corporate Tax Return',
     'description_de': 'Jährliche Körperschaftsteuererklärung mit Anlagen', 
     'law_reference': '§ 31 KStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'KSt', 'title_de': 'Anlage GK erstellen', 'title_en': 'Create Appendix GK',
     'description_de': 'Anlage zur Ermittlung des Gewerbeertrags', 
     'law_reference': '§ 7 GewStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    
    # Gewerbesteuer-Vorlagen
    {'category': 'GewSt', 'title_de': 'GewSt-Vorauszahlung', 'title_en': 'Trade Tax Prepayment',
     'description_de': 'Vierteljährliche Gewerbesteuer-Vorauszahlung', 
     'law_reference': '§ 19 GewStG', 'is_recurring': True, 'recurrence_frequency': 'quarterly'},
    {'category': 'GewSt', 'title_de': 'GewSt-Jahreserklärung', 'title_en': 'Annual Trade Tax Return',
     'description_de': 'Jährliche Gewerbesteuererklärung', 
     'law_reference': '§ 14a GewStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'GewSt', 'title_de': 'Gewerbesteuer-Zerlegung', 'title_en': 'Trade Tax Allocation',
     'description_de': 'Zerlegungserklärung bei mehreren Betriebsstätten', 
     'law_reference': '§ 28 GewStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    
    # Lohnsteuer-Vorlagen
    {'category': 'LohnSt', 'title_de': 'Lohnsteuer-Anmeldung (monatlich)', 'title_en': 'Payroll Tax Return (monthly)',
     'description_de': 'Monatliche Lohnsteuer-Anmeldung', 
     'law_reference': '§ 41a EStG', 'is_recurring': True, 'recurrence_frequency': 'monthly'},
    {'category': 'LohnSt', 'title_de': 'Lohnsteuerbescheinigung erstellen', 'title_en': 'Create Wage Tax Certificate',
     'description_de': 'Elektronische Lohnsteuerbescheinigung für Mitarbeiter', 
     'law_reference': '§ 41b EStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'LohnSt', 'title_de': 'Sozialversicherungsmeldungen', 'title_en': 'Social Security Reports',
     'description_de': 'Meldungen zur Sozialversicherung', 
     'law_reference': 'SGB IV', 'is_recurring': True, 'recurrence_frequency': 'monthly'},
    
    # Buchhaltung-Vorlagen
    {'category': 'Buchhaltung', 'title_de': 'Monatsabschluss', 'title_en': 'Monthly Closing',
     'description_de': 'Monatlicher Abschluss der Buchhaltung mit Abstimmungen', 
     'is_recurring': True, 'recurrence_frequency': 'monthly'},
    {'category': 'Buchhaltung', 'title_de': 'Quartalsabschluss', 'title_en': 'Quarterly Closing',
     'description_de': 'Quartalsmäßiger Abschluss mit Reporting', 
     'is_recurring': True, 'recurrence_frequency': 'quarterly'},
    {'category': 'Buchhaltung', 'title_de': 'Kontenabstimmung', 'title_en': 'Account Reconciliation',
     'description_de': 'Abstimmung aller Konten und Saldenbestätigung', 
     'is_recurring': True, 'recurrence_frequency': 'monthly'},
    {'category': 'Buchhaltung', 'title_de': 'Anlagenverzeichnis aktualisieren', 'title_en': 'Update Fixed Asset Register',
     'description_de': 'Aktualisierung des Anlageverzeichnisses mit AfA-Berechnung', 
     'is_recurring': True, 'recurrence_frequency': 'yearly'},
    
    # Jahresabschluss-Vorlagen
    {'category': 'Jahresabschluss', 'title_de': 'Jahresabschluss erstellen', 'title_en': 'Prepare Annual Financial Statements',
     'description_de': 'Erstellung des Jahresabschlusses nach HGB', 
     'law_reference': '§ 242 HGB', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'Jahresabschluss', 'title_de': 'E-Bilanz übermitteln', 'title_en': 'Submit E-Balance',
     'description_de': 'Elektronische Übermittlung der Bilanz an das Finanzamt', 
     'law_reference': '§ 5b EStG', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'Jahresabschluss', 'title_de': 'Lagebericht erstellen', 'title_en': 'Create Management Report',
     'description_de': 'Erstellung des Lageberichts für kapitalmarktorientierte Unternehmen', 
     'law_reference': '§ 289 HGB', 'is_recurring': True, 'recurrence_frequency': 'yearly'},
    {'category': 'Jahresabschluss', 'title_de': 'Gesellschafterversammlung vorbereiten', 'title_en': 'Prepare Shareholder Meeting',
     'description_de': 'Vorbereitung der Unterlagen für die Gesellschafterversammlung', 
     'is_recurring': True, 'recurrence_frequency': 'yearly'},
    
    # Sonstige Vorlagen
    {'category': 'Sonstige', 'title_de': 'Betriebsprüfung begleiten', 'title_en': 'Accompany Tax Audit',
     'description_de': 'Begleitung und Koordination der Betriebsprüfung', 
     'is_recurring': False},
    {'category': 'Sonstige', 'title_de': 'Einspruch einlegen', 'title_en': 'File Objection',
     'description_de': 'Einspruch gegen Steuerbescheid einlegen', 
     'law_reference': '§ 347 AO', 'is_recurring': False},
    {'category': 'Sonstige', 'title_de': 'Fristverlängerung beantragen', 'title_en': 'Request Extension',
     'description_de': 'Antrag auf Fristverlängerung beim Finanzamt', 
     'law_reference': '§ 109 AO', 'is_recurring': False},
]


# =============================================================================
# CREATION FUNCTIONS
# =============================================================================

def reset_database():
    """Drop all tables and recreate them."""
    print("\n🗑️  Resetting database...")
    db.drop_all()
    db.create_all()
    print("✅ Database reset complete!")


def create_modules():
    """Create application modules."""
    print("\n📦 Creating modules...")
    
    modules = []
    
    # Core module (always available)
    core = Module(
        code='core',
        name_de='Kernfunktionen',
        name_en='Core Functions',
        description_de='Dashboard, Aufgaben, Kalender und grundlegende Funktionen',
        description_en='Dashboard, tasks, calendar and basic functions',
        icon='bi-house',
        nav_order=0,
        is_core=True,
        is_active=True
    )
    db.session.add(core)
    modules.append(core)
    
    # Projects module
    projects = Module(
        code='projects',
        name_de='Projektmanagement',
        name_en='Project Management',
        description_de='Projekte, Sprints, Kanban-Boards und Issue-Tracking',
        description_en='Projects, sprints, Kanban boards and issue tracking',
        icon='bi-kanban',
        nav_order=10,
        is_core=False,
        is_active=True
    )
    db.session.add(projects)
    modules.append(projects)
    
    db.session.commit()
    print(f"   ✅ Created {len(modules)} modules")
    
    return {m.code: m for m in modules}


def create_users():
    """Create all demo users."""
    print("\n👥 Creating users...")
    users = []
    
    for data in DEMO_USERS:
        user = User(
            email=data['email'],
            name=data['name'],
            role=data['role'],
            is_superadmin=data.get('is_superadmin', False),
            is_active=True
        )
        user.set_password(data['password'])
        db.session.add(user)
        users.append(user)
        superadmin_marker = '⭐' if data.get('is_superadmin') else ''
        print(f"  ✓ {data['name']} ({data['role']}) {superadmin_marker}")
    
    db.session.commit()
    print(f"✅ {len(users)} users created!")
    return users


def create_tenants(users):
    """Create demo tenants and memberships."""
    print("\n🏢 Creating tenants...")
    tenants = []
    admin_user = users[0]  # First user is superadmin
    
    for data in DEMO_TENANTS:
        tenant = Tenant(
            name=data['name'],
            slug=data['slug'],
            is_active=True,
            settings=data.get('settings', {}),
            created_by_id=admin_user.id
        )
        db.session.add(tenant)
        tenants.append(tenant)
        print(f"  ✓ {data['name']}")
    
    db.session.flush()
    
    # Add users to first tenant
    main_tenant = tenants[0]
    for i, user in enumerate(users):
        role = 'admin' if i < 4 else 'member'
        if user.role == 'viewer' or user.role == 'readonly':
            role = 'viewer'
        
        membership = TenantMembership(
            tenant_id=main_tenant.id,
            user_id=user.id,
            role=role
        )
        db.session.add(membership)
        
        # Set default tenant for all users
        user.current_tenant_id = main_tenant.id
    
    db.session.commit()
    print(f"✅ {len(tenants)} tenants created!")
    return tenants


def create_user_modules(users, modules):
    """Assign modules to non-admin users."""
    print("\n🔐 Assigning module permissions...")
    
    projects_module = modules.get('projects')
    if not projects_module:
        print("   ⚠️  Projects module not found")
        return []
    
    assignments = []
    
    # Assign projects module to all non-admin users
    for user in users:
        # Admins don't need explicit module assignments (they have access to all)
        if user.role == 'admin':
            continue
        
        # Check if already assigned
        existing = UserModule.query.filter_by(user_id=user.id, module_id=projects_module.id).first()
        if not existing:
            um = UserModule(
                user_id=user.id,
                module_id=projects_module.id
            )
            db.session.add(um)
            assignments.append(um)
    
    db.session.commit()
    print(f"   ✅ Created {len(assignments)} module assignments")
    
    return assignments


def create_teams(users, tenants):
    """Create demo teams."""
    print("\n👨‍👩‍👧‍👦 Creating teams...")
    teams = []
    main_tenant = tenants[0]
    admin_user = users[0]
    
    for i, data in enumerate(DEMO_TEAMS):
        team = Team(
            name=data['name'],
            description=data['description'],
            tenant_id=main_tenant.id,
            manager_id=admin_user.id
        )
        db.session.add(team)
        db.session.flush()
        
        # Add members
        team_users = users[i*3:(i*3)+4] if len(users) > i*3 else users[:3]
        for member in team_users:
            if member not in team.members:
                team.members.append(member)
        
        teams.append(team)
        print(f"  ✓ {data['name']} ({len(team_users)} members)")
    
    db.session.commit()
    print(f"✅ {len(teams)} teams created!")
    return teams


def create_entities(users, tenants):
    """Create demo entities."""
    print("\n🏛️  Creating entities...")
    entities = []
    main_tenant = tenants[0]
    
    for data in DEMO_ENTITIES:
        entity = Entity(
            name=data['name'],
            short_name=data['short_name'],
            country=data['country'],
            tenant_id=main_tenant.id,
            is_active=True
        )
        db.session.add(entity)
        db.session.flush()
        
        # Assign first 4 users to each entity
        for i, user in enumerate(users[:4]):
            access = 'manage' if i == 0 else 'edit'
            user_entity = UserEntity(
                user_id=user.id,
                entity_id=entity.id,
                access_level=access
            )
            db.session.add(user_entity)
        
        entities.append(entity)
        print(f"  ✓ {data['name']} ({data['short_name']})")
    
    db.session.commit()
    print(f"✅ {len(entities)} entities created!")
    return entities


def create_task_categories(tenants):
    """Create demo task categories (includes tax types - unified model)."""
    print("\n📂 Creating task categories...")
    categories = []
    main_tenant = tenants[0]
    
    for data in DEMO_TASK_CATEGORIES:
        category = TaskCategory(
            code=data['code'],
            name=data['name'],
            name_en=data.get('name_en'),
            color=data.get('color', '#6c757d'),
            icon=data.get('icon', 'bi-folder'),
            tenant_id=main_tenant.id
        )
        db.session.add(category)
        categories.append(category)
        print(f"  ✓ {data['code']} - {data['name']}")
    
    db.session.commit()
    print(f"✅ {len(categories)} categories created!")
    return categories


def create_task_presets(tenants):
    """Create task presets from JSON files in data folder."""
    print("\n📝 Creating task presets from JSON files...")
    presets = []
    main_tenant = tenants[0]
    
    # Path to data folder
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
    
    # Import Anträge
    antraege_path = os.path.join(data_dir, 'Antraege.json')
    if os.path.exists(antraege_path):
        with open(antraege_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'sheets' in data:
                for sheet_name, records in data['sheets'].items():
                    for record in records:
                        title = record.get('Zweck des Antrags')
                        if not title:
                            continue
                        preset = TaskPreset(
                            tenant_id=main_tenant.id,
                            category='antrag',
                            title=title,
                            title_de=title,
                            law_reference=record.get('§ Paragraph'),
                            tax_type=record.get('Gesetz'),
                            description=record.get('Erläuterung'),
                            description_de=record.get('Erläuterung'),
                            source='json',
                            is_active=True
                        )
                        db.session.add(preset)
                        presets.append(preset)
        print(f"  ✓ Anträge: {len([p for p in presets if p.category == 'antrag'])} Vorlagen")
    
    # Import Aufgaben
    aufgaben_path = os.path.join(data_dir, 'steuerarten_aufgaben.json')
    if os.path.exists(aufgaben_path):
        with open(aufgaben_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'records' in data:
                for record in data['records']:
                    title = record.get('aufgabe')
                    if not title:
                        continue
                    preset = TaskPreset(
                        tenant_id=main_tenant.id,
                        category='aufgabe',
                        title=title,
                        title_de=title,
                        tax_type=record.get('steuerart'),
                        source='json',
                        is_active=True
                    )
                    db.session.add(preset)
                    presets.append(preset)
        print(f"  ✓ Aufgaben: {len([p for p in presets if p.category == 'aufgabe'])} Vorlagen")
    
    # Add some recurring presets manually
    recurring_presets = [
        {'category': 'aufgabe', 'title': 'USt-Voranmeldung (monatlich)', 'tax_type': 'Umsatzsteuer', 
         'is_recurring': True, 'recurrence_frequency': 'monthly', 'recurrence_day_offset': 10},
        {'category': 'aufgabe', 'title': 'Lohnsteuer-Anmeldung', 'tax_type': 'Lohnsteuer',
         'is_recurring': True, 'recurrence_frequency': 'monthly', 'recurrence_day_offset': 10},
        {'category': 'aufgabe', 'title': 'Quartalsabschluss', 'tax_type': 'Buchhaltung',
         'is_recurring': True, 'recurrence_frequency': 'quarterly'},
        {'category': 'aufgabe', 'title': 'Jahresabschluss erstellen', 'tax_type': 'Jahresabschluss',
         'is_recurring': True, 'recurrence_frequency': 'annual'},
    ]
    
    for rp in recurring_presets:
        preset = TaskPreset(
            tenant_id=main_tenant.id,
            category=rp['category'],
            title=rp['title'],
            title_de=rp['title'],
            tax_type=rp.get('tax_type'),
            is_recurring=rp.get('is_recurring', False),
            recurrence_frequency=rp.get('recurrence_frequency', 'none'),
            recurrence_day_offset=rp.get('recurrence_day_offset', 0),
            source='demo',
            is_active=True
        )
        db.session.add(preset)
        presets.append(preset)
    
    print(f"  ✓ Wiederkehrende Aufgaben: {len(recurring_presets)} Vorlagen")
    
    db.session.commit()
    print(f"✅ {len(presets)} task presets created!")
    return presets


def create_projects(users, tenants):
    """Create demo projects with types and statuses."""
    print("\n📁 Creating projects...")
    projects = []
    main_tenant = tenants[0]
    admin_user = users[0]
    
    for data in DEMO_PROJECTS:
        project = Project(
            name=data['name'],
            name_en=data.get('name_en', data['name']),
            key=data['key'],
            description=data['description'],
            methodology=data['methodology'].value if hasattr(data['methodology'], 'value') else str(data['methodology']),
            category=data.get('category', 'General'),
            icon=data.get('icon', 'bi-folder'),
            color=data.get('color', '#0076A8'),
            tenant_id=main_tenant.id,
            lead_id=admin_user.id,
            created_by_id=admin_user.id
        )
        db.session.add(project)
        db.session.flush()
        
        # Create issue types
        created_types = []
        for it_data in DEMO_ISSUE_TYPES:
            issue_type = IssueType(
                project_id=project.id,
                name=it_data['name'],
                name_en=it_data['name_en'],
                icon=it_data['icon'],
                color=it_data['color'],
                hierarchy_level=it_data.get('hierarchy_level', 2),
                is_subtask=it_data.get('is_subtask', False)
            )
            db.session.add(issue_type)
            created_types.append(issue_type)
        
        # Create statuses
        created_statuses = []
        for st_data in DEMO_ISSUE_STATUSES:
            status = IssueStatus(
                project_id=project.id,
                name=st_data['name'],
                name_en=st_data['name_en'],
                category=st_data['category'],
                color=st_data['color'],
                is_initial=st_data.get('is_initial', False),
                is_final=st_data.get('is_final', False),
                sort_order=st_data['sort_order']
            )
            db.session.add(status)
            created_statuses.append(status)
        
        db.session.flush()
        
        # Set allowed_transitions (now that we have IDs)
        status_name_to_id = {s.name: s.id for s in created_statuses}
        for i, st_data in enumerate(DEMO_ISSUE_STATUSES):
            transitions_to = st_data.get('transitions_to', [])
            if transitions_to:
                created_statuses[i].allowed_transitions = [
                    status_name_to_id[name] for name in transitions_to if name in status_name_to_id
                ]
            else:
                created_statuses[i].allowed_transitions = []  # Explicitly empty for final status
        
        db.session.flush()
        
        # Add project members
        for i, user in enumerate(users[:8]):
            role = 'admin' if i == 0 else ('lead' if i < 3 else 'member')
            member = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role=role,
                added_by_id=admin_user.id
            )
            db.session.add(member)
        
        # Store for later use
        project._types = {t.name: t for t in created_types}
        project._statuses = created_statuses
        
        projects.append(project)
        print(f"  ✓ {data['key']} - {data['name']} ({data['methodology'].value})")
    
    db.session.commit()
    print(f"✅ {len(projects)} projects created!")
    return projects


def create_sprints(projects):
    """Create demo sprints for Scrum projects."""
    print("\n🏃 Creating sprints...")
    sprints = []
    
    for project in projects:
        if project.methodology not in ['scrum', 'SCRUM']:
            continue
        
        sprint_data = [
            {'name': 'Sprint 1 - Kickoff', 'goal': 'Projektstart und Grundlagen', 'start': -42, 'end': -28, 'state': 'closed'},
            {'name': 'Sprint 2 - Foundation', 'goal': 'Basisinfrastruktur aufbauen', 'start': -28, 'end': -14, 'state': 'closed'},
            {'name': 'Sprint 3 - Development', 'goal': 'Kernfunktionen entwickeln', 'start': -7, 'end': 7, 'state': 'active'},
            {'name': 'Sprint 4 - Integration', 'goal': 'Systemintegration und Tests', 'start': 14, 'end': 28, 'state': 'future'},
            {'name': 'Sprint 5 - Release', 'goal': 'Finale Tests und Go-Live', 'start': 28, 'end': 42, 'state': 'future'},
        ]
        
        for s_data in sprint_data:
            sprint = Sprint(
                project_id=project.id,
                name=s_data['name'],
                goal=s_data['goal'],
                start_date=date.today() + timedelta(days=s_data['start']),
                end_date=date.today() + timedelta(days=s_data['end']),
                state=s_data['state'],
                started_at=datetime.now() + timedelta(days=s_data['start']) if s_data['state'] in ['active', 'closed'] else None,
                completed_at=datetime.now() + timedelta(days=s_data['end']) if s_data['state'] == 'closed' else None,
                tenant_id=project.tenant_id
            )
            db.session.add(sprint)
            sprints.append(sprint)
        
        print(f"  ✓ {project.key}: 5 sprints")
    
    db.session.commit()
    print(f"✅ {len(sprints)} sprints created!")
    return sprints


def create_issues(projects, users, sprints):
    """Create demo issues."""
    print("\n📋 Creating issues...")
    issues = []
    issue_num = {}
    
    for project in projects:
        issue_num[project.id] = 0
        types = getattr(project, '_types', {})
        statuses = getattr(project, '_statuses', [])
        project_sprints = [s for s in sprints if s.project_id == project.id]
        
        if not types or not statuses:
            continue
        
        for issue_data in DEMO_ISSUES:
            type_name = issue_data['type']
            issue_type = types.get(type_name)
            if not issue_type:
                continue
            
            issue_num[project.id] += 1
            status = random.choice(statuses)
            assignee = random.choice(users[:8])
            sprint = random.choice(project_sprints) if project_sprints else None
            
            due_days = issue_data.get('due_days', random.randint(7, 60))
            labels = issue_data.get('labels', [])
            if isinstance(labels, str):
                labels = [l.strip() for l in labels.split(',')]
            
            issue = Issue(
                project_id=project.id,
                key=f"{project.key}-{issue_num[project.id]}",
                type_id=issue_type.id,
                status_id=status.id,
                summary=issue_data['summary'],
                description=issue_data.get('description', f"Detaillierte Beschreibung für: {issue_data['summary']}"),
                priority=issue_data.get('priority', 3),
                story_points=issue_data.get('story_points'),
                labels=labels,
                due_date=date.today() + timedelta(days=due_days),
                assignee_id=assignee.id,
                reporter_id=users[0].id,
                sprint_id=sprint.id if sprint else None,
                tenant_id=project.tenant_id,
                created_at=datetime.now() - timedelta(days=random.randint(1, 60))
            )
            db.session.add(issue)
            issues.append(issue)
        
        print(f"  ✓ {project.key}: {issue_num[project.id]} issues")
    
    db.session.commit()
    print(f"✅ {len(issues)} issues created!")
    return issues


def create_comments(issues, users):
    """Create demo comments on issues."""
    print("\n💬 Creating comments...")
    comments = []
    
    for issue in issues[:50]:  # First 50 issues get comments
        num_comments = random.randint(1, 5)
        for _ in range(num_comments):
            comment = IssueComment(
                issue_id=issue.id,
                author_id=random.choice(users[:8]).id,
                content=random.choice(DEMO_COMMENTS),
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(comment)
            comments.append(comment)
    
    db.session.commit()
    print(f"✅ {len(comments)} comments created!")
    return comments


def create_tasks(users, entities, categories):
    """Create demo tasks from presets with comments, reviewers and various statuses."""
    print("\n📋 Creating tasks from presets...")
    tasks = []
    task_comments = []
    task_reviewers = []
    
    # Get users by role for assignment
    preparers = [u for u in users if u.role == 'preparer']
    reviewers = [u for u in users if u.role == 'reviewer']
    managers = [u for u in users if u.role in ('manager', 'admin')]
    all_workers = preparers + reviewers + managers[:2]
    
    # Get all presets (from database - already created)
    presets = TaskPreset.query.all()
    print(f"  Found {len(presets)} task presets to create tasks from")
    
    # Status distribution: more variation for realistic view
    status_distribution = [
        ('completed', 0.25),    # 25% completed
        ('approved', 0.10),     # 10% approved (ready to complete)
        ('in_review', 0.20),    # 20% in review
        ('submitted', 0.15),    # 15% submitted (awaiting review)
        ('draft', 0.30),        # 30% draft
    ]
    
    def pick_status():
        r = random.random()
        cumulative = 0
        for status, prob in status_distribution:
            cumulative += prob
            if r <= cumulative:
                return status
        return 'draft'
    
    # Create tasks for each entity using random presets
    for entity in entities:
        # Create 15-25 tasks per entity
        num_tasks = random.randint(15, 25)
        selected_presets = random.sample(presets, min(num_tasks, len(presets)))
        
        for i, preset in enumerate(selected_presets):
            status = pick_status()
            
            # Calculate due dates based on status (completed/approved = past, draft = future)
            if status in ('completed', 'approved'):
                days_offset = random.randint(-60, -5)
            elif status in ('in_review', 'submitted'):
                days_offset = random.randint(-10, 15)
            else:  # draft
                days_offset = random.randint(10, 90)
            
            # Pick owner
            owner = random.choice(all_workers) if all_workers else users[0]
            
            # Determine year and period
            year = 2026 if days_offset > -180 else 2025
            month = (date.today() + timedelta(days=days_offset)).month
            period = f"M{month:02d}" if preset.is_recurring and preset.recurrence_frequency == 'monthly' else f"Q{(month-1)//3 + 1}"
            
            task = Task(
                title=f"{preset.title_de or preset.title} - {entity.short_name or entity.name}",
                description=preset.description_de or preset.description or f"Aufgabe basierend auf: {preset.title_de}",
                status=status,
                due_date=date.today() + timedelta(days=days_offset),
                entity_id=entity.id,
                owner_id=owner.id,
                preset_id=preset.id,
                is_recurring_instance=preset.is_recurring,
                year=year,
                period=period,
                tenant_id=entity.tenant_id
            )
            
            # Add workflow timestamps based on status
            now = datetime.now()
            if status in ('submitted', 'in_review', 'approved', 'completed'):
                task.submitted_at = now - timedelta(days=random.randint(5, 20))
                task.submitted_by_id = owner.id
            if status in ('in_review', 'approved', 'completed'):
                task.reviewed_at = now - timedelta(days=random.randint(2, 10))
                task.reviewed_by_id = random.choice(reviewers).id if reviewers else users[0].id
            if status in ('approved', 'completed'):
                task.approved_at = now - timedelta(days=random.randint(1, 5))
                task.approved_by_id = random.choice(managers).id if managers else users[0].id
            if status == 'completed':
                task.completed_at = now - timedelta(days=random.randint(0, 3))
                task.completed_by_id = random.choice(managers).id if managers else users[0].id
                task.completion_note = f"Fristgerecht eingereicht am {task.completed_at.strftime('%d.%m.%Y')}."
            
            db.session.add(task)
            tasks.append(task)
    
    db.session.commit()
    print(f"  ✓ {len(tasks)} tasks created")
    
    # Now add reviewers and comments
    print("  Adding reviewers and comments...")
    
    for task in tasks:
        # Add 1-3 reviewers to tasks that are in workflow
        if task.status in ('submitted', 'in_review', 'approved', 'completed'):
            num_reviewers = random.randint(1, 3)
            available_reviewers = [u for u in (reviewers + managers[:2]) if u.id != task.owner_id]
            if available_reviewers:
                selected_reviewers = random.sample(available_reviewers, min(num_reviewers, len(available_reviewers)))
                
                for order, reviewer in enumerate(selected_reviewers, 1):
                    tr = TaskReviewer(
                        task_id=task.id,
                        user_id=reviewer.id,
                        order=order
                    )
                    # Set approval status based on task status
                    if task.status in ('approved', 'completed'):
                        tr.has_approved = True
                        tr.approved_at = task.approved_at or datetime.now()
                        tr.approval_note = random.choice([
                            "Alles korrekt geprüft.",
                            "Keine Beanstandungen.",
                            "Freigabe erteilt.",
                            "Geprüft und für gut befunden.",
                        ])
                    elif task.status == 'in_review' and order == 1 and random.random() > 0.5:
                        # First reviewer might have approved
                        tr.has_approved = True
                        tr.approved_at = datetime.now() - timedelta(days=random.randint(0, 3))
                        tr.approval_note = "Erste Prüfung abgeschlossen."
                    
                    db.session.add(tr)
                    task_reviewers.append(tr)
        
        # Add 1-4 comments to most tasks
        if random.random() > 0.2:  # 80% of tasks get comments
            num_comments = random.randint(1, 4)
            comment_authors = [u for u in all_workers + reviewers if u.id]
            
            for c in range(num_comments):
                author = random.choice(comment_authors) if comment_authors else users[0]
                days_ago = random.randint(0, 30)
                
                comment = Comment(
                    task_id=task.id,
                    text=random.choice(DEMO_TASK_COMMENTS),
                    created_by_id=author.id,
                    created_at=datetime.now() - timedelta(days=days_ago),
                    is_resolved=random.choice([True, False, False])  # 1/3 resolved
                )
                db.session.add(comment)
                task_comments.append(comment)
    
    db.session.commit()
    print(f"  ✓ {len(task_reviewers)} reviewers assigned")
    print(f"  ✓ {len(task_comments)} comments added")
    print(f"✅ Tasks with full demo data created!")
    return tasks


def create_notifications(users, issues):
    """Create demo notifications."""
    print("\n🔔 Creating notifications...")
    notifications = []
    
    notification_types = [
        (NotificationType.TASK_ASSIGNED, 'Aufgabe zugewiesen', 'Ihnen wurde eine neue Aufgabe zugewiesen'),
        (NotificationType.TASK_STATUS_CHANGED, 'Status geändert', 'Der Status einer Aufgabe wurde geändert'),
        (NotificationType.TASK_COMMENT, 'Neuer Kommentar', 'Neuer Kommentar zu Ihrer Aufgabe'),
        (NotificationType.REVIEW_REQUESTED, 'Review angefordert', 'Ein Review wurde für Sie angefordert'),
    ]
    
    for user in users[:8]:
        for _ in range(random.randint(3, 10)):
            ntype, title, message = random.choice(notification_types)
            issue = random.choice(issues[:30]) if issues else None
            
            notification = Notification(
                user_id=user.id,
                notification_type=ntype.value,
                title=title,
                message=message,
                entity_type='issue' if issue else None,
                entity_id=issue.id if issue else None,
                is_read=random.choice([True, False, False]),  # 2/3 unread
                created_at=datetime.now() - timedelta(hours=random.randint(1, 168))
            )
            db.session.add(notification)
            notifications.append(notification)
    
    db.session.commit()
    print(f"✅ {len(notifications)} notifications created!")
    return notifications


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main function to reset database and create all demo data."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("  ProjectOps Demo Data Generator - Fresh Database Reset")
        print("="*70)
        
        # Reset database
        reset_database()
        
        # Create all demo data
        modules = create_modules()
        users = create_users()
        tenants = create_tenants(users)
        user_modules = create_user_modules(users, modules)
        teams = create_teams(users, tenants)
        entities = create_entities(users, tenants)
        categories = create_task_categories(tenants)
        presets = create_task_presets(tenants)
        projects = create_projects(users, tenants)
        sprints = create_sprints(projects)
        issues = create_issues(projects, users, sprints)
        comments = create_comments(issues, users)
        tasks = create_tasks(users, entities, categories)
        notifications = create_notifications(users, issues)
        
        # Summary
        print("\n" + "="*70)
        print("  ✅ Demo Data Creation Complete!")
        print("="*70)
        print(f"""
📊 Summary:
   ├── Modules:         {len(modules)}
   ├── Users:           {len(users)}
   ├── User Modules:    {len(user_modules)}
   ├── Tenants:         {len(tenants)}
   ├── Teams:           {len(teams)}
   ├── Entities:        {len(entities)}
   ├── Task Categories: {len(categories)}
   ├── Task Presets:    {len(presets)}
   ├── Projects:        {len(projects)}
   ├── Sprints:         {len(sprints)}
   ├── Issues:          {len(issues)}
   ├── Comments:        {len(comments)}
   ├── Tasks:           {len(tasks)}
   └── Notifications:   {len(notifications)}

🔐 Login Credentials:
   ├── admin@example.com / admin123 (Superadmin)
   ├── pentest@zap.local / ZapTest2026! (Superadmin, no rate limit)
   ├── maria.mueller@democorp.local / Demo2026! (Admin)
   └── All other users: Demo2026!

🛡️  ZAP Pentest User:
   ├── Email: pentest@zap.local
   ├── Password: ZapTest2026!
   ├── Role: admin + is_superadmin = True
   └── Rate Limit: EXEMPT (configured in extensions.py)
        """)


if __name__ == "__main__":
    main()
