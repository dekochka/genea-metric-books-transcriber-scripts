# Coding Conventions

**Analysis Date:** 2026-02-21

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `wizard_controller.py`, `config_generator.py`, `preflight_validator.py`)
- Test files: `test_*.py` (e.g., `test_wizard_controller.py`, `test_ai_clients.py`)
- Config files: `kebab-case.yaml` (e.g., `config-RS-1782-Knyazha-TsGAKO.yaml`)
- Main script: `transcribe.py` (executable with shebang)

**Functions:**
- Lowercase with underscores: `snake_case`
- Examples: `load_config()`, `detect_mode()`, `normalize_config()`, `extract_image_number()`
- Descriptive names indicating action: `list_images()`, `download_image()`, `transcribe_image()`

**Variables:**
- Lowercase with underscores: `snake_case`
- Examples: `image_start_number`, `retry_mode`, `drive_folder_id`, `usage_metadata`
- Config keys: match YAML structure (e.g., `image_dir`, `api_key`, `ocr_model_id`)

**Classes:**
- PascalCase for class names
- Examples: `WizardController`, `ConfigGenerator`, `PreFlightValidator`, `LocalImageSource`, `GeminiDevClient`
- Strategy pattern classes: `*Strategy` suffix (e.g., `AuthenticationStrategy`, `ImageSourceStrategy`, `AIClientStrategy`)
- Output handlers: `*Output` suffix (e.g., `LogFileOutput`, `GoogleDocsOutput`, `WordOutput`, `MarkdownOutput`)

**Constants:**
- UPPERCASE_WITH_UNDERSCORES
- Examples: `DOCX_AVAILABLE`, `TRANSLATIONS` (in i18n module)

## Code Style

**Formatting:**
- Tool: None detected (no .prettierrc, .black config)
- Indentation: 4 spaces (Python standard)
- Line length: No strict enforcement detected, generally follows PEP 8 (~100-120 chars)
- String quotes: Double quotes preferred for docstrings, mixed single/double elsewhere

**Linting:**
- Tool: None detected (no .eslintrc, .pylintrc, .ruff config)
- Follows PEP 8 conventions by observation

**Docstrings:**
- Google-style docstrings used consistently
- All public functions and classes documented
- Example format:
```python
def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file with mode detection and validation.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing configuration values (normalized)

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If configuration validation fails
    """
```

## Import Organization

**Order:**
1. Standard library imports (grouped)
2. Third-party imports (grouped)
3. Local imports (grouped)

**Example from `transcribe.py`:**
```python
import io
import os
import sys
import argparse
import logging
import base64
import json
import traceback
import yaml
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
```

**Example from wizard modules:**
```python
import os
from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import questionary

from wizard.steps.base_step import WizardStep
from wizard.i18n import t, get_available_languages
```

**Path Aliases:**
- No path aliases configured
- Relative imports for wizard submodules: `from wizard.i18n import t`
- Project root added to path in tests: `sys.path.insert(0, project_root)`

## Error Handling

**Patterns:**
- Use specific exceptions with descriptive messages
- Raise `ValueError` for invalid configuration: `raise ValueError(f"Configuration file not found: {config_path}")`
- Raise `FileNotFoundError` for missing files
- Use try/except for API calls with retry logic
- Log errors before raising: `logging.error(f"Error message: {e}")`

**Retry logic:**
- Exponential backoff for API errors
- Maximum 3 attempts for transient failures
- Retry on specific errors: `ServerError` (503, 500), `ConnectionError`, `TimeoutError`
- Example from `GeminiDevClient.transcribe()`:
```python
max_retries = 3
retry_delay = 30  # seconds
for attempt in range(max_retries):
    try:
        # API call
    except ServerError as e:
        if is_retryable and attempt < max_retries - 1:
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
```

**Validation pattern:**
- Return tuple `(is_valid: bool, errors: list[str])`
- Example: `is_valid, errors = validate_config(config, mode)`
- Used consistently across validators and wizard steps

## Logging

**Framework:** Python `logging` module

**Patterns:**
- Structured logging with timestamps: `f"[{datetime.now().strftime('%H:%M:%S')}] message"`
- Log file and console output
- Separate AI response logger: `ai_logger` for detailed API responses
- Log levels: `INFO` for progress, `WARNING` for retries, `ERROR` for failures
- Compact format: timestamp + line number only (per CHANGELOG)

**Example:**
```python
logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Processing image '{filename}'")
logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] Retry attempt {attempt}")
logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] Failed: {error}")
```

**Logger setup:**
- Configured in `setup_logging()` function in `transcribe.py`
- Writes to file: `logs/transcription-YYYY-MM-DD_HH-MM-SS.log`
- Separate AI responses log: `logs/ai-responses-YYYY-MM-DD_HH-MM-SS.log`

## Comments

**When to Comment:**
- Explain complex logic (e.g., image number extraction patterns)
- Document configuration sections
- Clarify non-obvious behavior
- Mark sections of long functions: `# ------------------------- SECTION NAME -------------------------`

**JSDoc/TSDoc:**
- Not applicable (Python project)
- Docstrings used instead (see Docstrings section above)

**Inline comments:**
- Used to explain "why" not "what"
- Example: `# Use env var can be used, or invalid if not` (explaining validation logic)
- Pattern descriptions in regex sections: `# Check for IMG_YYYYMMDD_XXXX.jpg pattern`

## Function Design

**Size:**
- Functions range from 10-200 lines
- Long functions broken into logical sections with comments
- Complex functions (e.g., `transcribe_image()`, `process_all_local()`) are 200+ lines but well-documented
- Helper functions extracted when reusable (e.g., `extract_image_number()`, `scan_available_image_numbers()`)

**Parameters:**
- Type hints used consistently: `def load_config(config_path: str) -> dict:`
- Config passed as dictionary: `config: dict`
- Services passed as objects: `drive_service`, `docs_service`, `genai_client`
- Optional parameters with defaults: `lang: str = 'en'`

**Return Values:**
- Tuples for multiple return values: `return text, elapsed_time, usage_metadata`
- Validation functions return tuple: `return (is_valid, errors)`
- Dictionaries for structured data: `return {'name': filename, 'id': file_id, ...}`
- Type hints for return values: `-> tuple[bool, list[str]]`, `-> Optional[str]`

## Module Design

**Exports:**
- No explicit `__all__` declarations
- Public API defined by docstrings and naming (no leading underscore)
- Private helpers prefixed with underscore: `_build_config_structure()`, `_display_welcome()`

**Barrel Files:**
- Not used (Python convention differs from JavaScript)
- Direct imports from modules: `from wizard.i18n import t`
- `__init__.py` files present but mostly empty (package markers)

**Module Organization:**
- Main script: `transcribe.py` (contains core logic, 4800+ lines)
- Wizard modules: `wizard/` directory with focused modules
- Tests: `tests/` with `unit/` and `integration/` subdirectories
- Configuration: `config/` directory for YAML files
- Prompts: `prompts/` directory for transcription instructions

---

*Convention analysis: 2026-02-21*
