"""
Unit tests for authentication strategies.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from transcribe import LocalAuthStrategy, GoogleCloudAuthStrategy


class TestLocalAuthStrategy:
    """Tests for LocalAuthStrategy."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        api_key = "test-api-key-12345"
        strategy = LocalAuthStrategy(api_key)
        assert strategy.api_key == api_key
    
    def test_init_without_api_key_uses_env_var(self):
        """Test initialization without API key uses environment variable."""
        test_key = "env-api-key-67890"
        with patch.dict(os.environ, {'GEMINI_API_KEY': test_key}):
            strategy = LocalAuthStrategy()
            assert strategy.api_key == test_key
    
    def test_init_no_api_key_raises_error(self):
        """Test initialization without API key and no env var raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                LocalAuthStrategy()
    
    def test_authenticate_returns_api_key(self):
        """Test authenticate() returns the API key."""
        api_key = "test-api-key"
        strategy = LocalAuthStrategy(api_key)
        result = strategy.authenticate()
        assert result == api_key
    
    def test_validate_with_valid_key(self):
        """Test validate() with valid API key."""
        api_key = "test-api-key-12345"  # Length > 10
        strategy = LocalAuthStrategy(api_key)
        assert strategy.validate() is True
    
    def test_validate_with_short_key(self):
        """Test validate() with short API key."""
        api_key = "short"  # Length <= 10
        strategy = LocalAuthStrategy(api_key)
        assert strategy.validate() is False
    
    def test_validate_with_empty_key(self):
        """Test validate() with empty API key."""
        # Empty string will raise ValueError in __init__, so we can't test validate() directly
        # Instead, test that a very short key fails validation
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                LocalAuthStrategy("")  # Should raise in __init__


class TestGoogleCloudAuthStrategy:
    """Tests for GoogleCloudAuthStrategy."""
    
    @patch('transcribe.authenticate')
    def test_authenticate_delegates_to_authenticate_function(self, mock_authenticate):
        """Test authenticate() delegates to existing authenticate() function."""
        mock_creds = Mock()
        mock_authenticate.return_value = mock_creds
        
        strategy = GoogleCloudAuthStrategy("test_adc_file.json")
        result = strategy.authenticate()
        
        mock_authenticate.assert_called_once_with("test_adc_file.json")
        assert result == mock_creds
    
    def test_validate_with_existing_file(self):
        """Test validate() with existing ADC file."""
        with patch('os.path.exists', return_value=True):
            strategy = GoogleCloudAuthStrategy("test_adc_file.json")
            assert strategy.validate() is True
    
    def test_validate_with_missing_file(self):
        """Test validate() with missing ADC file."""
        with patch('os.path.exists', return_value=False):
            strategy = GoogleCloudAuthStrategy("missing_file.json")
            assert strategy.validate() is False
    
    def test_init_stores_adc_file(self):
        """Test __init__ stores ADC file path."""
        adc_file = "path/to/adc.json"
        strategy = GoogleCloudAuthStrategy(adc_file)
        assert strategy.adc_file == adc_file
