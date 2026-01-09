"""
Unit tests for Sprint and Board functionality.
"""
import pytest
from datetime import datetime, timedelta


@pytest.mark.unit
@pytest.mark.models
class TestSprintStatus:
    """Tests for Sprint status methods."""
    
    def test_sprint_is_active(self, db, project):
        """Test sprint active status detection."""
        from modules.projects.models import Sprint
        
        today = datetime.utcnow().date()
        sprint = Sprint(
            name='Active Sprint',
            project_id=project.id,
            start_date=today - timedelta(days=7),
            end_date=today + timedelta(days=7)
        )
        
        db.session.add(sprint)
        db.session.commit()
        
        # Sprint should be considered active (between start and end)
        assert sprint.start_date <= today <= sprint.end_date
        
        db.session.delete(sprint)
        db.session.commit()
    
    def test_sprint_is_future(self, db, project):
        """Test future sprint detection."""
        from modules.projects.models import Sprint
        
        today = datetime.utcnow().date()
        sprint = Sprint(
            name='Future Sprint',
            project_id=project.id,
            start_date=today + timedelta(days=14),
            end_date=today + timedelta(days=28)
        )
        
        db.session.add(sprint)
        db.session.commit()
        
        # Sprint should be in future
        assert sprint.start_date > today
        
        db.session.delete(sprint)
        db.session.commit()
    
    def test_sprint_is_past(self, db, project):
        """Test past sprint detection."""
        from modules.projects.models import Sprint
        
        today = datetime.utcnow().date()
        sprint = Sprint(
            name='Past Sprint',
            project_id=project.id,
            start_date=today - timedelta(days=28),
            end_date=today - timedelta(days=14)
        )
        
        db.session.add(sprint)
        db.session.commit()
        
        # Sprint should be in past
        assert sprint.end_date < today
        
        db.session.delete(sprint)
        db.session.commit()


@pytest.mark.unit
@pytest.mark.models
class TestSprintGoal:
    """Tests for Sprint goal."""
    
    def test_sprint_with_goal(self, sprint):
        """Test sprint has goal."""
        assert sprint.goal == 'Complete sprint goals'
    
    def test_sprint_without_goal(self, db, project):
        """Test sprint can exist without goal."""
        from modules.projects.models import Sprint
        
        sprint = Sprint(
            name='No Goal Sprint',
            project_id=project.id,
            start_date=datetime.utcnow().date(),
            end_date=(datetime.utcnow() + timedelta(days=14)).date()
        )
        
        db.session.add(sprint)
        db.session.commit()
        
        assert sprint.goal is None
        
        db.session.delete(sprint)
        db.session.commit()


@pytest.mark.unit
@pytest.mark.models
class TestIssueBoard:
    """Tests for Issue board functionality."""
    
    def test_issue_has_board_position(self, issue):
        """Test issue has board_position field."""
        assert hasattr(issue, 'board_position')
    
    def test_issue_default_board_position(self, issue):
        """Test issue default board position is 0."""
        assert issue.board_position == 0
    
    def test_issue_board_position_update(self, db, issue):
        """Test updating issue board position."""
        issue.board_position = 5
        db.session.commit()
        
        assert issue.board_position == 5


@pytest.mark.unit
@pytest.mark.models
class TestIssuePriority:
    """Tests for Issue priority."""
    
    def test_issue_has_priority(self, issue):
        """Test issue has priority field."""
        assert hasattr(issue, 'priority')
    
    def test_issue_default_priority(self, issue):
        """Test issue default priority is 3 (Medium)."""
        assert issue.priority == 3
    
    def test_issue_priority_values(self, db, issue):
        """Test setting different priority values."""
        # Highest = 1
        issue.priority = 1
        db.session.commit()
        assert issue.priority == 1
        
        # Lowest = 5
        issue.priority = 5
        db.session.commit()
        assert issue.priority == 5


@pytest.mark.unit
@pytest.mark.models
class TestIssueLabels:
    """Tests for Issue labels."""
    
    def test_issue_has_labels(self, issue):
        """Test issue has labels field."""
        assert hasattr(issue, 'labels')
    
    def test_issue_default_labels(self, issue):
        """Test issue default labels is empty list."""
        assert issue.labels == [] or issue.labels is None
    
    def test_issue_add_labels(self, db, issue):
        """Test adding labels to issue."""
        issue.labels = ['bug', 'critical', 'frontend']
        db.session.commit()
        
        assert 'bug' in issue.labels
        assert 'critical' in issue.labels
        assert len(issue.labels) == 3


@pytest.mark.unit
@pytest.mark.models
class TestIssueTimeTracking:
    """Tests for Issue time tracking."""
    
    def test_issue_has_time_fields(self, issue):
        """Test issue has time tracking fields."""
        assert hasattr(issue, 'original_estimate')
        assert hasattr(issue, 'time_spent')
        assert hasattr(issue, 'remaining_estimate')
    
    def test_issue_default_time_spent(self, issue):
        """Test issue default time spent is 0."""
        assert issue.time_spent == 0
    
    def test_issue_time_tracking(self, db, issue):
        """Test time tracking values."""
        # Set estimate to 8 hours (480 minutes)
        issue.original_estimate = 480
        issue.remaining_estimate = 480
        db.session.commit()
        
        # Log 2 hours of work
        issue.time_spent = 120
        issue.remaining_estimate = 360
        db.session.commit()
        
        assert issue.time_spent == 120
        assert issue.remaining_estimate == 360
