"""
Unit tests for Project models.
"""
import pytest
from datetime import datetime, timedelta


@pytest.mark.unit
@pytest.mark.models
class TestProjectModel:
    """Tests for Project model."""
    
    def test_project_creation(self, project):
        """Test project is created correctly."""
        assert project.name == 'Test Project'
        assert project.key == 'TEST'
        assert project.methodology == 'scrum'
        assert project.is_archived is False
    
    def test_project_tenant_relationship(self, project, tenant):
        """Test project belongs to tenant."""
        assert project.tenant_id == tenant.id
    
    def test_project_methodology_default(self, db, tenant):
        """Test default methodology is scrum."""
        from modules.projects.models import Project
        
        project = Project(
            name='New Project',
            key='NEW',
            tenant_id=tenant.id
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.methodology == 'scrum'
        
        db.session.delete(project)
        db.session.commit()
    
    def test_project_estimation_scale_default(self, project):
        """Test estimation scale defaults based on methodology."""
        # For scrum, default should be fibonacci
        config = project.get_estimation_scale_config()
        assert config['name']['en'] == 'Fibonacci'
    
    def test_project_estimation_scale_waterfall(self, db, tenant):
        """Test waterfall projects default to person days when no scale is set."""
        from modules.projects.models import Project
        
        project = Project(
            name='Waterfall Project',
            key='WF',
            tenant_id=tenant.id,
            methodology='waterfall'
        )
        db.session.add(project)
        db.session.commit()
        
        # Manually set estimation_scale to None to trigger methodology-based default
        project.estimation_scale = None
        db.session.commit()
        
        config = project.get_estimation_scale_config()
        # Waterfall should default to persondays - check the name
        assert config['name']['de'] == 'Personentage (PT)'
        assert config['name']['en'] == 'Person Days (PD)'
        
        db.session.delete(project)
        db.session.commit()
    
    def test_get_name_localized(self, db, tenant):
        """Test localized project name."""
        from modules.projects.models import Project
        
        project = Project(
            name='Deutscher Name',
            name_en='English Name',
            key='LOC',
            tenant_id=tenant.id
        )
        db.session.add(project)
        db.session.commit()
        
        assert project.get_name('de') == 'Deutscher Name'
        assert project.get_name('en') == 'English Name'
        
        db.session.delete(project)
        db.session.commit()


@pytest.mark.unit
@pytest.mark.models
class TestSprintModel:
    """Tests for Sprint model."""
    
    def test_sprint_creation(self, sprint):
        """Test sprint is created correctly."""
        assert sprint.name == 'Sprint 1'
        assert sprint.goal == 'Complete sprint goals'
    
    def test_sprint_project_relationship(self, sprint, project):
        """Test sprint belongs to project."""
        assert sprint.project_id == project.id
    
    def test_sprint_dates(self, sprint):
        """Test sprint has valid dates."""
        assert sprint.start_date is not None
        assert sprint.end_date is not None
        assert sprint.end_date > sprint.start_date
    
    def test_sprint_duration(self, sprint):
        """Test sprint duration calculation."""
        duration = (sprint.end_date - sprint.start_date).days
        assert duration == 14  # Default 2 weeks


@pytest.mark.unit
@pytest.mark.models
class TestIssueModel:
    """Tests for Issue model."""
    
    def test_issue_creation(self, issue):
        """Test issue is created correctly."""
        assert issue.summary == 'Test Issue'
        assert issue.key == 'TEST-1'
    
    def test_issue_relationships(self, issue, project, issue_type, issue_status, user):
        """Test issue relationships."""
        assert issue.project_id == project.id
        assert issue.type_id == issue_type.id
        assert issue.status_id == issue_status.id
        assert issue.reporter_id == user.id
    
    def test_issue_without_assignee(self, issue):
        """Test issue can exist without assignee."""
        assert issue.assignee_id is None
    
    def test_issue_story_points(self, db, issue):
        """Test setting story points."""
        issue.story_points = 5
        db.session.commit()
        
        assert issue.story_points == 5


@pytest.mark.unit
@pytest.mark.models  
class TestIssueTypeModel:
    """Tests for IssueType model."""
    
    def test_issue_type_creation(self, issue_type):
        """Test issue type is created correctly."""
        assert issue_type.name == 'Task'
        assert issue_type.icon == 'bi-check-square'
        assert issue_type.color == '#0076A8'
    
    def test_issue_type_project_relationship(self, issue_type, project):
        """Test issue type belongs to project."""
        assert issue_type.project_id == project.id


@pytest.mark.unit
@pytest.mark.models
class TestIssueStatusModel:
    """Tests for IssueStatus model."""
    
    def test_issue_status_creation(self, issue_status):
        """Test issue status is created correctly."""
        assert issue_status.name == 'To Do'
        assert issue_status.is_initial is True
    
    def test_issue_status_category(self, issue_status):
        """Test status has category."""
        assert issue_status.category == 'todo'
