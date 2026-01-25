"""
Context Collection Step

Step 2: Collects context information (villages, surnames, archive info).
Supports optional title page extraction (Phase 4) and manual entry.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.steps.base_step import WizardStep
from wizard.i18n import t


class ContextCollectionStep(WizardStep):
    """Step 2: Collect context information."""
    
    def __init__(self, controller):
        """Initialize context collection step."""
        super().__init__(controller)
        self.console = Console()
    
    def run(self) -> Dict[str, Any]:
        """
        Collect context information.
        
        Supports both title page extraction (Phase 4) and manual entry.
        
        Returns:
            Dictionary with context data:
            - archive_reference
            - document_type
            - date_range
            - main_villages (list of dicts with 'name' and 'variants')
            - additional_villages (list of dicts)
            - common_surnames (list of strings)
            - title_page_filename (optional)
        """
        lang = self.controller.get_language()
        self.console.print(f"\n[bold cyan]{t('context.title', lang)}[/bold cyan]")
        self.console.print(f"[dim]{t('context.description', lang)}[/dim]\n")
        
        # Get mode and config from previous step
        mode = self.controller.get_data("mode", "local")
        mode_data = self.controller.get_data(mode, {})
        
        # Ask if user wants to extract from title page (both modes support this now)
        # Use select instead of confirm for better reliability and clarity
        # Default is Yes (first choice)
        use_title_page_choice = questionary.select(
            t('context.title_page_prompt', lang),
            choices=[
                questionary.Choice(t('context.title_page_yes', lang), value=True),
                questionary.Choice(t('context.title_page_no', lang), value=False),
            ]
        ).ask()
        
        use_title_page = use_title_page_choice if use_title_page_choice is not None else True
        
        if use_title_page:
            # Try title page extraction
            context = self._extract_and_review_title_page(mode, mode_data)
        else:
            # Manual collection
            context = self._collect_context_manually()
        
        return {"context": context}
    
    def _collect_context_manually(self) -> Dict[str, Any]:
        """
        Collect context information manually via prompts.
        
        Returns:
            Context dictionary
        """
        lang = self.controller.get_language()
        context = {}
        
        # Archive reference
        self.console.print(f"[bold]{t('context.archive_reference_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.archive_reference_example', lang)}[/dim]")
        archive_ref = questionary.text(
            t('context.archive_reference_prompt', lang),
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['archive_reference'] = archive_ref.strip() if archive_ref else ""
        
        # Document type
        self.console.print(f"\n[bold]{t('context.document_type_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.document_type_example', lang)}[/dim]")
        doc_type = questionary.text(
            t('context.document_type_prompt', lang),
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['document_type'] = doc_type.strip() if doc_type else ""
        
        # Date range
        self.console.print(f"\n[bold]{t('context.date_range_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.date_range_example', lang)}[/dim]")
        date_range = questionary.text(
            t('context.date_range_prompt', lang),
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['date_range'] = date_range.strip() if date_range else ""
        
        # Main villages
        self.console.print(f"\n[bold]{t('context.main_villages_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.main_villages_hint1', lang)}[/dim]")
        self.console.print(f"[dim]{t('context.main_villages_hint2', lang)}[/dim]")
        self.console.print(f"[dim]{t('context.main_villages_hint3', lang)}[/dim]")
        
        main_villages = self._collect_villages(t('context.main_villages_title', lang))
        context['main_villages'] = main_villages
        
        # Additional villages
        self.console.print(f"\n[bold]{t('context.additional_villages_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.additional_villages_hint', lang)}[/dim]")
        has_additional = questionary.confirm(
            t('context.additional_villages_prompt', lang),
            default=False
        ).ask()
        
        if has_additional:
            additional_villages = self._collect_villages(t('context.additional_villages_title', lang))
            context['additional_villages'] = additional_villages
        else:
            context['additional_villages'] = []
        
        # Common surnames
        self.console.print(f"\n[bold]{t('context.common_surnames_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('context.common_surnames_hint', lang)}[/dim]")
        has_surnames = questionary.confirm(
            t('context.common_surnames_prompt', lang),
            default=False
        ).ask()
        
        if has_surnames:
            surnames = self._collect_surnames()
            context['common_surnames'] = surnames
        else:
            context['common_surnames'] = []
        
        return context
    
    def _collect_villages(self, label: str) -> List[Dict[str, Any]]:
        """
        Collect village information with variants.
        
        Args:
            label: Label for the prompt (e.g., "Main Villages")
            
        Returns:
            List of village dictionaries with 'name' and 'variants' keys
        """
        lang = self.controller.get_language()
        villages = []
        
        while True:
            village_input = questionary.text(
                t('context.village_prompt', lang),
                default=""
            ).ask()
            
            if not village_input or not village_input.strip():
                break
            
            village_input = village_input.strip()
            
            # Parse village name and variants
            # Format: "VillageName (variant1, variant2)" or just "VillageName"
            match = re.match(r'^(.+?)\s*\((.+?)\)$', village_input)
            if match:
                name = match.group(1).strip()
                variants_str = match.group(2).strip()
                variants = [v.strip() for v in variants_str.split(',') if v.strip()]
            else:
                name = village_input
                variants = []
            
            villages.append({
                'name': name,
                'variants': variants
            })
            
            lang = self.controller.get_language()
            self.console.print(f"  [green]✓[/green] {t('context.added', lang, item=name)}" + 
                             (f" (variants: {', '.join(variants)})" if variants else ""))
        
        return villages
    
    def _collect_surnames(self) -> List[str]:
        """
        Collect common surnames.
        
        Returns:
            List of surname strings
        """
        lang = self.controller.get_language()
        surnames = []
        
        while True:
            surname_input = questionary.text(
                t('context.surname_prompt', lang),
                default=""
            ).ask()
            
            if not surname_input or not surname_input.strip():
                break
            
            surnames.append(surname_input.strip())
            lang = self.controller.get_language()
            self.console.print(f"  [green]✓[/green] {t('context.added', lang, item=surname_input.strip())}")
        
        return surnames
    
    def _extract_and_review_title_page(self, mode: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract context from title page and allow user review/accept/reject.
        
        Returns:
            Final context dictionary (extracted + user edits, or manual entry)
        """
        try:
            # Initialize services first (needed for both getting title page info and extraction)
            if mode == "googlecloud":
                # Initialize Google services for title page extraction
                self.console.print("[dim]Initializing Google services for title page extraction...[/dim]")
                try:
                    services = self._initialize_google_services(config)
                    if not services:
                        self.console.print("[yellow]⚠ Failed to initialize Google services. Falling back to manual entry.[/yellow]")
                        return self._collect_context_manually()
                    
                    drive_service, genai_client = services
                    # Add services to config for use in extraction
                    config['drive_service'] = drive_service
                    config['genai_client'] = genai_client
                except Exception as e:
                    self.console.print(f"[yellow]⚠ Error initializing Google services: {e}[/yellow]")
                    logging.error(f"Error initializing Google services for title page extraction: {e}", exc_info=True)
                    return self._collect_context_manually()
            
            # Get title page information (now we have services if needed)
            if mode == "local":
                title_page_info = self._get_title_page_for_local(config.get('image_dir'))
            elif mode == "googlecloud":
                drive_service = config.get('drive_service')
                if not drive_service:
                    self.console.print("[yellow]⚠ Drive service not available. Falling back to manual entry.[/yellow]")
                    return self._collect_context_manually()
                
                title_page_info = self._get_title_page_for_googlecloud(
                    config.get('drive_folder_id'),
                    drive_service
                )
            else:
                self.console.print(f"[yellow]Unknown mode: {mode}. Falling back to manual entry.[/yellow]")
                return self._collect_context_manually()
            
            if not title_page_info:
                self.console.print("[yellow]⚠ Title page selection cancelled. Falling back to manual entry.[/yellow]")
                return self._collect_context_manually()
            
            # Initialize extractor
            from wizard.title_page_extractor import TitlePageExtractor
            
            if mode == "local":
                api_key = config.get('api_key')
                if not api_key:
                    self.console.print("[yellow]⚠ API key not available. Falling back to manual entry.[/yellow]")
                    return self._collect_context_manually()
                
                extractor = TitlePageExtractor(api_key=api_key, model_id=config.get('ocr_model_id', 'gemini-3-flash-preview'))
            else:  # googlecloud
                # Use already initialized services
                genai_client = config.get('genai_client')
                if not genai_client:
                    self.console.print("[yellow]⚠ Gemini client not available. Falling back to manual entry.[/yellow]")
                    return self._collect_context_manually()
                
                extractor = TitlePageExtractor(genai_client=genai_client, model_id=config.get('ocr_model_id', 'gemini-3-flash-preview'))
            
            # Extract context
            lang = self.controller.get_language()
            self.console.print(f"\n[dim]{t('context.extracting', lang)}[/dim]")
            extracted = extractor.extract(title_page_info, mode, config)
            
            if not extracted:
                self.console.print("[yellow]⚠ Title page extraction failed. Falling back to manual entry.[/yellow]")
                return self._collect_context_manually()
            
            # Show extracted data and allow review
            return self._review_extracted_context(extracted, title_page_info)
            
        except Exception as e:
            self.console.print(f"[red]Error during title page extraction: {e}[/red]")
            logging.error(f"Title page extraction error: {e}", exc_info=True)
            return self._collect_context_manually()
    
    def _review_extracted_context(self, extracted: Dict[str, Any], title_page_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show extracted context and allow user to accept/edit/reject.
        
        Returns:
            Final context dictionary
        """
        lang = self.controller.get_language()
        self.console.print(f"\n[bold cyan]{t('context.extracted_title', lang)}[/bold cyan]")
        self.console.print(f"  {t('context.archive_reference_label', lang)} {extracted.get('archive_reference', 'N/A')}")
        self.console.print(f"  {t('context.document_type_label', lang)} {extracted.get('document_type', 'N/A')}")
        self.console.print(f"  {t('context.date_range_label', lang)} {extracted.get('date_range', 'N/A')}")
        
        main_villages = extracted.get('main_villages', [])
        if main_villages:
            self.console.print(f"  {t('context.main_villages_label', lang)} {', '.join(main_villages)}")
        else:
            self.console.print(f"  {t('context.main_villages_none', lang)}")
        
        additional_villages = extracted.get('additional_villages', [])
        if additional_villages:
            self.console.print(f"  {t('context.additional_villages_label', lang)} {', '.join(additional_villages)}")
        
        surnames = extracted.get('common_surnames', [])
        if surnames:
            self.console.print(f"  {t('context.common_surnames_label', lang)} {', '.join(surnames)}")
        
        # Ask user what to do
        action = questionary.select(
            t('context.review_prompt', lang),
            choices=[
                questionary.Choice(t('context.review_accept', lang), value="accept"),
                questionary.Choice(t('context.review_edit', lang), value="edit"),
                questionary.Choice(t('context.review_reject', lang), value="reject"),
            ]
        ).ask()
        
        if action == "accept":
            return self._format_extracted_context(extracted, title_page_info)
        
        elif action == "edit":
            return self._edit_extracted_context(extracted, title_page_info)
        
        else:  # reject
            return self._collect_context_manually()
    
    def _edit_extracted_context(self, extracted: Dict[str, Any], title_page_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allow user to edit individual fields from extracted context.
        
        Returns:
            Edited context dictionary
        """
        final_context = {}
        
        # Archive reference
        archive_ref = questionary.text(
            "Archive Reference:",
            default=extracted.get('archive_reference', '')
        ).ask()
        final_context['archive_reference'] = archive_ref.strip() if archive_ref else ""
        
        # Document type
        doc_type = questionary.text(
            "Document Type:",
            default=extracted.get('document_type', '')
        ).ask()
        final_context['document_type'] = doc_type.strip() if doc_type else ""
        
        # Date range
        date_range = questionary.text(
            "Date Range:",
            default=extracted.get('date_range', '')
        ).ask()
        final_context['date_range'] = date_range.strip() if date_range else ""
        
        # Main villages (allow editing list)
        main_villages_text = questionary.text(
            "Main Villages (comma-separated, or 'Village (variant1, variant2)' format):",
            default=', '.join(extracted.get('main_villages', []))
        ).ask()
        
        # Parse villages (simple for now - just split by comma)
        # User can enter "Village1, Village2" or "Village1 (var1, var2), Village2"
        main_villages = []
        if main_villages_text:
            for village_str in main_villages_text.split(','):
                village_str = village_str.strip()
                if not village_str:
                    continue
                
                # Try to parse variant format
                match = re.match(r'^(.+?)\s*\((.+?)\)$', village_str)
                if match:
                    name = match.group(1).strip()
                    variants_str = match.group(2).strip()
                    variants = [v.strip() for v in variants_str.split(',') if v.strip()]
                    main_villages.append({'name': name, 'variants': variants})
                else:
                    main_villages.append({'name': village_str, 'variants': []})
        
        final_context['main_villages'] = main_villages
        
        # Additional villages
        additional_villages_text = questionary.text(
            "Additional Villages (comma-separated, optional):",
            default=', '.join(extracted.get('additional_villages', []))
        ).ask()
        
        additional_villages = []
        if additional_villages_text:
            for village_str in additional_villages_text.split(','):
                village_str = village_str.strip()
                if not village_str:
                    continue
                
                match = re.match(r'^(.+?)\s*\((.+?)\)$', village_str)
                if match:
                    name = match.group(1).strip()
                    variants_str = match.group(2).strip()
                    variants = [v.strip() for v in variants_str.split(',') if v.strip()]
                    additional_villages.append({'name': name, 'variants': variants})
                else:
                    additional_villages.append({'name': village_str, 'variants': []})
        
        final_context['additional_villages'] = additional_villages
        
        # Common surnames
        surnames_text = questionary.text(
            "Common Surnames (comma-separated, optional):",
            default=', '.join(extracted.get('common_surnames', []))
        ).ask()
        final_context['common_surnames'] = [
            s.strip() for s in surnames_text.split(',') if s.strip()
        ] if surnames_text else []
        
        # Add title page filename
        final_context['title_page_filename'] = title_page_info.get('filename')
        
        return final_context
    
    def _format_extracted_context(self, extracted: Dict[str, Any], title_page_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format extracted context into final structure.
        
        Converts extracted data (which may have simple lists) into
        the structured format expected by the wizard.
        """
        # Convert simple village strings to VillageInfo objects
        main_villages = []
        for village in extracted.get('main_villages', []):
            if isinstance(village, str):
                main_villages.append({'name': village, 'variants': []})
            else:
                main_villages.append(village)
        
        additional_villages = []
        for village in extracted.get('additional_villages', []):
            if isinstance(village, str):
                additional_villages.append({'name': village, 'variants': []})
            else:
                additional_villages.append(village)
        
        return {
            'archive_reference': extracted.get('archive_reference', ''),
            'document_type': extracted.get('document_type', ''),
            'date_range': extracted.get('date_range', ''),
            'main_villages': main_villages,
            'additional_villages': additional_villages,
            'common_surnames': extracted.get('common_surnames', []),
            'title_page_filename': title_page_info.get('filename'),
        }
    
    def _get_title_page_for_local(self, image_dir: str) -> Optional[Dict[str, Any]]:
        """
        Get title page file path for LOCAL mode.
        
        Args:
            image_dir: Directory containing images
            
        Returns:
            Dictionary with 'filename' and 'path' keys, or None if cancelled
        """
        if not image_dir or not os.path.isdir(image_dir):
            self.console.print(f"[red]Image directory not found: {image_dir}[/red]")
            return None
        
        # List image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        image_files = [
            f for f in os.listdir(image_dir)
            if os.path.splitext(f.lower())[1] in image_extensions
        ]
        
        if not image_files:
            self.console.print(f"[yellow]No image files found in {image_dir}[/yellow]")
            return None
        
        # Let user select or enter filename
        lang = self.controller.get_language()
        enter_manually_text = t('context.enter_filename_manually', lang)
        choices = image_files + [enter_manually_text]
        selected = questionary.select(
            t('context.title_page_select', lang),
            choices=choices
        ).ask()
        
        if selected == enter_manually_text:
            filename = questionary.text(
                t('context.title_page_filename_prompt', lang),
            ).ask()
            if not filename:
                return None
        else:
            filename = selected
        
        # Validate file exists
        file_path = os.path.join(image_dir, filename)
        if not os.path.exists(file_path):
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return None
        
        return {
            'filename': filename,
            'path': file_path
        }
    
    def _initialize_google_services(self, config: Dict[str, Any]) -> Optional[tuple]:
        """
        Initialize Google Drive and Vertex AI services for title page extraction.
        
        Args:
            config: Configuration dictionary with Google Cloud settings
            
        Returns:
            Tuple of (drive_service, genai_client) or None if failed
        """
        try:
            # Import required modules
            from google.auth import default
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            import json
            import os
            from googleapiclient.discovery import build
            import httplib2
            from google_auth_httplib2 import AuthorizedHttp
            from google import genai
            import vertexai
            
            # Get ADC file path
            adc_file = config.get('adc_file', 'application_default_credentials.json')
            if not os.path.exists(adc_file):
                logging.error(f"ADC file not found: {adc_file}")
                return None
            
            # Load credentials
            with open(adc_file, 'r') as f:
                creds_data = json.load(f)
            
            # Required scopes for Drive and Vertex AI
            scopes = [
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/cloud-platform"
            ]
            
            # Check if it's OAuth user credentials or service account
            if 'refresh_token' in creds_data:
                # OAuth user credentials
                creds = Credentials.from_authorized_user_info(creds_data, scopes=scopes)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            elif 'client_email' in creds_data:
                # Service account
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_file(adc_file)
            else:
                logging.error("Unrecognized credential format")
                return None
            
            # Initialize Vertex AI
            project_id = config.get('project_id')
            region = config.get('region', 'global')
            
            vertexai.init(
                project=project_id,
                location=region,
                credentials=creds
            )
            
            # Create genai client
            genai_client = genai.Client(
                vertexai=True,
                project=project_id,
                location=region,
                credentials=creds
            )
            
            # Initialize Drive service
            http_base = httplib2.Http(timeout=60)  # 1 minute timeout for wizard
            http = AuthorizedHttp(creds, http=http_base)
            drive_service = build("drive", "v3", http=http)
            
            return drive_service, genai_client
            
        except Exception as e:
            logging.error(f"Error initializing Google services: {e}", exc_info=True)
            return None
    
    def _get_title_page_for_googlecloud(self, drive_folder_id: str, drive_service: Any) -> Optional[Dict[str, Any]]:
        """
        Get title page filename for GOOGLECLOUD mode.
        
        Args:
            drive_folder_id: ID of the Drive folder
            drive_service: Google Drive API service
            
        Returns:
            Dictionary with 'filename' and 'drive_folder_id' keys, or None if cancelled
        """
        try:
            # List files in Drive folder
            query = f"'{drive_folder_id}' in parents and trashed=false"
            results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            files = results.get('files', [])
            
            # Filter for image files
            image_mime_types = {
                'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'
            }
            image_files = [
                f for f in files
                if f.get('mimeType', '').startswith('image/')
            ]
            
            lang = self.controller.get_language()
            if not image_files:
                self.console.print("[yellow]No image files found in Drive folder[/yellow]")
                # Still allow manual entry
                filename = questionary.text(
                    t('context.title_page_filename_manual', lang),
                ).ask()
                if not filename:
                    return None
                return {
                    'filename': filename,
                    'drive_folder_id': drive_folder_id
                }
            
            # Let user select or enter filename
            enter_manually_text = t('context.enter_filename_manually', lang)
            choices = [f['name'] for f in image_files] + [enter_manually_text]
            selected = questionary.select(
                t('context.title_page_select', lang),
                choices=choices
            ).ask()
            
            if selected == enter_manually_text:
                filename = questionary.text(
                    t('context.title_page_filename_prompt', lang),
                ).ask()
                if not filename:
                    return None
            else:
                filename = selected
            
            return {
                'filename': filename,
                'drive_folder_id': drive_folder_id
            }
            
        except Exception as e:
            lang = self.controller.get_language()
            self.console.print(f"[red]Error listing Drive files: {e}[/red]")
            logging.error(f"Error listing Drive files: {e}", exc_info=True)
            # Fallback to manual entry
            filename = questionary.text(
                t('context.title_page_filename_manual', lang),
            ).ask()
            if not filename:
                return None
            return {
                'filename': filename,
                'drive_folder_id': drive_folder_id
            }
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate collected context data.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        context = data.get('context', {})
        
        # Archive reference is required
        if not context.get('archive_reference'):
            errors.append("Archive reference is required")
        
        # Document type is required
        if not context.get('document_type'):
            errors.append("Document type is required")
        
        # Date range is required
        if not context.get('date_range'):
            errors.append("Date range is required")
        
        # At least one main village is required
        main_villages = context.get('main_villages', [])
        if not main_villages:
            errors.append("At least one main village is required")
        
        # Validate village structure
        for i, village in enumerate(main_villages):
            if not isinstance(village, dict):
                errors.append(f"Main village {i+1} must be a dictionary")
            elif 'name' not in village:
                errors.append(f"Main village {i+1} must have a 'name' field")
        
        # Validate additional villages structure
        additional_villages = context.get('additional_villages', [])
        for i, village in enumerate(additional_villages):
            if not isinstance(village, dict):
                errors.append(f"Additional village {i+1} must be a dictionary")
            elif 'name' not in village:
                errors.append(f"Additional village {i+1} must have a 'name' field")
        
        # Validate surnames are strings
        surnames = context.get('common_surnames', [])
        for i, surname in enumerate(surnames):
            if not isinstance(surname, str) or not surname.strip():
                errors.append(f"Surname {i+1} must be a non-empty string")
        
        return len(errors) == 0, errors
