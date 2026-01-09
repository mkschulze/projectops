"""
Tests for modules/projects/models.py
Tests for StatusCategory, ProjectMethodology, and related project models.
"""
import pytest


class TestStatusCategory:
    """Tests for StatusCategory enum."""
    
    def test_todo_value(self, app, db):
        """Test TODO value."""
        from modules.projects.models import StatusCategory
        assert StatusCategory.TODO.value == 'todo'
    
    def test_in_progress_value(self, app, db):
        """Test IN_PROGRESS value."""
        from modules.projects.models import StatusCategory
        assert StatusCategory.IN_PROGRESS.value == 'in_progress'
    
    def test_done_value(self, app, db):
        """Test DONE value."""
        from modules.projects.models import StatusCategory
        assert StatusCategory.DONE.value == 'done'
    
    def test_choices(self, app, db):
        """Test choices method."""
        from modules.projects.models import StatusCategory
        choices = StatusCategory.choices()
        
        assert isinstance(choices, list)
        assert len(choices) == 3
        assert ('todo', 'Todo') in choices


class TestProjectMethodology:
    """Tests for ProjectMethodology enum."""
    
    def test_scrum_value(self, app, db):
        """Test SCRUM value."""
        from modules.projects.models import ProjectMethodology
        assert ProjectMethodology.SCRUM.value == 'scrum'
    
    def test_kanban_value(self, app, db):
        """Test KANBAN value."""
        from modules.projects.models import ProjectMethodology
        assert ProjectMethodology.KANBAN.value == 'kanban'
    
    def test_waterfall_value(self, app, db):
        """Test WATERFALL value."""
        from modules.projects.models import ProjectMethodology
        assert ProjectMethodology.WATERFALL.value == 'waterfall'
    
    def test_custom_value(self, app, db):
        """Test CUSTOM value."""
        from modules.projects.models import ProjectMethodology
        assert ProjectMethodology.CUSTOM.value == 'custom'
    
    def test_methodology_choices(self, app, db):
        """Test choices method."""
        from modules.projects.models import ProjectMethodology
        choices = ProjectMethodology.choices()
        
        assert isinstance(choices, list)
        assert len(choices) == 4
        assert ('scrum', 'Scrum') in choices


class TestMethodologyConfig:
    """Tests for METHODOLOGY_CONFIG dictionary."""
    
    def test_methodology_config_exists(self, app, db):
        """Test METHODOLOGY_CONFIG exists."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert METHODOLOGY_CONFIG is not None
        assert isinstance(METHODOLOGY_CONFIG, dict)
    
    def test_scrum_config_exists(self, app, db):
        """Test scrum config exists."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'scrum' in METHODOLOGY_CONFIG
    
    def test_kanban_config_exists(self, app, db):
        """Test kanban config exists."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'kanban' in METHODOLOGY_CONFIG
    
    def test_waterfall_config_exists(self, app, db):
        """Test waterfall config exists."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'waterfall' in METHODOLOGY_CONFIG
    
    def test_custom_config_exists(self, app, db):
        """Test custom config exists."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'custom' in METHODOLOGY_CONFIG
    
    def test_scrum_has_features(self, app, db):
        """Test scrum has features dict."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'features' in METHODOLOGY_CONFIG['scrum']
        assert METHODOLOGY_CONFIG['scrum']['features']['sprints'] is True
    
    def test_kanban_no_sprints(self, app, db):
        """Test kanban has no sprints."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'features' in METHODOLOGY_CONFIG['kanban']
        assert METHODOLOGY_CONFIG['kanban']['features']['sprints'] is False
    
    def test_waterfall_no_sprints(self, app, db):
        """Test waterfall has no sprints."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'features' in METHODOLOGY_CONFIG['waterfall']
        assert METHODOLOGY_CONFIG['waterfall']['features']['sprints'] is False
    
    def test_scrum_has_terminology(self, app, db):
        """Test scrum has terminology."""
        from modules.projects.models import METHODOLOGY_CONFIG
        assert 'terminology' in METHODOLOGY_CONFIG['scrum']
        assert 'de' in METHODOLOGY_CONFIG['scrum']['terminology']
        assert 'en' in METHODOLOGY_CONFIG['scrum']['terminology']
    
    def test_terminology_has_sprint(self, app, db):
        """Test terminology includes sprint term."""
        from modules.projects.models import METHODOLOGY_CONFIG
        de_terms = METHODOLOGY_CONFIG['scrum']['terminology']['de']
        assert 'sprint' in de_terms


class TestProjectModelsImport:
    """Tests for project models imports."""
    
    def test_project_model_import(self, app, db):
        """Test Project model can be imported."""
        from modules.projects.models import Project
        assert Project is not None
    
    def test_issue_model_import(self, app, db):
        """Test Issue model can be imported."""
        from modules.projects.models import Issue
        assert Issue is not None
    
    def test_sprint_model_import(self, app, db):
        """Test Sprint model can be imported."""
        from modules.projects.models import Sprint
        assert Sprint is not None
    
    def test_issue_type_model_import(self, app, db):
        """Test IssueType model can be imported."""
        from modules.projects.models import IssueType
        assert IssueType is not None
    
    def test_issue_status_model_import(self, app, db):
        """Test IssueStatus model can be imported."""
        from modules.projects.models import IssueStatus
        assert IssueStatus is not None
    
    def test_issue_activity_model_import(self, app, db):
        """Test IssueActivity model can be imported."""
        from modules.projects.models import IssueActivity
        assert IssueActivity is not None


class TestProjectMember:
    """Tests for ProjectMember model."""
    
    def test_project_member_import(self, app, db):
        """Test ProjectMember can be imported."""
        from modules.projects.models import ProjectMember
        assert ProjectMember is not None
    
    def test_project_member_has_role_field(self, app, db):
        """Test ProjectMember has role field."""
        from modules.projects.models import ProjectMember
        assert hasattr(ProjectMember, 'role')
    
    def test_project_member_has_get_role_display(self, app, db):
        """Test ProjectMember has get_role_display method."""
        from modules.projects.models import ProjectMember
        assert hasattr(ProjectMember, 'get_role_display')
        assert callable(getattr(ProjectMember, 'get_role_display', None))


class TestProjectModelMethods:
    """Tests for Project model methods."""
    
    def test_project_get_name_german(self, db, project):
        """Test get_name returns German name."""
        name = project.get_name('de')
        assert name == project.name
    
    def test_project_get_name_english(self, db, project):
        """Test get_name returns English name if set."""
        project.name = 'German Name'
        project.name_en = 'English Name'
        
        assert project.get_name('de') == 'German Name'
        assert project.get_name('en') == 'English Name'
    
    def test_project_get_description_default(self, db, project):
        """Test get_description returns description."""
        project.description = 'Test Description'
        assert project.get_description() == 'Test Description'
    
    def test_project_get_description_empty(self, db, project):
        """Test get_description returns empty string if None."""
        project.description = None
        assert project.get_description() == ''
    
    def test_project_get_next_issue_key(self, db, project):
        """Test get_next_issue_key increments counter."""
        project.issue_counter = 0
        key1 = project.get_next_issue_key()
        assert key1 == f"{project.key}-1"
        
        key2 = project.get_next_issue_key()
        assert key2 == f"{project.key}-2"
    
    def test_project_get_methodology_config(self, db, project):
        """Test get_methodology_config returns dict."""
        config = project.get_methodology_config()
        assert isinstance(config, dict)
        assert 'features' in config
    
    def test_project_get_term_sprint(self, db, project):
        """Test get_term returns correct terminology."""
        project.methodology = 'scrum'
        term = project.get_term('sprint', 'de')
        assert term == 'Sprint'


class TestCreateDefaultFunctions:
    """Tests for create_default_* functions."""
    
    def test_create_default_issue_types_import(self, app, db):
        """Test create_default_issue_types can be imported."""
        from modules.projects.models import create_default_issue_types
        assert callable(create_default_issue_types)
    
    def test_create_default_issue_statuses_import(self, app, db):
        """Test create_default_issue_statuses can be imported."""
        from modules.projects.models import create_default_issue_statuses
        assert callable(create_default_issue_statuses)
