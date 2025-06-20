#!/usr/bin/env python3
"""
Script to extract and transcribe text from JPEG files in a Google Drive folder using Vertex AI Gemini 2.5 Pro Preview,
and compile results into a Google Doc in the same folder.

Features:
- Fetches up to 1000 images from Google Drive folder
- Supports selective image processing using IMAGE_START_NUMBER and IMAGE_COUNT
- Comprehensive logging of all Vertex AI responses with timestamps
- Handles pagination for large folders
- Test mode processes only the first TEST_IMAGE_COUNT images

Image Selection:
- Set IMAGE_START_NUMBER to specify starting image (e.g., 101 for image00101.jpg)
- Set IMAGE_COUNT to specify how many consecutive images to process
- Files must follow pattern: imageXXXXX.jpg where XXXXX is a 5-digit number

Test mode processes only the first TEST_IMAGE_COUNT images. Max images processed is capped by MAX_IMAGES.
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

# ------------------------- CONFIGURATION -------------------------
PROJECT_ID = "ru-ocr-genea"
DRIVE_FOLDER_ID = "1Hqd3Kgys9yyDg_iXlXDQm1GNBLVABVVX"
FOLDER_NAME = "1888-1924 Турилче Вербивки Метрич Книга (487-1-545)"
REGION = "global"  # Changed to global as per sample
OCR_MODEL_ID = "gemini-2.5-pro-preview-06-05"
ADC_FILE = "application_default_credentials.json"  # ADC file with refresh token
TEST_MODE = True
TEST_IMAGE_COUNT = 2
MAX_IMAGES = 1000  # Increased to 1000 to fetch more images
IMAGE_START_NUMBER = 101  # Starting image number (e.g., 101 for image00101.jpg)
IMAGE_COUNT = 90  # Number of images to process starting from IMAGE_START_NUMBER

# Image Selection Notes:
# - IMAGE_START_NUMBER: The starting image number (e.g., 101 will start from image00101.jpg)
# - IMAGE_COUNT: How many consecutive images to process (e.g., 5 will process image00101.jpg through image00105.jpg)
# - Files must follow the pattern: imageXXXXX.jpg where XXXXX is a 5-digit number
# - The script will fetch up to MAX_IMAGES from Google Drive, then filter based on these parameters

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Generate timestamp for log files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Logging setup
log_filename = f"transcription_{FOLDER_NAME.replace(' ', '_')}.log"
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

# LLM Instruction for transcription
INSTRUCTION = """Extract and transcribe all text from this handwritten 18th-century birth record from eastern Ukraine, written in Latin or Ukrainian. 
    The record contains the following fields: year (usually top left corner), page (usually top right corner), dateOfBirth (source is in in format like  day of birth, day of baptism, month in latin and year,  
    example of source: 14 14 septembris 1889 ), house number, short village name (e.g 21 Turyl), child's name, obstetrician's name, religion, 
    parents names (e.g "Onuphreus filius Stachii Martyniuk et Josephae Humeniuk - Eudoxia filia Michaii Hanczaryk et Parascevy Husak", extract full exact info as is), 
    godfather (patrini, e.g. Basilius Federczuk & Catarina uxor Joannis Lazaruk , agricola ), 
    Notes (e.g include info if child is illigitimate and other notes). 
    list of some villages related to this book: Werbiwka, Turylche, Pidpilipje, Zalesje, Slobodka, Pukljaki. 
    Some common surnames: Lazaruk, Szewczuk, Babij, Kowalczuk, Baziuk, Juskiw, Szepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick,   

Follow these instructions:

1. **Transcription Accuracy**:
  - Transcribe the text exactly as it appears, preserving Latin or Ukrainian spelling, abbreviations, and historical orthography.
  - If handwriting is unclear, provide the most likely transcription and note uncertainty in square brackets, e.g., [illegible] or [possibly Anna].
  - Handle Latin-specific characters (e.g., æ, œ) and common abbreviations (e.g., \"Joannes\" for \"Johannes\").

2. **Structured Output**:
  - Format the output for each record with the following fields (on new line):  
    year, page, (common page info)
        then for each row (every child birth record): 
        full child name with fathers name in between triple star (dont put name of field, just put value, start with child name) : ***Name Fathers Name Surname DOB*** e.g.  ***Maria Onuphreus Martyniuk 14/09/1889***
        extracted "**field**: value" on new line: dateofbirth,  dateofbaptism,  house_number, village_name, child_name,  parents, patrini, notes (any extra info), obstetrician, rawinfo.
last column rawinfo must include full text related to a row in original format as close to source row as possible

3. **Historical Context**:
  - Expect 18th-century Latin handwriting with potential flourishes, ligatures, or faded ink.
  - Dates may use Roman numerals (e.g., XVII for 17) or Latin month names (e.g., Januarius, Februarius).
  - Names may include patronymics or Latinized forms (e.g., \"Petri\" for Peter, \"Mariae\" for Maria).

4. **Error Handling**:
  - If text is ambiguous, prioritize the most contextually appropriate interpretation based on typical birth record structure.
  - Ignore irrelevant text (e.g., marginal notes, page numbers) unless it clearly relates to the specified fields."""

# ------------------------------------------------------------------

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
    Returns list of image metadata including id, name, and webViewLink.
    """
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
    
    # Filter images based on IMAGE_START_NUMBER and IMAGE_COUNT
    filtered_images = []
    start_filename = f"image{IMAGE_START_NUMBER:05d}.jpg"
    end_filename = f"image{IMAGE_START_NUMBER + IMAGE_COUNT - 1:05d}.jpg"
    
    logging.info(f"Filtering images from {start_filename} to {end_filename}")
    
    for img in all_images:
        filename = img['name']
        # Check if filename matches the pattern imageXXXXX.jpg
        if filename.startswith('image') and filename.endswith('.jpg'):
            try:
                # Extract the number from filename (e.g., "image00101.jpg" -> 101)
                number_str = filename[5:-4]  # Remove "image" prefix and ".jpg" suffix
                number = int(number_str)
                
                # Check if number is in the desired range
                if IMAGE_START_NUMBER <= number < IMAGE_START_NUMBER + IMAGE_COUNT:
                    filtered_images.append(img)
                    
            except ValueError:
                # Skip files that don't match the expected pattern
                continue
    
    logging.info(f"Selected {len(filtered_images)} images for processing (from {IMAGE_START_NUMBER} to {IMAGE_START_NUMBER + IMAGE_COUNT - 1})")
    
    # Log the selected filenames for verification
    if filtered_images:
        filenames = [img['name'] for img in filtered_images]
        logging.info(f"Selected files: {filenames}")
    
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
            types.Part.from_text(text=INSTRUCTION),
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
        system_instruction=[types.Part.from_text(text=INSTRUCTION)],
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
    )
    
    try:
        # Generate content
        response = genai_client.models.generate_content(
            model=OCR_MODEL_ID,
            contents=[content],
            config=generate_content_config
        )
        
        text = response.text
        
        # Ensure text is not None
        if text is None:
            text = "[No response text received from Vertex AI]"
        
        # Log the full AI response to the AI responses log
        ai_logger.info(f"=== AI Response for {file_name} ===")
        ai_logger.info(f"Model: {OCR_MODEL_ID}")
        ai_logger.info(f"Request timestamp: {datetime.now().isoformat()}")
        ai_logger.info(f"Image size: {len(image_bytes)} bytes")
        ai_logger.info(f"Instruction length: {len(INSTRUCTION)} characters")
        ai_logger.info(f"Response length: {len(text) if text else 0} characters")
        
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
        
    except Exception as e:
        error_msg = f"Error in Vertex AI transcription for {file_name}: {str(e)}"
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


def write_to_doc(docs_service, doc_id, pages, start_idx=0):
    """
    Write transcribed content to a Google Doc with minimal formatting.
    Formatting includes:
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
                
                # Process requests in batches if we're not in test mode
                if not TEST_MODE and len(all_requests) >= BATCH_SIZE:
                    logging.info(f"Processing batch of {len(all_requests)} requests...")
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': all_requests}).execute()
                    all_requests = []
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
        
        # Process any remaining requests
        if all_requests:
            logging.info(f"Processing final batch of {len(all_requests)} requests...")
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': all_requests}).execute()
            logging.info("Final batch processed successfully")
        
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
        ai_logger.info(f"Max images: {MAX_IMAGES}")
        ai_logger.info(f"Image start number: {IMAGE_START_NUMBER}")
        ai_logger.info(f"Image count: {IMAGE_COUNT}")
        ai_logger.info(f"=== Session Configuration ===\n")
        
        # Initialize services
        creds = authenticate()
        drive_service, docs_service, genai_client = init_services(creds)

        images = list_images(drive_service)
        
        if not images:
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
