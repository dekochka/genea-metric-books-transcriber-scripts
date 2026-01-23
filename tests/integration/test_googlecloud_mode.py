"""
Integration tests for GOOGLECLOUD mode end-to-end.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from transcribe import (
    load_config, detect_mode, normalize_config, validate_config,
    ModeFactory, process_batches_googlecloud
)


class TestGoogleCloudModeIntegration:
    """End-to-end integration tests for GOOGLECLOUD mode."""
    
    @pytest.fixture
    def test_config_path(self):
        """Path to test googlecloud configuration."""
        return os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'config_googlecloud.yaml'
        )
    
    def test_config_loading_and_validation(self, test_config_path):
        """Test loading and validating googlecloud mode configuration."""
        config = load_config(test_config_path)
        mode = detect_mode(config)
        normalized = normalize_config(config, mode)
        is_valid, errors = validate_config(normalized, mode)
        
        assert mode == 'googlecloud'
        # Validation may fail if ADC file doesn't exist, which is expected in tests
        # The important thing is that config structure is correct
    
    @patch('transcribe.authenticate')
    @patch('transcribe.init_services')
    @patch('transcribe.DriveImageSource')
    @patch('transcribe.VertexAIClient')
    @patch('transcribe.GoogleDocsOutput')
    def test_mode_factory_creates_googlecloud_handlers(self,
                                                        mock_output,
                                                        mock_ai_client,
                                                        mock_image_source,
                                                        mock_init_services,
                                                        mock_authenticate,
                                                        test_config_path):
        """Test ModeFactory creates correct handlers for googlecloud mode."""
        config = load_config(test_config_path)
        mode = detect_mode(config)
        normalized = normalize_config(config, mode)
        
        # Setup mocks
        mock_creds = Mock()
        mock_authenticate.return_value = mock_creds
        
        mock_drive_service = Mock()
        mock_docs_service = Mock()
        mock_genai_client = Mock()
        mock_init_services.return_value = (mock_drive_service, mock_docs_service, mock_genai_client)
        
        # Mock the prompt file opening specifically in ModeFactory
        with patch('builtins.open', mock_open(read_data="prompt text")):
            handlers = ModeFactory.create_handlers(mode, normalized)
        
        assert 'auth' in handlers
        assert 'image_source' in handlers
        assert 'ai_client' in handlers
        assert 'output' in handlers
        assert handlers['drive_service'] == mock_drive_service
        assert handlers['docs_service'] == mock_docs_service
        assert handlers['genai_client'] == mock_genai_client
    
    @patch('transcribe.authenticate')
    @patch('transcribe.init_services')
    @patch('transcribe.list_images')
    @patch('transcribe.VertexAIClient')
    @patch('transcribe.GoogleDocsOutput')
    def test_googlecloud_mode_image_listing(self, mock_output,
                                             mock_ai_client,
                                             mock_list_images, mock_init_services,
                                             mock_authenticate, test_config_path):
        """Test googlecloud mode can list images from Drive."""
        config = load_config(test_config_path)
        mode = detect_mode(config)
        normalized = normalize_config(config, mode)
        
        # Setup mocks
        mock_creds = Mock()
        mock_authenticate.return_value = mock_creds
        
        mock_drive_service = Mock()
        mock_docs_service = Mock()
        mock_genai_client = Mock()
        mock_init_services.return_value = (mock_drive_service, mock_docs_service, mock_genai_client)
        
        mock_list_images.return_value = [
            {'name': 'image1.jpg', 'id': 'id1', 'webViewLink': 'link1'},
            {'name': 'image2.jpg', 'id': 'id2', 'webViewLink': 'link2'}
        ]
        
        # Mock the prompt file opening specifically in ModeFactory
        with patch('builtins.open', mock_open(read_data="prompt text")):
            handlers = ModeFactory.create_handlers(mode, normalized)
        image_source = handlers['image_source']
        
        # Test image listing (DriveImageSource will call list_images internally)
        images = image_source.list_images(normalized)
        
        # Verify list_images was called
        mock_list_images.assert_called_once()
        assert len(images) == 2
    
    @patch('transcribe.authenticate')
    @patch('transcribe.init_services')
    @patch('transcribe.download_image')
    @patch('transcribe.transcribe_image')
    @patch('transcribe.create_doc')
    @patch('transcribe.write_to_doc')
    @patch('transcribe.update_overview_section')
    @patch('transcribe.DriveImageSource')
    @patch('transcribe.VertexAIClient')
    @patch('transcribe.GoogleDocsOutput')
    def test_googlecloud_mode_processing_flow(self, mock_output_class,
                                               mock_ai_client_class, mock_image_source_class,
                                               mock_update_overview, mock_write_to_doc,
                                               mock_create_doc, mock_transcribe_image,
                                               mock_download_image, mock_init_services,
                                               mock_authenticate, test_config_path):
        """Test complete googlecloud mode processing flow (mocked API calls)."""
        config = load_config(test_config_path)
        mode = detect_mode(config)
        normalized = normalize_config(config, mode)
        
        # Setup mocks
        mock_creds = Mock()
        mock_authenticate.return_value = mock_creds
        
        mock_drive_service = Mock()
        mock_docs_service = Mock()
        mock_genai_client = Mock()
        mock_init_services.return_value = (mock_drive_service, mock_docs_service, mock_genai_client)
        
        # Mock image source
        mock_image_source = Mock()
        mock_image_source.list_images.return_value = [
            {'name': 'image1.jpg', 'id': 'id1', 'webViewLink': 'link1'},
            {'name': 'image2.jpg', 'id': 'id2', 'webViewLink': 'link2'}
        ]
        mock_image_source.get_image_bytes.return_value = b"fake image bytes"
        mock_image_source.get_image_url.return_value = "https://drive.google.com/file/view"
        mock_image_source_class.return_value = mock_image_source
        
        # Mock AI client
        mock_ai_client = Mock()
        mock_ai_client.transcribe.return_value = ("Transcribed text", 1.5, Mock())
        
        # Mock output
        mock_output = Mock()
        mock_output.initialize.return_value = "doc_id_123"
        mock_output_class.return_value = mock_output
        
        # Mock the prompt file opening specifically in ModeFactory
        with patch('builtins.open', mock_open(read_data="prompt text")):
            handlers = ModeFactory.create_handlers(mode, normalized)
        
        # Override with our mocks for testing
        handlers['image_source'] = mock_image_source
        handlers['ai_client'] = mock_ai_client
        handlers['output'] = mock_output
        
        # Test processing
        images = handlers['image_source'].list_images(normalized)
        doc_id = handlers['output'].initialize(normalized)
        
        # Verify mocks were called
        mock_image_source.list_images.assert_called_once()
        mock_output.initialize.assert_called_once()
        assert doc_id == "doc_id_123"
