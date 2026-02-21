# Architecture

**Analysis Date:** 2026-02-21

## Pattern Overview

**Overall:** Strategy Pattern with Factory Method

**Key Characteristics:**
- Dual-mode operation with strategy-based abstraction layers
- Configuration-driven behavior with runtime mode detection
- Monolithic main script with embedded classes (5587 lines)
- Plugin-style wizard subsystem for interactive configuration
- Separation of concerns through abstract interfaces

## Layers

**Entry Layer:**
- Purpose: Command-line parsing, wizard orchestration, and config loading
- Location: `transcribe.py` (lines 5435-5587, main entry)
- Contains: Argument parsing, wizard mode detection, main function invocation
- Depends on: Configuration layer, wizard module
- Used by: CLI invocation

**Configuration Layer:**
- Purpose: Load, normalize, validate, and detect mode from YAML config
- Location: `transcribe.py` (lines 54-300)
- Contains: `load_config()`, `detect_mode()`, `normalize_config()`, `validate_config()`, `load_prompt()`
- Depends on: Nothing (pure configuration logic)
- Used by: Entry layer, main processing flow

**Strategy Factory Layer:**
- Purpose: Create mode-specific handler instances based on configuration
- Location: `transcribe.py` (class `ModeFactory` at line 1857)
- Contains: `create_handlers()`, `_create_local_handlers()`, `_create_googlecloud_handlers()`
- Depends on: All strategy implementations
- Used by: Main function

**Strategy Implementation Layer:**
- Purpose: Define and implement pluggable behaviors for auth, image sources, AI clients, and output
- Location: `transcribe.py` (lines 454-1856)
- Contains: Strategy classes:
  - `AuthenticationStrategy` (line 454): `LocalAuthStrategy`, `GoogleCloudAuthStrategy`
  - `ImageSourceStrategy` (line 523): `LocalImageSource`, `DriveImageSource`
  - `AIClientStrategy` (line 946): `GeminiDevClient`, `VertexAIClient`
  - `OutputStrategy` (line 1258): `LogFileOutput`, `GoogleDocsOutput`, `MarkdownOutput`, `WordOutput`, `CompositeOutput`
- Depends on: External APIs (Google Drive, Docs, Gemini, Vertex AI)
- Used by: Processing orchestration layer

**Processing Orchestration Layer:**
- Purpose: Core business logic for batch processing, transcription, and output generation
- Location: `transcribe.py` (lines 4486-5171)
- Contains: `process_all_local()`, `process_batches_googlecloud()`, `main()`
- Depends on: Strategy layer, utility functions
- Used by: Entry layer

**Utility Layer:**
- Purpose: Helper functions for docs, images, metrics, logging
- Location: `transcribe.py` (lines 2323-4483)
- Contains: `list_images()`, `download_image()`, `transcribe_image()`, `create_doc()`, `write_to_doc()`, `calculate_metrics()`, `create_overview_section()`, etc.
- Depends on: Google APIs
- Used by: Strategy implementations, orchestration layer

**Wizard Subsystem:**
- Purpose: Interactive configuration wizard with step-based data collection
- Location: `wizard/` directory
- Contains:
  - `wizard_controller.py`: Main orchestrator
  - `steps/`: Step implementations (base, mode selection, context collection, processing settings)
  - `config_generator.py`: YAML config file generation
  - `prompt_assembler.py`: Template-based prompt assembly
  - `title_page_extractor.py`: AI-powered context extraction from images
  - `preflight_validator.py`: Pre-processing validation
  - `i18n.py`: Internationalization (English/Ukrainian)
- Depends on: Configuration layer, AI clients
- Used by: Entry layer (optional wizard mode)

## Data Flow

**Wizard Mode Flow (Default):**

1. Entry point parses args → detects wizard mode (no config file provided)
2. `WizardController` orchestrates step progression
3. `ModeSelectionStep` collects mode choice (LOCAL or GOOGLECLOUD) and credentials
4. `ContextCollectionStep` optionally extracts context from title page image using AI
5. `ProcessingSettingsStep` collects processing parameters (ranges, batching)
6. `ConfigGenerator` writes YAML config to disk
7. Flow continues to Normal Mode Flow with generated config

**Normal Mode Flow (Config File Provided):**

1. Entry point loads config from YAML file
2. Config layer detects mode and normalizes structure (legacy → nested)
3. Config layer validates required fields for detected mode
4. Logging setup based on mode and config
5. Prompt loading (legacy: file, wizard: template + context assembly)
6. `ModeFactory` creates strategy handlers based on mode
7. Processing orchestration:
   - **LOCAL mode**: `process_all_local()` → batch transcribe → write to local files (log, markdown, word)
   - **GOOGLECLOUD mode**: `process_batches_googlecloud()` → batch transcribe → incremental Google Doc updates
8. Output finalization with metrics and overview section

**Image Processing Flow (Both Modes):**

1. `ImageSourceStrategy.list_images()` → filtered, sorted image list
2. For each image:
   - Download/load image bytes
   - `AIClientStrategy.transcribe_with_retry()` → Gemini API call with retries
   - Parse response, extract text and metadata
3. Batch accumulation (configurable batch size)
4. `OutputStrategy.write_batch()` → write batch to output destination
5. Repeat until all images processed
6. `OutputStrategy.finalize()` → update overview section with metrics

**State Management:**
- Stateless strategies (recreated per session)
- Session state tracked in processing functions via local variables
- Config immutable after loading (passed as dict)
- Output strategies maintain state (doc_id, file handles) between initialize/write/finalize

## Key Abstractions

**AuthenticationStrategy:**
- Purpose: Abstract credential acquisition for different API modes
- Examples: `transcribe.py` (lines 454, 478, 501)
- Pattern: Strategy pattern with `authenticate()` method returning credentials

**ImageSourceStrategy:**
- Purpose: Abstract image listing and loading from different sources
- Examples: `transcribe.py` (lines 523, 566, 888)
- Pattern: Strategy pattern with `list_images()` and `load_image_bytes()` methods

**AIClientStrategy:**
- Purpose: Abstract AI model invocation for different Gemini APIs
- Examples: `transcribe.py` (lines 946, 965, 1238)
- Pattern: Strategy pattern with `transcribe_with_retry()` method encapsulating retries and error handling

**OutputStrategy:**
- Purpose: Abstract output destination (files, docs) with incremental writing
- Examples: `transcribe.py` (lines 1258, 1301, 1449, 1612, 1724)
- Pattern: Strategy pattern with lifecycle methods: `initialize()`, `write_batch()`, `finalize()`

**WizardStep:**
- Purpose: Abstract wizard step with validation
- Examples: `wizard/steps/base_step.py`, `wizard/steps/mode_selection_step.py`, `wizard/steps/context_collection_step.py`
- Pattern: Template method pattern with `run()` and `validate()` abstract methods

## Entry Points

**Main Script Entry:**
- Location: `transcribe.py` (line 5435, `if __name__ == '__main__'`)
- Triggers: CLI invocation (`python transcribe.py [config_file]`)
- Responsibilities: Parse args, detect wizard mode, orchestrate wizard or load config, invoke `main()`

**Wizard Mode Entry:**
- Location: `transcribe.py` (line 5478)
- Triggers: No config file provided, wizard mode enabled
- Responsibilities: Import wizard module, create controller, add steps, run wizard, pass generated config to main flow

**Recovery Script Entry:**
- Location: `recovery_script.py` (line 1)
- Triggers: Manual invocation for recovery scenarios
- Responsibilities: Rebuild Google Doc from AI response logs and processing logs

**Refresh Credentials Entry:**
- Location: `refresh_credentials.py` (line 1)
- Triggers: Manual invocation for OAuth token refresh
- Responsibilities: Refresh Google OAuth credentials

## Error Handling

**Strategy:** Multi-layered error handling with retries and fallback mechanisms

**Patterns:**
- **API Retry Logic**: Exponential backoff with increasing timeouts (60s → 120s → 300s) in AI client strategies
- **Graceful Degradation**: Continue processing remaining images on individual failures
- **Comprehensive Logging**: Dual logging (main log + AI response log) with full tracebacks
- **Resume Information**: Log failed image names for retry mode
- **Output Finalization**: Ensure finalize() called even on partial success (try/finally blocks)
- **Config Validation**: Validate configuration before processing starts
- **Preflight Checks**: Wizard mode validates paths, credentials, and API access before processing

## Cross-Cutting Concerns

**Logging:**
- Dual logger setup: main logger (`logging`) + AI response logger (`ai_responses`)
- Compact format: timestamp + line number only
- Separate log files per session with timestamp and identifier
- Mode-specific log location (output_dir for LOCAL, logs/ for GOOGLECLOUD)

**Validation:**
- Configuration validation at load time (`validate_config()`)
- Mode-specific validation (LOCAL vs GOOGLECLOUD required fields)
- Wizard preflight validation before processing (`PreflightValidator`)
- Input data validation in wizard steps

**Authentication:**
- Strategy-based: `LocalAuthStrategy` (API key), `GoogleCloudAuthStrategy` (OAuth/ADC)
- Credential caching (ADC file)
- Separate refresh script for OAuth token renewal

---

*Architecture analysis: 2026-02-21*
