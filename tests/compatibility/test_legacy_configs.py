"""
Backward compatibility tests for legacy configurations.
"""
import os
import pytest
from unittest.mock import Mock, patch
from transcribe import load_config, detect_mode, normalize_config, validate_config, ModeFactory


class TestLegacyConfigCompatibility:
    """Tests for backward compatibility with legacy configurations."""
    
    def test_legacy_flat_config_structure(self):
        """Test that legacy flat config structure is detected as googlecloud mode."""
        legacy_config = {
            'project_id': 'test-project',
            'drive_folder_id': 'folder123',
            'adc_file': 'adc.json',
            'ocr_model_id': 'gemini-1.5-pro',
            'prompt_file': 'prompt.txt',
            'archive_index': 'test123',
            'image_start_number': 1,
            'image_count': 10,
            'batch_size_for_doc': 5
        }
        
        mode = detect_mode(legacy_config)
        assert mode == 'googlecloud'
        
        normalized = normalize_config(legacy_config, mode)
        assert 'googlecloud' in normalized
        assert normalized['googlecloud']['project_id'] == 'test-project'
        assert normalized['googlecloud']['drive_folder_id'] == 'folder123'
    
    def test_legacy_config_without_mode_field(self):
        """Test that config without explicit mode field is handled correctly."""
        # Config with googlecloud keys but no mode field
        config = {
            'project_id': 'test-project',
            'drive_folder_id': 'folder123',
            'googlecloud': {
                'project_id': 'test-project',
                'drive_folder_id': 'folder123'
            }
        }
        
        mode = detect_mode(config)
        # Should detect as googlecloud due to project_id/drive_folder_id
        assert mode == 'googlecloud'
    
    def test_legacy_config_normalization_preserves_all_fields(self):
        """Test that normalization preserves all legacy fields."""
        legacy_config = {
            'project_id': 'test-project',
            'drive_folder_id': 'folder123',
            'adc_file': 'adc.json',
            'ocr_model_id': 'gemini-1.5-pro',
            'prompt_file': 'prompt.txt',
            'archive_index': 'test123',
            'image_start_number': 1,
            'image_count': 10,
            'batch_size_for_doc': 5,
            'max_images': 100,
            'retry_mode': False,
            'retry_image_list': []
        }
        
        mode = detect_mode(legacy_config)
        normalized = normalize_config(legacy_config, mode)
        
        # Verify all fields are preserved
        assert normalized['prompt_file'] == 'prompt.txt'
        assert normalized['archive_index'] == 'test123'
        assert normalized['image_start_number'] == 1
        assert normalized['image_count'] == 10
        assert normalized['batch_size_for_doc'] == 5
        assert normalized['max_images'] == 100
        assert normalized['retry_mode'] is False
        assert normalized['retry_image_list'] == []
        
        # Verify googlecloud section has the right fields
        assert normalized['googlecloud']['project_id'] == 'test-project'
        assert normalized['googlecloud']['drive_folder_id'] == 'folder123'
        assert normalized['googlecloud']['adc_file'] == 'adc.json'
        assert normalized['googlecloud']['ocr_model_id'] == 'gemini-1.5-pro'
    
    @patch('transcribe.authenticate')
    @patch('transcribe.init_services')
    @patch('transcribe.DriveImageSource')
    @patch('transcribe.VertexAIClient')
    @patch('transcribe.GoogleDocsOutput')
    @patch('builtins.open', create=True)
    def test_legacy_config_works_with_mode_factory(self, mock_open, mock_output,
                                                     mock_ai_client, mock_image_source,
                                                     mock_init_services, mock_authenticate):
        """Test that legacy config works with ModeFactory."""
        legacy_config = {
            'project_id': 'test-project',
            'drive_folder_id': 'folder123',
            'adc_file': 'adc.json',
            'ocr_model_id': 'gemini-1.5-pro',
            'prompt_file': 'prompt.txt'
        }
        
        mode = detect_mode(legacy_config)
        normalized = normalize_config(legacy_config, mode)
        
        # Setup mocks
        mock_creds = Mock()
        mock_authenticate.return_value = mock_creds
        
        mock_drive_service = Mock()
        mock_docs_service = Mock()
        mock_genai_client = Mock()
        mock_init_services.return_value = (mock_drive_service, mock_docs_service, mock_genai_client)
        
        mock_open.return_value.__enter__.return_value.read.return_value = "prompt text"
        
        # Should not raise an error
        handlers = ModeFactory.create_handlers(mode, normalized)
        
        assert handlers is not None
        assert 'auth' in handlers
        assert 'image_source' in handlers
        assert 'ai_client' in handlers
        assert 'output' in handlers
    
    def test_mixed_legacy_and_new_config(self):
        """Test config that has both legacy and new structure."""
        mixed_config = {
            'mode': 'googlecloud',  # New explicit mode
            'project_id': 'test-project',  # Legacy field
            'drive_folder_id': 'folder123',  # Legacy field
            'googlecloud': {  # New nested structure
                'project_id': 'test-project',
                'drive_folder_id': 'folder123',
                'adc_file': 'adc.json'
            }
        }
        
        mode = detect_mode(mixed_config)
        assert mode == 'googlecloud'  # Should use explicit mode
        
        normalized = normalize_config(mixed_config, mode)
        # Should prefer nested structure if available
        assert 'googlecloud' in normalized
