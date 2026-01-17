#!/usr/bin/env python3
"""
Genealogical Record Transcription Tool

Transcribes handwritten birth, death, and marriage records from Google Drive images 
using Vertex AI Gemini 2.5 Pro and creates formatted Google Docs.

Key Features:
- Processes images from Google Drive folders with flexible naming patterns
- Uses external prompt files for different record types (see prompts/ folder)
- Comprehensive logging and error recovery
- Batch processing with configurable start/count parameters
- Test mode for development

Configuration:
- Requires a YAML config file (see config/config.yaml.example)
- Pass config file as mandatory argument: python transcribe.py config/your_config.yaml
- Configure image_start_number and image_count for selective processing
- Enable retry_mode to reprocess failed images

For detailed setup instructions, prerequisites, and troubleshooting, see README.md
"""

import io
import os
import sys
import argparse
import logging
import base64
import json
import traceback
import yaml
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
from google.genai import types

# ------------------------- CONFIGURATION LOADING -------------------------

def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        KeyError: If required configuration keys are missing
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
    
    # Validate required keys
    required_keys = [
        'prompt_file', 'project_id', 'drive_folder_id', 'folder_name',
        'archive_index', 'region', 'ocr_model_id', 'adc_file',
        'test_mode', 'test_image_count', 'max_images', 'image_start_number',
        'image_count', 'batch_size_for_doc', 'retry_mode', 'retry_image_list'
    ]
    
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise KeyError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    return config


def load_prompt_text(prompt_file: str) -> str:
    """
    Load prompt text from file in the prompts directory.
    
    Args:
        prompt_file: Name of the prompt file (without path)
        
    Returns:
        Prompt text as string, or fallback minimal prompt if file not found
    """
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_path = os.path.join(prompts_dir, prompt_file)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.warning(f"Failed to load prompt '{prompt_file}' from {prompt_path}: {e}. Falling back to minimal prompt.")
        return "Transcribe the content of this image as structured text."


def setup_logging(config: dict) -> tuple:
    """
    Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (log_filename, ai_log_filename, ai_logger)
    """
    # Create logs directory if it doesn't exist
    LOGS_DIR = "logs"
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Logging setup - create shorter log filename to avoid filesystem limits
    folder_name = config['folder_name']
    safe_folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_folder_name = safe_folder_name.replace(' ', '_')[:50]  # Limit to 50 chars
    log_filename = os.path.join(LOGS_DIR, f"transcription_{safe_folder_name}_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename)
        ]
    )
    
    # Set up separate logger for AI responses
    ai_logger = logging.getLogger('ai_responses')
    ai_logger.setLevel(logging.INFO)
    ai_log_filename = os.path.join(LOGS_DIR, f"{timestamp}-ai-responses.log")
    ai_handler = logging.FileHandler(ai_log_filename)
    ai_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    ai_logger.addHandler(ai_handler)
    ai_logger.propagate = False  # Prevent duplicate logging
    
    return log_filename, ai_log_filename, ai_logger


def authenticate(adc_file: str):
    """
    Load user credentials from ADC file with required OAuth2 scopes.
    
    Args:
        adc_file: Path to the ADC credentials file
        
    Returns:
        Credentials object
        
    Raises:
        SystemExit: If token is expired or revoked, with helpful error message
    """
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/cloud-platform"
    ]
    try:
        creds = Credentials.from_authorized_user_file(adc_file, scopes=scopes)
        
        # Check if credentials are expired and try to refresh if possible
        if creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully")
            except Exception as refresh_error:
                error_str = str(refresh_error).lower()
                if 'invalid_grant' in error_str or 'expired' in error_str or 'revoked' in error_str:
                    print("\n" + "="*70)
                    print("ERROR: Google Cloud authentication token has expired or been revoked")
                    print("="*70)
                    print("\nTo fix this, please refresh your Google Cloud credentials:")
                    print("\n  1. Verify your OAuth client configuration:")
                    print("     - Ensure client_secret.json belongs to the")
                    print("       correct Google Cloud project and Google account")
                    print("     - Check that the file matches the account you're authenticating with")
                    print("\n  2. Run the credential refresh script:")
                    print("     python refresh_credentials.py")
                    print("\n  3. Or use gcloud (if you have gcloud CLI installed):")
                    print("     gcloud auth application-default login --project=<PROJECT_ID> \\")
                    print("       --scopes=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform")
                    print("\n  4. After refreshing, run the transcription script again:")
                    print(f"     python transcribe.py <your_config.yaml>")
                    print("\n  For more details, see the 'Troubleshooting' section in README.md")
                    print("\n" + "="*70 + "\n")
                    logging.error(f"Google Cloud authentication failed: {str(refresh_error)}")
                    raise SystemExit(1)
                else:
                    raise
        
        logging.info(f"Credentials loaded with scopes: {scopes}")
        return creds
    except SystemExit:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if 'invalid_grant' in error_str or 'expired' in error_str or 'revoked' in error_str:
            print("\n" + "="*70)
            print("ERROR: Google Cloud authentication token has expired or been revoked")
            print("="*70)
            print("\nTo fix this, please refresh your Google Cloud credentials:")
            print("\n  1. Verify your OAuth client configuration:")
            print("     - Ensure client_secret.json belongs to the")
            print("       correct Google Cloud project and Google account")
            print("     - Check that the file matches the account you're authenticating with")
            print("\n  2. Run the credential refresh script:")
            print("     python refresh_credentials.py")
            print("\n  3. Or use gcloud (if you have gcloud CLI installed):")
            print("     gcloud auth application-default login --project=<PROJECT_ID> \\")
            print("       --scopes=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform")
            print("\n  4. After refreshing, run the transcription script again:")
            print(f"     python transcribe.py <your_config.yaml>")
            print("\n  For more details, see the 'Troubleshooting' section in README.md")
            print("\n" + "="*70 + "\n")
            logging.error(f"Google Cloud authentication failed: {str(e)}")
            raise SystemExit(1)
        else:
            # Re-raise other authentication errors
            logging.error(f"Authentication error: {str(e)}")
            raise


def init_services(creds, config: dict):
    """
    Initialize Google Cloud services.
    
    Args:
        creds: OAuth2 credentials
        config: Configuration dictionary
    """
    project_id = config['project_id']
    region = config['region']
    adc_file = config['adc_file']
    
    logging.info(f"Initializing Vertex AI for project {project_id}...")
    # Set env var for Vertex AI SDK
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = adc_file
    
    # Initialize Gemini client
    genai_client = genai.Client(
        vertexai=True,
        project=project_id,
        location=region,
        credentials=creds
    )
    logging.info(f"Gemini client initialized in {region} with project {project_id}")

    logging.info("Initializing Google Drive and Docs APIs...")
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
    # Configure httplib2 with longer timeout for Google Docs API (5 minutes for large documents)
    http_base = httplib2.Http(timeout=300)  # 5 minutes timeout
    # Create authorized http object from credentials
    http = AuthorizedHttp(creds, http=http_base)
    drive = build("drive", "v3", http=http)
    docs = build("docs", "v1", http=http)
    logging.info("Google Drive and Docs APIs initialized with 5-minute timeout.")
    return drive, docs, genai_client


def extract_image_number(filename):
    """
    Extract the numeric identifier from an image filename.
    Supports the same patterns as list_images().
    Returns the extracted number, or None if no number can be extracted.
    """
    import re
    
    # Helper: case-insensitive check for JPEG extension
    def has_jpeg_extension(fname: str) -> bool:
        lower = fname.lower()
        return lower.endswith('.jpg') or lower.endswith('.jpeg')
    
    # Regex pattern for timestamp format: image - YYYY-MM-DDTHHMMSS.mmm.jpg/jpeg
    timestamp_pattern = re.compile(r'^image - (\d{4}-\d{2}-\d{2}T\d{6}\.\d{3})\.(?:jpg|jpeg)$', re.IGNORECASE)
    
    # Regex pattern for IMG_YYYYMMDD_XXXX.jpg format (e.g., IMG_20250814_0036.jpg)
    img_date_pattern = re.compile(r'^IMG_\d{8}_(\d+)\.(?:jpg|jpeg)$', re.IGNORECASE)
    
    number = None
    
    # Check for timestamp pattern first
    timestamp_match = timestamp_pattern.match(filename)
    if timestamp_match:
        # For timestamp images, we can't extract a meaningful number
        return None
    
    # Check for IMG_YYYYMMDD_XXXX.jpg pattern
    img_date_match = img_date_pattern.match(filename)
    if img_date_match:
        try:
            return int(img_date_match.group(1))
        except ValueError:
            pass
    
    # Check if filename matches the pattern image (N).jpg/jpeg
    if filename.startswith('image (') and (filename.lower().endswith(').jpg') or filename.lower().endswith(').jpeg')):
        try:
            start_idx = filename.find('(') + 1
            end_idx = filename.find(')')
            number_str = filename[start_idx:end_idx]
            return int(number_str)
        except (ValueError, IndexError):
            pass
    
    # Check if filename matches the pattern imageXXXXX.jpg/jpeg
    if filename.startswith('image') and has_jpeg_extension(filename) and '(' not in filename and ' - ' not in filename and '_' not in filename:
        try:
            ext_len = 5 if filename.lower().endswith('.jpeg') else 4
            number_str = filename[5:-ext_len]
            return int(number_str)
        except ValueError:
            pass
    
    # Check if filename matches the pattern XXXXX.jpg/jpeg
    if has_jpeg_extension(filename) and not filename.startswith('image') and '_' not in filename:
        try:
            ext_len = 5 if filename.lower().endswith('.jpeg') else 4
            number_str = filename[:-ext_len]
            return int(number_str)
        except ValueError:
            pass
    
    # Check if filename matches the pattern PREFIX_XXXXX.jpg/jpeg (e.g., 004933159_00216.jpeg)
    if has_jpeg_extension(filename) and '_' in filename:
        try:
            ext_len = 5 if filename.lower().endswith('.jpeg') else 4
            base_no_ext = filename[:-ext_len]
            # Take numeric part after the last underscore
            underscore_idx = base_no_ext.rfind('_')
            if underscore_idx != -1:
                suffix = base_no_ext[underscore_idx + 1:]
                if suffix.isdigit():
                    return int(suffix)
        except Exception:
            pass
    
    return None


def list_images(drive_service, config: dict):
    """
    Get list of images from Google Drive folder, sorted by filename.
    Handles pagination to fetch up to max_images and filters based on image_start_number and image_count.
    Supports filename patterns: 
    - image (N).jpg where N is a number (e.g., image (7).jpg, image (10).jpg)
    - imageXXXXX.jpg where XXXXX is a 5-digit number (e.g., image00101.jpg)
    - XXXXX.jpg where XXXXX is a number (e.g., 52.jpg, 102.jpg)
    - XXXXXX_YYYYY.jpg where the number after underscore is used (e.g., 004933159_00216.jpeg)
    - IMG_YYYYMMDD_XXXX.jpg where XXXX is the image number (e.g., IMG_20250814_0036.jpg)
    - image - YYYY-MM-DDTHHMMSS.mmm.jpg (timestamp format, e.g., image - 2025-07-20T112914.366.jpg)
    Returns list of image metadata including id, name, and webViewLink.
    """
    import re
    from datetime import datetime
    
    drive_folder_id = config['drive_folder_id']
    folder_name = config['folder_name']
    max_images = config['max_images']
    retry_mode = config['retry_mode']
    retry_image_list = config['retry_image_list']
    image_start_number = config['image_start_number']
    image_count = config['image_count']
    
    query = (
        f"mimeType='image/jpeg' and '{drive_folder_id}' in parents and trashed=false"
    )
    
    all_images = []
    page_token = None
    
    # Fetch all images with pagination (up to max_images)
    while len(all_images) < max_images:
        try:
            # Add orderBy parameter to sort by name
            resp = drive_service.files().list(
                q=query,
                fields="nextPageToken,files(id,name,webViewLink)",
                orderBy="name",  # Sort by filename
                pageSize=100,  # Fetch 100 files per request
                pageToken=page_token
            ).execute()
            
            files = resp.get('files', [])
            if not files:
                break
                
            all_images.extend(files)
            page_token = resp.get('nextPageToken')
            
            if not page_token:
                break
                
        except Exception as e:
            error_str = str(e).lower()
            if 'invalid_grant' in error_str or 'expired' in error_str or 'revoked' in error_str:
                logging.error(f"Error fetching images from Google Drive: {str(e)}")
                project_id = config.get('project_id', '<PROJECT_ID>')
                print("\n" + "="*70)
                print("ERROR: Google Cloud authentication token has expired or been revoked")
                print("="*70)
                print("\nTo fix this, please refresh your Google Cloud credentials:")
                print("\n  1. Verify your OAuth client configuration:")
                print("     - Ensure client_secret.json belongs to the")
                print("       correct Google Cloud project and Google account")
                print("     - Check that the file matches the account you're authenticating with")
                print("\n  2. Run the credential refresh script:")
                print("     python refresh_credentials.py")
                print("\n  3. Or use gcloud (if you have gcloud CLI installed):")
                print(f"     gcloud auth application-default login --project={project_id} \\")
                print("       --scopes=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/cloud-platform")
                print("\n  4. After refreshing, run the transcription script again:")
                print(f"     python transcribe.py <your_config.yaml>")
                print("\n  For more details, see the 'Troubleshooting' section in README.md")
                print("\n" + "="*70 + "\n")
                # Return empty list so the script can exit gracefully
                return []
            else:
                logging.error(f"Error fetching images from Google Drive: {str(e)}")
                break
    
    # Limit to max_images
    all_images = all_images[:max_images]
    logging.info(f"Found {len(all_images)} total images in folder '{folder_name}' (sorted by filename)")
    
    # RETRY MODE: If enabled, filter for specific failed images only
    if retry_mode:
        logging.info(f"RETRY MODE ENABLED: Looking for {len(retry_image_list)} specific failed images")
        retry_images = []
        
        # Convert retry list to full image names (add "image - " prefix if needed)
        retry_full_names = []
        for retry_img in retry_image_list:
            if retry_img.startswith('image - '):
                retry_full_names.append(retry_img)
            else:
                retry_full_names.append(f"image - {retry_img}")
        
        # Find matching images
        for img in all_images:
            if img['name'] in retry_full_names:
                retry_images.append(img)
        
        logging.info(f"Found {len(retry_images)} retry images out of {len(retry_image_list)} requested")
        if retry_images:
            retry_filenames = [img['name'] for img in retry_images]
            logging.info(f"Retry images found: {retry_filenames}")
        else:
            logging.warning("No retry images found! Check the retry_image_list names in config.")
        
        return retry_images
    
    # NORMAL MODE: Separate images by pattern type
    numbered_images = []
    timestamp_images = []
    
    # Helper: case-insensitive check for JPEG extension
    def has_jpeg_extension(filename: str) -> bool:
        lower = filename.lower()
        return lower.endswith('.jpg') or lower.endswith('.jpeg')

    # Regex pattern for timestamp format: image - YYYY-MM-DDTHHMMSS.mmm.jpg/jpeg
    timestamp_pattern = re.compile(r'^image - (\d{4}-\d{2}-\d{2}T\d{6}\.\d{3})\.(?:jpg|jpeg)$', re.IGNORECASE)
    
    # Regex pattern for IMG_YYYYMMDD_XXXX.jpg format (e.g., IMG_20250814_0036.jpg)
    img_date_pattern = re.compile(r'^IMG_\d{8}_(\d+)\.(?:jpg|jpeg)$', re.IGNORECASE)
    
    for img in all_images:
        filename = img['name']
        number = None
        timestamp_match = None
        img_date_match = None
        
        # Check for timestamp pattern first
        timestamp_match = timestamp_pattern.match(filename)
        if timestamp_match:
            timestamp_images.append(img)
            continue
        
        # Check for IMG_YYYYMMDD_XXXX.jpg pattern (e.g., IMG_20250814_0036.jpg)
        img_date_match = img_date_pattern.match(filename)
        if img_date_match:
            try:
                number = int(img_date_match.group(1))
            except ValueError:
                continue
        
        # Check if filename matches the pattern image (N).jpg/jpeg
        if filename.startswith('image (') and (filename.lower().endswith(').jpg') or filename.lower().endswith(').jpeg')):
            try:
                # Extract the number from filename (e.g., "image (7).jpg" -> 7)
                start_idx = filename.find('(') + 1
                end_idx = filename.find(')')
                number_str = filename[start_idx:end_idx]
                number = int(number_str)
            except (ValueError, IndexError):
                continue
        
        # Check if filename matches the pattern imageXXXXX.jpg/jpeg
        elif filename.startswith('image') and has_jpeg_extension(filename) and '(' not in filename and ' - ' not in filename and '_' not in filename:
            try:
                # Extract the number from filename (e.g., "image00101.jpg" -> 101)
                ext_len = 5 if filename.lower().endswith('.jpeg') else 4
                number_str = filename[5:-ext_len]  # Remove "image" prefix and extension suffix
                number = int(number_str)
            except ValueError:
                continue
        
        # Check if filename matches the pattern XXXXX.jpg/jpeg (like 52.jpg, 102.jpg)
        elif has_jpeg_extension(filename) and not filename.startswith('image') and '_' not in filename:
            try:
                # Extract the number from filename (e.g., "52.jpg" -> 52, "102.jpg" -> 102)
                ext_len = 5 if filename.lower().endswith('.jpeg') else 4
                number_str = filename[:-ext_len]  # Remove extension suffix
                number = int(number_str)
            except ValueError:
                continue

        # Check if filename matches the pattern PREFIX_XXXXX.jpg/jpeg (e.g., 004933159_00216.jpeg)
        elif has_jpeg_extension(filename) and '_' in filename:
            try:
                ext_len = 5 if filename.lower().endswith('.jpeg') else 4
                base_no_ext = filename[:-ext_len]
                # Take numeric part after the last underscore
                underscore_idx = base_no_ext.rfind('_')
                if underscore_idx != -1:
                    suffix = base_no_ext[underscore_idx + 1:]
                    if suffix.isdigit():
                        number = int(suffix)
            except Exception:
                continue
        
        # If we found a valid number, check if it's in the desired range
        if number is not None:
            if image_start_number <= number < image_start_number + image_count:
                numbered_images.append(img)
    
    # Handle numbered images (existing logic)
    filtered_images = []
    
    if numbered_images:
        # Define expected filename patterns for logging
        start_filename_pattern1 = f"image ({image_start_number}).jpg"
        end_filename_pattern1 = f"image ({image_start_number + image_count - 1}).jpg"
        start_filename_pattern2 = f"image{image_start_number:05d}.jpg"
        end_filename_pattern2 = f"image{image_start_number + image_count - 1:05d}.jpg"
        start_filename_pattern3 = f"{image_start_number}.jpg"
        end_filename_pattern3 = f"{image_start_number + image_count - 1}.jpg"
        
        logging.info(f"Filtering numbered images from {start_filename_pattern1} to {end_filename_pattern1} OR {start_filename_pattern2} to {end_filename_pattern2} OR {start_filename_pattern3} to {end_filename_pattern3}")
        
        # Sort numbered images numerically by their extracted number
        def extract_number_for_sorting(img):
            filename = img['name']
            lower = filename.lower()
            if filename.startswith('image (') and (lower.endswith(').jpg') or lower.endswith(').jpeg')):
                # Extract number from "image (N).jpg" format
                start_idx = filename.find('(') + 1
                end_idx = filename.find(')')
                number_str = filename[start_idx:end_idx]
            elif filename.startswith('image') and has_jpeg_extension(filename) and '(' not in filename and ' - ' not in filename and '_' not in filename:
                # Extract number from "imageXXXXX.jpg" format
                ext_len = 5 if lower.endswith('.jpeg') else 4
                number_str = filename[5:-ext_len]  # Remove "image" prefix and extension suffix
            elif has_jpeg_extension(filename) and '_' in filename:
                # Extract number from "PREFIX_XXXXX.jpg/jpeg" format
                ext_len = 5 if lower.endswith('.jpeg') else 4
                base_no_ext = filename[:-ext_len]
                underscore_idx = base_no_ext.rfind('_')
                number_str = base_no_ext[underscore_idx + 1:]
            else:
                # Extract number from "XXXXX.jpg" format
                ext_len = 5 if lower.endswith('.jpeg') else 4
                number_str = filename[:-ext_len]  # Remove extension suffix
            return int(number_str)
        
        numbered_images.sort(key=extract_number_for_sorting)
        filtered_images.extend(numbered_images)
    
    # Handle timestamp images
    if timestamp_images:
        logging.info(f"Found {len(timestamp_images)} timestamp-based images")
        
        # Sort timestamp images chronologically
        def extract_timestamp_for_sorting(img):
            filename = img['name']
            match = timestamp_pattern.match(filename)
            if match:
                timestamp_str = match.group(1)
                # Parse timestamp: YYYY-MM-DDTHHMMSS.mmm -> datetime
                try:
                    # Convert format 2025-07-20T112914.366 to 2025-07-20T11:29:14.366
                    formatted_timestamp = f"{timestamp_str[:11]}{timestamp_str[11:13]}:{timestamp_str[13:15]}:{timestamp_str[15:]}"
                    return datetime.fromisoformat(formatted_timestamp)
                except ValueError:
                    return datetime.min
            return datetime.min
        
        timestamp_images.sort(key=extract_timestamp_for_sorting)
        
        # For timestamp images, treat image_start_number as the starting position (1-indexed)
        # and image_count as the number of images to process
        start_pos = max(1, image_start_number) - 1  # Convert to 0-indexed
        end_pos = min(len(timestamp_images), start_pos + image_count)
        
        selected_timestamp_images = timestamp_images[start_pos:end_pos]
        filtered_images.extend(selected_timestamp_images)
        
        if selected_timestamp_images:
            logging.info(f"Selected {len(selected_timestamp_images)} timestamp images from position {image_start_number} to {start_pos + len(selected_timestamp_images)}")
            filenames = [img['name'] for img in selected_timestamp_images]
            logging.info(f"Selected timestamp files: {filenames}")
    
    # Final sort of all filtered images
    if filtered_images:
        # Sort mixed list: numbered images by number, timestamp images by timestamp
        def mixed_sorting_key(img):
            filename = img['name']
            timestamp_match = timestamp_pattern.match(filename)
            
            if timestamp_match:
                # Timestamp image - sort by timestamp
                timestamp_str = timestamp_match.group(1)
                try:
                    formatted_timestamp = f"{timestamp_str[:11]}{timestamp_str[11:13]}:{timestamp_str[13:15]}:{timestamp_str[15:]}"
                    return (1, datetime.fromisoformat(formatted_timestamp))  # 1 to sort timestamp images after numbered
                except ValueError:
                    return (1, datetime.min)
            else:
                # Numbered image - sort by number
                lower = filename.lower()
                if filename.startswith('image (') and (lower.endswith(').jpg') or lower.endswith(').jpeg')):
                    start_idx = filename.find('(') + 1
                    end_idx = filename.find(')')
                    number_str = filename[start_idx:end_idx]
                elif filename.startswith('image') and has_jpeg_extension(filename) and '(' not in filename and ' - ' not in filename and '_' not in filename:
                    ext_len = 5 if lower.endswith('.jpeg') else 4
                    number_str = filename[5:-ext_len]
                elif has_jpeg_extension(filename) and '_' in filename:
                    ext_len = 5 if lower.endswith('.jpeg') else 4
                    base_no_ext = filename[:-ext_len]
                    underscore_idx = base_no_ext.rfind('_')
                    number_str = base_no_ext[underscore_idx + 1:]
                else:
                    ext_len = 5 if lower.endswith('.jpeg') else 4
                    number_str = filename[:-ext_len]
                try:
                    return (0, int(number_str))  # 0 to sort numbered images first
                except ValueError:
                    return (0, 0)
        
        filtered_images.sort(key=mixed_sorting_key)
    
    # If no images were selected by number/timestamp filters, fall back to position-based selection
    if not filtered_images and all_images and not retry_mode:
        # all_images are already sorted by name from the Drive API
        start_pos = max(1, image_start_number) - 1
        end_pos = min(len(all_images), start_pos + image_count)
        fallback_selected = all_images[start_pos:end_pos]
        if fallback_selected:
            logging.info(f"No numeric/timestamp matches; falling back to position selection: items {image_start_number} to {image_start_number + len(fallback_selected) - 1}")
            filtered_images = fallback_selected

    logging.info(f"Selected {len(filtered_images)} total images for processing")
    
    # Log the selected filenames for verification
    if filtered_images:
        filenames = [img['name'] for img in filtered_images]
        logging.info(f"Final selected files: {filenames}")
    
    return filtered_images


def download_image(drive_service, file_id, file_name, folder_name: str):
    import time
    download_start = time.time()
    logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading image '{file_name}' from folder '{folder_name}'")
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        chunk_count = 0
        while not done:
            status, done = downloader.next_chunk()
            chunk_count += 1
            if status:
                progress = int(status.progress() * 100)
                logging.debug(f"[{datetime.now().strftime('%H:%M:%S')}] Download progress for '{file_name}': {progress}%")
        fh.seek(0)
        img_bytes = fh.read()
        download_elapsed = time.time() - download_start
        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Image '{file_name}' downloaded successfully ({len(img_bytes)} bytes) in {download_elapsed:.1f}s ({chunk_count} chunks)")
        
        if download_elapsed > 30:
            logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Download took {download_elapsed:.1f}s (>30s) for '{file_name}' - possible network issues")
        
        return img_bytes
    except Exception as e:
        download_elapsed = time.time() - download_start
        error_type = type(e).__name__
        logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] Error downloading '{file_name}' after {download_elapsed:.1f}s: {error_type}: {str(e)}")
        logging.error(f"Full traceback:\n{traceback.format_exc()}")
        raise


def transcribe_image(genai_client, image_bytes, file_name, prompt_text: str, ocr_model_id: str):
    import signal
    import time
    
    function_start_time = time.time()
    logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Starting transcription for image '{file_name}' (size: {len(image_bytes)} bytes)")
    ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] === Starting transcription for {file_name} ===")
    
    # Create image part using base64 encoding
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )
    
            # Create content with instruction and image
    content = types.Content(
        role="user",
        parts=[
                    types.Part.from_text(text=prompt_text),
            image_part
        ]
    )
    
    # Configure generation parameters
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=0.8,
        seed=0,
        max_output_tokens=65535,
        # safety_settings=[
        #     types.SafetySetting(
        #         category="HARM_CATEGORY_HATE_SPEECH",
        #         threshold="OFF"
        #     ),
        #     types.SafetySetting(
        #         category="HARM_CATEGORY_DANGEROUS_CONTENT",
        #         threshold="OFF"
        #     ),
        #     types.SafetySetting(
        #         category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        #         threshold="OFF"
        #     ),
        #     types.SafetySetting(
        #         category="HARM_CATEGORY_HARASSMENT",
        #         threshold="OFF"
        #     )
        # ],
        system_instruction=[types.Part.from_text(text=prompt_text)],
        thinking_config=types.ThinkingConfig(
            thinking_budget=5000,
        ),
    )
    
    # Timeout handler
    def timeout_handler(signum, frame):
        elapsed = time.time() - function_start_time
        error_msg = f"Vertex AI API call timed out after {timeout_seconds/60:.1f} minutes (total elapsed: {elapsed:.1f}s) for {file_name}"
        logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
        ai_logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] TIMEOUT: {error_msg}")
        raise TimeoutError(error_msg)
    
    max_retries = 3
    retry_delay = 30  # seconds
    # Exponential backoff timeouts: 1 min, 2 min, 5 min
    timeout_seconds_list = [60, 120, 300]
    
    for attempt in range(max_retries):
        attempt_start_time = time.time()
        timeout_seconds = timeout_seconds_list[attempt]
        try:
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt + 1}/{max_retries} for image '{file_name}'")
            ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt + 1}/{max_retries} starting for {file_name}")
            
            # Set up timeout with exponential backoff (1 min, 2 min, 5 min)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout set to {timeout_seconds/60:.1f} minutes for '{file_name}'")
            
            api_call_start = time.time()
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Making API call to Vertex AI for '{file_name}'...")
            ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] API call initiated for {file_name}")
            
            # Generate content
            response = genai_client.models.generate_content(
                model=ocr_model_id,
                contents=[content],
                config=generate_content_config
            )
            
            # Cancel the timeout
            signal.alarm(0)
            
            api_call_elapsed = time.time() - api_call_start
            elapsed_time = time.time() - attempt_start_time
            total_elapsed = time.time() - function_start_time
            
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Vertex AI response received in {api_call_elapsed:.1f} seconds (attempt total: {elapsed_time:.1f}s, function total: {total_elapsed:.1f}s) for '{file_name}'")
            ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] API call completed in {api_call_elapsed:.1f}s for {file_name}")
            
            # Log warning if API call took unusually long
            if api_call_elapsed > 60:
                logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: API call took {api_call_elapsed:.1f} seconds (>60s) for '{file_name}' - possible throttling or network issues")
                ai_logger.warning(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Long API call duration ({api_call_elapsed:.1f}s) for {file_name}")
            
            text = response.text
            
            # Ensure text is not None
            if text is None:
                text = "[No response text received from Vertex AI]"
            
            # Log the full AI response to the AI responses log
            ai_logger.info(f"=== AI Response for {file_name} ===")
            ai_logger.info(f"Model: {ocr_model_id}")
            ai_logger.info(f"Request timestamp: {datetime.now().isoformat()}")
            ai_logger.info(f"Image size: {len(image_bytes)} bytes")
            ai_logger.info(f"Instruction length: {len(prompt_text)} characters")
            ai_logger.info(f"Response length: {len(text) if text else 0} characters")
            ai_logger.info(f"Processing time: {elapsed_time:.1f} seconds")
            
            # Log response metadata if available
            if hasattr(response, 'usage_metadata'):
                ai_logger.info(f"Usage metadata: {response.usage_metadata}")
            if hasattr(response, 'candidates') and response.candidates:
                ai_logger.info(f"Number of candidates: {len(response.candidates)}")
                if hasattr(response.candidates[0], 'finish_reason'):
                    ai_logger.info(f"Finish reason: {response.candidates[0].finish_reason}")
            
            ai_logger.info(f"Full response:\n{text}")
            ai_logger.info(f"=== End AI Response for {file_name} ===\n")
            
            # Log the first and last few lines of the response for troubleshooting
            if text:
                lines = text.split('\n')
                if len(lines) > 6:
                    first_lines = '\n'.join(lines[:3])
                    last_lines = '\n'.join(lines[-3:])
                    logging.info(f"First 3 lines of transcription for '{file_name}':\n{first_lines}\n...\nLast 3 lines:\n{last_lines}")
                else:
                    logging.info(f"Full transcription for '{file_name}':\n{text}")
            
            # Return text, timing, and usage metadata
            usage_metadata = None
            if hasattr(response, 'usage_metadata'):
                usage_metadata = response.usage_metadata
            
            function_total_elapsed = time.time() - function_start_time
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Transcription function completed for '{file_name}' in {function_total_elapsed:.1f}s total")
            ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Transcription completed successfully for {file_name} (total: {function_total_elapsed:.1f}s)")
            
            return text, elapsed_time, usage_metadata
            
        except (TimeoutError, ConnectionError, OSError) as e:
            # Cancel any pending timeout
            signal.alarm(0)
            
            attempt_elapsed = time.time() - attempt_start_time
            total_elapsed = time.time() - function_start_time
            error_type = type(e).__name__
            
            error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt + 1}/{max_retries} failed for '{file_name}' after {attempt_elapsed:.1f}s (total elapsed: {total_elapsed:.1f}s): {error_type}: {str(e)}"
            logging.warning(error_msg)
            ai_logger.warning(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt + 1} failed for {file_name}: {error_type}: {str(e)}")
            ai_logger.warning(f"Attempt elapsed time: {attempt_elapsed:.1f}s, Total function time: {total_elapsed:.1f}s")
            
            # Log full traceback for debugging
            logging.debug(f"Full traceback for {file_name}:\n{traceback.format_exc()}")
            ai_logger.debug(f"Traceback for {file_name}:\n{traceback.format_exc()}")
            
            if attempt < max_retries - 1:
                logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Retrying in {retry_delay} seconds... (exponential backoff)")
                ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Will retry in {retry_delay}s with exponential backoff")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Retry delay completed, starting next attempt...")
            else:
                error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] All {max_retries} attempts failed for '{file_name}' after {total_elapsed:.1f}s total: {error_type}: {str(e)}"
                ai_logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] === AI Error for {file_name} ===")
                ai_logger.error(f"Error type: {error_type}")
                ai_logger.error(f"Error message: {str(e)}")
                ai_logger.error(f"Total elapsed time: {total_elapsed:.1f}s")
                ai_logger.error(f"Full traceback:\n{traceback.format_exc()}")
                ai_logger.error(f"=== End AI Error for {file_name} ===\n")
                logging.error(error_msg)
                logging.error(f"Full traceback:\n{traceback.format_exc()}")
                # Return error text with None for timing and metadata
                return f"[Error during transcription: {str(e)}]", None, None
                
        except Exception as e:
            # Cancel any pending timeout
            signal.alarm(0)
            
            attempt_elapsed = time.time() - attempt_start_time
            total_elapsed = time.time() - function_start_time
            error_type = type(e).__name__
            
            error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Unexpected error in Vertex AI transcription for '{file_name}' after {attempt_elapsed:.1f}s (total elapsed: {total_elapsed:.1f}s): {error_type}: {str(e)}"
            ai_logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] === AI Error for {file_name} ===")
            ai_logger.error(f"Error type: {error_type}")
            ai_logger.error(f"Error message: {str(e)}")
            ai_logger.error(f"Attempt elapsed time: {attempt_elapsed:.1f}s, Total function time: {total_elapsed:.1f}s")
            ai_logger.error(f"Full traceback:\n{traceback.format_exc()}")
            ai_logger.error(f"=== End AI Error for {file_name} ===\n")
            logging.error(error_msg)
            logging.error(f"Full traceback:\n{traceback.format_exc()}")
            # Return error text with None for timing and metadata
            return f"[Error during transcription: {str(e)}]", None, None


def create_doc(docs_service, drive_service, title, config: dict):
    """Create a new Google Doc in the specified folder and return its ID."""
    drive_folder_id = config['drive_folder_id']
    folder_name = config['folder_name']
    
    try:
        # First create the document
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        
        # Then move it to the specified folder
        file = drive_service.files().update(
            fileId=doc_id,
            addParents=drive_folder_id,
            fields='id, parents'
        ).execute()
        
        logging.info(f"Created new Google Doc '{title}' in folder '{folder_name}' with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error creating Google Doc: {str(e)}")
        # Check if it's a permission error
        if 'insufficientFilePermissions' in str(e) or '403' in str(e):
            folder_name = config['folder_name']
            logging.warning(f"Insufficient permissions to add document to folder '{folder_name}'")
            logging.warning(f"Document was created but could not be moved to the target folder")
            logging.info(f"Returning None to trigger local save fallback")
            return None
        raise


def calculate_metrics(usage_metadata_list, timing_list):
    """
    Calculate metrics from usage metadata and timing data.
    Returns a dictionary with calculated metrics.
    """
    # Pricing rates (per 1M tokens) - estimated 2026 pricing for Gemini 3 Flash
    INPUT_RATE = 0.15  # $0.15 per 1M input tokens
    OUTPUT_RATE = 0.60  # $0.60 per 1M output tokens
    CACHED_RATE = 0.03  # $0.03 per 1M cached tokens
    
    total_time = sum(t for t in timing_list if t is not None)
    page_count = len([t for t in timing_list if t is not None])
    avg_time_per_page = total_time / page_count if page_count > 0 else 0
    
    total_input_tokens = 0
    total_output_tokens = 0
    total_cached_tokens = 0
    
    for usage_metadata in usage_metadata_list:
        if usage_metadata is None:
            continue
            
        # Extract prompt tokens (input) - this includes both text and image tokens
        if hasattr(usage_metadata, 'prompt_token_count') and usage_metadata.prompt_token_count:
            total_input_tokens += usage_metadata.prompt_token_count
        
        # Extract cached tokens (billed at lower rate)
        if hasattr(usage_metadata, 'cached_content_token_count') and usage_metadata.cached_content_token_count:
            total_cached_tokens += usage_metadata.cached_content_token_count
        
        # Extract candidate tokens (output) - this is the visible response
        if hasattr(usage_metadata, 'candidates_token_count') and usage_metadata.candidates_token_count:
            total_output_tokens += usage_metadata.candidates_token_count
        
        # Extract thoughts tokens (billed as output) - reasoning tokens
        if hasattr(usage_metadata, 'thoughts_token_count') and usage_metadata.thoughts_token_count:
            total_output_tokens += usage_metadata.thoughts_token_count
    
    # Calculate costs
    # Input tokens (excluding cached, which are billed separately)
    input_tokens_billed = total_input_tokens - total_cached_tokens if total_cached_tokens > 0 else total_input_tokens
    input_cost = (input_tokens_billed / 1_000_000) * INPUT_RATE
    output_cost = (total_output_tokens / 1_000_000) * OUTPUT_RATE
    cached_cost = (total_cached_tokens / 1_000_000) * CACHED_RATE
    estimated_cost_per_run = input_cost + output_cost + cached_cost
    estimated_cost_per_page = estimated_cost_per_run / page_count if page_count > 0 else 0
    
    return {
        'total_time': total_time,
        'avg_time_per_page': avg_time_per_page,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_cached_tokens': total_cached_tokens,
        'estimated_cost_per_run': estimated_cost_per_run,
        'estimated_cost_per_page': estimated_cost_per_page,
        'page_count': page_count
    }


def create_overview_section(pages, config: dict, prompt_text: str, metrics=None, start_time=None, end_time=None):
    """
    Create overview section content for the document.
    Returns tuple of (overview_content, formatting_info) where formatting_info is a dict with:
    - folder_link_info: (link_start_index, link_end_index, folder_url)
    - bold_labels: list of (start_index, end_index) for "Files Processed:", "Images with Errors:", "Metrics:", "Prompt Used:"
    - prompt_text_range: (start_index, end_index) for the prompt text
    - disclaimer_range: (start_index, end_index) for the disclaimer text (for yellow highlight)
    
    Args:
        pages: List of page dictionaries with 'name', 'webViewLink', 'text'
        config: Configuration dictionary
        prompt_text: The prompt text used for transcription
        metrics: Optional dictionary with calculated metrics (total_time, avg_time_per_page, etc.)
        start_time: Optional datetime object for when transcription started
        end_time: Optional datetime object for when transcription ended
    """
    drive_folder_id = config['drive_folder_id']
    folder_name = config['folder_name']
    archive_index = config['archive_index']
    ocr_model_id = config['ocr_model_id']
    prompt_file = config['prompt_file']
    
    # Get folder link from the first page
    folder_link = pages[0]['webViewLink'] if pages else ""
    # Extract folder ID from the link for a cleaner folder link
    if 'folders/' in folder_link:
        folder_id = folder_link.split('folders/')[1].split('/')[0]
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    else:
        # Use drive_folder_id to construct folder URL if webViewLink doesn't have folder info
        folder_url = f"https://drive.google.com/drive/folders/{drive_folder_id}"
    
    # Count successful and failed transcriptions
    successful_pages = [p for p in pages if p['text'] and not p['text'].startswith('[Error')]
    failed_pages = [p for p in pages if not p['text'] or p['text'].startswith('[Error')]
    
    # Get file range
    if pages:
        start_file = pages[0]['name']
        end_file = pages[-1]['name']
        file_count = len(pages)
    else:
        start_file = "N/A"
        end_file = "N/A"
        file_count = 0
    
    # Disclaimer text in 3 languages
    disclaimer_text = """Нейросеть допускает много неточностей в переводе имен и фамилий - использовать как приблизительный перевод рукописного текста и перепроверять с источником!

Нейромережа допускає багато неточностей у перекладі імен та прізвищ - використовувати як приблизний переклад рукописного тексту та перевіряти з джерелом!

The neural network makes many inaccuracies in translating names and surnames - use as an approximate translation of handwritten text and verify with the source!"""
    
    # Create overview content with disclaimer first, then folder name as link text
    overview_content = f"""TRANSCRIPTION RUN SUMMARY

{disclaimer_text}

Name: {folder_name}
Folder Link: {folder_name}
"""
    
    # Calculate folder link position (after "Folder Link: ")
    folder_link_start = overview_content.find("Folder Link: ") + len("Folder Link: ")
    folder_link_end = folder_link_start + len(folder_name)
    folder_link_info = (folder_link_start, folder_link_end, folder_url)
    
    # Add archive index if available
    if archive_index:
        overview_content += f"Archive Index: {archive_index}\n"
    
    # Add time start and time end
    if start_time:
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        overview_content += f"Time Start: {start_time_str}\n"
    if end_time:
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        overview_content += f"Time End: {end_time_str}\n"
    
    # Track positions for bold labels
    files_processed_label = "Files Processed:"
    images_errors_label = f"Images with Errors ({len(failed_pages)}):"
    metrics_label = "Metrics:"
    prompt_used_label = "Prompt Used:"
    
    overview_content += f"""Model: {ocr_model_id}
Prompt File: {prompt_file}

{files_processed_label}
Count: {file_count}
Start: {start_file}
End: {end_file}

{images_errors_label}
"""
    
    # Calculate positions for bold labels
    files_processed_start = overview_content.find(files_processed_label)
    files_processed_end = files_processed_start + len(files_processed_label)
    
    images_errors_start = overview_content.find(images_errors_label)
    images_errors_end = images_errors_start + len(images_errors_label)
    
    # Add failed images list
    if failed_pages:
        for page in failed_pages:
            overview_content += f"- {page['name']}\n"
    else:
        overview_content += "None\n"
    
    # Add metrics section
    if metrics:
        overview_content += f"""
{metrics_label}
Total Time: {metrics['total_time']:.1f} seconds
Average Time per Page (secs): {metrics['avg_time_per_page']:.2f}
Total Input Tokens Used: {metrics['total_input_tokens']:,}
Total Output Tokens Used: {metrics['total_output_tokens']:,}
Estimated Cost per Run: ${metrics['estimated_cost_per_run']:.6f}
Estimated Cost Per Page: ${metrics['estimated_cost_per_page']:.6f}
"""
    else:
        overview_content += f"""
{metrics_label}
Total Time: N/A
Average Time per Page (secs): N/A
Total Input Tokens Used: N/A
Total Output Tokens Used: N/A
Estimated Cost per Run: N/A
Estimated Cost Per Page: N/A
"""
    
    # Calculate metrics label position for bold formatting
    metrics_start = overview_content.find(metrics_label)
    metrics_end = metrics_start + len(metrics_label)
    
    # Calculate prompt text position
    prompt_used_start = overview_content.find(prompt_used_label)
    prompt_used_end = prompt_used_start + len(prompt_used_label)
    
    overview_content += f"""
{prompt_used_label}
{prompt_text}

{'='*50}

"""
    
    # Calculate prompt text range (after the label and newline)
    prompt_text_start = overview_content.find(prompt_used_label) + len(prompt_used_label) + 1  # +1 for newline
    prompt_text_end = prompt_text_start + len(prompt_text)
    
    # Recalculate disclaimer range (positions may have shifted)
    disclaimer_start = overview_content.find(disclaimer_text.split('\n')[0])
    disclaimer_end = disclaimer_start + len(disclaimer_text)
    
    formatting_info = {
        'folder_link_info': folder_link_info,
        'bold_labels': [
            (files_processed_start, files_processed_end),
            (images_errors_start, images_errors_end),
            (metrics_start, metrics_end),
            (prompt_used_start, prompt_used_end)
        ],
        'prompt_text_range': (prompt_text_start, prompt_text_end),
        'disclaimer_range': (disclaimer_start, disclaimer_end)
    }
    
    return overview_content, formatting_info


def update_overview_section(docs_service, doc_id, pages, config: dict, prompt_text: str, metrics=None, start_time=None, end_time=None):
    """
    Update the overview section in an existing document with final metrics.
    
    This function finds the overview section (between the header and first page transcription)
    and replaces it with updated content that includes final metrics from all batches.
    
    Args:
        docs_service: Google Docs API service
        doc_id: Document ID
        pages: List of all page dictionaries (from all batches)
        config: Configuration dictionary
        prompt_text: The prompt text used for transcription
        metrics: Final metrics dictionary with overall stats
        start_time: Start time of the transcription run
        end_time: End time of the transcription run
    """
    archive_index = config['archive_index']
    import time
    from googleapiclient.errors import HttpError
    
    max_retries = 3
    retry_delay = 30  # seconds
    # Exponential backoff timeouts: 1 min, 2 min, 5 min
    timeout_seconds_list = [60, 120, 300]
    
    for attempt in range(max_retries):
        attempt_start_time = time.time()
        try:
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt + 1}/{max_retries} to update overview section (timeout: {timeout_seconds_list[attempt]/60:.1f} min)...")
            
            # Get current document state
            doc = docs_service.documents().get(documentId=doc_id).execute()
            
            # Find the overview section
            # It's between the header (Heading 1) and the first page transcription (Heading 2 with archive index)
            content = doc['body']['content']
            
            # Find the end of the header (first Heading 1)
            header_end = None
            overview_start = None
            overview_end = None
            first_page_header_start = None
            
            for i, element in enumerate(content):
                if 'paragraph' in element:
                    para = element['paragraph']
                    if 'paragraphStyle' in para and para['paragraphStyle'].get('namedStyleType') == 'HEADING_1':
                        header_end = element['endIndex']
                    elif 'paragraphStyle' in para and para['paragraphStyle'].get('namedStyleType') == 'HEADING_2':
                        # Check if this is the first page header (contains archive index pattern)
                        if archive_index and archive_index in para.get('elements', [{}])[0].get('textRun', {}).get('content', ''):
                            first_page_header_start = element['startIndex']
                            break
            
            # If we found the header end and first page header start, the overview is between them
            if header_end and first_page_header_start:
                overview_start = header_end
                overview_end = first_page_header_start
            else:
                # Fallback: look for "TRANSCRIPTION RUN SUMMARY" text
                doc_text = ""
                for element in content:
                    if 'paragraph' in element:
                        for elem in element['paragraph'].get('elements', []):
                            if 'textRun' in elem:
                                doc_text += elem['textRun'].get('content', '')
                
                summary_pos = doc_text.find("TRANSCRIPTION RUN SUMMARY")
                if summary_pos >= 0:
                    # Find the start and end of the overview section
                    # It starts after the header and ends before the first page transcription
                    # We'll search for the first Heading 2 that's not "TRANSCRIPTION RUN SUMMARY"
                    for i, element in enumerate(content):
                        if 'paragraph' in element:
                            para = element['paragraph']
                            if 'paragraphStyle' in para:
                                style = para['paragraphStyle'].get('namedStyleType')
                                if style == 'HEADING_1':
                                    header_end = element['endIndex']
                                elif style == 'HEADING_2':
                                    # Check if this is not the summary heading
                                    text_content = ""
                                    for elem in para.get('elements', []):
                                        if 'textRun' in elem:
                                            text_content += elem['textRun'].get('content', '')
                                    if "TRANSCRIPTION RUN SUMMARY" not in text_content and archive_index:
                                        # This is likely the first page header
                                        first_page_header_start = element['startIndex']
                                        break
                    
                    if header_end and first_page_header_start:
                        overview_start = header_end
                        overview_end = first_page_header_start
            
            if not overview_start or not overview_end:
                logging.warning("Could not locate overview section boundaries. Skipping overview update.")
                return False
            
            # Prepare new overview content with final metrics
            overview_content, formatting_info = create_overview_section(pages, config, prompt_text, metrics, start_time, end_time)
            folder_link_info = formatting_info['folder_link_info']
            bold_labels = formatting_info['bold_labels']
            prompt_text_range = formatting_info['prompt_text_range']
            disclaimer_range = formatting_info.get('disclaimer_range', (0, 0))
            folder_link_start_offset, folder_link_end_offset, folder_url = folder_link_info
            
            # Calculate position of "TRANSCRIPTION RUN SUMMARY" heading
            summary_heading = "TRANSCRIPTION RUN SUMMARY"
            summary_heading_start = 0
            summary_heading_end = len(summary_heading)
            
            # Delete old overview and insert new one
            update_requests = [
            {
                'deleteContentRange': {
                    'range': {
                        'startIndex': overview_start,
                        'endIndex': overview_end
                    }
                }
            },
            {
                'insertText': {
                    'location': {'index': overview_start},
                    'text': overview_content
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': overview_start, 'endIndex': overview_start + len(overview_content)},
                    'paragraphStyle': {
                        'namedStyleType': 'NORMAL_TEXT',
                        'alignment': 'START'
                    },
                    'fields': 'namedStyleType,alignment'
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': overview_start + summary_heading_start, 'endIndex': overview_start + summary_heading_end + 1},
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2',
                        'alignment': 'START'
                    },
                    'fields': 'namedStyleType,alignment'
                }
            },
            {
                'updateTextStyle': {
                    'range': {'startIndex': overview_start + summary_heading_start, 'endIndex': overview_start + summary_heading_end},
                    'textStyle': {
                        'bold': False
                    },
                    'fields': 'bold'
                }
            }
            ]
            
            # Add disclaimer highlight (yellow background)
            if disclaimer_range[1] > disclaimer_range[0]:
                update_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': overview_start + disclaimer_range[0],
                            'endIndex': overview_start + disclaimer_range[1]
                        },
                        'textStyle': {
                            'backgroundColor': {
                                'color': {
                                    'rgbColor': {
                                        'red': 1.0,
                                        'green': 1.0,
                                        'blue': 0.0
                                    }
                                }
                            }
                        },
                        'fields': 'backgroundColor'
                    }
                })
            
            # Add folder link
            update_requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': overview_start + folder_link_start_offset,
                        'endIndex': overview_start + folder_link_end_offset
                    },
                    'textStyle': {
                        'link': {
                            'url': folder_url
                        }
                    },
                    'fields': 'link'
                }
            })
            
            # Add bold formatting for labels
            for label_start, label_end in bold_labels:
                update_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': overview_start + label_start,
                            'endIndex': overview_start + label_end
                        },
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
            
            # Format prompt text (6pt Roboto Mono Normal)
            if prompt_text_range[1] > prompt_text_range[0]:
                update_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': overview_start + prompt_text_range[0],
                            'endIndex': overview_start + prompt_text_range[1]
                        },
                        'textStyle': {
                            'fontSize': {
                                'magnitude': 6,
                                'unit': 'PT'
                            },
                            'weightedFontFamily': {
                                'fontFamily': 'Roboto Mono'
                            }
                        },
                        'fields': 'fontSize,weightedFontFamily'
                    }
                })
        
            # Execute update
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': update_requests}).execute()
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Overview section updated with final metrics successfully.")
            return True  # Success, exit retry loop
            
        except (TimeoutError, HttpError, ConnectionError, OSError) as e:
            attempt_elapsed = time.time() - attempt_start_time
            error_type = type(e).__name__
            error_msg = f"Attempt {attempt + 1}/{max_retries} failed to update overview section after {attempt_elapsed:.1f}s: {error_type}: {str(e)}"
            logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            
            if attempt < max_retries - 1:
                logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Retrying in {retry_delay} seconds... (exponential backoff)")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                # All retries exhausted
                logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] All {max_retries} attempts failed to update overview section: {error_type}: {str(e)}")
                logging.error(f"Full traceback:\n{traceback.format_exc()}")
                return False  # Give up after all retries
                
        except Exception as e:
            # Non-retryable error, log and return
            error_type = type(e).__name__
            logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] Error updating overview section: {error_type}: {str(e)}")
            logging.error(f"Full traceback:\n{traceback.format_exc()}")
            return False
    
    # If we get here, all retries failed
    return False


def add_record_links_to_text(text, archive_index, page_number, web_view_link):
    """
    Find lines starting with ### or #### (like "### Запись 1" or "#### Record 1") and append clickable archive reference.
    For example: "### Запись 1" becomes "### Запись 1 ф201оп4спр104стр22"
    or "#### Record 1" becomes "#### Record 1 ф201оп4спр104стр22"
    where the archive part is a hyperlink.
    
    Returns tuple of (modified_text, link_insertions) where link_insertions is a list of
    (start_index, end_index, url) tuples for creating links in Google Docs.
    """
    if not text or not archive_index or not web_view_link:
        return text, []
    
    import re
    
    lines = text.split('\n')
    modified_lines = []
    link_insertions = []
    current_pos = 0
    
    # Pattern to match ### or #### at start of line (with optional whitespace) followed by any text
    # Matches lines like "### Запись 1", "#### Record 1", "### Запис 1", etc.
    pattern = re.compile(r'^(#{3,4}\s+[^\n]+)', re.IGNORECASE)
    
    for line in lines:
        match = pattern.match(line)
        if match:
            # Found a record header line
            original_line = match.group(1)
            archive_ref = f"{archive_index}стр{page_number}"
            modified_line = f"{original_line} {archive_ref}"
            modified_lines.append(modified_line)
            
            # Calculate position for link insertion (the archive_ref part)
            link_start = current_pos + len(original_line) + 1  # +1 for the space
            link_end = link_start + len(archive_ref)
            link_insertions.append((link_start, link_end, web_view_link))
            
            current_pos += len(modified_line) + 1  # +1 for newline
        else:
            modified_lines.append(line)
            current_pos += len(line) + 1  # +1 for newline
    
    modified_text = '\n'.join(modified_lines)
    return modified_text, link_insertions


def save_transcription_locally(pages, doc_name, config: dict, prompt_text: str, logs_dir: str, metrics=None, start_time=None, end_time=None):
    """
    Save transcription to a local text file when Google Doc creation fails.
    """
    folder_name = config['folder_name']
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(logs_dir, "local_transcriptions")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename
        safe_doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_doc_name = safe_doc_name.replace(' ', '_')
        output_file = os.path.join(output_dir, f"{safe_doc_name}.txt")
        
        # Create overview content (for local files, we just need the text, not formatting info)
        overview_content, _ = create_overview_section(pages, config, prompt_text, metrics, start_time, end_time)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write document header
            run_date = datetime.now().strftime("%Y%m%d")
            document_header = f"{folder_name} {run_date}"
            f.write(document_header + "\n\n")
            
            # Write overview
            f.write(overview_content)
            f.write("\n" + "="*80 + "\n\n")
            
            # Write each page
            for page in pages:
                f.write(f"\n{'='*80}\n")
                f.write(f"FILE: {page['name']}\n")
                f.write(f"SOURCE: {page['webViewLink']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(page['text'] if page['text'] else "[No transcription available]")
                f.write("\n\n")
        
        logging.info(f"Transcription saved locally to: {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"Error saving transcription locally: {str(e)}")
        raise


def write_to_doc(docs_service, doc_id, pages, config: dict, prompt_text: str, start_idx=0, metrics=None, start_time=None, end_time=None, write_overview=True):
    """
    Write transcribed content to a Google Doc using Atomic Page Writes.
    Fetches the true document end index before every page write to prevent index drift errors.
    
    Formatting includes:
    - Overview section with metadata (if write_overview=True)
    - Archive reference + page number as Heading 2 (e.g., "ф201оп4спр104стр22")
    - Source image link
    - Raw Vertex AI output with clickable links on record headers
    
    Args:
        docs_service: Google Docs API service
        doc_id: Document ID
        pages: List of page dictionaries
        config: Configuration dictionary
        prompt_text: The prompt text used for transcription
        start_idx: Starting index in pages list (for incremental writes)
        metrics: Optional metrics dictionary
        start_time: Optional start time
        end_time: Optional end time
        write_overview: If True, write overview section and document header (default: True)
    """
    folder_name = config['folder_name']
    archive_index = config['archive_index']
    
    logging.info(f"Preparing document content for folder '{folder_name}'...")
    if archive_index:
        logging.info(f"Using archive index: {archive_index}")
    
    try:
        # Circuit breaker to prevent cascading failures
        MAX_CONSECUTIVE_FAILURES = 5
        consecutive_failures = 0
        
        # --- PHASE 1: Write Overview (if needed) ---
        if write_overview:
            # Fetch current doc state - start at beginning
            doc = docs_service.documents().get(documentId=doc_id).execute()
            idx = 1  # Start of document
            
            # Prepare Header
            run_date = datetime.now().strftime("%Y%m%d")
            document_header = f"{folder_name} {run_date}"
            
            # Insert Header
            header_requests = [
                {
                    'insertText': {
                        'location': {'index': idx},
                        'text': document_header + "\n\n"
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {'startIndex': idx, 'endIndex': idx + len(document_header) + 2},
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_1',
                            'alignment': 'START'
                        },
                        'fields': 'namedStyleType,alignment'
                    }
                }
            ]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': header_requests}).execute()
            logging.info(f"Document header added: {document_header}")
            
            # Refresh Index for Overview
            doc = docs_service.documents().get(documentId=doc_id).execute()
            # Google Docs content list includes a final EOF character, so endIndex - 1 is the actual end
            idx = doc['body']['content'][-1]['endIndex'] - 1
            
            # Prepare Overview Content
            overview_content, formatting_info = create_overview_section(pages, config, prompt_text, metrics, start_time, end_time)
            folder_link_info = formatting_info['folder_link_info']
            bold_labels = formatting_info['bold_labels']
            prompt_text_range = formatting_info['prompt_text_range']
            disclaimer_range = formatting_info.get('disclaimer_range', (0, 0))
            folder_link_start_offset, folder_link_end_offset, folder_url = folder_link_info
            
            # Calculate position of "TRANSCRIPTION RUN SUMMARY" heading
            summary_heading = "TRANSCRIPTION RUN SUMMARY"
            summary_heading_start = 0
            summary_heading_end = len(summary_heading)
            
            # Construct Overview Requests
            overview_requests = [
            {
                'insertText': {
                    'location': {'index': idx},
                    'text': overview_content
                }
            },
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': idx, 'endIndex': idx + len(overview_content)},
                    'paragraphStyle': {
                        'namedStyleType': 'NORMAL_TEXT',
                        'alignment': 'START'
                    },
                    'fields': 'namedStyleType,alignment'
                }
            },
            {
                'updateParagraphStyle': {
                        'range': {'startIndex': idx + summary_heading_start, 'endIndex': idx + summary_heading_end + 1},  # +1 for newline
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_2',
                            'alignment': 'START'
                        },
                        'fields': 'namedStyleType,alignment'
                    }
                },
                {
                    'updateTextStyle': {
                        'range': {'startIndex': idx + summary_heading_start, 'endIndex': idx + summary_heading_end},
                        'textStyle': {
                            'bold': False
                        },
                        'fields': 'bold'
                    }
                },
                {
                    'updateTextStyle': {
                        'range': {'startIndex': idx + folder_link_start_offset, 'endIndex': idx + folder_link_end_offset},
                        'textStyle': {
                            'link': {'url': folder_url},
                            'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                            'underline': True
                        },
                        'fields': 'link,foregroundColor,underline'
                    }
                }
            ]
            
            # Add bold formatting for labels
            for label_start, label_end in bold_labels:
                overview_requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': idx + label_start, 'endIndex': idx + label_end},
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
            
            # Add yellow highlight for disclaimer
            if disclaimer_range[1] > disclaimer_range[0]:
                disclaimer_start, disclaimer_end = disclaimer_range
                overview_requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': idx + disclaimer_start, 'endIndex': idx + disclaimer_end},
                        'textStyle': {
                            'backgroundColor': {
                                'color': {
                                    'rgbColor': {
                                        'red': 1.0,
                                        'green': 1.0,
                                        'blue': 0.0
                                    }
                                }
                            }
                        },
                        'fields': 'backgroundColor'
                    }
                })
            
            # Add formatting for prompt text (6pt Roboto Mono)
            prompt_text_start, prompt_text_end = prompt_text_range
            overview_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': idx + prompt_text_start, 'endIndex': idx + prompt_text_end},
                    'textStyle': {
                        'fontSize': {
                            'magnitude': 6.0,
                            'unit': 'PT'
                        },
                        'weightedFontFamily': {
                            'fontFamily': 'Roboto Mono',
                            'weight': 400  # Normal weight
                        }
                    },
                    'fields': 'fontSize,weightedFontFamily'
                }
            })
            
            # Execute Overview
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': overview_requests}).execute()
            consecutive_failures = 0  # Reset counter on success
            logging.info("Overview section added successfully.")
        
        # --- PHASE 2: Write Page Transcriptions (Atomic Writes - One by One) ---
        for i, item in enumerate(pages[start_idx:], start=start_idx + 1):
            try:
                # CRITICAL FIX: Get Fresh Index Before Every Page Write
                # This ensures our index is 100% accurate and prevents "Precondition check failed" errors
                doc = docs_service.documents().get(documentId=doc_id).execute()
                current_idx = doc['body']['content'][-1]['endIndex'] - 1
                
                page_requests = []
                
                # Prepare page data
                page_number = i
                if archive_index:
                    page_header = f"{archive_index}стр{page_number}"
                else:
                    page_header = item['name']
                
                link_text = f"Src Img Url: {item['name']}"
                
                # Build requests for this page atomically
                # 1. Insert Header
                page_requests.append({
                        'insertText': {
                        'location': {'index': current_idx},
                            'text': f"{page_header}\n"
                        }
                })
                page_requests.append({
                        'updateParagraphStyle': {
                        'range': {'startIndex': current_idx, 'endIndex': current_idx + len(page_header) + 1},
                            'paragraphStyle': {
                            'namedStyleType': 'HEADING_2',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                })
                current_idx += len(page_header) + 1
                
                # 2. Insert Image Link
                page_requests.append({
                        'insertText': {
                        'location': {'index': current_idx},
                            'text': link_text + "\n"
                        }
                })
                link_val_start = current_idx + len("Src Img Url: ")
                link_val_end = current_idx + len(link_text)
                page_requests.append({
                        'updateTextStyle': {
                        'range': {'startIndex': link_val_start, 'endIndex': link_val_end},
                            'textStyle': {
                                'link': {'url': item['webViewLink']},
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                                'underline': True
                            },
                            'fields': 'link,foregroundColor,underline'
                        }
                })
                current_idx += len(link_text) + 1
                
                # 3. Insert Transcription Body
                if item['text']:
                    modified_text, link_insertions = add_record_links_to_text(
                        item['text'], 
                        archive_index, 
                        page_number, 
                        item['webViewLink']
                    )
                    text_to_insert = modified_text + "\n\n"
                    body_start_idx = current_idx
                    
                    page_requests.append({
                        'insertText': {
                            'location': {'index': current_idx},
                            'text': text_to_insert
                        }
                    })
                    page_requests.append({
                        'updateParagraphStyle': {
                            'range': {'startIndex': current_idx, 'endIndex': current_idx + len(text_to_insert)},
                            'paragraphStyle': {
                                'namedStyleType': 'NORMAL_TEXT',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                    })
                    
                    # Apply links to ### record headers
                    for l_start, l_end, l_url in link_insertions:
                        abs_start = body_start_idx + l_start
                        abs_end = body_start_idx + l_end
                        page_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': abs_start, 'endIndex': abs_end},
                                'textStyle': {
                                    'link': {'url': l_url},
                                    'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                                    'underline': True
                                },
                                'fields': 'link,foregroundColor,underline'
                            }
                        })
                    
                # 4. Execute immediately for this page (Atomic Write)
                if page_requests:
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': page_requests}).execute()
                    consecutive_failures = 0  # Reset counter on success
                logging.info(f"Added transcription for '{item['name']}' to document (header: {page_header})")
                
            except Exception as e:
                consecutive_failures += 1
                logging.error(f"Error writing page {i} ('{item['name']}') to Doc: {str(e)}")
                logging.warning(f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")
                
                # Circuit breaker: stop if too many consecutive failures
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logging.error(f"Circuit breaker triggered: {consecutive_failures} consecutive failures")
                    logging.error(f"Stopping document write to prevent cascading errors")
                    logging.error(f"Successfully wrote {i - consecutive_failures} out of {len(pages)} pages")
                    logging.error(f"Use recovery_script.py with the AI response log to recover remaining pages")
                    raise Exception(f"Exceeded maximum consecutive failures ({MAX_CONSECUTIVE_FAILURES}). Document write stopped.")
                
                # Try to write an error marker to the doc so the user knows something is missing
                try:
                    doc = docs_service.documents().get(documentId=doc_id).execute()
                    err_idx = doc['body']['content'][-1]['endIndex'] - 1
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [{
                        'insertText': {
                            'location': {'index': err_idx},
                            'text': f"\n[ERROR WRITING CONTENT FOR {item['name']}: {str(e)}]\n\n"
                        }
                    }]}).execute()
                except Exception as error_write_error:
                    logging.error(f"Could not write error message to document: {error_write_error}")
                    # Continue to next page even if error marker fails
        
        logging.info("Google Doc updated successfully")
        
    except Exception as e:
        logging.error(f"Critical error in write_to_doc: {str(e)}")
        raise


def main(config: dict, prompt_text: str, ai_logger, logs_dir: str):
    """Main function to process images and create transcription document."""
    # Extract config values for easier access
    project_id = config['project_id']
    folder_name = config['folder_name']
    archive_index = config['archive_index']
    ocr_model_id = config['ocr_model_id']
    test_mode = config['test_mode']
    retry_mode = config['retry_mode']
    retry_image_list = config['retry_image_list']
    max_images = config['max_images']
    image_start_number = config['image_start_number']
    image_count = config['image_count']
    batch_size_for_doc = config['batch_size_for_doc']
    adc_file = config['adc_file']
    
    try:
        # Log session start
        ai_logger.info(f"=== Transcription Session Started ===")
        ai_logger.info(f"Session timestamp: {datetime.now().isoformat()}")
        ai_logger.info(f"Project ID: {project_id}")
        ai_logger.info(f"Folder: {folder_name}")
        ai_logger.info(f"Archive Index: {archive_index if archive_index else 'None'}")
        ai_logger.info(f"Model: {ocr_model_id}")
        ai_logger.info(f"Test mode: {test_mode}")
        ai_logger.info(f"Retry mode: {retry_mode}")
        if retry_mode:
            ai_logger.info(f"Retry images count: {len(retry_image_list)}")
            ai_logger.info(f"Retry images: {retry_image_list}")
        else:
            ai_logger.info(f"Max images: {max_images}")
            ai_logger.info(f"Image start number: {image_start_number}")
            ai_logger.info(f"Image count: {image_count}")
        ai_logger.info(f"Batch size for doc: {batch_size_for_doc}")
        ai_logger.info(f"=== Session Configuration ===\n")
        
        # Initialize services
        creds = authenticate(adc_file)
        drive_service, docs_service, genai_client = init_services(creds, config)

        images = list_images(drive_service, config)
        
        if not images:
            if retry_mode:
                logging.error(f"No retry images found in folder '{folder_name}' from the retry_image_list")
                ai_logger.error(f"No retry images found from list of {len(retry_image_list)} images")
            else:
                logging.error(f"No images found in folder '{folder_name}' for the specified range (start: {image_start_number}, count: {image_count})")
                ai_logger.error(f"No images found for range {image_start_number} to {image_start_number + image_count - 1}")
            return
        
        # Process images in batches for incremental document writing
        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Starting transcription of {len(images)} images in batches of {batch_size_for_doc}...")
        ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] === Starting batch transcription of {len(images)} images (batch size: {batch_size_for_doc}) ===")
        start_time = datetime.now()
        transcribed_pages = []
        usage_metadata_list = []
        timing_list = []
        last_image_end_time = None
        doc_id = None
        doc_name = None
        first_batch = True
        
        # Process images in batches
        total_images = len(images)
        num_batches = (total_images + batch_size_for_doc - 1) // batch_size_for_doc  # Ceiling division
        
        try:
            for batch_num in range(num_batches):
                batch_start_idx = batch_num * batch_size_for_doc
                batch_end_idx = min(batch_start_idx + batch_size_for_doc, total_images)
                batch_images = images[batch_start_idx:batch_end_idx]
                batch_size = len(batch_images)
                
                logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] === Processing batch {batch_num + 1}/{num_batches} (images {batch_start_idx + 1}-{batch_end_idx} of {total_images}) ===")
                ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] === Batch {batch_num + 1}/{num_batches}: Processing images {batch_start_idx + 1}-{batch_end_idx} ===")
                
                # Track batch-level transcribed pages and metrics
                batch_transcribed_pages = []
                batch_usage_metadata_list = []
                batch_timing_list = []
                
                for batch_idx, img in enumerate(batch_images, 1):
                    global_idx = batch_start_idx + batch_idx
                    image_start_time = datetime.now()
                    image_name = img['name']
                    
                    # Log gap detection
                    if last_image_end_time:
                        gap_seconds = (image_start_time - last_image_end_time).total_seconds()
                        if gap_seconds > 60:  # Log if gap is more than 1 minute
                            logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Large time gap detected: {gap_seconds:.1f} seconds ({gap_seconds/60:.1f} minutes) between previous image and '{image_name}'")
                            ai_logger.warning(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Time gap of {gap_seconds:.1f}s ({gap_seconds/60:.1f} min) before {image_name}")
                    
                    logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Processing image {global_idx}/{total_images} (batch {batch_num + 1}, item {batch_idx}/{batch_size}): '{image_name}'")
                    ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] === Processing image {global_idx}/{total_images}: {image_name} ===")
                    
                    try:
                        download_start = datetime.now()
                        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading image '{image_name}'...")
                        img_bytes = download_image(drive_service, img['id'], img['name'], folder_name)
                        download_elapsed = (datetime.now() - download_start).total_seconds()
                        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Image '{image_name}' downloaded in {download_elapsed:.1f}s, starting transcription...")
                        
                        transcription_start = datetime.now()
                        text, elapsed_time, usage_metadata = transcribe_image(genai_client, img_bytes, img['name'], prompt_text, ocr_model_id)
                        transcription_elapsed = (datetime.now() - transcription_start).total_seconds()
                        
                        # Ensure text is not None
                        if text is None:
                            text = "[No transcription text received]"
                        
                        batch_transcribed_pages.append({
                            'name': img['name'],
                            'webViewLink': img['webViewLink'],
                            'text': text
                        })
                        
                        # Collect metrics
                        batch_timing_list.append(elapsed_time)
                        batch_usage_metadata_list.append(usage_metadata)
                        
                        image_end_time = datetime.now()
                        image_total_elapsed = (image_end_time - image_start_time).total_seconds()
                        last_image_end_time = image_end_time
                        
                        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Successfully completed image {global_idx}/{total_images}: '{image_name}' (transcription: {transcription_elapsed:.1f}s, total: {image_total_elapsed:.1f}s)")
                        ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Completed {image_name} - Transcription: {transcription_elapsed:.1f}s, Total: {image_total_elapsed:.1f}s")
                        
                        # Log progress
                        progress_pct = (global_idx / total_images) * 100
                        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {global_idx}/{total_images} images ({progress_pct:.1f}%)")
                        
                    except Exception as e:
                        image_end_time = datetime.now()
                        image_total_elapsed = (image_end_time - image_start_time).total_seconds()
                        last_image_end_time = image_end_time
                        error_type = type(e).__name__
                        
                        # Calculate next image number to start from in case of failure
                        # Extract the number from the current image filename
                        current_image_number = extract_image_number(image_name)
                        if current_image_number is not None:
                            next_image_number = current_image_number + 1
                        else:
                            # Fallback: if we can't extract number, use position-based calculation
                            next_image_number = image_start_number + global_idx
                        
                        error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Error transcribing image {global_idx}/{total_images} '{image_name}' after {image_total_elapsed:.1f}s: {error_type}: {str(e)}"
                        logging.error(error_msg)
                        logging.error(f"Full traceback:\n{traceback.format_exc()}")
                        logging.error(f"RESUME INFO: To resume from this point, update config image_start_number = {next_image_number} (filename number from '{image_name}')")
                        ai_logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR processing {image_name}: {error_type}: {str(e)}")
                        ai_logger.error(f"RESUME INFO: Update config image_start_number = {next_image_number} to resume from next image (current image filename number: {current_image_number})")
                        ai_logger.error(f"Traceback:\n{traceback.format_exc()}")
                        
                # Add error message as text
                        batch_transcribed_pages.append({
                    'name': img['name'],
                    'webViewLink': img['webViewLink'],
                    'text': f"[Error during transcription: {str(e)}]"
                })
                        # Add None for metrics on error
                        batch_timing_list.append(None)
                        batch_usage_metadata_list.append(None)
                
                # After batch is transcribed, write to document
                if batch_transcribed_pages:
                    # Accumulate all transcribed pages and metrics
                    transcribed_pages.extend(batch_transcribed_pages)
                    usage_metadata_list.extend(batch_usage_metadata_list)
                    timing_list.extend(batch_timing_list)
                    
                    if first_batch:
                        # Create document after first batch
                        run_date = datetime.now().strftime("%Y%m%d")
                        doc_name = f"{folder_name} {run_date}"
                        
                        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] First batch completed ({len(batch_transcribed_pages)} images). Creating Google Doc '{doc_name}'...")
                        ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] First batch completed, creating document...")
                        
                        # Calculate metrics for overview (will be updated later)
                        batch_metrics = calculate_metrics(usage_metadata_list, timing_list) if usage_metadata_list else None
                        
                        # Try to create Google Doc
                        doc_id = create_doc(docs_service, drive_service, doc_name, config)
                        
                        if doc_id is None:
                            # Permission error - save locally instead
                            logging.warning("Cannot create Google Doc due to insufficient permissions")
                            logging.info("Saving transcription to local file instead...")
                            local_file = save_transcription_locally(transcribed_pages, doc_name, config, prompt_text, logs_dir, batch_metrics, start_time, None)
                            logging.info(f"✓ Transcription saved locally: {local_file}")
                            logging.info(f"✓ Processed {len(transcribed_pages)} images successfully")
                            # Continue processing but save locally for each batch
                            first_batch = False
                            continue
                        else:
                            # Write first batch with overview
                            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Writing first batch ({len(batch_transcribed_pages)} images) to document with overview...")
                            write_to_doc(docs_service, doc_id, transcribed_pages, config, prompt_text, start_idx=0, metrics=batch_metrics, start_time=start_time, end_time=None, write_overview=True)
                            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ First batch written to document")
                            first_batch = False
                    else:
                        # Append subsequent batches to existing document
                        if doc_id:
                            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Writing batch {batch_num + 1} ({len(batch_transcribed_pages)} images) to document...")
                            # Calculate start_idx for this batch (number of pages already written)
                            pages_written_so_far = len(transcribed_pages) - len(batch_transcribed_pages)
                            # Pass full transcribed_pages list with correct start_idx for proper page numbering
                            write_to_doc(docs_service, doc_id, transcribed_pages, config, prompt_text, start_idx=pages_written_so_far, metrics=None, start_time=None, end_time=None, write_overview=False)
                            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Batch {batch_num + 1} written to document")
                        else:
                            # Document creation failed earlier, save locally
                            logging.warning(f"Cannot write batch {batch_num + 1} to document (doc creation failed). Saving locally...")
                            # Append to local file if it exists, or create new one
                            run_date = datetime.now().strftime("%Y%m%d")
                            doc_name = f"{folder_name} {run_date}"
                            save_transcription_locally(batch_transcribed_pages, doc_name, config, prompt_text, logs_dir, None, None, None)
        
        except Exception as batch_error:
            # Log error and resume information
            error_type = type(batch_error).__name__
            images_processed = len(transcribed_pages) if 'transcribed_pages' in locals() else 0
            
            # Calculate next image number from the last successfully processed image
            next_image_number = None
            if images_processed > 0 and 'transcribed_pages' in locals():
                last_image_name = transcribed_pages[-1]['name']
                last_image_number = extract_image_number(last_image_name)
                if last_image_number is not None:
                    next_image_number = last_image_number + 1
                else:
                    # Fallback: use position-based calculation
                    next_image_number = image_start_number + images_processed
            elif images_processed > 0:
                # Fallback if we can't get the last image name
                next_image_number = image_start_number + images_processed
            
            logging.error(f"[{datetime.now().strftime('%H:%M:%S')}] Error processing batch: {error_type}: {str(batch_error)}")
            logging.error(f"RESUME INFO: Processed {images_processed} images successfully before error")
            if next_image_number is not None:
                last_image_info = f" (last processed: {transcribed_pages[-1]['name'] if images_processed > 0 and 'transcribed_pages' in locals() else 'unknown'})"
                logging.error(f"RESUME INFO: To resume from this point, update config image_start_number = {next_image_number}{last_image_info}")
            logging.error(f"Full traceback:\n{traceback.format_exc()}")
            
            ai_logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] === Batch Processing Error ===")
            ai_logger.error(f"Error type: {error_type}")
            ai_logger.error(f"Error message: {str(batch_error)}")
            ai_logger.error(f"Images processed before error: {images_processed}")
            if next_image_number is not None:
                ai_logger.error(f"RESUME INFO: Update config image_start_number = {next_image_number} to resume from next image")
            ai_logger.error(f"Full traceback:\n{traceback.format_exc()}")
            ai_logger.error(f"=== End Batch Processing Error ===")
            
            # Re-raise to be caught by outer exception handler
            raise
        
        # Record end time
        end_time = datetime.now()
        batch_total_elapsed = (end_time - start_time).total_seconds()
        
        logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Completed all batches: {len(transcribed_pages)} images processed in {batch_total_elapsed:.1f} seconds ({batch_total_elapsed/60:.1f} minutes)")
        ai_logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] === All batches transcription completed ===")
        ai_logger.info(f"Total images: {len(transcribed_pages)}")
        ai_logger.info(f"Total time: {batch_total_elapsed:.1f}s ({batch_total_elapsed/60:.1f} min)")
        ai_logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        ai_logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate final metrics
        final_metrics = calculate_metrics(usage_metadata_list, timing_list) if usage_metadata_list else None
        
        # Update the overview section with final metrics from all batches
        if doc_id and len(transcribed_pages) > 0:
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Updating overview section with final metrics from all batches...")
            success = update_overview_section(docs_service, doc_id, transcribed_pages, config, prompt_text, final_metrics, start_time, end_time)
            if success:
                logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Overview section updated successfully.")
            else:
                logging.warning(f"[{datetime.now().strftime('%H:%M:%S')}] Overview section update failed or was skipped.")
            
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] All batches written to document '{doc_name}'")
            logging.info(f"Final metrics: {final_metrics}")
        elif len(transcribed_pages) > 0:
            # Document creation failed, but we saved locally
            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] All batches processed. Transcription saved locally.")
        
        # Log session completion
        ai_logger.info(f"=== Transcription Session Completed ===")
        ai_logger.info(f"Session end timestamp: {datetime.now().isoformat()}")
        ai_logger.info(f"Total images processed: {len(transcribed_pages)}")
        ai_logger.info(f"Successful transcriptions: {len([p for p in transcribed_pages if p['text'] and not p['text'].startswith('[Error')])}")
        ai_logger.info(f"Failed transcriptions: {len([p for p in transcribed_pages if not p['text'] or p['text'].startswith('[Error')])}")
        ai_logger.info(f"=== Session Summary ===\n")
        
    except Exception as e:
        # Log session error with resume information
        error_type = type(e).__name__
        images_processed = len(transcribed_pages) if 'transcribed_pages' in locals() else 0
        
        # Calculate next image number from the last successfully processed image
        next_image_number = None
        if images_processed > 0 and 'transcribed_pages' in locals():
            last_image_name = transcribed_pages[-1]['name']
            last_image_number = extract_image_number(last_image_name)
            if last_image_number is not None:
                next_image_number = last_image_number + 1
            else:
                # Fallback: use position-based calculation
                next_image_number = image_start_number + images_processed
        elif images_processed > 0:
            # Fallback if we can't get the last image name
            next_image_number = image_start_number + images_processed
        
        ai_logger.error(f"=== Transcription Session Error ===")
        ai_logger.error(f"Error timestamp: {datetime.now().isoformat()}")
        ai_logger.error(f"Error type: {error_type}")
        ai_logger.error(f"Error: {str(e)}")
        ai_logger.error(f"Images processed before error: {images_processed}")
        if next_image_number is not None:
            last_image_info = f" (last processed: {transcribed_pages[-1]['name'] if images_processed > 0 and 'transcribed_pages' in locals() else 'unknown'})"
            ai_logger.error(f"RESUME INFO: Update config image_start_number = {next_image_number} to resume from next image{last_image_info}")
        ai_logger.error(f"=== Session Error End ===\n")
        
        logging.error(f"Error in main: {error_type}: {str(e)}")
        if next_image_number is not None:
            last_image_info = f" (last processed: {transcribed_pages[-1]['name'] if images_processed > 0 and 'transcribed_pages' in locals() else 'unknown'})"
            logging.error(f"RESUME INFO: Processed {images_processed} images successfully before error")
            logging.error(f"RESUME INFO: To resume from this point, update config image_start_number = {next_image_number}{last_image_info}")
        logging.error(f"Full traceback:\n{traceback.format_exc()}")
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Genealogical Record Transcription Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python transcribe.py config/config.yaml
  
The config file must be a YAML file containing all required configuration parameters.
See config/config.yaml.example for a template.
        """
    )
    parser.add_argument(
        'config_file',
        type=str,
        help='Path to YAML configuration file (e.g., config/config.yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration first (needed for logging setup)
        config = load_config(args.config_file)
        
        # Set up logging (needs config for folder_name) - MUST be done before any logging calls
        log_filename, ai_log_filename, ai_logger = setup_logging(config)
        
        # Now we can log
        logging.info(f"Configuration loaded from: {args.config_file}")
        logging.info(f"Logging initialized. Main log: {log_filename}, AI log: {ai_log_filename}")
        
        # Load prompt text
        prompt_file = config['prompt_file']
        prompt_text = load_prompt_text(prompt_file)
        logging.info(f"Prompt file loaded: {prompt_file} ({len(prompt_text)} characters)")
        
        # Get logs directory for save_transcription_locally
        logs_dir = "logs"
        
        # Run main function
        main(config, prompt_text, ai_logger, logs_dir)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Please provide a valid configuration file path.", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required configuration key: {e}", file=sys.stderr)
        print(f"Please check your configuration file against config/config.yaml.example", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logging.error(f"Fatal error: {e}")
        logging.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)
