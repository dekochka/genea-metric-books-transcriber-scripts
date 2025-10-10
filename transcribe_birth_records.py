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
PROMPT_FILE = os.environ.get("PROMPT_FILE", "INSTRUCTION.txt")

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
DRIVE_FOLDER_ID = "1wtD1MxriKowHUn9Ll_SnIyzHLPvHwPMo"
FOLDER_NAME = "1837-1866 Kurypow Курипов Остров Пукасивцы FamSearch 004933159"

REGION = "global"  # Changed to global as per sample
OCR_MODEL_ID = "gemini-2.5-pro"
ADC_FILE = "application_default_credentials.json"  # ADC file with refresh token
TEST_MODE = True
TEST_IMAGE_COUNT = 2
MAX_IMAGES = 1000  # Increased to 1000 to fetch more images
IMAGE_START_NUMBER = 6  # Starting image number (e.g., 101 for image00101.jpg or 101.jpg)
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
    
    for img in all_images:
        filename = img['name']
        number = None
        timestamp_match = None
        
        # Check for timestamp pattern first
        timestamp_match = timestamp_pattern.match(filename)
        if timestamp_match:
            timestamp_images.append(img)
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
            thinking_budget=-1,
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
        raise


def create_overview_section(pages):
    """
    Create overview section content for the document.
    Returns a list of requests to add the overview section.
    """
    # Get folder link from the first page
    folder_link = pages[0]['webViewLink'] if pages else ""
    # Extract folder ID from the link for a cleaner folder link
    if 'folders/' in folder_link:
        folder_id = folder_link.split('folders/')[1].split('/')[0]
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    else:
        folder_url = folder_link
    
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
    
    # Create overview content
    overview_content = f"""OVERVIEW

Name: {FOLDER_NAME}
Folder Link: {folder_url}
Model: {OCR_MODEL_ID}
Prompt File: {PROMPT_FILE}

Files Processed:
Count: {file_count}
Start: {start_file}
End: {end_file}

Images with Errors ({len(failed_pages)}):
"""
    
    # Add failed images list
    if failed_pages:
        for page in failed_pages:
            overview_content += f"- {page['name']}\n"
    else:
        overview_content += "None\n"
    
    overview_content += f"""
Prompt Used:
{PROMPT_TEXT}

{'='*50}

"""
    
    return overview_content


def write_to_doc(docs_service, doc_id, pages, start_idx=0):
    """
    Write transcribed content to a Google Doc with minimal formatting.
    Formatting includes:
    - Overview section with metadata
    - Filename as Heading 1
    - Source link
    - Raw Vertex AI output as normal text
    
    Handles batching of requests to stay within Google Docs API limits (500 requests per batch).
    """
    logging.info(f"Preparing document content for folder '{FOLDER_NAME}'...")
    
    try:
        # Get the current document to check its structure
        doc = docs_service.documents().get(documentId=doc_id).execute()
        
        # Start at the beginning of the document
        idx = 1
        all_requests = []
        BATCH_SIZE = 450  # Using 450 to be safe, as some operations might generate multiple requests
        
        # Add overview section at the beginning
        overview_content = create_overview_section(pages)
        all_requests.extend([
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
            }
        ])
        idx += len(overview_content)
        
        for i, item in enumerate(pages[start_idx:], start=start_idx + 1):
            try:
                # Add filename as Heading 1
                all_requests.extend([
                    {
                        'insertText': {
                            'location': {'index': idx},
                            'text': f"{item['name']}\n"
                        }
                    },
                    {
                        'updateParagraphStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(item['name']) + 1},
                            'paragraphStyle': {
                                'namedStyleType': 'HEADING_1',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                    }
                ])
                idx += len(item['name']) + 1
                
                # Add source link
                link_text = f"Source: view:{item['name']}"
                all_requests.extend([
                    {
                        'insertText': {
                            'location': {'index': idx},
                            'text': link_text + "\n"
                        }
                    },
                    {
                        'updateTextStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(link_text)},
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
                
                # Add raw Vertex AI output as normal text
                if item['text']:
                    all_requests.extend([
                        {
                            'insertText': {
                                'location': {'index': idx},
                                'text': item['text'] + "\n\n"
                            }
                        },
                        {
                            'updateParagraphStyle': {
                                'range': {'startIndex': idx, 'endIndex': idx + len(item['text']) + 2},
                                'paragraphStyle': {
                                    'namedStyleType': 'NORMAL_TEXT',
                                    'alignment': 'START'
                                },
                                'fields': 'namedStyleType,alignment'
                            }
                        }
                    ])
                    idx += len(item['text']) + 2
                
                logging.info(f"Added transcription for '{item['name']}' to document")
                
                # Process requests in batches (always enforce chunking to avoid API limits)
                if len(all_requests) >= BATCH_SIZE:
                    logging.info(f"Processing batch of up to {BATCH_SIZE} requests (current queue: {len(all_requests)})...")
                    # Send only BATCH_SIZE requests to stay under 500 requests per batchUpdate
                    batch = all_requests[:BATCH_SIZE]
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': batch}).execute()
                    # Drop the sent chunk and keep the rest queued
                    all_requests = all_requests[BATCH_SIZE:]
                    logging.info("Batch processed successfully")
                
            except Exception as e:
                logging.error(f"Error processing page {i} ('{item['name']}'): {str(e)}")
                # Add error message to document
                error_text = f"\n[Error processing this page: {str(e)}]\n"
                all_requests.append({
                    'insertText': {
                        'location': {'index': idx},
                        'text': error_text
                    }
                })
                idx += len(error_text)
        
        # Process any remaining requests in safe chunks
        while all_requests:
            chunk = all_requests[:BATCH_SIZE]
            logging.info(f"Processing remaining batch of {len(chunk)} requests (left: {len(all_requests)})...")
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': chunk}).execute()
            all_requests = all_requests[BATCH_SIZE:]
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
        
        # Create document with descriptive name based on image range
        if len(transcribed_pages) > 0:
            first_image = transcribed_pages[0]['name']
            last_image = transcribed_pages[-1]['name']
            doc_name = f"transcription_{first_image[:-4]}-{last_image[:-4]}"
            doc_id = create_doc(docs_service, drive_service, doc_name)
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
