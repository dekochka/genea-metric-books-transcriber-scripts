# Testing Patterns

**Analysis Date:** 2026-02-21

## Test Framework

**Runner:**
- pytest 7.x+ (version not pinned in requirements.txt)
- Config: `.pytest.ini`

**Assertion Library:**
- pytest built-in assertions
- Uses standard Python `assert` statements

**Run Commands:**
```bash
pytest                      # Run all tests
pytest --verbose           # Verbose output (default via addopts)
pytest --cov=transcribe    # Run with coverage (manual opt-in)
pytest -m unit             # Run unit tests only
pytest -m integration      # Run integration tests only
pytest -m local_mode       # Run local mode tests
pytest -m googlecloud_mode # Run googlecloud mode tests
```

## Test File Organization

**Location:**
- Separate `tests/` directory (not co-located)
- Subdirectories: `unit/`, `integration/`, `compatibility/`, `fixtures/`

**Naming:**
- Pattern: `test_*.py`
- Mirrors source structure where applicable:
  - `test_wizard_controller.py` → `wizard/wizard_controller.py`
  - `test_ai_clients.py` → tests AI client classes in `transcribe.py`
  - `test_config_generator.py` → `wizard/config_generator.py`

**Structure:**
```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/                       # Test data
│   ├── config_local.yaml
│   └── config_googlecloud.yaml
├── unit/                           # Unit tests
│   ├── test_ai_clients.py
│   ├── test_wizard_controller.py
│   ├── test_config_generator.py
│   └── ...
├── integration/                    # Integration tests
│   ├── test_config.py
│   ├── test_local_mode.py
│   ├── test_googlecloud_mode.py
│   └── test_wizard_flow.py
└── compatibility/                  # Backward compatibility tests
    └── test_legacy_configs.py
```

## Test Structure

**Suite Organization:**
```python
class TestWizardController:
    """Test cases for WizardController."""

    def test_init(self):
        """Test WizardController initialization."""
        controller = WizardController()
        assert controller.steps == []
        assert controller.collected_data == {}

    def test_add_step(self):
        """Test adding steps to controller."""
        controller = WizardController()
        step = MockStep(controller)
        controller.add_step(step)
        assert len(controller.steps) == 1
```

**Patterns:**
- Test class per source class: `class TestWizardController`
- Test method per function/behavior: `test_init`, `test_add_step`
- Descriptive docstrings for each test
- Group related tests in classes
- Use `pytest.fixture` for test setup

**Test naming:**
- `test_<function>_<scenario>` pattern
- Examples:
  - `test_load_config_local_mode`
  - `test_transcribe_with_retry`
  - `test_validate_config_local_missing_api_key`
- Descriptive names indicate what is tested and expected outcome

## Mocking

**Framework:** `unittest.mock`

**Patterns:**
```python
from unittest.mock import Mock, MagicMock, patch

# Mock objects
mock_client = Mock()
mock_client.models.generate_content.return_value = mock_response

# Patching
@patch('transcribe.genai.Client')
def test_init_creates_client(self, mock_client_class):
    mock_client_class.return_value = mock_client
    client = GeminiDevClient("test-api-key", "gemini-1.5-pro")
    mock_client_class.assert_called_once_with(api_key="test-api-key")

# Context manager patching
with patch.dict(os.environ, {'KEY': 'value'}):
    # Test code

# Multiple patches
@patch('transcribe.genai.Client')
@patch('time.time')
@patch('time.sleep')
def test_transcribe_success(self, mock_sleep, mock_time, mock_client_class):
    # Test with all mocks
```

**What to Mock:**
- External API clients: `genai.Client`, Google Drive/Docs services
- Time functions: `time.time()`, `time.sleep()` for retry testing
- File system: `os.path.exists()`, `os.stat()`
- Environment variables: `os.environ` (via `patch.dict`)
- Network calls: Any external service calls

**What NOT to Mock:**
- Simple data structures: dictionaries, lists
- Pure functions with no side effects
- Configuration objects (use real YAML fixtures)
- Internal business logic (test actual implementation)

## Fixtures and Factories

**Test Data:**
```python
# Shared fixtures in conftest.py
@pytest.fixture
def test_image_dir(tmp_path):
    """Fixture providing temporary directory with minimal test images."""
    for i in range(1, 4):  # Only 3 small test images
        (tmp_path / f"image{i:05d}.jpg").write_bytes(b"fake image data")
    return str(tmp_path)

@pytest.fixture
def test_images():
    """Fixture providing list of test image filenames."""
    return [
        'cover-title-page.jpg',
        'image00001.jpg',
        'image00002.jpg',
        'image00003.jpg'
    ]

# Auto-cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Auto-cleanup fixture to help with memory management."""
    yield
    gc.collect()  # Force garbage collection after each test
```

**Mock Factories:**
```python
# Mock step class for testing wizard
class MockStep(WizardStep):
    """Mock wizard step for testing."""

    def __init__(self, controller, step_data=None, should_cancel=False):
        super().__init__(controller)
        self.step_data = step_data or {}
        self.should_cancel = should_cancel
        self.run_called = False

    def run(self):
        self.run_called = True
        if self.should_cancel:
            return None
        return self.step_data

    def validate(self, data):
        return True, []
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Test data: `tests/fixtures/` directory (YAML configs, sample images)
- Mock classes: Defined inline in test files

## Coverage

**Requirements:** None enforced (disabled by default for memory efficiency)

**View Coverage:**
```bash
pytest --cov=transcribe           # Run with coverage
pytest --cov=transcribe --cov-report=html  # Generate HTML report
```

**Notes:**
- Coverage disabled by default in `.pytest.ini`: `addopts = --verbose --tb=short` (no --cov)
- Explicit opt-in when needed: `pytest --cov=transcribe`
- Memory-efficient settings to avoid accumulation during test runs
- HTML reports saved to `htmlcov/` directory

## Test Types

**Unit Tests:**
- Scope: Individual functions, classes, methods
- Location: `tests/unit/`
- Marker: `@pytest.mark.unit`
- Examples:
  - `test_ai_clients.py` - Tests AI client strategies in isolation
  - `test_wizard_controller.py` - Tests wizard controller methods
  - `test_config_generator.py` - Tests config generation logic
- Characteristics: Fast, isolated, heavy mocking

**Integration Tests:**
- Scope: Multiple components working together
- Location: `tests/integration/`
- Marker: `@pytest.mark.integration`
- Examples:
  - `test_config.py` - Tests configuration loading with real YAML files
  - `test_local_mode.py` - Tests local mode end-to-end flow
  - `test_wizard_flow.py` - Tests wizard multi-step flow
- Characteristics: Slower, uses real config files, minimal mocking

**Compatibility Tests:**
- Scope: Backward compatibility with legacy configs
- Location: `tests/compatibility/`
- Example: `test_legacy_configs.py`

## Common Patterns

**Async Testing:**
- Not used (synchronous code)
- AI API calls use synchronous client (no `async/await`)

**Error Testing:**
```python
def test_local_auth_missing_api_key(self):
    """Test LocalAuthStrategy error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API key required"):
            LocalAuthStrategy()

def test_invalid_mode_value(self):
    """Test error with invalid mode value."""
    config = {'mode': 'invalid_mode'}
    with pytest.raises(ValueError, match="Unknown mode"):
        ModeFactory.create_handlers('invalid_mode', config)
```

**Parametrized Tests:**
```python
@pytest.mark.parametrize("filename,expected", [
    ("image00001.jpg", 1),
    ("image00102.jpg", 102),
    ("IMG_20250814_0036.jpg", 36),
    ("004933159_00216.jpeg", 216),
])
def test_extract_image_number(filename, expected):
    """Test pattern: various filename formats"""
    result = extract_image_number(filename)
    assert result == expected
```

**Retry Testing:**
```python
def test_transcribe_with_retry(self, mock_logging, mock_sleep, mock_time, mock_client_class):
    """Test transcribe() retries on failure."""
    mock_models.generate_content.side_effect = [
        ConnectionError("API Error"),  # Retryable exception
        mock_response  # Success on retry
    ]

    text, elapsed_time, usage_metadata = client.transcribe(image_bytes, "test.jpg", "prompt text")

    assert text == "Success after retry"
    assert mock_models.generate_content.call_count == 2  # Retried once
```

**Validation Testing:**
```python
def test_validate_config_local_valid(self, tmp_path):
    """Test validation of valid local config."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    config = {
        'local': {
            'api_key': 'test-key-12345',
            'image_dir': str(image_dir)
        },
        'prompt_file': 'prompt.txt'
    }
    is_valid, errors = validate_config(config, 'local')
    assert is_valid is True
    assert len(errors) == 0
```

**Time Mocking for Performance Tests:**
```python
@patch('time.time')
def test_transcribe_success(self, mock_time, mock_client_class):
    """Test transcribe() successfully transcribes image."""
    # Provide enough time values for all time.time() calls
    mock_time.side_effect = [0, 0, 0, 1.5, 1.5, 1.5, 1.5, 1.5]

    text, elapsed_time, usage_metadata = client.transcribe(image_bytes, "test.jpg", "prompt text")

    assert elapsed_time > 0
```

## Test Markers

**Custom markers in `.pytest.ini`:**
```ini
markers =
    unit: Unit tests
    integration: Integration tests
    local_mode: Tests for LOCAL mode
    googlecloud_mode: Tests for GOOGLECLOUD mode
```

**Usage:**
```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.local_mode
def test_local_flow():
    pass
```

## Memory Management

**Test configuration focuses on memory efficiency:**
- Sequential test execution (no parallel)
- Auto-cleanup fixture with `gc.collect()`
- Minimal test data: Only 3 small images per fixture
- Use `tmp_path` instead of real directories
- Coverage disabled by default

**From `.pytest.ini`:**
```ini
# Memory-efficient settings: disable coverage by default
# Run tests sequentially to avoid memory accumulation
addopts = --verbose --tb=short
```

---

*Testing analysis: 2026-02-21*
