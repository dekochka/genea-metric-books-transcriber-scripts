#!/usr/bin/env python3
"""
Script to extract and transcribe text from JPEG files in a Google Drive folder using Vertex AI Gemini 2.5 Pro Preview,
and compile results into a Google Doc in the same folder.

Test mode processes only the first TEST_IMAGE_COUNT images. Max images processed is capped by MAX_IMAGES.
"""

import io
import os
import logging
import base64
import json
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
TEST_MODE = False
TEST_IMAGE_COUNT = 2
MAX_IMAGES = 200

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

# LLM Instruction for transcription
INSTRUCTION = """Extract and transcribe all text from this handwritten 18th-century birth record from eastern Ukraine, written in Latin. 
    The record contains the following fields: year (usually top left corner), page (usually top right corner), dateOfBirth (source is in in format like  day of birth, day of baptism, month in latin and year,  
    example of source: 14 14 septembris 1889 ), house number, short village name (e.g 21 Turyl), child's name, obstetrician's name, religion, 
    parents names (e.g "Onuphreus filius Stachii Martyniuk et Josephae Humeniuk - Eudoxia filia Michaii Hanczaryk et Parascevy Husak", extract full exact info as is), 
    godfather (patrini, e.g. Basilius Federczuk & Catarina uxor Joannis Lazaruk , agricola ), 
    Notes (e.g include info if child is illigitimate and other notes). 
    list of some villages related to this book: Werbiwka, Turylche, Pidpilipje, Zalesje, Slobodka, Pukljaki. 
    Some common surnames: Lazaruk, Szewczuk, Babij, Kowalczuk, Baziuk, Juskiw, Szepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick,   

Follow these instructions:

1. **Transcription Accuracy**:
  - Transcribe the text exactly as it appears, preserving Latin spelling, abbreviations, and historical orthography.
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
    Returns list of image metadata including id, name, and webViewLink.
    """
    query = (
        f"mimeType='image/jpeg' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
    )
    # Add orderBy parameter to sort by name
    resp = drive_service.files().list(
        q=query,
        fields="files(id,name,webViewLink)",
        orderBy="name"  # Sort by filename
    ).execute()
    images = resp.get('files', [])[:MAX_IMAGES]
    logging.info(f"Found {len(images)} images in folder '{FOLDER_NAME}' (sorted by filename)")
    return images


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
    
    # Generate content
    response = genai_client.models.generate_content(
        model=OCR_MODEL_ID,
        contents=[content],
        config=generate_content_config
    )
    
    text = response.text
    
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
        # Initialize services
        creds = authenticate()
        drive_service, docs_service, genai_client = init_services(creds)

        images = list_images(drive_service)
        if TEST_MODE:
            images = images[:TEST_IMAGE_COUNT]
        
        if not images:
            logging.error(f"No images found in folder '{FOLDER_NAME}'")
            return
        
        # First, transcribe all images
        logging.info(f"Starting transcription of {len(images)} images...")
        transcribed_pages = []
        for img in images:
            try:
                img_bytes = download_image(drive_service, img['id'], img['name'])
                text = transcribe_image(genai_client, img_bytes, img['name'])
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
        
        # Then create documents in batches of 50 for non-test mode
        if not TEST_MODE:
            for i in range(0, len(transcribed_pages), 50):
                end_idx = min(i + 50, len(transcribed_pages))
                # Create document name with page range
                doc_name = f"pg{i+1:03d}-{end_idx:03d}"
                doc_id = create_doc(docs_service, drive_service, doc_name)
                write_to_doc(docs_service, doc_id, transcribed_pages, i)
                logging.info(f"Created document {doc_name} with images {i+1} to {end_idx}")
        else:
            # Test mode - create single document
            doc_id = create_doc(docs_service, drive_service, "test_transcription")
            write_to_doc(docs_service, doc_id, transcribed_pages)
        
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        raise


if __name__ == '__main__':
    main()
