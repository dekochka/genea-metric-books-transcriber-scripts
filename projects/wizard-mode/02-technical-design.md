# Technical Design: Configuration Wizard & Context Separation

**Project:** Genea Metric Books Transcriber - Wizard Mode  
**Document Type:** Technical Design Specification  
**Date:** January 2026  
**Version:** 1.0  
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Design](#component-design)
4. [Data Structures](#data-structures)
5. [API Specifications](#api-specifications)
6. [Integration Points](#integration-points)
7. [File Structure](#file-structure)
8. [Dependencies](#dependencies)
9. [Implementation Details](#implementation-details)
10. [Error Handling](#error-handling)
11. [Testing Strategy](#testing-strategy)
12. [Backward Compatibility](#backward-compatibility)

---

## Overview

### Design Goals

1. **Eliminate Manual File Editing**: Users should never need to edit YAML or Markdown files directly
2. **Separate Context from Instructions**: Static prompt templates + dynamic context injection
3. **Guided Configuration**: Interactive wizard with validation and helpful prompts
4. **Backward Compatibility**: Existing configs and prompts must continue to work
5. **Extensibility**: Easy to add new prompt templates and context fields

### Design Principles

- **Progressive Enhancement**: Wizard is optional; existing workflow unchanged
- **Single Source of Truth**: Context stored in YAML config, not in prompt files
- **Template-Based**: Reusable prompt templates with variable substitution
- **Validation First**: Pre-flight checks prevent runtime errors
- **User-Friendly**: Clear error messages with actionable solutions

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WIZARD MODULE                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Wizard Controller (CLI Entry Point)         │ │
│  │  - Orchestrates wizard flow                             │ │
│  │  - Manages step progression                             │ │
│  │  - Handles user input/output                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│         v                 v                 v                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Step 1:    │  │   Step 2:    │  │   Step 3:    │         │
│  │   Mode &     │  │   Context    │  │   Processing │         │
│  │   Source     │  │   Collection │  │   Settings   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                     │
│                           v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Title Page Extractor (Optional)                 │ │
│  │  - Loads title page image                               │ │
│  │  - Uses Gemini API for OCR                              │ │
│  │  - Extracts structured context data                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Prompt Assembly Engine                           │ │
│  │  - Loads static template                                 │ │
│  │  - Injects context variables                             │ │
│  │  - Generates final prompt text                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Configuration Generator                           │ │
│  │  - Builds YAML config structure                           │ │
│  │  - Validates all settings                                │ │
│  │  - Writes config file                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Pre-Flight Validator                              │ │
│  │  - Validates authentication                               │ │
│  │  - Checks file paths                                     │ │
│  │  - Verifies API access                                   │ │
│  │  - Tests prompt assembly                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING SYSTEM                               │
│  - transcribe.py (main entry point)                             │
│  - Config loading/validation                                    │
│  - Prompt loading                                               │
│  - Image processing                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User runs: python transcribe.py --wizard
    │
    ├─> WizardController.initialize()
    │       │
    │       ├─> Step1: ModeSelectionStep.run()
    │       │       └─> Collects: mode, source_type
    │       │
    │       ├─> Step2: ContextCollectionStep.run()
    │       │       │
    │       │       ├─> Ask: Extract from title page? (Y/N)
    │       │       │       │
    │       │       │       └─> TitlePageExtractor.extract()
    │       │       │               └─> Pre-populates context fields
    │       │       │
    │       │       └─> Collects: villages, surnames, archive_info
    │       │
    │       └─> Step3: ProcessingSettingsStep.run()
    │               └─> Collects: image_start, image_count, batch_size
    │
    ├─> PromptAssemblyEngine.assemble(template_name, context)
    │       │
    │       ├─> Load template from prompts/templates/
    │       ├─> Replace variables: {{ARCHIVE_REFERENCE}}, etc.
    │       └─> Return assembled prompt text
    │
    ├─> ConfigGenerator.generate(mode, context, settings)
    │       │
    │       ├─> Build YAML structure
    │       ├─> Include context section
    │       ├─> Set prompt_template (not prompt_file)
    │       └─> Write to config file
    │
    └─> PreFlightValidator.validate(config_path)
            │
            ├─> Test API key
            ├─> Check file paths
            ├─> Verify prompt assembly
            └─> Return validation results
```

---

## Component Design

### 1. WizardController

**Purpose:** Main orchestrator for wizard flow

**Location:** `wizard/wizard_controller.py`

**Responsibilities:**
- Manage wizard step progression
- Handle user input/output using `questionary` library
- Coordinate between steps
- Save final configuration

**Interface:**
```python
class WizardController:
    def __init__(self):
        self.steps = []
        self.collected_data = {}
    
    def run(self) -> str:
        """
        Run the complete wizard flow.
        
        Returns:
            Path to generated config file
        """
        pass
    
    def add_step(self, step: WizardStep):
        """Add a step to the wizard flow."""
        pass
    
    def get_data(self, key: str) -> Any:
        """Get collected data from previous steps."""
        pass
    
    def set_data(self, key: str, value: Any):
        """Store data for use in subsequent steps."""
        pass
```

**Implementation Notes:**
- Uses `questionary` for interactive prompts
- Uses `rich` for formatted output and progress indicators
- Supports step navigation (back/forward)
- Validates input at each step

---

### 2. Wizard Steps

**Base Class:**
```python
class WizardStep(ABC):
    """Base class for wizard steps."""
    
    def __init__(self, controller: WizardController):
        self.controller = controller
    
    @abstractmethod
    def run(self) -> dict:
        """
        Execute the step and collect user input.
        
        Returns:
            Dictionary of collected data
        """
        pass
    
    @abstractmethod
    def validate(self, data: dict) -> tuple[bool, list[str]]:
        """
        Validate collected data.
        
        Returns:
            (is_valid, list_of_errors)
        """
        pass
```

**Concrete Steps:**

#### Step 1: ModeSelectionStep
```python
class ModeSelectionStep(WizardStep):
    """Step 1: Select processing mode and image source."""
    
    def run(self) -> dict:
        """
        Collect:
        - mode: 'local' or 'googlecloud'
        - image_source: path or drive_folder_id
        - api_key: (if local mode)
        """
        pass
```

#### Step 2: ContextCollectionStep
```python
class ContextCollectionStep(WizardStep):
    """Step 2: Collect context information."""
    
    def run(self) -> dict:
        """
        Context collection flow with optional title page extraction:
        
        ┌─────────────────────────────────────────┐
        │  Step 2: Context Collection            │
        └─────────────────────────────────────────┘
                    │
                    v
        ┌─────────────────────────────────────────┐
        │  Extract from title page? (Y/N)        │
        └─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        v YES                   v NO
        │                       │
        ┌──────────────┐        ┌──────────────────┐
        │ Get title    │        │ Manual Entry     │
        │ page file    │        │ (skip extraction)│
        └──────────────┘        └──────────────────┘
                │
                v
        ┌──────────────────────┐
        │ AI Extraction        │
        │ (Gemini API call)    │
        └──────────────────────┘
                │
                v
        ┌──────────────────────┐
        │ Display Extracted   │
        │ Data                │
        └──────────────────────┘
                │
                v
        ┌─────────────────────────────────────────┐
        │  User Choice:                          │
        │  1. Accept All                         │
        │  2. Edit Some Fields                    │
        │  3. Reject & Enter Manually            │
        └─────────────────────────────────────────┘
                │
        ┌───────┼───────┐
        │       │       │
        v       v       v
        │       │       │
        ┌───┐ ┌───┐ ┌──────┐
        │Use│ │Edit│ │Manual│
        │All│ │Some│ │Entry │
        └───┘ └───┘ └──────┘
                │
                v
        ┌──────────────────────┐
        │ Final Context Data   │
        └──────────────────────┘
        """
        """
        Collect context information with optional title page extraction.
        
        Flow:
        1. Ask if user wants to extract from title page (optional)
        2. If yes:
           a. Get title page filename/path
           b. Extract context using AI
           c. Show extracted data for review
           d. User can: Accept all, Edit fields, Reject all
        3. If no or rejected:
           a. Collect context manually via prompts
        
        Returns:
            Dictionary with:
            - archive_reference
            - document_type
            - date_range
            - main_villages (list)
            - additional_villages (list)
            - common_surnames (list)
            - title_page_filename (optional)
        """
        pass
    
    def _extract_and_review_title_page(self, mode: str, config: dict) -> dict:
        """
        Extract context from title page and allow user review/accept/reject.
        
        Returns:
            Final context dictionary (extracted + user edits, or manual entry)
        """
        # 1. Ask if user wants to extract from title page
        use_title_page = questionary.confirm(
            "Do you want to extract context from a title page image?",
            default=True
        ).ask()
        
        if not use_title_page:
            return self._collect_context_manually()
        
        # 2. Get title page information
        if mode == 'local':
            title_page_info = self._get_title_page_for_local(config['image_dir'])
        else:
            title_page_info = self._get_title_page_for_googlecloud(
                config['drive_folder_id'],
                config.get('drive_service')
            )
        
        # 3. Extract context using AI
        extractor = TitlePageExtractor(
            api_key=config.get('api_key'),
            model_id=config.get('ocr_model_id', 'gemini-3-flash-preview')
        )
        
        extracted = extractor.extract(title_page_info, mode, config)
        
        if not extracted:
            console.print("[yellow]⚠ Title page extraction failed. Falling back to manual entry.[/yellow]")
            return self._collect_context_manually()
        
        # 4. Show extracted data and allow review
        return self._review_extracted_context(extracted, title_page_info)
    
    def _review_extracted_context(self, extracted: dict, title_page_info: dict) -> dict:
        """
        Show extracted context and allow user to accept/edit/reject.
        
        Returns:
            Final context dictionary
        """
        console.print("\n[bold cyan]Extracted Context from Title Page:[/bold cyan]")
        console.print(f"  Archive Reference: {extracted.get('archive_reference', 'N/A')}")
        console.print(f"  Document Type: {extracted.get('document_type', 'N/A')}")
        console.print(f"  Date Range: {extracted.get('date_range', 'N/A')}")
        console.print(f"  Main Villages: {', '.join(extracted.get('main_villages', []))}")
        console.print(f"  Additional Villages: {', '.join(extracted.get('additional_villages', []))}")
        
        # Ask user what to do
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Accept all extracted data",
                "Edit some fields",
                "Reject and enter manually",
            ]
        ).ask()
        
        if action == "Accept all extracted data":
            return self._format_extracted_context(extracted, title_page_info)
        
        elif action == "Edit some fields":
            return self._edit_extracted_context(extracted, title_page_info)
        
        else:  # Reject and enter manually
            return self._collect_context_manually()
    
    def _edit_extracted_context(self, extracted: dict, title_page_info: dict) -> dict:
        """
        Allow user to edit individual fields from extracted context.
        
        Returns:
            Edited context dictionary
        """
        final_context = {}
        
        # Archive reference
        archive_ref = questionary.text(
            "Archive Reference:",
            default=extracted.get('archive_reference', '')
        ).ask()
        final_context['archive_reference'] = archive_ref
        
        # Document type
        doc_type = questionary.text(
            "Document Type:",
            default=extracted.get('document_type', '')
        ).ask()
        final_context['document_type'] = doc_type
        
        # Date range
        date_range = questionary.text(
            "Date Range:",
            default=extracted.get('date_range', '')
        ).ask()
        final_context['date_range'] = date_range
        
        # Main villages (allow editing list)
        main_villages_text = questionary.text(
            "Main Villages (comma-separated):",
            default=', '.join(extracted.get('main_villages', []))
        ).ask()
        final_context['main_villages'] = [
            v.strip() for v in main_villages_text.split(',') if v.strip()
        ]
        
        # Additional villages
        additional_villages_text = questionary.text(
            "Additional Villages (comma-separated, optional):",
            default=', '.join(extracted.get('additional_villages', []))
        ).ask()
        final_context['additional_villages'] = [
            v.strip() for v in additional_villages_text.split(',') if v.strip()
        ]
        
        # Common surnames
        surnames_text = questionary.text(
            "Common Surnames (comma-separated, optional):",
            default=', '.join(extracted.get('common_surnames', []))
        ).ask()
        final_context['common_surnames'] = [
            s.strip() for s in surnames_text.split(',') if s.strip()
        ]
        
        # Add title page filename
        final_context['title_page_filename'] = title_page_info.get('filename')
        
        return final_context
    
    def _format_extracted_context(self, extracted: dict, title_page_info: dict) -> dict:
        """
        Format extracted context into final structure.
        
        Converts extracted data (which may have simple lists) into
        the structured format expected by the wizard.
        """
        # Convert simple village strings to VillageInfo objects
        main_villages = []
        for village in extracted.get('main_villages', []):
            if isinstance(village, str):
                main_villages.append({'name': village, 'variants': []})
            else:
                main_villages.append(village)
        
        additional_villages = []
        for village in extracted.get('additional_villages', []):
            if isinstance(village, str):
                additional_villages.append({'name': village, 'variants': []})
            else:
                additional_villages.append(village)
        
        return {
            'archive_reference': extracted.get('archive_reference', ''),
            'document_type': extracted.get('document_type', ''),
            'date_range': extracted.get('date_range', ''),
            'main_villages': main_villages,
            'additional_villages': additional_villages,
            'common_surnames': extracted.get('common_surnames', []),
            'title_page_filename': title_page_info.get('filename'),
        }
    
    def _collect_context_manually(self) -> dict:
        """
        Collect context information manually via prompts.
        
        Returns:
            Context dictionary
        """
        # Manual collection prompts...
        pass
    
    def _get_title_page_for_local(self, image_dir: str) -> dict:
        """Get title page file path for LOCAL mode."""
        # List files in image_dir
        # Let user select or enter filename
        # Return: {'filename': '...', 'path': '...'}
        pass
    
    def _get_title_page_for_googlecloud(self, drive_folder_id: str, drive_service) -> dict:
        """Get title page filename for GOOGLECLOUD mode."""
        # List files in Drive folder
        # Let user select or enter filename
        # Return: {'filename': '...', 'drive_folder_id': '...'}
        pass
```

#### Step 3: ProcessingSettingsStep
```python
class ProcessingSettingsStep(WizardStep):
    """Step 3: Configure processing parameters."""
    
    def run(self) -> dict:
        """
        Collect:
        - prompt_template: template name
        - archive_index
        - image_start_number
        - image_count
        - batch_size_for_doc
        - ocr_model_id
        """
        pass
```

---

### 3. TitlePageExtractor

**Purpose:** Extract context from title page images using Gemini API

**Location:** `wizard/title_page_extractor.py`

**Interface:**
```python
class TitlePageExtractor:
    def __init__(self, api_key: str, model_id: str = "gemini-3-flash-preview"):
        self.api_key = api_key
        self.model_id = model_id
    
    def extract(self, title_page_info: dict, mode: str, config: dict) -> dict:
        """
        Extract context information from title page image.
        
        Handles both LOCAL and GOOGLECLOUD modes:
        - LOCAL: Direct file path to image
        - GOOGLECLOUD: Filename in Drive folder, downloads first
        
        Args:
            title_page_info: Dictionary with title page information:
                - For LOCAL: {'filename': 'cover.jpg', 'path': '/path/to/cover.jpg'}
                - For GOOGLECLOUD: {'filename': 'cover.jpg', 'drive_folder_id': '...'}
            mode: 'local' or 'googlecloud'
            config: Configuration dictionary (for Drive service access if needed)
            
        Returns:
            Dictionary with extracted context:
            {
                'archive_reference': str,
                'document_type': str,
                'date_range': str,
                'main_villages': list[str],
                'additional_villages': list[str],
                'common_surnames': list[str],  # May be empty
                'confidence': float  # 0.0-1.0
            }
        """
        pass
    
    def _load_image_local(self, image_path: str) -> bytes:
        """Load image from local file system."""
        pass
    
    def _load_image_drive(self, filename: str, drive_folder_id: str, drive_service) -> bytes:
        """Load image from Google Drive folder."""
        pass
    
    def _extract_from_image_bytes(self, image_bytes: bytes, filename: str) -> dict:
        """Extract context from image bytes using Gemini API."""
        pass
    
    def _build_extraction_prompt(self) -> str:
        """Build the prompt for context extraction."""
        pass
    
    def _parse_extraction_response(self, response: str) -> dict:
        """Parse Gemini response into structured data."""
        pass
```

**Mode-Specific Handling:**

**LOCAL Mode:**
- Title page is a file in the `image_dir`
- Direct file path: `os.path.join(image_dir, title_page_filename)`
- Load image directly from file system

**GOOGLECLOUD Mode:**
- Title page is a file in the Drive folder
- Filename only (not full path)
- Must:
  1. Find file in Drive folder by filename using Drive API
  2. Download file from Drive
  3. Extract context from downloaded bytes

**Extraction Prompt Template:**
```python
def _build_extraction_prompt(self) -> str:
    """Build the prompt for context extraction."""
    return """You are an expert archivist. Extract the following information from this title page image:

1. Archive reference in format: "Ф. X, оп. Y, спр. Z" or similar
2. Document type (e.g., "Метрична книга про народження")
3. Date range (e.g., "1888-1924" or "1888 (липень - грудень) - 1924")
4. Main village(s) mentioned (list all variations/spellings)
5. Additional villages that may appear (if mentioned)
6. Any common surnames visible (optional)

Return your response as JSON in this format:
{
    "archive_reference": "...",
    "document_type": "...",
    "date_range": "...",
    "main_villages": ["village1", "village2"],
    "additional_villages": ["village3"],
    "common_surnames": ["surname1", "surname2"]
}

IMPORTANT: Return ONLY valid JSON, no additional text or markdown formatting."""
```

**API Request Parameters:**

**Request Structure:**
```python
# 1. Initialize client
client = genai.Client(api_key=api_key)  # For LOCAL mode
# OR
client = genai.Client(credentials=credentials)  # For GOOGLECLOUD mode

# 2. Create image part
image_part = types.Part.from_bytes(
    data=image_bytes,           # Image file as bytes
    mime_type="image/jpeg"      # MIME type: "image/jpeg" or "image/png"
)

# 3. Create text prompt part
text_part = types.Part.from_text(text=extraction_prompt)

# 4. Create content with both parts
content = types.Content(
    role="user",
    parts=[text_part, image_part]  # Order: text first, then image
)

# 5. Configure generation parameters
config = types.GenerateContentConfig(
    temperature=0.1,              # Low for consistent extraction
    top_p=0.8,
    seed=0,                      # Deterministic results
    max_output_tokens=4096,       # Sufficient for JSON response
    system_instruction=[types.Part.from_text(text=extraction_prompt)],
    thinking_config=types.ThinkingConfig(
        thinking_budget=2000,     # Lower than transcription
    ),
)

# 6. Make API call
response = client.models.generate_content(
    model=model_id,              # e.g., "gemini-3-flash-preview"
    contents=[content],          # List with single content object
    config=config                # Generation configuration
)

# 7. Extract response text
response_text = response.text
```

**Key Parameters:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `model` | `"gemini-3-flash-preview"` | Model ID (same as transcription) |
| `contents` | `[Content(role="user", parts=[text, image])]` | Image + prompt |
| `temperature` | `0.1` | Low for consistent extraction |
| `max_output_tokens` | `4096` | Sufficient for JSON response |
| `thinking_budget` | `2000` | Lower than transcription (faster) |
| `mime_type` | `"image/jpeg"` | Image format |

**Response Format:**
```python
# Response object has:
response.text  # String containing JSON (or text)
response.usage_metadata  # Token usage information
response.candidates  # Alternative responses (if any)
```

**User Review & Accept/Reject Flow:**

After extraction, the wizard presents the extracted data and offers three options:

1. **Accept All Extracted Data:**
   - Uses all extracted fields as-is
   - Formats data into wizard structure
   - Proceeds to next step

2. **Edit Some Fields:**
   - Shows each field with extracted value as default
   - User can edit any field individually
   - User can add/remove villages or surnames
   - Final context = extracted data + user edits

3. **Reject and Enter Manually:**
   - Discards all extracted data
   - Falls back to manual entry flow
   - User enters all context from scratch

**Implementation Notes:**
- Uses same Gemini client infrastructure as regular transcription
- Same API structure: `Part.from_bytes()` + `Part.from_text()` in `Content`
- Lower token limits (4096 vs 65535) since extraction is shorter
- Lower thinking budget (2000 vs 5000) for faster extraction
- Handles OCR errors gracefully (returns empty dict on failure, falls back to manual)
- Parses JSON from response text (may need extraction if wrapped in markdown)
- **Always allows user review** - extraction is a convenience, not mandatory
- User can skip title page extraction entirely and enter context manually

**Complete API Call Example:**

```python
from google import genai
from google.genai import types

# 1. Initialize client (LOCAL mode)
client = genai.Client(api_key="your-api-key")

# OR (GOOGLECLOUD mode - uses existing genai_client from config)
client = genai_client  # Already initialized with credentials

# 2. Load image bytes
with open("title_page.jpg", "rb") as f:
    image_bytes = f.read()

# 3. Build extraction prompt
extraction_prompt = """You are an expert archivist. Extract..."""

# 4. Create parts
image_part = types.Part.from_bytes(
    data=image_bytes,
    mime_type="image/jpeg"
)
text_part = types.Part.from_text(text=extraction_prompt)

# 5. Create content
content = types.Content(
    role="user",
    parts=[text_part, image_part]  # Text first, then image
)

# 6. Configure generation
config = types.GenerateContentConfig(
    temperature=0.1,
    top_p=0.8,
    seed=0,
    max_output_tokens=4096,
    system_instruction=[types.Part.from_text(text=extraction_prompt)],
    thinking_config=types.ThinkingConfig(thinking_budget=2000),
)

# 7. Make API call
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[content],
    config=config
)

# 8. Extract and parse response
response_text = response.text
# Parse JSON from response_text...
```

---

### 4. PromptAssemblyEngine

**Purpose:** Assemble final prompt from template + context

**Location:** `wizard/prompt_assembler.py`

**Interface:**
```python
class PromptAssemblyEngine:
    def __init__(self, templates_dir: str = "prompts/templates"):
        self.templates_dir = templates_dir
    
    def assemble(self, template_name: str, context: dict) -> str:
        """
        Assemble prompt from template and context.
        
        Args:
            template_name: Name of template (e.g., "metric-book-birth")
            context: Context dictionary with villages, surnames, etc.
            
        Returns:
            Assembled prompt text ready for use
        """
        pass
    
    def list_templates(self) -> list[str]:
        """List available prompt templates."""
        pass
    
    def get_template_info(self, template_name: str) -> dict:
        """Get metadata about a template (description, required fields)."""
        pass
    
    def _load_template(self, template_name: str) -> str:
        """Load template file."""
        pass
    
    def _replace_variables(self, template: str, context: dict) -> str:
        """Replace template variables with context values."""
        pass
    
    def _format_villages(self, villages: list[dict]) -> str:
        """Format village list for template insertion."""
        pass
    
    def _format_surnames(self, surnames: list[str]) -> str:
        """Format surname list for template insertion."""
        pass
```

**Variable Mapping:**

| Template Variable | Context Key | Format |
|-----------------|-------------|--------|
| `{{ARCHIVE_REFERENCE}}` | `context.archive_reference` | String |
| `{{DOCUMENT_DESCRIPTION}}` | `context.document_type` | String |
| `{{DATE_RANGE}}` | `context.date_range` | String |
| `{{MAIN_VILLAGES}}` | `context.main_villages` | Formatted list |
| `{{ADDITIONAL_VILLAGES}}` | `context.additional_villages` | Formatted list |
| `{{COMMON_SURNAMES}}` | `context.common_surnames` | Formatted list |
| `{{MAIN_VILLAGE_NAME}}` | `context.main_villages[0].name` | String |
| `{{MAIN_VILLAGE_NAME_LATIN}}` | `context.main_villages[0].variants[0]` | String |
| `{{FOND_NUMBER}}` | Extracted from `archive_reference` | String |

**Title Page Loading Differences:**

| Mode | Title Page Location | Loading Method |
|------|-------------------|----------------|
| **LOCAL** | File in `image_dir` | Direct file path: `os.path.join(image_dir, filename)` |
| **GOOGLECLOUD** | File in Drive folder | 1. Search Drive folder by filename<br>2. Download file from Drive<br>3. Process downloaded bytes |

**Implementation Notes:**
- For LOCAL mode: Title page must be in the same directory as other images (`image_dir`)
- For GOOGLECLOUD mode: Title page is identified by filename only, searched in Drive folder
- Wizard should handle both scenarios appropriately
- Title page extraction requires API key (same for both modes)

**Example Transformation:**

**Input Context:**
```python
context = {
    'archive_reference': 'Державний архів Тернопільської області - Ф. 487, оп. 1, спр. 545',
    'document_type': 'Метрична книга про народження',
    'date_range': '1888 (липень - грудень) - 1924 (січень - квітень)',
    'main_villages': [
        {'name': 'Турильче', 'variants': ['Turilche', 'Turilcze']}
    ],
    'additional_villages': [
        {'name': 'Вербивка', 'variants': ['Werbivka', 'Werbowce', 'Wierzbówka', 'Вербивці']},
        {'name': 'Нивра', 'variants': ['Niwra', 'Нивра']}
    ],
    'common_surnames': [
        'Boiechko (Боєчко)',
        'Voitkiv (Войтків)',
        'Havryliuk (Гаврилюк)'
    ]
}
```

**Output (replaces `{{MAIN_VILLAGES}}`):**
```markdown
## Villages: 
 Main related to document: 
    *   с. Турильче (v. Turilche, Turilcze)

May appear in document (not full list): 
    *   Вербивка (Werbivka, Werbowce, Wierzbówka, Вербивці), 
    *   Нивра (Niwra, Нивра)
```

---

### 5. ConfigGenerator

**Purpose:** Generate YAML configuration file from wizard data

**Location:** `wizard/config_generator.py`

**Interface:**
```python
class ConfigGenerator:
    def __init__(self):
        pass
    
    def generate(self, wizard_data: dict, output_path: str) -> str:
        """
        Generate YAML config file from wizard data.
        
        Args:
            wizard_data: Complete data collected from wizard
            output_path: Path where config should be saved
            
        Returns:
            Path to generated config file
        """
        pass
    
    def _build_config_structure(self, wizard_data: dict) -> dict:
        """Build YAML structure from wizard data."""
        pass
    
    def _format_context_section(self, context: dict) -> dict:
        """Format context data for YAML config."""
        pass
```

**Generated Config Structure:**

**For LOCAL Mode:**
```yaml
# Generated by Wizard Mode
# Date: 2026-01-25

mode: "local"

# Mode-specific configuration
local:
  api_key: "your-api-key"  # or use GEMINI_API_KEY env var
  image_dir: "/path/to/images"
  output_dir: "logs"
  ocr_model_id: "gemini-3-flash-preview"
  # Note: title_page_filename not in local config (if needed, would be in image_dir)
```

**For GOOGLECLOUD Mode:**
```yaml
# Generated by Wizard Mode
# Date: 2026-01-25

mode: "googlecloud"

# Mode-specific configuration
googlecloud:
  project_id: "ru-ocr-genea"
  drive_folder_id: "1e_T8TdXaWTYNfEQg-l8xX8Mhzm9IEF0T"
  region: "global"
  ocr_model_id: "gemini-3-flash-preview"
  adc_file: "application_default_credentials.json"
  document_name: "My Document"
  title_page_filename: "cover-title-page.jpg"  # Filename in Drive folder

# Context section (NEW)
context:
  archive_reference: "Державний архів Тернопільської області - Ф. 487, оп. 1, спр. 545"
  document_type: "Метрична книга про народження"
  date_range: "1888 (липень - грудень) - 1924 (січень - квітень)"
  main_villages:
    - name: "Турильче"
      variants: ["Turilche", "Turilcze"]
  additional_villages:
    - name: "Вербивка"
      variants: ["Werbivka", "Werbowce", "Wierzbówka", "Вербивці"]
    - name: "Нивра"
      variants: ["Niwra", "Нивра"]
  common_surnames:
    - "Boiechko (Боєчко)"
    - "Voitkiv (Войтків)"
    - "Havryliuk (Гаврилюк)"

# Processing settings
prompt_template: "metric-book-birth"  # References static template
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 13
batch_size_for_doc: 3
max_images: 20
retry_mode: false
retry_image_list: []
```

**Key Changes:**
- `prompt_file` → `prompt_template` (references template, not file)
- New `context` section with structured data
- Context can be used to assemble prompt dynamically

---

### 6. PreFlightValidator

**Purpose:** Validate configuration before processing starts

**Location:** `wizard/preflight_validator.py`

**Interface:**
```python
class PreFlightValidator:
    def __init__(self):
        pass
    
    def validate(self, config_path: str) -> ValidationResult:
        """
        Perform comprehensive pre-flight validation.
        
        Args:
            config_path: Path to config file to validate
            
        Returns:
            ValidationResult with is_valid, errors, warnings
        """
        pass
    
    def validate_authentication(self, config: dict) -> list[str]:
        """Validate API keys and credentials."""
        pass
    
    def validate_paths(self, config: dict, mode: str) -> list[str]:
        """
        Validate file and directory paths.
        
        Mode-specific validation:
        - LOCAL: Check image_dir exists, title page file exists (if specified)
        - GOOGLECLOUD: Check Drive folder accessible, title page found (if specified)
        """
        pass
    
    def validate_context(self, config: dict) -> list[str]:
        """Validate context data completeness."""
        pass
    
    def validate_prompt_assembly(self, config: dict) -> list[str]:
        """Test prompt assembly with current context."""
        pass
```

**ValidationResult:**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]
```

**Validation Checks:**

1. **Authentication:**
   - API key exists and is valid (test with simple request)
   - Google Cloud credentials valid (if cloud mode)
   - Drive folder accessible (if cloud mode)

2. **Paths:**
   - Image directory exists and is readable (local mode)
   - Output directory is writable
   - Title page file exists (if specified)
   - Template file exists

3. **Context:**
   - At least one main village specified
   - Archive reference format valid
   - Date range format reasonable

4. **Prompt Assembly:**
   - Template exists
   - All required variables can be replaced
   - Assembled prompt is non-empty

5. **Images:**
   - Image files found matching pattern
   - Image count matches expected range
   - Title page exists (if specified):
     - **LOCAL mode**: File exists in `image_dir`
     - **GOOGLECLOUD mode**: File found in Drive folder by filename

---

## Data Structures

### Context Data Structure

```python
@dataclass
class ContextData:
    """Structured context data for prompt assembly."""
    archive_reference: str
    document_type: str
    date_range: str
    main_villages: list[VillageInfo]
    additional_villages: list[VillageInfo]
    common_surnames: list[str]
    title_page_filename: Optional[str] = None

@dataclass
class VillageInfo:
    """Information about a village."""
    name: str  # Primary name (e.g., "Турильче")
    variants: list[str]  # Alternative spellings (e.g., ["Turilche", "Turilcze"])
```

### Wizard Data Structure

```python
@dataclass
class WizardData:
    """Complete data collected from wizard."""
    # Step 1: Mode & Source
    mode: str  # 'local' or 'googlecloud'
    image_source: str  # Path or drive_folder_id
    api_key: Optional[str] = None
    
    # Step 2: Context
    context: ContextData
    
    # Step 3: Processing Settings
    prompt_template: str
    archive_index: str
    image_start_number: int = 1
    image_count: int = 1
    batch_size_for_doc: int = 3
    ocr_model_id: str = "gemini-3-flash-preview"
    max_images: Optional[int] = None
    retry_mode: bool = False
    retry_image_list: list[str] = field(default_factory=list)
```

### Config Structure (Extended)

```python
# Extends existing config structure with context section
Config = {
    'mode': str,
    'local' | 'googlecloud': {...},
    'context': {  # NEW
        'archive_reference': str,
        'document_type': str,
        'date_range': str,
        'main_villages': list[dict],
        'additional_villages': list[dict],
        'common_surnames': list[str],
    },
    'prompt_template': str,  # Changed from 'prompt_file'
    'archive_index': str,
    'image_start_number': int,
    'image_count': int,
    # ... other existing fields
}
```

---

## API Specifications

### Command-Line Interface

**New Entry Point:**
```bash
python transcribe.py --wizard [--output config/my-project.yaml]
```

**Arguments:**
- `--wizard`: Enable wizard mode
- `--output`: Optional output path for config file (default: prompts user)

**Existing Entry Point (Unchanged):**
```bash
python transcribe.py config/config.yaml
```

### Internal APIs

#### Prompt Loading (Modified)

**Current:**
```python
def load_prompt_text(prompt_file: str) -> str:
    """Load prompt from prompts/ directory."""
```

**New (Backward Compatible):**
```python
def load_prompt_text(config: dict) -> str:
    """
    Load prompt text from config.
    
    Supports both:
    1. prompt_file: Direct file reference (legacy)
    2. prompt_template + context: Template assembly (new)
    """
    if 'prompt_file' in config:
        # Legacy mode: load file directly
        return load_prompt_file(config['prompt_file'])
    elif 'prompt_template' in config:
        # Wizard mode: assemble from template
        assembler = PromptAssemblyEngine()
        context = config.get('context', {})
        return assembler.assemble(config['prompt_template'], context)
    else:
        raise ValueError("Either prompt_file or prompt_template must be specified")
```

---

## Integration Points

### 1. Integration with transcribe.py

**Modifications Required:**

1. **Argument Parser:**
   ```python
   parser.add_argument(
       '--wizard',
       action='store_true',
       help='Run interactive configuration wizard'
   )
   parser.add_argument(
       '--output',
       type=str,
       help='Output path for generated config file (wizard mode only)'
   )
   ```

2. **Main Entry Point:**
   ```python
   if args.wizard:
       from wizard.wizard_controller import WizardController
       controller = WizardController()
       config_path = controller.run()
       # Continue with normal flow using generated config
       config = load_config(config_path)
   else:
       # Existing flow
       config = load_config(args.config_file)
   ```

3. **Prompt Loading:**
   - Modify `load_prompt_text()` to support template assembly
   - Keep backward compatibility with `prompt_file`

### 2. Integration with Existing Config System

**No Breaking Changes:**
- Existing `load_config()`, `validate_config()`, `normalize_config()` remain unchanged
- New `context` section is optional
- `prompt_template` is alternative to `prompt_file` (not replacement)

**Validation Updates:**
```python
def validate_config(config: dict, mode: str) -> tuple[bool, list[str]]:
    errors = []
    
    # Existing validations...
    
    # New: Validate prompt_template or prompt_file
    if 'prompt_template' in config:
        if 'context' not in config:
            errors.append("prompt_template requires context section")
        # Validate template exists
        template_path = f"prompts/templates/{config['prompt_template']}.md"
        if not os.path.exists(template_path):
            errors.append(f"Template not found: {template_path}")
    elif 'prompt_file' not in config:
        errors.append("Either prompt_file or prompt_template must be specified")
    
    # New: Validate context if present
    if 'context' in config:
        context = config['context']
        if not context.get('main_villages'):
            errors.append("context.main_villages is required")
        if not context.get('archive_reference'):
            errors.append("context.archive_reference is required")
    
    return len(errors) == 0, errors
```

### 3. Integration with Gemini Client

**Title Page Extraction:**
- Reuse existing Gemini client infrastructure
- Use same API key and model selection
- Handle errors gracefully (fallback to manual entry)

---

## File Structure

### New Files

```
genea_gcloud_gemini_transcriber/
├── wizard/
│   ├── __init__.py
│   ├── wizard_controller.py       # Main orchestrator
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── base_step.py           # Base class for steps
│   │   ├── mode_selection_step.py
│   │   ├── context_collection_step.py
│   │   └── processing_settings_step.py
│   ├── title_page_extractor.py    # OCR extraction
│   ├── prompt_assembler.py        # Template assembly
│   ├── config_generator.py        # YAML generation
│   └── preflight_validator.py     # Validation
├── prompts/
│   └── templates/
│       ├── metric-book-birth.md    # Static template (already created)
│       ├── metric-book-marriage.md # Future
│       └── revision-list.md        # Future
└── transcribe.py                   # Modified entry point
```

### Modified Files

- `transcribe.py`: Add `--wizard` argument, modify prompt loading
- `transcribe.py`: Update `validate_config()` to support `prompt_template` and `context`

---

## Dependencies

### New Dependencies

**Required:**
- `questionary>=1.10.0` - Interactive CLI prompts
- `rich>=13.0.0` - Formatted terminal output, progress bars

**Optional (for future enhancements):**
- `typer>=0.9.0` - Alternative CLI framework (if we want more advanced CLI)

### Updated requirements.txt

```txt
# Existing dependencies...
questionary>=1.10.0
rich>=13.0.0
```

### Installation

```bash
pip install questionary rich
```

---

## Implementation Details

### 1. Wizard Flow Implementation

**Step Progression:**
```python
class WizardController:
    def run(self) -> str:
        console = Console()
        console.print(Panel.fit("Genealogical Transcription Wizard", style="bold blue"))
        
        # Step 1: Mode Selection
        step1 = ModeSelectionStep(self)
        step1_data = step1.run()
        self.set_data('mode', step1_data)
        
        # Step 2: Context Collection
        step2 = ContextCollectionStep(self)
        step2_data = step2.run()
        self.set_data('context', step2_data)
        
        # Step 3: Processing Settings
        step3 = ProcessingSettingsStep(self)
        step3_data = step3.run()
        self.set_data('settings', step3_data)
        
        # Assemble final data
        wizard_data = self._assemble_wizard_data()
        
        # Generate config
        generator = ConfigGenerator()
        output_path = questionary.path(
            "Where should the config file be saved?",
            default="config/my-project.yaml"
        ).ask()
        
        config_path = generator.generate(wizard_data, output_path)
        
        # Validate
        validator = PreFlightValidator()
        result = validator.validate(config_path)
        
        if not result.is_valid:
            console.print("[red]Validation failed:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            if not questionary.confirm("Continue anyway?").ask():
                return None
        
        console.print(f"[green]✓ Configuration saved to: {config_path}[/green]")
        return config_path
```

### 2. Template Variable Replacement

**Implementation:**
```python
class PromptAssemblyEngine:
    def _replace_variables(self, template: str, context: dict) -> str:
        """Replace all template variables with context values."""
        result = template
        
        # Simple variable replacement
        replacements = {
            '{{ARCHIVE_REFERENCE}}': context.get('archive_reference', ''),
            '{{DOCUMENT_DESCRIPTION}}': context.get('document_type', ''),
            '{{DATE_RANGE}}': context.get('date_range', ''),
            '{{MAIN_VILLAGES}}': self._format_villages(
                context.get('main_villages', []), 
                is_main=True
            ),
            '{{ADDITIONAL_VILLAGES}}': self._format_villages(
                context.get('additional_villages', []), 
                is_main=False
            ),
            '{{COMMON_SURNAMES}}': self._format_surnames(
                context.get('common_surnames', [])
            ),
        }
        
        # Extract fond number from archive reference
        fond_match = re.search(r'Ф\.\s*(\d+)', context.get('archive_reference', ''))
        if fond_match:
            replacements['{{FOND_NUMBER}}'] = fond_match.group(1)
        
        # Main village name (first main village)
        if context.get('main_villages'):
            main_village = context['main_villages'][0]
            replacements['{{MAIN_VILLAGE_NAME}}'] = main_village['name']
            if main_village.get('variants'):
                replacements['{{MAIN_VILLAGE_NAME_LATIN}}'] = main_village['variants'][0]
        
        # Perform replacements
        for var, value in replacements.items():
            result = result.replace(var, value)
        
        return result
```

### 3. Title Page Extraction

**Implementation:**
```python
class TitlePageExtractor:
    def extract(self, title_page_info: dict, mode: str, config: dict) -> dict:
        """Extract context from title page (mode-aware)."""
        # Load image based on mode
        if mode == 'local':
            image_bytes = self._load_image_local(title_page_info['path'])
        elif mode == 'googlecloud':
            drive_service = config.get('drive_service')  # From wizard context
            image_bytes = self._load_image_drive(
                title_page_info['filename'],
                title_page_info['drive_folder_id'],
                drive_service
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        if not image_bytes:
            logging.warning("Failed to load title page image")
            return {}
        
        # Extract context from image bytes
        return self._extract_from_image_bytes(
            image_bytes,
            title_page_info.get('filename', 'title_page')
        )
    
    def _load_image_local(self, image_path: str) -> bytes:
        """Load image from local file system."""
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Failed to load local image {image_path}: {e}")
            return None
    
    def _load_image_drive(self, filename: str, drive_folder_id: str, drive_service) -> bytes:
        """Load image from Google Drive folder."""
        try:
            # Find file in Drive
            from transcribe import find_title_page_image, download_image
            
            image_file_id = find_title_page_image(drive_service, drive_folder_id, filename)
            if not image_file_id:
                logging.warning(f"Title page '{filename}' not found in Drive folder")
                return None
            
            # Download image
            image_bytes = download_image(
                drive_service,
                image_file_id,
                filename,
                f"Folder_{drive_folder_id[:8]}"
            )
            return image_bytes
            
        except Exception as e:
            logging.error(f"Failed to load Drive image {filename}: {e}")
            return None
    
    def _extract_from_image_bytes(self, image_bytes: bytes, filename: str) -> dict:
        """
        Extract context from image bytes using Gemini API.
        
        Uses the same API structure as regular transcription but with
        a specialized extraction prompt.
        """
        prompt = self._build_extraction_prompt()
        
        try:
            # Initialize Gemini client (same as regular transcription)
            client = genai.Client(api_key=self.api_key)
            
            # Create image part (same format as transcribe_image)
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"  # or detect from filename
            )
            
            # Create text prompt part
            text_part = types.Part.from_text(text=prompt)
            
            # Create content with both image and prompt
            content = types.Content(
                role="user",
                parts=[text_part, image_part]
            )
            
            # Configure generation parameters (same as regular transcription)
            generate_content_config = types.GenerateContentConfig(
                temperature=0.1,          # Low temperature for consistent extraction
                top_p=0.8,
                seed=0,                    # Deterministic results
                max_output_tokens=4096,    # Lower than transcription (extraction is shorter)
                system_instruction=[types.Part.from_text(text=prompt)],
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2000,  # Lower budget for extraction
                ),
            )
            
            # Make API call (same structure as transcribe_image)
            response = client.models.generate_content(
                model=self.model_id,
                contents=[content],
                config=generate_content_config
            )
            
            # Extract text from response
            response_text = response.text if response.text else ""
            
            # Parse JSON response
            extracted = self._parse_extraction_response(response_text)
            
            # Log usage metadata if available
            if hasattr(response, 'usage_metadata'):
                logging.info(f"Title page extraction usage: {response.usage_metadata}")
            
            return extracted
            
        except Exception as e:
            logging.warning(f"Title page extraction failed: {e}")
            return {}
    
    def _parse_extraction_response(self, response_text: str) -> dict:
        """Parse JSON response from Gemini."""
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Fallback: return empty dict
        return {}
```

---

## Error Handling

### Error Categories

1. **User Input Errors:**
   - Invalid file paths
   - Invalid format (e.g., archive reference)
   - Missing required fields
   - **Handling:** Clear error messages, allow retry

2. **Template Errors:**
   - Template file not found
   - Missing required variables
   - **Handling:** Fallback to manual prompt entry

3. **Title Page Extraction Errors:**
   - Image file not found
   - OCR failure
   - **Handling:** Fallback to manual entry, show warning

4. **Validation Errors:**
   - API key invalid
   - Paths inaccessible
   - **Handling:** Show errors, allow continue anyway

### Error Messages

**Format:**
```
[ERROR] Description of what went wrong
  → Suggestion: What user should do
  → Example: Example of correct input
```

**Example:**
```
[ERROR] Archive reference format invalid
  → Suggestion: Use format "Ф. 487, оп. 1, спр. 545"
  → Example: Ф. 487, оп. 1, спр. 545
```

---

## Testing Strategy

### Unit Tests

**Test Files:**
- `tests/unit/test_wizard_controller.py`
- `tests/unit/test_prompt_assembler.py`
- `tests/unit/test_title_page_extractor.py`
- `tests/unit/test_config_generator.py`
- `tests/unit/test_preflight_validator.py`

**Key Test Cases:**

1. **Prompt Assembly:**
   - Template loading
   - Variable replacement
   - Missing variable handling
   - Village/surname formatting

2. **Config Generation:**
   - YAML structure correctness
   - Context section formatting
   - Backward compatibility

3. **Title Page Extraction:**
   - JSON parsing
   - Error handling
   - Fallback behavior

4. **Validation:**
   - All validation checks
   - Error message clarity
   - Warning generation

### Integration Tests

**Test Files:**
- `tests/integration/test_wizard_flow.py`
- `tests/integration/test_wizard_config_compatibility.py`

**Key Test Cases:**

1. **End-to-End Wizard:**
   - Complete wizard flow
   - Config file generation
   - Generated config works with transcribe.py

2. **Backward Compatibility:**
   - Old configs still work
   - Old prompts still work
   - Mixed usage scenarios

### Manual Testing

**Test Scenarios:**
1. New user runs wizard from scratch
2. User extracts context from title page
3. User manually enters all context
4. User edits generated config
5. User runs transcription with wizard-generated config

---

## Backward Compatibility

### Compatibility Strategy

1. **Wizard is Optional:**
   - Existing `python transcribe.py config.yaml` still works
   - Wizard is opt-in via `--wizard` flag

2. **Config Format:**
   - Old configs with `prompt_file` continue to work
   - New configs with `prompt_template` + `context` work
   - Both formats supported simultaneously

3. **Prompt Loading:**
   - Modified `load_prompt_text()` checks for both:
     - `prompt_file` → load file directly (legacy)
     - `prompt_template` + `context` → assemble from template (new)

4. **No Breaking Changes:**
   - All existing configs remain valid
   - All existing prompts remain valid
   - Existing workflows unchanged

### Migration Path

**For Existing Users:**
1. Continue using existing configs/prompts (no change required)
2. Optionally migrate to wizard-generated configs
3. Optionally convert existing prompts to templates

**For New Users:**
1. Use wizard from the start
2. No need to understand YAML or Markdown

---

## Implementation Phases

### Phase 1: Core Wizard (Week 1)

**Deliverables:**
1. ✅ WizardController with step management
2. ✅ Three wizard steps (Mode, Context, Settings)
3. ✅ PromptAssemblyEngine
4. ✅ ConfigGenerator
5. ✅ Basic validation

**Files to Create:**
- `wizard/wizard_controller.py`
- `wizard/steps/*.py`
- `wizard/prompt_assembler.py`
- `wizard/config_generator.py`

**Files to Modify:**
- `transcribe.py` (add `--wizard` argument)
- `transcribe.py` (modify `load_prompt_text()`)

### Phase 2: Title Page Extraction (Week 2)

**Deliverables:**
1. ✅ TitlePageExtractor
2. ✅ Integration with wizard
3. ✅ User review/accept/reject interface:
   - Display extracted data in readable format
   - "Accept all" option (use extracted data as-is)
   - "Edit some fields" option (edit individual fields)
   - "Reject and enter manually" option (discard extracted, enter from scratch)
   - Option to skip title page extraction entirely

**Files to Create:**
- `wizard/title_page_extractor.py`

### Phase 3: Enhanced Validation & Feedback (Week 2-3)

**Deliverables:**
1. ✅ PreFlightValidator
2. ✅ Rich progress indicators
3. ✅ Cost estimation

**Files to Create:**
- `wizard/preflight_validator.py`

**Files to Modify:**
- `transcribe.py` (add progress bars)

### Phase 4: HTML Proofing (Week 3-4)

**Deliverables:**
1. ✅ HTML output generation
2. ✅ Side-by-side layout

**Files to Create:**
- `wizard/html_proofer.py` (or add to existing output module)

---

## Success Criteria

### Functional Requirements

- ✅ Wizard generates valid config files
- ✅ Prompt assembly works correctly
- ✅ Title page extraction extracts context
- ✅ Generated configs work with existing transcribe.py
- ✅ Backward compatibility maintained

### Non-Functional Requirements

- ✅ Wizard completes in < 5 minutes
- ✅ Error messages are clear and actionable
- ✅ Validation catches 95%+ of errors before processing
- ✅ Title page extraction accuracy > 80%

---

## Mode-Specific Considerations

### Title Page Handling

**LOCAL Mode:**
- Title page is a file in the `image_dir` directory
- User provides filename (e.g., `cover-title-page.jpg`)
- Full path: `os.path.join(image_dir, title_page_filename)`
- Direct file access - no API calls needed
- **Note:** Currently, LOCAL mode config doesn't include `title_page_filename` in examples, but wizard can support it

**GOOGLECLOUD Mode:**
- Title page is a file in the Google Drive folder
- User provides filename only (e.g., `cover-title-page.jpg`)
- Must search Drive folder by filename using Drive API
- Must download file from Drive before processing
- Requires Drive API access and proper authentication
- **Config location:** `googlecloud.title_page_filename`

### Wizard Flow Differences

**Step 1: Mode Selection**
- LOCAL: Collects `image_dir` path
- GOOGLECLOUD: Collects `drive_folder_id` (from URL or direct input)

**Step 2: Context Collection (Title Page)**
- LOCAL: 
  - Lists files in `image_dir`
  - User selects title page from list or enters filename
  - Validates file exists
- GOOGLECLOUD:
  - Lists files in Drive folder (requires Drive API)
  - User selects title page from list or enters filename
  - Validates file exists in Drive folder

**Step 3: Title Page Extraction**
- LOCAL: Direct file read → Extract
- GOOGLECLOUD: Drive API search → Download → Extract

### Config Generation Differences

**LOCAL Mode Config:**
```yaml
mode: "local"
local:
  image_dir: "/path/to/images"
  # title_page_filename not in local section (would be in image_dir)
```

**GOOGLECLOUD Mode Config:**
```yaml
mode: "googlecloud"
googlecloud:
  drive_folder_id: "..."
  title_page_filename: "cover-title-page.jpg"  # In googlecloud section
```

---

## Open Questions & Decisions Needed

1. **Template Variable Syntax:**
   - Current: `{{VARIABLE}}`
   - Alternative: `{VARIABLE}`, `$VARIABLE`, etc.
   - **Decision:** Use `{{VARIABLE}}` (clear, unlikely to conflict)

2. **Context Storage:**
   - Option 1: In YAML config (recommended)
   - Option 2: Separate context file
   - **Decision:** In YAML config for simplicity

3. **Prompt File Naming:**
   - Option 1: Keep `prompt_file` for legacy, add `prompt_template` for new
   - Option 2: Deprecate `prompt_file`, use only `prompt_template`
   - **Decision:** Support both for backward compatibility

4. **Title Page Extraction Model:**
   - Use same model as transcription?
   - Use lighter/faster model?
   - **Decision:** Use same model for consistency

5. **Title Page in LOCAL Mode:**
   - Should LOCAL mode support title pages?
   - If yes, where should it be configured?
   - **Decision:** Support it in wizard, store in `local` section if needed, or as shared config

---

## Next Steps

1. **Review & Approve:** Technical design review
2. **Create Implementation Plan:** Detailed task breakdown
3. **Set Up Development Environment:** Install dependencies
4. **Begin Phase 1 Implementation:** Core wizard components

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Ready for Implementation
