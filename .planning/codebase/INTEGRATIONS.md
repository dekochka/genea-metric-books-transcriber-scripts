# External Integrations

**Analysis Date:** 2026-02-21

## APIs & External Services

**Google Gemini AI (Two Integration Paths):**

1. **Gemini Developer API** (LOCAL mode)
   - SDK/Client: `google-genai` (genai.Client)
   - Auth: `GEMINI_API_KEY` environment variable or config file
   - Used for: OCR/vision processing of local images
   - Models: gemini-3-flash-preview (recommended), gemini-flash-latest, gemini-flash-lite-latest, gemini-3-pro-preview
   - Implementation: `transcribe.py` class `GeminiDevClient` (line 965)

2. **Vertex AI** (GOOGLECLOUD mode)
   - SDK/Client: `google-cloud-aiplatform` (vertexai.init + genai.Client)
   - Auth: Application Default Credentials (ADC) via gcloud or OAuth2
   - Used for: OCR/vision processing of Google Drive images
   - Models: Same model options as Developer API
   - Implementation: `transcribe.py` class `VertexAIClient` (line 1238)

**Google Drive API v3:**
- Service: Image source for GOOGLECLOUD mode
- SDK/Client: `google-api-python-client` (build("drive", "v3"))
- Auth: OAuth2 credentials via ADC file
- Used for: Fetching images from specified Drive folder
- Implementation: `transcribe.py` class `DriveImageSource` (line 888)
- Configuration: `drive_folder_id` in config.googlecloud section

**Google Docs API v1:**
- Service: Document output for GOOGLECLOUD mode
- SDK/Client: `google-api-python-client` (build("docs", "v1"))
- Auth: OAuth2 credentials via ADC file
- Used for: Creating and updating transcription documents
- Implementation: `transcribe.py` class `GoogleDocsOutput` (line 1449)

## Data Storage

**Databases:**
- None (stateless CLI application)

**File Storage:**
- Local filesystem only
- LOCAL mode: Reads from `image_dir` (configurable path)
- GOOGLECLOUD mode: Reads from Google Drive folder (via API)
- Output locations:
  - LOCAL: Logs to `logs/` directory, Markdown/Word to source `image_dir`
  - GOOGLECLOUD: Logs to `logs/` directory, transcriptions to Google Docs

**Caching:**
- None (no caching layer)

## Authentication & Identity

**Auth Provider:**
- Custom per mode

**LOCAL Mode Authentication:**
- Gemini Developer API key
- Source: Environment variable `GEMINI_API_KEY` or config file `local.api_key`
- Obtain from: https://aistudio.google.com/api-keys
- Implementation: `transcribe.py` class `LocalAuthStrategy` (line 478)

**GOOGLECLOUD Mode Authentication:**
- OAuth2 via Application Default Credentials (ADC)
- Source: ADC file path specified in `googlecloud.adc_file` config (default: `application_default_credentials.json`)
- Setup: `gcloud auth application-default login` or OAuth2 flow via `refresh_credentials.py`
- Credentials: `client_secret.json` (OAuth client credentials, not committed)
- Implementation: `transcribe.py` class `GoogleCloudAuthStrategy` (line 501)

## Monitoring & Observability

**Error Tracking:**
- None (no external error tracking service)

**Logs:**
- Local file-based logging with Python `logging` module
- Log directory: `logs/` (configurable in LOCAL mode via `output_dir`)
- Separate logs for:
  - Script execution (`{archive_index}_{timestamp}.log`)
  - AI responses (embedded in logs)
  - LOCAL mode: Session metadata in output files

## CI/CD & Deployment

**Hosting:**
- None (local CLI application)

**CI Pipeline:**
- None detected (no GitHub Actions, Jenkins, etc.)

**Version Control:**
- Git repository (GitHub: dekochka/genea-metric-books-transcriber-scripts per README)

## Environment Configuration

**Required env vars (LOCAL mode):**
- `GEMINI_API_KEY` - Gemini Developer API key (alternative to config file)

**Required env vars (GOOGLECLOUD mode):**
- None (uses ADC file instead)

**Configuration files:**
- `config/*.yaml` - Mode-specific configuration
- `application_default_credentials.json` - OAuth2 ADC file (GOOGLECLOUD mode, not committed)
- `client_secret.json` - OAuth client credentials (GOOGLECLOUD mode, not committed)
- `prompts/*.md` - Transcription prompt templates (committed, project-specific)

**Secrets location:**
- Environment variables for API keys (LOCAL mode)
- Local files for OAuth credentials (GOOGLECLOUD mode, gitignored)
- Files noted as present but never read: `.env*` (existence checked but not used)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Testing & Development Tools

**Test Framework:**
- pytest with pytest-mock and pytest-cov
- Test markers: unit, integration, local_mode, googlecloud_mode
- Configuration: `.pytest.ini`

**Interactive Wizard:**
- questionary - Interactive CLI prompts
- rich - Terminal formatting and panels
- Implementation: `wizard/` module with multi-step wizard controller

---

*Integration audit: 2026-02-21*
