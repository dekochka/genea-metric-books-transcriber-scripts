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
- Set PROMPT_FILE environment variable to select prompt (default: INSTRUCTION.txt)
- Configure IMAGE_START_NUMBER and IMAGE_COUNT for selective processing
- Enable RETRY_MODE to reprocess failed images

For detailed setup instructions, prerequisites, and troubleshooting, see README.md
"""

import io
import os
import logging
import base64
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
from google.genai import types

# ------------------------- PROMPTS -------------------------
# Set which prompt file to load from the `prompts` folder (without path).
# Use "INSTRUCTION.txt" by default.
PROMPT_FILE = os.environ.get("PROMPT_FILE", "INSTRUCTION_BLUDNIKI.txt")

def load_prompt_text() -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    prompt_path = os.path.join(prompts_dir, PROMPT_FILE)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.warning(f"Failed to load prompt '{PROMPT_FILE}' from {prompt_path}: {e}. Falling back to minimal prompt.")
        return "Transcribe the content of this image as structured text."

# Load prompt once at startup
PROMPT_TEXT = load_prompt_text()

# ------------------------- CONFIGURATION -------------------------
#PROJECT_ID = "ru-ocr-genea"
PROJECT_ID = "ukr-transcribe-genea"
#DRIVE_FOLDER_ID = "1Hqd3Kgys9yyDg_iXlXDQm1GNBLVABVVX"
#FOLDER_NAME = "1888-1924 Турилче Вербивки Метрич Книга (487-1-545)"
#DRIVE_FOLDER_ID = "1ka-1tUaGDc55BGihPm9q56Yskfbm6m-a"
#FOLDER_NAME = "1874-1936 Турильче Вербивка записи о смерти 487-1-729-смерті"
DRIVE_FOLDER_ID = "1rhICtjI-CIRBl9yehxUGT2GWlLk0483P"
FOLDER_NAME = "1837-1866 Bludniki FamilySearch 004932767 Подгруппа 8 Ф.201 О.4А Д.350"
ARCHIVE_INDEX = "ф201оп4Aспр350"

REGION = "global"  # Changed to global as per sample
OCR_MODEL_ID = "gemini-3-flash-preview"
ADC_FILE = "application_default_credentials.json"  # ADC file with refresh token
TEST_MODE = True
TEST_IMAGE_COUNT = 2
MAX_IMAGES = 1000  # Increased to 1000 to fetch more images
IMAGE_START_NUMBER = 89  # Starting image number (e.g., 101 for image00101.jpg or 101.jpg)
IMAGE_COUNT = 1  # Number of images to process starting from IMAGE_START_NUMBER

# RETRY MODE - Set to True to retry specific failed images
RETRY_MODE = False
RETRY_IMAGE_LIST = [
    # Image that failed with timeout on 2025-08-03 (now fixed)
     "2025-07-23T065033.080.jpg"
]

# Image Selection Notes:
# - IMAGE_START_NUMBER: The starting image number (e.g., 101 will start from image00101.jpg or 101.jpg)
# - IMAGE_COUNT: How many consecutive images to process (e.g., 5 will process image00101.jpg through image00105.jpg or 101.jpg through 105.jpg)
# - Files must follow one of these patterns: 
#   * image (N).jpg where N is a number (e.g., image (7).jpg, image (10).jpg)
#   * imageXXXXX.jpg where XXXXX is a 5-digit number (e.g., image00101.jpg)
#   * XXXXX.jpg where XXXXX is a number (e.g., 52.jpg, 102.jpg)
#   * image - YYYY-MM-DDTHHMMSS.mmm.jpg (timestamp format, e.g., image - 2025-07-20T112914.366.jpg)
# - The script will fetch up to MAX_IMAGES from Google Drive, then filter based on these parameters

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Generate timestamp for log files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Logging setup - create shorter log filename to avoid filesystem limits
safe_folder_name = "".join(c for c in FOLDER_NAME if c.isalnum() or c in (' ', '-', '_')).rstrip()
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

# Make ai_logger globally accessible
globals()['ai_logger'] = ai_logger


def authenticate():
    """
    Load user credentials from ADC file with required OAuth2 scopes.
    """
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/cloud-platform"
    ]
    creds = Credentials.from_authorized_user_file(ADC_FILE, scopes=scopes)
    logging.info(f"Credentials loaded with scopes: {scopes}")
    return creds


def init_services(creds):
    logging.info(f"Initializing Vertex AI for project {PROJECT_ID}...")
    # Set env var for Vertex AI SDK
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ADC_FILE
    
    # Initialize Gemini client
    genai_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION,
        credentials=creds
    )
    logging.info(f"Gemini client initialized in {REGION} with project {PROJECT_ID}")

    logging.info("Initializing Google Drive and Docs APIs...")
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    logging.info("Google Drive and Docs APIs initialized.")
    return drive, docs, genai_client


def list_images(drive_service):
    """
    Get list of images from Google Drive folder, sorted by filename.
    Handles pagination to fetch up to 1000 images and filters based on IMAGE_START_NUMBER and IMAGE_COUNT.
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
    
    query = (
        f"mimeType='image/jpeg' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
    )
    
    all_images = []
    page_token = None
    
    # Fetch all images with pagination (up to MAX_IMAGES)
    while len(all_images) < MAX_IMAGES:
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
            logging.error(f"Error fetching images from Google Drive: {str(e)}")
            break
    
    # Limit to MAX_IMAGES
    all_images = all_images[:MAX_IMAGES]
    logging.info(f"Found {len(all_images)} total images in folder '{FOLDER_NAME}' (sorted by filename)")
    
    # RETRY MODE: If enabled, filter for specific failed images only
    if RETRY_MODE:
        logging.info(f"RETRY MODE ENABLED: Looking for {len(RETRY_IMAGE_LIST)} specific failed images")
        retry_images = []
        
        # Convert retry list to full image names (add "image - " prefix if needed)
        retry_full_names = []
        for retry_img in RETRY_IMAGE_LIST:
            if retry_img.startswith('image - '):
                retry_full_names.append(retry_img)
            else:
                retry_full_names.append(f"image - {retry_img}")
        
        # Find matching images
        for img in all_images:
            if img['name'] in retry_full_names:
                retry_images.append(img)
        
        logging.info(f"Found {len(retry_images)} retry images out of {len(RETRY_IMAGE_LIST)} requested")
        if retry_images:
            retry_filenames = [img['name'] for img in retry_images]
            logging.info(f"Retry images found: {retry_filenames}")
        else:
            logging.warning("No retry images found! Check the RETRY_IMAGE_LIST names.")
        
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
            if IMAGE_START_NUMBER <= number < IMAGE_START_NUMBER + IMAGE_COUNT:
                numbered_images.append(img)
    
    # Handle numbered images (existing logic)
    filtered_images = []
    
    if numbered_images:
        # Define expected filename patterns for logging
        start_filename_pattern1 = f"image ({IMAGE_START_NUMBER}).jpg"
        end_filename_pattern1 = f"image ({IMAGE_START_NUMBER + IMAGE_COUNT - 1}).jpg"
        start_filename_pattern2 = f"image{IMAGE_START_NUMBER:05d}.jpg"
        end_filename_pattern2 = f"image{IMAGE_START_NUMBER + IMAGE_COUNT - 1:05d}.jpg"
        start_filename_pattern3 = f"{IMAGE_START_NUMBER}.jpg"
        end_filename_pattern3 = f"{IMAGE_START_NUMBER + IMAGE_COUNT - 1}.jpg"
        
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
        
        # For timestamp images, treat IMAGE_START_NUMBER as the starting position (1-indexed)
        # and IMAGE_COUNT as the number of images to process
        start_pos = max(1, IMAGE_START_NUMBER) - 1  # Convert to 0-indexed
        end_pos = min(len(timestamp_images), start_pos + IMAGE_COUNT)
        
        selected_timestamp_images = timestamp_images[start_pos:end_pos]
        filtered_images.extend(selected_timestamp_images)
        
        if selected_timestamp_images:
            logging.info(f"Selected {len(selected_timestamp_images)} timestamp images from position {IMAGE_START_NUMBER} to {start_pos + len(selected_timestamp_images)}")
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
    if not filtered_images and all_images and not RETRY_MODE:
        # all_images are already sorted by name from the Drive API
        start_pos = max(1, IMAGE_START_NUMBER) - 1
        end_pos = min(len(all_images), start_pos + IMAGE_COUNT)
        fallback_selected = all_images[start_pos:end_pos]
        if fallback_selected:
            logging.info(f"No numeric/timestamp matches; falling back to position selection: items {IMAGE_START_NUMBER} to {IMAGE_START_NUMBER + len(fallback_selected) - 1}")
            filtered_images = fallback_selected

    logging.info(f"Selected {len(filtered_images)} total images for processing")
    
    # Log the selected filenames for verification
    if filtered_images:
        filenames = [img['name'] for img in filtered_images]
        logging.info(f"Final selected files: {filenames}")
    
    return filtered_images


def download_image(drive_service, file_id, file_name):
    logging.info(f"Downloading image '{file_name}' from folder '{FOLDER_NAME}'")
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    img_bytes = fh.read()
    logging.info(f"Image '{file_name}' downloaded successfully ({len(img_bytes)} bytes)")
    return img_bytes


def transcribe_image(genai_client, image_bytes, file_name):
    import signal
    import time
    
    logging.info(f"Sending image '{file_name}' to Vertex AI for transcription...")
    
    # Create image part using base64 encoding
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )
    
            # Create content with instruction and image
    content = types.Content(
        role="user",
        parts=[
                    types.Part.from_text(text=PROMPT_TEXT),
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
        system_instruction=[types.Part.from_text(text=PROMPT_TEXT)],
        thinking_config=types.ThinkingConfig(
            thinking_budget=5000,
        ),
    )
    
    # Timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Vertex AI API call timed out after 30 minutes for {file_name}")
    
    max_retries = 1
    retry_delay = 30  # seconds
    timeout_seconds = 10 * 60  # 10 minutes
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} for image '{file_name}'")
            
            # Set up timeout (30 minutes)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            start_time = time.time()
            
            # Generate content
            response = genai_client.models.generate_content(
                model=OCR_MODEL_ID,
                contents=[content],
                config=generate_content_config
            )
            
            # Cancel the timeout
            signal.alarm(0)
            
            elapsed_time = time.time() - start_time
            logging.info(f"Vertex AI response received in {elapsed_time:.1f} seconds for '{file_name}'")
            
            text = response.text
            
            # Ensure text is not None
            if text is None:
                text = "[No response text received from Vertex AI]"
            
            # Log the full AI response to the AI responses log
            ai_logger.info(f"=== AI Response for {file_name} ===")
            ai_logger.info(f"Model: {OCR_MODEL_ID}")
            ai_logger.info(f"Request timestamp: {datetime.now().isoformat()}")
            ai_logger.info(f"Image size: {len(image_bytes)} bytes")
            ai_logger.info(f"Instruction length: {len(PROMPT_TEXT)} characters")
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
            
            return text
            
        except (TimeoutError, ConnectionError, OSError) as e:
            # Cancel any pending timeout
            signal.alarm(0)
            
            error_msg = f"Attempt {attempt + 1}/{max_retries} failed for {file_name}: {str(e)}"
            logging.warning(error_msg)
            ai_logger.warning(error_msg)
            
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                error_msg = f"All {max_retries} attempts failed for {file_name}: {str(e)}"
                ai_logger.error(f"=== AI Error for {file_name} ===")
                ai_logger.error(error_msg)
                ai_logger.error(f"=== End AI Error for {file_name} ===\n")
                logging.error(error_msg)
                raise
                
        except Exception as e:
            # Cancel any pending timeout
            signal.alarm(0)
            
            error_msg = f"Unexpected error in Vertex AI transcription for {file_name}: {str(e)}"
            ai_logger.error(f"=== AI Error for {file_name} ===")
            ai_logger.error(error_msg)
            ai_logger.error(f"=== End AI Error for {file_name} ===\n")
            logging.error(error_msg)
            raise


def create_doc(docs_service, drive_service, title):
    """Create a new Google Doc in the specified folder and return its ID."""
    try:
        # First create the document
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        
        # Then move it to the specified folder
        file = drive_service.files().update(
            fileId=doc_id,
            addParents=DRIVE_FOLDER_ID,
            fields='id, parents'
        ).execute()
        
        logging.info(f"Created new Google Doc '{title}' in folder '{FOLDER_NAME}' with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error creating Google Doc: {str(e)}")
        # Check if it's a permission error
        if 'insufficientFilePermissions' in str(e) or '403' in str(e):
            logging.warning(f"Insufficient permissions to add document to folder '{FOLDER_NAME}'")
            logging.warning(f"Document was created but could not be moved to the target folder")
            logging.info(f"Returning None to trigger local save fallback")
            return None
        raise


def create_overview_section(pages):
    """
    Create overview section content for the document.
    Returns tuple of (overview_content, formatting_info) where formatting_info is a dict with:
    - folder_link_info: (link_start_index, link_end_index, folder_url)
    - bold_labels: list of (start_index, end_index) for "Files Processed:", "Images with Errors:", "Prompt Used:"
    - prompt_text_range: (start_index, end_index) for the prompt text
    """
    # Get folder link from the first page
    folder_link = pages[0]['webViewLink'] if pages else ""
    # Extract folder ID from the link for a cleaner folder link
    if 'folders/' in folder_link:
        folder_id = folder_link.split('folders/')[1].split('/')[0]
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    else:
        # Use DRIVE_FOLDER_ID to construct folder URL if webViewLink doesn't have folder info
        folder_url = f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}"
    
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
    
    # Create overview content with folder name as link text
    overview_content = f"""TRANSCRIPTION RUN SUMMARY

Name: {FOLDER_NAME}
Folder Link: {FOLDER_NAME}
"""
    
    # Calculate folder link position (after "Folder Link: ")
    folder_link_start = overview_content.find("Folder Link: ") + len("Folder Link: ")
    folder_link_end = folder_link_start + len(FOLDER_NAME)
    folder_link_info = (folder_link_start, folder_link_end, folder_url)
    
    # Add archive index if available
    if ARCHIVE_INDEX:
        overview_content += f"Archive Index: {ARCHIVE_INDEX}\n"
    
    # Track positions for bold labels
    files_processed_label = "Files Processed:"
    images_errors_label = f"Images with Errors ({len(failed_pages)}):"
    prompt_used_label = "Prompt Used:"
    
    overview_content += f"""Model: {OCR_MODEL_ID}
Prompt File: {PROMPT_FILE}

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
    
    # Calculate prompt text position
    prompt_used_start = overview_content.find(prompt_used_label)
    prompt_used_end = prompt_used_start + len(prompt_used_label)
    
    overview_content += f"""
{prompt_used_label}
{PROMPT_TEXT}

{'='*50}

"""
    
    # Calculate prompt text range (after the label and newline)
    prompt_text_start = overview_content.find(prompt_used_label) + len(prompt_used_label) + 1  # +1 for newline
    prompt_text_end = prompt_text_start + len(PROMPT_TEXT)
    
    formatting_info = {
        'folder_link_info': folder_link_info,
        'bold_labels': [
            (files_processed_start, files_processed_end),
            (images_errors_start, images_errors_end),
            (prompt_used_start, prompt_used_end)
        ],
        'prompt_text_range': (prompt_text_start, prompt_text_end)
    }
    
    return overview_content, formatting_info


def add_record_links_to_text(text, archive_index, page_number, web_view_link):
    """
    Find lines starting with ### (like "### Запись 1") and append clickable archive reference.
    For example: "### Запись 1" becomes "### Запись 1 ф201оп4спр104стр22"
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
    
    # Pattern to match ### at start of line (with optional whitespace) followed by any text
    # Matches lines like "### Запись 1", "### Record 1", "### Запис 1", etc.
    pattern = re.compile(r'^(###\s+[^\n]+)', re.IGNORECASE)
    
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


def save_transcription_locally(pages, doc_name):
    """
    Save transcription to a local text file when Google Doc creation fails.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(LOGS_DIR, "local_transcriptions")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename
        safe_doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_doc_name = safe_doc_name.replace(' ', '_')
        output_file = os.path.join(output_dir, f"{safe_doc_name}.txt")
        
        # Create overview content (for local files, we just need the text, not formatting info)
        overview_content, _ = create_overview_section(pages)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write document header
            run_date = datetime.now().strftime("%Y%m%d")
            document_header = f"{FOLDER_NAME} {run_date}"
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


def write_to_doc(docs_service, doc_id, pages, start_idx=0):
    """
    Write transcribed content to a Google Doc with minimal formatting.
    Formatting includes:
    - Overview section with metadata
    - Archive reference + page number as Heading 2 (e.g., "ф201оп4спр104стр22")
    - Source image link
    - Raw Vertex AI output with clickable links on record headers
    
    Handles batching of requests to stay within Google Docs API limits (500 requests per batch).
    Implements circuit breaker pattern to stop after consecutive failures.
    """
    logging.info(f"Preparing document content for folder '{FOLDER_NAME}'...")
    if ARCHIVE_INDEX:
        logging.info(f"Using archive index: {ARCHIVE_INDEX}")
    
    try:
        # Get the current document to check its structure
        doc = docs_service.documents().get(documentId=doc_id).execute()
        
        # Start at the beginning of the document
        idx = 1
        all_requests = []
        BATCH_SIZE = 450  # Using 450 to be safe, as some operations might generate multiple requests
        
        # Circuit breaker to prevent cascading failures
        MAX_CONSECUTIVE_FAILURES = 5
        consecutive_failures = 0
        
        # Add document header (FOLDER_NAME + date) as Heading 1
        run_date = datetime.now().strftime("%Y%m%d")
        document_header = f"{FOLDER_NAME} {run_date}"
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
        doc = docs_service.documents().get(documentId=doc_id).execute()
        idx = doc['body']['content'][-1]['endIndex'] - 1
        logging.info(f"Document header added: {document_header}")
        
        # Add overview section
        overview_content, formatting_info = create_overview_section(pages)
        folder_link_info = formatting_info['folder_link_info']
        bold_labels = formatting_info['bold_labels']
        prompt_text_range = formatting_info['prompt_text_range']
        folder_link_start_offset, folder_link_end_offset, folder_url = folder_link_info
        
        # Calculate position of "TRANSCRIPTION RUN SUMMARY" heading
        summary_heading = "TRANSCRIPTION RUN SUMMARY"
        summary_heading_start = 0
        summary_heading_end = len(summary_heading)
        
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
        
        # Write overview immediately and re-fetch index to ensure accuracy
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': overview_requests}).execute()
        doc = docs_service.documents().get(documentId=doc_id).execute()
        # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
        idx = doc['body']['content'][-1]['endIndex'] - 1
        consecutive_failures = 0  # Reset counter on success
        logging.info(f"Overview section added. Document end index: {doc['body']['content'][-1]['endIndex']}, insertion index: {idx}")
        
        for i, item in enumerate(pages[start_idx:], start=start_idx + 1):
            try:
                # Determine page header: use archive index + page number if available, otherwise image name
                page_number = i
                if ARCHIVE_INDEX:
                    page_header = f"{ARCHIVE_INDEX}стр{page_number}"
                else:
                    page_header = item['name']
                
                # Add page header as Heading 2
                all_requests.extend([
                    {
                        'insertText': {
                            'location': {'index': idx},
                            'text': f"{page_header}\n"
                        }
                    },
                    {
                        'updateParagraphStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(page_header) + 1},
                            'paragraphStyle': {
                                'namedStyleType': 'HEADING_2',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                    }
                ])
                idx += len(page_header) + 1
                
                # Add source image link in new format: "Src Img Url: IMG_NAME_URL"
                link_text = f"Src Img Url: {item['name']}"
                all_requests.extend([
                    {
                        'insertText': {
                            'location': {'index': idx},
                            'text': link_text + "\n"
                        }
                    },
                    {
                        'updateTextStyle': {
                            'range': {'startIndex': idx + len("Src Img Url: "), 'endIndex': idx + len(link_text)},
                            'textStyle': {
                                'link': {'url': item['webViewLink']},
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                                'underline': True
                            },
                            'fields': 'link,foregroundColor,underline'
                        }
                    }
                ])
                idx += len(link_text) + 1
                
                # Process transcribed text to add links to ### record headers
                if item['text']:
                    modified_text, link_insertions = add_record_links_to_text(
                        item['text'], 
                        ARCHIVE_INDEX, 
                        page_number, 
                        item['webViewLink']
                    )
                    text_to_insert = modified_text + "\n\n"
                    text_start_idx = idx
                    
                    # Insert text
                    all_requests.append({
                        'insertText': {
                            'location': {'index': idx},
                            'text': text_to_insert
                        }
                    })
                    
                    # Add paragraph style
                    all_requests.append({
                        'updateParagraphStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(text_to_insert)},
                            'paragraphStyle': {
                                'namedStyleType': 'NORMAL_TEXT',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                    })
                    
                    # Add links to record headers (### lines with archive references)
                    for link_start_offset, link_end_offset, url in link_insertions:
                        link_start = text_start_idx + link_start_offset
                        link_end = text_start_idx + link_end_offset
                        all_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': link_start, 'endIndex': link_end},
                                'textStyle': {
                                    'link': {'url': url},
                                    'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                                    'underline': True
                                },
                                'fields': 'link,foregroundColor,underline'
                            }
                        })
                    
                    idx += len(text_to_insert)
                
                logging.info(f"Added transcription for '{item['name']}' to document (header: {page_header})")
                
                # Process requests in batches (always enforce chunking to avoid API limits)
                if len(all_requests) >= BATCH_SIZE:
                    logging.info(f"Processing batches (current queue: {len(all_requests)})...")
                    # Write all pending requests in chunks to avoid stale indices
                    # (Keeping requests across batch boundaries causes index drift)
                    while all_requests:
                        chunk = all_requests[:BATCH_SIZE]
                        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': chunk}).execute()
                        all_requests = all_requests[BATCH_SIZE:]
                        logging.info(f"Batch of {len(chunk)} requests processed ({len(all_requests)} remaining in queue)...")
                    
                    # Re-fetch document to get current end index (prevents "Precondition check failed" errors)
                    doc = docs_service.documents().get(documentId=doc_id).execute()
                    # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
                    idx = doc['body']['content'][-1]['endIndex'] - 1
                    consecutive_failures = 0  # Reset counter on success
                    logging.info(f"All batches processed successfully. Document index updated to {idx}")
                
            except Exception as e:
                consecutive_failures += 1
                logging.error(f"Error processing page {i} ('{item['name']}'): {str(e)}")
                logging.warning(f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")
                
                # Circuit breaker: stop if too many consecutive failures
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logging.error(f"Circuit breaker triggered: {consecutive_failures} consecutive failures")
                    logging.error(f"Stopping document write to prevent cascading errors")
                    logging.error(f"Successfully wrote {i - consecutive_failures} out of {len(pages)} pages")
                    logging.error(f"Use recovery_script.py with the AI response log to recover remaining pages")
                    raise Exception(f"Exceeded maximum consecutive failures ({MAX_CONSECUTIVE_FAILURES}). Document write stopped.")
                
                # Process any pending requests before handling error
                if all_requests:
                    try:
                        logging.info(f"Flushing {len(all_requests)} pending requests before error handling...")
                        while all_requests:
                            chunk = all_requests[:BATCH_SIZE]
                            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': chunk}).execute()
                            all_requests = all_requests[BATCH_SIZE:]
                        # Re-fetch document to get current end index
                        doc = docs_service.documents().get(documentId=doc_id).execute()
                        # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
                        idx = doc['body']['content'][-1]['endIndex'] - 1
                        consecutive_failures = 0  # Reset if flush succeeds
                        logging.info(f"Pending requests flushed successfully. Document index updated to {idx}")
                    except Exception as flush_error:
                        logging.error(f"Error flushing pending requests: {flush_error}")
                        # Clear the queue to prevent further cascading errors
                        all_requests = []
                
                # Add error message to document
                error_text = f"\n[Error processing this page: {str(e)}]\n"
                try:
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [{
                        'insertText': {
                            'location': {'index': idx},
                            'text': error_text
                        }
                    }]}).execute()
                    # Re-fetch document after adding error message
                    doc = docs_service.documents().get(documentId=doc_id).execute()
                    # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
                    idx = doc['body']['content'][-1]['endIndex'] - 1
                except Exception as error_write_error:
                    logging.error(f"Could not write error message to document: {error_write_error}")
        
        # Process any remaining requests in safe chunks (should be minimal after loop batching)
        if all_requests:
            logging.info(f"Processing final {len(all_requests)} remaining requests...")
        while all_requests:
            chunk = all_requests[:BATCH_SIZE]
            logging.info(f"Processing remaining batch of {len(chunk)} requests (left: {len(all_requests)})...")
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': chunk}).execute()
            all_requests = all_requests[BATCH_SIZE:]
            consecutive_failures = 0  # Reset counter on success
            
            # Re-fetch document to keep index synchronized
            if all_requests:  # Only if there are more batches to process
                doc = docs_service.documents().get(documentId=doc_id).execute()
                # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
                idx = doc['body']['content'][-1]['endIndex'] - 1
                logging.info(f"Remaining batch processed. Document index updated to {idx}")
        logging.info("All batches processed successfully")
        
        logging.info("Google Doc updated successfully")
        
    except Exception as e:
        logging.error(f"Critical error in write_to_doc: {str(e)}")
        raise


def main():
    """Main function to process images and create transcription document."""
    try:
        # Log session start
        ai_logger.info(f"=== Transcription Session Started ===")
        ai_logger.info(f"Session timestamp: {datetime.now().isoformat()}")
        ai_logger.info(f"Project ID: {PROJECT_ID}")
        ai_logger.info(f"Folder: {FOLDER_NAME}")
        ai_logger.info(f"Archive Index: {ARCHIVE_INDEX if ARCHIVE_INDEX else 'None'}")
        ai_logger.info(f"Model: {OCR_MODEL_ID}")
        ai_logger.info(f"Test mode: {TEST_MODE}")
        ai_logger.info(f"Retry mode: {RETRY_MODE}")
        if RETRY_MODE:
            ai_logger.info(f"Retry images count: {len(RETRY_IMAGE_LIST)}")
            ai_logger.info(f"Retry images: {RETRY_IMAGE_LIST}")
        else:
            ai_logger.info(f"Max images: {MAX_IMAGES}")
            ai_logger.info(f"Image start number: {IMAGE_START_NUMBER}")
            ai_logger.info(f"Image count: {IMAGE_COUNT}")
        ai_logger.info(f"=== Session Configuration ===\n")
        
        # Initialize services
        creds = authenticate()
        drive_service, docs_service, genai_client = init_services(creds)

        images = list_images(drive_service)
        
        if not images:
            if RETRY_MODE:
                logging.error(f"No retry images found in folder '{FOLDER_NAME}' from the RETRY_IMAGE_LIST")
                ai_logger.error(f"No retry images found from list of {len(RETRY_IMAGE_LIST)} images")
            else:
                logging.error(f"No images found in folder '{FOLDER_NAME}' for the specified range (start: {IMAGE_START_NUMBER}, count: {IMAGE_COUNT})")
                ai_logger.error(f"No images found for range {IMAGE_START_NUMBER} to {IMAGE_START_NUMBER + IMAGE_COUNT - 1}")
            return
        
        # First, transcribe all images
        logging.info(f"Starting transcription of {len(images)} images...")
        transcribed_pages = []
        for img in images:
            try:
                img_bytes = download_image(drive_service, img['id'], img['name'])
                text = transcribe_image(genai_client, img_bytes, img['name'])
                
                # Ensure text is not None
                if text is None:
                    text = "[No transcription text received]"
                
                transcribed_pages.append({
                    'name': img['name'],
                    'webViewLink': img['webViewLink'],
                    'text': text
                })
                logging.info(f"Successfully transcribed {img['name']}")
            except Exception as e:
                logging.error(f"Error transcribing {img['name']}: {str(e)}")
                # Add error message as text
                transcribed_pages.append({
                    'name': img['name'],
                    'webViewLink': img['webViewLink'],
                    'text': f"[Error during transcription: {str(e)}]"
                })
        
        # Create document with filename as FOLDER_NAME + date (restored previous logic)
        if len(transcribed_pages) > 0:
            run_date = datetime.now().strftime("%Y%m%d")
            doc_name = f"{FOLDER_NAME} {run_date}"
            
            # Try to create Google Doc with FOLDER_NAME + date (this sets both filename and tab title)
            doc_id = create_doc(docs_service, drive_service, doc_name)
            
            if doc_id is None:
                # Permission error - save locally instead
                logging.warning("Cannot create Google Doc due to insufficient permissions")
                logging.info("Saving transcription to local file instead...")
                local_file = save_transcription_locally(transcribed_pages, doc_name)
                logging.info(f"✓ Transcription saved locally: {local_file}")
                logging.info(f"✓ Processed {len(transcribed_pages)} images successfully")
            else:
                # Successfully created doc - write to it
                write_to_doc(docs_service, doc_id, transcribed_pages)
                logging.info(f"Created document '{doc_name}' with {len(transcribed_pages)} images")
        
        # Log session completion
        ai_logger.info(f"=== Transcription Session Completed ===")
        ai_logger.info(f"Session end timestamp: {datetime.now().isoformat()}")
        ai_logger.info(f"Total images processed: {len(transcribed_pages)}")
        ai_logger.info(f"Successful transcriptions: {len([p for p in transcribed_pages if p['text'] and not p['text'].startswith('[Error')])}")
        ai_logger.info(f"Failed transcriptions: {len([p for p in transcribed_pages if not p['text'] or p['text'].startswith('[Error')])}")
        ai_logger.info(f"=== Session Summary ===\n")
        
    except Exception as e:
        # Log session error
        ai_logger.error(f"=== Transcription Session Error ===")
        ai_logger.error(f"Error timestamp: {datetime.now().isoformat()}")
        ai_logger.error(f"Error: {str(e)}")
        ai_logger.error(f"=== Session Error End ===\n")
        logging.error(f"Error in main: {str(e)}")
        raise


if __name__ == '__main__':
    main()
