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
- Set IMAGE_START_NUMBER to specify starting image (e.g., 101 for image00101.jpg or 101.jpg)
- Set IMAGE_COUNT to specify how many consecutive images to process (e.g., 5 will process image00101.jpg through image00105.jpg or 101.jpg through 105.jpg)
- Files must follow one of these patterns: 
  * image (N).jpg where N is a number (e.g., image (7).jpg, image (10).jpg)
  * imageXXXXX.jpg where XXXXX is a 5-digit number (e.g., image00101.jpg)
  * XXXXX.jpg where XXXXX is a number (e.g., 52.jpg, 102.jpg)
  * image - YYYY-MM-DDTHHMMSS.mmm.jpg (timestamp format, e.g., image - 2025-07-20T112914.366.jpg)
- The script will fetch up to MAX_IMAGES from Google Drive, then filter based on these parameters

Test mode processes only the first TEST_IMAGE_COUNT images. Max images processed is capped by MAX_IMAGES.

Retry Mode:
- Set RETRY_MODE = True to process only specific failed images from previous runs
- Add failed image filenames to RETRY_IMAGE_LIST (can be with or without "image - " prefix)
- When retry mode is enabled, IMAGE_START_NUMBER and IMAGE_COUNT are ignored
- Useful for reprocessing images that failed due to network timeouts or server errors
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
#DRIVE_FOLDER_ID = "1Hqd3Kgys9yyDg_iXlXDQm1GNBLVABVVX"
#FOLDER_NAME = "1888-1924 Турилче Вербивки Метрич Книга (487-1-545)"
#DRIVE_FOLDER_ID = "1ka-1tUaGDc55BGihPm9q56Yskfbm6m-a"
#FOLDER_NAME = "1874-1936 Турильче Вербивка записи о смерти 487-1-729-смерті"
DRIVE_FOLDER_ID = "1-IkGrRBc6Fr-OsabPWmnuZt2qbYS0C5S"
FOLDER_NAME = "1848-1896 МК Вовкивцы Борщев рождения"

REGION = "global"  # Changed to global as per sample
OCR_MODEL_ID = "gemini-2.5-pro"
ADC_FILE = "application_default_credentials.json"  # ADC file with refresh token
TEST_MODE = True
TEST_IMAGE_COUNT = 2
MAX_IMAGES = 1000  # Increased to 1000 to fetch more images
IMAGE_START_NUMBER = 200  # Starting image number (e.g., 101 for image00101.jpg or 101.jpg)
IMAGE_COUNT = 300  # Number of images to process starting from IMAGE_START_NUMBER

# RETRY MODE - Set to True to retry specific failed images
RETRY_MODE = True
RETRY_IMAGE_LIST = [
    # Complete list of all images with "No response text received from Vertex AI" errors
    # Extracted from logs 20250720*, 20250721*, 20250722* - Total: 48 images
    "2025-07-20T112519.385.jpg",
    "2025-07-20T112522.938.jpg",
    "2025-07-20T112528.377.jpg",
    "2025-07-20T112544.332.jpg",
    "2025-07-20T112551.367.jpg",
    "2025-07-20T112553.471.jpg",
    "2025-07-20T112601.854.jpg",
    "2025-07-20T112609.044.jpg",
    "2025-07-20T112620.042.jpg",
    "2025-07-20T112622.286.jpg",
    "2025-07-20T112628.271.jpg",
    "2025-07-20T112639.662.jpg",
    "2025-07-20T112709.093.jpg",
    "2025-07-20T112712.160.jpg",
    "2025-07-20T112727.715.jpg",
    "2025-07-20T112732.117.jpg",
    "2025-07-20T112734.448.jpg",
    "2025-07-20T112747.332.jpg",
    "2025-07-20T112751.226.jpg",
    "2025-07-20T112755.647.jpg",
    "2025-07-20T112759.892.jpg",
    "2025-07-20T112807.803.jpg",
    "2025-07-20T112809.729.jpg",
    "2025-07-20T112811.697.jpg",
    "2025-07-20T112830.064.jpg",
    "2025-07-20T112835.861.jpg",
    "2025-07-20T112855.914.jpg",
    "2025-07-20T112916.700.jpg",
    "2025-07-20T112939.521.jpg",
    "2025-07-20T112946.336.jpg",
    "2025-07-20T113026.573.jpg",
    "2025-07-20T113040.781.jpg",
    "2025-07-20T113128.157.jpg",
    "2025-07-20T113233.281.jpg",
    "2025-07-20T113259.045.jpg",
    "2025-07-20T113335.360.jpg",
    "2025-07-20T113339.509.jpg",
    "2025-07-20T113351.813.jpg",
    "2025-07-20T113359.967.jpg",
    "2025-07-20T113410.088.jpg",
    "2025-07-20T113412.034.jpg",
    "2025-07-20T113416.201.jpg",
    "2025-07-20T113433.524.jpg",
    "2025-07-20T113507.088.jpg",
    "2025-07-20T113510.674.jpg",
    "2025-07-20T113516.313.jpg",
    "2025-07-20T113544.156.jpg",
    "2025-07-20T113621.536.jpg"
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
INSTRUCTION_BIRTH_RECORD = """Extract and transcribe all text from this handwritten 18th-century birth record from eastern Ukraine, written in Latin or Ukrainian. 
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

# LLM Instruction for transcription
INSTRUCTION = """Extract and transcribe all text from this handwritten 18th-century birth record from eastern Ukraine, written in Latin or Ukrainian. 
    The record contains the following fields: year (usually top left corner), page (usually top right corner), dateOfBirth (source is in in format like  day of birth, day of baptism, month in latin and year,  
    example of source: 14 14 septembris 1889 ), house number, short village name (e.g 21 Turyl), child's name, obstetrician's name, religion, 
    parents names (e.g "Onuphreus filius Stachii Martyniuk et Josephae Humeniuk - Eudoxia filia Michaii Hanczaryk et Parascevy Husak", extract full exact info as is), 
    godfather (patrini, e.g. Basilius Federczuk & Catarina uxor Joannis Lazaruk , agricola ), 
    Notes (e.g include info if child is illigitimate and other notes). 
    list of some villages related to this book: Wolkiwci (Волківці). 
    Some common surnames:  Baziuk, Basiuk, Lazaruk, Szewczuk, Bijak, Juskiw, Szepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick,   

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



# LLM Instruction for transcription
INSTRUCTION_DEATH_RECORD = """Extract and transcribe all text from this handwritten 18th or 19th-century death record from eastern Ukraine, written in Latin or Ukrainian.

The record contains the following fields: year (usually top left corner), page (usually top right corner), date of death, date of burial, house number, short village name (e.g 21 Turyl), full name of the deceased, religion, sex, age, reason/cause of death, Notes, and raw info.

Specifically, look for:

Year, Page: (Usually top left and top right corners, respectively).
Date of death, Date of burial: (Source might be in a format like "obiit 14 septembris 1889", "sepultus 16 septembris 1889").
House Number: (e.g., No 21, Domus 45).
Village Name: (e.g., Turyl, Werbiwka).
Full name: (Of the deceased, including any given marital status, profession, or parentage if indicated, e.g., "Joannes Kowalczuk filius Mathiae", "Maria Nowak vidua Josephi Nowak", "Anna Szewczuk uxor Petri").
Religion: (e.g., Graeco Catholica, Romano Catholica).
Sex: (e.g., masculi/masculinus for male, feminae/femininus for female).
Age: (Often in years, months, or days, e.g., aetatis suae 60 annorum, 2 menses, infans).
Reason/Cause of Death: (e.g., senectute - old age, morbus - illness, dysenteria - dysentery, pestis - plague, ignota - unknown).
Burial Details: (e.g., name of the officiating priest, witnesses present at burial, if explicitly stated and distinct from other notes).
Notes: (Any other relevant information such as marital status if not included in the name, specific profession, or unusual circumstances surrounding the death).
List of some villages related to this book/region: Werbiwka, Turylche, Pidpilipje, Zalesje, Slobodka, Pukljaki.
Some common surnames: Lazaruk, Szewczuk, Babij, Kowalczuk, Baziuk, Juskiw, Szepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick.

Follow these instructions:

Transcription Accuracy:

Transcribe the text exactly as it appears, preserving Latin or Ukrainian spelling, abbreviations, and historical orthography.
If handwriting is unclear, provide the most likely transcription and note uncertainty in square brackets, e.g., [illegible] or [possibly Anna].
Handle Latin-specific characters (e.g., æ, œ) and common abbreviations (e.g., "obiit" for "died", "sepultus" for "buried", "aet." for "aetatis").
Structured Output:

Format the output for each record with the following fields (on new line):
year, page, (common page info)
Then for each row (every death record):
full deceased's name, followed by their age and date of death in between triple star (don't put name of field, just put value, start with deceased's name): e.g. ***Joannes Kowalczuk, aet. 70, 10/10/1890***
extracted "field: value" on new line: date_of_death, date_of_burial, house_number, village_name, deceased_name, religion, sex, age, cause_of_death, burial_details, notes (any extra info), raw_info.
raw_info must include the full text related to a row in original format as close to the source row as possible.
Historical Context:

Expect 18th-century Latin/Ukrainian handwriting with potential flourishes, ligatures, or faded ink.
Dates may use Roman numerals (e.g., XVII for 17) or Latin month names (e.g., Januarius, Februarius).
Names may include patronymics or Latinized forms (e.g., "Petri" for Peter, "Mariae" for Maria). Pay attention to titles like filius (son), filia (daughter), uxor (wife), vidua (widow), caelebs (bachelor), virgo (spinster).
Error Handling:

If text is ambiguous, prioritize the most contextually appropriate interpretation based on typical death record structure.
Ignore irrelevant text (e.g., marginal notes, page numbers) unless it clearly relates to the specified fields."""

# ------------------------------------------------------------------
#    list of some villages related to this book: Werbiwka, Turylche, Pidpilipje, Zalesje, Slobodka, Pukljaki. 
#    Some common surnames: Lazaruk, Shewczuk, Babij, Kowalczuk, Basiuk, Juskiw, Sczepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick,   

INSTRUCTION_MARRIAGES = """Extract and transcribe all text from this handwritten 18th-century marriage records from eastern Ukraine, written in Latin or Ukrainian. 
    The record typically contains the following fields - table columns from left to right: 
    mensis (month, year, date of marriage), 
    Sponsus info - nrus domus (house number with sometimes short village name e.g 21 Turyl), 
    name (including names of parents and address e.g  Gregorius filiusBasilius Federczuk & Catarina uxor Joannis Lazaruk ), 
    religion, aetas (age), marriage status(coelebs, viduus),
    Sponsa info - same info/columns as for Sponsus;
    Testes info & Conditio - e.g +Nikitas Sofroniek +Ignatus Patyga 
    Notes (other notes usually below row). 
    list of some villages related to this book: Wolkiwci (Волківці). 
    Some common surnames:  Baziuk, Basiuk, Bijak, Juskiw, Szepanowski, Martynuk, Wisnuj, Bojeczok, Zachidnick,   

Follow these instructions:

1. **Transcription Accuracy**:
  - Transcribe the text exactly as it appears, preserving Latin or Ukrainian spelling, abbreviations, and historical orthography.
  - If handwriting is unclear, provide the most likely transcription and note uncertainty in square brackets, e.g., [illegible] or [possibly Anna].
  - Handle Latin-specific characters (e.g., æ, œ) and common abbreviations (e.g., \"Joannes\" for \"Johannes\").

2. **Structured Output**:
  - Format the output for each record with the following fields (on new line):  
    year, page, (common page info)
        then for each row (every marriage record): 
        full groom name with fathers name in between triple star (dont put name of field, just put value, start with child name) : 
        ***Name Fathers Name Surname DOB*** e.g.  ***Gregorii Ignatus Lazaruk 14/09/1889***
        full bride name with fathers name in between triple star (dont put name of field, just put value, start with child name) : 
        ***Name Fathers Name Surname DOB*** e.g.  ***Maria Onuphreus Martyniuk 14/09/1889***
        then extracted "field: value" on new line: 
        dateofmarriage (format: DD/MM/YYYY), 
        house_number, village_name, groom_name, groom_age, groom_dob (derived year of birth of groom), groom_parents, religion, marriage_status,
        bride_name, bride_age, bride_dob (derived year of birth of bride), bride_parents (including village and house number of found in parents info), religion, marriage_status,
        testes, notes (any extra info), rawinfo.
last column rawinfo must include full text related to a row in original format as close to source row as possible with related notes

3. **Historical Context**:
  - Expect 18th-century Latin or Ukrainian handwriting with potential flourishes, ligatures, or faded ink.
  - Dates may use Roman numerals (e.g., XVII for 17) or Latin month names (e.g., Januarius, Februarius).
  - Names may include patronymics or Latinized forms (e.g., \"Petri\" for Peter, \"Mariae\" for Maria).

4. **Error Handling**:
  - If text is ambiguous, prioritize the most contextually appropriate interpretation based on typical birth record structure.
  - Ignore irrelevant text (e.g., marginal notes, page numbers) unless it clearly relates to the specified fields."""

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
    
    # Regex pattern for timestamp format: image - YYYY-MM-DDTHHMMSS.mmm.jpg
    timestamp_pattern = re.compile(r'^image - (\d{4}-\d{2}-\d{2}T\d{6}\.\d{3})\.jpg$')
    
    for img in all_images:
        filename = img['name']
        number = None
        timestamp_match = None
        
        # Check for timestamp pattern first
        timestamp_match = timestamp_pattern.match(filename)
        if timestamp_match:
            timestamp_images.append(img)
            continue
        
        # Check if filename matches the pattern image (N).jpg
        if filename.startswith('image (') and filename.endswith(').jpg'):
            try:
                # Extract the number from filename (e.g., "image (7).jpg" -> 7)
                start_idx = filename.find('(') + 1
                end_idx = filename.find(')')
                number_str = filename[start_idx:end_idx]
                number = int(number_str)
            except (ValueError, IndexError):
                continue
        
        # Check if filename matches the pattern imageXXXXX.jpg
        elif filename.startswith('image') and filename.endswith('.jpg') and not '(' in filename and not ' - ' in filename:
            try:
                # Extract the number from filename (e.g., "image00101.jpg" -> 101)
                number_str = filename[5:-4]  # Remove "image" prefix and ".jpg" suffix
                number = int(number_str)
            except ValueError:
                continue
        
        # Check if filename matches the pattern XXXXX.jpg (like 52.jpg, 102.jpg)
        elif filename.endswith('.jpg') and not filename.startswith('image'):
            try:
                # Extract the number from filename (e.g., "52.jpg" -> 52, "102.jpg" -> 102)
                number_str = filename[:-4]  # Remove ".jpg" suffix
                number = int(number_str)
            except ValueError:
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
            if filename.startswith('image (') and filename.endswith(').jpg'):
                # Extract number from "image (N).jpg" format
                start_idx = filename.find('(') + 1
                end_idx = filename.find(')')
                number_str = filename[start_idx:end_idx]
            elif filename.startswith('image') and filename.endswith('.jpg') and not '(' in filename and not ' - ' in filename:
                # Extract number from "imageXXXXX.jpg" format
                number_str = filename[5:-4]  # Remove "image" prefix and ".jpg" suffix
            else:
                # Extract number from "XXXXX.jpg" format
                number_str = filename[:-4]  # Remove ".jpg" suffix
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
                if filename.startswith('image (') and filename.endswith(').jpg'):
                    start_idx = filename.find('(') + 1
                    end_idx = filename.find(')')
                    number_str = filename[start_idx:end_idx]
                elif filename.startswith('image') and filename.endswith('.jpg') and not '(' in filename and not ' - ' in filename:
                    number_str = filename[5:-4]
                else:
                    number_str = filename[:-4]
                try:
                    return (0, int(number_str))  # 0 to sort numbered images first
                except ValueError:
                    return (0, 0)
        
        filtered_images.sort(key=mixed_sorting_key)
    
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
