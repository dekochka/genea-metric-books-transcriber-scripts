"""
Integration tests for complete wizard flow
"""
import os
import pytest
import tempfile
import yaml
import shutil
from unittest.mock import Mock, MagicMock, patch
from wizard.wizard_controller import WizardController
from wizard.steps.mode_selection_step import ModeSelectionStep
from wizard.steps.context_collection_step import ContextCollectionStep
from wizard.steps.processing_settings_step import ProcessingSettingsStep


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
def mock_wizard_data():
    """Mock wizard data for testing."""
    return {
        "mode": "local",
        "local": {
            "image_dir": "/path/to/images",
            "output_dir": "/path/to/output",
            "api_key": "test_api_key_1234567890",
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
        "image_count": 3
    }


class TestWizardFlow:
    """Integration tests for complete wizard flow."""
    
    @patch('questionary.path')
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('wizard.config_generator.ConfigGenerator')
    def test_wizard_generates_valid_config(self, mock_config_generator, mock_validator,
                                           mock_detect_mode, mock_load_config, mock_questionary_path,
                                           temp_dir, mock_wizard_data):
        """Test that wizard generates a valid YAML config file."""
        controller = WizardController()
        
        # Mock steps to return wizard data
        class MockModeStep:
            def run(self):
                return {"mode": "local", "local": mock_wizard_data["local"]}
            def validate(self, data):
                return True, []
        
        class MockContextStep:
            def run(self):
                return {"context": mock_wizard_data["context"]}
            def validate(self, data):
                return True, []
        
        class MockProcessingStep:
            def run(self):
                return {
                    "prompt_template": mock_wizard_data["prompt_template"],
                    "archive_index": mock_wizard_data["archive_index"],
                    "image_start_number": mock_wizard_data["image_start_number"],
                    "image_count": mock_wizard_data["image_count"]
                }
            def validate(self, data):
                return True, []
        
        step1 = MockModeStep()
        step1.controller = controller
        step2 = MockContextStep()
        step2.controller = controller
        step3 = MockProcessingStep()
        step3.controller = controller
        
        controller.add_step(step1)
        controller.add_step(step2)
        controller.add_step(step3)
        
        # Mock config generator
        output_path = os.path.join(temp_dir, "test-config.yaml")
        mock_generator = MagicMock()
        mock_generator.generate.return_value = output_path
        mock_config_generator.return_value = mock_generator
        
        # Mock questionary for output path
        mock_questionary_path.return_value.ask.return_value = output_path
        
        # Mock validation
        mock_validator_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.has_issues.return_value = False
        mock_validator_instance.validate.return_value = mock_result
        mock_validator.return_value = mock_validator_instance
        
        # Mock config loading
        mock_load_config.return_value = mock_wizard_data
        mock_detect_mode.return_value = 'local'
        
        # Run wizard
        result = controller.run()
        
        assert result == output_path
        mock_generator.generate.assert_called_once()
        
        # Verify the data passed to generator
        call_args = mock_generator.generate.call_args
        generated_data = call_args[0][0]
        
        assert generated_data["mode"] == "local"
        assert "context" in generated_data
        assert generated_data["context"]["archive_reference"] == "Ф. 487, оп. 1, спр. 545"
    
    def test_generated_config_structure(self, temp_dir, mock_wizard_data):
        """Test that generated config has correct structure."""
        from wizard.config_generator import ConfigGenerator
        
        generator = ConfigGenerator()
        output_path = os.path.join(temp_dir, "test-config.yaml")
        
        generator.generate(mock_wizard_data, output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Load and verify structure
        with open(output_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert config['mode'] == 'local'
        assert 'local' in config
        assert 'context' in config
        assert config['context']['archive_reference'] == 'Ф. 487, оп. 1, спр. 545'
        assert config['prompt_template'] == 'metric-book-birth'
        assert config['archive_index'] == '487-1-545'
    
    def test_generated_config_compatible_with_transcribe(self, temp_dir, test_image_dir, mock_wizard_data):
        """Test that generated config can be loaded by transcribe.py."""
        from wizard.config_generator import ConfigGenerator
        from transcribe import load_config, detect_mode
        
        # Update paths to use real test directories
        mock_wizard_data['local']['image_dir'] = test_image_dir
        mock_wizard_data['local']['output_dir'] = temp_dir
        mock_wizard_data['local']['api_key'] = 'test_api_key_1234567890'  # Valid length
        
        generator = ConfigGenerator()
        output_path = os.path.join(temp_dir, "test-config.yaml")
        
        generator.generate(mock_wizard_data, output_path)
        
        # Try to load config using transcribe.py functions
        # Note: load_config validates paths, so we need real paths
        config = load_config(output_path)
        mode = detect_mode(config)
        
        assert mode == 'local'
        assert config['mode'] == 'local'
        assert 'context' in config
        assert 'prompt_template' in config
    
    def test_wizard_handles_cancellation(self):
        """Test that wizard handles user cancellation gracefully."""
        controller = WizardController()
        
        class CancellingStep:
            def run(self):
                return None  # User cancelled
            def validate(self, data):
                return True, []
        
        step = CancellingStep()
        step.controller = controller
        controller.add_step(step)
        
        result = controller.run()
        
        # Should return None when cancelled
        assert result is None
    
    @patch('questionary.path')
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('wizard.config_generator.ConfigGenerator')
    def test_wizard_data_passed_between_steps(self, mock_gen, mock_val, mock_detect, 
                                              mock_load, mock_q_path, temp_dir):
        """Test that data collected in one step is available in subsequent steps."""
        controller = WizardController()
        
        collected_data = []
        
        class Step1:
            def run(self):
                data = {"mode": "local", "test_key": "test_value"}
                collected_data.append(data)
                return data
            def validate(self, data):
                return True, []
        
        class Step2:
            def run(self):
                # Should be able to access data from Step1
                mode = self.controller.get_data('mode')
                test_value = self.controller.get_data('test_key')
                data = {"context": {"archive_reference": f"Mode was {mode}, test was {test_value}"}}
                collected_data.append(data)
                return data
            def validate(self, data):
                return True, []
        
        step1 = Step1()
        step1.controller = controller
        step2 = Step2()
        step2.controller = controller
        
        controller.add_step(step1)
        controller.add_step(step2)
        
        mock_gen.return_value.generate.return_value = os.path.join(temp_dir, "test.yaml")
        mock_q_path.return_value.ask.return_value = os.path.join(temp_dir, "test.yaml")
        mock_val.return_value.validate.return_value = MagicMock(is_valid=True, has_issues=lambda: False)
        mock_load.return_value = {}
        mock_detect.return_value = 'local'
        
        controller.run()
        
        # Verify data was collected and passed
        assert len(collected_data) == 2
        assert collected_data[0]["mode"] == "local"
        assert "Mode was local" in collected_data[1]["context"]["archive_reference"]
