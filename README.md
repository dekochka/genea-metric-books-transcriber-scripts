# Genea Google Cloud Gemini Transcriber

This script extracts and transcribes text from JPEG files containing 18th-century birth records stored in a Google Drive folder. It uses Google Vertex AI/Gemini 2.5 Pro for transcription and organizes the results into Google Docs.

## Prerequisites

1. Python 3.7 or higher
2. Google Cloud Project with Vertex AI API enabled
3. Authentication setup (choose one method):

### Method 1: Service Account (Recommended for Production)
1. Go to Google Cloud Console > IAM & Admin > Service Accounts
2. Create a new service account
3. Grant the following roles:
   - Google Drive API > Drive File Viewer
   - Google Docs API > Docs Editor
   - Vertex AI > Vertex AI User
4. Create and download a JSON key file
5. Save it as `application_default_credentials.json` in the script directory

### Method 2: OAuth Client (Alternative for Testing)
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Create OAuth 2.0 Client ID
3. Add test users (your Google account)
4. Download client secret JSON
5. Save it as `client_secret.json` in the script directory
6. On first run, the script will open a browser for authentication

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set your Google Drive folder ID in the script:
```python
DRIVE_FOLDER_ID = "your_folder_id_here"
```

2. (Optional) Adjust other constants:
```python
TEST_MODE = False  # Set to True for testing with fewer images
TEST_IMAGE_COUNT = 2  # Number of images to process in test mode
MAX_IMAGES = 200  # Maximum number of images to process
```

## Usage

1. Run the script:
```bash
python transcribe_birth_records.py
```

2. The script will:
   - List all JPEG files in the specified folder
   - Download each image
   - Send it to Vertex AI for transcription
   - Create Google Docs with the transcriptions (50 images per doc)
   - Save the docs in the same folder

## Output

- Documents are named with page ranges (e.g., "pg001-050")
- Each document contains:
  - Image filenames as headings
  - Source links to original images
  - Transcribed text
  - Error messages (if any)

## Troubleshooting

1. Authentication Issues:
   - For Service Account: Ensure the JSON key file is properly downloaded and placed in the script directory
   - For OAuth: Check that your account is added as a test user and the client secret is properly configured

2. API Errors:
   - Verify that all required APIs are enabled in your Google Cloud Project
   - Check that your account/service account has the necessary permissions

3. Rate Limits:
   - The script includes built-in rate limiting and batching
   - If you hit rate limits, try reducing the batch size or adding delays

## Notes

- The script processes images in batches of 50 to stay within API limits
- Test mode is available for quick verification of functionality
- All operations are logged for debugging purposes
- Source links are preserved for reference 