"""
Unit tests for configuration module.
"""
import pytest


@pytest.mark.unit
class TestConfig:
    """Tests for config module."""
    
    def test_config_module_exists(self):
        """Test config module can be imported."""
        import config
        
        assert config is not None
    
    def test_config_class_exists(self):
        """Test Config class exists."""
        from config import Config
        
        assert Config is not None
    
    def test_config_has_secret_key(self):
        """Test Config has SECRET_KEY."""
        from config import Config
        
        assert hasattr(Config, 'SECRET_KEY')
    
    def test_config_has_sqlalchemy_database_uri(self):
        """Test Config has database URI."""
        from config import Config
        
        assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI')
    
    def test_config_has_sqlalchemy_track_modifications(self):
        """Test Config has track modifications setting."""
        from config import Config
        
        assert hasattr(Config, 'SQLALCHEMY_TRACK_MODIFICATIONS')
        # Should be False for performance
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False


@pytest.mark.unit
class TestTestingConfig:
    """Tests for testing configuration."""
    
    def test_testing_config_exists(self):
        """Test TestingConfig class exists."""
        from config import TestingConfig
        
        assert TestingConfig is not None
    
    def test_testing_config_has_testing_flag(self):
        """Test TestingConfig has TESTING=True."""
        from config import TestingConfig
        
        assert hasattr(TestingConfig, 'TESTING')
        assert TestingConfig.TESTING is True
    
    def test_testing_config_uses_memory_db(self):
        """Test TestingConfig uses in-memory database."""
        from config import TestingConfig
        
        db_uri = TestingConfig.SQLALCHEMY_DATABASE_URI
        assert 'memory' in db_uri or 'sqlite' in db_uri


@pytest.mark.unit
class TestDevelopmentConfig:
    """Tests for development configuration."""
    
    def test_development_config_exists(self):
        """Test DevelopmentConfig class exists."""
        from config import DevelopmentConfig
        
        assert DevelopmentConfig is not None
    
    def test_development_config_has_debug(self):
        """Test DevelopmentConfig has DEBUG setting."""
        from config import DevelopmentConfig
        
        assert hasattr(DevelopmentConfig, 'DEBUG')
