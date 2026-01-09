# Multi-Tenancy Design Document

> Detailliertes funktionales und technisches Design für Enterprise Multi-Tenancy
> 
> **Version:** 1.0  
> **Datum:** 2026-01-03  
> **Status:** Draft

---

## 1. Executive Summary

### 1.1 Ziel
Implementierung einer vollständigen Multi-Tenancy-Lösung, die es ermöglicht, mehrere unabhängige Mandanten (Clients) in einer einzelnen Applikationsinstanz zu betreiben, mit strikter Datenisolation und rollenbasierter Zugriffskontrolle.

### 1.2 Architektur-Entscheidung
**Session-basierter Tenant-Kontext** mit automatischer Query-Filterung

- Keine Tenant-Informationen in URLs (maximale Sicherheit)
- Server-kontrollierter Tenant-Wechsel
- Automatische Datenisolation auf Datenbankebene

### 1.3 Scope
- Tenant (Client) Verwaltung durch Super-Admin
- User-Tenant-Zuordnung mit Rollen pro Tenant
- Datenisolation für alle bestehenden und neuen Entities
- Demo-Daten für 2-3 Beispiel-Tenants

---

## 2. Funktionale Anforderungen

### 2.1 Benutzerrollen

#### 2.1.1 Super-Admin (Systemebene)
| Berechtigung | Beschreibung |
|--------------|--------------|
| Tenant erstellen | Neue Mandanten anlegen |
| Tenant bearbeiten | Name, Logo, Einstellungen ändern |
| Tenant deaktivieren | Mandant temporär sperren |
| Tenant löschen | Mandant und alle Daten entfernen |
| User zu Tenant zuweisen | Beliebige User zu beliebigen Tenants zuordnen |
| Alle Tenants sehen | Übersicht aller Mandanten |
| In Tenant wechseln | Als Super-Admin in jeden Tenant "eintreten" |
| System-Einstellungen | Globale Konfiguration |

#### 2.1.2 Tenant-Admin (Mandantenebene)
| Berechtigung | Beschreibung |
|--------------|--------------|
| User einladen | Neue User zum Tenant einladen |
| User-Rollen verwalten | Rollen innerhalb des Tenants ändern |
| User entfernen | User aus Tenant entfernen (nicht löschen) |
| Tenant-Einstellungen | Mandantenspezifische Konfiguration |
| Alle Daten des Tenants | Voller Zugriff auf Entities, Projekte, Tasks |

#### 2.1.3 Tenant-Rollen
| Rolle | Entities | Projekte | Tasks | Team | Berichte |
|-------|----------|----------|-------|------|----------|
| Admin | CRUD | CRUD | CRUD | CRUD | Alle |
| Manager | Read | CRUD | CRUD | Read | Eigene + Team |
| Member | Read | Read | Zugewiesene | Read | Eigene |
| Viewer | Read | Read | Read | Read | Keine |

### 2.2 User Stories

#### Super-Admin
```
Als Super-Admin möchte ich...
- SA-01: Einen neuen Mandanten anlegen können
- SA-02: Bestehende Mandanten bearbeiten können
- SA-03: Mandanten deaktivieren/reaktivieren können
- SA-04: User zu Mandanten zuweisen können
- SA-05: In jeden Mandanten wechseln können zur Analyse
- SA-06: Übersicht aller Mandanten mit Statistiken sehen
- SA-07: Audit-Logs systemweit einsehen können
```

#### Tenant-Admin
```
Als Tenant-Admin möchte ich...
- TA-01: User zu meinem Mandanten einladen können
- TA-02: Rollen meiner User verwalten können
- TA-03: User aus meinem Mandanten entfernen können
- TA-04: Mandanten-Einstellungen konfigurieren können
- TA-05: Audit-Logs meines Mandanten sehen können
```

#### Regulärer User
```
Als User möchte ich...
- U-01: Zwischen meinen Mandanten wechseln können
- U-02: Sehen zu welchem Mandanten ich gerade arbeite
- U-03: Nur Daten meines aktuellen Mandanten sehen
- U-04: Meinen Standard-Mandanten festlegen können
```

### 2.3 UI/UX Design

#### 2.3.1 Tenant-Switcher (Header)
```
┌─────────────────────────────────────────────────────────────────┐
│ [Company Logo]  Dashboard  Kalender  Projekte     [🏢 Mandant A ▼] [👤 User ▼] │
│                                                     │             │
│                                                     ▼             │
│                                        ┌────────────────────┐    │
│                                        │ ✓ Mandant A        │    │
│                                        │   Mandant B        │    │
│                                        │   Mandant C        │    │
│                                        │ ─────────────────  │    │
│                                        │ ⚙️ Mandant wechseln │    │
│                                        └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Super-Admin Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│ ADMIN > MANDANTEN                                    [+ Neu]    │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│ │ 🏢 Mandant A    │ │ 🏢 Mandant B    │ │ 🏢 Mandant C    │    │
│ │ ───────────────  │ │ ───────────────  │ │ ───────────────  │    │
│ │ 👥 12 User      │ │ 👥 8 User       │ │ 👥 5 User       │    │
│ │ 📁 45 Projekte  │ │ 📁 23 Projekte  │ │ 📁 12 Projekte  │    │
│ │ ✅ Aktiv        │ │ ✅ Aktiv        │ │ ⏸️ Inaktiv      │    │
│ │ [Bearbeiten]    │ │ [Bearbeiten]    │ │ [Aktivieren]    │    │
│ │ [Eintreten →]   │ │ [Eintreten →]   │ │ [Eintreten →]   │    │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3.3 Tenant-Erstellung
```
┌─────────────────────────────────────────────────────────────────┐
│ NEUEN MANDANTEN ERSTELLEN                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Name *                    [Mustermann GmbH              ]       │
│                                                                 │
│ Slug (URL-freundlich) *   [mustermann-gmbh              ]       │
│                                                                 │
│ Logo                      [📁 Datei wählen...]                  │
│                                                                 │
│ Primärfarbe               [#0076A8] 🎨                          │
│                                                                 │
│ Initialer Admin *         [▼ User auswählen...          ]       │
│                                                                 │
│ Module aktivieren         ☑️ ProjectOps                    │
│                           ☑️ Projekte                           │
│                           ☐ Anträge (optional)                  │
│                                                                 │
│                           [Abbrechen]  [✓ Erstellen]            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Technisches Design

### 3.1 Datenmodell

#### 3.1.1 Neue Tabellen

```sql
-- Tenant (Mandant)
CREATE TABLE tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    logo_url VARCHAR(255),
    primary_color VARCHAR(7) DEFAULT '#0076A8',
    is_active BOOLEAN DEFAULT TRUE,
    settings JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    created_by_id INTEGER REFERENCES user(id)
);

-- Tenant-Membership (User-Tenant-Zuordnung)
CREATE TABLE tenant_membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',  -- admin, manager, member, viewer
    is_default BOOLEAN DEFAULT FALSE,  -- Standard-Tenant beim Login
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    invited_by_id INTEGER REFERENCES user(id),
    UNIQUE(tenant_id, user_id)
);

-- Index für schnelle Lookups
CREATE INDEX idx_tenant_membership_user ON tenant_membership(user_id);
CREATE INDEX idx_tenant_membership_tenant ON tenant_membership(tenant_id);
```

#### 3.1.2 Erweiterung bestehender Tabellen

```sql
-- Alle tenant-spezifischen Tabellen erhalten tenant_id
ALTER TABLE entity ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE team ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE tax_type ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE task_preset ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE task ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE notification ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);

-- Projects-Modul
ALTER TABLE project ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE issue ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);
ALTER TABLE sprint ADD COLUMN tenant_id INTEGER REFERENCES tenant(id);

-- User-Erweiterung
ALTER TABLE user ADD COLUMN is_superadmin BOOLEAN DEFAULT FALSE;
ALTER TABLE user ADD COLUMN current_tenant_id INTEGER REFERENCES tenant(id);

-- Indices für Performance
CREATE INDEX idx_entity_tenant ON entity(tenant_id);
CREATE INDEX idx_team_tenant ON team(tenant_id);
CREATE INDEX idx_task_tenant ON task(tenant_id);
CREATE INDEX idx_project_tenant ON project(tenant_id);
CREATE INDEX idx_issue_tenant ON issue(tenant_id);
```

#### 3.1.3 Entity-Relationship-Diagramm

```
                            ┌──────────────┐
                            │    User      │
                            │ ───────────  │
                            │ is_superadmin│
                            │ current_     │
                            │ tenant_id    │
                            └──────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌──────────────┐  ┌──────────┐  ┌──────────────┐
            │   Tenant     │  │Membership│  │   Tenant     │
            │ ───────────  │◄─│ ──────── │─►│   (other)    │
            │ name, slug   │  │ role     │  │              │
            │ is_active    │  │is_default│  │              │
            └──────┬───────┘  └──────────┘  └──────────────┘
                   │
     ┌─────────────┼─────────────┬─────────────┐
     │             │             │             │
     ▼             ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Entity  │  │  Team   │  │ Project │  │  Task   │
│tenant_id│  │tenant_id│  │tenant_id│  │tenant_id│
└─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### 3.2 Python Models

#### 3.2.1 Tenant Model

```python
# models.py

class Tenant(db.Model):
    """Mandant/Client für Multi-Tenancy"""
    __tablename__ = 'tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#0076A8')
    is_active = db.Column(db.Boolean, default=True)
    settings = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    memberships = db.relationship('TenantMembership', back_populates='tenant',
                                   cascade='all, delete-orphan')
    entities = db.relationship('Entity', backref='tenant', lazy='dynamic')
    teams = db.relationship('Team', backref='tenant', lazy='dynamic')
    projects = db.relationship('Project', backref='tenant', lazy='dynamic')
    tasks = db.relationship('Task', backref='tenant', lazy='dynamic')
    
    @property
    def members(self):
        """Alle User dieses Tenants"""
        return [m.user for m in self.memberships]
    
    @property
    def admin_users(self):
        """Alle Admins dieses Tenants"""
        return [m.user for m in self.memberships if m.role == 'admin']
    
    def get_member_role(self, user):
        """Rolle eines Users in diesem Tenant"""
        membership = TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).first()
        return membership.role if membership else None
    
    def has_member(self, user):
        """Prüft ob User Mitglied ist"""
        return TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).first() is not None
    
    def __repr__(self):
        return f'<Tenant {self.name}>'


class TenantMembership(db.Model):
    """User-Tenant-Zuordnung mit Rolle"""
    __tablename__ = 'tenant_membership'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    is_default = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    tenant = db.relationship('Tenant', back_populates='memberships')
    user = db.relationship('User', foreign_keys=[user_id], backref='tenant_memberships')
    invited_by = db.relationship('User', foreign_keys=[invited_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user'),
    )
    
    ROLES = ['admin', 'manager', 'member', 'viewer']
    
    def __repr__(self):
        return f'<TenantMembership {self.user_id}@{self.tenant_id} ({self.role})>'
```

#### 3.2.2 User Model Erweiterung

```python
# models.py - User Erweiterung

class User(UserMixin, db.Model):
    # ... bestehende Felder ...
    
    # Neue Felder für Multi-Tenancy
    is_superadmin = db.Column(db.Boolean, default=False)
    current_tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    
    # Relationship
    current_tenant = db.relationship('Tenant', foreign_keys=[current_tenant_id])
    
    @property
    def tenants(self):
        """Alle Tenants des Users"""
        return [m.tenant for m in self.tenant_memberships if m.tenant.is_active]
    
    @property
    def default_tenant(self):
        """Standard-Tenant des Users"""
        default = TenantMembership.query.filter_by(
            user_id=self.id, is_default=True
        ).first()
        if default:
            return default.tenant
        # Fallback: Erster aktiver Tenant
        first = TenantMembership.query.filter_by(user_id=self.id).first()
        return first.tenant if first else None
    
    def get_role_in_tenant(self, tenant_id=None):
        """Rolle des Users im Tenant"""
        tid = tenant_id or self.current_tenant_id
        if not tid:
            return None
        membership = TenantMembership.query.filter_by(
            user_id=self.id, tenant_id=tid
        ).first()
        return membership.role if membership else None
    
    def is_tenant_admin(self, tenant_id=None):
        """Ist User Admin in diesem Tenant?"""
        return self.get_role_in_tenant(tenant_id) == 'admin'
    
    def can_access_tenant(self, tenant_id):
        """Darf User auf diesen Tenant zugreifen?"""
        if self.is_superadmin:
            return True
        return TenantMembership.query.filter_by(
            user_id=self.id, tenant_id=tenant_id
        ).first() is not None
```

### 3.3 Tenant-Middleware

#### 3.3.1 Request Context

```python
# middleware/tenant.py

from flask import g, session, redirect, url_for, flash
from functools import wraps
from models import Tenant, TenantMembership

def load_tenant_context():
    """Lädt Tenant-Kontext für jeden Request"""
    g.tenant = None
    g.tenant_role = None
    
    if not current_user.is_authenticated:
        return
    
    # Super-Admin kann jeden Tenant sehen
    if current_user.is_superadmin:
        tenant_id = session.get('current_tenant_id') or current_user.current_tenant_id
        if tenant_id:
            g.tenant = Tenant.query.get(tenant_id)
        return
    
    # Normaler User: Tenant aus Session oder Default
    tenant_id = session.get('current_tenant_id')
    
    if tenant_id:
        # Prüfen ob User noch Zugriff hat
        if current_user.can_access_tenant(tenant_id):
            g.tenant = Tenant.query.get(tenant_id)
            g.tenant_role = current_user.get_role_in_tenant(tenant_id)
        else:
            # Kein Zugriff mehr, zurück zum Default
            session.pop('current_tenant_id', None)
            tenant_id = None
    
    if not tenant_id:
        # Default-Tenant setzen
        default = current_user.default_tenant
        if default:
            g.tenant = default
            session['current_tenant_id'] = default.id
            g.tenant_role = current_user.get_role_in_tenant(default.id)


def tenant_required(f):
    """Decorator: Route erfordert aktiven Tenant-Kontext"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.tenant:
            flash('Bitte wählen Sie einen Mandanten aus.', 'warning')
            return redirect(url_for('select_tenant'))
        if not g.tenant.is_active and not current_user.is_superadmin:
            flash('Dieser Mandant ist deaktiviert.', 'error')
            return redirect(url_for('select_tenant'))
        return f(*args, **kwargs)
    return decorated_function


def tenant_admin_required(f):
    """Decorator: Route erfordert Tenant-Admin-Rolle"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.tenant:
            flash('Kein Mandant ausgewählt.', 'warning')
            return redirect(url_for('select_tenant'))
        if g.tenant_role != 'admin' and not current_user.is_superadmin:
            flash('Sie benötigen Admin-Rechte für diese Aktion.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    """Decorator: Route nur für Super-Admins"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_superadmin:
            flash('Diese Funktion ist nur für System-Administratoren.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
```

#### 3.3.2 Query Scoping

```python
# middleware/tenant_scoping.py

from flask import g
from sqlalchemy import event
from sqlalchemy.orm import Query

class TenantQuery(Query):
    """Automatisch gefilterter Query für Tenant-Isolation"""
    
    def __init__(self, entities, session=None):
        super().__init__(entities, session)
        # Automatischer Tenant-Filter
        if hasattr(g, 'tenant') and g.tenant:
            for entity in entities:
                if hasattr(entity, 'tenant_id'):
                    self = self.filter(entity.tenant_id == g.tenant.id)


# Alternativ: Event-basierter Ansatz
def apply_tenant_filter(query):
    """Filter für Tenant-Isolation"""
    if not hasattr(g, 'tenant') or not g.tenant:
        return query
    
    # Prüfe ob Model tenant_id hat
    mapper = query.column_descriptions[0]['entity']
    if hasattr(mapper, 'tenant_id'):
        query = query.filter(mapper.tenant_id == g.tenant.id)
    
    return query


# Mixin für tenant-aware Models
class TenantMixin:
    """Mixin für Models die einem Tenant gehören"""
    
    @declared_attr
    def tenant_id(cls):
        return db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)
    
    @classmethod
    def query_for_tenant(cls):
        """Query gefiltert nach aktuellem Tenant"""
        if hasattr(g, 'tenant') and g.tenant:
            return cls.query.filter_by(tenant_id=g.tenant.id)
        return cls.query.filter(False)  # Keine Ergebnisse ohne Tenant
```

### 3.4 Routes & API

#### 3.4.1 Tenant-Wechsel Endpoint

```python
# routes/tenant.py

@app.route('/switch-tenant/<int:tenant_id>', methods=['POST'])
@login_required
def switch_tenant(tenant_id):
    """Wechselt den aktiven Tenant"""
    
    # Zugriffsprüfung
    if not current_user.can_access_tenant(tenant_id):
        flash('Kein Zugriff auf diesen Mandanten.', 'error')
        return redirect(url_for('dashboard'))
    
    tenant = Tenant.query.get_or_404(tenant_id)
    
    if not tenant.is_active and not current_user.is_superadmin:
        flash('Dieser Mandant ist deaktiviert.', 'error')
        return redirect(url_for('dashboard'))
    
    # Tenant in Session speichern
    session['current_tenant_id'] = tenant_id
    current_user.current_tenant_id = tenant_id
    db.session.commit()
    
    # Audit-Log
    log_audit('tenant_switch', f'Wechsel zu Mandant: {tenant.name}')
    
    flash(f'Gewechselt zu: {tenant.name}', 'success')
    return redirect(url_for('dashboard'))


@app.route('/select-tenant')
@login_required
def select_tenant():
    """Tenant-Auswahl Seite (wenn kein Tenant aktiv)"""
    tenants = current_user.tenants
    
    if len(tenants) == 1:
        # Nur ein Tenant: Automatisch wechseln
        return redirect(url_for('switch_tenant', tenant_id=tenants[0].id))
    
    return render_template('select_tenant.html', tenants=tenants)
```

#### 3.4.2 Super-Admin Routes

```python
# routes/admin/tenants.py

@admin_bp.route('/tenants')
@login_required
@superadmin_required
def tenant_list():
    """Liste aller Tenants"""
    tenants = Tenant.query.order_by(Tenant.name).all()
    return render_template('admin/tenants/list.html', tenants=tenants)


@admin_bp.route('/tenants/new', methods=['GET', 'POST'])
@login_required
@superadmin_required
def tenant_create():
    """Neuen Tenant erstellen"""
    if request.method == 'POST':
        tenant = Tenant(
            name=request.form['name'],
            slug=slugify(request.form['slug']),
            primary_color=request.form.get('primary_color', '#0076A8'),
            created_by_id=current_user.id
        )
        db.session.add(tenant)
        
        # Initialen Admin zuweisen
        if request.form.get('admin_user_id'):
            membership = TenantMembership(
                tenant=tenant,
                user_id=request.form['admin_user_id'],
                role='admin',
                is_default=True,
                invited_by_id=current_user.id
            )
            db.session.add(membership)
        
        db.session.commit()
        flash(f'Mandant "{tenant.name}" erstellt.', 'success')
        return redirect(url_for('admin.tenant_list'))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('admin/tenants/form.html', users=users)


@admin_bp.route('/tenants/<int:tenant_id>/members')
@login_required
@superadmin_required
def tenant_members(tenant_id):
    """User-Verwaltung für einen Tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    memberships = TenantMembership.query.filter_by(tenant_id=tenant_id).all()
    available_users = User.query.filter(
        ~User.id.in_([m.user_id for m in memberships])
    ).all()
    
    return render_template('admin/tenants/members.html',
        tenant=tenant,
        memberships=memberships,
        available_users=available_users
    )


@admin_bp.route('/tenants/<int:tenant_id>/enter')
@login_required
@superadmin_required
def tenant_enter(tenant_id):
    """Als Super-Admin in Tenant wechseln"""
    tenant = Tenant.query.get_or_404(tenant_id)
    session['current_tenant_id'] = tenant_id
    session['superadmin_mode'] = True  # Merker für UI
    flash(f'Sie arbeiten jetzt als Super-Admin in: {tenant.name}', 'info')
    return redirect(url_for('dashboard'))
```

### 3.5 Template Integration

#### 3.5.1 Tenant-Switcher Component

```html
<!-- templates/components/tenant_switcher.html -->

{% if current_user.is_authenticated %}
<div class="dropdown tenant-switcher">
    <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center gap-2" 
            type="button" data-bs-toggle="dropdown">
        {% if g.tenant %}
            {% if g.tenant.logo_url %}
                <img src="{{ g.tenant.logo_url }}" alt="" class="tenant-logo" height="20">
            {% else %}
                <i class="bi bi-building"></i>
            {% endif %}
            <span class="d-none d-md-inline">{{ g.tenant.name }}</span>
        {% else %}
            <i class="bi bi-building-add"></i>
            <span>{{ 'Mandant wählen' if lang == 'de' else 'Select Client' }}</span>
        {% endif %}
    </button>
    
    <ul class="dropdown-menu dropdown-menu-end">
        {% if session.get('superadmin_mode') %}
            <li class="dropdown-header text-warning">
                <i class="bi bi-shield-check me-1"></i>Super-Admin Modus
            </li>
            <li><hr class="dropdown-divider"></li>
        {% endif %}
        
        {% for tenant in current_user.tenants %}
            <li>
                <form action="{{ url_for('switch_tenant', tenant_id=tenant.id) }}" method="POST">
                    <button type="submit" class="dropdown-item d-flex align-items-center gap-2
                        {{ 'active' if g.tenant and g.tenant.id == tenant.id }}">
                        {% if g.tenant and g.tenant.id == tenant.id %}
                            <i class="bi bi-check-lg text-success"></i>
                        {% else %}
                            <i class="bi bi-circle"></i>
                        {% endif %}
                        {{ tenant.name }}
                    </button>
                </form>
            </li>
        {% endfor %}
        
        {% if current_user.is_superadmin %}
            <li><hr class="dropdown-divider"></li>
            <li>
                <a class="dropdown-item" href="{{ url_for('admin.tenant_list') }}">
                    <i class="bi bi-gear me-2"></i>{{ 'Mandanten verwalten' if lang == 'de' else 'Manage Clients' }}
                </a>
            </li>
        {% endif %}
    </ul>
</div>
{% endif %}
```

#### 3.5.2 Base Template Anpassung

```html
<!-- templates/base.html - Navbar Erweiterung -->

<nav class="navbar navbar-expand-lg navbar-dark bg-company-green">
    <div class="container-fluid">
        <!-- Logo -->
        <a class="navbar-brand" href="{{ url_for('index') }}">
            <img src="{{ url_for('static', filename='logo.svg') }}" height="30">
        </a>
        
        <!-- Navigation Links (nur wenn Tenant aktiv) -->
        {% if g.tenant %}
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('calendar') }}">Kalender</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('projects.project_list') }}">Projekte</a>
                </li>
            </ul>
        {% endif %}
        
        <!-- Right Side -->
        <div class="d-flex align-items-center gap-3">
            <!-- Tenant Switcher -->
            {% include 'components/tenant_switcher.html' %}
            
            <!-- User Menu -->
            {% include 'components/user_menu.html' %}
        </div>
    </div>
</nav>

<!-- Tenant-Kontext Banner (Super-Admin) -->
{% if session.get('superadmin_mode') and g.tenant %}
<div class="alert alert-warning rounded-0 mb-0 py-1 text-center">
    <small>
        <i class="bi bi-shield-exclamation me-1"></i>
        Super-Admin Modus: {{ g.tenant.name }}
        <a href="{{ url_for('admin.tenant_list') }}" class="ms-2">
            <i class="bi bi-x-circle"></i> Beenden
        </a>
    </small>
</div>
{% endif %}
```

---

## 4. Migration & Datenbank

### 4.1 Migrationsschritte

```python
# migrations/versions/xxx_add_multi_tenancy.py

"""Add multi-tenancy support

Revision ID: mt001_multi_tenancy
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Tenant Tabelle erstellen
    op.create_table('tenant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('logo_url', sa.String(255)),
        sa.Column('primary_color', sa.String(7), default='#0076A8'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('settings', sa.JSON()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('user.id')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # 2. TenantMembership Tabelle
    op.create_table('tenant_membership',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, default='member'),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('joined_at', sa.DateTime()),
        sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('user.id')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', name='unique_tenant_user')
    )
    op.create_index('idx_tenant_membership_user', 'tenant_membership', ['user_id'])
    op.create_index('idx_tenant_membership_tenant', 'tenant_membership', ['tenant_id'])
    
    # 3. User erweitern
    op.add_column('user', sa.Column('is_superadmin', sa.Boolean(), default=False))
    op.add_column('user', sa.Column('current_tenant_id', sa.Integer(), sa.ForeignKey('tenant.id')))
    
    # 4. Alle tenant-aware Tabellen erweitern
    tenant_tables = [
        'entity', 'team', 'tax_type', 'task_preset', 'task', 
        'notification', 'project', 'issue', 'sprint'
    ]
    for table in tenant_tables:
        op.add_column(table, sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.id')))
        op.create_index(f'idx_{table}_tenant', table, ['tenant_id'])


def downgrade():
    # Rückgängig machen in umgekehrter Reihenfolge
    tenant_tables = [
        'entity', 'team', 'tax_type', 'task_preset', 'task',
        'notification', 'project', 'issue', 'sprint'
    ]
    for table in tenant_tables:
        op.drop_index(f'idx_{table}_tenant', table)
        op.drop_column(table, 'tenant_id')
    
    op.drop_column('user', 'current_tenant_id')
    op.drop_column('user', 'is_superadmin')
    op.drop_table('tenant_membership')
    op.drop_table('tenant')
```

### 4.2 Daten-Bereinigung

```python
# scripts/clear_existing_data.py

"""Löscht alle bestehenden Daten vor Multi-Tenancy"""

def clear_all_data():
    """ACHTUNG: Löscht ALLE Daten außer System-Tabellen"""
    
    # Reihenfolge wichtig wegen Foreign Keys
    tables_to_clear = [
        'issue_activity',
        'issue_comment', 
        'issue_attachment',
        'issue_link',
        'issue_worklog',
        'issue_reviewer',
        'issue',
        'sprint',
        'project_member',
        'project',
        'comment',
        'task_evidence',
        'task_reviewer',
        'task',
        'task_preset',
        'team_members',
        'team',
        'entity_user_access',
        'entity',
        'tax_type',
        'notification',
        'audit_log',
    ]
    
    for table in tables_to_clear:
        db.session.execute(f'DELETE FROM {table}')
    
    db.session.commit()
    print(f"Cleared {len(tables_to_clear)} tables")
```

---

## 5. Demo-Daten

### 5.1 Demo-Tenants

```python
# scripts/create_demo_tenants.py

DEMO_TENANTS = [
    {
        'name': 'Demo Corporation',
        'slug': 'democorp',
        'primary_color': '#86BC25',
        'description': 'Interner Demo-Mandant für Demo Corporation',
    },
    {
        'name': 'Mustermann GmbH',
        'slug': 'mustermann',
        'primary_color': '#0076A8',
        'description': 'Beispiel-Mandant für Kundenpräsentationen',
    },
    {
        'name': 'Innovation AG',
        'slug': 'innovation-ag',
        'primary_color': '#E31937',
        'description': 'Zweiter Demo-Mandant',
    }
]

def create_demo_tenants():
    for data in DEMO_TENANTS:
        tenant = Tenant(
            name=data['name'],
            slug=data['slug'],
            primary_color=data['primary_color'],
            settings={'description': data['description']},
            is_active=True
        )
        db.session.add(tenant)
    
    db.session.commit()
```

### 5.2 Demo-User

```python
DEMO_USERS = [
    # Super-Admin (alle Tenants)
    {
        'email': 'admin@projectops.de',
        'name': 'System Administrator',
        'password': 'admin123',
        'is_superadmin': True,
        'tenants': []  # Superadmin braucht keine Memberships
    },
    
    # Demo Corporation Users
    {
        'email': 'maria.mueller@democorp.local',
        'name': 'Maria Müller',
        'password': 'demo123',
        'tenants': [
            {'slug': 'democorp', 'role': 'admin', 'is_default': True}
        ]
    },
    {
        'email': 'thomas.schmidt@democorp.local',
        'name': 'Thomas Schmidt',
        'password': 'demo123',
        'tenants': [
            {'slug': 'democorp', 'role': 'manager'}
        ]
    },
    
    # Mustermann Users
    {
        'email': 'anna.mustermann@example.de',
        'name': 'Anna Mustermann',
        'password': 'demo123',
        'tenants': [
            {'slug': 'mustermann', 'role': 'admin', 'is_default': True}
        ]
    },
    {
        'email': 'max.mustermann@example.de',
        'name': 'Max Mustermann',
        'password': 'demo123',
        'tenants': [
            {'slug': 'mustermann', 'role': 'member'}
        ]
    },
    
    # Multi-Tenant User (für Demo von Tenant-Wechsel)
    {
        'email': 'berater@democorp.local',
        'name': 'Klaus Berater',
        'password': 'demo123',
        'tenants': [
            {'slug': 'democorp', 'role': 'manager', 'is_default': True},
            {'slug': 'mustermann', 'role': 'viewer'},
            {'slug': 'innovation-ag', 'role': 'member'}
        ]
    }
]
```

### 5.3 Demo-Daten pro Tenant

```python
def create_demo_data_for_tenant(tenant):
    """Erstellt Demo-Daten für einen Tenant"""
    
    # Entities
    entities = [
        Entity(name='Hauptverwaltung', tenant_id=tenant.id),
        Entity(name='Niederlassung Nord', tenant_id=tenant.id),
        Entity(name='Niederlassung Süd', tenant_id=tenant.id),
    ]
    
    # Teams
    teams = [
        Team(name='Steuerteam', color='#0076A8', tenant_id=tenant.id),
        Team(name='Buchhaltung', color='#86BC25', tenant_id=tenant.id),
    ]
    
    # TaxTypes
    tax_types = [
        TaxType(name='Körperschaftsteuer', code='KSt', tenant_id=tenant.id),
        TaxType(name='Gewerbesteuer', code='GewSt', tenant_id=tenant.id),
        TaxType(name='Umsatzsteuer', code='USt', tenant_id=tenant.id),
    ]
    
    # Projects (mit Issues)
    projects = [
        create_demo_project(tenant, 'Q1 2026 Reporting', 'scrum'),
        create_demo_project(tenant, 'Jahresabschluss 2025', 'waterfall'),
    ]
    
    # Tasks
    tasks = create_demo_tasks(tenant, entities, tax_types)
    
    db.session.add_all(entities + teams + tax_types + projects + tasks)
    db.session.commit()
```

---

## 6. Sicherheit

### 6.1 Security Checklist

| Prüfung | Implementierung | Status |
|---------|-----------------|--------|
| Tenant-Isolation in allen Queries | TenantMixin + Middleware | ⏳ |
| Zugriffsprüfung bei Tenant-Wechsel | `can_access_tenant()` | ⏳ |
| Super-Admin Audit-Logging | Alle Admin-Aktionen loggen | ⏳ |
| CSRF-Schutz bei Tenant-Wechsel | POST-only + CSRF-Token | ⏳ |
| Rate-Limiting für Tenant-API | Flask-Limiter | ⏳ |
| Session-Invalidierung bei Tenant-Deaktivierung | Signal/Hook | ⏳ |

### 6.2 Audit-Log Erweiterung

```python
# Neue Audit-Typen für Multi-Tenancy
AUDIT_TYPES = [
    'tenant_created',
    'tenant_updated', 
    'tenant_deactivated',
    'tenant_deleted',
    'tenant_member_added',
    'tenant_member_removed',
    'tenant_member_role_changed',
    'tenant_switch',
    'superadmin_enter_tenant',
]
```

---

## 7. Implementierungsplan

### Phase 1: Foundation (Tag 1)
- [ ] Tenant + TenantMembership Models
- [ ] Migration erstellen und ausführen
- [ ] User-Erweiterung (is_superadmin, current_tenant_id)
- [ ] Bestehende Daten löschen

### Phase 2: Middleware & Security (Tag 1-2)
- [ ] Tenant-Context Middleware
- [ ] Decorators (tenant_required, superadmin_required)
- [ ] Query-Scoping für alle Models
- [ ] Tenant-ID zu allen Models hinzufügen

### Phase 3: Super-Admin UI (Tag 2)
- [ ] Tenant-Liste
- [ ] Tenant erstellen/bearbeiten
- [ ] Tenant aktivieren/deaktivieren
- [ ] User-Tenant-Zuordnung

### Phase 4: Tenant-Switcher (Tag 2-3)
- [ ] Switcher-Komponente
- [ ] Wechsel-Route
- [ ] Session-Handling
- [ ] Base-Template Integration

### Phase 5: Demo-Daten (Tag 3)
- [ ] Demo-Tenants erstellen
- [ ] Demo-User mit Memberships
- [ ] Demo-Daten pro Tenant
- [ ] CLI-Commands für Setup

### Phase 6: Testing & Fixes (Tag 3-4)
- [ ] Alle bestehenden Routes prüfen
- [ ] Cross-Tenant Isolation testen
- [ ] Edge-Cases behandeln
- [ ] Performance-Optimierung

---

## 8. Design-Entscheidungen

### 8.1 Tenant-Löschung: Soft-Delete mit Archiv ✅

| Aktion | Wer | Beschreibung |
|--------|-----|--------------|
| Archivieren | Tenant-Admin | Tenant wird deaktiviert, Daten bleiben erhalten |
| Endgültig löschen | Super-Admin | Nur aus dem Archiv, mit Bestätigung |
| Wiederherstellen | Super-Admin | Archivierter Tenant kann reaktiviert werden |

```python
class Tenant(db.Model):
    # Status-Felder
    is_active = db.Column(db.Boolean, default=True)
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    archived_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

### 8.2 Daten-Export: JSON + ZIP ✅

Export-Format für Dokumentation und Archivierung:

```
tenant_export_2026-01-03/
├── manifest.json           # Metadaten, Version, Exportdatum
├── tenant.json             # Tenant-Konfiguration
├── users.json              # User + Memberships
├── entities.json           # Mandanten/Gesellschaften
├── teams.json              # Teams + Mitglieder
├── projects/
│   ├── project_1.json      # Projekt + Issues + Sprints
│   └── project_2.json
├── tasks/
│   ├── tasks.json          # Alle Tasks
│   └── attachments/        # Task-Anhänge
├── tax_types.json          # Steuerarten
└── audit_log.json          # Audit-Trail
```

**Features:**
- Vollständiger Export aller Tenant-Daten
- Zeitstempel und Versionierung
- Kann für Migration oder Backup genutzt werden
- Import-Funktion für Wiederherstellung (optional)

### 8.3 Logo-Speicherung: Database (Base64) ✅

```python
class Tenant(db.Model):
    logo_data = db.Column(db.Text)           # Base64-encoded image
    logo_mime_type = db.Column(db.String(50))  # z.B. 'image/png'
```

**Vorteile:**
- Keine separate Datei-Infrastruktur nötig
- Backup inkludiert Logo automatisch
- Einfache Migration
- Limit: max 500KB pro Logo

### 8.4 Email-Domain-Mapping: Nicht implementiert ❌

Manuelle Zuordnung durch Super-Admin ist ausreichend.
Kann später als Feature ergänzt werden wenn gewünscht.

### 8.5 API-Keys pro Tenant: Vorgesehen ✅

Ermöglicht externe Integrationen:

| Integration | Verwendung |
|-------------|------------|
| DATEV | Automatischer Datenimport |
| SAP | Steuertermine synchronisieren |
| Zapier/Power Automate | Workflow-Automatisierung |
| Mobile Apps | REST-API Zugriff |
| Reporting-Tools | Daten exportieren |
| Kalendersysteme | iCal-Export mit Auth |

```python
class TenantApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    name = db.Column(db.String(100))          # z.B. "DATEV Integration"
    key_hash = db.Column(db.String(128))      # SHA-256 Hash
    key_prefix = db.Column(db.String(8))      # Erste 8 Zeichen für Anzeige
    scopes = db.Column(db.JSON)               # ['read:tasks', 'write:tasks']
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
```

**Hinweis:** API-Key-System wird in Phase 2 implementiert (nach Core Multi-Tenancy).

---

## 9. Erweiterte Features

### 9.1 Tenant-Archiv UI (Super-Admin)

```
┌─────────────────────────────────────────────────────────────────┐
│ ADMIN > ARCHIVIERTE MANDANTEN                                   │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🗄️ Alte Firma GmbH                                          │ │
│ │ ─────────────────────────────────────────────────────────── │ │
│ │ Archiviert: 2025-12-15 von Admin                           │ │
│ │ Daten: 5 User, 12 Projekte, 234 Tasks                      │ │
│ │                                                             │ │
│ │ [📥 Exportieren]  [♻️ Wiederherstellen]  [🗑️ Endgültig löschen] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ⚠️ Endgültiges Löschen entfernt alle Daten unwiderruflich!     │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Export-Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│ TENANT EXPORTIEREN: Mustermann GmbH                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Exportieren:                                                    │
│   ☑️ Tenant-Konfiguration                                       │
│   ☑️ User & Berechtigungen                                      │
│   ☑️ Entities & Teams                                           │
│   ☑️ Projekte & Issues                                          │
│   ☑️ Tasks & Termine                                            │
│   ☑️ Anhänge & Dateien                                          │
│   ☐ Audit-Log (optional)                                        │
│                                                                 │
│ Format:                                                         │
│   ○ JSON (strukturiert, für Re-Import)                         │
│   ● ZIP mit JSON (komprimiert, empfohlen)                      │
│   ○ Excel (nur Basisdaten)                                     │
│                                                                 │
│                           [Abbrechen]  [📥 Export starten]      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Anhang

### A. Glossar

| Begriff | Definition |
|---------|------------|
| Tenant | Ein Mandant/Client mit eigener Datenpartition |
| Super-Admin | Systemweiter Administrator (sieht alle Tenants) |
| Tenant-Admin | Administrator eines einzelnen Mandanten |
| Membership | Zuordnung eines Users zu einem Tenant |
| Tenant-Scope | Automatische Filterung auf aktuellen Tenant |

### B. Referenzen

- Flask Multi-Tenancy Patterns
- SQLAlchemy Query Filtering
- Enterprise SaaS Architecture
