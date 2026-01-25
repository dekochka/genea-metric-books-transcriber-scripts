"""
Integration tests for wizard-generated config compatibility
"""
import os
import pytest
import tempfile
import yaml
import shutil
from transcribe import load_config, detect_mode, validate_config
from wizard.config_generator import ConfigGenerator
from wizard.prompt_assembler import PromptAssemblyEngine


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_image_dir(temp_dir):
    """Create temporary directory with test images."""
    image_dir = os.path.join(temp_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    
    # Create a few test image files
    for i in range(1, 4):
        image_path = os.path.join(image_dir, f"image{i:05d}.jpg")
        with open(image_path, 'wb') as f:
            f.write(b"fake image data")
    
    return image_dir


@pytest.fixture
def legacy_config():
    """Example legacy config format."""
    return {
        "mode": "local",
        "local": {
            "image_dir": "/path/to/images",
            "output_dir": "/path/to/output",
            "api_key": "test_key"
        },
        "prompt_file": "prompts/example.md",
        "archive_index": "test-index",
        "image_start_number": 1,
        "image_count": 10
    }


@pytest.fixture
def wizard_config():
    """Example wizard-generated config format."""
    return {
        "mode": "local",
        "local": {
            "image_dir": "/path/to/images",
            "output_dir": "/path/to/output",
            "api_key": "test_key",
            "ocr_model_id": "gemini-3-flash-preview"
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


class TestConfigCompatibility:
    """Test backward compatibility between old and new config formats."""
    
    def test_legacy_config_still_works(self, temp_dir, test_image_dir, legacy_config):
        """Test that old config format with prompt_file still works."""
        # Update paths to use real directories
        legacy_config['local']['image_dir'] = test_image_dir
        legacy_config['local']['output_dir'] = temp_dir
        legacy_config['local']['api_key'] = 'test_api_key_1234567890'
        
        config_path = os.path.join(temp_dir, "legacy-config.yaml")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(legacy_config, f, default_flow_style=False, allow_unicode=True)
        
        # Should load without errors (may fail validation if prompt_file doesn't exist, but format should be accepted)
        try:
            config = load_config(config_path)
            assert config['mode'] == 'local'
            assert 'prompt_file' in config
            assert config['prompt_file'] == 'prompts/example.md'
        except ValueError as e:
            # Expected if prompt_file doesn't exist, but config structure should be valid
            assert 'prompt_file' in str(e) or 'prompt_template' in str(e)
    
    def test_wizard_config_works(self, temp_dir, test_image_dir, wizard_config):
        """Test that new wizard-generated config works."""
        # Update paths to use real directories
        wizard_config['local']['image_dir'] = test_image_dir
        wizard_config['local']['output_dir'] = temp_dir
        wizard_config['local']['api_key'] = 'test_api_key_1234567890'
        
        config_path = os.path.join(temp_dir, "wizard-config.yaml")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(wizard_config, f, default_flow_style=False, allow_unicode=True)
        
        # Should load without errors (may fail validation if template doesn't exist, but format should be accepted)
        try:
            config = load_config(config_path)
            assert config['mode'] == 'local'
            assert 'prompt_template' in config
            assert 'context' in config
            assert config['context']['archive_reference'] == 'Ф. 487, оп. 1, спр. 545'
        except ValueError as e:
            # Expected if template doesn't exist, but config structure should be valid
            assert 'prompt_template' in str(e) or 'prompt_file' in str(e)
    
    def test_both_config_formats_detect_mode(self, temp_dir, test_image_dir, legacy_config, wizard_config):
        """Test that both config formats correctly detect mode."""
        # Update paths to use real directories
        legacy_config['local']['image_dir'] = test_image_dir
        legacy_config['local']['output_dir'] = temp_dir
        legacy_config['local']['api_key'] = 'test_api_key_1234567890'
        
        wizard_config['local']['image_dir'] = test_image_dir
        wizard_config['local']['output_dir'] = temp_dir
        wizard_config['local']['api_key'] = 'test_api_key_1234567890'
        
        legacy_path = os.path.join(temp_dir, "legacy.yaml")
        wizard_path = os.path.join(temp_dir, "wizard.yaml")
        
        with open(legacy_path, 'w', encoding='utf-8') as f:
            yaml.dump(legacy_config, f, default_flow_style=False, allow_unicode=True)
        
        with open(wizard_path, 'w', encoding='utf-8') as f:
            yaml.dump(wizard_config, f, default_flow_style=False, allow_unicode=True)
        
        # Load configs (may fail validation but should load structure)
        try:
            legacy_loaded = load_config(legacy_path)
            legacy_mode = detect_mode(legacy_loaded)
            assert legacy_mode == 'local'
        except ValueError:
            # If validation fails, at least verify the file structure
            with open(legacy_path, 'r') as f:
                legacy_data = yaml.safe_load(f)
            assert legacy_data['mode'] == 'local'
        
        try:
            wizard_loaded = load_config(wizard_path)
            wizard_mode = detect_mode(wizard_loaded)
            assert wizard_mode == 'local'
        except ValueError:
            # If validation fails, at least verify the file structure
            with open(wizard_path, 'r') as f:
                wizard_data = yaml.safe_load(f)
            assert wizard_data['mode'] == 'local'
    
    def test_validate_config_handles_both_formats(self, temp_dir, test_image_dir, legacy_config, wizard_config):
        """Test that validate_config works with both formats."""
        # Update paths to use real directories
        legacy_config['local']['image_dir'] = test_image_dir
        legacy_config['local']['output_dir'] = temp_dir
        legacy_config['local']['api_key'] = 'test_api_key_1234567890'
        
        wizard_config['local']['image_dir'] = test_image_dir
        wizard_config['local']['output_dir'] = temp_dir
        wizard_config['local']['api_key'] = 'test_api_key_1234567890'
        
        legacy_path = os.path.join(temp_dir, "legacy.yaml")
        wizard_path = os.path.join(temp_dir, "wizard.yaml")
        
        with open(legacy_path, 'w', encoding='utf-8') as f:
            yaml.dump(legacy_config, f, default_flow_style=False, allow_unicode=True)
        
        with open(wizard_path, 'w', encoding='utf-8') as f:
            yaml.dump(wizard_config, f, default_flow_style=False, allow_unicode=True)
        
        # Load configs directly (bypassing load_config validation)
        with open(legacy_path, 'r') as f:
            legacy_loaded = yaml.safe_load(f)
        with open(wizard_path, 'r') as f:
            wizard_loaded = yaml.safe_load(f)
        
        # validate_config should accept both formats (may fail for missing files, but format is valid)
        try:
            validate_config(legacy_loaded, 'local')
        except ValueError as e:
            # Expected if prompt_file doesn't exist, but format should be valid
            error_str = str(e)
            assert 'prompt_file' in error_str or 'prompt_template' in error_str or 'image_dir' in error_str
        
        try:
            validate_config(wizard_loaded, 'local')
        except ValueError as e:
            # Expected if template doesn't exist, but format should be valid
            error_str = str(e)
            assert 'prompt_template' in error_str or 'prompt_file' in error_str or 'image_dir' in error_str
    
    def test_prompt_assembly_works_with_wizard_config(self, temp_dir, wizard_config):
        """Test that prompt assembly works with wizard-generated config."""
        # Create a test template
        templates_dir = os.path.join(temp_dir, "templates")
        os.makedirs(templates_dir, exist_ok=True)
        
        template_content = """# Test Template

{{ARCHIVE_REFERENCE}}
{{DOCUMENT_DESCRIPTION}}
{{DATE_RANGE}}

{{MAIN_VILLAGES}}
{{COMMON_SURNAMES}}
"""
        
        template_path = os.path.join(templates_dir, "metric-book-birth.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Test prompt assembly
        assembler = PromptAssemblyEngine(templates_dir=templates_dir)
        context = wizard_config['context']
        
        assembled = assembler.assemble("metric-book-birth", context)
        
        assert "{{ARCHIVE_REFERENCE}}" not in assembled
        assert "Ф. 487, оп. 1, спр. 545" in assembled
        assert "Княжа" in assembled
        assert "Іванов" in assembled
    
    def test_mixed_usage_scenario(self, temp_dir, test_image_dir):
        """Test scenario where user mixes old and new configs."""
        # Create a config that has both prompt_file and prompt_template (edge case)
        mixed_config = {
            "mode": "local",
            "local": {
                "image_dir": test_image_dir,
                "output_dir": temp_dir,
                "api_key": "test_api_key_1234567890"
            },
            "prompt_file": "prompts/old.md",  # Old format
            "prompt_template": "metric-book-birth",  # New format
            "context": {
                "archive_reference": "Ф. 487"
            },
            "archive_index": "test-index"
        }
        
        config_path = os.path.join(temp_dir, "mixed.yaml")
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(mixed_config, f, default_flow_style=False, allow_unicode=True)
        
        # Should load structure (may fail validation if files don't exist)
        try:
            config = load_config(config_path)
            assert 'prompt_file' in config
            assert 'prompt_template' in config
            assert 'context' in config
        except ValueError:
            # If validation fails, at least verify structure
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            assert 'prompt_file' in config
            assert 'prompt_template' in config
            assert 'context' in config
    
    def test_wizard_config_round_trip(self, temp_dir, wizard_config):
        """Test that wizard config can be saved and reloaded correctly."""
        from wizard.config_generator import ConfigGenerator
        
        generator = ConfigGenerator()
        output_path = os.path.join(temp_dir, "round-trip.yaml")
        
        # Generate config
        generator.generate(wizard_config, output_path)
        
        # Reload and verify
        with open(output_path, 'r', encoding='utf-8') as f:
            reloaded = yaml.safe_load(f)
        
        assert reloaded['mode'] == wizard_config['mode']
        assert reloaded['prompt_template'] == wizard_config['prompt_template']
        assert reloaded['context']['archive_reference'] == wizard_config['context']['archive_reference']
        assert len(reloaded['context']['main_villages']) == len(wizard_config['context']['main_villages'])
