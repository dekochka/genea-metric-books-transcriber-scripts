"""
Unit tests for ModeFactory.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from transcribe import ModeFactory


class TestModeFactory:
    """Tests for ModeFactory."""
    
    def test_create_handlers_local_mode(self):
        """Test create_handlers() for local mode."""
        config = {
            'local': {
                'api_key': 'test-api-key',
                'image_dir': '/test/images',
                'output_dir': '/test/output',
                'ocr_model_id': 'gemini-1.5-pro'
            }
        }
        
        with patch('transcribe.LocalAuthStrategy') as mock_auth, \
             patch('transcribe.LocalImageSource') as mock_image_source, \
             patch('transcribe.GeminiDevClient') as mock_ai_client, \
             patch('transcribe.LogFileOutput') as mock_output, \
             patch('transcribe.logging.getLogger') as mock_logger:
            
            mock_auth_instance = Mock()
            mock_auth_instance.authenticate.return_value = 'test-api-key'
            mock_auth.return_value = mock_auth_instance
            
            handlers = ModeFactory.create_handlers('local', config)
            
            assert 'auth' in handlers
            assert 'image_source' in handlers
            assert 'ai_client' in handlers
            assert 'output' in handlers
            assert handlers['drive_service'] is None
            assert handlers['docs_service'] is None
    
    @patch('transcribe.GoogleCloudAuthStrategy')
    @patch('transcribe.init_services')
    @patch('transcribe.DriveImageSource')
    @patch('transcribe.VertexAIClient')
    @patch('transcribe.GoogleDocsOutput')
    @patch('builtins.open', create=True)
    def test_create_handlers_googlecloud_mode(self, mock_open, mock_output, mock_ai_client,
                                               mock_image_source, mock_init_services, mock_auth):
        """Test create_handlers() for googlecloud mode."""
        config = {
            'googlecloud': {
                'project_id': 'test-project',
                'drive_folder_id': 'folder123',
                'adc_file': 'adc.json',
                'ocr_model_id': 'gemini-3-flash-preview',
                'document_name': 'Test Doc'
            },
            'prompt_file': 'prompt.txt'
        }
        
        # Setup mocks
        mock_auth_instance = Mock()
        mock_creds = Mock()
        mock_auth_instance.authenticate.return_value = mock_creds
        mock_auth.return_value = mock_auth_instance
        
        mock_drive_service = Mock()
        mock_docs_service = Mock()
        mock_genai_client = Mock()
        mock_init_services.return_value = (mock_drive_service, mock_docs_service, mock_genai_client)
        
        mock_open.return_value.__enter__.return_value.read.return_value = "prompt text"
        
        handlers = ModeFactory.create_handlers('googlecloud', config)
        
        assert 'auth' in handlers
        assert 'image_source' in handlers
        assert 'ai_client' in handlers
        assert 'output' in handlers
        assert handlers['drive_service'] == mock_drive_service
        assert handlers['docs_service'] == mock_docs_service
        assert handlers['genai_client'] == mock_genai_client
    
    def test_create_handlers_invalid_mode(self):
        """Test create_handlers() with invalid mode raises error."""
        with pytest.raises(ValueError, match="Unknown mode"):
            ModeFactory.create_handlers('invalid_mode', {})
    
    def test_create_handlers_local_mode_uses_env_var(self):
        """Test create_handlers() for local mode uses environment variable for API key."""
        import os
        config = {
            'local': {
                'image_dir': '/test/images',
                'output_dir': '/test/output',
                'ocr_model_id': 'gemini-1.5-pro'
                # No api_key - should use env var
            }
        }
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'env-api-key'}), \
             patch('transcribe.LocalAuthStrategy') as mock_auth, \
             patch('transcribe.LocalImageSource'), \
             patch('transcribe.GeminiDevClient'), \
             patch('transcribe.LogFileOutput'), \
             patch('transcribe.logging.getLogger'):
            
            mock_auth_instance = Mock()
            mock_auth_instance.authenticate.return_value = 'env-api-key'
            mock_auth.return_value = mock_auth_instance
            
            handlers = ModeFactory.create_handlers('local', config)
            
            # Verify LocalAuthStrategy was called with None (to use env var)
            mock_auth.assert_called_once_with(None)
            assert handlers['auth'] == mock_auth_instance
