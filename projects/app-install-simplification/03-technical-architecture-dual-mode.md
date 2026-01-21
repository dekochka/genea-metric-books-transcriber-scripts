# Technical Architecture: Dual-Mode Implementation (LOCAL & GOOGLECLOUD)

**Project:** Genea Metric Books Transcriber Scripts  
**Document Type:** Technical Architecture Specification  
**Date:** January 2025  
**Author:** Technical Architect  
**Status:** Design Phase

---

## Executive Summary

This document specifies the technical architecture for introducing dual-mode operation (LOCAL and GOOGLECLOUD) to the transcription tool. The architecture maintains backward compatibility while dramatically simplifying setup for new users through local mode, while preserving full functionality for advanced users through Google Cloud mode.

**Decision:** Refactor existing `transcribe.py` with mode-based architecture rather than creating separate scripts.

**Key Principles:**
- Single codebase with mode abstraction
- Backward compatible configuration
- Shared core logic
- Mode-specific implementations
- Clear separation of concerns

---

## Architecture Decision: Refactor vs New Script

### Analysis

#### Option 1: Create New Script (`transcribe_local.py`)
**Pros:**
- Clean separation
- No risk to existing code
- Simpler initial implementation
- Independent evolution

**Cons:**
- Code duplication (~60% shared logic)
- Maintenance overhead (bug fixes in two places)
- Feature divergence risk
- User confusion (which script to use?)
- Configuration inconsistency

#### Option 2: Refactor Existing Script (Recommended)
**Pros:**
- Single codebase, shared logic
- Consistent behavior across modes
- Unified configuration
- Easier maintenance
- Better code organization
- Clear mode selection

**Cons:**
- More complex refactoring
- Requires careful testing
- Risk of breaking existing workflows

### Decision: Refactor Existing Script

**Rationale:**
1. **Code Reuse:** ~60% of logic is shared (image processing, transcription, logging)
2. **Maintenance:** Single codebase reduces bugs and inconsistencies
3. **User Experience:** One script, clear mode selection
4. **Configuration:** Unified schema with mode detection
5. **Future-Proof:** Easier to add features, maintain consistency

**Implementation Strategy:**
- Abstract mode-specific operations into interfaces/classes
- Use factory pattern for mode-specific components
- Maintain backward compatibility
- Gradual migration path

---

## High-Level Architecture

### Current Architecture (Single Mode)

```
transcribe.py
├── Configuration Loading
├── Authentication (OAuth2/ADC)
├── Service Initialization (Drive, Docs, Vertex AI)
├── Image Listing (Drive API)
├── Image Downloading (Drive API)
├── Image Transcription (Vertex AI)
├── Document Creation (Docs API)
└── Document Writing (Docs API)
```

### Proposed Architecture (Dual Mode)

```
transcribe.py
├── Configuration Loading & Mode Detection
├── Mode Factory (LOCAL | GOOGLECLOUD)
│   ├── Authentication Strategy
│   ├── Image Source Strategy
│   ├── AI Client Strategy
│   └── Output Strategy
├── Shared Core Logic
│   ├── Image Processing
│   ├── Transcription Orchestration
│   ├── Logging
│   └── Error Handling
└── Mode-Specific Implementations
    ├── LOCAL Mode
    │   ├── API Key Auth
    │   ├── Local File System
    │   ├── Gemini Developer API
    │   └── Log File Output
    └── GOOGLECLOUD Mode
        ├── OAuth2/ADC Auth
        ├── Google Drive API
        ├── Vertex AI
        └── Google Docs API
```

---

## Configuration Architecture

### Configuration Schema Design

#### Unified Configuration Structure

```yaml
# Mode selection (required)
# Options: "local" | "googlecloud"
# Default: "googlecloud" (for backward compatibility)
mode: "local"

# ------------------------- MODE-SPECIFIC CONFIGURATION -------------------------

# LOCAL MODE CONFIGURATION
# Required when mode: "local"
local:
  # API key for Gemini Developer API
  # Can also be set via GEMINI_API_KEY environment variable
  api_key: "your-api-key-here"  # or use env var
  
  # Local directory containing images
  image_dir: "/path/to/images"
  
  # Output directory for log files (optional, default: "logs")
  output_dir: "logs"
  
  # OCR Model ID (optional, default: "gemini-1.5-pro")
  ocr_model_id: "gemini-1.5-pro"

# GOOGLECLOUD MODE CONFIGURATION
# Required when mode: "googlecloud"
googlecloud:
  # Google Cloud Project ID
  project_id: "ukr-transcribe-genea"
  
  # Google Drive folder ID
  drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
  
  # Vertex AI region
  region: "global"
  
  # OCR Model ID
  ocr_model_id: "gemini-3-flash-preview"
  
  # Application Default Credentials file
  adc_file: "application_default_credentials.json"
  
  # Document name (optional, auto-fetched from Drive)
  document_name: "My Document"
  
  # Title page image filename (optional)
  title_page_filename: "image00001.jpg"

# ------------------------- SHARED CONFIGURATION -------------------------
# These apply to both modes

# Prompt file (required)
prompt_file: "f487o1s545-Turilche.md"

# Archive index reference
archive_index: "ф487оп1спр545"

# Image processing settings
image_start_number: 1
image_count: 100

# Retry mode (optional)
retry_mode: false
retry_image_list: []

# Batch processing (only for GOOGLECLOUD mode)
# Not needed for LOCAL mode (no document batching)
batch_size_for_doc: 2  # Only used in GOOGLECLOUD mode

# Maximum images (only for GOOGLECLOUD mode)
max_images: 1000  # Only used in GOOGLECLOUD mode
```

### Backward Compatibility

#### Legacy Configuration Support

For existing configurations without `mode` field:

```python
def detect_mode(config: dict) -> str:
    """
    Auto-detect mode from configuration.
    - If 'project_id' or 'drive_folder_id' present → GOOGLECLOUD
    - If 'local' section present → LOCAL
    - Default → GOOGLECLOUD (backward compatibility)
    """
    if 'mode' in config:
        return config['mode'].lower()
    
    # Legacy detection
    if 'project_id' in config or 'drive_folder_id' in config:
        return 'googlecloud'
    
    if 'local' in config:
        return 'local'
    
    # Default for backward compatibility
    return 'googlecloud'
```

### Configuration Validation

```python
def validate_config(config: dict, mode: str) -> tuple[bool, list[str]]:
    """
    Validate configuration based on mode.
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Shared required fields
    if 'prompt_file' not in config:
        errors.append("prompt_file is required")
    
    if 'archive_index' not in config:
        errors.append("archive_index is required")
    
    # Mode-specific validation
    if mode == 'local':
        if 'local' not in config:
            errors.append("local mode requires 'local' configuration section")
        else:
            local_config = config['local']
            if 'api_key' not in local_config and 'GEMINI_API_KEY' not in os.environ:
                errors.append("local mode requires api_key or GEMINI_API_KEY env var")
            if 'image_dir' not in local_config:
                errors.append("local mode requires image_dir")
    
    elif mode == 'googlecloud':
        if 'googlecloud' not in config:
            errors.append("googlecloud mode requires 'googlecloud' configuration section")
        else:
            gc_config = config['googlecloud']
            required = ['project_id', 'drive_folder_id', 'region', 'ocr_model_id', 'adc_file']
            for field in required:
                if field not in gc_config:
                    errors.append(f"googlecloud mode requires {field}")
    
    return len(errors) == 0, errors
```

---

## Code Organization & Refactoring

### Proposed Module Structure

```
transcribe.py (refactored)
├── Configuration Module
│   ├── load_config()
│   ├── detect_mode()
│   ├── validate_config()
│   └── normalize_config()
│
├── Mode Abstraction Layer
│   ├── ModeFactory (creates mode-specific handlers)
│   ├── AuthenticationStrategy (interface)
│   │   ├── LocalAuthStrategy
│   │   └── GoogleCloudAuthStrategy
│   ├── ImageSourceStrategy (interface)
│   │   ├── LocalImageSource
│   │   └── DriveImageSource
│   ├── AIClientStrategy (interface)
│   │   ├── GeminiDevClient
│   │   └── VertexAIClient
│   └── OutputStrategy (interface)
│       ├── LogFileOutput
│       └── GoogleDocsOutput
│
├── Shared Core Logic
│   ├── Image Processing
│   │   ├── extract_image_number()
│   │   ├── filter_images()
│   │   └── sort_images()
│   ├── Transcription
│   │   ├── transcribe_image()
│   │   └── process_batch()
│   ├── Logging
│   │   ├── setup_logging()
│   │   └── log_session()
│   └── Error Handling
│       ├── handle_errors()
│       └── generate_resume_info()
│
└── Main Orchestration
    ├── main() (mode-agnostic)
    └── run_transcription()
```

### Strategy Pattern Implementation

#### Authentication Strategy

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

class LocalAuthStrategy(AuthenticationStrategy):
    """API key authentication for local mode."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("API key required (config or GEMINI_API_KEY env var)")
    
    def authenticate(self) -> str:
        """Return API key for Gemini Developer API."""
        return self.api_key
    
    def validate(self) -> bool:
        """Validate API key format."""
        return bool(self.api_key and len(self.api_key) > 10)

class GoogleCloudAuthStrategy(AuthenticationStrategy):
    """OAuth2/ADC authentication for Google Cloud mode."""
    
    def __init__(self, adc_file: str):
        self.adc_file = adc_file
    
    def authenticate(self) -> Credentials:
        """Authenticate using ADC file."""
        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/cloud-platform"
        ]
        creds = Credentials.from_authorized_user_file(self.adc_file, scopes=scopes)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    
    def validate(self) -> bool:
        """Validate credentials file exists and is readable."""
        return os.path.exists(self.adc_file)
```

#### Image Source Strategy

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

class LocalImageSource(ImageSourceStrategy):
    """Local file system image source."""
    
    def __init__(self, image_dir: str):
        self.image_dir = image_dir
        if not os.path.isdir(image_dir):
            raise ValueError(f"Image directory does not exist: {image_dir}")
    
    def list_images(self, config: dict) -> list[dict]:
        """List images from local directory."""
        import glob
        
        # Supported extensions
        extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']
        images = []
        
        for ext in extensions:
            pattern = os.path.join(self.image_dir, ext)
            images.extend(glob.glob(pattern))
        
        # Sort and filter based on config
        images = sorted(images)
        
        # Convert to dict format compatible with existing code
        image_list = []
        for img_path in images:
            filename = os.path.basename(img_path)
            image_list.append({
                'name': filename,
                'path': img_path,
                'id': img_path,  # Use path as ID for local mode
                'webViewLink': f"file://{img_path}"  # Local file URL
            })
        
        # Apply filtering (image_start_number, image_count, etc.)
        return self._filter_images(image_list, config)
    
    def get_image_bytes(self, image_info: dict) -> bytes:
        """Read image from local file system."""
        with open(image_info['path'], 'rb') as f:
            return f.read()
    
    def get_image_url(self, image_info: dict) -> str:
        """Return local file path."""
        return image_info['path']
    
    def _filter_images(self, images: list, config: dict) -> list:
        """Filter images based on config (reuse existing logic)."""
        # Reuse extract_image_number and filtering logic from current code
        # ...

class DriveImageSource(ImageSourceStrategy):
    """Google Drive image source (existing implementation)."""
    
    def __init__(self, drive_service, drive_folder_id: str):
        self.drive_service = drive_service
        self.drive_folder_id = drive_folder_id
    
    def list_images(self, config: dict) -> list[dict]:
        """List images from Google Drive (existing implementation)."""
        # Reuse existing list_images() function
        return list_images(self.drive_service, config)
    
    def get_image_bytes(self, image_info: dict) -> bytes:
        """Download image from Drive (existing implementation)."""
        return download_image(
            self.drive_service,
            image_info['id'],
            image_info['name'],
            config.get('document_name', 'Unknown')
        )
    
    def get_image_url(self, image_info: dict) -> str:
        """Return Drive web view link."""
        return image_info.get('webViewLink', '')
```

#### AI Client Strategy

```python
class AIClientStrategy(ABC):
    """Abstract base class for AI client strategies."""
    
    @abstractmethod
    def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
        """Transcribe image. Returns (text, elapsed_time, usage_metadata)."""
        pass

class GeminiDevClient(AIClientStrategy):
    """Gemini Developer API client."""
    
    def __init__(self, api_key: str, model_id: str = "gemini-1.5-pro"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_id)
        self.model_id = model_id
    
    def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
        """Transcribe using Gemini Developer API."""
        import time
        import PIL.Image
        
        start_time = time.time()
        
        # Convert bytes to PIL Image
        image = PIL.Image.open(io.BytesIO(image_bytes))
        
        # Generate content
        response = self.model.generate_content(
            [prompt, image],
            generation_config={
                'temperature': 0.1,
                'top_p': 0.8,
                'max_output_tokens': 65535,
            }
        )
        
        elapsed_time = time.time() - start_time
        
        # Extract usage metadata if available
        usage_metadata = {}
        if hasattr(response, 'usage_metadata'):
            usage_metadata = {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'completion_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            }
        
        text = response.text if response.text else "[No transcription text received]"
        
        return text, elapsed_time, usage_metadata

class VertexAIClient(AIClientStrategy):
    """Vertex AI client (existing implementation)."""
    
    def __init__(self, genai_client, model_id: str):
        self.genai_client = genai_client
        self.model_id = model_id
    
    def transcribe(self, image_bytes: bytes, filename: str, prompt: str) -> tuple[str, float, dict]:
        """Transcribe using Vertex AI (existing implementation)."""
        # Reuse existing transcribe_image() function
        return transcribe_image(self.genai_client, image_bytes, filename, prompt, self.model_id)
```

#### Output Strategy

```python
class OutputStrategy(ABC):
    """Abstract base class for output strategies."""
    
    @abstractmethod
    def initialize(self, config: dict) -> Any:
        """Initialize output destination."""
        pass
    
    @abstractmethod
    def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> Any:
        """Write batch of transcriptions."""
        pass
    
    @abstractmethod
    def finalize(self, all_pages: list[dict], metrics: dict) -> None:
        """Finalize output (update overview, etc.)."""
        pass

class LogFileOutput(OutputStrategy):
    """Log file output for local mode."""
    
    def __init__(self, output_dir: str, ai_logger):
        self.output_dir = output_dir
        self.ai_logger = ai_logger
        os.makedirs(output_dir, exist_ok=True)
    
    def initialize(self, config: dict) -> str:
        """Initialize log file. Returns log file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        document_name = config.get('document_name', 'transcription')
        log_filename = os.path.join(
            self.output_dir,
            f"{timestamp}-{document_name}-transcription.log"
        )
        
        # Log session start
        self.ai_logger.info(f"=== Transcription Session Started ===")
        self.ai_logger.info(f"Mode: LOCAL")
        self.ai_logger.info(f"Document: {document_name}")
        self.ai_logger.info(f"Archive Index: {config.get('archive_index', 'None')}")
        self.ai_logger.info(f"=== Session Configuration ===\n")
        
        return log_filename
    
    def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> None:
        """Write batch to log file."""
        for page in pages:
            self.ai_logger.info(f"=== AI Response for {page['name']} ===")
            self.ai_logger.info(f"Image: {page.get('webViewLink', page.get('path', ''))}")
            self.ai_logger.info(f"Transcription:\n{page['text']}")
            self.ai_logger.info(f"=== End AI Response for {page['name']} ===\n")
    
    def finalize(self, all_pages: list[dict], metrics: dict) -> None:
        """Finalize log file."""
        self.ai_logger.info(f"=== Transcription Session Completed ===")
        self.ai_logger.info(f"Total images: {len(all_pages)}")
        if metrics:
            self.ai_logger.info(f"Metrics: {metrics}")

class GoogleDocsOutput(OutputStrategy):
    """Google Docs output (existing implementation)."""
    
    def __init__(self, docs_service, drive_service):
        self.docs_service = docs_service
        self.drive_service = drive_service
    
    def initialize(self, config: dict) -> str:
        """Create Google Doc. Returns document ID."""
        # Reuse existing create_doc() function
        doc_id = create_doc(self.docs_service, self.drive_service, doc_name, config)
        return doc_id
    
    def write_batch(self, pages: list[dict], batch_num: int, is_first: bool) -> None:
        """Write batch to Google Doc (existing implementation)."""
        # Reuse existing write_to_doc() function
        # ...
    
    def finalize(self, all_pages: list[dict], metrics: dict) -> None:
        """Update overview section (existing implementation)."""
        # Reuse existing update_overview_section() function
        # ...
```

### Mode Factory

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
    
    @staticmethod
    def _create_local_handlers(config: dict) -> dict:
        """Create handlers for local mode."""
        local_config = config['local']
        
        # Authentication
        auth = LocalAuthStrategy(local_config.get('api_key'))
        
        # Image source
        image_source = LocalImageSource(local_config['image_dir'])
        
        # AI client
        ai_client = GeminiDevClient(
            auth.authenticate(),
            local_config.get('ocr_model_id', 'gemini-1.5-pro')
        )
        
        # Output
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
    
    @staticmethod
    def _create_googlecloud_handlers(config: dict) -> dict:
        """Create handlers for Google Cloud mode (existing implementation)."""
        gc_config = config['googlecloud']
        
        # Authentication
        auth = GoogleCloudAuthStrategy(gc_config['adc_file'])
        creds = auth.authenticate()
        
        # Initialize services
        drive_service, docs_service, genai_client = init_services(creds, gc_config)
        
        # Image source
        image_source = DriveImageSource(drive_service, gc_config['drive_folder_id'])
        
        # AI client
        ai_client = VertexAIClient(genai_client, gc_config['ocr_model_id'])
        
        # Output
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

---

## Main Function Refactoring

### New Main Function Structure

```python
def main(config: dict, prompt_text: str, ai_logger, logs_dir: str):
    """Main function - mode-agnostic transcription orchestration."""
    
    # Detect and validate mode
    mode = detect_mode(config)
    is_valid, errors = validate_config(config, mode)
    if not is_valid:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    logging.info(f"Running in {mode.upper()} mode")
    
    # Create mode-specific handlers
    handlers = ModeFactory.create_handlers(mode, config)
    
    # Normalize config for shared logic
    normalized_config = normalize_config(config, mode)
    
    # List images
    images = handlers['image_source'].list_images(normalized_config)
    if not images:
        logging.error("No images found")
        return
    
    # Initialize output
    output_id = handlers['output'].initialize(normalized_config)
    
    # Process images (shared logic)
    transcribed_pages = []
    usage_metadata_list = []
    timing_list = []
    
    start_time = datetime.now()
    
    # Batch processing (only for Google Cloud mode)
    if mode == 'googlecloud':
        batch_size = normalized_config.get('batch_size_for_doc', 10)
        transcribed_pages = process_batches_googlecloud(
            images, handlers, prompt_text, normalized_config, batch_size
        )
    else:
        # Local mode: process all at once (no batching needed)
        transcribed_pages = process_all_local(
            images, handlers, prompt_text, normalized_config
        )
    
    end_time = datetime.now()
    
    # Calculate metrics
    metrics = calculate_metrics(usage_metadata_list, timing_list)
    
    # Finalize output
    handlers['output'].finalize(transcribed_pages, metrics)
    
    logging.info(f"Transcription completed: {len(transcribed_pages)} images")
```

### Shared Processing Logic

```python
def process_all_local(images: list, handlers: dict, prompt_text: str, config: dict) -> list:
    """Process all images in local mode (no batching)."""
    transcribed_pages = []
    
    for idx, image_info in enumerate(images, 1):
        logging.info(f"Processing image {idx}/{len(images)}: {image_info['name']}")
        
        try:
            # Get image bytes
            img_bytes = handlers['image_source'].get_image_bytes(image_info)
            
            # Transcribe
            text, elapsed_time, usage_metadata = handlers['ai_client'].transcribe(
                img_bytes, image_info['name'], prompt_text
            )
            
            transcribed_pages.append({
                'name': image_info['name'],
                'webViewLink': handlers['image_source'].get_image_url(image_info),
                'text': text
            })
            
            logging.info(f"✓ Completed {image_info['name']} ({elapsed_time:.1f}s)")
            
        except Exception as e:
            logging.error(f"Error processing {image_info['name']}: {e}")
            transcribed_pages.append({
                'name': image_info['name'],
                'webViewLink': handlers['image_source'].get_image_url(image_info),
                'text': f"[Error: {str(e)}]"
            })
    
    # Write all pages to log file
    handlers['output'].write_batch(transcribed_pages, batch_num=1, is_first=True)
    
    return transcribed_pages

def process_batches_googlecloud(images: list, handlers: dict, prompt_text: str, 
                                config: dict, batch_size: int) -> list:
    """Process images in batches for Google Cloud mode (existing logic)."""
    # Reuse existing batch processing logic from current main() function
    # ...
```

---

## Input/Output Changes

### Input Changes

#### LOCAL Mode Input
- **Source:** Local file system directory
- **Format:** Image files (JPG, JPEG)
- **Location:** Specified in `local.image_dir`
- **No network required** for file access

#### GOOGLECLOUD Mode Input
- **Source:** Google Drive folder
- **Format:** Same as current (Drive API)
- **Location:** Specified in `googlecloud.drive_folder_id`
- **Network required** for downloads

### Output Changes

#### LOCAL Mode Output
- **Format:** Log files (text)
- **Location:** `local.output_dir` (default: `logs/`)
- **Structure:**
  ```
  logs/
  ├── YYYYMMDD_HHMMSS-document_name-transcription.log
  └── YYYYMMDD_HHMMSS-ai-responses.log
  ```
- **Content:** Plain text transcriptions with timestamps
- **No formatting** (can be enhanced later with HTML/Markdown)

#### GOOGLECLOUD Mode Output
- **Format:** Google Docs (formatted)
- **Location:** Google Drive folder
- **Structure:** Same as current (formatted document)
- **Content:** Rich formatting, clickable links, overview section

### Output Enhancement (Future)

For LOCAL mode, consider adding:
- HTML report generation
- Markdown file output
- PDF export (via post-processing)
- Optional Google Docs export

---

## Interface Changes

### Command-Line Interface

#### Current Interface
```bash
python transcribe.py config/config.yaml
```

#### New Interface (Unchanged)
```bash
python transcribe.py config/config.yaml
```

**No changes needed** - mode is detected from configuration.

### Configuration Interface

#### New Configuration Examples

**LOCAL Mode:**
```yaml
mode: "local"

local:
  api_key: "your-api-key"  # or use GEMINI_API_KEY env var
  image_dir: "/path/to/images"
  output_dir: "logs"
  ocr_model_id: "gemini-1.5-pro"

prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 100
```

**GOOGLECLOUD Mode:**
```yaml
mode: "googlecloud"

googlecloud:
  project_id: "ukr-transcribe-genea"
  drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
  region: "global"
  ocr_model_id: "gemini-3-flash-preview"
  adc_file: "application_default_credentials.json"

prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 100
batch_size_for_doc: 2
max_images: 1000
```

### Backward Compatibility

Legacy configurations (without `mode` field) will:
1. Auto-detect as GOOGLECLOUD mode
2. Map old flat structure to new nested structure
3. Continue working without changes

```python
def normalize_config(config: dict, mode: str) -> dict:
    """Normalize config to internal format."""
    normalized = config.copy()
    
    if mode == 'googlecloud':
        # Legacy flat structure → nested structure
        if 'googlecloud' not in normalized:
            normalized['googlecloud'] = {
                'project_id': normalized.pop('project_id', None),
                'drive_folder_id': normalized.pop('drive_folder_id', None),
                'region': normalized.pop('region', 'global'),
                'ocr_model_id': normalized.pop('ocr_model_id', None),
                'adc_file': normalized.pop('adc_file', None),
                'document_name': normalized.pop('document_name', None),
                'title_page_filename': normalized.pop('title_page_filename', None)
            }
    
    return normalized
```

---

## Dependencies & Requirements

### Updated Requirements

#### Current `requirements.txt`
```txt
google-cloud-aiplatform>=1.36.0
google-api-python-client>=2.108.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.1.0
google-genai>=0.8.0
Pillow>=10.0.0
python-dotenv>=1.0.0
pyyaml>=6.0
```

#### New `requirements.txt` (Conditional)
```txt
# Core dependencies (always required)
pyyaml>=6.0
python-dotenv>=1.0.0
Pillow>=10.0.0

# Google Cloud dependencies (for GOOGLECLOUD mode)
google-cloud-aiplatform>=1.36.0
google-api-python-client>=2.108.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.1.0

# Gemini API dependencies
# Option 1: google-genai (supports both Vertex AI and Developer API)
google-genai>=0.8.0

# Option 2: google-generativeai (Developer API only, lighter)
# google-generativeai>=0.3.0  # Alternative for LOCAL mode only
```

**Note:** `google-genai` supports both Vertex AI and Developer API, so we can use it for both modes.

### Optional Dependencies

For future enhancements:
```txt
# HTML report generation (optional)
markdown>=3.4.0
jinja2>=3.1.0

# PDF export (optional)
reportlab>=4.0.0  # or weasyprint
```

---

## Migration Path

### Phase 1: Refactoring (Week 1-2)
1. Create strategy interfaces
2. Implement LOCAL mode strategies
3. Refactor existing code into GOOGLECLOUD strategies
4. Create ModeFactory
5. Refactor main() function
6. Add configuration detection/validation

### Phase 2: Testing (Week 2-3)
1. Unit tests for each strategy
2. Integration tests for LOCAL mode
3. Integration tests for GOOGLECLOUD mode
4. Backward compatibility tests
5. End-to-end tests

### Phase 3: Documentation (Week 3)
1. Update README with dual-mode instructions
2. Create configuration examples
3. Update troubleshooting guide
4. Migration guide for existing users

### Phase 4: Release (Week 4)
1. Beta testing with users
2. Bug fixes
3. Final documentation
4. Release

---

## Testing Strategy

### Unit Tests

```python
# test_authentication_strategies.py
def test_local_auth_strategy():
    strategy = LocalAuthStrategy(api_key="test-key")
    assert strategy.validate() == True
    assert strategy.authenticate() == "test-key"

def test_googlecloud_auth_strategy():
    # Mock ADC file
    strategy = GoogleCloudAuthStrategy(adc_file="test_adc.json")
    # Test authentication

# test_image_sources.py
def test_local_image_source():
    source = LocalImageSource("/test/images")
    images = source.list_images(config)
    assert len(images) > 0

# test_ai_clients.py
def test_gemini_dev_client():
    client = GeminiDevClient(api_key="test", model_id="gemini-1.5-pro")
    # Mock transcription call
```

### Integration Tests

```python
# test_local_mode_integration.py
def test_local_mode_end_to_end():
    config = load_test_config("local")
    # Run transcription
    # Verify log files created
    # Verify transcriptions present

# test_googlecloud_mode_integration.py
def test_googlecloud_mode_end_to_end():
    config = load_test_config("googlecloud")
    # Run transcription
    # Verify Google Doc created
    # Verify content correct
```

### Backward Compatibility Tests

```python
def test_legacy_config_compatibility():
    # Load old config format
    config = load_config("config/legacy_config.yaml")
    # Should auto-detect as GOOGLECLOUD mode
    # Should work without changes
```

---

## Risk Mitigation

### Technical Risks

#### 1. Breaking Existing Workflows
**Risk:** Refactoring breaks existing Google Cloud mode  
**Mitigation:**
- Comprehensive testing
- Backward compatibility layer
- Gradual migration
- Keep existing code paths intact

#### 2. Code Complexity
**Risk:** Dual-mode increases complexity  
**Mitigation:**
- Clear separation of concerns
- Strategy pattern (proven design)
- Comprehensive documentation
- Code reviews

#### 3. API Differences
**Risk:** Gemini Developer API differs from Vertex AI  
**Mitigation:**
- Abstract differences in strategy
- Feature detection
- Graceful degradation
- Clear error messages

### User Adoption Risks

#### 1. Configuration Confusion
**Risk:** Users confused by new config structure  
**Mitigation:**
- Clear examples
- Auto-detection of legacy configs
- Migration guide
- Helpful error messages

#### 2. Mode Selection
**Risk:** Users don't know which mode to use  
**Mitigation:**
- Clear documentation
- Default to LOCAL for new users
- Recommendations in README
- Setup wizard (future)

---

## Performance Considerations

### LOCAL Mode Performance
- **Faster file access** (local vs network)
- **No Drive API rate limits**
- **No document batching overhead**
- **Simpler error recovery**

### GOOGLECLOUD Mode Performance
- **Unchanged** from current implementation
- **Same batching logic**
- **Same rate limiting**

---

## Security Considerations

### LOCAL Mode Security
- **API key management:**
  - Support environment variables
  - Warn against committing keys
  - Document secure storage
- **File system access:**
  - Validate paths
  - Prevent directory traversal
  - Document permissions

### GOOGLECLOUD Mode Security
- **Unchanged** from current implementation
- **OAuth2/ADC credentials**
- **Same security practices**

---

## Future Enhancements

### Phase 2: Output Formatting (LOCAL Mode)
- HTML report generation
- Markdown output
- PDF export
- Optional Google Docs export

### Phase 3: Hybrid Mode
- Process locally
- Export to Google Docs
- Best of both worlds

### Phase 4: Setup Wizard
- Interactive configuration
- Mode selection guidance
- API key setup helper

---

## Conclusion

This architecture provides:
- **Single codebase** with clear separation
- **Backward compatibility** for existing users
- **Simplified setup** for new users (LOCAL mode)
- **Full functionality** for advanced users (GOOGLECLOUD mode)
- **Maintainable structure** using proven design patterns

**Recommended Approach:** Refactor existing script with strategy pattern implementation.

**Estimated Effort:** 3-4 weeks (refactoring + testing + documentation)

**Risk Level:** Medium (mitigated by comprehensive testing and backward compatibility)

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** After implementation planning approval
