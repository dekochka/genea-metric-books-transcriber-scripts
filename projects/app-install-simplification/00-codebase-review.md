# Codebase Review - Current Implementation Analysis

**Date:** January 2025  
**Purpose:** Document current codebase structure for dual-mode refactoring  
**Status:** Complete

---

## Overview

The current `transcribe.py` is a monolithic script (~2549 lines) that implements Google Cloud-based transcription workflow. This document maps the current structure to identify refactoring points for dual-mode implementation.

---

## Function Dependency Map

### Configuration & Setup Functions
```
load_config(config_path) → dict
  ├── Validates required keys (project_id, drive_folder_id, etc.)
  └── Returns config dict

load_prompt_text(prompt_file) → str
  └── Loads prompt from prompts/ directory

setup_logging(config) → tuple
  └── Returns (log_filename, ai_log_filename, ai_logger)
```

### Authentication & Services
```
authenticate(adc_file) → Credentials
  └── Loads OAuth2 credentials from ADC file

init_services(creds, config) → tuple
  ├── Creates Vertex AI genai.Client
  ├── Creates Google Drive API service
  └── Creates Google Docs API service
  └── Returns (drive_service, docs_service, genai_client)
```

### Image Processing Functions
```
extract_image_number(filename) → int | None
  └── Extracts numeric identifier from filename patterns

get_folder_name(drive_service, drive_folder_id) → str | None
  └── Fetches folder name from Drive API

list_images(drive_service, config) → list[dict]
  ├── Fetches images from Google Drive folder
  ├── Supports pagination (up to max_images)
  ├── Filters by image_start_number and image_count
  ├── Supports retry_mode for specific images
  └── Returns list of image metadata (id, name, webViewLink)

download_image(drive_service, file_id, file_name, document_name) → bytes
  └── Downloads image bytes from Drive API
```

### AI Transcription Functions
```
transcribe_image(genai_client, image_bytes, file_name, prompt_text, ocr_model_id) → tuple
  ├── Sends image to Vertex AI Gemini
  ├── Handles retries with exponential backoff
  ├── Extracts usage metadata
  └── Returns (text, elapsed_time, usage_metadata)
```

### Document Creation & Writing Functions
```
find_title_page_image(drive_service, drive_folder_id, title_page_filename) → dict | None
  └── Finds title page image in Drive folder

upload_image_to_drive(drive_service, image_bytes, filename, drive_folder_id) → str
  └── Uploads image to Drive (for title page)

insert_title_page_image_and_transcribe(...) → None
  ├── Inserts title page image into Google Doc
  └── Transcribes title page

create_doc(docs_service, drive_service, title, config) → str | None
  ├── Creates Google Doc
  ├── Adds document header
  ├── Inserts title page (if configured)
  └── Returns doc_id or None on permission error

write_to_doc(docs_service, drive_service, doc_id, pages, config, ...) → None
  ├── Writes transcriptions to Google Doc
  ├── Adds page headers with archive index
  ├── Adds clickable source links
  ├── Adds record links (archive references)
  └── Updates overview section

update_overview_section(docs_service, doc_id, pages, config, ...) → bool
  └── Updates TRANSCRIPTION RUN SUMMARY section with final metrics

add_record_links_to_text(text, archive_index, page_number, web_view_link) → str
  └── Adds clickable archive references to record headers (lines starting with ###)
```

### Utility Functions
```
calculate_metrics(usage_metadata_list, timing_list) → dict
  └── Calculates aggregate metrics from usage data

save_transcription_locally(pages, doc_name, config, ...) → str
  └── Fallback: saves transcription to local text file
```

### Main Function
```
main(config, prompt_text, ai_logger, logs_dir) → None
  ├── authenticate()
  ├── init_services()
  ├── get_folder_name() (if document_name not provided)
  ├── list_images()
  ├── Loop: Process images in batches
  │   ├── download_image()
  │   ├── transcribe_image()
  │   └── write_to_doc() (after each batch)
  ├── update_overview_section() (final)
  └── Error handling with resume information
```

---

## Current Architecture Flow

```
Entry Point (__main__)
  ├── Load config
  ├── Setup logging
  ├── Load prompt
  └── Call main()

main()
  ├── authenticate() → Credentials
  ├── init_services() → (drive, docs, genai_client)
  ├── get_folder_name() → document_name
  ├── list_images() → [image_metadata]
  │
  └── Batch Processing Loop:
      ├── For each image in batch:
      │   ├── download_image() → bytes
      │   ├── transcribe_image() → (text, time, metadata)
      │   └── Collect results
      │
      └── After batch:
          ├── create_doc() (first batch only)
          ├── write_to_doc()
          └── update_overview_section() (final batch)
```

---

## Refactoring Points

### 1. Mode-Specific Operations (Strategy Pattern Candidates)

#### Authentication
- **Current:** `authenticate(adc_file)` - OAuth2/ADC only
- **Refactor to:** `AuthenticationStrategy` interface
  - `LocalAuthStrategy`: API key authentication
  - `GoogleCloudAuthStrategy`: OAuth2/ADC (existing)

#### Image Source
- **Current:** `list_images(drive_service, config)` + `download_image(drive_service, ...)`
- **Refactor to:** `ImageSourceStrategy` interface
  - `LocalImageSource`: List from local directory, read files
  - `DriveImageSource`: List from Drive API, download (existing)

#### AI Client
- **Current:** `transcribe_image(genai_client, ...)` - Vertex AI only
- **Refactor to:** `AIClientStrategy` interface
  - `GeminiDevClient`: Gemini Developer API (new)
  - `VertexAIClient`: Vertex AI (existing)

#### Output
- **Current:** `create_doc()`, `write_to_doc()`, `update_overview_section()` - Google Docs only
- **Refactor to:** `OutputStrategy` interface
  - `LogFileOutput`: Write to log files (new)
  - `GoogleDocsOutput`: Google Docs (existing)

### 2. Shared Code (No Refactoring Needed)

These functions can be reused as-is:
- `extract_image_number()` - Works for both local and Drive filenames
- `calculate_metrics()` - Mode-agnostic
- `load_prompt_text()` - Mode-agnostic
- `setup_logging()` - Mode-agnostic (may need minor adjustments)
- `add_record_links_to_text()` - Mode-agnostic

### 3. Configuration Changes

**Current Required Keys:**
```python
required_keys = [
    'prompt_file', 'project_id', 'drive_folder_id',
    'archive_index', 'region', 'ocr_model_id', 'adc_file',
    'max_images', 'image_start_number',
    'image_count', 'batch_size_for_doc', 'retry_mode', 'retry_image_list'
]
```

**New Structure:**
- Add `mode` field (or auto-detect)
- Add `local` section (for LOCAL mode)
- Add `googlecloud` section (for GOOGLECLOUD mode)
- Keep shared fields at root level

### 4. Main Function Refactoring

**Current Flow:**
1. Authenticate (OAuth2)
2. Init services (Drive, Docs, Vertex AI)
3. List images (Drive API)
4. Process in batches (download → transcribe → write to doc)

**New Flow:**
1. Detect mode from config
2. Validate config for mode
3. Create mode-specific handlers via factory
4. List images (via strategy)
5. Process images (via strategies)
6. Write output (via strategy)

---

## Key Dependencies

### External Libraries
- `google-cloud-aiplatform` - Vertex AI (GOOGLECLOUD mode)
- `google-api-python-client` - Drive & Docs APIs (GOOGLECLOUD mode)
- `google-auth-*` - Authentication (GOOGLECLOUD mode)
- `google-genai` - Can be used for both modes (Vertex AI + Developer API)
- `Pillow` - Image processing
- `pyyaml` - Configuration
- `python-dotenv` - Environment variables

### New Dependencies Needed
- `google-generativeai` OR use `google-genai` for Developer API (LOCAL mode)
- `pytest`, `pytest-cov`, `pytest-mock` - Testing (already planned)

---

## Risk Areas

### 1. Breaking Changes
- **Risk:** Refactoring may break existing Google Cloud workflows
- **Mitigation:** Keep existing functions as wrappers, comprehensive testing

### 2. API Differences
- **Risk:** Gemini Developer API may differ from Vertex AI
- **Mitigation:** Abstract differences in strategy classes, test early

### 3. Configuration Migration
- **Risk:** Existing configs may not work
- **Mitigation:** Auto-detect mode, normalize legacy configs

### 4. Error Handling
- **Risk:** Error handling logic is complex and mode-specific
- **Mitigation:** Preserve existing error handling, extend for local mode

---

## Code Statistics

- **Total Lines:** ~2549
- **Functions:** 21
- **Classes:** 0 (all procedural)
- **Mode-Specific Code:** ~60% (authentication, services, Drive/Docs operations)
- **Shared Code:** ~40% (image processing, transcription logic, utilities)

---

## Next Steps

1. ✅ Phase 0: Preparation & Setup (in progress)
2. ⏭️ Phase 1: Configuration & Mode Detection
3. ⏭️ Phase 2: Strategy Interfaces & Base Classes
4. ⏭️ Phase 3: LOCAL Mode Implementation
5. ⏭️ Phase 4: GOOGLECLOUD Mode Refactoring
6. ⏭️ Phase 5: Main Function Refactoring

---

**Document Version:** 1.0  
**Last Updated:** January 2025
