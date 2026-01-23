"""
Error handling tests for various error scenarios.
"""
import os
import pytest
from unittest.mock import Mock, patch
from transcribe import (
    LocalAuthStrategy, GoogleCloudAuthStrategy,
    LocalImageSource, DriveImageSource,
    ModeFactory, load_config, validate_config
)


class TestAuthenticationErrors:
    """Tests for authentication error scenarios."""
    
    def test_local_auth_missing_api_key(self):
        """Test LocalAuthStrategy error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                LocalAuthStrategy()
    
    def test_googlecloud_auth_missing_file(self):
        """Test GoogleCloudAuthStrategy error when ADC file is missing."""
        with patch('os.path.exists', return_value=False):
            strategy = GoogleCloudAuthStrategy("missing_file.json")
            assert strategy.validate() is False


class TestImageSourceErrors:
    """Tests for image source error scenarios."""
    
    def test_local_image_source_invalid_directory(self):
        """Test LocalImageSource error with invalid directory."""
        with pytest.raises(ValueError, match="Image directory does not exist"):
            LocalImageSource("/nonexistent/directory/12345")
    
    def test_local_image_source_empty_directory(self, tmp_path):
        """Test LocalImageSource with empty directory."""
        source = LocalImageSource(str(tmp_path))
        config = {
            'image_start_number': 1,
            'image_count': 10,
            'retry_mode': False,
            'retry_image_list': []
        }
        images = source.list_images(config)
        assert len(images) == 0  # Should return empty list, not raise error
    
    @patch('transcribe.list_images')
    def test_drive_image_source_api_error(self, mock_list_images):
        """Test DriveImageSource handles API errors."""
        mock_drive_service = Mock()
        mock_list_images.side_effect = Exception("Drive API Error")
        
        source = DriveImageSource(mock_drive_service, "folder123")
        config = {'image_start_number': 1, 'image_count': 10}
        
        with pytest.raises(Exception, match="Drive API Error"):
            source.list_images(config)


class TestConfigurationErrors:
    """Tests for configuration error scenarios."""
    
    def test_invalid_mode_value(self):
        """Test error with invalid mode value."""
        config = {'mode': 'invalid_mode'}
        # ModeFactory should raise ValueError
        with pytest.raises(ValueError, match="Unknown mode"):
            ModeFactory.create_handlers('invalid_mode', config)
    
    def test_missing_required_fields_local(self):
        """Test validation error with missing required fields for local mode."""
        config = {
            'local': {
                # Missing api_key and image_dir
            },
            'prompt_file': 'prompt.txt'
        }
        is_valid, errors = validate_config(config, 'local')
        assert is_valid is False
        assert len(errors) > 0
    
    def test_missing_required_fields_googlecloud(self):
        """Test validation error with missing required fields for googlecloud mode."""
        config = {
            'googlecloud': {
                # Missing required fields
            },
            'prompt_file': 'prompt.txt'
        }
        is_valid, errors = validate_config(config, 'googlecloud')
        assert is_valid is False
        assert len(errors) > 0
    
    def test_missing_prompt_file(self):
        """Test validation error with missing prompt_file."""
        config = {
            'local': {
                'api_key': 'test-key',
                'image_dir': '/test/images'
            }
            # Missing prompt_file
        }
        is_valid, errors = validate_config(config, 'local')
        assert is_valid is False
        assert any('prompt_file' in error.lower() for error in errors)


class TestOutputErrors:
    """Tests for output strategy error scenarios."""
    
    def test_google_docs_output_not_initialized(self):
        """Test GoogleDocsOutput error when writing before initialization."""
        from transcribe import GoogleDocsOutput
        
        mock_services = {
            'docs_service': Mock(),
            'drive_service': Mock(),
            'genai_client': Mock()
        }
        
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            {'document_name': 'Test'},
            "prompt"
        )
        # doc_id is None (not initialized)
        
        with pytest.raises(ValueError, match="Document not initialized"):
            output.write_batch([], 1, True)
    
    def test_google_docs_output_finalize_not_initialized(self):
        """Test GoogleDocsOutput error when finalizing before initialization."""
        from transcribe import GoogleDocsOutput
        
        mock_services = {
            'docs_service': Mock(),
            'drive_service': Mock(),
            'genai_client': Mock()
        }
        
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            {'document_name': 'Test'},
            "prompt"
        )
        
        with pytest.raises(ValueError, match="Document not initialized"):
            output.finalize([], {})


class TestAIClientErrors:
    """Tests for AI client error scenarios."""
    
    @patch('transcribe.genai.Client')
    @patch('time.time')
    @patch('time.sleep')
    def test_gemini_dev_client_api_error(self, mock_sleep, mock_time, mock_client_class):
        """Test GeminiDevClient handles API errors with retries."""
        import time
        
        mock_client = Mock()
        mock_models = Mock()
        # Simulate API error (non-retryable Exception - returns error message, doesn't raise)
        mock_models.generate_content.side_effect = Exception("API Error")
        mock_client.models = mock_models
        mock_client_class.return_value = mock_client
        
        # Need many time values for the function execution
        mock_time.side_effect = [0, 0, 0, 0.5, 0.5, 0.5, 0.5]  # Enough for one attempt
        
        from transcribe import GeminiDevClient
        client = GeminiDevClient("test-api-key", "gemini-1.5-pro")
        
        # Non-retryable exceptions return error message, don't raise
        text, elapsed_time, usage_metadata = client.transcribe(b"fake bytes", "test.jpg", "prompt")
        assert text.startswith("[Error during transcription:")
        assert usage_metadata is None
    
    @patch('transcribe.transcribe_image')
    def test_vertex_ai_client_delegation_error(self, mock_transcribe_image):
        """Test VertexAIClient propagates errors from transcribe_image."""
        mock_genai_client = Mock()
        mock_transcribe_image.side_effect = Exception("Vertex AI Error")
        
        from transcribe import VertexAIClient
        client = VertexAIClient(mock_genai_client, "gemini-3-flash-preview")
        
        with pytest.raises(Exception, match="Vertex AI Error"):
            client.transcribe(b"fake bytes", "test.jpg", "prompt")
