"""
Unit tests for WizardController
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from wizard.wizard_controller import WizardController
from wizard.steps.base_step import WizardStep


class MockStep(WizardStep):
    """Mock wizard step for testing."""
    
    def __init__(self, controller, step_data=None, should_cancel=False):
        """Initialize mock step."""
        super().__init__(controller)
        self.step_data = step_data or {}
        self.should_cancel = should_cancel
        self.run_called = False
    
    def run(self):
        """Mock run method."""
        self.run_called = True
        if self.should_cancel:
            return None
        return self.step_data
    
    def validate(self, data):
        """Mock validate method."""
        return True, []


class TestWizardController:
    """Test cases for WizardController."""
    
    def test_init(self):
        """Test WizardController initialization."""
        controller = WizardController()
        assert controller.steps == []
        assert controller.collected_data == {}
        assert controller.console is not None
    
    def test_add_step(self):
        """Test adding steps to controller."""
        controller = WizardController()
        step1 = MockStep(controller)
        step2 = MockStep(controller)
        
        controller.add_step(step1)
        controller.add_step(step2)
        
        assert len(controller.steps) == 2
        assert controller.steps[0] == step1
        assert controller.steps[1] == step2
    
    def test_get_data_existing(self):
        """Test getting existing data."""
        controller = WizardController()
        controller.collected_data['test_key'] = 'test_value'
        
        result = controller.get_data('test_key')
        assert result == 'test_value'
    
    def test_get_data_missing_with_default(self):
        """Test getting missing data with default value."""
        controller = WizardController()
        
        result = controller.get_data('missing_key', default='default_value')
        assert result == 'default_value'
    
    def test_get_data_missing_no_default(self):
        """Test getting missing data without default."""
        controller = WizardController()
        
        result = controller.get_data('missing_key')
        assert result is None
    
    def test_set_data(self):
        """Test setting data."""
        controller = WizardController()
        
        controller.set_data('key1', 'value1')
        controller.set_data('key2', 42)
        
        assert controller.collected_data['key1'] == 'value1'
        assert controller.collected_data['key2'] == 42
    
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.config_generator.ConfigGenerator')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('questionary.path')
    def test_run_single_step(self, mock_questionary_path, mock_validator_class, mock_config_generator_class, 
                             mock_detect_mode, mock_load_config):
        """Test running wizard with single step."""
        controller = WizardController()
        
        step_data = {'mode': 'local', 'image_dir': '/path/to/images'}
        step = MockStep(controller, step_data=step_data)
        controller.add_step(step)
        
        # Mock config generator
        mock_generator = MagicMock()
        mock_generator.generate.return_value = '/path/to/config.yaml'
        mock_config_generator_class.return_value = mock_generator
        
        # Mock validation
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.has_issues.return_value = False
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator
        
        # Mock config loading
        mock_load_config.return_value = {}
        mock_detect_mode.return_value = 'local'
        
        result = controller.run(output_path='/path/to/config.yaml')
        
        assert step.run_called is True
        assert result == '/path/to/config.yaml'
        mock_generator.generate.assert_called_once()
    
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.config_generator.ConfigGenerator')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('questionary.path')
    def test_run_multiple_steps(self, mock_questionary_path, mock_validator_class, mock_config_generator_class,
                                mock_detect_mode, mock_load_config):
        """Test running wizard with multiple steps."""
        controller = WizardController()
        
        step1 = MockStep(controller, step_data={'mode': 'local'})
        step2 = MockStep(controller, step_data={'image_dir': '/path/to/images'})
        step3 = MockStep(controller, step_data={'output_dir': '/path/to/output'})
        
        controller.add_step(step1)
        controller.add_step(step2)
        controller.add_step(step3)
        
        # Mock config generator
        mock_generator = MagicMock()
        mock_generator.generate.return_value = '/path/to/config.yaml'
        mock_config_generator_class.return_value = mock_generator
        
        # Mock questionary for output path
        mock_questionary_path.return_value.ask.return_value = '/path/to/config.yaml'
        
        # Mock validation
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.has_issues.return_value = False
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator
        
        # Mock config loading
        mock_load_config.return_value = {}
        mock_detect_mode.return_value = 'local'
        
        result = controller.run()
        
        assert step1.run_called is True
        assert step2.run_called is True
        assert step3.run_called is True
        assert result is not None
    
    def test_run_step_cancels(self):
        """Test wizard cancellation when step returns None."""
        controller = WizardController()
        
        step1 = MockStep(controller, step_data={'mode': 'local'})
        step2 = MockStep(controller, should_cancel=True)  # This step cancels
        
        controller.add_step(step1)
        controller.add_step(step2)
        
        result = controller.run()
        
        assert step1.run_called is True
        assert step2.run_called is True
        assert result is None  # Wizard was cancelled
    
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.config_generator.ConfigGenerator')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('questionary.path')
    def test_run_data_passed_to_steps(self, mock_questionary_path, mock_validator_class, mock_config_generator_class,
                                      mock_detect_mode, mock_load_config):
        """Test that data is passed between steps."""
        controller = WizardController()
        
        # Create step that uses data from controller
        class DataUsingStep(WizardStep):
            def run(self):
                mode = self.controller.get_data('mode')
                return {'image_dir': f'/path/to/{mode}/images'}
            
            def validate(self, data):
                return True, []
        
        step1 = MockStep(controller, step_data={'mode': 'local'})
        step2 = DataUsingStep(controller)
        
        controller.add_step(step1)
        controller.add_step(step2)
        
        # Mock config generator
        mock_generator = MagicMock()
        mock_generator.generate.return_value = '/path/to/config.yaml'
        mock_config_generator_class.return_value = mock_generator
        
        # Mock questionary for output path
        mock_questionary_path.return_value.ask.return_value = '/path/to/config.yaml'
        
        # Mock validation
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.has_issues.return_value = False
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator
        
        # Mock config loading
        mock_load_config.return_value = {}
        mock_detect_mode.return_value = 'local'
        
        result = controller.run()
        
        assert result is not None
        # Verify step2 received data from step1
        assert controller.collected_data.get('mode') == 'local'
    
    @patch('transcribe.load_config')
    @patch('transcribe.detect_mode')
    @patch('wizard.config_generator.ConfigGenerator')
    @patch('wizard.preflight_validator.PreFlightValidator')
    @patch('questionary.path')
    def test_run_includes_validation(self, mock_questionary_path, mock_validator_class, mock_config_generator_class,
                                    mock_detect_mode, mock_load_config):
        """Test that wizard runs validation before generating config."""
        controller = WizardController()
        
        step = MockStep(controller, step_data={'mode': 'local'})
        controller.add_step(step)
        
        # Mock validator
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.has_issues.return_value = False
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator
        
        # Mock config generator
        mock_generator = MagicMock()
        mock_generator.generate.return_value = '/path/to/config.yaml'
        mock_config_generator_class.return_value = mock_generator
        
        # Mock questionary for output path
        mock_questionary_path.return_value.ask.return_value = '/path/to/config.yaml'
        
        # Mock config loading
        mock_load_config.return_value = {}
        mock_detect_mode.return_value = 'local'
        
        result = controller.run()
        
        # Validator should be called
        mock_validator.validate.assert_called_once()
        assert result is not None
