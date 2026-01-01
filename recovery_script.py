#!/usr/bin/env python3
"""
Recovery script to process AI response logs and create a Google Doc.
This script parses the AI response logs from transcribe_birth_records.py
and recreates the Google Doc that failed to be created due to timeout errors.
"""

import re
import os
import logging
import argparse
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Use same configuration as main script
PROJECT_ID = "ru-ocr-genea"
ADC_FILE = "application_default_credentials.json"

def setup_logging():
    """Set up logging for the recovery script"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"recovery_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename)
        ]
    )

def authenticate():
    """Load user credentials from ADC file with required OAuth2 scopes."""
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/cloud-platform"
    ]
    creds = Credentials.from_authorized_user_file(ADC_FILE, scopes=scopes)
    logging.info(f"Credentials loaded with scopes: {scopes}")
    return creds

def init_services(creds):
    """Initialize Google Drive and Docs APIs."""
    logging.info("Initializing Google Drive and Docs APIs...")
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    logging.info("Google Drive and Docs APIs initialized.")
    return drive, docs

def parse_ai_log(log_file_path, image_links=None):
    """
    Parse the AI response log file and extract image names, view links, and transcriptions.
    Uses line-by-line parsing for better performance on large files.
    
    Args:
        log_file_path: Path to the AI response log file
        image_links: Optional dict mapping image names to webViewLinks from Drive folder
    
    Returns a list of dictionaries with 'name', 'webViewLink', and 'text' keys.
    """
    logging.info(f"Parsing AI log file: {log_file_path}")
    if image_links:
        logging.info(f"Using {len(image_links)} webViewLinks from Drive folder")
    
    pages = []
    folder_name = "Unknown Folder"
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logging.info(f"Processing {len(lines)} lines from log file")
        
        # State tracking for line-by-line parsing
        current_image = None
        current_web_view_link = None
        in_response = False
        in_error = False
        response_lines = []
        error_message = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Extract folder name from session info
            if "- Folder:" in line:
                folder_name = line.split("- Folder:", 1)[1].strip()
                logging.info(f"Detected folder: {folder_name}")
            
            # Start of AI response
            elif "=== AI Response for " in line and line.endswith(" ==="):
                # Extract image name from the line
                start_idx = line.find("=== AI Response for ") + 20
                end_idx = line.rfind(" ===")
                current_image = line[start_idx:end_idx].strip()
                current_web_view_link = None  # Reset for new image
                in_response = False
                in_error = False
                response_lines = []
                
            # Start of AI error
            elif "=== AI Error for " in line and line.endswith(" ==="):
                # Extract image name from the line
                start_idx = line.find("=== AI Error for ") + 17
                end_idx = line.rfind(" ===")
                current_image = line[start_idx:end_idx].strip()
                current_web_view_link = None  # Reset for new image
                in_response = False
                in_error = True
                error_message = None
                
            # Extract Source URL (Google Drive link)
            elif "- Source URL:" in line or "INFO - Source URL:" in line:
                # Extract the URL after "Source URL:"
                if "Source URL:" in line:
                    url_start = line.find("Source URL:") + len("Source URL:")
                    current_web_view_link = line[url_start:].strip()
            
            # Start of actual response content
            elif "- Full response:" in line and current_image:
                in_response = True
                response_lines = []
                
            # End of AI response
            elif "=== End AI Response for " in line and current_image:
                if in_response and response_lines:
                    response_text = '\n'.join(response_lines).strip()
                    # Priority order for webViewLink:
                    # 1. From Drive folder (if image_links provided)
                    # 2. From log file (current_web_view_link)
                    # 3. Placeholder
                    if image_links and current_image in image_links:
                        web_view_link = image_links[current_image]
                    elif current_web_view_link:
                        web_view_link = current_web_view_link
                    else:
                        web_view_link = f"https://drive.google.com/file/d/placeholder_id_for_{current_image.replace(' ', '_')}/view"
                        logging.warning(f"No Source URL found for {current_image}, using placeholder")
                    
                    pages.append({
                        'name': current_image,
                        'webViewLink': web_view_link,
                        'text': response_text
                    })
                    
                    logging.info(f"Extracted transcription for: {current_image}")
                
                current_image = None
                current_web_view_link = None
                in_response = False
                response_lines = []
                
            # End of AI error
            elif "=== End AI Error for " in line and current_image:
                if in_error and error_message:
                    # Priority order for webViewLink:
                    # 1. From Drive folder (if image_links provided)
                    # 2. From log file (current_web_view_link)
                    # 3. Placeholder
                    if image_links and current_image in image_links:
                        web_view_link = image_links[current_image]
                    elif current_web_view_link:
                        web_view_link = current_web_view_link
                    else:
                        web_view_link = f"https://drive.google.com/file/d/placeholder_id_for_{current_image.replace(' ', '_')}/view"
                        logging.warning(f"No Source URL found for {current_image}, using placeholder")
                    
                    pages.append({
                        'name': current_image,
                        'webViewLink': web_view_link,
                        'text': f"[Error during transcription: {error_message}]"
                    })
                    
                    logging.info(f"Extracted error entry for: {current_image}")
                
                current_image = None
                current_web_view_link = None
                in_error = False
                error_message = None
                
            # Extract error message
            elif in_error and "Unexpected error" in line and ":" in line:
                # Extract the error message after the colon
                error_parts = line.split(":", 1)
                if len(error_parts) > 1:
                    error_message = error_parts[1].strip()
                
            # Collect response lines
            elif in_response:
                # Skip timestamp lines that mark the end
                if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', line):
                    response_lines.append(lines[i].rstrip('\n'))
            
            i += 1
            
            # Progress indicator for large files
            if i % 1000 == 0:
                logging.info(f"Processed {i}/{len(lines)} lines...")
    
    except Exception as e:
        logging.error(f"Error parsing log file: {str(e)}")
        raise
    
    logging.info(f"Successfully parsed {len(pages)} entries from log file")
    return pages, folder_name

def get_drive_folder_id(drive_service, folder_name):
    """
    Try to find the folder ID by name. This is a best-effort attempt.
    In practice, you might need to manually specify the folder ID.
    """
    try:
        # Search for folders with the given name
        results = drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        
        folders = results.get('files', [])
        if folders:
            folder_id = folders[0]['id']
            logging.info(f"Found folder '{folder_name}' with ID: {folder_id}")
            return folder_id
        else:
            logging.warning(f"Could not find folder '{folder_name}' in Drive")
            return None
    except Exception as e:
        logging.error(f"Error searching for folder: {str(e)}")
        return None

def fetch_images_from_folder(drive_service, folder_id):
    """
    Fetch all images from a Google Drive folder and return a dictionary
    mapping filename to webViewLink.
    """
    logging.info(f"Fetching images from folder ID: {folder_id}")
    
    try:
        image_links = {}
        page_token = None
        
        while True:
            query = f"'{folder_id}' in parents and (mimeType contains 'image/' or name contains '.jpg' or name contains '.jpeg' or name contains '.png') and trashed=false"
            
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken,files(id,name,webViewLink)",
                pageToken=page_token,
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            for file in files:
                image_links[file['name']] = file['webViewLink']
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        logging.info(f"Found {len(image_links)} images in folder")
        return image_links
    
    except Exception as e:
        logging.error(f"Error fetching images from folder: {str(e)}")
        return {}

def create_doc(docs_service, drive_service, title, folder_id=None):
    """Create a new Google Doc and optionally move it to a specified folder."""
    try:
        # First create the document
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        
        # If folder_id is provided, move the document to that folder
        if folder_id:
            try:
                file = drive_service.files().update(
                    fileId=doc_id,
                    addParents=folder_id,
                    fields='id, parents'
                ).execute()
                logging.info(f"Created new Google Doc '{title}' in folder with ID: {doc_id}")
            except Exception as e:
                logging.warning(f"Created document but could not move to folder: {str(e)}")
                # Check if it's a permission error
                if 'insufficientFilePermissions' in str(e) or '403' in str(e):
                    logging.warning(f"Insufficient permissions to add document to folder")
                    logging.info(f"Returning None to trigger local save fallback")
                    return None
        else:
            logging.info(f"Created new Google Doc '{title}' with ID: {doc_id}")
        
        return doc_id
    except Exception as e:
        logging.error(f"Error creating Google Doc: {str(e)}")
        raise

def save_transcription_locally(pages, doc_name, folder_name):
    """
    Save transcription to a local text file when Google Doc creation fails.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = "logs/local_transcriptions"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename
        safe_doc_name = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_doc_name = safe_doc_name.replace(' ', '_')
        output_file = os.path.join(output_dir, f"{safe_doc_name}.txt")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("="*80 + "\n")
            f.write(f"TRANSCRIPTION RECOVERY\n")
            f.write(f"Folder: {folder_name}\n")
            f.write(f"Total Pages: {len(pages)}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("="*80 + "\n\n")
            
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
    Uses small per-item batchUpdate calls with rate limit handling and exponential backoff.
    """
    import time
    from googleapiclient.errors import HttpError
    
    logging.info(f"Preparing document content with {len(pages)} pages...")

    try:
        # Get the current document state
        doc = docs_service.documents().get(documentId=doc_id).execute()
        # Google Docs always ends with a trailing newline; insert before it (endIndex - 1)
        idx = doc['body']['content'][-1]['endIndex'] - 1
        
        # Rate limit tracking
        requests_in_current_minute = 0
        minute_start_time = time.time()
        MAX_REQUESTS_PER_MINUTE = 55  # Stay under the 60 limit with buffer

        for i, item in enumerate(pages[start_idx:], start=start_idx + 1):
            # Check if we need to wait for rate limit reset
            elapsed = time.time() - minute_start_time
            if requests_in_current_minute >= MAX_REQUESTS_PER_MINUTE:
                if elapsed < 60:
                    wait_time = 60 - elapsed + 1  # Add 1 second buffer
                    logging.info(f"Rate limit approaching ({requests_in_current_minute} requests), waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                # Reset counter
                requests_in_current_minute = 0
                minute_start_time = time.time()
            
            max_retries = 5
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    requests_for_item = []

                    # 1) Add filename as Heading 1
                    requests_for_item.append({
                        'insertText': {
                            'location': {'index': idx},
                            'text': f"{item['name']}\n"
                        }
                    })
                    requests_for_item.append({
                        'updateParagraphStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(item['name']) + 1},
                            'paragraphStyle': {
                                'namedStyleType': 'HEADING_1',
                                'alignment': 'START'
                            },
                            'fields': 'namedStyleType,alignment'
                        }
                    })
                    idx += len(item['name']) + 1

                    # 2) Add source link line
                    link_text = f"Source: view:{item['name']}"
                    requests_for_item.append({
                        'insertText': {
                            'location': {'index': idx},
                            'text': link_text + "\n"
                        }
                    })
                    requests_for_item.append({
                        'updateTextStyle': {
                            'range': {'startIndex': idx, 'endIndex': idx + len(link_text)},
                            'textStyle': {
                                'link': {'url': item['webViewLink']},
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 1.0}}},
                                'underline': True
                            },
                            'fields': 'link,foregroundColor,underline'
                        }
                    })
                    idx += len(link_text) + 1

                    # 3) Add raw transcription
                    if item['text']:
                        text_to_insert = item['text'] + "\n\n"
                        requests_for_item.append({
                            'insertText': {
                                'location': {'index': idx},
                                'text': text_to_insert
                            }
                        })
                        requests_for_item.append({
                            'updateParagraphStyle': {
                                'range': {'startIndex': idx, 'endIndex': idx + len(text_to_insert)},
                                'paragraphStyle': {
                                    'namedStyleType': 'NORMAL_TEXT',
                                    'alignment': 'START'
                                },
                                'fields': 'namedStyleType,alignment'
                            }
                        })
                        idx += len(text_to_insert)

                    # Execute this small batch for the item
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests_for_item}).execute()
                    requests_in_current_minute += 1
                    
                    # Re-fetch document to get current end index (prevents index drift)
                    doc = docs_service.documents().get(documentId=doc_id).execute()
                    idx = doc['body']['content'][-1]['endIndex'] - 1
                    
                    logging.info(f"Added transcription for '{item['name']}' to document ({i}/{len(pages)})")
                    break  # Success, exit retry loop

                except HttpError as e:
                    if e.resp.status == 429:  # Rate limit error
                        if attempt < max_retries - 1:
                            logging.warning(f"Rate limit hit for page {i}, attempt {attempt + 1}/{max_retries}. Waiting {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            # Reset rate limit tracking
                            requests_in_current_minute = 0
                            minute_start_time = time.time()
                        else:
                            logging.error(f"Max retries exceeded for page {i} ('{item['name']}'): {str(e)}")
                            raise
                    else:
                        # Non-rate-limit error, don't retry
                        logging.error(f"Error processing page {i} ('{item['name']}'): {str(e)}")
                        raise
                        
                except Exception as e:
                    logging.error(f"Error processing page {i} ('{item['name']}'): {str(e)}")
                    # Try to record the error message text so we don't lose place
                    error_text = f"\n[Error processing this page: {str(e)}]\n"
                    try:
                        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [
                            {'insertText': {'location': {'index': idx}, 'text': error_text}}
                        ]}).execute()
                        requests_in_current_minute += 1
                        
                        # Re-fetch document to get current end index
                        doc = docs_service.documents().get(documentId=doc_id).execute()
                        idx = doc['body']['content'][-1]['endIndex'] - 1
                    except Exception as nested:
                        logging.error(f"Failed to write error marker to document: {nested}")
                    break  # Don't retry non-rate-limit errors

        logging.info("Google Doc updated successfully")

    except Exception as e:
        logging.error(f"Critical error in write_to_doc: {str(e)}")
        raise

def main():
    """Main function to recover transcription data and create Google Doc."""
    parser = argparse.ArgumentParser(description='Recovery script to create Google Doc from AI response logs')
    parser.add_argument('log_file', help='Path to the AI response log file')
    parser.add_argument('--doc-title', help='Custom title for the Google Doc (default: derived from log file)')
    parser.add_argument('--folder-id', help='Google Drive folder ID where original images are located and where to upload the recovered doc')
    parser.add_argument('--folder-name', help='Google Drive folder name (used to search for folder if folder-id not provided; also tries to auto-detect from log file)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        logging.info("=== Recovery Script Started ===")
        logging.info(f"Log file: {args.log_file}")
        logging.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Check if log file exists
        if not os.path.exists(args.log_file):
            logging.error(f"Log file not found: {args.log_file}")
            return
        
        # Initialize services first (needed to fetch images from Drive)
        creds = authenticate()
        drive_service, docs_service = init_services(creds)
        
        # Parse the AI response log first to get folder_name from log
        pages, folder_name_from_log = parse_ai_log(args.log_file, image_links=None)
        
        if not pages:
            logging.error("No transcription data found in the log file")
            return
        
        # Determine folder ID (priority: args.folder_id > args.folder_name > folder_name_from_log)
        folder_id = args.folder_id
        folder_name = args.folder_name or folder_name_from_log
        
        if not folder_id and folder_name:
            logging.info(f"Searching for folder by name: {folder_name}")
            folder_id = get_drive_folder_id(drive_service, folder_name)
        
        # Fetch images from the Drive folder to get webViewLinks
        image_links = {}
        if folder_id:
            logging.info(f"Fetching images from Drive folder: {folder_id}")
            image_links = fetch_images_from_folder(drive_service, folder_id)
            if not image_links:
                logging.warning("No images found in folder or error fetching images. Links may not work correctly.")
            else:
                # Re-parse the log with the image links to update webViewLinks
                logging.info("Re-parsing log with Drive folder webViewLinks...")
                pages, _ = parse_ai_log(args.log_file, image_links=image_links)
        else:
            logging.warning("No folder ID provided or found. Source links will use placeholders.")
        
        # Final check for pages (should not fail here, but just in case)
        if not pages:
            logging.error("No transcription data found after processing")
            return
        
        # Count how many pages have real links vs placeholders
        real_links = sum(1 for page in pages if 'placeholder_id_for' not in page['webViewLink'])
        placeholder_links = len(pages) - real_links
        logging.info(f"Successfully parsed {len(pages)} transcriptions")
        logging.info(f"Link status: {real_links} real Google Drive links, {placeholder_links} placeholder links")
        
        # Create document title
        if args.doc_title:
            doc_title = args.doc_title
        else:
            # Create title based on first and last image names
            first_image = pages[0]['name']
            last_image = pages[-1]['name']
            doc_title = f"transcription_{first_image[:-4]}-{last_image[:-4]}_recovered"
        
        # Create the Google Doc
        logging.info(f"Creating Google Doc: {doc_title}")
        doc_id = create_doc(docs_service, drive_service, doc_title, folder_id)
        
        if doc_id is None:
            # Permission error - save locally instead
            logging.warning("Cannot create Google Doc due to insufficient permissions")
            logging.info("Saving transcription to local file instead...")
            local_file = save_transcription_locally(pages, doc_title, folder_name)
            logging.info(f"=== Recovery Completed (Local Save) ===")
            logging.info(f"✓ Transcription saved locally: {local_file}")
            logging.info(f"✓ Processed {len(pages)} images successfully")
        else:
            # Write content to the document
            write_to_doc(docs_service, doc_id, pages)
            
            logging.info(f"=== Recovery Completed Successfully ===")
            logging.info(f"Document created with {len(pages)} images")
            logging.info(f"Document ID: {doc_id}")
            logging.info(f"Document URL: https://docs.google.com/document/d/{doc_id}/edit")
        
    except Exception as e:
        logging.error(f"Recovery failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()