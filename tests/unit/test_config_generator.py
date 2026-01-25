"""
Unit tests for ConfigGenerator
"""
import os
import pytest
import tempfile
import yaml
from wizard.config_generator import ConfigGenerator


@pytest.fixture
def generator():
    """Create ConfigGenerator instance."""
    return ConfigGenerator()


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestConfigGenerator:
    """Test cases for ConfigGenerator."""
    
    def test_init(self, generator):
        """Test ConfigGenerator initialization."""
        assert generator is not None
        assert generator.console is not None
    
    def test_generate_local_mode_basic(self, generator, temp_output_dir):
        """Test generating config for LOCAL mode."""
        wizard_data = {
            "mode": "local",
            "local": {
                "image_dir": "/path/to/images",
                "output_dir": "/path/to/output"
            },
            "context": {
                "archive_reference": "Ф. 487, оп. 1, спр. 545",
                "document_type": "Birth records",
                "date_range": "1850-1900",
                "main_villages": [
                    {"name": "Княжа", "variants": ["Knyazha"]}
                ],
                "common_surnames": ["Іванов", "Петров"]
            },
            "prompt_template": "metric-book-birth",
            "archive_index": "487-1-545",
            "image_start_number": 1,
            "image_count": 10
        }
        
        output_path = os.path.join(temp_output_dir, "test-config.yaml")
        result_path = generator.generate(wizard_data, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify YAML content
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config['mode'] == 'local'
        assert config['local']['image_dir'] == '/path/to/images'
        assert config['context']['archive_reference'] == 'Ф. 487, оп. 1, спр. 545'
        assert config['prompt_template'] == 'metric-book-birth'
        assert config['archive_index'] == '487-1-545'
    
    def test_generate_googlecloud_mode(self, generator, temp_output_dir):
        """Test generating config for GOOGLECLOUD mode."""
        wizard_data = {
            "mode": "googlecloud",
            "googlecloud": {
                "drive_folder_id": "abc123",
                "output_dir": "/path/to/output"
            },
            "context": {
                "archive_reference": "Ф. 487, оп. 1, спр. 545"
            },
            "prompt_template": "metric-book-birth",
            "batch_size_for_doc": 50,
            "max_images": 100
        }
        
        output_path = os.path.join(temp_output_dir, "test-config.yaml")
        generator.generate(wizard_data, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config['mode'] == 'googlecloud'
        assert config['googlecloud']['drive_folder_id'] == 'abc123'
        assert config['batch_size_for_doc'] == 50
        assert config['max_images'] == 100
    
    def test_format_context_section(self, generator):
        """Test context section formatting."""
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545',
            'document_type': 'Birth records',
            'date_range': '1850-1900',
            'title_page_filename': 'cover.jpg',
            'main_villages': [
                {'name': 'Княжа', 'variants': ['Knyazha']}
            ],
            'additional_villages': [
                {'name': 'Шубино', 'variants': []}
            ],
            'common_surnames': ['Іванов', 'Петров']
        }
        
        formatted = generator._format_context_section(context)
        
        assert formatted['archive_reference'] == 'Ф. 487, оп. 1, спр. 545'
        assert formatted['document_type'] == 'Birth records'
        assert formatted['date_range'] == '1850-1900'
        assert formatted['title_page_filename'] == 'cover.jpg'
        assert len(formatted['main_villages']) == 1
        assert len(formatted['additional_villages']) == 1
        assert len(formatted['common_surnames']) == 2
    
    def test_format_context_section_partial(self, generator):
        """Test context section formatting with partial data."""
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545'
        }
        
        formatted = generator._format_context_section(context)
        
        assert formatted['archive_reference'] == 'Ф. 487, оп. 1, спр. 545'
        assert 'document_type' not in formatted
        assert 'main_villages' not in formatted
    
    def test_format_context_section_empty(self, generator):
        """Test context section formatting with empty context."""
        formatted = generator._format_context_section({})
        assert len(formatted) == 0
    
    def test_generate_creates_output_directory(self, generator, temp_output_dir):
        """Test that output directory is created if it doesn't exist."""
        wizard_data = {
            "mode": "local",
            "local": {"image_dir": "/path/to/images", "output_dir": "/path/to/output"},
            "context": {"archive_reference": "Ф. 487"}
        }
        
        nested_dir = os.path.join(temp_output_dir, "nested", "subdir")
        output_path = os.path.join(nested_dir, "config.yaml")
        
        generator.generate(wizard_data, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.isdir(nested_dir)
    
    def test_generate_retry_settings(self, generator, temp_output_dir):
        """Test that retry settings are included."""
        wizard_data = {
            "mode": "local",
            "local": {"image_dir": "/path/to/images", "output_dir": "/path/to/output"},
            "context": {},
            "retry_mode": True,
            "retry_image_list": [1, 5, 10]
        }
        
        output_path = os.path.join(temp_output_dir, "config.yaml")
        generator.generate(wizard_data, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config['retry_mode'] is True
        assert config['retry_image_list'] == [1, 5, 10]
    
    def test_generate_defaults(self, generator, temp_output_dir):
        """Test that default values are set correctly."""
        wizard_data = {
            "mode": "local",
            "local": {"image_dir": "/path/to/images", "output_dir": "/path/to/output"},
            "context": {}
        }
        
        output_path = os.path.join(temp_output_dir, "config.yaml")
        generator.generate(wizard_data, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config['retry_mode'] is False
        assert config['retry_image_list'] == []
    
    def test_generate_yaml_unicode_support(self, generator, temp_output_dir):
        """Test that YAML generation supports Unicode characters."""
        wizard_data = {
            "mode": "local",
            "local": {"image_dir": "/path/to/images", "output_dir": "/path/to/output"},
            "context": {
                "archive_reference": "Ф. 487, оп. 1, спр. 545",
                "main_villages": [
                    {"name": "Княжа", "variants": ["Knyazha"]}
                ],
                "common_surnames": ["Іванов", "Петров"]
            }
        }
        
        output_path = os.path.join(temp_output_dir, "config.yaml")
        generator.generate(wizard_data, output_path)
        
        # Verify file can be read and contains Unicode
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Ф. 487" in content
            assert "Княжа" in content
            assert "Іванов" in content
        
        # Verify YAML can be parsed
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            assert config['context']['archive_reference'] == "Ф. 487, оп. 1, спр. 545"
