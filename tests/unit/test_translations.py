"""
Unit tests for translations module.
"""
import pytest


@pytest.mark.unit
class TestTranslations:
    """Tests for translations module."""
    
    def test_translations_module_exists(self):
        """Test translations module can be imported."""
        import translations
        
        assert translations is not None
    
    def test_get_translation_function_exists(self):
        """Test get_translation function exists."""
        from translations import get_translation
        
        assert callable(get_translation)
    
    def test_get_translation_german(self):
        """Test getting German translations."""
        from translations import get_translation
        
        # Test a common key
        result = get_translation('dashboard', 'de')
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_translation_english(self):
        """Test getting English translations."""
        from translations import get_translation
        
        result = get_translation('dashboard', 'en')
        assert result is not None
        assert isinstance(result, str)
    
    def test_translation_fallback(self):
        """Test fallback for missing translations."""
        from translations import get_translation
        
        # Unknown key should return the key itself or a default
        result = get_translation('unknown_key_xyz_123', 'de')
        assert result is not None
    
    def test_translations_dict_exists(self):
        """Test TRANSLATIONS dict exists."""
        from translations import TRANSLATIONS
        
        assert isinstance(TRANSLATIONS, dict)
    
    def test_translations_dict_has_entries(self):
        """Test TRANSLATIONS dict has entries."""
        from translations import TRANSLATIONS
        
        assert len(TRANSLATIONS) > 0
    
    def test_translations_contain_common_keys(self):
        """Test translations contain common UI keys."""
        from translations import TRANSLATIONS
        
        # Check for common keys
        common_keys = ['save', 'cancel', 'delete', 'edit']
        for key in common_keys:
            assert key in TRANSLATIONS, f"Missing key: {key}"
            assert 'de' in TRANSLATIONS[key]
            assert 'en' in TRANSLATIONS[key]


@pytest.mark.unit
class TestTranslationLanguages:
    """Tests for supported languages."""
    
    def test_german_supported(self):
        """Test German language is supported."""
        from translations import TRANSLATIONS
        
        # Check that all entries have German translations
        for key, value in TRANSLATIONS.items():
            assert 'de' in value, f"Missing German for: {key}"
    
    def test_english_supported(self):
        """Test English language is supported."""
        from translations import TRANSLATIONS
        
        # Check that all entries have English translations
        for key, value in TRANSLATIONS.items():
            assert 'en' in value, f"Missing English for: {key}"
