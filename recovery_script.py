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

def parse_ai_log(log_file_path):
    """
    Parse the AI response log file and extract image names, view links, and transcriptions.
    Uses line-by-line parsing for better performance on large files.
    Returns a list of dictionaries with 'name', 'webViewLink', and 'text' keys.
    """
    logging.info(f"Parsing AI log file: {log_file_path}")
    
    pages = []
    folder_name = "Unknown Folder"
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logging.info(f"Processing {len(lines)} lines from log file")
        
        # State tracking for line-by-line parsing
        current_image = None
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
                in_response = False
                in_error = False
                response_lines = []
                
            # Start of AI error
            elif "=== AI Error for " in line and line.endswith(" ==="):
                # Extract image name from the line
                start_idx = line.find("=== AI Error for ") + 17
                end_idx = line.rfind(" ===")
                current_image = line[start_idx:end_idx].strip()
                in_response = False
                in_error = True
                error_message = None
                
            # Start of actual response content
            elif "- Full response:" in line and current_image:
                in_response = True
                response_lines = []
                
            # End of AI response
            elif "=== End AI Response for " in line and current_image:
                if in_response and response_lines:
                    response_text = '\n'.join(response_lines).strip()
                    web_view_link = f"https://drive.google.com/file/d/placeholder_id_for_{current_image.replace(' ', '_')}/view"
                    
                    pages.append({
                        'name': current_image,
                        'webViewLink': web_view_link,
                        'text': response_text
                    })
                    
                    logging.info(f"Extracted transcription for: {current_image}")
                
                current_image = None
                in_response = False
                response_lines = []
                
            # End of AI error
            elif "=== End AI Error for " in line and current_image:
                if in_error and error_message:
                    web_view_link = f"https://drive.google.com/file/d/placeholder_id_for_{current_image.replace(' ', '_')}/view"
                    
                    pages.append({
                        'name': current_image,
                        'webViewLink': web_view_link,
                        'text': f"[Error during transcription: {error_message}]"
                    })
                    
                    logging.info(f"Extracted error entry for: {current_image}")
                
                current_image = None
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
        else:
            logging.info(f"Created new Google Doc '{title}' with ID: {doc_id}")
        
        return doc_id
    except Exception as e:
        logging.error(f"Error creating Google Doc: {str(e)}")
        raise

def write_to_doc(docs_service, doc_id, pages, start_idx=0):
    """
    Write transcribed content to a Google Doc with minimal formatting.
    Uses small per-item batchUpdate calls to avoid precondition/range errors.
    """
    logging.info(f"Preparing document content with {len(pages)} pages...")

    try:
        # Ensure we have the current doc (and its initial length)
        docs_service.documents().get(documentId=doc_id).execute()

        idx = 1  # Start at the beginning of a new/empty doc

        for i, item in enumerate(pages[start_idx:], start=start_idx + 1):
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
                logging.info(f"Added transcription for '{item['name']}' to document")

            except Exception as e:
                logging.error(f"Error processing page {i} ('{item['name']}'): {str(e)}")
                # Try to record the error message text so we don't lose place
                error_text = f"\n[Error processing this page: {str(e)}]\n"
                try:
                    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [
                        {'insertText': {'location': {'index': idx}, 'text': error_text}}
                    ]}).execute()
                    idx += len(error_text)
                except Exception as nested:
                    logging.error(f"Failed to write error marker to document: {nested}")

        logging.info("Google Doc updated successfully")

    except Exception as e:
        logging.error(f"Critical error in write_to_doc: {str(e)}")
        raise

def main():
    """Main function to recover transcription data and create Google Doc."""
    parser = argparse.ArgumentParser(description='Recovery script to create Google Doc from AI response logs')
    parser.add_argument('log_file', help='Path to the AI response log file')
    parser.add_argument('--doc-title', help='Custom title for the Google Doc (default: derived from log file)')
    parser.add_argument('--folder-id', help='Google Drive folder ID to place the document (optional)')
    
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
        
        # Parse the AI response log
        pages, folder_name = parse_ai_log(args.log_file)
        
        if not pages:
            logging.error("No transcription data found in the log file")
            return
        
        # Initialize services
        creds = authenticate()
        drive_service, docs_service = init_services(creds)
        
        # Determine folder ID if not provided
        folder_id = args.folder_id
        if not folder_id:
            folder_id = get_drive_folder_id(drive_service, folder_name)
        
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