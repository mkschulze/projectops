"""
Factory Boy factories for test data generation.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, timedelta

from extensions import db


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""
    
    class Meta:
        abstract = True
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


# =============================================================================
# USER FACTORIES
# =============================================================================

class UserFactory(BaseFactory):
    """Factory for User model."""
    
    class Meta:
        from models import User
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Sequence(lambda n: f'User {n}')
    role = 'preparer'
    is_active = True
    
    @factory.lazy_attribute
    def password_hash(self):
        from werkzeug.security import generate_password_hash
        return generate_password_hash('testpassword123')


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    
    role = 'admin'
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    name = factory.Sequence(lambda n: f'Admin {n}')


# =============================================================================
# TENANT FACTORIES
# =============================================================================

class TenantFactory(BaseFactory):
    """Factory for Tenant model."""
    
    class Meta:
        from models import Tenant
        model = Tenant
    
    name = factory.Sequence(lambda n: f'Tenant {n}')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    is_active = True


class TenantMembershipFactory(BaseFactory):
    """Factory for TenantMembership model."""
    
    class Meta:
        from models import TenantMembership
        model = TenantMembership
    
    tenant = factory.SubFactory(TenantFactory)
    user = factory.SubFactory(UserFactory)
    role = 'member'
    is_default = False


# =============================================================================
# PROJECT FACTORIES
# =============================================================================

class ProjectFactory(BaseFactory):
    """Factory for Project model."""
    
    class Meta:
        from modules.projects.models import Project
        model = Project
    
    name = factory.Sequence(lambda n: f'Project {n}')
    key = factory.Sequence(lambda n: f'PRJ{n}')
    description = factory.Faker('paragraph')
    tenant = factory.SubFactory(TenantFactory)
    methodology = 'scrum'


class ProjectMemberFactory(BaseFactory):
    """Factory for ProjectMember model."""
    
    class Meta:
        from modules.projects.models import ProjectMember
        model = ProjectMember
    
    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = 'member'


class SprintFactory(BaseFactory):
    """Factory for Sprint model."""
    
    class Meta:
        from modules.projects.models import Sprint
        model = Sprint
    
    name = factory.Sequence(lambda n: f'Sprint {n}')
    project = factory.SubFactory(ProjectFactory)
    start_date = factory.LazyFunction(lambda: datetime.utcnow().date())
    end_date = factory.LazyFunction(lambda: (datetime.utcnow() + timedelta(days=14)).date())
    goal = factory.Faker('sentence')


class IssueTypeFactory(BaseFactory):
    """Factory for IssueType model."""
    
    class Meta:
        from modules.projects.models import IssueType
        model = IssueType
    
    name = factory.Iterator(['Task', 'Bug', 'Story', 'Epic'])
    project = factory.SubFactory(ProjectFactory)
    icon = 'bi-check-square'
    color = '#0076A8'


class IssueStatusFactory(BaseFactory):
    """Factory for IssueStatus model."""
    
    class Meta:
        from modules.projects.models import IssueStatus
        model = IssueStatus
    
    name = factory.Iterator(['To Do', 'In Progress', 'Done'])
    project = factory.SubFactory(ProjectFactory)
    position = factory.Sequence(lambda n: n)
    is_initial = False
    
    @factory.lazy_attribute
    def category(self):
        from modules.projects.models import StatusCategory
        name_to_category = {
            'To Do': StatusCategory.TODO,
            'In Progress': StatusCategory.IN_PROGRESS,
            'Done': StatusCategory.DONE
        }
        return name_to_category.get(self.name, StatusCategory.TODO)


class IssueFactory(BaseFactory):
    """Factory for Issue model."""
    
    class Meta:
        from modules.projects.models import Issue
        model = Issue
    
    summary = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    project = factory.SubFactory(ProjectFactory)
    issue_type = factory.SubFactory(IssueTypeFactory)
    status = factory.SubFactory(IssueStatusFactory)
    reporter = factory.SubFactory(UserFactory)
    
    @factory.lazy_attribute
    def key(self):
        return f'{self.project.key}-1'


# =============================================================================
# TASK FACTORIES (Legacy)
# =============================================================================

class EntityFactory(BaseFactory):
    """Factory for Entity model."""
    
    class Meta:
        from models import Entity
        model = Entity
    
    name = factory.Sequence(lambda n: f'Entity {n}')
    entity_type = 'division'
    tenant = factory.SubFactory(TenantFactory)
    is_active = True


class TaskCategoryFactory(BaseFactory):
    """Factory for TaskCategory model."""
    
    class Meta:
        from models import TaskCategory
        model = TaskCategory
    
    name = factory.Sequence(lambda n: f'Category {n}')
    tenant = factory.SubFactory(TenantFactory)


class TaskFactory(BaseFactory):
    """Factory for Task model."""
    
    class Meta:
        from models import Task
        model = Task
    
    name = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    entity = factory.SubFactory(EntityFactory)
    category = factory.SubFactory(TaskCategoryFactory)
    status = 'todo'
    priority = 2
    due_date = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=7))
