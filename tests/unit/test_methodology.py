"""
Unit tests for project methodology configuration.
"""
import pytest


@pytest.mark.unit
@pytest.mark.models
class TestMethodologyConfig:
    """Tests for methodology configuration."""
    
    def test_methodology_config_exists(self):
        """Test METHODOLOGY_CONFIG can be imported."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        assert METHODOLOGY_CONFIG is not None
        assert isinstance(METHODOLOGY_CONFIG, dict)
    
    def test_scrum_methodology_exists(self):
        """Test Scrum methodology is configured."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        assert 'scrum' in METHODOLOGY_CONFIG
    
    def test_kanban_methodology_exists(self):
        """Test Kanban methodology is configured."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        assert 'kanban' in METHODOLOGY_CONFIG
    
    def test_waterfall_methodology_exists(self):
        """Test Waterfall methodology is configured."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        assert 'waterfall' in METHODOLOGY_CONFIG
    
    def test_custom_methodology_exists(self):
        """Test Custom methodology is configured."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        assert 'custom' in METHODOLOGY_CONFIG
    
    def test_scrum_has_sprints(self):
        """Test Scrum methodology supports sprints."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        scrum_config = METHODOLOGY_CONFIG['scrum']
        # Sprints are in features dict, not at top level
        assert scrum_config.get('features', {}).get('sprints', False) is True
    
    def test_kanban_no_sprints(self):
        """Test Kanban methodology doesn't require sprints."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        kanban_config = METHODOLOGY_CONFIG['kanban']
        # Sprints are in features dict, not at top level
        assert kanban_config.get('features', {}).get('sprints', True) is False
    
    def test_methodology_has_terminology(self):
        """Test methodologies have terminology configured."""
        from modules.projects.models import METHODOLOGY_CONFIG
        
        for methodology, config in METHODOLOGY_CONFIG.items():
            assert 'terminology' in config, f"{methodology} missing terminology"


@pytest.mark.unit
@pytest.mark.models
class TestProjectMethodology:
    """Tests for Project methodology methods."""
    
    def test_get_methodology_config(self, project):
        """Test getting methodology configuration."""
        config = project.get_methodology_config()
        
        assert config is not None
        assert isinstance(config, dict)
    
    def test_get_term_returns_string(self, project):
        """Test get_term returns a string."""
        term = project.get_term('sprint', 'de')
        
        assert term is not None
        assert isinstance(term, str)
    
    def test_get_term_different_languages(self, project):
        """Test get_term works for different languages."""
        term_de = project.get_term('sprint', 'de')
        term_en = project.get_term('sprint', 'en')
        
        assert term_de is not None
        assert term_en is not None


@pytest.mark.unit
@pytest.mark.models
class TestEstimationScales:
    """Tests for estimation scale configuration."""
    
    def test_fibonacci_scale(self, project):
        """Test Fibonacci scale values."""
        project.estimation_scale = 'fibonacci'
        config = project.get_estimation_scale_config()
        
        values = [v['label'] for v in config['values']]
        assert '1' in values
        assert '2' in values
        assert '3' in values
        assert '5' in values
        assert '8' in values
        assert '13' in values
    
    def test_tshirt_scale(self, project):
        """Test T-Shirt scale values."""
        project.estimation_scale = 'tshirt'
        config = project.get_estimation_scale_config()
        
        values = [v['label'] for v in config['values']]
        assert 'XS' in values
        assert 'S' in values
        assert 'M' in values
        assert 'L' in values
        assert 'XL' in values
    
    def test_linear_scale(self, project):
        """Test Linear scale values."""
        project.estimation_scale = 'linear'
        config = project.get_estimation_scale_config()
        
        values = [v['label'] for v in config['values']]
        assert '1' in values
        assert '5' in values
        assert '10' in values
    
    def test_persondays_scale(self, project):
        """Test Person Days scale values."""
        project.estimation_scale = 'persondays'
        config = project.get_estimation_scale_config()
        
        values = [v['label'] for v in config['values']]
        assert '1' in values
        assert '5' in values
        assert '10' in values
    
    def test_scale_has_name(self, project):
        """Test scale configuration has name."""
        config = project.get_estimation_scale_config()
        
        assert 'name' in config
        assert 'de' in config['name']
        assert 'en' in config['name']
    
    def test_scale_has_hint(self, project):
        """Test scale configuration has hint."""
        config = project.get_estimation_scale_config()
        
        assert 'hint' in config
        assert 'de' in config['hint']
        assert 'en' in config['hint']
    
    def test_scale_values_have_points(self, project):
        """Test scale values have point mappings."""
        config = project.get_estimation_scale_config()
        
        for value in config['values']:
            assert 'points' in value
            assert 'label' in value
