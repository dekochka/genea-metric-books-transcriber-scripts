# Wizard Mode Quick Start Guide

This guide will help you get started with the interactive wizard mode for configuring transcription projects.

## What is Wizard Mode?

Wizard mode is an interactive configuration tool that guides you through setting up a transcription project step-by-step. It eliminates the need to manually edit YAML configuration files and helps prevent common configuration errors.

### Key Benefits

- ✅ **No YAML editing required** - Interactive prompts guide you through all settings
- ✅ **Title page extraction** - Automatically extracts context from title page images using AI
- ✅ **Pre-flight validation** - Catches errors before processing starts
- ✅ **Context separation** - Keeps prompt templates static while storing project-specific context
- ✅ **Backward compatible** - Generated configs work with existing workflow

## Prerequisites

1. Python 3.10+ installed
2. Dependencies installed: `pip install -r requirements.txt`
3. Gemini API key (for LOCAL mode) - Get from [Google AI Studio](https://aistudio.google.com/api-keys)

## Quick Start

### Step 1: Run the Wizard

Wizard mode is enabled by default. Simply run:

```bash
python3 transcribe.py
```

**Note:** If you want to use a config file instead (traditional mode), provide the config file path:

```bash
python3 transcribe.py config/my-config.yaml
```

To explicitly disable wizard mode and require a config file:

```bash
python3 transcribe.py --wizard-off config/my-config.yaml
```

### Step 2: Follow the Interactive Prompts

The wizard will guide you through three main steps:

#### Step 1: Mode Selection
- Choose processing mode (LOCAL or GOOGLECLOUD)
- Select image directory or Drive folder
- Enter API key (or use environment variable)
- Choose OCR model

#### Step 2: Context Collection
- Optionally extract context from title page image
- Review and edit extracted information
- Or manually enter context (villages, surnames, archive reference)

#### Step 3: Processing Settings
- Select prompt template
- Configure image range (start number and count)
- Set batch size (GOOGLECLOUD mode only)

### Step 3: Review and Validate

The wizard automatically:
- Validates your configuration
- Checks API keys, paths, and templates
- Verifies image availability
- Shows any errors or warnings

### Step 4: Use Your Config

After the wizard generates your config file, use it normally:

```bash
python3 transcribe.py config/my-project.yaml
```

## Detailed Walkthrough

### Mode Selection

**For LOCAL Mode:**
```
? Select processing mode: Local (process images from local folder)
? Enter path to directory containing images: data_samples/test_input_sample
? Use GEMINI_API_KEY environment variable? No
Get your API key from: https://aistudio.google.com/api-keys
? Enter Gemini API key: [your-api-key]
? Enter output directory for logs: logs
? Select OCR model: gemini-3-flash-preview (recommended)
```

**For GOOGLECLOUD Mode:**
```
? Select processing mode: Google Cloud (process images from Google Drive)
? Enter Google Drive folder ID: [folder-id]
? Enter path to ADC file: application_default_credentials.json
? Enter output directory for logs: logs
? Select OCR model: gemini-3-flash-preview (recommended)
```

### Context Collection

#### Option A: Extract from Title Page (Recommended)

If you have a title page image, the wizard can extract context automatically:

```
? Do you want to extract context from a title page image? Yes
? Select title page image: cover-title-page.jpg

[Extracting context from title page...]

Extracted Context from Title Page:
  Archive Reference: Ф. 487, оп. 1, спр. 526 (545)
  Document Type: Метрична книга про народження
  Date Range: 1888 (липень - грудень) - 1924 (січень - квітень)
  Main Villages: Турильче (Turylcze)
  Common Surnames: Rohaczuk, Didyk, Babij, Paszczuk

? What would you like to do?
  ❯ Accept all extracted data
    Edit extracted data
    Reject and enter manually
```

**Review and Edit:**
If you choose to edit, you can modify any field:
- Archive reference
- Document type
- Date range
- Villages (add variants, additional villages)
- Surnames

#### Option B: Manual Entry

```
? Do you want to extract context from a title page image? No

Context Information Collection
Provide information about the document and villages.

? Enter archive reference: Ф. 487, оп. 1, спр. 545
? Enter document type: Birth records
? Enter date range: 1850-1900
? Enter main village name: Княжа
? Enter village name variants (comma-separated): Knyazha, Kniazha
? Add another main village? No
? Enter additional village name: Шубино
? Add another additional village? No
? Enter common surname: Іванов
? Add another surname? Yes
? Enter common surname: Петров
? Add another surname? No
```

### Processing Settings

```
Step 3: Processing Settings

? Select prompt template: metric-book-birth - Role
Auto-generated archive index: ф487оп1спр545
? Enter starting image number (default: 1): 1
? Enter number of images to process: 10
```

**Prompt Templates:**
The wizard lists available templates from `prompts/templates/`:
- `metric-book-birth` - For birth records
- `metric-book-marriage` - For marriage records (if available)
- `metric-book-death` - For death records (if available)

**Archive Index:**
Automatically generated from archive reference (e.g., "Ф. 487, оп. 1, спр. 545" → "ф487оп1спр545")

## Generated Configuration

The wizard generates a YAML configuration file with:

```yaml
mode: "local"

local:
  image_dir: "data_samples/test_input_sample"
  output_dir: "logs"
  api_key: "your-api-key"
  ocr_model_id: "gemini-3-flash-preview"

context:
  archive_reference: "Ф. 487, оп. 1, спр. 545"
  document_type: "Birth records"
  date_range: "1850-1900"
  main_villages:
    - name: "Княжа"
      variants: ["Knyazha"]
  common_surnames:
    - "Іванов"
    - "Петров"

prompt_template: "metric-book-birth"
archive_index: "ф487оп1спр545"
image_start_number: 1
image_count: 10
```

## Tips and Best Practices

1. **Use Title Page Extraction**: If you have a title page image, use the extraction feature - it's faster and more accurate than manual entry

2. **Review Extracted Data**: Always review AI-extracted context before accepting - verify archive references and village names

3. **Save Config Files**: Use descriptive names for config files (e.g., `knyazha-1894.yaml` instead of `my-project.yaml`)

4. **Edit Generated Configs**: You can manually edit wizard-generated configs if needed - they're standard YAML files

5. **Reuse Templates**: Once you have prompt templates set up, you can reuse them across multiple projects

6. **Test with Small Batches**: Start with `image_count: 3` to test your configuration before processing large batches

## Troubleshooting

### Wizard Fails to Start
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.10+)

### Title Page Extraction Fails
- Ensure image file exists and is readable
- Check API key is valid
- Try manual entry as fallback

### Validation Errors
- Review error messages carefully
- Fix issues (missing paths, invalid API keys, etc.)
- You can choose to continue despite warnings (not recommended)

### Generated Config Doesn't Work
- Check that all paths are correct
- Verify API key is valid
- Ensure prompt template exists in `prompts/templates/`
- Review validation output for specific errors

## Migration from Manual Configs

If you have existing manual configs, you can:

1. **Continue using them** - Old configs with `prompt_file` still work
2. **Convert to wizard format** - Run wizard and manually copy settings
3. **Hybrid approach** - Use wizard for new projects, keep old configs for existing ones

Both formats are fully supported and can coexist.

## Next Steps

After generating your config:
1. Review the generated YAML file
2. Test with a small batch (`image_count: 3`)
3. Verify output quality
4. Process full batch when satisfied

For more information, see:
- [Configuration Guide](CONFIGURATION.md) - Detailed configuration options
- [README](../README.md) - General usage and features
