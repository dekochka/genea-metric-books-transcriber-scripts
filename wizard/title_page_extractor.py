"""
Title Page Extractor

Extracts context information from title page images using Gemini API.
Supports both LOCAL and GOOGLECLOUD modes.
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types


class TitlePageExtractor:
    """Extracts context from title page images using Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-3-flash-preview", genai_client: Optional[Any] = None):
        """
        Initialize title page extractor.
        
        Args:
            api_key: Gemini API key (for LOCAL mode)
            model_id: Model ID to use (default: gemini-3-flash-preview)
            genai_client: Pre-initialized genai.Client (for GOOGLECLOUD mode)
        """
        self.model_id = model_id
        
        if genai_client:
            # GOOGLECLOUD mode: use provided client
            self.client = genai_client
            self.mode = "googlecloud"
        elif api_key:
            # LOCAL mode: create client with API key
            self.client = genai.Client(api_key=api_key)
            self.mode = "local"
        else:
            raise ValueError("Either api_key or genai_client must be provided")
        
        logging.info(f"TitlePageExtractor initialized for {self.mode} mode with model {model_id}")
    
    def extract(self, title_page_info: Dict[str, Any], mode: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract context information from title page image.
        
        Handles both LOCAL and GOOGLECLOUD modes:
        - LOCAL: Direct file path to image
        - GOOGLECLOUD: Filename in Drive folder, downloads first
        
        Args:
            title_page_info: Dictionary with title page information:
                - For LOCAL: {'filename': 'cover.jpg', 'path': '/path/to/cover.jpg'}
                - For GOOGLECLOUD: {'filename': 'cover.jpg', 'drive_folder_id': '...'}
            mode: 'local' or 'googlecloud'
            config: Configuration dictionary (for Drive service access if needed)
            
        Returns:
            Dictionary with extracted context:
            {
                'archive_reference': str,
                'document_type': str,
                'date_range': str,
                'main_villages': list[str],
                'additional_villages': list[str],
                'common_surnames': list[str],  # May be empty
            }
            Returns None if extraction fails
        """
        try:
            # Load image bytes based on mode
            if mode == "local":
                image_bytes = self._load_image_local(title_page_info.get('path'))
            elif mode == "googlecloud":
                drive_service = config.get('drive_service')
                if not drive_service:
                    logging.error("Drive service not available in config for GOOGLECLOUD mode")
                    return None
                image_bytes = self._load_image_drive(
                    title_page_info.get('filename'),
                    title_page_info.get('drive_folder_id'),
                    drive_service
                )
            else:
                logging.error(f"Unknown mode: {mode}")
                return None
            
            if not image_bytes:
                logging.error("Failed to load image bytes")
                return None
            
            # Extract context from image
            filename = title_page_info.get('filename', 'title_page')
            extracted = self._extract_from_image_bytes(image_bytes, filename)
            
            return extracted
            
        except Exception as e:
            logging.error(f"Error extracting context from title page: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            return None
    
    def _load_image_local(self, image_path: str) -> Optional[bytes]:
        """
        Load image from local file system.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image bytes, or None if failed
        """
        if not image_path or not os.path.exists(image_path):
            logging.error(f"Image file not found: {image_path}")
            return None
        
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading image file {image_path}: {e}")
            return None
    
    def _load_image_drive(self, filename: str, drive_folder_id: str, drive_service) -> Optional[bytes]:
        """
        Load image from Google Drive folder.
        
        Args:
            filename: Name of the file in Drive
            drive_folder_id: ID of the Drive folder
            drive_service: Google Drive API service
            
        Returns:
            Image bytes, or None if failed
        """
        try:
            # Find file in Drive folder
            query = f"name='{filename}' and '{drive_folder_id}' in parents and trashed=false"
            results = drive_service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if not files:
                logging.error(f"File '{filename}' not found in Drive folder {drive_folder_id}")
                return None
            
            file_id = files[0]['id']
            
            # Download file
            from googleapiclient.http import MediaIoBaseDownload
            import io
            
            request = drive_service.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_handle.seek(0)
            return file_handle.read()
            
        except Exception as e:
            logging.error(f"Error downloading image from Drive: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            return None
    
    def _extract_from_image_bytes(self, image_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extract context from image bytes using Gemini API.
        
        Args:
            image_bytes: Image file as bytes
            filename: Image filename (for logging)
            
        Returns:
            Dictionary with extracted context, or None if failed
        """
        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt()
            
            # Determine MIME type from filename
            mime_type = "image/jpeg"
            if filename.lower().endswith('.png'):
                mime_type = "image/png"
            elif filename.lower().endswith('.gif'):
                mime_type = "image/gif"
            elif filename.lower().endswith('.webp'):
                mime_type = "image/webp"
            
            # Create image part
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            
            # Create text prompt part
            text_part = types.Part.from_text(text=prompt)
            
            # Create content with both parts
            content = types.Content(
                role="user",
                parts=[text_part, image_part]  # Order: text first, then image
            )
            
            # Configure generation parameters
            config = types.GenerateContentConfig(
                temperature=0.1,              # Low for consistent extraction
                top_p=0.8,
                seed=0,                      # Deterministic results
                max_output_tokens=4096,       # Sufficient for JSON response
                system_instruction=[types.Part.from_text(text=prompt)],
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2000,     # Lower than transcription
                ),
            )
            
            # Make API call
            logging.info(f"Extracting context from title page: {filename}")
            # Suppress warnings about thought_signature (these are informational from google_genai library)
            import warnings
            import logging as std_logging
            # Suppress both Python warnings and google_genai library warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*thought_signature.*")
                warnings.filterwarnings("ignore", category=UserWarning, module="google_genai")
                # Also suppress logging warnings from google_genai
                old_level = std_logging.getLogger("google_genai.types").level
                std_logging.getLogger("google_genai.types").setLevel(std_logging.ERROR)
                try:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=[content],
                        config=config
                    )
                finally:
                    std_logging.getLogger("google_genai.types").setLevel(old_level)
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') and response.text else ""
            
            if not response_text:
                logging.error("Empty response from Gemini API")
                return None
            
            # Parse JSON from response
            extracted = self._parse_extraction_response(response_text)
            
            return extracted
            
        except Exception as e:
            logging.error(f"Error calling Gemini API for title page extraction: {e}")
            import traceback
            logging.debug(traceback.format_exc())
            return None
    
    def _build_extraction_prompt(self) -> str:
        """
        Build the prompt for context extraction.
        
        Returns:
            Prompt text
        """
        return """You are an expert archivist. Extract the following information from this title page image:

1. Archive reference in format: "Ф. X, оп. Y, спр. Z" or similar
2. Document type (e.g., "Метрична книга про народження")
3. Date range (e.g., "1888-1924" or "1888 (липень - грудень) - 1924")
4. Main village(s) mentioned (list all variations/spellings)
5. Additional villages that may appear (if mentioned)
6. Any common surnames visible (optional)

Return your response as JSON in this format:
{
    "archive_reference": "...",
    "document_type": "...",
    "date_range": "...",
    "main_villages": ["village1", "village2"],
    "additional_villages": ["village3"],
    "common_surnames": ["surname1", "surname2"]
}

IMPORTANT: Return ONLY valid JSON, no additional text or markdown formatting."""
    
    def _parse_extraction_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse Gemini response into structured data.
        
        Handles JSON that may be wrapped in markdown code blocks.
        
        Args:
            response_text: Response text from Gemini API
            
        Returns:
            Dictionary with extracted context, or None if parsing failed
        """
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text.strip()
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate and normalize structure
            result = {
                'archive_reference': data.get('archive_reference', ''),
                'document_type': data.get('document_type', ''),
                'date_range': data.get('date_range', ''),
                'main_villages': data.get('main_villages', []),
                'additional_villages': data.get('additional_villages', []),
                'common_surnames': data.get('common_surnames', []),
            }
            
            # Ensure lists are actually lists
            for key in ['main_villages', 'additional_villages', 'common_surnames']:
                if not isinstance(result[key], list):
                    result[key] = []
            
            return result
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from response: {e}")
            logging.debug(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            logging.error(f"Error parsing extraction response: {e}")
            return None
