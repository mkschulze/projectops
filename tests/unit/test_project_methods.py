"""
Tests for Project model methods and behaviors.
Focused on improving code coverage for modules/projects/models.py
"""
import pytest
from datetime import datetime, date, timedelta


class TestProjectGetMethods:
    """Tests for Project getter methods."""
    
    def test_get_name_returns_name(self, db, project):
        """Test get_name returns the project name."""
        assert project.get_name() == project.name
    
    def test_get_name_with_english(self, db, project):
        """Test get_name returns name_en when available."""
        project.name = 'German Name'
        project.name_en = 'English Name'
        db.session.commit()
        
        assert project.get_name('en') == 'English Name'
        assert project.get_name('de') == 'German Name'
    
    def test_get_description_returns_description(self, db, project):
        """Test get_description returns description."""
        project.description = 'Test Description'
        db.session.commit()
        
        assert project.get_description() == 'Test Description'
    
    def test_get_next_issue_key_increments(self, db, project):
        """Test get_next_issue_key increments counter."""
        project.issue_counter = 0
        db.session.commit()
        
        key1 = project.get_next_issue_key()
        assert key1 == f'{project.key}-1'
        
        key2 = project.get_next_issue_key()
        assert key2 == f'{project.key}-2'


class TestProjectMethodologyConfig:
    """Tests for Project methodology configuration."""
    
    def test_get_methodology_config_returns_dict(self, db, project):
        """Test get_methodology_config returns a dict."""
        config = project.get_methodology_config()
        assert isinstance(config, dict)
    
    def test_get_methodology_config_has_features(self, db, project):
        """Test config has features key."""
        config = project.get_methodology_config()
        assert 'features' in config
    
    def test_get_term_returns_string(self, db, project):
        """Test get_term returns a string."""
        term = project.get_term('sprint')
        assert isinstance(term, str)
    
    def test_has_feature_returns_bool(self, db, project):
        """Test has_feature returns boolean."""
        result = project.has_feature('sprints')
        assert isinstance(result, bool)
    
    def test_scrum_has_sprints(self, db, project):
        """Test Scrum methodology has sprints feature."""
        project.methodology = 'scrum'
        db.session.commit()
        
        assert project.has_feature('sprints') is True
    
    def test_waterfall_no_sprints(self, db, project):
        """Test Waterfall methodology has no sprints."""
        project.methodology = 'waterfall'
        db.session.commit()
        
        assert project.has_feature('sprints') is False
    
    def test_get_methodology_name_german(self, db, project):
        """Test get_methodology_name in German."""
        project.methodology = 'scrum'
        db.session.commit()
        
        name = project.get_methodology_name('de')
        assert isinstance(name, str)
        assert len(name) > 0


class TestProjectMembership:
    """Tests for Project membership methods."""
    
    def test_is_member_false_when_not_member(self, db, project, user):
        """Test is_member returns False when user is not a member."""
        result = project.is_member(user)
        assert result is False
    
    def test_is_member_true_when_member(self, db, project_with_member):
        """Test is_member returns True when user is a member."""
        project, user = project_with_member
        result = project.is_member(user)
        assert result is True
    
    def test_get_member_role_none_when_not_member(self, db, project, user):
        """Test get_member_role returns None when user is not a member."""
        result = project.get_member_role(user)
        assert result is None
    
    def test_get_member_role_returns_role(self, db, project_with_member):
        """Test get_member_role returns role string."""
        project, user = project_with_member
        result = project.get_member_role(user)
        assert result == 'member'
    
    def test_can_user_edit_false_for_non_member(self, db, project, user):
        """Test can_user_edit returns False for non-member."""
        result = project.can_user_edit(user)
        assert result is False
    
    def test_is_admin_false_for_regular_member(self, db, project_with_member):
        """Test is_admin returns False for regular member."""
        project, user = project_with_member
        result = project.is_admin(user)
        assert result is False
    
    def test_member_count_property(self, db, project):
        """Test member_count property."""
        count = project.member_count
        assert isinstance(count, int)
        assert count >= 0


class TestProjectEstimation:
    """Tests for Project estimation methods."""
    
    def test_get_estimation_scale_config_returns_dict(self, db, project):
        """Test get_estimation_scale_config returns dict."""
        config = project.get_estimation_scale_config()
        assert isinstance(config, dict)
    
    def test_get_estimation_values_returns_list(self, db, project):
        """Test get_estimation_values returns list."""
        values = project.get_estimation_values()
        assert isinstance(values, list)
    
    def test_scrum_uses_fibonacci(self, db, project):
        """Test Scrum default uses Fibonacci scale."""
        project.methodology = 'scrum'
        project.estimation_scale = 'fibonacci'
        db.session.commit()
        
        values = project.get_estimation_values()
        # Values is a list of dicts with 'points' key
        points = [v['points'] for v in values]
        assert 1 in points
        assert 2 in points
        assert 3 in points
        assert 5 in points
    
    def test_waterfall_uses_persondays(self, db, project):
        """Test Waterfall uses Persondays scale."""
        project.methodology = 'waterfall'
        project.estimation_scale = 'persondays'
        db.session.commit()
        
        values = project.get_estimation_values()
        # Values is a list of dicts with 'points' key
        assert len(values) > 0
        assert isinstance(values[0], dict)


class TestProjectDefaultTypes:
    """Tests for Project default type methods."""
    
    def test_get_default_issue_type_with_types(self, db, project, issue_type):
        """Test get_default_issue_type when types exist."""
        default_type = project.get_default_issue_type()
        assert default_type is not None
    
    def test_get_initial_status_with_statuses(self, db, project, issue_status):
        """Test get_initial_status when statuses exist."""
        initial = project.get_initial_status()
        assert initial is not None


class TestProjectRepr:
    """Tests for Project __repr__ method."""
    
    def test_project_repr(self, db, project):
        """Test Project __repr__ format."""
        repr_str = repr(project)
        assert project.key in repr_str
        assert project.name in repr_str


class TestSprintModel:
    """Tests for Sprint model methods."""
    
    def test_sprint_has_project_relationship(self, db, sprint):
        """Test Sprint has project relationship."""
        assert sprint.project is not None
    
    def test_sprint_goal_property(self, db, sprint):
        """Test Sprint goal can be set."""
        sprint.goal = 'New Sprint Goal'
        db.session.commit()
        
        assert sprint.goal == 'New Sprint Goal'


class TestIssueModel:
    """Tests for Issue model methods."""
    
    def test_issue_has_key(self, db, issue):
        """Test Issue has key property."""
        assert issue.key is not None
        assert '-' in issue.key
    
    def test_issue_has_summary(self, db, issue):
        """Test Issue has summary."""
        assert issue.summary == 'Test Issue'
    
    def test_issue_has_project(self, db, issue):
        """Test Issue has project relationship."""
        assert issue.project is not None
    
    def test_issue_has_reporter(self, db, issue):
        """Test Issue has reporter relationship."""
        assert issue.reporter is not None
    
    def test_issue_has_status(self, db, issue):
        """Test Issue has status relationship."""
        assert issue.status is not None
    
    def test_issue_has_issue_type(self, db, issue):
        """Test Issue has issue_type relationship."""
        assert issue.issue_type is not None


class TestIssueTypeModel:
    """Tests for IssueType model methods."""
    
    def test_issue_type_get_name(self, db, issue_type):
        """Test IssueType get_name method."""
        from modules.projects.models import IssueType
        
        name = issue_type.get_name()
        assert name == 'Task'
    
    def test_issue_type_has_icon(self, db, issue_type):
        """Test IssueType has icon."""
        assert issue_type.icon is not None
    
    def test_issue_type_has_color(self, db, issue_type):
        """Test IssueType has color."""
        assert issue_type.color is not None


class TestIssueStatusModel:
    """Tests for IssueStatus model methods."""
    
    def test_issue_status_get_name(self, db, issue_status):
        """Test IssueStatus get_name method."""
        from modules.projects.models import IssueStatus
        
        name = issue_status.get_name()
        assert name == 'To Do'
    
    def test_issue_status_has_category(self, db, issue_status):
        """Test IssueStatus has category."""
        assert issue_status.category == 'todo'
    
    def test_issue_status_is_initial(self, db, issue_status):
        """Test IssueStatus is_initial flag."""
        assert issue_status.is_initial is True


class TestProjectMemberModel:
    """Tests for ProjectMember model."""
    
    def test_project_member_get_role_display_german(self, db, project_with_member):
        """Test ProjectMember get_role_display in German."""
        project, user = project_with_member
        from modules.projects.models import ProjectMember
        
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=user.id
        ).first()
        
        display = member.get_role_display('de')
        assert display == 'Mitglied'
    
    def test_project_member_get_role_display_english(self, db, project_with_member):
        """Test ProjectMember get_role_display in English."""
        project, user = project_with_member
        from modules.projects.models import ProjectMember
        
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=user.id
        ).first()
        
        display = member.get_role_display('en')
        assert display == 'Member'
    
    def test_project_member_repr(self, db, project_with_member):
        """Test ProjectMember __repr__ method."""
        project, user = project_with_member
        from modules.projects.models import ProjectMember
        
        member = ProjectMember.query.filter_by(
            project_id=project.id,
            user_id=user.id
        ).first()
        
        repr_str = repr(member)
        assert 'ProjectMember' in repr_str
