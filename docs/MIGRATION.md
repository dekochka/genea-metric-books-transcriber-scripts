# Migration Guide: Legacy to Dual-Mode Configuration

This guide helps you migrate from the legacy flat configuration format to the new dual-mode configuration format.

## Overview

The tool now supports two operation modes:
- **LOCAL Mode**: Process images from local file system
- **GOOGLECLOUD Mode**: Process images from Google Drive (original functionality)

**Good News**: Your existing legacy configuration files will continue to work! The tool automatically detects and converts legacy configs to the new format internally. However, migrating to the new format gives you:
- Clearer configuration structure
- Better validation
- Access to LOCAL mode features
- Future-proof configuration

## Automatic Conversion

The tool automatically converts legacy configs when it detects them. You don't need to migrate immediately, but it's recommended for clarity and to access new features.

### How Auto-Detection Works

The tool detects legacy format when it sees:
- Flat structure with `project_id` and `drive_folder_id` at the top level
- No `mode` field or `local`/`googlecloud` sections

Legacy configs are automatically converted to GOOGLECLOUD mode internally.

## Migration Steps

### Step 1: Identify Your Current Config Format

**Legacy Format** (still works):
```yaml
project_id: "ukr-transcribe-genea"
drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
adc_file: "application_default_credentials.json"
region: "global"
ocr_model_id: "gemini-flash-latest"
prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 100
batch_size_for_doc: 10
max_images: 1000
retry_mode: false
retry_image_list: []
```

**New Format** (recommended):
```yaml
mode: "googlecloud"

googlecloud:
  project_id: "ukr-transcribe-genea"
  drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
  adc_file: "application_default_credentials.json"
  region: "global"
  ocr_model_id: "gemini-flash-latest"

prompt_file: "f487o1s545-Turilche.md"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 100
batch_size_for_doc: 10
max_images: 1000
retry_mode: false
retry_image_list: []
```

### Step 2: Choose Your Migration Path

#### Option A: Migrate to GOOGLECLOUD Mode (Keep Current Functionality)

If you want to keep using Google Drive and Google Docs:

1. **Copy your existing config**:
   ```bash
   cp config/my-legacy-config.yaml config/my-new-config.yaml
   ```

2. **Add mode declaration** at the top:
   ```yaml
   mode: "googlecloud"
   ```

3. **Group Google Cloud settings** under `googlecloud:` section:
   ```yaml
   googlecloud:
     project_id: "ukr-transcribe-genea"
     drive_folder_id: "1YHAeW5Yi8oeKqvQHHKHf8u0o_MpTKJPR"
     adc_file: "application_default_credentials.json"
     region: "global"
     ocr_model_id: "gemini-flash-latest"
     # Optional settings
     document_name: "My Document"
     title_page_filename: "cover.jpg"
     batch_size_for_doc: 10
     max_images: 1000
   ```

4. **Keep shared settings** at the top level:
   ```yaml
   prompt_file: "f487o1s545-Turilche.md"
   archive_index: "ф487оп1спр545"
   image_start_number: 1
   image_count: 100
   retry_mode: false
   retry_image_list: []
   ```

5. **Test your new config**:
   ```bash
   python3 transcribe.py config/my-new-config.yaml
   ```

#### Option B: Migrate to LOCAL Mode (Simpler Setup)

If you want to try the new LOCAL mode (no Google Cloud setup required):

1. **Get a Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

2. **Set environment variable**:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. **Create new LOCAL mode config**:
   ```yaml
   mode: "local"
   
   local:
     api_key: "${GEMINI_API_KEY}"  # Use environment variable
     image_dir: "/path/to/your/local/images"
     output_dir: "logs"
     ocr_model_id: "gemini-flash-latest"
   
   # Shared settings (same as before)
   prompt_file: "f487o1s545-Turilche.md"
   archive_index: "ф487оп1спр545"
   image_start_number: 1
   image_count: 100
   retry_mode: false
   retry_image_list: []
   ```

4. **Copy your images** to a local directory (if using LOCAL mode)

5. **Test your new config**:
   ```bash
   python3 transcribe.py config/my-local-config.yaml
   ```

### Step 3: Field Mapping Reference

#### Legacy → GOOGLECLOUD Mode

| Legacy Field | New Location | Notes |
|-------------|--------------|-------|
| `project_id` | `googlecloud.project_id` | Required |
| `drive_folder_id` | `googlecloud.drive_folder_id` | Required |
| `adc_file` | `googlecloud.adc_file` | Required |
| `region` | `googlecloud.region` | Optional (default: "global") |
| `ocr_model_id` | `googlecloud.ocr_model_id` | Optional (default: "gemini-flash-latest") |
| `document_name` | `googlecloud.document_name` | Optional |
| `title_page_filename` | `googlecloud.title_page_filename` | Optional |
| `batch_size_for_doc` | `googlecloud.batch_size_for_doc` | Optional (default: 10) |
| `max_images` | `googlecloud.max_images` | Optional (default: 1000) |
| `prompt_file` | `prompt_file` | Top level (shared) |
| `archive_index` | `archive_index` | Top level (shared) |
| `image_start_number` | `image_start_number` | Top level (shared) |
| `image_count` | `image_count` | Top level (shared) |
| `retry_mode` | `retry_mode` | Top level (shared) |
| `retry_image_list` | `retry_image_list` | Top level (shared) |

#### Legacy → LOCAL Mode

| Legacy Field | New Location | Notes |
|-------------|--------------|-------|
| `project_id` | ❌ Not used | LOCAL mode doesn't need GCP |
| `drive_folder_id` | ❌ Not used | Use `local.image_dir` instead |
| `adc_file` | ❌ Not used | Use `local.api_key` instead |
| `region` | ❌ Not used | Not applicable to LOCAL mode |
| `ocr_model_id` | `local.ocr_model_id` | Optional (default: "gemini-flash-latest") |
| `document_name` | ❌ Not used | LOCAL mode uses log files |
| `title_page_filename` | ❌ Not used | LOCAL mode uses log files |
| `batch_size_for_doc` | ❌ Not used | LOCAL mode doesn't batch |
| `max_images` | ❌ Not used | LOCAL mode processes all matching images |
| `prompt_file` | `prompt_file` | Top level (shared) |
| `archive_index` | `archive_index` | Top level (shared) |
| `image_start_number` | `image_start_number` | Top level (shared) |
| `image_count` | `image_count` | Top level (shared) |
| `retry_mode` | `retry_mode` | Top level (shared) |
| `retry_image_list` | `retry_image_list` | Top level (shared) |

## Common Migration Scenarios

### Scenario 1: Keep Using Google Drive (GOOGLECLOUD Mode)

**Before (Legacy)**:
```yaml
project_id: "my-project"
drive_folder_id: "abc123"
adc_file: "adc.json"
prompt_file: "my-prompt.md"
image_start_number: 1
image_count: 50
```

**After (New Format)**:
```yaml
mode: "googlecloud"

googlecloud:
  project_id: "my-project"
  drive_folder_id: "abc123"
  adc_file: "adc.json"

prompt_file: "my-prompt.md"
image_start_number: 1
image_count: 50
```

### Scenario 2: Switch to Local Processing (LOCAL Mode)

**Before (Legacy)**:
```yaml
project_id: "my-project"
drive_folder_id: "abc123"
adc_file: "adc.json"
prompt_file: "my-prompt.md"
image_start_number: 1
image_count: 50
```

**After (LOCAL Mode)**:
```yaml
mode: "local"

local:
  api_key: "${GEMINI_API_KEY}"
  image_dir: "/path/to/local/images"

prompt_file: "my-prompt.md"
image_start_number: 1
image_count: 50
```

**Changes needed**:
1. Get Gemini API key
2. Copy images from Google Drive to local directory
3. Update config to use LOCAL mode

## Troubleshooting Migration

### Issue: "Mode not detected" or "Invalid configuration"

**Solution**: Make sure you have either:
- `mode: "local"` or `mode: "googlecloud"` explicitly set, OR
- A `local:` or `googlecloud:` section in your config

### Issue: "Missing required field" errors

**Solution**: Check that all required fields are present:
- **LOCAL mode**: `local.api_key`, `local.image_dir`
- **GOOGLECLOUD mode**: `googlecloud.project_id`, `googlecloud.drive_folder_id`, `googlecloud.adc_file`

### Issue: Legacy config not working after update

**Solution**: The tool should still support legacy configs. If you're having issues:
1. Verify your config file syntax (YAML formatting)
2. Check that all required fields are present
3. Try explicitly setting `mode: "googlecloud"` if using legacy format

### Issue: Want to use both modes

**Solution**: Create separate config files:
- `config/local-projects.yaml` for LOCAL mode
- `config/googlecloud-projects.yaml` for GOOGLECLOUD mode

Run with the appropriate config file:
```bash
python3 transcribe.py config/local-projects.yaml
python3 transcribe.py config/googlecloud-projects.yaml
```

## Backward Compatibility

**Important**: Legacy configuration format is still fully supported. You don't need to migrate immediately. The tool will:
- Automatically detect legacy format
- Convert it internally to the new format
- Continue working as before

However, migrating gives you:
- ✅ Clearer configuration structure
- ✅ Better error messages
- ✅ Access to LOCAL mode
- ✅ Future-proof setup

## Need Help?

- Check the [Configuration Guide](CONFIGURATION.md) for detailed configuration options
- Review example configs in `config/` directory:
  - `config.local.example.yaml` - LOCAL mode example
  - `config.googlecloud.example.yaml` - GOOGLECLOUD mode example
  - `config.yaml.example` - Legacy format example (still supported)
