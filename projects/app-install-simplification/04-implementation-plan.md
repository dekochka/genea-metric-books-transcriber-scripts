# Implementation Plan: Dual-Mode Transcription Tool

**Project:** Genea Metric Books Transcriber Scripts  
**Document Type:** Implementation Plan  
**Date:** January 2025  
**Author:** Senior Developer  
**Status:** Ready for Implementation  
**Estimated Duration:** 3-4 weeks

---

## Executive Summary

This document provides a detailed, actionable implementation plan for introducing dual-mode operation (LOCAL and GOOGLECLOUD) to the transcription tool. The plan is organized into phases with specific tasks, dependencies, time estimates, and acceptance criteria.

**Implementation Approach:**
- Refactor existing `transcribe.py` using Strategy pattern
- Maintain backward compatibility
- Incremental development with testing at each phase
- Comprehensive test coverage before release

**Total Estimated Effort:** 15-20 working days (3-4 weeks)

---

## Implementation Phases Overview

| Phase | Name | Duration | Dependencies | Status |
|-------|------|---------|--------------|--------|
| 0 | Preparation & Setup | 1 day | None | Pending |
| 1 | Configuration & Mode Detection | 2 days | Phase 0 | Pending |
| 2 | Strategy Interfaces & Base Classes | 2 days | Phase 1 | Pending |
| 3 | LOCAL Mode Implementation | 4 days | Phase 2 | Pending |
| 4 | GOOGLECLOUD Mode Refactoring | 3 days | Phase 2 | Pending |
| 5 | Main Function Refactoring | 2 days | Phase 3, 4 | Pending |
| 6 | Testing & Validation | 3 days | Phase 5 | Pending |
| 7 | Documentation & Release | 2 days | Phase 6 | Pending |

**Total:** 19 days (approximately 4 weeks)

---

## Phase 0: Preparation & Setup

**Duration:** 1 day  
**Goal:** Prepare development environment and create project structure

### Tasks

#### Task 0.1: Create Development Branch
**Effort:** 0.5 hours  
**Owner:** Developer

**Actions:**
```bash
git checkout -b feature/dual-mode-implementation
git push -u origin feature/dual-mode-implementation
```

**Acceptance Criteria:**
- [ ] New branch created
- [ ] Branch pushed to remote
- [ ] Current codebase is clean (no uncommitted changes)

---

#### Task 0.2: Set Up Test Environment
**Effort:** 2 hours  
**Owner:** Developer

**Actions:**
1. Create test directory structure:
   ```
   tests/
   ├── unit/
   │   ├── test_config.py
   │   ├── test_auth_strategies.py
   │   ├── test_image_sources.py
   │   ├── test_ai_clients.py
   │   └── test_output_strategies.py
   ├── integration/
   │   ├── test_local_mode.py
   │   └── test_googlecloud_mode.py
   ├── fixtures/
   │   ├── config_local.yaml
   │   └── config_googlecloud.yaml
   └── conftest.py
   ```

2. **Note:** Test images are available in `data_samples/test_input_sample/`:
   - `cover-title-page.jpg` - Cover/title page image
   - `image00001.jpg` - Test image 1
   - `image00002.jpg` - Test image 2
   - `image00003.jpg` - Test image 3
   
   Reference this directory in tests instead of creating new test images.

3. Install test dependencies:
   ```bash
   pip install pytest pytest-cov pytest-mock
   ```

3. Create `.pytest.ini`:
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = --cov=transcribe --cov-report=html --cov-report=term
   ```

4. Verify test data sample directory exists:
   ```bash
   ls -la data_samples/test_input_sample/
   ```
   
   Should contain:
   - `cover-title-page.jpg` - Cover/title page image
   - `image00001.jpg` - Test image 1
   - `image00002.jpg` - Test image 2
   - `image00003.jpg` - Test image 3

**Acceptance Criteria:**
- [ ] Test directory structure created
- [ ] Test data sample directory identified (`data_samples/test_input_sample/`)
- [ ] Test dependencies installed
- [ ] pytest configuration file created
- [ ] Can run `pytest` successfully (even with no tests)

---

#### Task 0.3: Create Backup of Current Implementation
**Effort:** 0.5 hours  
**Owner:** Developer

**Actions:**
1. Create backup branch:
   ```bash
   git checkout -b backup/pre-dual-mode
   git push origin backup/pre-dual-mode
   git checkout feature/dual-mode-implementation
   ```

2. Tag current version:
   ```bash
   git tag v1.0.0-pre-dual-mode
   git push origin v1.0.0-pre-dual-mode
   ```

**Acceptance Criteria:**
- [ ] Backup branch created
- [ ] Version tagged
- [ ] Can revert to backup if needed

---

#### Task 0.4: Review Current Codebase
**Effort:** 3 hours  
**Owner:** Developer

**Actions:**
1. Document current function dependencies:
   - Map all functions in `transcribe.py`
   - Identify shared vs mode-specific code
   - List all external dependencies

2. Create dependency graph:
   ```
   main()
   ├── load_config()
   ├── authenticate()
   ├── init_services()
   │   ├── build() [Drive, Docs APIs]
   │   └── genai.Client() [Vertex AI]
   ├── list_images()
   ├── download_image()
   ├── transcribe_image()
   ├── create_doc()
   └── write_to_doc()
   ```

3. Identify refactoring points:
   - Functions that need abstraction
   - Code that can be shared
   - Mode-specific implementations

**Deliverables:**
- [ ] Function dependency map
- [ ] Refactoring points document
- [ ] Shared code identification

**Acceptance Criteria:**
- [ ] Complete understanding of current codebase
- [ ] Clear refactoring strategy
- [ ] Risk areas identified

---

## Phase 1: Configuration & Mode Detection

**Duration:** 2 days  
**Goal:** Implement configuration loading, mode detection, and validation

### Tasks

#### Task 1.1: Extend Configuration Loading
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Phase 0

**Actions:**
1. Update `load_config()` function:
   ```python
   def load_config(config_path: str) -> dict:
       """Load and validate configuration file."""
       # Existing YAML loading
       # Add mode detection
       # Add validation
   ```

2. Add mode detection function:
   ```python
   def detect_mode(config: dict) -> str:
       """
       Detect mode from configuration.
       - Explicit mode field → use it
       - Legacy config (project_id/drive_folder_id) → googlecloud
       - local section present → local
       - Default → googlecloud (backward compatibility)
       """
   ```

3. Add configuration normalization:
   ```python
   def normalize_config(config: dict, mode: str) -> dict:
       """Normalize config to internal format."""
       # Convert legacy flat structure to nested
       # Ensure all required fields present
   ```

**Files to Modify:**
- `transcribe.py` (extend existing `load_config()`)

**Test Cases:**
- [ ] Load config with explicit `mode: "local"`
- [ ] Load config with explicit `mode: "googlecloud"`
- [ ] Load legacy config (auto-detect as googlecloud)
- [ ] Load config with `local` section (auto-detect as local)
- [ ] Invalid mode value raises error

**Acceptance Criteria:**
- [ ] Mode detection works correctly
- [ ] Legacy configs auto-detect correctly
- [ ] Normalization preserves all fields
- [ ] Unit tests pass

---

#### Task 1.2: Implement Configuration Validation
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 1.1

**Actions:**
1. Create validation function:
   ```python
   def validate_config(config: dict, mode: str) -> tuple[bool, list[str]]:
       """
       Validate configuration based on mode.
       Returns (is_valid, error_messages)
       """
       errors = []
       
       # Shared validation
       if 'prompt_file' not in config:
           errors.append("prompt_file is required")
       
       # Mode-specific validation
       if mode == 'local':
           # Validate local section
       elif mode == 'googlecloud':
           # Validate googlecloud section
       
       return len(errors) == 0, errors
   ```

2. Add validation for:
   - Required fields per mode
   - File/directory existence
   - API key format (local mode)
   - Credentials file existence (googlecloud mode)

**Files to Modify:**
- `transcribe.py` (add `validate_config()`)

**Test Cases:**
- [ ] Valid local config passes validation
- [ ] Valid googlecloud config passes validation
- [ ] Missing required fields fail validation
- [ ] Invalid API key format fails validation
- [ ] Non-existent directories fail validation

**Acceptance Criteria:**
- [ ] Validation catches all invalid configs
- [ ] Error messages are clear and actionable
- [ ] Unit tests pass

---

#### Task 1.3: Create Configuration Examples
**Effort:** 2 hours  
**Owner:** Developer  
**Dependencies:** Task 1.1

**Actions:**
1. Create example config files:
   - `config/config.local.example.yaml` - Include example pointing to `data_samples/test_input_sample/` for testing
   - `config/config.googlecloud.example.yaml`
   - Update `config/config.yaml.example` with mode selection

2. Document configuration options:
   - Add comments explaining each field
   - Provide examples for common scenarios
   - Document environment variable alternatives
   - Note that `data_samples/test_input_sample/` can be used for testing

3. Example local config should reference test data:
   ```yaml
   mode: "local"
   local:
     api_key: "your-api-key-here"  # or use GEMINI_API_KEY env var
     image_dir: "data_samples/test_input_sample"  # Test data location
     output_dir: "logs"
     ocr_model_id: "gemini-1.5-pro"
   # ... rest of config
   ```

**Files to Create:**
- `config/config.local.example.yaml`
- `config/config.googlecloud.example.yaml`

**Files to Modify:**
- `config/config.yaml.example` (add mode field)

**Acceptance Criteria:**
- [ ] Example configs are valid
- [ ] Examples demonstrate both modes
- [ ] Local example references test data sample directory
- [ ] Documentation is clear

---

#### Task 1.4: Update Configuration Schema Documentation
**Effort:** 2 hours  
**Owner:** Developer  
**Dependencies:** Task 1.3

**Actions:**
1. Document new configuration structure in README
2. Add migration guide for existing configs
3. Document backward compatibility

**Files to Modify:**
- `README.md`

**Acceptance Criteria:**
- [ ] Configuration documentation is complete
- [ ] Migration guide is clear
- [ ] Examples are accurate

---

## Phase 2: Strategy Interfaces & Base Classes

**Duration:** 2 days  
**Goal:** Create abstract base classes and interfaces for strategy pattern

### Tasks

#### Task 2.1: Create Authentication Strategy Interface
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Phase 1

**Actions:**
1. Create abstract base class:
   ```python
   from abc import ABC, abstractmethod
   
   class AuthenticationStrategy(ABC):
       """Abstract base class for authentication strategies."""
       
       @abstractmethod
       def authenticate(self) -> Any:
           """Authenticate and return credentials/client."""
           pass
       
       @abstractmethod
       def validate(self) -> bool:
           """Validate authentication is working."""
           pass
   ```

2. Create placeholder implementations:
   - `LocalAuthStrategy` (skeleton)
   - `GoogleCloudAuthStrategy` (skeleton)

**Files to Create:**
- `transcribe.py` (add strategy classes)

**Test Cases:**
- [ ] Cannot instantiate abstract class
- [ ] Concrete classes can be instantiated
- [ ] Abstract methods must be implemented

**Acceptance Criteria:**
- [ ] Abstract base class defined
- [ ] Interface is clear and well-documented
- [ ] Unit tests pass

---

#### Task 2.2: Create Image Source Strategy Interface
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 2.1

**Actions:**
1. Create abstract base class:
   ```python
   class ImageSourceStrategy(ABC):
       """Abstract base class for image source strategies."""
       
       @abstractmethod
       def list_images(self, config: dict) -> list[dict]:
           """List available images."""
           pass
       
       @abstractmethod
       def get_image_bytes(self, image_info: dict) -> bytes:
           """Get image bytes."""
           pass
       
       @abstractmethod
       def get_image_url(self, image_info: dict) -> str:
           """Get image URL/link for output."""
           pass
   ```

2. Create placeholder implementations:
   - `LocalImageSource` (skeleton)
   - `DriveImageSource` (skeleton)

**Files to Modify:**
- `transcribe.py` (add strategy classes)

**Test Cases:**
- [ ] Abstract class cannot be instantiated
- [ ] Concrete classes implement all methods
- [ ] Method signatures are correct

**Acceptance Criteria:**
- [ ] Abstract base class defined
- [ ] Interface matches requirements
- [ ] Unit tests pass

---

#### Task 2.3: Create AI Client Strategy Interface
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 2.2

**Actions:**
1. Create abstract base class:
   ```python
   class AIClientStrategy(ABC):
       """Abstract base class for AI client strategies."""
       
       @abstractmethod
       def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
           """
           Transcribe image.
           Returns (text, elapsed_time, usage_metadata).
           """
           pass
   ```

2. Create placeholder implementations:
   - `GeminiDevClient` (skeleton)
   - `VertexAIClient` (skeleton)

**Files to Modify:**
- `transcribe.py` (add strategy classes)

**Test Cases:**
- [ ] Abstract class cannot be instantiated
- [ ] Return type is consistent
- [ ] Method signature is correct

**Acceptance Criteria:**
- [ ] Abstract base class defined
- [ ] Interface matches existing `transcribe_image()` signature
- [ ] Unit tests pass

---

#### Task 2.4: Create Output Strategy Interface
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 2.3

**Actions:**
1. Create abstract base class:
   ```python
   class OutputStrategy(ABC):
       """Abstract base class for output strategies."""
       
       @abstractmethod
       def initialize(self, config: dict) -> Any:
           """Initialize output destination. Returns output ID."""
           pass
       
       @abstractmethod
       def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> None:
           """Write batch of transcriptions."""
           pass
       
       @abstractmethod
       def finalize(self, all_pages: list[dict], metrics: dict) -> None:
           """Finalize output."""
           pass
   ```

2. Create placeholder implementations:
   - `LogFileOutput` (skeleton)
   - `GoogleDocsOutput` (skeleton)

**Files to Modify:**
- `transcribe.py` (add strategy classes)

**Test Cases:**
- [ ] Abstract class cannot be instantiated
- [ ] All methods are abstract
- [ ] Interface is clear

**Acceptance Criteria:**
- [ ] Abstract base class defined
- [ ] Interface supports both modes
- [ ] Unit tests pass

---

#### Task 2.5: Create Mode Factory
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Tasks 2.1-2.4

**Actions:**
1. Create factory class:
   ```python
   class ModeFactory:
       """Factory for creating mode-specific components."""
       
       @staticmethod
       def create_handlers(mode: str, config: dict) -> dict:
           """Create all mode-specific handlers."""
           if mode == 'local':
               return ModeFactory._create_local_handlers(config)
           elif mode == 'googlecloud':
               return ModeFactory._create_googlecloud_handlers(config)
           else:
               raise ValueError(f"Unknown mode: {mode}")
   ```

2. Implement factory methods (skeletons):
   - `_create_local_handlers()`
   - `_create_googlecloud_handlers()`

**Files to Modify:**
- `transcribe.py` (add factory class)

**Test Cases:**
- [ ] Factory creates correct handlers for local mode
- [ ] Factory creates correct handlers for googlecloud mode
- [ ] Invalid mode raises error
- [ ] All handlers are created

**Acceptance Criteria:**
- [ ] Factory pattern implemented
- [ ] Handlers are created correctly
- [ ] Unit tests pass

---

## Phase 3: LOCAL Mode Implementation

**Duration:** 4 days  
**Goal:** Implement all LOCAL mode strategies

### Tasks

#### Task 3.1: Implement LocalAuthStrategy
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Phase 2

**Actions:**
1. Implement `LocalAuthStrategy`:
   ```python
   class LocalAuthStrategy(AuthenticationStrategy):
       def __init__(self, api_key: str = None):
           self.api_key = api_key or os.getenv('GEMINI_API_KEY')
           if not self.api_key:
               raise ValueError("API key required")
       
       def authenticate(self) -> str:
           return self.api_key
       
       def validate(self) -> bool:
           return bool(self.api_key and len(self.api_key) > 10)
   ```

2. Add environment variable support
3. Add API key format validation

**Files to Modify:**
- `transcribe.py` (implement `LocalAuthStrategy`)

**Test Cases:**
- [ ] API key from config works
- [ ] API key from env var works
- [ ] Missing API key raises error
- [ ] Invalid API key format fails validation

**Acceptance Criteria:**
- [ ] Authentication works with API key
- [ ] Environment variable support works
- [ ] Unit tests pass

---

#### Task 3.2: Implement LocalImageSource
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Task 3.1

**Actions:**
1. Implement `LocalImageSource`:
   ```python
   class LocalImageSource(ImageSourceStrategy):
       def __init__(self, image_dir: str):
           self.image_dir = image_dir
           if not os.path.isdir(image_dir):
               raise ValueError(f"Directory does not exist: {image_dir}")
       
       def list_images(self, config: dict) -> list[dict]:
           # List images from directory
           # Apply filtering (image_start_number, image_count)
           # Reuse existing filtering logic
       
       def get_image_bytes(self, image_info: dict) -> bytes:
           with open(image_info['path'], 'rb') as f:
               return f.read()
       
       def get_image_url(self, image_info: dict) -> str:
           return image_info['path']
   ```

2. Reuse existing image filtering logic:
   - `extract_image_number()`
   - Image sorting logic
   - Pattern matching

**Files to Modify:**
- `transcribe.py` (implement `LocalImageSource`)

**Test Cases:**
- [ ] Lists images from directory
- [ ] Filters by image_start_number
- [ ] Filters by image_count
- [ ] Handles missing directory
- [ ] Supports all filename patterns
- [ ] Test with `data_samples/test_input_sample/` directory

**Test Data:**
- Use `data_samples/test_input_sample/` for testing:
  - Should list: `cover-title-page.jpg`, `image00001.jpg`, `image00002.jpg`, `image00003.jpg`
  - Test filtering with `image_start_number: 1, image_count: 3`

**Acceptance Criteria:**
- [ ] Image listing works correctly
- [ ] Filtering matches existing behavior
- [ ] All filename patterns supported
- [ ] Works with test data sample directory
- [ ] Unit tests pass

---

#### Task 3.3: Implement GeminiDevClient
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Task 3.2

**Actions:**
1. Research Gemini Developer API:
   - Check `google-genai` vs `google-generativeai`
   - Determine correct API usage
   - Test API calls

2. Implement `GeminiDevClient`:
   ```python
   class GeminiDevClient(AIClientStrategy):
       def __init__(self, api_key: str, model_id: str = "gemini-1.5-pro"):
           import google.generativeai as genai
           genai.configure(api_key=api_key)
           self.model = genai.GenerativeModel(model_id)
       
       def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
           # Convert bytes to PIL Image
           # Call API
           # Extract response
           # Return (text, elapsed_time, usage_metadata)
   ```

3. Add error handling and retries
4. Match existing `transcribe_image()` behavior

**Files to Modify:**
- `transcribe.py` (implement `GeminiDevClient`)

**Test Cases:**
- [ ] Transcribes image correctly
- [ ] Returns correct format
- [ ] Handles API errors
- [ ] Retries on failures
- [ ] Extracts usage metadata

**Acceptance Criteria:**
- [ ] API integration works
- [ ] Response format matches interface
- [ ] Error handling is robust
- [ ] Unit tests pass (with mocked API)

---

#### Task 3.4: Implement LogFileOutput
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 3.3

**Actions:**
1. Implement `LogFileOutput`:
   ```python
   class LogFileOutput(OutputStrategy):
       def __init__(self, output_dir: str, ai_logger):
           self.output_dir = output_dir
           self.ai_logger = ai_logger
           os.makedirs(output_dir, exist_ok=True)
       
       def initialize(self, config: dict) -> str:
           # Create log file
           # Log session start
           return log_file_path
       
       def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> None:
           # Write transcriptions to log
       
       def finalize(self, all_pages: list[dict], metrics: dict) -> None:
           # Log session completion
           # Log metrics
   ```

2. Match existing log format
3. Ensure log files are readable

**Files to Modify:**
- `transcribe.py` (implement `LogFileOutput`)

**Test Cases:**
- [ ] Creates log file
- [ ] Writes transcriptions correctly
- [ ] Logs session metadata
- [ ] Finalizes correctly

**Acceptance Criteria:**
- [ ] Log output matches requirements
- [ ] Files are readable
- [ ] Format is consistent
- [ ] Unit tests pass

---

#### Task 3.5: Complete Local Mode Factory
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Tasks 3.1-3.4

**Actions:**
1. Complete `ModeFactory._create_local_handlers()`:
   ```python
   @staticmethod
   def _create_local_handlers(config: dict) -> dict:
       local_config = config['local']
       
       auth = LocalAuthStrategy(local_config.get('api_key'))
       image_source = LocalImageSource(local_config['image_dir'])
       ai_client = GeminiDevClient(
           auth.authenticate(),
           local_config.get('ocr_model_id', 'gemini-1.5-pro')
       )
       output_dir = local_config.get('output_dir', 'logs')
       ai_logger = logging.getLogger('ai_responses')
       output = LogFileOutput(output_dir, ai_logger)
       
       return {
           'auth': auth,
           'image_source': image_source,
           'ai_client': ai_client,
           'output': output,
           'drive_service': None,
           'docs_service': None
       }
   ```

2. Add error handling
3. Validate all components

**Files to Modify:**
- `transcribe.py` (complete factory method)

**Test Cases:**
- [ ] Factory creates all handlers
- [ ] Handlers are correctly initialized
- [ ] Missing config fields handled gracefully

**Acceptance Criteria:**
- [ ] Factory works correctly
- [ ] All handlers are created
- [ ] Unit tests pass

---

#### Task 3.6: Test LOCAL Mode End-to-End
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 3.5

**Actions:**
1. Create test configuration pointing to `data_samples/test_input_sample/`:
   ```yaml
   mode: "local"
   local:
     api_key: "${GEMINI_API_KEY}"  # Use env var
     image_dir: "data_samples/test_input_sample"
     output_dir: "tests/output"
     ocr_model_id: "gemini-1.5-pro"
   prompt_file: "prompts/f487o1s545-Turilche.md"  # Use existing prompt
   archive_index: "ф487оп1спр545"
   image_start_number: 1
   image_count: 3  # Test with 3 images
   ```

2. Run end-to-end test:
   ```bash
   python transcribe.py tests/fixtures/config_local_test.yaml
   ```

3. Verify output:
   - Check log files in `tests/output/`
   - Verify transcriptions for all 3 images
   - Verify cover page handling (if implemented)
   - Check error handling

**Test Cases:**
- [ ] Complete transcription run succeeds
- [ ] All 3 test images are processed
- [ ] Log files are created in correct location
- [ ] Transcriptions are correct
- [ ] Cover page is handled (if applicable)
- [ ] Error handling works

**Test Data:**
- Use existing test images from `data_samples/test_input_sample/`:
  - `cover-title-page.jpg` - For title page testing
  - `image00001.jpg` - Test image 1
  - `image00002.jpg` - Test image 2
  - `image00003.jpg` - Test image 3

**Acceptance Criteria:**
- [ ] End-to-end test passes
- [ ] All test images processed successfully
- [ ] Output is correct
- [ ] No errors in logs
- [ ] Log files are readable and properly formatted

---

## Phase 4: GOOGLECLOUD Mode Refactoring

**Duration:** 3 days  
**Goal:** Refactor existing code into GOOGLECLOUD strategies

### Tasks

#### Task 4.1: Implement GoogleCloudAuthStrategy
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Phase 2

**Actions:**
1. Refactor existing `authenticate()` function:
   ```python
   class GoogleCloudAuthStrategy(AuthenticationStrategy):
       def __init__(self, adc_file: str):
           self.adc_file = adc_file
       
       def authenticate(self) -> Credentials:
           # Move existing authenticate() logic here
           scopes = [...]
           creds = Credentials.from_authorized_user_file(...)
           # Token refresh logic
           return creds
       
       def validate(self) -> bool:
           return os.path.exists(self.adc_file)
   ```

2. Keep existing error handling
3. Maintain backward compatibility

**Files to Modify:**
- `transcribe.py` (refactor `authenticate()` → `GoogleCloudAuthStrategy`)

**Test Cases:**
- [ ] Authentication works as before
- [ ] Token refresh works
- [ ] Error messages are preserved
- [ ] Validation works

**Acceptance Criteria:**
- [ ] Refactored code works identically
- [ ] No regression in functionality
- [ ] Unit tests pass

---

#### Task 4.2: Implement DriveImageSource
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 4.1

**Actions:**
1. Refactor existing `list_images()` and `download_image()`:
   ```python
   class DriveImageSource(ImageSourceStrategy):
       def __init__(self, drive_service, drive_folder_id: str):
           self.drive_service = drive_service
           self.drive_folder_id = drive_folder_id
       
       def list_images(self, config: dict) -> list[dict]:
           # Move existing list_images() logic here
           return list_images(self.drive_service, config)
       
       def get_image_bytes(self, image_info: dict) -> bytes:
           # Move existing download_image() logic here
           return download_image(...)
       
       def get_image_url(self, image_info: dict) -> str:
           return image_info.get('webViewLink', '')
   ```

2. Keep existing functions as wrappers (for backward compatibility)
3. Ensure no behavior changes

**Files to Modify:**
- `transcribe.py` (refactor image functions → `DriveImageSource`)

**Test Cases:**
- [ ] Image listing works as before
- [ ] Image downloading works as before
- [ ] All filename patterns supported
- [ ] Filtering logic unchanged

**Acceptance Criteria:**
- [ ] Refactored code works identically
- [ ] No regression in functionality
- [ ] Unit tests pass

---

#### Task 4.3: Implement VertexAIClient
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 4.2

**Actions:**
1. Refactor existing `transcribe_image()`:
   ```python
   class VertexAIClient(AIClientStrategy):
       def __init__(self, genai_client, model_id: str):
           self.genai_client = genai_client
           self.model_id = model_id
       
       def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
           # Move existing transcribe_image() logic here
           # Keep all retry logic, timeouts, etc.
   ```

2. Keep existing function as wrapper
3. Ensure identical behavior

**Files to Modify:**
- `transcribe.py` (refactor `transcribe_image()` → `VertexAIClient`)

**Test Cases:**
- [ ] Transcription works as before
- [ ] Retry logic works
- [ ] Timeout handling works
- [ ] Error handling unchanged

**Acceptance Criteria:**
- [ ] Refactored code works identically
- [ ] No regression in functionality
- [ ] Unit tests pass

---

#### Task 4.4: Implement GoogleDocsOutput
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Task 4.3

**Actions:**
1. Refactor existing document functions:
   ```python
   class GoogleDocsOutput(OutputStrategy):
       def __init__(self, docs_service, drive_service):
           self.docs_service = docs_service
           self.drive_service = drive_service
       
       def initialize(self, config: dict) -> str:
           # Move create_doc() logic here
           return doc_id
       
       def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> None:
           # Move write_to_doc() logic here
       
       def finalize(self, all_pages: list[dict], metrics: dict) -> None:
           # Move update_overview_section() logic here
   ```

2. Keep existing functions as wrappers
3. Maintain all formatting logic

**Files to Modify:**
- `transcribe.py` (refactor document functions → `GoogleDocsOutput`)

**Test Cases:**
- [ ] Document creation works
- [ ] Document writing works
- [ ] Formatting is preserved
- [ ] Overview section works

**Acceptance Criteria:**
- [ ] Refactored code works identically
- [ ] No regression in functionality
- [ ] Unit tests pass

---

#### Task 4.5: Complete GoogleCloud Mode Factory
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Tasks 4.1-4.4

**Actions:**
1. Complete `ModeFactory._create_googlecloud_handlers()`:
   ```python
   @staticmethod
   def _create_googlecloud_handlers(config: dict) -> dict:
       gc_config = config['googlecloud']
       
       auth = GoogleCloudAuthStrategy(gc_config['adc_file'])
       creds = auth.authenticate()
       drive_service, docs_service, genai_client = init_services(creds, gc_config)
       
       image_source = DriveImageSource(drive_service, gc_config['drive_folder_id'])
       ai_client = VertexAIClient(genai_client, gc_config['ocr_model_id'])
       output = GoogleDocsOutput(docs_service, drive_service)
       
       return {
           'auth': auth,
           'image_source': image_source,
           'ai_client': ai_client,
           'output': output,
           'drive_service': drive_service,
           'docs_service': docs_service
       }
   ```

2. Ensure `init_services()` still works
3. Validate all components

**Files to Modify:**
- `transcribe.py` (complete factory method)

**Test Cases:**
- [ ] Factory creates all handlers
- [ ] Services are initialized correctly
- [ ] All handlers work together

**Acceptance Criteria:**
- [ ] Factory works correctly
- [ ] All handlers are created
- [ ] Unit tests pass

---

#### Task 4.6: Test GOOGLECLOUD Mode End-to-End
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 4.5

**Actions:**
1. Use existing test configuration
2. Run end-to-end test
3. Compare output with previous version
4. Verify no regressions

**Test Cases:**
- [ ] Complete transcription run succeeds
- [ ] Google Doc is created
- [ ] Formatting is correct
- [ ] No behavior changes

**Acceptance Criteria:**
- [ ] End-to-end test passes
- [ ] Output matches previous version
- [ ] No regressions

---

## Phase 5: Main Function Refactoring

**Duration:** 2 days  
**Goal:** Refactor main() to use strategies

### Tasks

#### Task 5.1: Create Shared Processing Logic
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Phase 3, 4

**Actions:**
1. Extract shared logic:
   ```python
   def process_all_local(images: list, handlers: dict, prompt_text: str, config: dict) -> list:
       """Process all images in local mode."""
       # Shared processing logic
   
   def process_batches_googlecloud(images: list, handlers: dict, prompt_text: str, 
                                   config: dict, batch_size: int) -> list:
       """Process images in batches for Google Cloud mode."""
       # Existing batch processing logic
   ```

2. Reuse existing batch processing for Google Cloud
3. Create simpler processing for Local mode

**Files to Modify:**
- `transcribe.py` (add processing functions)

**Test Cases:**
- [ ] Processing logic works for both modes
- [ ] Batch processing works for Google Cloud
- [ ] Simple processing works for Local

**Acceptance Criteria:**
- [ ] Shared logic is extracted
- [ ] Both modes work correctly
- [ ] Unit tests pass

---

#### Task 5.2: Refactor Main Function
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Task 5.1

**Actions:**
1. Refactor `main()`:
   ```python
   def main(config: dict, prompt_text: str, ai_logger, logs_dir: str):
       # Detect mode
       mode = detect_mode(config)
       
       # Validate config
       is_valid, errors = validate_config(config, mode)
       if not is_valid:
           raise ValueError(f"Configuration errors: {', '.join(errors)}")
       
       # Create handlers
       handlers = ModeFactory.create_handlers(mode, config)
       
       # Normalize config
       normalized_config = normalize_config(config, mode)
       
       # List images
       images = handlers['image_source'].list_images(normalized_config)
       
       # Initialize output
       output_id = handlers['output'].initialize(normalized_config)
       
       # Process images
       if mode == 'googlecloud':
           transcribed_pages = process_batches_googlecloud(...)
       else:
           transcribed_pages = process_all_local(...)
       
       # Finalize output
       handlers['output'].finalize(transcribed_pages, metrics)
   ```

2. Maintain backward compatibility
3. Keep existing error handling

**Files to Modify:**
- `transcribe.py` (refactor `main()`)

**Test Cases:**
- [ ] Main function works for local mode
- [ ] Main function works for googlecloud mode
- [ ] Error handling works
- [ ] Backward compatibility maintained

**Acceptance Criteria:**
- [ ] Main function is mode-agnostic
- [ ] Both modes work correctly
- [ ] Integration tests pass

---

#### Task 5.3: Update Entry Point
**Effort:** 2 hours  
**Owner:** Developer  
**Dependencies:** Task 5.2

**Actions:**
1. Update `if __name__ == '__main__':` block:
   - Keep existing argument parsing
   - Add mode detection logging
   - Update error messages

2. Ensure backward compatibility

**Files to Modify:**
- `transcribe.py` (update entry point)

**Test Cases:**
- [ ] Script runs with local config
- [ ] Script runs with googlecloud config
- [ ] Script runs with legacy config
- [ ] Error messages are clear

**Acceptance Criteria:**
- [ ] Entry point works correctly
- [ ] Error messages are helpful
- [ ] Integration tests pass

---

## Phase 6: Testing & Validation

**Duration:** 3 days  
**Goal:** Comprehensive testing of both modes

### Tasks

#### Task 6.1: Unit Tests for Strategies
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Phase 5

**Actions:**
1. Write unit tests for:
   - Authentication strategies
   - Image source strategies
   - AI client strategies
   - Output strategies
   - Mode factory

2. Use mocks for external dependencies
3. Achieve >80% code coverage

**Files to Create:**
- `tests/unit/test_auth_strategies.py`
- `tests/unit/test_image_sources.py`
- `tests/unit/test_ai_clients.py`
- `tests/unit/test_output_strategies.py`
- `tests/unit/test_mode_factory.py`

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] Code coverage >80%
- [ ] All edge cases covered

---

#### Task 6.2: Integration Tests
**Effort:** 6 hours  
**Owner:** Developer  
**Dependencies:** Task 6.1

**Actions:**
1. Write integration tests:
   - Local mode end-to-end
   - Google Cloud mode end-to-end
   - Configuration loading
   - Mode detection

2. Use test data from `data_samples/test_input_sample/`:
   - Reference the directory in test configurations
   - Use existing images: `cover-title-page.jpg`, `image00001.jpg`, `image00002.jpg`, `image00003.jpg`
   - Test with real API (if possible) or mocks

3. Create test fixtures that reference the test data:
   ```python
   # In conftest.py or test files
   TEST_IMAGE_DIR = os.path.join(
       os.path.dirname(__file__),
       '../../data_samples/test_input_sample'
   )
   ```

**Files to Create:**
- `tests/integration/test_local_mode.py`
- `tests/integration/test_googlecloud_mode.py`
- `tests/integration/test_config.py`

**Test Data Location:**
- Use `data_samples/test_input_sample/` for all integration tests
- Contains: `cover-title-page.jpg`, `image00001.jpg`, `image00002.jpg`, `image00003.jpg`

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Both modes work end-to-end
- [ ] Tests use existing test data sample
- [ ] No regressions

---

#### Task 6.3: Backward Compatibility Tests
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 6.2

**Actions:**
1. Test with existing configurations:
   - Legacy config files
   - Existing workflows
   - Previous output formats

2. Verify no breaking changes
3. Document any differences

**Files to Create:**
- `tests/compatibility/test_legacy_configs.py`

**Acceptance Criteria:**
- [ ] Legacy configs work
- [ ] No breaking changes
- [ ] Output is compatible

---

#### Task 6.4: Performance Testing
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 6.3

**Actions:**
1. Compare performance:
   - Local mode vs Google Cloud mode
   - Before vs after refactoring
   - Memory usage
   - API call efficiency

2. Identify any performance regressions
3. Optimize if needed

**Acceptance Criteria:**
- [ ] No significant performance regression
- [ ] Local mode is faster for file access
- [ ] Google Cloud mode performance unchanged

---

#### Task 6.5: Error Handling Tests
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 6.4

**Actions:**
1. Test error scenarios:
   - Invalid configurations
   - Missing files/directories
   - API failures
   - Network errors
   - Permission errors

2. Verify error messages are clear
3. Test recovery mechanisms

**Acceptance Criteria:**
- [ ] All error scenarios handled
- [ ] Error messages are helpful
- [ ] Recovery works correctly

---

## Phase 7: Documentation & Release

**Duration:** 2 days  
**Goal:** Complete documentation and prepare for release

### Tasks

#### Task 7.1: Update README
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Phase 6

**Actions:**
1. Update README with:
   - Dual-mode explanation
   - Configuration examples
   - Setup instructions for both modes
   - Migration guide

2. Add troubleshooting section
3. Update architecture diagrams

**Files to Modify:**
- `README.md`

**Acceptance Criteria:**
- [ ] Documentation is complete
- [ ] Examples are accurate
- [ ] Instructions are clear

---

#### Task 7.2: Create Configuration Guide
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 7.1

**Actions:**
1. Create detailed configuration guide:
   - All configuration options
   - Mode-specific settings
   - Environment variables
   - Best practices

2. Add examples for common scenarios

**Files to Create:**
- `docs/CONFIGURATION.md` (optional)
- Or update README with detailed section

**Acceptance Criteria:**
- [ ] Configuration guide is complete
- [ ] All options documented
- [ ] Examples are provided

---

#### Task 7.3: Update Example Configurations
**Effort:** 2 hours  
**Owner:** Developer  
**Dependencies:** Task 7.2

**Actions:**
1. Update example configs:
   - `config/config.yaml.example` (add mode)
   - Create `config/config.local.example.yaml`
   - Create `config/config.googlecloud.example.yaml`

2. Ensure examples are valid
3. Add comments

**Files to Modify:**
- `config/config.yaml.example`

**Files to Create:**
- `config/config.local.example.yaml`
- `config/config.googlecloud.example.yaml`

**Acceptance Criteria:**
- [ ] Examples are valid
- [ ] Examples demonstrate both modes
- [ ] Comments are helpful

---

#### Task 7.4: Create Migration Guide
**Effort:** 3 hours  
**Owner:** Developer  
**Dependencies:** Task 7.3

**Actions:**
1. Create migration guide:
   - For existing users
   - For new users
   - Step-by-step instructions
   - Common issues and solutions

**Files to Create:**
- `docs/MIGRATION.md` (optional)
- Or add to README

**Acceptance Criteria:**
- [ ] Migration guide is clear
- [ ] Covers all scenarios
- [ ] Includes troubleshooting

---

#### Task 7.5: Code Review & Cleanup
**Effort:** 4 hours  
**Owner:** Developer  
**Dependencies:** Task 7.4

**Actions:**
1. Code review checklist:
   - [ ] Code follows style guide
   - [ ] All functions documented
   - [ ] No dead code
   - [ ] Error handling is consistent
   - [ ] Logging is appropriate

2. Clean up:
   - Remove debug code
   - Remove commented code
   - Fix linting issues
   - Optimize imports

**Acceptance Criteria:**
- [ ] Code is clean
- [ ] Documentation is complete
- [ ] No linting errors

---

#### Task 7.6: Prepare Release
**Effort:** 2 hours  
**Owner:** Developer  
**Dependencies:** Task 7.5

**Actions:**
1. Create release notes:
   - New features
   - Breaking changes (if any)
   - Migration instructions
   - Known issues

2. Update version number
3. Create release tag

**Files to Create:**
- `CHANGELOG.md` (or update existing)

**Acceptance Criteria:**
- [ ] Release notes are complete
- [ ] Version is updated
- [ ] Ready for release

---

## Testing Strategy

### Unit Testing
- **Coverage Target:** >80%
- **Tools:** pytest, pytest-cov
- **Focus:** Individual strategy classes, utility functions

### Integration Testing
- **Coverage:** End-to-end workflows
- **Tools:** pytest with fixtures
- **Focus:** Complete transcription runs for both modes

### Compatibility Testing
- **Coverage:** Legacy configurations
- **Focus:** Backward compatibility, no breaking changes

### Performance Testing
- **Metrics:** Execution time, memory usage
- **Focus:** No regressions, local mode performance

### Error Handling Testing
- **Coverage:** All error scenarios
- **Focus:** Clear error messages, graceful failures

---

## Risk Mitigation

### Technical Risks

#### Risk 1: Breaking Existing Functionality
**Probability:** Medium  
**Impact:** High  
**Mitigation:**
- Comprehensive testing
- Backward compatibility layer
- Gradual migration
- Keep existing code paths

#### Risk 2: API Differences
**Probability:** Low  
**Impact:** Medium  
**Mitigation:**
- Research API differences early
- Abstract differences in strategies
- Test with real APIs
- Provide fallbacks

#### Risk 3: Performance Regression
**Probability:** Low  
**Impact:** Medium  
**Mitigation:**
- Performance testing
- Benchmark before/after
- Optimize if needed

### Schedule Risks

#### Risk 1: Underestimated Effort
**Probability:** Medium  
**Impact:** Medium  
**Mitigation:**
- Add 20% buffer to estimates
- Prioritize critical features
- Defer non-essential features

#### Risk 2: External Dependencies
**Probability:** Low  
**Impact:** Low  
**Mitigation:**
- Test APIs early
- Have fallback plans
- Document dependencies

---

## Success Criteria

### Functional Requirements
- [ ] LOCAL mode works end-to-end
- [ ] GOOGLECLOUD mode works end-to-end
- [ ] Backward compatibility maintained
- [ ] Configuration validation works
- [ ] Error handling is robust

### Non-Functional Requirements
- [ ] Code coverage >80%
- [ ] No performance regression
- [ ] Documentation is complete
- [ ] Examples are accurate
- [ ] Migration guide is clear

### Quality Requirements
- [ ] Code follows style guide
- [ ] All functions documented
- [ ] No linting errors
- [ ] Tests pass consistently
- [ ] No known critical bugs

---

## Dependencies & Prerequisites

### Development Environment
- Python 3.10+
- Git
- pytest and testing tools
- Code editor/IDE

### External Dependencies
- Google Gemini Developer API access (for LOCAL mode testing)
- Google Cloud credentials (for GOOGLECLOUD mode testing)
- Test images: Use existing `data_samples/test_input_sample/` directory containing:
  - `cover-title-page.jpg` - Cover/title page for testing
  - `image00001.jpg` - Test image 1
  - `image00002.jpg` - Test image 2
  - `image00003.jpg` - Test image 3

### Knowledge Requirements
- Python programming
- Strategy pattern
- Google APIs (Gemini, Vertex AI, Drive, Docs)
- Testing best practices

---

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | 0-2 | Setup, Configuration, Strategy Interfaces |
| 2 | 3-4 | LOCAL Mode, GOOGLECLOUD Refactoring |
| 3 | 5-6 | Main Refactoring, Testing |
| 4 | 7 | Documentation, Release |

**Total Duration:** 4 weeks (19 working days)

---

## Post-Implementation

### Immediate Follow-up
1. User testing with beta users
2. Bug fixes based on feedback
3. Performance monitoring
4. Documentation updates

### Future Enhancements
1. HTML report generation (LOCAL mode)
2. Setup wizard
3. Hybrid mode (local processing + cloud export)
4. Additional output formats

---

## Conclusion

This implementation plan provides a detailed, actionable roadmap for implementing dual-mode operation. The plan is structured to minimize risk, maintain backward compatibility, and deliver a high-quality solution.

**Key Success Factors:**
- Incremental development with testing
- Backward compatibility focus
- Comprehensive testing strategy
- Clear documentation

**Estimated Completion:** 4 weeks from start

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Status:** Ready for Implementation
