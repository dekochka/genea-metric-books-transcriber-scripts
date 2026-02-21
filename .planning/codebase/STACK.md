# Technology Stack

**Analysis Date:** 2026-02-21

## Languages

**Primary:**
- Python 3.12+ (3.14.2 detected) - Main application language for transcription processing and AI integration

## Runtime

**Environment:**
- Python 3.12+ (tested with 3.14.2)

**Package Manager:**
- pip with requirements.txt
- Lockfile: Not present (no requirements.lock or Pipfile.lock)
- Virtual environment recommended (venv)

## Frameworks

**Core:**
- No web framework (CLI application)
- google-genai >=0.8.0 - Gemini AI SDK for vision/OCR capabilities
- google-cloud-aiplatform >=1.36.0 - Vertex AI integration for enterprise mode

**Testing:**
- pytest (with pytest-mock, pytest-cov) - Unit and integration testing
- Test configuration in `.pytest.ini`

**Build/Dev:**
- Shell script `tests/setup_and_test.sh` for environment setup and test execution
- Virtual environment (venv) for dependency isolation

## Key Dependencies

**Critical:**
- google-genai >=0.8.0 - Primary AI client for LOCAL mode using Gemini Developer API
- google-cloud-aiplatform >=1.36.0 - Vertex AI client for GOOGLECLOUD mode
- google-api-python-client >=2.108.0 - Google Drive and Docs API access
- google-auth-oauthlib >=1.1.0 - OAuth2 authentication flow
- Pillow >=10.0.0 - Image processing and manipulation

**Infrastructure:**
- pyyaml >=6.0 - Configuration file parsing (YAML)
- python-dotenv >=1.0.0 - Environment variable management
- questionary >=1.10.0 - Interactive CLI wizard interface
- rich >=13.0.0 - Terminal UI formatting and progress display
- python-docx >=0.8.11 - Word document generation for LOCAL mode output

**Authentication:**
- google-auth-httplib2 >=0.1.1 - HTTP client for Google API authentication
- google-auth-oauthlib >=1.1.0 - OAuth2 flow management

## Configuration

**Environment:**
- YAML-based configuration files in `config/` directory
- Two example configs: `config.local.example.yaml` and `config.googlecloud.example.yaml`
- Environment variable support: `GEMINI_API_KEY` for LOCAL mode API authentication
- Wizard mode generates configuration interactively (default mode)

**Build:**
- No build configuration (interpreted Python)
- Testing config in `.pytest.ini`
- Requirements defined in `requirements.txt`

## Platform Requirements

**Development:**
- Python 3.12+ (3.10+ minimum per documentation)
- Virtual environment (venv) recommended
- Shell environment for test script execution
- Optional: gcloud CLI for GOOGLECLOUD mode ADC authentication

**Production:**
- CLI application (local execution)
- No deployment infrastructure required
- Two operational modes:
  - LOCAL: Processes local filesystem images using Gemini Developer API
  - GOOGLECLOUD: Processes Google Drive images using Vertex AI, outputs to Google Docs

---

*Stack analysis: 2026-02-21*
