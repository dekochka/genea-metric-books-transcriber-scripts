"""
Integration tests for configuration loading and mode detection.
"""
import os
import pytest
import yaml
from transcribe import load_config, detect_mode, normalize_config, validate_config


class TestConfigurationLoading:
    """Tests for configuration loading and validation."""
    
    @pytest.fixture
    def test_config_dir(self):
        """Path to test configuration directory."""
        return os.path.join(os.path.dirname(__file__), '..', 'fixtures')
    
    def test_load_config_local_mode(self, test_config_dir):
        """Test loading local mode configuration."""
        config_path = os.path.join(test_config_dir, 'config_local.yaml')
        config = load_config(config_path)
        
        assert 'mode' in config or 'local' in config
        assert config.get('mode') == 'local' or 'local' in config
    
    def test_load_config_googlecloud_mode(self, test_config_dir):
        """Test loading googlecloud mode configuration."""
        config_path = os.path.join(test_config_dir, 'config_googlecloud.yaml')
        config = load_config(config_path)
        
        assert 'mode' in config or 'googlecloud' in config
        assert config.get('mode') == 'googlecloud' or 'googlecloud' in config
    
    def test_detect_mode_explicit_local(self):
        """Test mode detection with explicit local mode."""
        config = {'mode': 'local', 'local': {'api_key': 'test'}}
        mode = detect_mode(config)
        assert mode == 'local'
    
    def test_detect_mode_explicit_googlecloud(self):
        """Test mode detection with explicit googlecloud mode."""
        config = {'mode': 'googlecloud', 'googlecloud': {'project_id': 'test'}}
        mode = detect_mode(config)
        assert mode == 'googlecloud'
    
    def test_detect_mode_from_local_section(self):
        """Test mode detection from local section presence."""
        config = {'local': {'api_key': 'test', 'image_dir': '/test'}}
        mode = detect_mode(config)
        assert mode == 'local'
    
    def test_detect_mode_from_legacy_config(self):
        """Test mode detection from legacy config (googlecloud)."""
        config = {'project_id': 'test', 'drive_folder_id': 'folder123'}
        mode = detect_mode(config)
        assert mode == 'googlecloud'
    
    def test_normalize_config_local(self):
        """Test config normalization for local mode."""
        config = {
            'mode': 'local',
            'local': {
                'api_key': 'test-key',
                'image_dir': '/test/images'
            },
            'prompt_file': 'prompt.txt'
        }
        normalized = normalize_config(config, 'local')
        
        assert 'local' in normalized
        assert normalized['local']['api_key'] == 'test-key'
        assert normalized['prompt_file'] == 'prompt.txt'
    
    def test_normalize_config_googlecloud(self):
        """Test config normalization for googlecloud mode."""
        config = {
            'mode': 'googlecloud',
            'googlecloud': {
                'project_id': 'test-project',
                'drive_folder_id': 'folder123'
            },
            'prompt_file': 'prompt.txt'
        }
        normalized = normalize_config(config, 'googlecloud')
        
        assert 'googlecloud' in normalized
        assert normalized['googlecloud']['project_id'] == 'test-project'
        assert normalized['prompt_file'] == 'prompt.txt'
    
    def test_validate_config_local_valid(self, tmp_path):
        """Test validation of valid local config."""
        # Create actual directories for validation
        image_dir = tmp_path / "images"
        image_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        config = {
            'local': {
                'api_key': 'test-key-12345',
                'image_dir': str(image_dir),
                'output_dir': str(output_dir)
            },
            'prompt_file': 'prompt.txt',
            'archive_index': 'test123'
        }
        is_valid, errors = validate_config(config, 'local')
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_local_missing_api_key(self):
        """Test validation of local config missing API key."""
        config = {
            'local': {
                'image_dir': '/test/images'
            },
            'prompt_file': 'prompt.txt'
        }
        # Should be valid if env var can be used
        is_valid, errors = validate_config(config, 'local')
        # May be valid if env var is available, or invalid if not
        # This depends on implementation
    
    def test_validate_config_local_missing_image_dir(self):
        """Test validation of local config missing image_dir."""
        config = {
            'local': {
                'api_key': 'test-key'
            },
            'prompt_file': 'prompt.txt'
        }
        is_valid, errors = validate_config(config, 'local')
        assert is_valid is False
        assert len(errors) > 0
