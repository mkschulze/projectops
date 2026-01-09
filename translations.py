"""
ProjectOps - Translations (DE/EN)
"""

TRANSLATIONS = {
    # Navigation
    'nav_home': {'de': 'Startseite', 'en': 'Home'},
    'nav_admin': {'de': 'Administration', 'en': 'Administration'},
    'nav_users': {'de': 'Benutzer', 'en': 'Users'},
    'nav_logout': {'de': 'Abmelden', 'en': 'Logout'},
    'nav_login': {'de': 'Anmelden', 'en': 'Login'},
    'nav_dashboard': {'de': 'Dashboard', 'en': 'Dashboard'},
    'nav_calendar': {'de': 'Kalender', 'en': 'Calendar'},
    'nav_tasks': {'de': 'Aufgaben', 'en': 'Tasks'},
    'nav_entities': {'de': 'Gesellschaften', 'en': 'Entities'},
    'nav_categories': {'de': 'Kategorien', 'en': 'Categories'},
    'nav_tax_types': {'de': 'Steuerarten', 'en': 'Tax Types'},  # Legacy alias
    
    # Common
    'save': {'de': 'Speichern', 'en': 'Save'},
    'cancel': {'de': 'Abbrechen', 'en': 'Cancel'},
    'delete': {'de': 'Löschen', 'en': 'Delete'},
    'edit': {'de': 'Bearbeiten', 'en': 'Edit'},
    'create': {'de': 'Erstellen', 'en': 'Create'},
    'search': {'de': 'Suchen', 'en': 'Search'},
    'back': {'de': 'Zurück', 'en': 'Back'},
    'actions': {'de': 'Aktionen', 'en': 'Actions'},
    'yes': {'de': 'Ja', 'en': 'Yes'},
    'no': {'de': 'Nein', 'en': 'No'},
    'name': {'de': 'Name', 'en': 'Name'},
    'status': {'de': 'Status', 'en': 'Status'},
    'active': {'de': 'Aktiv', 'en': 'Active'},
    'inactive': {'de': 'Inaktiv', 'en': 'Inactive'},
    'description': {'de': 'Beschreibung', 'en': 'Description'},
    'description_placeholder': {'de': 'Optionale Beschreibung...', 'en': 'Optional description...'},
    'confirm_delete': {'de': 'Sind Sie sicher?', 'en': 'Are you sure?'},
    'code': {'de': 'Code', 'en': 'Code'},
    'code_readonly': {'de': 'Code kann nicht geändert werden', 'en': 'Code cannot be changed'},
    
    # Auth
    'email': {'de': 'E-Mail', 'en': 'Email'},
    'password': {'de': 'Passwort', 'en': 'Password'},
    'login_title': {'de': 'Anmeldung', 'en': 'Login'},
    'login_button': {'de': 'Anmelden', 'en': 'Sign In'},
    'remember_me': {'de': 'Angemeldet bleiben', 'en': 'Remember me'},
    'password_change_hint': {'de': 'Leer lassen, um das Passwort nicht zu ändern', 'en': 'Leave empty to keep current password'},
    
    # Users
    'users': {'de': 'Benutzer', 'en': 'Users'},
    'new_user': {'de': 'Neuer Benutzer', 'en': 'New User'},
    'edit_user': {'de': 'Benutzer bearbeiten', 'en': 'Edit User'},
    'role': {'de': 'Rolle', 'en': 'Role'},
    'role_admin_desc': {'de': 'Vollzugriff auf alle Funktionen', 'en': 'Full access to all features'},
    'role_manager_desc': {'de': 'Kann Aufgaben zuweisen und Berichte erstellen', 'en': 'Can assign tasks and create reports'},
    'role_reviewer_desc': {'de': 'Kann Aufgaben prüfen und abschließen', 'en': 'Can review and complete tasks'},
    'role_preparer_desc': {'de': 'Kann Aufgaben bearbeiten und einreichen', 'en': 'Can prepare and submit tasks'},
    'role_readonly_desc': {'de': 'Nur Lesezugriff', 'en': 'Read-only access'},
    
    # Entities
    'entities': {'de': 'Gesellschaften', 'en': 'Entities'},
    'entity': {'de': 'Gesellschaft', 'en': 'Entity'},
    'new_entity': {'de': 'Neue Gesellschaft', 'en': 'New Entity'},
    'edit_entity': {'de': 'Gesellschaft bearbeiten', 'en': 'Edit Entity'},
    'short_name': {'de': 'Kurzname', 'en': 'Short Name'},
    'country': {'de': 'Land', 'en': 'Country'},
    'parent_entity': {'de': 'Übergeordnete Gesellschaft', 'en': 'Parent Entity'},
    'no_parent': {'de': 'Keine', 'en': 'None'},
    'parent_entity_help': {'de': 'Optional: Für Konzernstrukturen', 'en': 'Optional: For group structures'},
    'no_entities': {'de': 'Keine Gesellschaften vorhanden', 'en': 'No entities found'},
    
    # Categories (formerly Tax Types)
    'categories': {'de': 'Kategorien', 'en': 'Categories'},
    'category': {'de': 'Kategorie', 'en': 'Category'},
    'new_category': {'de': 'Neue Kategorie', 'en': 'New Category'},
    'edit_category': {'de': 'Kategorie bearbeiten', 'en': 'Edit Category'},
    'no_categories': {'de': 'Keine Kategorien vorhanden', 'en': 'No categories found'},
    'category_color': {'de': 'Farbe', 'en': 'Color'},
    'category_icon': {'de': 'Icon', 'en': 'Icon'},
    # Legacy aliases for backward compatibility
    'tax_types': {'de': 'Steuerarten', 'en': 'Tax Types'},
    'tax_type': {'de': 'Steuerart', 'en': 'Tax Type'},
    'new_tax_type': {'de': 'Neue Steuerart', 'en': 'New Tax Type'},
    'edit_tax_type': {'de': 'Steuerart bearbeiten', 'en': 'Edit Tax Type'},
    'no_tax_types': {'de': 'Keine Steuerarten vorhanden', 'en': 'No tax types found'},
    
    # Tasks
    'tasks': {'de': 'Aufgaben', 'en': 'Tasks'},
    'task': {'de': 'Aufgabe', 'en': 'Task'},
    'new_task': {'de': 'Neue Aufgabe', 'en': 'New Task'},
    'edit_task': {'de': 'Aufgabe bearbeiten', 'en': 'Edit Task'},
    'due_date': {'de': 'Fälligkeitsdatum', 'en': 'Due Date'},
    'owner': {'de': 'Verantwortlich', 'en': 'Owner'},
    'reviewer': {'de': 'Prüfer', 'en': 'Reviewer'},
    'no_tasks': {'de': 'Keine Aufgaben vorhanden', 'en': 'No tasks found'},
    
    # Task Status
    'status_draft': {'de': 'Entwurf', 'en': 'Draft'},
    'status_submitted': {'de': 'Eingereicht', 'en': 'Submitted'},
    'status_in_review': {'de': 'In Prüfung', 'en': 'In Review'},
    'status_approved': {'de': 'Genehmigt', 'en': 'Approved'},
    'status_completed': {'de': 'Abgeschlossen', 'en': 'Completed'},
    'status_rejected': {'de': 'Zurückgewiesen', 'en': 'Rejected'},
    'status_overdue': {'de': 'Überfällig', 'en': 'Overdue'},
    'status_due_soon': {'de': 'Bald fällig', 'en': 'Due Soon'},
    
    # Archive
    'archive': {'de': 'Archiv', 'en': 'Archive'},
    'archive_task': {'de': 'Aufgabe archivieren', 'en': 'Archive Task'},
    'restore_task': {'de': 'Aufgabe wiederherstellen', 'en': 'Restore Task'},
    'archived': {'de': 'Archiviert', 'en': 'Archived'},
    'archived_on': {'de': 'Archiviert am', 'en': 'Archived on'},
    'archived_by': {'de': 'Archiviert von', 'en': 'Archived by'},
    'archive_reason': {'de': 'Archivierungsgrund', 'en': 'Archive Reason'},
    'restore': {'de': 'Wiederherstellen', 'en': 'Restore'},
    'no_archived_tasks': {'de': 'Keine archivierten Aufgaben', 'en': 'No archived tasks'},
    'permanently_delete': {'de': 'Endgültig löschen', 'en': 'Permanently Delete'},
    'permanent_delete_warning': {'de': 'Diese Aktion kann nicht rückgängig gemacht werden!', 'en': 'This action cannot be undone!'},
    'tasks_selected': {'de': 'Aufgaben ausgewählt', 'en': 'tasks selected'},
    'confirm_permanent_delete': {'de': 'Wirklich endgültig löschen?', 'en': 'Really permanently delete?'},
    
    # Workflow
    'workflow': {'de': 'Freigabe-Workflow', 'en': 'Approval Workflow'},
    'approve': {'de': 'Genehmigen', 'en': 'Approve'},
    'reject': {'de': 'Zurückweisen', 'en': 'Reject'},
    'rejected': {'de': 'Zurückgewiesen', 'en': 'Rejected'},
    'rejection_reason': {'de': 'Grund für Zurückweisung', 'en': 'Rejection Reason'},
    'submit': {'de': 'Einreichen', 'en': 'Submit'},
    'start_review': {'de': 'Prüfung starten', 'en': 'Start Review'},
    'complete': {'de': 'Abschließen', 'en': 'Complete'},
    'restart': {'de': 'Neu beginnen', 'en': 'Restart'},
    'task_completed': {'de': 'Aufgabe abgeschlossen', 'en': 'Task Completed'},
    'no_actions_available': {'de': 'Keine Aktionen verfügbar', 'en': 'No Actions Available'},
    'next_action': {'de': 'Nächste Aktion', 'en': 'Next Action'},
    'quick_info': {'de': 'Schnellinfo', 'en': 'Quick Info'},
    'created': {'de': 'Erstellt', 'en': 'Created'},
    'updated': {'de': 'Aktualisiert', 'en': 'Updated'},
    
    # Dashboard
    'dashboard': {'de': 'Dashboard', 'en': 'Dashboard'},
    'admin_dashboard': {'de': 'Admin-Dashboard', 'en': 'Admin Dashboard'},
    'welcome': {'de': 'Willkommen', 'en': 'Welcome'},
    'statistics': {'de': 'Statistiken', 'en': 'Statistics'},
    'total_users': {'de': 'Benutzer gesamt', 'en': 'Total Users'},
    'active_users': {'de': 'Aktive Benutzer', 'en': 'Active Users'},
    'total_entities': {'de': 'Gesellschaften', 'en': 'Entities'},
    'total_categories': {'de': 'Kategorien', 'en': 'Categories'},
    'total_tax_types': {'de': 'Steuerarten', 'en': 'Tax Types'},  # Legacy alias
    'total_tasks': {'de': 'Aufgaben gesamt', 'en': 'Total Tasks'},
    'tasks_overdue': {'de': 'Überfällige Aufgaben', 'en': 'Overdue Tasks'},
    'tasks_completed': {'de': 'Abgeschlossene Aufgaben', 'en': 'Completed Tasks'},
    'my_tasks': {'de': 'Meine Aufgaben', 'en': 'My Tasks'},
    
    # Calendar
    'calendar': {'de': 'Kalender', 'en': 'Calendar'},
    'year_view': {'de': 'Jahresansicht', 'en': 'Year View'},
    'month_view': {'de': 'Monatsansicht', 'en': 'Month View'},
    'week_view': {'de': 'Wochenansicht', 'en': 'Week View'},
    'calendar_week': {'de': 'KW', 'en': 'Week'},
    'calendar_prev': {'de': 'Vorheriger Monat', 'en': 'Previous Month'},
    'calendar_next': {'de': 'Nächster Monat', 'en': 'Next Month'},
    'quick_navigation': {'de': 'Schnellnavigation', 'en': 'Quick Navigation'},
    'weekday_mon': {'de': 'Mo', 'en': 'Mon'},
    'weekday_tue': {'de': 'Di', 'en': 'Tue'},
    'weekday_wed': {'de': 'Mi', 'en': 'Wed'},
    'weekday_thu': {'de': 'Do', 'en': 'Thu'},
    'weekday_fri': {'de': 'Fr', 'en': 'Fri'},
    'weekday_sat': {'de': 'Sa', 'en': 'Sat'},
    'weekday_sun': {'de': 'So', 'en': 'Sun'},
    'legend': {'de': 'Legende', 'en': 'Legend'},
    'more': {'de': 'weitere', 'en': 'more'},
    
    # Evidence
    'evidence': {'de': 'Nachweise', 'en': 'Evidence'},
    'upload_file': {'de': 'Datei hochladen', 'en': 'Upload File'},
    'add_link': {'de': 'Link hinzufügen', 'en': 'Add Link'},
    
    # Comments
    'comments': {'de': 'Kommentare', 'en': 'Comments'},
    'add_comment': {'de': 'Kommentar hinzufügen', 'en': 'Add Comment'},
    
    # Teams
    'teams': {'de': 'Teams', 'en': 'Teams'},
    'team': {'de': 'Team', 'en': 'Team'},
    'new_team': {'de': 'Neues Team', 'en': 'New Team'},
    'edit_team': {'de': 'Team bearbeiten', 'en': 'Edit Team'},
    'team_name': {'de': 'Teamname', 'en': 'Team Name'},
    'team_manager': {'de': 'Team-Manager', 'en': 'Team Manager'},
    'team_manager_hint': {'de': 'Optional: Der verantwortliche Leiter des Teams', 'en': 'Optional: The responsible team leader'},
    'team_members': {'de': 'Team-Mitglieder', 'en': 'Team Members'},
    'team_members_hint': {'de': 'Wählen Sie die Mitglieder dieses Teams aus', 'en': 'Select the members of this team'},
    'members': {'de': 'Mitglieder', 'en': 'Members'},
    'manager': {'de': 'Manager', 'en': 'Manager'},
    'no_manager': {'de': 'Kein Manager', 'en': 'No Manager'},
    'no_teams': {'de': 'Keine Teams vorhanden', 'en': 'No teams found'},
    'color': {'de': 'Farbe', 'en': 'Color'},
    'choose_color': {'de': 'Farbe wählen', 'en': 'Choose color'},
    'deactivate': {'de': 'Deaktivieren', 'en': 'Deactivate'},
    'confirm_deactivate_team': {'de': 'Team wirklich deaktivieren?', 'en': 'Really deactivate team?'},
    'current_members': {'de': 'Aktuelle Mitglieder', 'en': 'Current Members'},
    'owner_team': {'de': 'Verantwortliches Team', 'en': 'Owner Team'},
    'reviewer_team': {'de': 'Prüfer-Team', 'en': 'Reviewer Team'},
    'no_team': {'de': 'Kein Team', 'en': 'No Team'},
    'nav_teams': {'de': 'Teams', 'en': 'Teams'},
    
    # Audit Log
    'audit_log': {'de': 'Änderungsprotokoll', 'en': 'Audit Log'},
    
    # Languages
    'german': {'de': 'Deutsch', 'en': 'German'},
    'english': {'de': 'Englisch', 'en': 'English'},
    
    # Notifications
    'notifications': {'de': 'Benachrichtigungen', 'en': 'Notifications'},
    'no_notifications': {'de': 'Keine Benachrichtigungen', 'en': 'No notifications'},
    'mark_all_read': {'de': 'Alle als gelesen markieren', 'en': 'Mark all as read'},
    'view_all_notifications': {'de': 'Alle anzeigen', 'en': 'View all'},
    'notification_task_assigned': {'de': 'Aufgabe zugewiesen', 'en': 'Task assigned'},
    'notification_reviewer_added': {'de': 'Als Prüfer hinzugefügt', 'en': 'Added as reviewer'},
    'notification_status_changed': {'de': 'Status geändert', 'en': 'Status changed'},
    'notification_task_approved': {'de': 'Aufgabe genehmigt', 'en': 'Task approved'},
    'notification_task_rejected': {'de': 'Aufgabe abgelehnt', 'en': 'Task rejected'},
    'notification_comment': {'de': 'Neuer Kommentar', 'en': 'New comment'},
    'notification_review_requested': {'de': 'Review angefordert', 'en': 'Review requested'},
    'notification_due_soon': {'de': 'Bald fällig', 'en': 'Due soon'},
    'notification_overdue': {'de': 'Überfällig', 'en': 'Overdue'},
    'all_notifications': {'de': 'Alle Benachrichtigungen', 'en': 'All Notifications'},
    'unread_notifications': {'de': 'Ungelesen', 'en': 'Unread'},
    'read_notifications': {'de': 'Gelesen', 'en': 'Read'},
    
    # Errors
    'error_404_title': {'de': 'Seite nicht gefunden', 'en': 'Page not found'},
    'error_404_message': {'de': 'Die angeforderte Seite existiert nicht.', 'en': 'The requested page does not exist.'},
    'error_500_title': {'de': 'Serverfehler', 'en': 'Server Error'},
    'error_500_message': {'de': 'Ein interner Fehler ist aufgetreten.', 'en': 'An internal error occurred.'},
}


def get_translation(key, lang='de'):
    """Get translation for key in specified language"""
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get('de', key))
    return key
