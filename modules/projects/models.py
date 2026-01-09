"""
Project Management Module - Database Models

Flexible Architecture:
- IssueType: Configurable per project (Epic, Story, Task, or custom)
- IssueStatus: Configurable workflows with category mapping
- Issue: Core work item with auto-generated keys
"""
from datetime import datetime
from enum import Enum

from extensions import db


# =============================================================================
# ENUMS (for category mapping, not for restricting types)
# =============================================================================

class StatusCategory(Enum):
    """Category for status mapping (used for reports/metrics)"""
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    
    @classmethod
    def choices(cls):
        return [(c.value, c.name.replace('_', ' ').title()) for c in cls]


class ProjectMethodology(Enum):
    """Project methodology template"""
    SCRUM = 'scrum'
    KANBAN = 'kanban'
    WATERFALL = 'waterfall'
    CUSTOM = 'custom'
    
    @classmethod
    def choices(cls):
        return [(m.value, m.name.title()) for m in cls]


# =============================================================================
# METHODOLOGY CONFIGURATION
# =============================================================================

METHODOLOGY_CONFIG = {
    'scrum': {
        'name': {'de': 'Scrum', 'en': 'Scrum'},
        'description': {
            'de': 'Agile Methodik mit Sprints, User Stories und täglichen Stand-ups',
            'en': 'Agile methodology with sprints, user stories and daily stand-ups'
        },
        'features': {
            'sprints': True,
            'story_points': True,
            'velocity': True,
            'burndown': True,
            'backlog': True,
            'kanban_board': True
        },
        'terminology': {
            'de': {
                'sprint': 'Sprint',
                'sprint_plural': 'Sprints',
                'sprint_new': 'Neuer Sprint',
                'sprint_edit': 'Sprint bearbeiten',
                'backlog': 'Backlog',
                'epic': 'Epic',
                'story': 'User Story',
                'task': 'Aufgabe',
                'bug': 'Bug',
                'issue': 'Issue',
                'issue_plural': 'Issues',
                'story_points': 'Story Points',
                'velocity': 'Velocity',
                'burndown': 'Burndown',
                'board': 'Board',
                'done': 'Erledigt',
                'in_progress': 'In Bearbeitung',
                'todo': 'Zu erledigen',
                'release': 'Release'
            },
            'en': {
                'sprint': 'Sprint',
                'sprint_plural': 'Sprints',
                'sprint_new': 'New Sprint',
                'sprint_edit': 'Edit Sprint',
                'backlog': 'Backlog',
                'epic': 'Epic',
                'story': 'User Story',
                'task': 'Task',
                'bug': 'Bug',
                'issue': 'Issue',
                'issue_plural': 'Issues',
                'story_points': 'Story Points',
                'velocity': 'Velocity',
                'burndown': 'Burndown',
                'board': 'Board',
                'done': 'Done',
                'in_progress': 'In Progress',
                'todo': 'To Do',
                'release': 'Release'
            }
        }
    },
    'kanban': {
        'name': {'de': 'Kanban', 'en': 'Kanban'},
        'description': {
            'de': 'Kontinuierlicher Flow mit WIP-Limits und visueller Arbeitsverwaltung',
            'en': 'Continuous flow with WIP limits and visual work management'
        },
        'features': {
            'sprints': False,
            'story_points': False,
            'velocity': False,
            'burndown': False,
            'backlog': True,
            'kanban_board': True,
            'wip_limits': True,
            'cycle_time': True
        },
        'terminology': {
            'de': {
                'sprint': 'Zyklus',
                'sprint_plural': 'Zyklen',
                'sprint_new': 'Neuer Zyklus',
                'sprint_edit': 'Zyklus bearbeiten',
                'backlog': 'Aufgabenliste',
                'epic': 'Initiative',
                'story': 'Arbeitspaket',
                'task': 'Aufgabe',
                'bug': 'Fehler',
                'issue': 'Aufgabe',
                'issue_plural': 'Aufgaben',
                'story_points': 'Aufwand',
                'velocity': 'Durchsatz',
                'burndown': 'Fortschritt',
                'board': 'Kanban-Board',
                'done': 'Fertig',
                'in_progress': 'In Arbeit',
                'todo': 'Offen',
                'release': 'Lieferung'
            },
            'en': {
                'sprint': 'Cycle',
                'sprint_plural': 'Cycles',
                'sprint_new': 'New Cycle',
                'sprint_edit': 'Edit Cycle',
                'backlog': 'Queue',
                'epic': 'Initiative',
                'story': 'Work Item',
                'task': 'Task',
                'bug': 'Defect',
                'issue': 'Item',
                'issue_plural': 'Items',
                'story_points': 'Effort',
                'velocity': 'Throughput',
                'burndown': 'Progress',
                'board': 'Kanban Board',
                'done': 'Done',
                'in_progress': 'In Progress',
                'todo': 'Open',
                'release': 'Delivery'
            }
        }
    },
    'waterfall': {
        'name': {'de': 'Wasserfall', 'en': 'Waterfall'},
        'description': {
            'de': 'Sequenzielle Projektphasen mit Meilensteinen und Liefergegenständen',
            'en': 'Sequential project phases with milestones and deliverables'
        },
        'features': {
            'sprints': False,
            'story_points': False,
            'velocity': False,
            'burndown': False,
            'backlog': False,
            'kanban_board': True,
            'phases': True,
            'milestones': True,
            'gantt': True
        },
        'terminology': {
            'de': {
                'sprint': 'Phase',
                'sprint_plural': 'Phasen',
                'sprint_new': 'Neue Phase',
                'sprint_edit': 'Phase bearbeiten',
                'backlog': 'Anforderungsliste',
                'epic': 'Arbeitspaket',
                'story': 'Anforderung',
                'task': 'Aktivität',
                'bug': 'Abweichung',
                'issue': 'Aktivität',
                'issue_plural': 'Aktivitäten',
                'story_points': 'Aufwand (PT)',
                'velocity': 'Fortschritt',
                'burndown': 'Phasenfortschritt',
                'board': 'Übersicht',
                'done': 'Abgeschlossen',
                'in_progress': 'In Umsetzung',
                'todo': 'Geplant',
                'release': 'Meilenstein'
            },
            'en': {
                'sprint': 'Phase',
                'sprint_plural': 'Phases',
                'sprint_new': 'New Phase',
                'sprint_edit': 'Edit Phase',
                'backlog': 'Requirements',
                'epic': 'Work Package',
                'story': 'Requirement',
                'task': 'Activity',
                'bug': 'Deviation',
                'issue': 'Activity',
                'issue_plural': 'Activities',
                'story_points': 'Effort (PD)',
                'velocity': 'Progress',
                'burndown': 'Phase Progress',
                'board': 'Overview',
                'done': 'Completed',
                'in_progress': 'In Progress',
                'todo': 'Planned',
                'release': 'Milestone'
            }
        }
    },
    'custom': {
        'name': {'de': 'Benutzerdefiniert', 'en': 'Custom'},
        'description': {
            'de': 'Eigene Methodik mit anpassbarer Terminologie',
            'en': 'Custom methodology with customizable terminology'
        },
        'features': {
            'sprints': True,
            'story_points': True,
            'velocity': True,
            'burndown': True,
            'backlog': True,
            'kanban_board': True
        },
        'terminology': {
            'de': {
                'sprint': 'Iteration',
                'sprint_plural': 'Iterationen',
                'sprint_new': 'Neue Iteration',
                'sprint_edit': 'Iteration bearbeiten',
                'backlog': 'Aufgabenliste',
                'epic': 'Thema',
                'story': 'Anforderung',
                'task': 'Aufgabe',
                'bug': 'Fehler',
                'issue': 'Eintrag',
                'issue_plural': 'Einträge',
                'story_points': 'Punkte',
                'velocity': 'Geschwindigkeit',
                'burndown': 'Fortschritt',
                'board': 'Board',
                'done': 'Erledigt',
                'in_progress': 'In Bearbeitung',
                'todo': 'Offen',
                'release': 'Version'
            },
            'en': {
                'sprint': 'Iteration',
                'sprint_plural': 'Iterations',
                'sprint_new': 'New Iteration',
                'sprint_edit': 'Edit Iteration',
                'backlog': 'Work Queue',
                'epic': 'Theme',
                'story': 'Requirement',
                'task': 'Task',
                'bug': 'Issue',
                'issue': 'Item',
                'issue_plural': 'Items',
                'story_points': 'Points',
                'velocity': 'Velocity',
                'burndown': 'Progress',
                'board': 'Board',
                'done': 'Done',
                'in_progress': 'In Progress',
                'todo': 'Open',
                'release': 'Version'
            }
        }
    }
}


class ProjectRole(Enum):
    """Project member role enumeration"""
    ADMIN = 'admin'      # Full project control
    LEAD = 'lead'        # Can manage issues, sprints
    MEMBER = 'member'    # Can work on issues
    VIEWER = 'viewer'    # Read-only access
    
    @classmethod
    def choices(cls):
        return [(role.value, role.name.title()) for role in cls]


class Project(db.Model):
    """Project model for grouping issues"""
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    key = db.Column(db.String(10), nullable=False, index=True)  # TAX, AUD, HR (unique per tenant)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))  # English name (optional)
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)  # English description (optional)
    
    # Project lead
    lead_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Methodology & Configuration
    methodology = db.Column(db.String(20), default='scrum')  # scrum, kanban, waterfall, custom
    
    # Terminology overrides (JSON) - allows custom labels per project
    # Example: {"epic": "Initiative", "story": "Requirement", "sprint": "Iteration"}
    terminology = db.Column(db.JSON, default=dict)
    
    # Estimation scale configuration
    # Options: 'fibonacci', 'tshirt', 'linear', 'custom'
    estimation_scale = db.Column(db.String(20), default='fibonacci')
    # Custom scale values (JSON array) - used when estimation_scale='custom'
    estimation_values = db.Column(db.JSON, default=list)
    
    # Categorization
    category = db.Column(db.String(50))  # e.g., 'tax', 'audit', 'consulting'
    icon = db.Column(db.String(50), default='bi-folder')  # Bootstrap icon
    color = db.Column(db.String(7), default='#4A90D9')  # Hex color for badges
    
    # Status
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    
    # Issue counter for auto-incrementing issue keys
    issue_counter = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    lead = db.relationship('User', foreign_keys=[lead_id], backref='led_projects')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    members = db.relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan')
    issue_types = db.relationship('IssueType', back_populates='project', cascade='all, delete-orphan')
    issue_statuses = db.relationship('IssueStatus', back_populates='project', cascade='all, delete-orphan')
    issues = db.relationship('Issue', back_populates='project', cascade='all, delete-orphan')
    
    def get_name(self, lang='de'):
        """Get localized name"""
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name
    
    def get_description(self, lang='de'):
        """Get localized description"""
        if lang == 'en' and self.description_en:
            return self.description_en
        return self.description or ''
    
    def get_next_issue_key(self):
        """Generate next issue key (e.g., TAX-42)"""
        self.issue_counter += 1
        return f"{self.key}-{self.issue_counter}"
    
    def get_methodology_config(self):
        """Get the methodology configuration for this project"""
        return METHODOLOGY_CONFIG.get(self.methodology or 'scrum', METHODOLOGY_CONFIG['scrum'])
    
    def get_term(self, key, lang='de'):
        """
        Get terminology for a specific key, with fallback chain:
        1. Project-specific override (self.terminology)
        2. Methodology default (METHODOLOGY_CONFIG)
        3. Scrum default as ultimate fallback
        """
        # First check project-specific overrides
        if self.terminology and key in self.terminology:
            term = self.terminology[key]
            # Handle both simple string and {de:..., en:...} format
            if isinstance(term, dict):
                return term.get(lang, term.get('de', key))
            return term
        
        # Then check methodology default
        config = self.get_methodology_config()
        terms = config.get('terminology', {}).get(lang, {})
        if key in terms:
            return terms[key]
        
        # Ultimate fallback to scrum terminology
        return METHODOLOGY_CONFIG['scrum']['terminology'].get(lang, {}).get(key, key)
    
    def get_article(self, key, case='nom'):
        """
        Get the correct German article for a terminology key.
        case: 'nom' (nominative: ein/eine), 'dat' (dative: einem/einer)
        
        Sprint is masculine → ein/einem
        Iteration is feminine → eine/einer
        """
        term = self.get_term(key, 'de').lower()
        
        # Feminine terms (die)
        feminine_terms = ['iteration', 'phase', 'aufgabe', 'story']
        
        if any(f in term for f in feminine_terms):
            return 'eine' if case == 'nom' else 'einer'
        else:
            # Default to masculine (der) - Sprint, Meilenstein, etc.
            return 'ein' if case == 'nom' else 'einem'
    
    def has_feature(self, feature):
        """Check if a feature is enabled for this project's methodology"""
        config = self.get_methodology_config()
        return config.get('features', {}).get(feature, False)
    
    def get_methodology_name(self, lang='de'):
        """Get localized methodology name"""
        config = self.get_methodology_config()
        return config.get('name', {}).get(lang, self.methodology)
    
    def is_member(self, user):
        """Check if user is a member of this project"""
        if user.role == 'admin':
            return True
        return any(m.user_id == user.id for m in self.members)
    
    def get_member_role(self, user):
        """Get user's role in this project"""
        if user.role == 'admin':
            return 'admin'
        for m in self.members:
            if m.user_id == user.id:
                return m.role
        return None
    
    def can_user_edit(self, user):
        """Check if user can edit project settings"""
        role = self.get_member_role(user)
        return role in ['admin', 'lead']
    
    def is_admin(self, user):
        """Check if user is admin/lead for this project"""
        role = self.get_member_role(user)
        return role in ['admin', 'lead']
    
    def can_user_manage_issues(self, user):
        """Check if user can create/edit issues"""
        role = self.get_member_role(user)
        return role in ['admin', 'lead', 'member']
    
    def get_default_issue_type(self):
        """Get the default issue type for this project"""
        return IssueType.query.filter_by(
            project_id=self.id,
            is_default=True
        ).first() or self.issue_types[0] if self.issue_types else None
    
    def get_initial_status(self):
        """Get the initial status for new issues"""
        return IssueStatus.query.filter_by(
            project_id=self.id,
            is_initial=True
        ).first() or self.issue_statuses[0] if self.issue_statuses else None
    
    def get_estimation_scale_config(self):
        """Get estimation scale configuration with labels and story point mappings"""
        scales = {
            'fibonacci': {
                'name': {'de': 'Fibonacci', 'en': 'Fibonacci'},
                'hint': {
                    'de': 'Story Points messen relativen Aufwand (Komplexität + Unsicherheit + Umfang), nicht Zeitdauer.',
                    'en': 'Story points measure relative effort (complexity + uncertainty + scope), not time.'
                },
                'values': [
                    {'label': '1', 'points': 1, 'description': {'de': 'Trivial – wenige Stunden, klar definiert', 'en': 'Trivial – few hours, well defined'}},
                    {'label': '2', 'points': 2, 'description': {'de': 'Einfach – überschaubar, kaum Unbekannte', 'en': 'Simple – straightforward, few unknowns'}},
                    {'label': '3', 'points': 3, 'description': {'de': 'Klein – typische Aufgabe (Referenzgröße)', 'en': 'Small – typical task (reference size)'}},
                    {'label': '5', 'points': 5, 'description': {'de': 'Mittel – mehrere Aspekte, etwas Komplexität', 'en': 'Medium – several aspects, some complexity'}},
                    {'label': '8', 'points': 8, 'description': {'de': 'Groß – komplex, Abstimmung nötig', 'en': 'Large – complex, coordination needed'}},
                    {'label': '13', 'points': 13, 'description': {'de': 'Sehr groß – viele Unbekannte, ggf. aufteilen', 'en': 'Very large – many unknowns, consider splitting'}},
                    {'label': '21', 'points': 21, 'description': {'de': 'Riesig – zu groß, muss aufgeteilt werden!', 'en': 'Huge – too large, must be split!'}},
                ]
            },
            'tshirt': {
                'name': {'de': 'T-Shirt Größen', 'en': 'T-Shirt Sizes'},
                'hint': {
                    'de': 'Intuitive Größeneinteilung für schnelle, grobe Schätzungen ohne exakte Zahlen.',
                    'en': 'Intuitive sizing for quick, rough estimates without exact numbers.'
                },
                'values': [
                    {'label': 'XS', 'points': 1, 'description': {'de': 'Winzig – schnell erledigt', 'en': 'Tiny – done quickly'}},
                    {'label': 'S', 'points': 2, 'description': {'de': 'Klein – überschaubar', 'en': 'Small – manageable'}},
                    {'label': 'M', 'points': 3, 'description': {'de': 'Mittel – Standardaufgabe', 'en': 'Medium – standard task'}},
                    {'label': 'L', 'points': 5, 'description': {'de': 'Groß – mehr Aufwand', 'en': 'Large – more effort'}},
                    {'label': 'XL', 'points': 8, 'description': {'de': 'Sehr groß – komplex', 'en': 'Extra large – complex'}},
                    {'label': 'XXL', 'points': 13, 'description': {'de': 'Riesig – aufteilen empfohlen', 'en': 'Huge – splitting recommended'}},
                ]
            },
            'linear': {
                'name': {'de': 'Linear (1-10)', 'en': 'Linear (1-10)'},
                'hint': {
                    'de': 'Einfache Skala von 1-10 für Teams, die mit gleichmäßigen Abstufungen arbeiten möchten.',
                    'en': 'Simple 1-10 scale for teams preferring uniform increments.'
                },
                'values': [
                    {'label': str(i), 'points': i, 'description': {'de': f'Aufwand {i}/10', 'en': f'Effort {i}/10'}}
                    for i in range(1, 11)
                ]
            },
            'persondays': {
                'name': {'de': 'Personentage (PT)', 'en': 'Person Days (PD)'},
                'hint': {
                    'de': 'Direkte Aufwandsschätzung in Personentagen – ideal für klassische Projektplanung.',
                    'en': 'Direct effort estimation in person days – ideal for traditional project planning.'
                },
                'values': [
                    {'label': '0.5', 'points': 0.5, 'description': {'de': '½ Tag', 'en': '½ day'}},
                    {'label': '1', 'points': 1, 'description': {'de': '1 Tag', 'en': '1 day'}},
                    {'label': '2', 'points': 2, 'description': {'de': '2 Tage', 'en': '2 days'}},
                    {'label': '3', 'points': 3, 'description': {'de': '3 Tage', 'en': '3 days'}},
                    {'label': '5', 'points': 5, 'description': {'de': '1 Woche', 'en': '1 week'}},
                    {'label': '10', 'points': 10, 'description': {'de': '2 Wochen', 'en': '2 weeks'}},
                    {'label': '20', 'points': 20, 'description': {'de': '1 Monat', 'en': '1 month'}},
                ]
            },
            'custom': {
                'name': {'de': 'Benutzerdefiniert', 'en': 'Custom'},
                'hint': {
                    'de': 'Eigene Werte und Beschreibungen passend zu Ihrem Team.',
                    'en': 'Custom values and descriptions tailored to your team.'
                },
                'values': self.estimation_values or []
            }
        }
        
        # Default scale based on methodology
        default_scale = 'fibonacci'
        if self.methodology == 'waterfall':
            default_scale = 'persondays'
        elif self.methodology == 'kanban':
            default_scale = 'tshirt'
        
        return scales.get(self.estimation_scale or default_scale, scales['fibonacci'])
    
    def get_estimation_values(self):
        """Get list of estimation values for this project"""
        config = self.get_estimation_scale_config()
        return config.get('values', [])
    
    @property
    def member_count(self):
        """Get number of members"""
        return len(self.members)
    
    def __repr__(self):
        return f'<Project {self.key}: {self.name}>'


class ProjectMember(db.Model):
    """Project membership with role"""
    __tablename__ = 'project_member'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, lead, member, viewer
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', foreign_keys=[user_id], backref='project_memberships')
    added_by = db.relationship('User', foreign_keys=[added_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='unique_project_member'),
    )
    
    def get_role_display(self, lang='de'):
        """Get localized role display name"""
        roles_de = {
            'admin': 'Administrator',
            'lead': 'Projektleiter',
            'member': 'Mitglied',
            'viewer': 'Beobachter'
        }
        roles_en = {
            'admin': 'Administrator',
            'lead': 'Project Lead',
            'member': 'Member',
            'viewer': 'Viewer'
        }
        roles = roles_de if lang == 'de' else roles_en
        return roles.get(self.role, self.role)
    
    def __repr__(self):
        return f'<ProjectMember {self.user_id} in {self.project_id} as {self.role}>'


# =============================================================================
# CONFIGURABLE ISSUE TYPES (per project)
# =============================================================================

class IssueType(db.Model):
    """Configurable issue type per project (Epic, Story, Task, etc.)"""
    __tablename__ = 'issue_type'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # Type definition
    name = db.Column(db.String(50), nullable=False)  # "Epic", "Story", "Task"
    name_en = db.Column(db.String(50))  # English name
    description = db.Column(db.String(200))
    
    # Visual
    icon = db.Column(db.String(50), default='bi-card-checklist')  # Bootstrap icon
    color = db.Column(db.String(7), default='#4A90D9')  # Hex color
    
    # Hierarchy (0 = top level like Epic, 1 = Story, 2 = Task, 3 = Sub-Task)
    hierarchy_level = db.Column(db.Integer, default=1)
    can_have_children = db.Column(db.Boolean, default=True)
    allowed_child_types = db.Column(db.JSON, default=list)  # List of type IDs that can be children
    
    # Behavior
    is_default = db.Column(db.Boolean, default=False)  # Default type for quick create
    is_subtask = db.Column(db.Boolean, default=False)  # Sub-task type
    
    # Ordering
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='issue_types')
    issues = db.relationship('Issue', back_populates='issue_type')
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'name', name='unique_issue_type_per_project'),
    )
    
    def get_name(self, lang='de'):
        """Get localized name"""
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name
    
    def __repr__(self):
        return f'<IssueType {self.name} in Project {self.project_id}>'


# =============================================================================
# CONFIGURABLE WORKFLOW STATUS (per project)
# =============================================================================

class IssueStatus(db.Model):
    """Configurable workflow status per project"""
    __tablename__ = 'issue_status'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # Status definition
    name = db.Column(db.String(50), nullable=False)  # "Open", "In Progress", "Done"
    name_en = db.Column(db.String(50))  # English name
    description = db.Column(db.String(200))
    
    # Category mapping for reports/metrics
    category = db.Column(db.String(20), default='todo')  # todo, in_progress, done
    
    # Visual
    icon = db.Column(db.String(50))  # Optional icon
    color = db.Column(db.String(7), default='#75787B')  # Hex color
    
    # Workflow
    is_initial = db.Column(db.Boolean, default=False)  # Starting status for new issues
    is_final = db.Column(db.Boolean, default=False)  # End status (Done, Cancelled)
    allowed_transitions = db.Column(db.JSON, default=list)  # List of status IDs that can transition to
    
    # Ordering (for board columns)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='issue_statuses')
    issues = db.relationship('Issue', back_populates='status')
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'name', name='unique_status_per_project'),
    )
    
    def get_name(self, lang='de'):
        """Get localized name"""
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name
    
    def can_transition_to(self, target_status_id):
        """Check if transition to target status is allowed"""
        if not self.allowed_transitions:
            return True  # No restrictions = all transitions allowed
        return target_status_id in self.allowed_transitions
    
    def __repr__(self):
        return f'<IssueStatus {self.name} ({self.category}) in Project {self.project_id}>'


# =============================================================================
# ISSUE MODEL (Core work item)
# =============================================================================

class Issue(db.Model):
    """Issue/work item - the core entity for project work"""
    __tablename__ = 'issue'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Auto-generated key (TAX-1, TAX-2, etc.)
    key = db.Column(db.String(20), nullable=False, index=True)  # Unique per tenant
    
    # Issue type (Epic, Story, Task, etc.)
    type_id = db.Column(db.Integer, db.ForeignKey('issue_type.id'), nullable=False)
    
    # Workflow status
    status_id = db.Column(db.Integer, db.ForeignKey('issue_status.id'), nullable=False)
    
    # Content
    summary = db.Column(db.String(500), nullable=False)  # Title/summary
    description = db.Column(db.Text)  # Markdown description
    
    # Hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('issue.id'), index=True)  # Parent issue (for sub-tasks)
    
    # Assignment
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Priority (1=Highest, 2=High, 3=Medium, 4=Low, 5=Lowest)
    priority = db.Column(db.Integer, default=3)
    
    # Time tracking
    original_estimate = db.Column(db.Integer)  # in minutes
    time_spent = db.Column(db.Integer, default=0)  # in minutes
    remaining_estimate = db.Column(db.Integer)  # in minutes
    
    # Dates
    due_date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    resolution_date = db.Column(db.DateTime)  # When moved to final status
    
    # Sprint/Iteration (optional, for Scrum)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id'), index=True)
    
    # Story points (for Scrum estimation)
    story_points = db.Column(db.Float)
    
    # Labels (JSON array of strings)
    labels = db.Column(db.JSON, default=list)
    
    # Custom fields (JSON object for flexible data)
    custom_fields = db.Column(db.JSON, default=dict)
    
    # Board position (for Kanban ordering within a column)
    board_position = db.Column(db.Integer, default=0)
    
    # Backlog position (for prioritization)
    backlog_position = db.Column(db.Integer, default=0)
    
    # Archival
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='issues')
    issue_type = db.relationship('IssueType', back_populates='issues')
    status = db.relationship('IssueStatus', back_populates='issues')
    parent = db.relationship('Issue', remote_side=[id], backref='children')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_issues')
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_issues')
    reviewers = db.relationship('IssueReviewer', back_populates='issue', lazy='dynamic', cascade='all, delete-orphan')
    # sprint relationship will be added when Sprint model is created
    
    def get_approval_count(self):
        """Get approval count tuple (approved, total)"""
        total = self.reviewers.count()
        approved = self.reviewers.filter_by(has_approved=True).count()
        return (approved, total)
    
    def get_approval_status(self):
        """Get detailed approval status"""
        reviewers_list = self.reviewers.all()
        total = len(reviewers_list)
        approved = [r for r in reviewers_list if r.has_approved]
        rejected = [r for r in reviewers_list if r.has_rejected]
        pending = [r for r in reviewers_list if not r.has_approved and not r.has_rejected]
        
        return {
            'total': total,
            'approved_count': len(approved),
            'rejected_count': len(rejected),
            'pending_count': len(pending),
            'is_complete': len(approved) == total and total > 0,
            'is_rejected': len(rejected) > 0,
            'progress_percent': int((len(approved) / total * 100)) if total > 0 else 0,
            'pending_reviewers': [r.user for r in pending],
            'approved_reviewers': [r.user for r in approved],
            'rejected_reviewers': [r.user for r in rejected]
        }
    
    def requires_review(self):
        """Check if this issue requires review (has reviewers assigned)"""
        return self.reviewers.count() > 0
    
    def can_user_review(self, user):
        """Check if user can review this issue"""
        if not self.status:
            return False, "No status set"
        
        # Check if user is a reviewer
        reviewer = self.reviewers.filter_by(user_id=user.id).first()
        if not reviewer:
            return False, "You are not a reviewer for this issue"
        
        if reviewer.has_approved:
            return False, "You have already approved this issue"
        if reviewer.has_rejected:
            return False, "You have already rejected this issue"
        
        return True, "Can review"
    
    def get_priority_display(self, lang='de'):
        """Get priority display name"""
        priorities = {
            1: ('Höchste', 'Highest'),
            2: ('Hoch', 'High'),
            3: ('Mittel', 'Medium'),
            4: ('Niedrig', 'Low'),
            5: ('Niedrigste', 'Lowest')
        }
        idx = 0 if lang == 'de' else 1
        return priorities.get(self.priority, ('Mittel', 'Medium'))[idx]
    
    def get_priority_icon(self):
        """Get priority icon class"""
        icons = {
            1: 'bi-chevron-double-up text-danger',
            2: 'bi-chevron-up text-danger',
            3: 'bi-dash text-warning',
            4: 'bi-chevron-down text-success',
            5: 'bi-chevron-double-down text-success'
        }
        return icons.get(self.priority, 'bi-dash text-warning')
    
    def format_time(self, minutes):
        """Format minutes as readable time (e.g., '2h 30m')"""
        if not minutes:
            return '-'
        hours = minutes // 60
        mins = minutes % 60
        if hours and mins:
            return f'{hours}h {mins}m'
        elif hours:
            return f'{hours}h'
        else:
            return f'{mins}m'
    
    @property
    def time_spent_display(self):
        return self.format_time(self.time_spent)
    
    @property
    def original_estimate_display(self):
        return self.format_time(self.original_estimate)
    
    @property
    def remaining_estimate_display(self):
        return self.format_time(self.remaining_estimate)
    
    @property
    def progress_percent(self):
        """Calculate progress based on time tracking"""
        if not self.original_estimate:
            return 0
        return min(100, int((self.time_spent / self.original_estimate) * 100))
    
    @property
    def is_overdue(self):
        """Check if issue is past due date and not done"""
        if not self.due_date or not self.status:
            return False
        if self.status.is_final:
            return False
        return self.due_date < datetime.utcnow().date()
    
    def __repr__(self):
        return f'<Issue {self.key}: {self.summary[:30]}>'


# =============================================================================
# ISSUE COMMENT MODEL
# =============================================================================

class IssueComment(db.Model):
    """Comments on issues"""
    __tablename__ = 'issue_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Content (Markdown supported)
    content = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issue = db.relationship('Issue', backref=db.backref('comments', lazy='dynamic', order_by='IssueComment.created_at.desc()'))
    author = db.relationship('User', backref='issue_comments')
    
    def __repr__(self):
        return f'<IssueComment {self.id} on {self.issue_id} by User {self.author_id}>'


# =============================================================================
# ISSUE ATTACHMENT MODEL
# =============================================================================

class IssueAttachment(db.Model):
    """File attachments on issues"""
    __tablename__ = 'issue_attachment'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # File info
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    filepath = db.Column(db.String(500), nullable=False)  # Server path
    filesize = db.Column(db.Integer)  # Size in bytes
    mimetype = db.Column(db.String(100))  # MIME type
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issue = db.relationship('Issue', backref=db.backref('attachments', lazy='dynamic', order_by='IssueAttachment.uploaded_at.desc()'))
    uploaded_by = db.relationship('User', backref='uploaded_attachments')
    
    @property
    def filesize_display(self):
        """Format file size for display"""
        if not self.filesize:
            return '-'
        if self.filesize < 1024:
            return f'{self.filesize} B'
        elif self.filesize < 1024 * 1024:
            return f'{self.filesize / 1024:.1f} KB'
        else:
            return f'{self.filesize / (1024 * 1024):.1f} MB'
    
    @property
    def is_image(self):
        """Check if attachment is an image"""
        return self.mimetype and self.mimetype.startswith('image/')
    
    @property
    def icon(self):
        """Get icon class based on file type"""
        if not self.mimetype:
            return 'bi-file-earmark'
        if self.mimetype.startswith('image/'):
            return 'bi-file-earmark-image'
        elif self.mimetype.startswith('video/'):
            return 'bi-file-earmark-play'
        elif self.mimetype == 'application/pdf':
            return 'bi-file-earmark-pdf'
        elif 'spreadsheet' in self.mimetype or 'excel' in self.mimetype:
            return 'bi-file-earmark-excel'
        elif 'document' in self.mimetype or 'word' in self.mimetype:
            return 'bi-file-earmark-word'
        elif 'zip' in self.mimetype or 'compressed' in self.mimetype:
            return 'bi-file-earmark-zip'
        elif self.mimetype.startswith('text/'):
            return 'bi-file-earmark-text'
        return 'bi-file-earmark'
    
    def __repr__(self):
        return f'<IssueAttachment {self.filename} on Issue {self.issue_id}>'


# =============================================================================
# ISSUE REVIEWER MODEL - Multi-Stage Approval Workflow
# =============================================================================

class IssueReviewer(db.Model):
    """Association table for Issue-Reviewer many-to-many with approval tracking"""
    __tablename__ = 'issue_reviewer'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    order = db.Column(db.Integer, default=1)  # Order in approval chain
    
    # Approval tracking
    has_approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    approval_note = db.Column(db.Text)
    
    # Rejection tracking
    has_rejected = db.Column(db.Boolean, default=False)
    rejected_at = db.Column(db.DateTime)
    rejection_note = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issue = db.relationship('Issue', back_populates='reviewers')
    user = db.relationship('User', backref='issue_reviewer_assignments')
    
    __table_args__ = (
        db.UniqueConstraint('issue_id', 'user_id', name='unique_issue_reviewer'),
    )
    
    def approve(self, note=None):
        """Mark this reviewer's approval"""
        self.has_approved = True
        self.approved_at = datetime.utcnow()
        self.approval_note = note
        self.has_rejected = False
        self.rejected_at = None
        self.rejection_note = None
    
    def reject(self, note=None):
        """Mark this reviewer's rejection"""
        self.has_rejected = True
        self.rejected_at = datetime.utcnow()
        self.rejection_note = note
        self.has_approved = False
        self.approved_at = None
        self.approval_note = None
    
    def reset(self):
        """Reset approval/rejection status"""
        self.has_approved = False
        self.approved_at = None
        self.approval_note = None
        self.has_rejected = False
        self.rejected_at = None
        self.rejection_note = None
    
    @property
    def status_display(self):
        """Get status display"""
        if self.has_approved:
            return 'approved'
        elif self.has_rejected:
            return 'rejected'
        return 'pending'
    
    def __repr__(self):
        return f'<IssueReviewer User {self.user_id} on Issue {self.issue_id}>'


# =============================================================================
# ISSUE ACTIVITY MODEL (Change tracking)
# =============================================================================

class IssueActivity(db.Model):
    """Activity log for tracking all changes to issues"""
    __tablename__ = 'issue_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Activity type: status_change, assignee_change, comment, attachment, link, worklog, 
    #                field_update, created, reviewer_added, approved, rejected
    activity_type = db.Column(db.String(50), nullable=False)
    
    # Field that was changed (for field_update type)
    field_name = db.Column(db.String(50))
    
    # Old and new values (JSON for complex values)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    
    # Optional details/message
    details = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    issue = db.relationship('Issue', backref=db.backref('activities', lazy='dynamic', 
                           order_by='IssueActivity.created_at.desc()'))
    user = db.relationship('User', backref='issue_activities')
    
    def get_activity_icon(self):
        """Get icon for activity type"""
        icons = {
            'created': 'bi-plus-circle text-success',
            'status_change': 'bi-arrow-right-circle text-primary',
            'assignee_change': 'bi-person text-info',
            'comment': 'bi-chat-dots text-secondary',
            'attachment': 'bi-paperclip text-warning',
            'link': 'bi-link-45deg text-muted',
            'worklog': 'bi-clock text-info',
            'field_update': 'bi-pencil text-muted',
            'reviewer_added': 'bi-person-plus text-primary',
            'reviewer_removed': 'bi-person-dash text-warning',
            'approved': 'bi-check-circle text-success',
            'rejected': 'bi-x-circle text-danger',
            'priority_change': 'bi-exclamation-circle text-warning',
            'sprint_change': 'bi-calendar-event text-info',
        }
        return icons.get(self.activity_type, 'bi-circle text-muted')
    
    def get_activity_text(self, lang='de'):
        """Get human-readable activity text"""
        texts = {
            'created': ('hat das Issue erstellt', 'created this issue'),
            'status_change': ('hat den Status geändert', 'changed status'),
            'assignee_change': ('hat die Zuweisung geändert', 'changed assignee'),
            'comment': ('hat kommentiert', 'commented'),
            'attachment': ('hat eine Datei angehängt', 'attached a file'),
            'link': ('hat eine Verknüpfung hinzugefügt', 'added a link'),
            'worklog': ('hat Zeit protokolliert', 'logged time'),
            'field_update': ('hat ein Feld aktualisiert', 'updated a field'),
            'reviewer_added': ('hat einen Reviewer hinzugefügt', 'added a reviewer'),
            'reviewer_removed': ('hat einen Reviewer entfernt', 'removed a reviewer'),
            'approved': ('hat genehmigt', 'approved'),
            'rejected': ('hat abgelehnt', 'rejected'),
            'priority_change': ('hat die Priorität geändert', 'changed priority'),
            'sprint_change': ('hat den Sprint geändert', 'changed sprint'),
        }
        idx = 0 if lang == 'de' else 1
        return texts.get(self.activity_type, ('hat eine Änderung vorgenommen', 'made a change'))[idx]
    
    def __repr__(self):
        return f'<IssueActivity {self.activity_type} on Issue {self.issue_id} by User {self.user_id}>'


# =============================================================================
# ISSUE LINK MODEL
# =============================================================================

class IssueLinkType(Enum):
    """Types of issue links"""
    BLOCKS = 'blocks'           # This issue blocks another
    IS_BLOCKED_BY = 'is_blocked_by'  # This issue is blocked by another
    RELATES_TO = 'relates_to'   # Related issues
    DUPLICATES = 'duplicates'   # This duplicates another
    IS_DUPLICATED_BY = 'is_duplicated_by'  # Another duplicates this
    CAUSES = 'causes'           # This issue causes another
    IS_CAUSED_BY = 'is_caused_by'  # This is caused by another
    
    @classmethod
    def choices(cls):
        return [(lt.value, lt.name.replace('_', ' ').title()) for lt in cls]
    
    @classmethod
    def get_inverse(cls, link_type):
        """Get the inverse link type"""
        inverses = {
            'blocks': 'is_blocked_by',
            'is_blocked_by': 'blocks',
            'duplicates': 'is_duplicated_by',
            'is_duplicated_by': 'duplicates',
            'causes': 'is_caused_by',
            'is_caused_by': 'causes',
            'relates_to': 'relates_to',  # Symmetric
        }
        return inverses.get(link_type, link_type)


class IssueLink(db.Model):
    """Links between issues"""
    __tablename__ = 'issue_link'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Source issue (the "from" side of the link)
    source_issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    
    # Target issue (the "to" side of the link)
    target_issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    
    # Link type
    link_type = db.Column(db.String(50), nullable=False)  # blocks, is_blocked_by, relates_to, duplicates
    
    # Who created the link
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    source_issue = db.relationship('Issue', foreign_keys=[source_issue_id], 
                                    backref=db.backref('outward_links', lazy='dynamic'))
    target_issue = db.relationship('Issue', foreign_keys=[target_issue_id], 
                                    backref=db.backref('inward_links', lazy='dynamic'))
    created_by = db.relationship('User', backref='created_issue_links')
    
    def get_link_display(self, lang='de'):
        """Get display text for link type"""
        labels = {
            'blocks': ('blockiert', 'blocks'),
            'is_blocked_by': ('wird blockiert von', 'is blocked by'),
            'relates_to': ('bezieht sich auf', 'relates to'),
            'duplicates': ('dupliziert', 'duplicates'),
            'is_duplicated_by': ('wird dupliziert von', 'is duplicated by'),
            'causes': ('verursacht', 'causes'),
            'is_caused_by': ('wird verursacht von', 'is caused by'),
        }
        idx = 0 if lang == 'de' else 1
        return labels.get(self.link_type, (self.link_type, self.link_type))[idx]
    
    def __repr__(self):
        return f'<IssueLink {self.source_issue_id} {self.link_type} {self.target_issue_id}>'


# =============================================================================
# WORKLOG MODEL (Time tracking)
# =============================================================================

class Worklog(db.Model):
    """Time tracking entries for issues"""
    __tablename__ = 'worklog'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Time logged (in minutes)
    time_spent = db.Column(db.Integer, nullable=False)
    
    # When the work was done
    work_date = db.Column(db.Date, default=datetime.utcnow)
    
    # Description of work done
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issue = db.relationship('Issue', backref=db.backref('worklogs', lazy='dynamic', order_by='Worklog.work_date.desc()'))
    author = db.relationship('User', backref='worklogs')
    
    @property
    def time_spent_display(self):
        """Format time spent for display"""
        if not self.time_spent:
            return '-'
        hours = self.time_spent // 60
        mins = self.time_spent % 60
        if hours and mins:
            return f'{hours}h {mins}m'
        elif hours:
            return f'{hours}h'
        else:
            return f'{mins}m'
    
    def __repr__(self):
        return f'<Worklog {self.time_spent}m on Issue {self.issue_id} by User {self.author_id}>'


# =============================================================================
# SPRINT MODEL (for Scrum projects)
# =============================================================================

class Sprint(db.Model):
    """Sprint/Iteration for time-boxed work (Scrum)"""
    __tablename__ = 'sprint'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Sprint info
    name = db.Column(db.String(100), nullable=False)  # "Sprint 1", "Sprint 2"
    goal = db.Column(db.Text)  # Sprint goal
    
    # Dates
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # State
    state = db.Column(db.String(20), default='future')  # future, active, closed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    project = db.relationship('Project', backref='sprints')
    issues = db.relationship('Issue', backref='sprint', foreign_keys=[Issue.sprint_id])
    
    @property
    def is_active(self):
        return self.state == 'active'
    
    @property
    def total_points(self):
        """Sum of story points in sprint"""
        return sum(i.story_points or 0 for i in self.issues)
    
    @property
    def completed_points(self):
        """Sum of story points for done issues"""
        return sum(
            i.story_points or 0 
            for i in self.issues 
            if i.status and i.status.is_final
        )
    
    def __repr__(self):
        return f'<Sprint {self.name} ({self.state})>'


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_default_issue_types(project):
    """Create default issue types for a new project based on methodology"""
    
    scrum_types = [
        {'name': 'Epic', 'name_en': 'Epic', 'icon': 'bi-lightning-charge', 'color': '#6E2B62', 
         'hierarchy_level': 0, 'can_have_children': True, 'sort_order': 1},
        {'name': 'Story', 'name_en': 'Story', 'icon': 'bi-bookmark', 'color': '#4A90D9', 
         'hierarchy_level': 1, 'can_have_children': True, 'is_default': True, 'sort_order': 2},
        {'name': 'Aufgabe', 'name_en': 'Task', 'icon': 'bi-check2-square', 'color': '#0076A8', 
         'hierarchy_level': 2, 'can_have_children': True, 'sort_order': 3},
        {'name': 'Fehler', 'name_en': 'Bug', 'icon': 'bi-bug', 'color': '#DA291C', 
         'hierarchy_level': 2, 'can_have_children': True, 'sort_order': 4},
        {'name': 'Unteraufgabe', 'name_en': 'Sub-Task', 'icon': 'bi-card-list', 'color': '#75787B', 
         'hierarchy_level': 3, 'can_have_children': False, 'is_subtask': True, 'sort_order': 5},
    ]
    
    kanban_types = [
        {'name': 'Aufgabe', 'name_en': 'Task', 'icon': 'bi-check2-square', 'color': '#0076A8', 
         'hierarchy_level': 1, 'can_have_children': True, 'is_default': True, 'sort_order': 1},
        {'name': 'Fehler', 'name_en': 'Bug', 'icon': 'bi-bug', 'color': '#DA291C', 
         'hierarchy_level': 1, 'can_have_children': True, 'sort_order': 2},
    ]
    
    waterfall_types = [
        {'name': 'Phase', 'name_en': 'Phase', 'icon': 'bi-folder2', 'color': '#6E2B62', 
         'hierarchy_level': 0, 'can_have_children': True, 'sort_order': 1},
        {'name': 'Meilenstein', 'name_en': 'Milestone', 'icon': 'bi-flag', 'color': '#4A90D9', 
         'hierarchy_level': 1, 'can_have_children': True, 'sort_order': 2},
        {'name': 'Arbeitspaket', 'name_en': 'Work Package', 'icon': 'bi-box', 'color': '#0076A8', 
         'hierarchy_level': 2, 'can_have_children': True, 'is_default': True, 'sort_order': 3},
    ]
    
    type_configs = {
        'scrum': scrum_types,
        'kanban': kanban_types,
        'waterfall': waterfall_types,
        'custom': scrum_types  # Default to Scrum for custom
    }
    
    types = type_configs.get(project.methodology, scrum_types)
    
    for t in types:
        issue_type = IssueType(project_id=project.id, **t)
        db.session.add(issue_type)
    
    return types


def create_default_issue_statuses(project):
    """Create default workflow statuses for a new project based on methodology"""
    
    scrum_statuses = [
        {'name': 'Offen', 'name_en': 'Open', 'category': 'todo', 'color': '#75787B', 
         'is_initial': True, 'sort_order': 1},
        {'name': 'In Bearbeitung', 'name_en': 'In Progress', 'category': 'in_progress', 'color': '#0076A8', 
         'sort_order': 2},
        {'name': 'In Prüfung', 'name_en': 'In Review', 'category': 'in_progress', 'color': '#6E2B62', 
         'sort_order': 3},
        {'name': 'Erledigt', 'name_en': 'Done', 'category': 'done', 'color': '#4A90D9', 
         'is_final': True, 'sort_order': 4},
    ]
    
    kanban_statuses = [
        {'name': 'Backlog', 'name_en': 'Backlog', 'category': 'todo', 'color': '#75787B', 
         'is_initial': True, 'sort_order': 1},
        {'name': 'Bereit', 'name_en': 'Ready', 'category': 'todo', 'color': '#0076A8', 
         'sort_order': 2},
        {'name': 'In Arbeit', 'name_en': 'In Progress', 'category': 'in_progress', 'color': '#E87722', 
         'sort_order': 3},
        {'name': 'Prüfung', 'name_en': 'Review', 'category': 'in_progress', 'color': '#6E2B62', 
         'sort_order': 4},
        {'name': 'Fertig', 'name_en': 'Done', 'category': 'done', 'color': '#4A90D9', 
         'is_final': True, 'sort_order': 5},
    ]
    
    waterfall_statuses = [
        {'name': 'Geplant', 'name_en': 'Planned', 'category': 'todo', 'color': '#75787B', 
         'is_initial': True, 'sort_order': 1},
        {'name': 'Aktiv', 'name_en': 'Active', 'category': 'in_progress', 'color': '#0076A8', 
         'sort_order': 2},
        {'name': 'Abgeschlossen', 'name_en': 'Completed', 'category': 'done', 'color': '#4A90D9', 
         'is_final': True, 'sort_order': 3},
        {'name': 'Blockiert', 'name_en': 'Blocked', 'category': 'in_progress', 'color': '#DA291C', 
         'sort_order': 4},
    ]
    
    status_configs = {
        'scrum': scrum_statuses,
        'kanban': kanban_statuses,
        'waterfall': waterfall_statuses,
        'custom': scrum_statuses
    }
    
    statuses = status_configs.get(project.methodology, scrum_statuses)
    
    for s in statuses:
        status = IssueStatus(project_id=project.id, **s)
        db.session.add(status)
    
    return statuses