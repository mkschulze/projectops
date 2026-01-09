"""
Deloitte ProjectOps - Database Models
"""
from datetime import datetime, date
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib

from extensions import db


# ============================================================================
# MULTI-TENANCY MODELS
# ============================================================================

class TenantRole(Enum):
    """Roles within a tenant"""
    ADMIN = 'admin'      # Full access to tenant settings and all data
    MANAGER = 'manager'  # Can manage projects, tasks, users within tenant
    MEMBER = 'member'    # Standard user, can work on assigned items
    VIEWER = 'viewer'    # Read-only access
    
    @classmethod
    def choices(cls):
        return [(role.value, role.name.title()) for role in cls]


class Tenant(db.Model):
    """Mandant/Client for Multi-Tenancy"""
    __tablename__ = 'tenant'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Branding
    logo_data = db.Column(db.Text)  # Base64-encoded image (max 500KB)
    logo_mime_type = db.Column(db.String(50))  # e.g., 'image/png'
    primary_color = db.Column(db.String(7), default='#0076A8')
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    archived_at = db.Column(db.DateTime)
    archived_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Settings (JSON for flexible config)
    settings = db.Column(db.JSON, default=dict)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    memberships = db.relationship('TenantMembership', back_populates='tenant',
                                   cascade='all, delete-orphan')
    api_keys = db.relationship('TenantApiKey', back_populates='tenant',
                                cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    archived_by = db.relationship('User', foreign_keys=[archived_by_id])
    
    @property
    def members(self):
        """All users of this tenant"""
        return [m.user for m in self.memberships]
    
    @property
    def admin_users(self):
        """All admins of this tenant"""
        return [m.user for m in self.memberships if m.role == 'admin']
    
    @property
    def member_count(self):
        """Number of members"""
        return len(self.memberships)
    
    def get_member_role(self, user):
        """Get role of a user in this tenant"""
        membership = TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).first()
        return membership.role if membership else None
    
    def has_member(self, user):
        """Check if user is member"""
        return TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).first() is not None
    
    def add_member(self, user, role='member', invited_by=None, is_default=False):
        """Add a user to this tenant"""
        existing = TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).first()
        if existing:
            return existing
        
        membership = TenantMembership(
            tenant_id=self.id,
            user_id=user.id,
            role=role,
            is_default=is_default,
            invited_by_id=invited_by.id if invited_by else None
        )
        db.session.add(membership)
        return membership
    
    def remove_member(self, user):
        """Remove a user from this tenant"""
        TenantMembership.query.filter_by(
            tenant_id=self.id, user_id=user.id
        ).delete()
    
    def archive(self, user):
        """Archive this tenant (soft-delete)"""
        self.is_archived = True
        self.is_active = False
        self.archived_at = datetime.utcnow()
        self.archived_by_id = user.id if user else None
    
    def restore(self):
        """Restore tenant from archive"""
        self.is_archived = False
        self.is_active = True
        self.archived_at = None
        self.archived_by_id = None
    
    def __repr__(self):
        return f'<Tenant {self.name}>'


class TenantMembership(db.Model):
    """User-Tenant assignment with role"""
    __tablename__ = 'tenant_membership'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='member')  # admin, manager, member, viewer
    is_default = db.Column(db.Boolean, default=False)  # Default tenant on login
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
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager_or_above(self):
        return self.role in ('admin', 'manager')
    
    def can_edit(self):
        return self.role in ('admin', 'manager', 'member')
    
    def __repr__(self):
        return f'<TenantMembership {self.user_id}@{self.tenant_id} ({self.role})>'


class TenantApiKey(db.Model):
    """API Keys for external integrations per tenant"""
    __tablename__ = 'tenant_api_key'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "DATEV Integration"
    key_hash = db.Column(db.String(128), nullable=False)  # SHA-256 hash
    key_prefix = db.Column(db.String(8), nullable=False)  # First 8 chars for display
    scopes = db.Column(db.JSON, default=list)  # ['read:tasks', 'write:tasks']
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    tenant = db.relationship('Tenant', back_populates='api_keys')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    @classmethod
    def generate_key(cls):
        """Generate a new API key (returns plaintext key, only shown once)"""
        key = secrets.token_urlsafe(32)
        return key
    
    @classmethod
    def hash_key(cls, key):
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def verify_key(self, key):
        """Verify a plaintext key against stored hash"""
        return self.key_hash == self.hash_key(key)
    
    def is_expired(self):
        """Check if key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def record_usage(self):
        """Record API key usage"""
        self.last_used_at = datetime.utcnow()
    
    def has_scope(self, scope):
        """Check if key has specific scope"""
        if not self.scopes:
            return False
        return scope in self.scopes or '*' in self.scopes
    
    def __repr__(self):
        return f'<TenantApiKey {self.key_prefix}... for Tenant {self.tenant_id}>'


# ============================================================================
# ASSOCIATION TABLES
# ============================================================================

# Team membership association table
team_members = db.Table('team_members',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow),
    db.Column('is_team_lead', db.Boolean, default=False)
)


class EntityAccessLevel(Enum):
    """Access level for entity permissions"""
    VIEW = 'view'       # Can view tasks for this entity
    EDIT = 'edit'       # Can create/edit tasks for this entity
    MANAGE = 'manage'   # Full access including reassign, delete
    
    @classmethod
    def choices(cls):
        return [(level.value, level.name.title()) for level in cls]


class UserEntity(db.Model):
    """Association table for User-Entity permissions with access level"""
    __tablename__ = 'user_entity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    access_level = db.Column(db.String(20), default='view')  # view, edit, manage
    inherit_to_children = db.Column(db.Boolean, default=True)  # Inherit access to child entities
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='entity_permissions')
    entity = db.relationship('Entity', backref='user_permissions')
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'entity_id', name='unique_user_entity'),
    )
    
    def can_view(self):
        return self.access_level in ['view', 'edit', 'manage']
    
    def can_edit(self):
        return self.access_level in ['edit', 'manage']
    
    def can_manage(self):
        return self.access_level == 'manage'
    
    def __repr__(self):
        return f'<UserEntity {self.user_id}:{self.entity_id}:{self.access_level}>'


class TaskReviewer(db.Model):
    """Association table for Task-Reviewer many-to-many with approval tracking"""
    __tablename__ = 'task_reviewer'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
    user = db.relationship('User', backref='reviewer_assignments')
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='unique_task_reviewer'),
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
    def decision(self):
        """Get the reviewer's decision status"""
        if self.has_approved:
            return 'approved'
        elif self.has_rejected:
            return 'rejected'
        return 'pending'
    
    @property
    def decided_at(self):
        """Get the timestamp when decision was made"""
        if self.has_approved:
            return self.approved_at
        elif self.has_rejected:
            return self.rejected_at
        return None
    
    @property
    def note(self):
        """Get the decision note"""
        if self.has_approved:
            return self.approval_note
        elif self.has_rejected:
            return self.rejection_note
        return None


# ============================================================================
# ENUMS
# ============================================================================

class TaskStatus(Enum):
    """Task status enumeration"""
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    IN_REVIEW = 'in_review'
    COMPLETED = 'completed'
    
    @classmethod
    def choices(cls):
        return [(status.value, status.name.replace('_', ' ').title()) for status in cls]


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    REVIEWER = 'reviewer'
    PREPARER = 'preparer'
    READONLY = 'readonly'
    
    @classmethod
    def choices(cls):
        return [(role.value, role.name.title()) for role in cls]


class EvidenceType(Enum):
    """Evidence type enumeration"""
    FILE = 'file'
    LINK = 'link'


class RecurrenceType(Enum):
    """Task recurrence type"""
    NONE = 'none'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    ANNUAL = 'annual'


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='preparer')  # admin, manager, reviewer, preparer, readonly
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    calendar_token = db.Column(db.String(64), unique=True, index=True)  # Token for iCal feed access
    
    # Multi-Tenancy fields
    is_superadmin = db.Column(db.Boolean, default=False, index=True)  # System-wide admin
    current_tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)
    
    # Email notification preferences (JSON field)
    email_notifications = db.Column(db.Boolean, default=True)  # Master switch
    email_on_assignment = db.Column(db.Boolean, default=True)
    email_on_status_change = db.Column(db.Boolean, default=True)
    email_on_due_reminder = db.Column(db.Boolean, default=True)
    email_on_comment = db.Column(db.Boolean, default=False)  # Off by default (can be noisy)
    
    # Relationships
    owned_tasks = db.relationship('Task', foreign_keys='Task.owner_id', backref='owner', lazy='dynamic')
    reviewed_tasks = db.relationship('Task', foreign_keys='Task.reviewer_id', backref='reviewer', lazy='dynamic')
    current_tenant = db.relationship('Tenant', foreign_keys=[current_tenant_id])
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_manager(self):
        """Check if user has manager role"""
        return self.role in ('admin', 'manager')
    
    def can_review(self):
        """Check if user can review tasks"""
        return self.role in ('admin', 'manager', 'reviewer')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_teams(self):
        """Get all teams this user belongs to"""
        return Team.query.filter(Team.members.contains(self)).all()
    
    def get_or_create_calendar_token(self):
        """Get existing calendar token or create a new one"""
        if not self.calendar_token:
            import secrets
            self.calendar_token = secrets.token_urlsafe(32)
            db.session.commit()
        return self.calendar_token
    
    def regenerate_calendar_token(self):
        """Generate a new calendar token (invalidates old subscription URLs)"""
        import secrets
        self.calendar_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.calendar_token
    
    # =========================================================================
    # MULTI-TENANCY METHODS
    # =========================================================================
    
    @property
    def tenants(self):
        """All active tenants this user belongs to"""
        return [m.tenant for m in self.tenant_memberships if m.tenant.is_active]
    
    @property
    def all_tenants(self):
        """All tenants (including inactive) this user belongs to"""
        return [m.tenant for m in self.tenant_memberships]
    
    @property
    def default_tenant(self):
        """Get default tenant for this user"""
        default = TenantMembership.query.filter_by(
            user_id=self.id, is_default=True
        ).first()
        if default and default.tenant.is_active:
            return default.tenant
        # Fallback: first active tenant
        for m in self.tenant_memberships:
            if m.tenant.is_active:
                return m.tenant
        return None
    
    def get_role_in_tenant(self, tenant_id=None):
        """Get role in specific tenant"""
        tid = tenant_id or self.current_tenant_id
        if not tid:
            return None
        membership = TenantMembership.query.filter_by(
            user_id=self.id, tenant_id=tid
        ).first()
        return membership.role if membership else None
    
    def is_tenant_admin(self, tenant_id=None):
        """Check if user is admin in tenant"""
        return self.get_role_in_tenant(tenant_id) == 'admin'
    
    def is_tenant_manager_or_above(self, tenant_id=None):
        """Check if user is manager or admin in tenant"""
        role = self.get_role_in_tenant(tenant_id)
        return role in ('admin', 'manager')
    
    def can_access_tenant(self, tenant_id):
        """Check if user can access tenant"""
        if self.is_superadmin:
            return True
        return TenantMembership.query.filter_by(
            user_id=self.id, tenant_id=tenant_id
        ).first() is not None
    
    def set_current_tenant(self, tenant_id):
        """Set current working tenant"""
        if self.can_access_tenant(tenant_id):
            self.current_tenant_id = tenant_id
            return True
        return False
    
    # =========================================================================
    # ENTITY ACCESS METHODS
    # =========================================================================
    
    def get_accessible_entities(self, min_level='view'):
        """
        Get all entities this user can access at the specified level or higher.
        Includes inherited access from parent entities.
        
        Args:
            min_level: Minimum access level required ('view', 'edit', 'manage')
        
        Returns:
            List of Entity objects
        """
        # Admins and managers can access all entities
        if self.is_admin() or self.is_manager():
            from models import Entity
            return Entity.query.filter_by(is_active=True).all()
        
        # Get direct permissions
        level_hierarchy = {'view': 0, 'edit': 1, 'manage': 2}
        min_level_num = level_hierarchy.get(min_level, 0)
        
        accessible_ids = set()
        
        for perm in self.entity_permissions:
            perm_level_num = level_hierarchy.get(perm.access_level, 0)
            if perm_level_num >= min_level_num:
                accessible_ids.add(perm.entity_id)
                
                # If inherit_to_children, add all child entities
                if perm.inherit_to_children:
                    self._add_child_entities(perm.entity, accessible_ids)
        
        if not accessible_ids:
            return []
        
        from models import Entity
        return Entity.query.filter(Entity.id.in_(accessible_ids), Entity.is_active == True).all()
    
    def _add_child_entities(self, entity, id_set):
        """Recursively add child entity IDs to the set"""
        for child in entity.children:
            id_set.add(child.id)
            self._add_child_entities(child, id_set)
    
    def get_accessible_entity_ids(self, min_level='view'):
        """Get IDs of accessible entities (for query filtering)"""
        return [e.id for e in self.get_accessible_entities(min_level)]
    
    def can_access_entity(self, entity_or_id, min_level='view'):
        """
        Check if user can access a specific entity at the given level.
        
        Args:
            entity_or_id: Entity object or entity ID
            min_level: Required access level
        
        Returns:
            bool
        """
        # Admins and managers have full access
        if self.is_admin() or self.is_manager():
            return True
        
        entity_id = entity_or_id if isinstance(entity_or_id, int) else entity_or_id.id
        accessible_ids = self.get_accessible_entity_ids(min_level)
        return entity_id in accessible_ids
    
    def get_entity_access_level(self, entity_or_id):
        """
        Get the access level for a specific entity.
        
        Returns:
            'manage', 'edit', 'view', or None
        """
        if self.is_admin() or self.is_manager():
            return 'manage'
        
        entity_id = entity_or_id if isinstance(entity_or_id, int) else entity_or_id.id
        
        # Check direct permission
        for perm in self.entity_permissions:
            if perm.entity_id == entity_id:
                return perm.access_level
        
        # Check inherited from parent
        from models import Entity
        entity = Entity.query.get(entity_id) if isinstance(entity_or_id, int) else entity_or_id
        if entity and entity.parent:
            parent_level = self.get_entity_access_level(entity.parent)
            if parent_level:
                # Check if parent permission allows inheritance
                for perm in self.entity_permissions:
                    if perm.entity_id == entity.parent.id and perm.inherit_to_children:
                        return parent_level
        
        return None


class Team(db.Model):
    """Team model for grouping users"""
    __tablename__ = 'team'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    name = db.Column(db.String(100), nullable=False)  # Internal identifier (unique per tenant)
    name_de = db.Column(db.String(100))  # German display name
    name_en = db.Column(db.String(100))  # English display name
    description = db.Column(db.Text)
    description_de = db.Column(db.Text)  # German description
    description_en = db.Column(db.Text)  # English description
    color = db.Column(db.String(7), default='#4A90D9')  # Brand color as default
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Manager of the team
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_teams')
    
    # Many-to-many relationship with users
    members = db.relationship('User', secondary=team_members, lazy='dynamic',
                             backref=db.backref('teams', lazy='dynamic'))
    
    # Tasks assigned to this team
    owned_tasks = db.relationship('Task', foreign_keys='Task.owner_team_id', backref='owner_team', lazy='dynamic')
    
    def add_member(self, user):
        """Add a user to this team"""
        if not self.is_member(user):
            self.members.append(user)
    
    def remove_member(self, user):
        """Remove a user from this team"""
        if self.is_member(user):
            self.members.remove(user)
    
    def is_member(self, user):
        """Check if user is a member of this team"""
        return self.members.filter_by(id=user.id).count() > 0
    
    def get_member_count(self):
        """Get number of team members"""
        return self.members.count()
    
    def get_name(self, lang='de'):
        """Get translated name based on language"""
        if lang == 'en' and self.name_en:
            return self.name_en
        if lang == 'de' and self.name_de:
            return self.name_de
        return self.name_de or self.name_en or self.name
    
    def get_description(self, lang='de'):
        """Get translated description based on language"""
        if lang == 'en' and self.description_en:
            return self.description_en
        if lang == 'de' and self.description_de:
            return self.description_de
        return self.description_de or self.description_en or self.description or ''
    
    def __repr__(self):
        return f'<Team {self.name}>'


class AuditLog(db.Model):
    """Audit log for tracking changes"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    entity_name = db.Column(db.String(200))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    # Relationships
    user = db.relationship('User', backref='audit_logs', lazy=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.entity_type}>'


# ============================================================================
# ADD YOUR CUSTOM MODELS BELOW
# ============================================================================


class Entity(db.Model):
    """Legal entity (Gesellschaft) for tax compliance"""
    __tablename__ = 'entity'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    name = db.Column(db.String(200), nullable=False)  # Internal identifier
    name_de = db.Column(db.String(200))  # German display name
    name_en = db.Column(db.String(200))  # English display name
    short_name = db.Column(db.String(50))
    country = db.Column(db.String(5), default='DE')  # ISO country code
    group_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for entity groups
    children = db.relationship('Entity', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    tasks = db.relationship('Task', backref='entity', lazy='dynamic')
    
    def get_name(self, lang='de'):
        """Get translated name based on language"""
        if lang == 'en' and self.name_en:
            return self.name_en
        if lang == 'de' and self.name_de:
            return self.name_de
        return self.name_de or self.name_en or self.name
    
    def __repr__(self):
        return f'<Entity {self.name}>'


class TaskCategory(db.Model):
    """Task category for organizing tasks (e.g., Tax types, Compliance, Reporting)"""
    __tablename__ = 'task_category'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    code = db.Column(db.String(20), nullable=False)  # KSt, USt, COMPL, etc. (unique per tenant)
    name = db.Column(db.String(100), nullable=False)  # Internal/legacy name
    name_de = db.Column(db.String(100))  # German display name
    name_en = db.Column(db.String(100))  # English display name
    description = db.Column(db.Text)  # Legacy description field
    description_de = db.Column(db.Text)  # German description
    description_en = db.Column(db.Text)  # English description
    is_active = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(7), default='#6c757d')  # Hex color for visual distinction
    icon = db.Column(db.String(50), default='bi-folder')  # Bootstrap icon class
    
    templates = db.relationship('TaskTemplate', backref='task_category', lazy='dynamic')
    
    def get_name(self, lang='de'):
        """Get translated name based on language"""
        if lang == 'en' and self.name_en:
            return self.name_en
        if lang == 'de' and self.name_de:
            return self.name_de
        return self.name_de or self.name_en or self.name
    
    def get_description(self, lang='de'):
        """Get translated description based on language"""
        if lang == 'en' and self.description_en:
            return self.description_en
        if lang == 'de' and self.description_de:
            return self.description_de
        return self.description_de or self.description_en or self.description or ''
    
    def __repr__(self):
        return f'<TaskCategory {self.code}>'


# Backward compatibility aliases
TaxType = TaskCategory
Category = TaskCategory  # Alias for code that uses Category


class TaskTemplate(db.Model):
    """Task template for generating recurring tasks"""
    __tablename__ = 'task_template'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('task_category.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)  # Short identifier
    description = db.Column(db.Text)
    default_recurrence = db.Column(db.String(20), default='annual')  # none, monthly, quarterly, annual
    default_due_day = db.Column(db.Integer, default=15)  # Day of month
    default_due_month_offset = db.Column(db.Integer, default=0)  # Months after period end
    source_row = db.Column(db.Integer)  # Row number from Excel import
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tasks = db.relationship('Task', backref='template', lazy='dynamic')
    
    def __repr__(self):
        return f'<TaskTemplate {self.keyword}>'


class CustomFieldType(Enum):
    """Types of custom fields for presets"""
    TEXT = 'text'
    TEXTAREA = 'textarea'
    NUMBER = 'number'
    DATE = 'date'
    SELECT = 'select'
    CHECKBOX = 'checkbox'
    
    @classmethod
    def choices(cls):
        return [(t.value, t.value.title()) for t in cls]


class PresetCustomField(db.Model):
    """Custom fields that can be added to presets for extended data collection"""
    __tablename__ = 'preset_custom_field'
    
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.Integer, db.ForeignKey('task_preset.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Internal field name (e.g., 'filing_deadline')
    label_de = db.Column(db.String(200), nullable=False)  # German label
    label_en = db.Column(db.String(200))  # English label
    field_type = db.Column(db.String(20), nullable=False, default='text')  # text, textarea, number, date, select, checkbox
    is_required = db.Column(db.Boolean, default=False)
    placeholder_de = db.Column(db.String(200))  # German placeholder
    placeholder_en = db.Column(db.String(200))  # English placeholder
    default_value = db.Column(db.String(500))  # Default value
    options = db.Column(db.Text)  # JSON array of options for select fields
    validation_regex = db.Column(db.String(200))  # Optional regex validation
    help_text_de = db.Column(db.Text)  # German help text
    help_text_en = db.Column(db.Text)  # English help text
    sort_order = db.Column(db.Integer, default=0)  # Display order
    
    # Conditional visibility
    condition_field = db.Column(db.String(100))  # Field name to check
    condition_operator = db.Column(db.String(20))  # 'equals', 'not_equals', 'contains'
    condition_value = db.Column(db.String(200))  # Value to compare
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    preset = db.relationship('TaskPreset', backref=db.backref('custom_fields', lazy='dynamic', order_by='PresetCustomField.sort_order'))
    
    def get_label(self, lang='de'):
        if lang == 'en' and self.label_en:
            return self.label_en
        return self.label_de
    
    def get_placeholder(self, lang='de'):
        if lang == 'en' and self.placeholder_en:
            return self.placeholder_en
        return self.placeholder_de or ''
    
    def get_help_text(self, lang='de'):
        if lang == 'en' and self.help_text_en:
            return self.help_text_en
        return self.help_text_de or ''
    
    def get_options_list(self):
        """Parse options JSON into list"""
        if not self.options:
            return []
        import json
        try:
            return json.loads(self.options)
        except:
            return []
    
    def __repr__(self):
        return f'<PresetCustomField {self.name}>'


class TaskCustomFieldValue(db.Model):
    """Stores custom field values for individual tasks"""
    __tablename__ = 'task_custom_field_value'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('preset_custom_field.id'), nullable=False)
    value = db.Column(db.Text)  # Stored as string, parsed based on field type
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', backref=db.backref('custom_field_values', lazy='dynamic'))
    field = db.relationship('PresetCustomField')
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'field_id', name='unique_task_field_value'),
    )
    
    def __repr__(self):
        return f'<TaskCustomFieldValue {self.field_id}={self.value[:20] if self.value else ""}>'


class TaskPreset(db.Model):
    """Predefined task templates for quick task creation (Aufgabenvorlagen)"""
    __tablename__ = 'task_preset'
    
    CATEGORIES = ['antrag', 'aufgabe']
    
    # Recurrence frequency options
    RECURRENCE_FREQUENCIES = [
        ('none', 'Keine Wiederholung'),
        ('monthly', 'Monatlich'),
        ('quarterly', 'Vierteljährlich'),
        ('semi_annual', 'Halbjährlich'),
        ('annual', 'Jährlich'),
        ('custom', 'Benutzerdefiniert (RRULE)')
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    category = db.Column(db.String(20), nullable=False, default='aufgabe')  # antrag, aufgabe
    tax_type = db.Column(db.String(100))  # Steuerart (free text, more flexible than FK)
    title = db.Column(db.String(300), nullable=False)  # Internal/legacy title
    title_de = db.Column(db.String(300))  # German title
    title_en = db.Column(db.String(300))  # English title
    law_reference = db.Column(db.String(100))  # § Paragraph (for Anträge)
    description = db.Column(db.Text)  # Legacy description field
    description_de = db.Column(db.Text)  # German description
    description_en = db.Column(db.Text)  # English description
    source = db.Column(db.String(50))  # Import source: 'json', 'excel', 'manual'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Recurrence fields
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_frequency = db.Column(db.String(20), default='none')  # monthly, quarterly, semi_annual, annual, custom
    recurrence_rrule = db.Column(db.String(500))  # Custom RRULE string for complex patterns
    recurrence_day_offset = db.Column(db.Integer, default=0)  # Days offset from period start (e.g., 10 = 10th of month)
    recurrence_end_date = db.Column(db.Date)  # Optional end date for recurrence
    last_generated_date = db.Column(db.Date)  # Last date for which tasks were generated
    default_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Default owner for generated tasks
    default_entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))  # Default entity for generated tasks
    
    # Relationships
    default_owner = db.relationship('User', foreign_keys=[default_owner_id])
    default_entity = db.relationship('Entity', foreign_keys=[default_entity_id])
    
    def get_title(self, lang='de'):
        """Get translated title based on language"""
        if lang == 'en' and self.title_en:
            return self.title_en
        if lang == 'de' and self.title_de:
            return self.title_de
        return self.title_de or self.title_en or self.title
    
    def get_description(self, lang='de'):
        """Get translated description based on language"""
        if lang == 'en' and self.description_en:
            return self.description_en
        if lang == 'de' and self.description_de:
            return self.description_de
        return self.description_de or self.description_en or self.description or ''
    
    def __repr__(self):
        return f'<TaskPreset {self.title[:30]}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON export"""
        return {
            'id': self.id,
            'category': self.category,
            'tax_type': self.tax_type,
            'title': self.title,
            'title_de': self.title_de,
            'title_en': self.title_en,
            'law_reference': self.law_reference,
            'description': self.description,
            'description_de': self.description_de,
            'description_en': self.description_en,
            'is_active': self.is_active
        }


class Task(db.Model):
    """Individual task instance (calendar item)"""
    __tablename__ = 'task'
    
    # Status workflow: draft -> submitted -> in_review -> approved -> completed
    # Or can be rejected back to draft at any stage
    VALID_STATUSES = ['draft', 'submitted', 'in_review', 'approved', 'completed', 'rejected']
    
    # Status transitions: current_status -> [allowed next statuses]
    STATUS_TRANSITIONS = {
        'draft': ['submitted'],
        'submitted': ['in_review', 'rejected'],
        'in_review': ['approved', 'rejected'],
        'approved': ['completed', 'rejected'],
        'completed': [],  # Final state
        'rejected': ['draft'],  # Can restart
    }
    
    # Who can perform which transitions
    STATUS_PERMISSIONS = {
        'draft->submitted': ['owner', 'preparer', 'manager', 'admin'],
        'submitted->in_review': ['reviewer', 'manager', 'admin'],
        'submitted->rejected': ['reviewer', 'manager', 'admin'],
        'in_review->approved': ['manager', 'admin'],
        'in_review->rejected': ['reviewer', 'manager', 'admin'],
        'approved->completed': ['manager', 'admin'],
        'approved->rejected': ['manager', 'admin'],
        'rejected->draft': ['owner', 'preparer', 'manager', 'admin'],
    }
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    template_id = db.Column(db.Integer, db.ForeignKey('task_template.id'), nullable=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    period = db.Column(db.String(10))  # Q1, Q2, Q3, Q4, M01-M12, or empty for annual
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False, index=True)
    
    status = db.Column(db.String(20), default='draft', index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    owner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True, index=True)  # Team assignment
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Legacy single reviewer (optional)
    reviewer_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # Reviewer team
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Manager who approves
    
    # Recurring task fields
    preset_id = db.Column(db.Integer, db.ForeignKey('task_preset.id'), nullable=True, index=True)
    is_recurring_instance = db.Column(db.Boolean, default=False)  # True if auto-generated from preset
    
    # Workflow timestamps
    submitted_at = db.Column(db.DateTime)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    completed_at = db.Column(db.DateTime)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rejected_at = db.Column(db.DateTime)
    rejected_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rejection_reason = db.Column(db.Text)
    
    completion_note = db.Column(db.Text)  # What was filed, where, by whom
    
    # Archiving fields (soft-delete)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    archived_at = db.Column(db.DateTime)
    archived_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    archive_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evidence = db.relationship('TaskEvidence', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    # Multi-reviewer relationship
    reviewers = db.relationship('TaskReviewer', backref='task', lazy='dynamic', 
                                cascade='all, delete-orphan', order_by='TaskReviewer.order')
    
    # Additional user relationships for workflow
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id], backref='tasks_submitted')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id], backref='tasks_reviewed_by')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='tasks_approved')
    completed_by = db.relationship('User', foreign_keys=[completed_by_id], backref='tasks_completed')
    rejected_by = db.relationship('User', foreign_keys=[rejected_by_id], backref='tasks_rejected')
    approver = db.relationship('User', foreign_keys=[approver_id], backref='tasks_to_approve')
    
    # Team relationships
    reviewer_team = db.relationship('Team', foreign_keys=[reviewer_team_id], backref='tasks_to_review')
    
    # Preset relationship (for recurring tasks)
    preset = db.relationship('TaskPreset', backref='generated_tasks')
    
    # Archive relationship
    archived_by = db.relationship('User', foreign_keys=[archived_by_id], backref='tasks_archived')
    
    # =========================================================================
    # ARCHIVE METHODS
    # =========================================================================
    
    def archive(self, user, reason=None):
        """Archive this task (soft-delete)"""
        self.is_archived = True
        self.archived_at = datetime.utcnow()
        self.archived_by_id = user.id if user else None
        self.archive_reason = reason
    
    def restore(self):
        """Restore this task from archive"""
        self.is_archived = False
        self.archived_at = None
        self.archived_by_id = None
        self.archive_reason = None
    
    # =========================================================================
    # TEAM METHODS
    # =========================================================================
    
    def get_owner_display(self):
        """Get display name for owner (user or team)"""
        if self.owner:
            return self.owner.name
        elif self.owner_team:
            return f"Team: {self.owner_team.name}"
        return None
    
    def get_all_assigned_users(self):
        """Get all users assigned to this task (owner + team members)"""
        users = set()
        if self.owner:
            users.add(self.owner)
        if self.owner_team:
            for member in self.owner_team.members.all():
                users.add(member)
        return list(users)
    
    def is_assigned_to_user(self, user):
        """Check if task is assigned to user (directly or via team)"""
        if self.owner_id == user.id:
            return True
        if self.owner_team and self.owner_team.is_member(user):
            return True
        return False
    
    def is_reviewer_via_team(self, user):
        """Check if user is a reviewer via team assignment"""
        if self.reviewer_team and self.reviewer_team.is_member(user):
            return True
        return False
    
    # =========================================================================
    # MULTI-REVIEWER METHODS
    # =========================================================================
    
    def get_reviewer_users(self):
        """Get list of reviewer User objects"""
        return [tr.user for tr in self.reviewers.all()]
    
    def get_reviewer_ids(self):
        """Get list of reviewer user IDs"""
        return [tr.user_id for tr in self.reviewers.all()]
    
    def add_reviewer(self, user, order=None):
        """Add a reviewer to this task"""
        existing = TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).first()
        if existing:
            return existing
        if order is None:
            max_order = db.session.query(db.func.max(TaskReviewer.order)).filter_by(task_id=self.id).scalar() or 0
            order = max_order + 1
        tr = TaskReviewer(task_id=self.id, user_id=user.id, order=order)
        db.session.add(tr)
        return tr
    
    def remove_reviewer(self, user):
        """Remove a reviewer from this task"""
        TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).delete()
    
    def set_reviewers(self, user_ids):
        """Set reviewers from list of user IDs (replaces existing)"""
        # Remove all existing
        TaskReviewer.query.filter_by(task_id=self.id).delete()
        # Add new ones
        for i, user_id in enumerate(user_ids, 1):
            tr = TaskReviewer(task_id=self.id, user_id=user_id, order=i)
            db.session.add(tr)
    
    def get_reviewer_status(self, user):
        """Get approval status for a specific reviewer"""
        tr = TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).first()
        if not tr:
            return None
        if tr.has_approved:
            return 'approved'
        if tr.has_rejected:
            return 'rejected'
        return 'pending'
    
    def approve_by_reviewer(self, user, note=None):
        """Record approval by a specific reviewer"""
        tr = TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).first()
        if tr:
            tr.approve(note)
            return True
        return False
    
    def reject_by_reviewer(self, user, note=None):
        """Record rejection by a specific reviewer"""
        tr = TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).first()
        if tr:
            tr.reject(note)
            return True
        return False
    
    def reset_all_approvals(self):
        """Reset all reviewer approvals (e.g., when resubmitting)"""
        for tr in self.reviewers.all():
            tr.reset()
    
    def get_approval_count(self):
        """Get count of approved vs total reviewers"""
        total = self.reviewers.count()
        approved = self.reviewers.filter_by(has_approved=True).count()
        return approved, total
    
    def all_reviewers_approved(self):
        """Check if all assigned reviewers have approved"""
        total = self.reviewers.count()
        if total == 0:
            return True  # No reviewers required
        approved = self.reviewers.filter_by(has_approved=True).count()
        return approved >= total
    
    def any_reviewer_rejected(self):
        """Check if any reviewer has rejected"""
        return self.reviewers.filter_by(has_rejected=True).count() > 0
    
    def is_reviewer(self, user):
        """Check if user is a reviewer for this task (directly or via team)"""
        # Check direct reviewer assignment
        if TaskReviewer.query.filter_by(task_id=self.id, user_id=user.id).count() > 0:
            return True
        # Check reviewer team membership
        if self.reviewer_team and self.reviewer_team.is_member(user):
            return True
        return False
    
    def get_pending_reviewers(self):
        """Get reviewers who haven't approved or rejected yet"""
        return self.reviewers.filter_by(has_approved=False, has_rejected=False).all()
    
    def can_transition_to(self, new_status, user):
        """Check if user can transition task to new status"""
        if new_status not in self.STATUS_TRANSITIONS.get(self.status, []):
            return False
        
        transition_key = f"{self.status}->{new_status}"
        allowed_roles = self.STATUS_PERMISSIONS.get(transition_key, [])
        
        # Check user role
        if user.role in ['admin', 'manager']:
            return True
        if 'owner' in allowed_roles and self.owner_id == user.id:
            return True
        # Check multi-reviewer permissions
        if 'reviewer' in allowed_roles and self.is_reviewer(user):
            return True
        # Legacy single reviewer check
        if 'reviewer' in allowed_roles and self.reviewer_id == user.id:
            return True
        if user.role in allowed_roles:
            return True
        
        return False
    
    def get_allowed_transitions(self, user):
        """Get list of statuses user can transition to"""
        allowed = []
        for next_status in self.STATUS_TRANSITIONS.get(self.status, []):
            if self.can_transition_to(next_status, user):
                allowed.append(next_status)
        return allowed
    
    def transition_to(self, new_status, user, note=None):
        """Perform status transition with timestamp and user tracking"""
        if not self.can_transition_to(new_status, user):
            raise ValueError(f"Transition from {self.status} to {new_status} not allowed for user {user.email}")
        
        old_status = self.status
        self.status = new_status
        now = datetime.utcnow()
        
        if new_status == 'submitted':
            self.submitted_at = now
            self.submitted_by_id = user.id
        elif new_status == 'in_review':
            self.reviewed_at = now
            self.reviewed_by_id = user.id
        elif new_status == 'approved':
            self.approved_at = now
            self.approved_by_id = user.id
        elif new_status == 'completed':
            self.completed_at = now
            self.completed_by_id = user.id
            if note:
                self.completion_note = note
        elif new_status == 'rejected':
            self.rejected_at = now
            self.rejected_by_id = user.id
            if note:
                self.rejection_reason = note
        elif new_status == 'draft':
            # Reset rejection when restarting
            self.rejection_reason = None
        
        return old_status
    
    @property
    def workflow_progress(self):
        """Get workflow progress percentage"""
        progress_map = {
            'draft': 0,
            'submitted': 25,
            'in_review': 50,
            'approved': 75,
            'completed': 100,
            'rejected': 10,
        }
        return progress_map.get(self.status, 0)
    
    @property
    def next_action_by(self):
        """Who needs to take action next"""
        if self.status == 'draft':
            return self.owner
        elif self.status == 'submitted':
            return self.reviewer
        elif self.status == 'in_review':
            return self.approver or self.reviewer
        elif self.status == 'approved':
            return self.approver or self.owner
        elif self.status == 'rejected':
            return self.owner
        return None
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.status == 'completed':
            return False
        return self.due_date < date.today()
    
    @property
    def is_due_soon(self, days=7):
        """Check if task is due within N days"""
        if self.status == 'completed':
            return False
        delta = (self.due_date - date.today()).days
        return 0 <= delta <= days
    
    @property
    def effective_status(self):
        """Get effective status including automatic overlays"""
        if self.status == 'completed':
            return 'completed'
        if self.is_overdue:
            return 'overdue'
        if self.is_due_soon:
            return 'due_soon'
        return self.status
    
    def __repr__(self):
        return f'<Task {self.title} ({self.due_date})>'


class TaskEvidence(db.Model):
    """Evidence attached to a task (files or links)"""
    __tablename__ = 'task_evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    evidence_type = db.Column(db.String(10), nullable=False)  # file, link
    
    # For files
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # For links
    url = db.Column(db.String(500))
    link_title = db.Column(db.String(200))
    
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    uploaded_by = db.relationship('User', backref='uploaded_evidence')
    
    def __repr__(self):
        return f'<TaskEvidence {self.evidence_type}: {self.filename or self.url}>'


class Comment(db.Model):
    """Comments on tasks or references"""
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    reference_id = db.Column(db.Integer, db.ForeignKey('reference_application.id'), nullable=True)
    
    text = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    
    created_by = db.relationship('User', backref='comments')
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.created_by_id}>'


class ReferenceApplication(db.Model):
    """Reference library for law-based applications (Anträge)"""
    __tablename__ = 'reference_application'
    
    id = db.Column(db.Integer, primary_key=True)
    law = db.Column(db.String(100))  # e.g., "EStG", "KStG"
    paragraph = db.Column(db.String(50))  # e.g., "§ 34a"
    title = db.Column(db.String(200), nullable=False)
    purpose = db.Column(db.Text)
    explanation = db.Column(db.Text)
    deadline_info = db.Column(db.Text)  # When to apply
    source = db.Column(db.String(100))  # Which Excel sheet/import
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('Comment', backref='reference', lazy='dynamic')
    
    def __repr__(self):
        return f'<ReferenceApplication {self.law} {self.paragraph}>'


# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

class NotificationType(Enum):
    """Types of in-app notifications"""
    TASK_ASSIGNED = 'task_assigned'
    TASK_STATUS_CHANGED = 'task_status_changed'
    TASK_COMMENT = 'task_comment'
    TASK_APPROVED = 'task_approved'
    TASK_REJECTED = 'task_rejected'
    REVIEW_REQUESTED = 'review_requested'
    TASK_DUE_SOON = 'task_due_soon'
    TASK_OVERDUE = 'task_overdue'
    REVIEWER_ADDED = 'reviewer_added'
    
    @classmethod
    def choices(cls):
        return [(t.value, t.name.replace('_', ' ').title()) for t in cls]


class Notification(db.Model):
    """In-app notification for users"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), index=True)  # Multi-tenancy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Notification content
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    title_de = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    message = db.Column(db.Text)
    message_de = db.Column(db.Text)
    message_en = db.Column(db.Text)
    
    # Related entity (task, comment, etc.)
    entity_type = db.Column(db.String(50))  # 'task', 'comment', etc.
    entity_id = db.Column(db.Integer, index=True)
    
    # Actor who triggered the notification
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # State
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
    
    def get_title(self, lang='de'):
        """Get translated title"""
        if lang == 'en' and self.title_en:
            return self.title_en
        if lang == 'de' and self.title_de:
            return self.title_de
        return self.title_de or self.title_en or self.title
    
    def get_message(self, lang='de'):
        """Get translated message"""
        if lang == 'en' and self.message_en:
            return self.message_en
        if lang == 'de' and self.message_de:
            return self.message_de
        return self.message_de or self.message_en or self.message or ''
    
    def get_icon(self):
        """Get Bootstrap icon class based on notification type"""
        icons = {
            NotificationType.TASK_ASSIGNED.value: 'bi-person-plus',
            NotificationType.TASK_STATUS_CHANGED.value: 'bi-arrow-repeat',
            NotificationType.TASK_COMMENT.value: 'bi-chat-dots',
            NotificationType.TASK_APPROVED.value: 'bi-check-circle',
            NotificationType.TASK_REJECTED.value: 'bi-x-circle',
            NotificationType.REVIEW_REQUESTED.value: 'bi-eye',
            NotificationType.TASK_DUE_SOON.value: 'bi-clock',
            NotificationType.TASK_OVERDUE.value: 'bi-exclamation-triangle',
            NotificationType.REVIEWER_ADDED.value: 'bi-person-check',
        }
        return icons.get(self.notification_type, 'bi-bell')
    
    def get_color(self):
        """Get color class based on notification type"""
        colors = {
            NotificationType.TASK_ASSIGNED.value: 'text-primary',
            NotificationType.TASK_STATUS_CHANGED.value: 'text-info',
            NotificationType.TASK_COMMENT.value: 'text-secondary',
            NotificationType.TASK_APPROVED.value: 'text-success',
            NotificationType.TASK_REJECTED.value: 'text-danger',
            NotificationType.REVIEW_REQUESTED.value: 'text-warning',
            NotificationType.TASK_DUE_SOON.value: 'text-warning',
            NotificationType.TASK_OVERDUE.value: 'text-danger',
            NotificationType.REVIEWER_ADDED.value: 'text-primary',
        }
        return colors.get(self.notification_type, 'text-muted')
    
    def to_dict(self, lang='de'):
        """Convert to dictionary for JSON/API"""
        return {
            'id': self.id,
            'type': self.notification_type,
            'title': self.get_title(lang),
            'message': self.get_message(lang),
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'actor': self.actor.name if self.actor else None,
            'icon': self.get_icon(),
            'color': self.get_color(),
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_ago': self._time_ago()
        }
    
    def _time_ago(self):
        """Get human-readable time ago string"""
        if not self.created_at:
            return ''
        delta = datetime.utcnow() - self.created_at
        seconds = delta.total_seconds()
        if seconds < 60:
            return 'gerade eben'
        elif seconds < 3600:
            mins = int(seconds // 60)
            return f'vor {mins} Min.'
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f'vor {hours} Std.'
        else:
            days = int(seconds // 86400)
            return f'vor {days} Tag{"en" if days > 1 else ""}'
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}: {self.notification_type}>'


# ============================================================================
# ASSOCIATION TABLES
# ============================================================================

# Entity-User permissions (which users can access which entities)
entity_user_access = db.Table('entity_user_access',
    db.Column('entity_id', db.Integer, db.ForeignKey('entity.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


# ============================================================================
# MODULE SYSTEM
# ============================================================================

class Module(db.Model):
    """Application module definition"""
    __tablename__ = 'module'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 'tasks', 'projects'
    name_de = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    description_de = db.Column(db.Text)
    description_en = db.Column(db.Text)
    icon = db.Column(db.String(50), default='bi-puzzle')  # Bootstrap icon class
    nav_order = db.Column(db.Integer, default=100)  # Lower = earlier in nav
    is_core = db.Column(db.Boolean, default=False)  # Core modules can't be disabled
    is_active = db.Column(db.Boolean, default=True)  # Global on/off switch
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_modules = db.relationship('UserModule', back_populates='module', cascade='all, delete-orphan')
    
    def get_name(self, lang='de'):
        """Get localized name"""
        return self.name_de if lang == 'de' else self.name_en
    
    def get_description(self, lang='de'):
        """Get localized description"""
        return self.description_de if lang == 'de' else self.description_en
    
    def __repr__(self):
        return f'<Module {self.code}>'


class UserModule(db.Model):
    """User-Module access assignment"""
    __tablename__ = 'user_module'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='user_modules')
    module = db.relationship('Module', back_populates='user_modules')
    granted_by = db.relationship('User', foreign_keys=[granted_by_id])
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_id', name='unique_user_module'),
    )
    
    def __repr__(self):
        return f'<UserModule {self.user_id}:{self.module_id}>'

