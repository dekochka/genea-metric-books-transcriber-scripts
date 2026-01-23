# Configuration Guide

This guide provides detailed information about configuring the Genea Metric Books Transcriber for both LOCAL and GOOGLECLOUD modes.

## Table of Contents

- [Mode Selection](#mode-selection)
- [LOCAL Mode Configuration](#local-mode-configuration)
- [GOOGLECLOUD Mode Configuration](#googlecloud-mode-configuration)
- [Shared Configuration Options](#shared-configuration-options)
- [Environment Variables](#environment-variables)
- [Legacy Configuration Format](#legacy-configuration-format)
- [Configuration Examples](#configuration-examples)

## Mode Selection

The tool automatically detects the mode from your configuration, or you can explicitly set it:

```yaml
mode: "local"  # or "googlecloud"
```

**Auto-detection rules:**
- If `local` section is present → LOCAL mode
- If `googlecloud` section is present → GOOGLECLOUD mode
- If legacy flat format (e.g., `project_id`, `drive_folder_id`) → GOOGLECLOUD mode
- Default → GOOGLECLOUD mode (for backward compatibility)

## LOCAL Mode Configuration

LOCAL mode processes images from your local file system and outputs transcriptions to log files.

### Required Settings

```yaml
mode: "local"

local:
  # API key for Gemini Developer API
  # Can also be set via GEMINI_API_KEY environment variable (recommended)
  api_key: "your-api-key-here"
  
  # Local directory containing images to transcribe
  image_dir: "/path/to/your/images"
```

### Optional Settings

```yaml
local:
  # Output directory for log files (default: "logs")
  output_dir: "logs"
  
  # OCR Model ID (default: "gemini-1.5-pro")
  # Available models: "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"
  ocr_model_id: "gemini-1.5-pro"
```

### Security Best Practices

**Recommended**: Use environment variable for API key instead of storing it in the config file:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Then in your config file:
```yaml
local:
  api_key: "${GEMINI_API_KEY}"  # Will use environment variable
```

## GOOGLECLOUD Mode Configuration

GOOGLECLOUD mode processes images from Google Drive and outputs formatted transcriptions to Google Docs.

### Required Settings

```yaml
mode: "googlecloud"

googlecloud:
  # Google Cloud Project ID
  project_id: "your-project-id"
  
  # Google Drive folder ID containing images
  # Get from folder URL: https://drive.google.com/drive/folders/FOLDER_ID
  drive_folder_id: "your-folder-id"
  
  # Application Default Credentials file path
  adc_file: "application_default_credentials.json"
```

### Optional Settings

```yaml
googlecloud:
  # Vertex AI region (default: "global")
  # Options: "global", "us-central1", "us-east1", etc.
  region: "global"
  
  # OCR Model ID (default: "gemini-3-flash-preview")
  # Examples: "gemini-3-flash-preview", "gemini-2.5-pro", "gemini-1.5-pro"
  ocr_model_id: "gemini-3-flash-preview"
  
  # Document name (optional)
  # If not provided, will be fetched from Google Drive folder name
  document_name: "My Transcription Document"
  
  # Title page image filename (optional)
  # Image to insert under document header on first page
  title_page_filename: "title_page.jpg"
  
  # Batch size for Google Doc writing (default: 10)
  # Number of images to transcribe before writing to Google Doc
  batch_size_for_doc: 10
  
  # Maximum images to fetch from Drive (default: 1000)
  max_images: 1000
```

## Shared Configuration Options

These settings apply to both LOCAL and GOOGLECLOUD modes:

```yaml
# Prompt file (required)
# Path to prompt file in prompts/ folder (without full path)
prompt_file: "f487o1s545-Turilche.md"

# Archive index reference (optional)
# Format: ф[FOND]оп[OPIS]спр[DELO] or custom format
# Used for document headers and record links
archive_index: "ф487оп1спр545"

# Processing settings
image_start_number: 1      # Starting image number (from filename)
image_count: 100           # Number of images to process

# Retry mode
retry_mode: false          # Enable retry mode
retry_image_list: []       # List of image filenames to retry
```

### Processing Settings Explained

- **`image_start_number`**: The starting image number extracted from the filename (e.g., `1` for `image00001.jpg`, `101` for `image00101.jpg`)
- **`image_count`**: Number of consecutive images to process starting from `image_start_number`
- **`retry_mode`**: When `true`, only processes images listed in `retry_image_list`
- **`retry_image_list`**: List of specific image filenames to retry (e.g., `["image00005.jpg", "image00010.jpg"]`)

### Supported Filename Patterns

The tool supports multiple filename patterns:

- `image (N).jpg/jpeg` - e.g., `image (7).jpg`, `image (10).jpg`
- `imageNNNNN.jpg/jpeg` - e.g., `image00101.jpg`, `image00001.jpg`
- `NNNNN.jpg/jpeg` - e.g., `52.jpg`, `102.jpg`
- `image - YYYY-MM-DDTHHMMSS.mmm.jpg/jpeg` - e.g., `image - 2025-07-20T112914.366.jpg`
- `PREFIX_NNNNN.jpg/jpeg` - e.g., `004933159_00216.jpeg`

If no numeric/timestamp match is found, the script falls back to position-based selection.

## Environment Variables

### LOCAL Mode

- **`GEMINI_API_KEY`**: Gemini Developer API key (recommended over config file)

### GOOGLECLOUD Mode

- **`GOOGLE_APPLICATION_CREDENTIALS`**: Path to ADC file (alternative to `adc_file` in config)

## Legacy Configuration Format

The tool supports the legacy flat configuration format for backward compatibility:

```yaml
# Legacy format (still supported)
project_id: "your-project-id"
drive_folder_id: "your-folder-id"
adc_file: "application_default_credentials.json"
region: "global"
ocr_model_id: "gemini-3-flash-preview"
prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 100
batch_size_for_doc: 10
max_images: 1000
retry_mode: false
retry_image_list: []
```

The tool automatically converts legacy configs to the new nested format internally.

## Configuration Examples

### Minimal LOCAL Mode Config

```yaml
mode: "local"

local:
  api_key: "${GEMINI_API_KEY}"  # Use environment variable
  image_dir: "data_samples/test_input_sample"

prompt_file: "f487o1s545-Turilche.md"
image_start_number: 1
image_count: 10
```

### Full LOCAL Mode Config

```yaml
mode: "local"

local:
  api_key: "${GEMINI_API_KEY}"
  image_dir: "/Users/me/documents/genealogy/images"
  output_dir: "logs"
  ocr_model_id: "gemini-1.5-pro"

prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 50
retry_mode: false
retry_image_list: []
```

### Minimal GOOGLECLOUD Mode Config

```yaml
mode: "googlecloud"

googlecloud:
  project_id: "ukr-transcribe-genea"
  drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
  adc_file: "application_default_credentials.json"

prompt_file: "f487o1s545-Turilche.md"
image_start_number: 1
image_count: 100
```

### Full GOOGLECLOUD Mode Config

```yaml
mode: "googlecloud"

googlecloud:
  project_id: "ukr-transcribe-genea"
  drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
  region: "global"
  ocr_model_id: "gemini-3-flash-preview"
  adc_file: "application_default_credentials.json"
  document_name: "Turilche Birth Records 1894"
  title_page_filename: "cover-title-page.jpg"
  batch_size_for_doc: 10
  max_images: 1000

prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 120
retry_mode: false
retry_image_list: []
```

## Validation

The tool validates your configuration before processing:

- **LOCAL Mode**: Checks for API key, image directory existence, output directory writability
- **GOOGLECLOUD Mode**: Checks for project ID, Drive folder ID, ADC file existence, prompt file existence

Validation errors are reported with clear messages indicating what needs to be fixed.

## Best Practices

1. **Use environment variables** for sensitive data (API keys, credentials)
2. **Use absolute paths** for image directories to avoid confusion
3. **Test with small `image_count`** first (e.g., 3-5 images) before processing large batches
4. **Keep prompt files organized** in the `prompts/` folder with descriptive names
5. **Use descriptive config filenames** (e.g., `turilche-1894.yaml` instead of `config.yaml`)
6. **Document your archive_index format** for consistency across projects
