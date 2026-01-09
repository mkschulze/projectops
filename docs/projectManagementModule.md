# Projektmanagement-Modul — Technischer Plan

> **Ziel:** Erweiterung des ProjectOpss um ein modulares, Jira-ähnliches Projektmanagement-System
> 
> **Status:** Planung
> **Erstellt:** 2025-12-31

---

## Teil 1: Exploration & Anforderungsanalyse

### 1.1 Geschäftliche Anforderungen

#### Kernziele

| Ziel | Beschreibung | Priorität |
|------|--------------|-----------|
| **Modularität** | PM als opt-in Modul, das Admins pro Benutzer freischalten können | MUSS |
| **Jira-ähnlich** | Bekannte UX-Patterns für Adoption | MUSS |
| **Standalone** | PM funktioniert unabhängig von ProjectOps Tasks | MUSS |
| **Integration** | Optional: ProjectOps Tasks als PM-Issues verknüpfen | KANN |
| **Skalierbar** | Weitere Module in Zukunft möglich | SOLL |

#### Benutzerrollen & Berechtigungen

| Rolle | PM-Berechtigungen |
|-------|-------------------|
| **Admin** | Module freischalten, globale PM-Einstellungen |
| **Project Admin** | Projekt erstellen/löschen, Mitglieder verwalten, Workflows konfigurieren |
| **Project Lead** | Issues zuweisen, Sprints planen, Board konfigurieren |
| **Developer/Member** | Issues bearbeiten, Status ändern, Kommentieren |
| **Viewer** | Nur Lesen |

#### Funktionale Anforderungen

##### Projektverwaltung (P1 - Kritisch)
- [ ] Projekte erstellen mit eindeutigem Key (z.B. "TAX", "AUD")
- [ ] Projektmitglieder zuweisen
- [ ] Projekt-Lead festlegen
- [ ] Projekt archivieren/löschen

##### Issue-Management (P1 - Kritisch)
- [ ] Issue-Typen: Epic, Story, Task, Bug, Sub-Task
- [ ] Issue-Attribute: Titel, Beschreibung, Priorität, Status, Assignee, Reporter
- [ ] Automatische Issue-Keys (TAX-1, TAX-2, ...)
- [ ] Issue-Beziehungen: Parent/Child, Blocks/Blocked by, Relates to

##### Kanban Board (P1 - Kritisch)
- [ ] Drag & Drop Status-Änderung
- [ ] Spalten basierend auf Workflow-Status
- [ ] Swimlanes nach Assignee/Epic/Priorität
- [ ] Quick-Filter

##### Backlog (P2 - Hoch)
- [ ] Priorisierte Issue-Liste
- [ ] Drag & Drop Sortierung
- [ ] Bulk-Aktionen (Move to Sprint, Priorität ändern)

##### Sprint-Management (P2 - Hoch)
- [ ] Sprint erstellen mit Start/End-Datum
- [ ] Sprint-Ziel definieren
- [ ] Issues in Sprint ziehen
- [ ] Sprint starten/beenden
- [ ] Burndown Chart

##### Erweiterte Features (P3 - Nice-to-have)
- [ ] Epics mit Progress-Tracking
- [ ] Komponenten (technische Bereiche)
- [ ] Versionen/Releases
- [ ] Workflow-Builder (konfigurierbare Status-Übergänge)
- [ ] JQL-ähnliche Suche
- [ ] Dashboards & Reports

---

### 1.2 Technische Analyse

#### Bestandsaufnahme (Ist-Zustand)

```
Aktuelle Architektur:
├── app.py              # Monolithische Routen (~3100 Zeilen)
├── models.py           # Alle Models (~850 Zeilen)
├── services.py         # Business Logic (~650 Zeilen)
├── translations.py     # i18n
└── templates/          # Jinja2 Templates

Probleme für Modularität:
1. Alle Routen in einer Datei
2. Keine Blueprint-Struktur
3. Keine Modul-Abstraktion
4. Navbar ist statisch (keine dynamischen Module)
```

#### Technische Risiken

| Risiko | Auswirkung | Mitigation |
|--------|------------|------------|
| Monolithische app.py | Schwer zu warten | Blueprint-Refactoring |
| Keine Modul-Infrastruktur | Feature-Toggle komplex | ModuleRegistry Pattern |
| Performance bei vielen Issues | Langsame Boards | Pagination, Lazy Loading |
| Drag & Drop Komplexität | JS-Bugs | SortableJS Bibliothek |

#### Technologie-Entscheidungen

| Entscheidung | Gewählt | Alternative | Begründung |
|--------------|---------|-------------|------------|
| Drag & Drop | SortableJS | HTML5 native | Robuster, Touch-Support |
| Echtzeit-Updates | Flask-SocketIO | Polling | Bereits vorhanden |
| Markdown Editor | SimpleMDE | TinyMCE | Leichtgewichtig |
| Charts | Chart.js | ApexCharts | Bereits vorhanden |

---

### 1.3 Integrationsanalyse

#### Modul-System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  ModuleRegistry                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   ProjectOps    │  │   Projects  │  │   Future    │             │
│  │   Module    │  │   Module    │  │   Modules   │             │
│  │             │  │             │  │             │             │
│  │ - routes    │  │ - routes    │  │ - ...       │             │
│  │ - models    │  │ - models    │  │             │             │
│  │ - services  │  │ - services  │  │             │             │
│  │ - templates │  │ - templates │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  Shared Services                                                │
│  - User Management                                              │
│  - Notifications                                                │
│  - Audit Logging                                                │
│  - Email Service                                                │
├─────────────────────────────────────────────────────────────────┤
│  Database Layer (SQLAlchemy)                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Datenbank-Schema (Vorschau)

```sql
-- Modul-System
CREATE TABLE module (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) UNIQUE,     -- 'projectops', 'projects'
    name VARCHAR(100),
    description TEXT,
    is_core BOOLEAN DEFAULT FALSE,  -- Core-Module können nicht deaktiviert werden
    is_active BOOLEAN DEFAULT TRUE,
    icon VARCHAR(50),
    nav_order INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE user_module (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    module_id INTEGER REFERENCES module(id),
    granted_at TIMESTAMP,
    granted_by_id INTEGER REFERENCES user(id),
    UNIQUE(user_id, module_id)
);

-- Projektmanagement
CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    key VARCHAR(10) UNIQUE,      -- 'TAX', 'AUD'
    name VARCHAR(200),
    description TEXT,
    lead_id INTEGER REFERENCES user(id),
    category VARCHAR(50),
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE project_member (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    user_id INTEGER REFERENCES user(id),
    role VARCHAR(50),            -- 'admin', 'member', 'viewer'
    joined_at TIMESTAMP,
    UNIQUE(project_id, user_id)
);

CREATE TABLE issue_type (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),  -- NULL = global
    name VARCHAR(50),
    icon VARCHAR(50),
    color VARCHAR(7),
    is_subtask BOOLEAN DEFAULT FALSE,
    sort_order INTEGER
);

CREATE TABLE issue_status (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    name VARCHAR(50),
    category VARCHAR(20),        -- 'todo', 'in_progress', 'done'
    color VARCHAR(7),
    sort_order INTEGER
);

CREATE TABLE issue (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    key VARCHAR(20),             -- 'TAX-42'
    issue_number INTEGER,        -- Auto-increment per project
    type_id INTEGER REFERENCES issue_type(id),
    status_id INTEGER REFERENCES issue_status(id),
    priority VARCHAR(20),        -- 'highest', 'high', 'medium', 'low', 'lowest'
    
    title VARCHAR(500),
    description TEXT,
    
    reporter_id INTEGER REFERENCES user(id),
    assignee_id INTEGER REFERENCES user(id),
    
    parent_id INTEGER REFERENCES issue(id),      -- For sub-tasks
    epic_id INTEGER REFERENCES issue(id),        -- Epic link
    sprint_id INTEGER REFERENCES sprint(id),
    
    story_points INTEGER,
    original_estimate INTEGER,   -- Minutes
    time_spent INTEGER,          -- Minutes
    
    due_date DATE,
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    UNIQUE(project_id, issue_number)
);

CREATE TABLE sprint (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    name VARCHAR(100),
    goal TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),          -- 'future', 'active', 'closed'
    created_at TIMESTAMP
);

CREATE TABLE issue_comment (
    id INTEGER PRIMARY KEY,
    issue_id INTEGER REFERENCES issue(id),
    author_id INTEGER REFERENCES user(id),
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE issue_attachment (
    id INTEGER PRIMARY KEY,
    issue_id INTEGER REFERENCES issue(id),
    filename VARCHAR(255),
    filepath VARCHAR(500),
    filesize INTEGER,
    mimetype VARCHAR(100),
    uploaded_by_id INTEGER REFERENCES user(id),
    uploaded_at TIMESTAMP
);

CREATE TABLE issue_link (
    id INTEGER PRIMARY KEY,
    source_issue_id INTEGER REFERENCES issue(id),
    target_issue_id INTEGER REFERENCES issue(id),
    link_type VARCHAR(50),       -- 'blocks', 'is_blocked_by', 'relates_to', 'duplicates'
    created_at TIMESTAMP
);

CREATE TABLE worklog (
    id INTEGER PRIMARY KEY,
    issue_id INTEGER REFERENCES issue(id),
    author_id INTEGER REFERENCES user(id),
    time_spent INTEGER,          -- Minutes
    work_date DATE,
    description TEXT,
    created_at TIMESTAMP
);

CREATE TABLE board (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    name VARCHAR(100),
    type VARCHAR(20),            -- 'kanban', 'scrum'
    filter_jql TEXT,             -- Optional filter
    created_at TIMESTAMP
);

CREATE TABLE board_column (
    id INTEGER PRIMARY KEY,
    board_id INTEGER REFERENCES board(id),
    status_id INTEGER REFERENCES issue_status(id),
    name VARCHAR(50),
    sort_order INTEGER,
    min_issues INTEGER,          -- WIP limit min
    max_issues INTEGER           -- WIP limit max
);
```

---

## Teil 2: Technical & Functional Design

### 2.1 Architektur-Design

#### Blueprint-Struktur

```
company-projectops-calendar/
├── app.py                      # Application Factory, nur Init
├── config.py                   # Konfiguration
├── extensions.py               # Flask Extensions (db, login, socketio)
├── models/                     # Shared Models
│   ├── __init__.py
│   ├── user.py
│   ├── audit.py
│   └── module.py               # Module, UserModule
│
├── modules/                    # Modul-Container
│   ├── __init__.py             # ModuleRegistry
│   │
│   ├── core/                   # Kern-Funktionen
│   │   ├── __init__.py
│   │   ├── routes.py           # Login, Dashboard, Admin
│   │   ├── decorators.py       # @login_required, @admin_required
│   │   └── templates/
│   │       ├── base.html
│   │       ├── login.html
│   │       └── admin/
│   │
│   ├── projectops/                 # ProjectOps (bestehend, refactored)
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── models.py           # Task, Entity, TaxType, etc.
│   │   ├── services.py
│   │   └── templates/
│   │       ├── dashboard.html
│   │       ├── calendar.html
│   │       └── tasks/
│   │
│   └── projects/               # NEU: Projektmanagement
│       ├── __init__.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── projects.py
│       │   ├── issues.py
│       │   ├── boards.py
│       │   ├── sprints.py
│       │   └── api.py          # REST API für Drag & Drop
│       ├── models/
│       │   ├── __init__.py
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── sprint.py
│       │   └── board.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── issue_service.py
│       │   ├── sprint_service.py
│       │   └── board_service.py
│       └── templates/
│           └── projects/
│               ├── list.html
│               ├── detail.html
│               ├── settings.html
│               ├── issues/
│               │   ├── list.html
│               │   ├── detail.html
│               │   ├── form.html
│               │   └── _card.html
│               ├── boards/
│               │   ├── kanban.html
│               │   └── backlog.html
│               └── sprints/
│                   ├── list.html
│                   └── detail.html
│
├── services/                   # Shared Services
│   ├── __init__.py
│   ├── notification_service.py
│   ├── email_service.py
│   └── export_service.py
│
├── static/
│   ├── js/
│   │   ├── modules/
│   │   │   └── projects/
│   │   │       ├── kanban.js
│   │   │       └── backlog.js
│   │   └── shared/
│   │       └── notifications.js
│   └── css/
│
└── translations.py
```

#### ModuleRegistry Pattern

```python
# modules/__init__.py

class ModuleRegistry:
    """Central registry for all application modules"""
    
    _modules = {}
    
    @classmethod
    def register(cls, module_code: str, module_class):
        """Register a module"""
        cls._modules[module_code] = module_class
    
    @classmethod
    def get_module(cls, module_code: str):
        """Get a module by code"""
        return cls._modules.get(module_code)
    
    @classmethod
    def get_all_modules(cls):
        """Get all registered modules"""
        return cls._modules.values()
    
    @classmethod
    def get_user_modules(cls, user):
        """Get modules accessible by user"""
        if user.is_admin:
            return cls._modules.values()
        
        user_module_codes = {um.module.code for um in user.modules}
        return [m for c, m in cls._modules.items() if c in user_module_codes]


class BaseModule:
    """Base class for all modules"""
    
    code = None          # Unique module identifier
    name = None          # Display name
    icon = None          # Bootstrap icon
    nav_order = 0        # Navigation order
    is_core = False      # Cannot be disabled
    
    @classmethod
    def get_blueprint(cls):
        """Return Flask Blueprint for this module"""
        raise NotImplementedError
    
    @classmethod
    def get_nav_items(cls, user):
        """Return navigation items for this user"""
        raise NotImplementedError
    
    @classmethod
    def init_app(cls, app):
        """Initialize module with Flask app"""
        pass
```

#### Modul-Definition Beispiel

```python
# modules/projects/__init__.py

from flask import Blueprint
from modules import BaseModule, ModuleRegistry

class ProjectsModule(BaseModule):
    code = 'projects'
    name = 'Projektmanagement'
    name_en = 'Project Management'
    icon = 'bi-kanban'
    nav_order = 20
    is_core = False
    
    _blueprint = None
    
    @classmethod
    def get_blueprint(cls):
        if cls._blueprint is None:
            cls._blueprint = Blueprint(
                'projects',
                __name__,
                template_folder='templates',
                url_prefix='/projects'
            )
            from .routes import register_routes
            register_routes(cls._blueprint)
        return cls._blueprint
    
    @classmethod
    def get_nav_items(cls, user):
        return [
            {
                'label': cls.name,
                'icon': cls.icon,
                'url': '/projects',
                'children': [
                    {'label': 'Alle Projekte', 'url': '/projects'},
                    {'label': 'Meine Issues', 'url': '/projects/issues/my'},
                    {'label': 'Boards', 'url': '/projects/boards'},
                ]
            }
        ]

# Register module
ModuleRegistry.register('projects', ProjectsModule)
```

---

### 2.2 Functional Design

#### Issue-Workflow (Standard)

```
┌─────────┐     ┌───────────┐     ┌───────────┐     ┌──────────┐
│  OPEN   │────▶│IN PROGRESS│────▶│  IN TEST  │────▶│   DONE   │
└────┬────┘     └─────┬─────┘     └─────┬─────┘     └──────────┘
     │                │                 │
     │                │                 │
     ▼                ▼                 ▼
┌─────────┐     ┌───────────┐     ┌───────────┐
│ ON HOLD │◀───▶│  BLOCKED  │────▶│ CANCELLED │
└─────────┘     └───────────┘     └───────────┘
```

#### Status-Kategorien

| Kategorie | Status | Farbe | Beschreibung |
|-----------|--------|-------|--------------|
| `todo` | Open | Grau | Noch nicht begonnen |
| `todo` | On Hold | Gelb | Pausiert |
| `in_progress` | In Progress | Blau | In Bearbeitung |
| `in_progress` | Blocked | Rot | Blockiert |
| `in_progress` | In Test | Teal | In QA/Review |
| `done` | Done | Grün | Abgeschlossen |
| `done` | Cancelled | Dunkelgrau | Abgebrochen |

#### Issue-Typen

| Typ | Icon | Farbe | Kann Sub-Tasks haben | Kann Epic sein |
|-----|------|-------|---------------------|----------------|
| Epic | 🔮 | Lila | Nein | Ja |
| Story | 📗 | Grün | Ja | Nein |
| Task | ☑️ | Blau | Ja | Nein |
| Bug | 🐛 | Rot | Ja | Nein |
| Sub-Task | 📎 | Grau | Nein | Nein |

#### Prioritäten

| Priorität | Icon | Farbe | Beschreibung |
|-----------|------|-------|--------------|
| Highest | ⬆️⬆️ | Dunkelrot | Kritisch, sofort bearbeiten |
| High | ⬆️ | Rot | Wichtig, bald bearbeiten |
| Medium | ➡️ | Gelb | Normal |
| Low | ⬇️ | Blau | Weniger wichtig |
| Lowest | ⬇️⬇️ | Grau | Kann warten |

---

### 2.3 API-Design

#### REST Endpoints

```
# Projekte
GET    /projects                     # Liste aller Projekte
POST   /projects                     # Neues Projekt erstellen
GET    /projects/<key>               # Projekt-Details
PUT    /projects/<key>               # Projekt aktualisieren
DELETE /projects/<key>               # Projekt löschen
GET    /projects/<key>/settings      # Projekt-Einstellungen

# Issues
GET    /projects/<key>/issues        # Issues im Projekt
POST   /projects/<key>/issues        # Neues Issue
GET    /projects/<key>/issues/<num>  # Issue-Details (TAX-42)
PUT    /projects/<key>/issues/<num>  # Issue aktualisieren
DELETE /projects/<key>/issues/<num>  # Issue löschen

# Board API (für Drag & Drop)
GET    /api/projects/<key>/board              # Board-Daten
PUT    /api/projects/<key>/issues/<num>/move  # Issue verschieben
POST   /api/projects/<key>/issues/<num>/rank  # Issue-Reihenfolge

# Sprints
GET    /projects/<key>/sprints              # Sprint-Liste
POST   /projects/<key>/sprints              # Sprint erstellen
PUT    /projects/<key>/sprints/<id>         # Sprint aktualisieren
POST   /projects/<key>/sprints/<id>/start   # Sprint starten
POST   /projects/<key>/sprints/<id>/close   # Sprint beenden

# Backlog
GET    /projects/<key>/backlog              # Backlog-Issues
PUT    /api/projects/<key>/backlog/rank     # Backlog sortieren
```

#### WebSocket Events (Real-time Board Updates)

```javascript
// Client → Server
socket.emit('join_board', { project_key: 'TAX' });
socket.emit('leave_board', { project_key: 'TAX' });

// Server → Client
socket.on('issue_moved', {
    issue_key: 'TAX-42',
    from_status: 'open',
    to_status: 'in_progress',
    moved_by: 'user@democorp.local'
});

socket.on('issue_updated', {
    issue_key: 'TAX-42',
    changes: { assignee: 'new@democorp.local' }
});

socket.on('issue_created', {
    issue: { ... }
});
```

---

### 2.4 UI-Komponenten Design

#### Kanban Board

```html
┌────────────────────────────────────────────────────────────────────┐
│ [🔍 Quick Filter] [Assignee ▼] [Type ▼] [Epic ▼]  [⚙️] [📊]      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ TO DO (3)   │  │ IN PROGRESS │  │  IN TEST    │  │   DONE    │ │
│  │             │  │    (2)      │  │    (1)      │  │    (5)    │ │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├───────────┤ │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌───────┐ │ │
│  │ │ TAX-45  │ │  │ │ TAX-42  │ │  │ │ TAX-38  │ │  │ │TAX-31 │ │ │
│  │ │ ☑️ Task │ │  │ │ 📗 Story│ │  │ │ 🐛 Bug  │ │  │ │ ✓     │ │ │
│  │ │ ⬆️ High │ │  │ │ ➡️ Med  │ │  │ │ ⬆️ High │ │  │ └───────┘ │ │
│  │ │ 👤 Max  │ │  │ │ 👤 Anna │ │  │ │ 👤 Tom  │ │  │ ┌───────┐ │ │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │  │ │TAX-32 │ │ │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │             │  │ │ ✓     │ │ │
│  │ │ TAX-46  │ │  │ │ TAX-43  │ │  │             │  │ └───────┘ │ │
│  │ │ 🐛 Bug  │ │  │ │ ☑️ Task │ │  │             │  │           │ │
│  │ └─────────┘ │  │ └─────────┘ │  │             │  │           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Issue Card Component

```html
<div class="issue-card" draggable="true" data-issue-key="TAX-42">
    <div class="issue-card-header">
        <span class="issue-type-icon" title="Story">📗</span>
        <a href="/projects/TAX/issues/42" class="issue-key">TAX-42</a>
        <span class="issue-priority" title="Medium">➡️</span>
    </div>
    <div class="issue-card-title">
        Implement user authentication
    </div>
    <div class="issue-card-footer">
        <span class="issue-epic-badge" style="background: #8777D9;">
            Authentication
        </span>
        <div class="issue-meta">
            <span class="story-points">3</span>
            <img src="/avatar/max" class="assignee-avatar" title="Max Müller">
        </div>
    </div>
</div>
```

#### Issue Detail Modal/Page

```
┌──────────────────────────────────────────────────────────────────────┐
│ TAX-42: Implement user authentication                          [X]  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────┐  ┌────────────────────────────┐ │
│  │ Description                    │  │ Details                    │ │
│  │ ────────────────────────────── │  │ ────────────────────────── │ │
│  │ As a user, I want to...        │  │ Type:      📗 Story        │ │
│  │                                │  │ Status:    🔵 In Progress  │ │
│  │ ## Acceptance Criteria         │  │ Priority:  ➡️ Medium       │ │
│  │ - [ ] Login form works         │  │ Assignee:  👤 Max Müller   │ │
│  │ - [ ] Session persists         │  │ Reporter:  👤 Anna Schmidt │ │
│  │ - [ ] Logout clears session    │  │ Sprint:    Sprint 3        │ │
│  │                                │  │ Epic:      Authentication  │ │
│  │ [Edit Description]             │  │ Points:    3               │ │
│  │                                │  │ Due Date:  15.01.2026      │ │
│  ├────────────────────────────────┤  │                            │ │
│  │ Activity                       │  │ Time Tracking              │ │
│  │ ────────────────────────────── │  │ ────────────────────────── │ │
│  │ [Comments] [History] [Worklog] │  │ Estimated: 4h              │ │
│  │                                │  │ Logged:    2h 30m          │ │
│  │ 💬 Max: "Started working on...│  │ Remaining: 1h 30m          │ │
│  │    vor 2 Stunden               │  │ [Log Time]                 │ │
│  │                                │  │                            │ │
│  │ [Add Comment...]               │  └────────────────────────────┘ │
│  └────────────────────────────────┘                                 │
│                                                                      │
│  Sub-Tasks (2/3 done)                                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ✓ TAX-43: Create login form              Max      Done       │  │
│  │ ✓ TAX-44: Implement session handling     Max      Done       │  │
│  │ ○ TAX-45: Add logout functionality       Max      In Progress│  │
│  │ [+ Add Sub-Task]                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Links                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ blocks → TAX-50: Deploy to production                        │  │
│  │ [+ Add Link]                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Teil 3: Implementierungsplan

### 3.1 Phasen-Übersicht

| Phase | Name | Beschreibung | Aufwand | Abhängigkeiten |
|-------|------|--------------|---------|----------------|
| PM-0 | Infrastruktur | Blueprint-Refactoring, Modul-System | 3-4h | - |
| PM-1 | Basis | Projekt-CRUD, Mitglieder | 2-3h | PM-0 |
| PM-2 | Issues | Issue-CRUD, Typen, Status | 3-4h | PM-1 |
| PM-3 | Kanban | Board mit Drag & Drop | 3-4h | PM-2 |
| PM-4 | Backlog | Priorisierte Liste, Ranking | 2h | PM-2 |
| PM-5 | Sprints | Sprint-Management | 2-3h | PM-4 |
| PM-6 | Details | Kommentare, Attachments, Links | 2-3h | PM-2 |
| PM-7 | Epics | Epic-Hierarchie, Progress | 2h | PM-2 |
| PM-8 | Suche | Filter, Quick Search | 2h | PM-2 |
| PM-9 | Charts | Burndown, Velocity | 2h | PM-5 |
| PM-10 | Workflows | Konfigurierbare Übergänge | 3h | PM-2 |

### 3.2 Detaillierter Implementierungsplan

#### Phase PM-0: Infrastruktur (3-4h)

**Ziel:** Modulare Architektur aufbauen

**Tasks:**
```
PM-0.1 Extensions extrahieren (30min)
       - extensions.py erstellen
       - db, login_manager, socketio auslagern
       - Zirkuläre Imports vermeiden

PM-0.2 Blueprint-Struktur (1h)
       - modules/ Verzeichnis erstellen
       - modules/core/ für Basis-Routen
       - Bestehende Routen kategorisieren

PM-0.3 ModuleRegistry (45min)
       - BaseModule Klasse
       - ModuleRegistry Singleton
       - Module Model & UserModule

PM-0.4 Dynamische Navigation (45min)
       - base.html anpassen
       - Nav-Items aus Modulen laden
       - Modul-Berechtigung prüfen

PM-0.5 Admin Modul-Verwaltung (1h)
       - Admin-UI für Module
       - User-Modul-Zuweisung
       - Modul aktivieren/deaktivieren
```

**Dateien:**
- `extensions.py` (neu)
- `modules/__init__.py` (neu)
- `modules/core/` (neu)
- `models/module.py` (neu)
- `templates/base.html` (ändern)
- `templates/admin/modules.html` (neu)
- `templates/admin/user_modules.html` (neu)

**Migration:**
```python
# d1e2f3g4h5i6_add_module_system.py
def upgrade():
    # module table
    # user_module table
```

---

#### Phase PM-1: Projekt-Basis (2-3h)

**Ziel:** Projekte erstellen und verwalten

**Tasks:**
```
PM-1.1 Project Model (30min)
       - Project, ProjectMember Models
       - Validierung (Key Format: ^[A-Z]{2,5}$)
       
PM-1.2 Projekt-Routen (1h)
       - /projects - Liste
       - /projects/new - Erstellen
       - /projects/<key> - Detail
       - /projects/<key>/settings - Einstellungen
       
PM-1.3 Projekt-Templates (1h)
       - projects/list.html
       - projects/form.html
       - projects/detail.html
       - projects/settings.html
       
PM-1.4 Mitglieder-Verwaltung (30min)
       - Mitglieder hinzufügen/entfernen
       - Rollen zuweisen
```

**Dateien:**
- `modules/projects/__init__.py`
- `modules/projects/models/project.py`
- `modules/projects/routes/projects.py`
- `modules/projects/templates/projects/`

---

#### Phase PM-2: Issue-Management (3-4h)

**Ziel:** Issues erstellen und bearbeiten

**Tasks:**
```
PM-2.1 Issue Models (45min)
       - Issue, IssueType, IssueStatus
       - Auto-Increment Issue-Nummer pro Projekt
       - Key-Generierung (TAX-1, TAX-2, ...)
       
PM-2.2 Standard-Typen & Status (30min)
       - Default IssueTypes: Epic, Story, Task, Bug, Sub-Task
       - Default IssueStatus: Open, In Progress, In Test, Done
       
PM-2.3 Issue-CRUD Routen (1h)
       - /projects/<key>/issues
       - /projects/<key>/issues/new
       - /projects/<key>/issues/<num>
       
PM-2.4 Issue-Formular (1h)
       - Typ, Titel, Beschreibung
       - Priorität, Assignee
       - Parent-Auswahl (für Sub-Tasks)
       - Markdown-Editor für Description
       
PM-2.5 Issue-Detail Seite (1h)
       - Alle Felder anzeigen
       - Inline-Edit für einzelne Felder
       - Activity Feed Platzhalter
```

**Dateien:**
- `modules/projects/models/issue.py`
- `modules/projects/routes/issues.py`
- `modules/projects/templates/projects/issues/`

---

#### Phase PM-3: Kanban Board (3-4h)

**Ziel:** Visuelles Board mit Drag & Drop

**Tasks:**
```
PM-3.1 Board Model (30min)
       - Board, BoardColumn
       - Default Kanban-Board pro Projekt
       
PM-3.2 Board-View Route (30min)
       - /projects/<key>/board
       - Issues nach Status gruppieren
       
PM-3.3 Kanban Template (1h)
       - Spalten-Layout
       - Issue-Cards
       - Responsive Design
       
PM-3.4 SortableJS Integration (1h)
       - Drag & Drop zwischen Spalten
       - Sortierung innerhalb Spalte
       
PM-3.5 Move-API (30min)
       - PUT /api/projects/<key>/issues/<num>/move
       - Status-Update + Audit Log
       
PM-3.6 WebSocket Updates (30min)
       - Board-Room joinieren
       - Echtzeit-Updates bei Änderungen
```

**Dateien:**
- `modules/projects/models/board.py`
- `modules/projects/routes/boards.py`
- `modules/projects/routes/api.py`
- `modules/projects/templates/projects/boards/kanban.html`
- `static/js/modules/projects/kanban.js`

**JavaScript-Bibliothek:**
```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
```

---

#### Phase PM-4: Backlog (2h)

**Ziel:** Priorisierte Issue-Liste

**Tasks:**
```
PM-4.1 Backlog-View (30min)
       - /projects/<key>/backlog
       - Issues ohne Sprint
       
PM-4.2 Ranking-System (30min)
       - rank Feld zu Issue
       - Drag & Drop Sortierung
       
PM-4.3 Bulk-Aktionen (30min)
       - Move to Sprint
       - Set Priority
       - Assign
       
PM-4.4 Sprint-Integration (30min)
       - Sprint-Selector
       - Issues in Sprint ziehen
```

---

#### Phase PM-5: Sprint-Management (2-3h)

**Ziel:** Sprints planen und durchführen

**Tasks:**
```
PM-5.1 Sprint Model (30min)
       - name, goal, start_date, end_date, status
       
PM-5.2 Sprint-CRUD (45min)
       - /projects/<key>/sprints
       - Sprint erstellen/bearbeiten
       
PM-5.3 Sprint-Board (45min)
       - Aktiver Sprint als Default-Board
       - Sprint-Header mit Infos
       
PM-5.4 Sprint starten/beenden (30min)
       - Validierung (nur ein aktiver Sprint)
       - Unfertige Issues beim Schließen
       
PM-5.5 Sprint-Bericht (30min)
       - Velocity berechnen
       - Burndown-Daten
```

---

#### Phase PM-6: Issue-Details (2-3h)

**Tasks:**
```
PM-6.1 Kommentare (45min)
       - IssueComment Model
       - Add/Edit/Delete Kommentare
       - Markdown-Rendering
       
PM-6.2 Attachments (45min)
       - IssueAttachment Model
       - File Upload
       - Preview/Download
       
PM-6.3 Issue-Links (30min)
       - IssueLink Model
       - blocks/blocked by/relates to
       
PM-6.4 Activity Log (30min)
       - Alle Änderungen tracken
       - Timeline-View
       
PM-6.5 Worklog (30min)
       - Zeit erfassen
       - Remaining aktualisieren
```

---

#### Phase PM-7: Epics (2h)

**Tasks:**
```
PM-7.1 Epic als Issue-Typ (30min)
       - Epic-spezifische Felder
       - Child-Issues verknüpfen
       
PM-7.2 Epic-Board (30min)
       - Issues nach Epic gruppieren
       - Epic-Swimlanes
       
PM-7.3 Progress-Tracking (30min)
       - Story Points summieren
       - Fortschrittsbalken
       
PM-7.4 Epic-Roadmap (30min)
       - Timeline-Ansicht
       - Gantt-ähnlich
```

---

#### Phase PM-8: Suche & Filter (2h)

**Tasks:**
```
PM-8.1 Quick-Filter (30min)
       - Assignee, Type, Priority
       - URL-Parameter
       
PM-8.2 Text-Suche (30min)
       - Titel, Beschreibung
       - Issue-Key
       
PM-8.3 Saved Filters (30min)
       - Filter speichern
       - Als Board-Filter nutzen
       
PM-8.4 JQL-Light (30min)
       - Einfache Query-Sprache
       - assignee = currentUser()
       - status = "In Progress"
```

---

#### Phase PM-9: Charts & Reports (2h)

**Tasks:**
```
PM-9.1 Burndown Chart (45min)
       - Chart.js Line Chart
       - Ideal vs Actual
       
PM-9.2 Velocity Chart (30min)
       - Story Points pro Sprint
       - Bar Chart
       
PM-9.3 Cumulative Flow (45min)
       - Stacked Area Chart
       - Issues über Zeit nach Status
```

---

#### Phase PM-10: Workflows (3h) ✅ ERLEDIGT

**Tasks:**
```
PM-10.1 Workflow Model (30min) ✅
        - Erlaubte Status-Übergänge
        - Pro Projekt konfigurierbar
        
PM-10.2 Workflow-Editor (1h) ✅
        - Visual Editor für Übergänge
        - Validierung
        
PM-10.3 Transition-Checks (30min) ✅
        - Pflichtfelder bei Übergang
        - Berechtigungsprüfung
        
PM-10.4 Post-Functions (1h) ✅
        - Automatische Aktionen
        - Assignee setzen, Notifications
```

---

#### Phase PM-11: Methodology Agnostic (2h) ✅ ERLEDIGT

**Tasks:**
```
PM-11.1 METHODOLOGY_CONFIG (30min) ✅
        - Scrum, Kanban, Waterfall, Custom Definitionen
        - Features und Terminologie pro Methodik
        
PM-11.2 Helper-Methoden (30min) ✅
        - get_term(key, lang) mit Fallback-Kette
        - has_feature(feature) Check
        - get_methodology_name(lang)
        
PM-11.3 Settings UI (45min) ✅
        - Methodik-Auswahl mit Feature-Badges
        - Terminologie-Anpassung (DE/EN)
        - Reset zu Standard
        
PM-11.4 Template Integration (15min) ✅
        - Sprint-Liste, Backlog, Board mit get_term()
        - Dynamische Labels basierend auf Methodik
```

---

### 3.3 Test-Strategie

#### Unit Tests
```python
# tests/modules/projects/test_issue_service.py
def test_create_issue_generates_key():
    issue = IssueService.create(project_key='TAX', title='Test')
    assert issue.key == 'TAX-1'
    
def test_issue_key_auto_increments():
    IssueService.create(project_key='TAX', title='First')
    issue = IssueService.create(project_key='TAX', title='Second')
    assert issue.key == 'TAX-2'
```

#### Integration Tests
```python
# tests/modules/projects/test_board_api.py
def test_move_issue_updates_status(client, auth):
    response = client.put(
        '/api/projects/TAX/issues/1/move',
        json={'status': 'in_progress'}
    )
    assert response.status_code == 200
    assert Issue.query.get(1).status.name == 'In Progress'
```

---

### 3.4 Deployment-Überlegungen

#### Neue Dependencies
```toml
[packages]
# Existing...
simplemde = "*"           # Markdown Editor (optional)
```

#### Migrations-Reihenfolge
1. `d1e2f3g4h5i6_add_module_system.py`
2. `e2f3g4h5i6j7_add_project_models.py`
3. `f3g4h5i6j7k8_add_issue_models.py`
4. `g4h5i6j7k8l9_add_board_models.py`
5. `h5i6j7k8l9m0_add_sprint_models.py`

#### Feature Flags (Optional)
```python
# config.py
FEATURE_FLAGS = {
    'PM_SPRINTS': True,
    'PM_EPICS': True,
    'PM_WORKFLOWS': False,  # Noch nicht fertig
}
```

---

## Anhang

### A. Glossar

| Begriff | Beschreibung |
|---------|--------------|
| **Epic** | Große User Story, die mehrere Stories gruppiert |
| **Story** | Anforderung aus Benutzersicht |
| **Task** | Technische Aufgabe |
| **Bug** | Fehler im System |
| **Sub-Task** | Teil einer Story/Task |
| **Sprint** | Zeitbox für Entwicklung (meist 2 Wochen) |
| **Backlog** | Priorisierte Liste aller Issues |
| **Velocity** | Durchschnittliche Story Points pro Sprint |
| **Burndown** | Verbleibende Arbeit über Zeit |

### B. Referenzen

- [Jira Cloud REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [SortableJS Dokumentation](https://sortablejs.github.io/Sortable/)
- [Chart.js Dokumentation](https://www.chartjs.org/docs/latest/)

### C. Offene Fragen

1. Sollen ProjectOps-Tasks als PM-Issues importierbar sein?
2. Sollen Projekte Entity-bezogen sein?
3. Sollen Workflows beim Erstellen eines Projekts kopiert werden können?
4. Ist Zeiterfassung (Worklog) im MVP enthalten?

---

**Nächster Schritt:** Bestätigung des Plans und Start mit Phase PM-0 (Infrastruktur)
