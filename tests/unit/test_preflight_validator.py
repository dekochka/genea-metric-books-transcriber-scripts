"""
Unit tests for PreFlightValidator
"""
import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from wizard.preflight_validator import PreFlightValidator, ValidationResult


@pytest.fixture
def validator():
    """Create PreFlightValidator instance."""
    return PreFlightValidator()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_init(self):
        """Test ValidationResult initialization."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []
    
    def test_has_issues_no_issues(self):
        """Test has_issues returns False when no issues."""
        result = ValidationResult(is_valid=True)
        assert result.has_issues() is False
    
    def test_has_issues_with_errors(self):
        """Test has_issues returns True when errors present."""
        result = ValidationResult(is_valid=False, errors=["Error 1"])
        assert result.has_issues() is True
    
    def test_has_issues_with_warnings(self):
        """Test has_issues returns True when warnings present."""
        result = ValidationResult(is_valid=True, warnings=["Warning 1"])
        assert result.has_issues() is True


class TestPreFlightValidator:
    """Test cases for PreFlightValidator."""
    
    def test_init(self, validator):
        """Test PreFlightValidator initialization."""
        assert validator is not None
        assert validator.console is not None
    
    def test_validate_local_mode_missing_api_key(self, validator):
        """Test validation fails when API key is missing."""
        config = {
            "mode": "local",
            "local": {}
        }
        
        with patch.dict(os.environ, {}, clear=True):
            result = validator.validate(config, "local")
        
        assert result.is_valid is False
        assert any("API key" in error for error in result.errors)
    
    def test_validate_local_mode_invalid_api_key(self, validator):
        """Test validation warns when API key is too short."""
        config = {
            "mode": "local",
            "local": {
                "api_key": "short"
            }
        }
        
        with patch.dict(os.environ, {}, clear=True):
            result = validator.validate(config, "local")
        
        assert any("too short" in warning.lower() for warning in result.warnings)
    
    @patch('google.genai.Client')
    def test_validate_local_mode_valid_api_key(self, mock_client_class, validator):
        """Test validation passes with valid API key."""
        # Mock successful API call
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_models.list.return_value = []
        mock_client.models = mock_models
        mock_client_class.return_value = mock_client
        
        config = {
            "mode": "local",
            "local": {
                "api_key": "valid_api_key_1234567890"
            }
        }
        
        with patch.dict(os.environ, {}, clear=True):
            result = validator.validate(config, "local")
        
        # Should not have API key errors (other validations may fail)
        assert not any("API key" in error for error in result.errors)
    
    def test_validate_googlecloud_mode_missing_adc(self, validator):
        """Test validation fails when ADC file is missing."""
        config = {
            "mode": "googlecloud",
            "googlecloud": {}
        }
        
        result = validator.validate(config, "googlecloud")
        
        assert any("ADC file" in error for error in result.errors)
    
    def test_validate_googlecloud_mode_adc_not_found(self, validator):
        """Test validation fails when ADC file doesn't exist."""
        config = {
            "mode": "googlecloud",
            "googlecloud": {
                "adc_file": "/nonexistent/path/adc.json"
            }
        }
        
        result = validator.validate(config, "googlecloud")
        
        assert any("not found" in error.lower() for error in result.errors)
    
    def test_validate_paths_missing_image_dir(self, validator, temp_dir):
        """Test validation fails when image directory is missing."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": "/nonexistent/path",
                "output_dir": temp_dir
            },
            "context": {}
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        assert any("image" in error.lower() for error in result.errors)
    
    def test_validate_paths_missing_output_dir(self, validator, temp_dir):
        """Test validation fails when output directory is missing."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": "/nonexistent/output"
            },
            "context": {}
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        assert any("output" in error.lower() for error in result.errors)
    
    def test_validate_context_missing_archive_reference(self, validator, temp_dir):
        """Test validation warns when archive reference is missing."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": temp_dir
            },
            "context": {}
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        assert any("archive" in warning.lower() for warning in result.warnings)
    
    def test_validate_context_complete(self, validator, temp_dir):
        """Test validation passes with complete context."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": temp_dir
            },
            "context": {
                "archive_reference": "Ф. 487, оп. 1, спр. 545",
                "document_type": "Birth records",
                "date_range": "1850-1900",
                "main_villages": [{"name": "Княжа"}],
                "common_surnames": ["Іванов"]
            }
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        # Should not have context warnings
        assert not any("archive" in warning.lower() for warning in result.warnings)
    
    def test_validate_prompt_assembly_missing_template(self, validator, temp_dir):
        """Test validation fails when prompt template is missing."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": temp_dir
            },
            "context": {},
            "prompt_template": "nonexistent-template"
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        assert any("template" in error.lower() for error in result.errors)
    
    def test_validate_images_no_images(self, validator, temp_dir):
        """Test validation errors when no images found."""
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": temp_dir
            },
            "context": {}
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key_1234567890"}):
            with patch('google.genai.Client') as mock_client_class:
                mock_client = MagicMock()
                mock_models = MagicMock()
                mock_models.list.return_value = []
                mock_client.models = mock_models
                mock_client_class.return_value = mock_client
                result = validator.validate(config, "local")
        
        # Check for errors about images (implementation adds error, not warning)
        assert any("image" in error.lower() or "no image" in error.lower() for error in result.errors)
    
    def test_validate_images_found(self, validator, temp_dir):
        """Test validation passes when images are found."""
        # Create test image files
        for i in range(1, 4):
            image_path = os.path.join(temp_dir, f"image{i:05d}.jpg")
            with open(image_path, 'w') as f:
                f.write("fake image")
        
        config = {
            "mode": "local",
            "local": {
                "image_dir": temp_dir,
                "output_dir": temp_dir
            },
            "context": {
                "archive_reference": "Ф. 487"
            }
        }
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            result = validator.validate(config, "local")
        
        # Should not have image warnings
        assert not any("no images" in warning.lower() for warning in result.warnings)
