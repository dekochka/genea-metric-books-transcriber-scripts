"""
Processing Settings Step

Step 3: Collects processing parameters (image range, batch size, etc.).
"""

import os
import logging
from typing import Any, Dict, Optional
import questionary
from rich.console import Console

from wizard.steps.base_step import WizardStep
from wizard.i18n import t


class ProcessingSettingsStep(WizardStep):
    """Step 3: Collect processing settings."""
    
    def __init__(self, controller):
        """Initialize processing settings step."""
        super().__init__(controller)
        self.console = Console()
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the step and collect user input.
        
        Returns:
            Dictionary with processing settings
        """
        lang = self.controller.get_language()
        self.console.print(f"\n[bold]{t('processing.title', lang)}[/bold]\n")
        
        data = {}
        
        # Prompt template selection
        templates = self._list_available_templates()
        if templates:
            template_choice = questionary.select(
                t('processing.template_prompt', lang),
                choices=[
                    questionary.Choice(
                        f"{t['name']} - {t['description']}",
                        value=t['name']
                    )
                    for t in templates
                ]
            ).ask()
            
            if template_choice:
                data["prompt_template"] = template_choice
        else:
            # Fallback: ask for template name
            template_name = questionary.text(
                t('processing.template_name_prompt', lang),
                default=t('processing.template_name_default', lang)
            ).ask()
            
            if template_name:
                data["prompt_template"] = template_name
        
        # Archive index - auto-generate from archive reference if available
        context = self.controller.get_data("context", {})
        archive_reference = context.get("archive_reference", "")
        
        if archive_reference:
            # Auto-generate archive_index from archive_reference
            # Convert "Ф. 487, оп. 1, спр. 545" to "ф487оп1спр545"
            archive_index = self._normalize_archive_reference(archive_reference)
            data["archive_index"] = archive_index
            self.console.print(f"[dim]{t('processing.archive_index_auto', lang, index=archive_index)}[/dim]")
        else:
            # Fallback: ask user if no archive reference available
            archive_index = questionary.text(
                t('processing.archive_index_prompt', lang),
            ).ask()
            if archive_index:
                data["archive_index"] = archive_index
        
        # Image sorting method - ask FIRST to determine selection logic
        self.console.print(f"\n[dim]{t('processing.sort_method_description', lang)}[/dim]")
        
        # Detect if we can extract numbers from images
        min_max = self._detect_image_number_range()
        can_extract_numbers = min_max is not None
        suggested_start = min_max[0] if min_max else None
        suggested_max = min_max[1] if min_max else None
        
        # Build choices list
        choices = []
        default_value = "name_asc"
        
        # Always include "by number extracted" option - users can use it even if we can't auto-detect
        # (especially useful for GOOGLECLOUD mode where we can't scan files without API access)
        number_extracted_choice = t('processing.sort_method_number_extracted', lang)
        if not can_extract_numbers:
            # Add note that range detection wasn't available
            mode = self.controller.get_data("mode")
            if mode == "googlecloud":
                number_extracted_choice += " (enter number manually)"
        
        choices.append(
            questionary.Choice(
                number_extracted_choice,
                value="number_extracted"
            )
        )
        
        if can_extract_numbers:
            default_value = "number_extracted"  # Default to number extraction when we can detect patterns
        
        # Always include these options
        choices.extend([
            questionary.Choice(
                t('processing.sort_method_name_asc', lang),
                value="name_asc"
            ),
            questionary.Choice(
                t('processing.sort_method_created', lang),
                value="created_date"
            ),
            questionary.Choice(
                t('processing.sort_method_modified', lang),
                value="modified_date"
            ),
        ])
        
        sort_method = questionary.select(
            t('processing.sort_method_prompt', lang),
            choices=choices,
            default=default_value
        ).ask()
        
        if sort_method:
            data["image_sort_method"] = sort_method
        else:
            data["image_sort_method"] = default_value
        
        # Image start number - prompt depends on sort method
        if sort_method == "number_extracted":
            # For number_extracted: use extracted number from filename
            if suggested_start is not None and suggested_max is not None:
                self.console.print(f"[dim]Detected image number range: {suggested_start} - {suggested_max} (from available files)[/dim]")
            elif suggested_start:
                self.console.print(f"[dim]Detected minimum image number: {suggested_start} (from available files)[/dim]")
            else:
                # Can't auto-detect (e.g., GOOGLECLOUD mode), but user can still enter manually
                mode = self.controller.get_data("mode")
                if mode == "googlecloud":
                    self.console.print(f"[dim]Enter the image number from filename (e.g., for 'image00001.jpg' enter 1)[/dim]")
                else:
                    self.console.print(f"[yellow][dim]No numeric patterns detected. Enter image number manually.[/dim][/yellow]")
            
            default_start = str(suggested_start) if suggested_start else t('processing.image_start_default', lang)
            image_start = questionary.text(
                t('processing.image_start_prompt', lang),
                default=default_start
            ).ask()
            
            try:
                data["image_start_number"] = int(image_start) if image_start else (suggested_start or 1)
            except ValueError:
                data["image_start_number"] = suggested_start or 1
        else:
            # For other methods: use position in sorted list (1-indexed)
            total_files = self._count_available_images()
            if total_files:
                self.console.print(f"[dim]Found {total_files} image files. Position-based selection (1-indexed).[/dim]")
            
            image_start = questionary.text(
                t('processing.image_start_position_prompt', lang),
                default="1"
            ).ask()
            
            try:
                data["image_start_number"] = int(image_start) if image_start else 1
            except ValueError:
                data["image_start_number"] = 1
        
        # Image count - calculate max available based on sort method
        max_available = self._calculate_max_available_images(
            data["image_start_number"], 
            sort_method,
            suggested_start,
            suggested_max
        )
        
        # Build prompt with max available info
        if max_available:
            prompt_text = t('processing.image_count_prompt_with_max', lang, max=max_available)
        else:
            prompt_text = t('processing.image_count_prompt', lang)
        
        image_count = questionary.text(
            prompt_text,
        ).ask()
        
        try:
            data["image_count"] = int(image_count) if image_count else 1
        except ValueError:
            data["image_count"] = 1
        
        # Display selected range with file names (using sort method)
        self._display_selected_range(data["image_start_number"], data["image_count"], sort_method, lang)
        
        # Batch size (only for googlecloud mode)
        mode = self.controller.get_data("mode")
        if mode == "googlecloud":
            batch_size = questionary.text(
                t('processing.batch_size_prompt', lang),
                default=t('processing.batch_size_default', lang)
            ).ask()
            
            try:
                data["batch_size_for_doc"] = int(batch_size) if batch_size else 3
            except ValueError:
                data["batch_size_for_doc"] = 3
            
            # max_images is now auto-calculated in transcribe.py based on image_start_number + image_count
            # No need to ask user - removed to simplify wizard
        
        # OCR model is already set in mode selection step, so skip here
        # (It's stored in mode-specific config section, not in processing settings)
        
        return data
    
    def _normalize_archive_reference(self, archive_ref: str) -> str:
        """
        Normalize archive reference to archive index format.
        
        Converts "Ф. 487, оп. 1, спр. 545" to "ф487оп1спр545"
        
        Args:
            archive_ref: Archive reference string
            
        Returns:
            Normalized archive index string
        """
        import re
        
        # Remove spaces and punctuation, keep only letters and numbers
        # Extract fond, opis, sprava numbers
        # Pattern: Ф. 487, оп. 1, спр. 545 or Ф.487, оп.1, спр.545
        pattern = r'[Фф]\.?\s*(\d+)[,\s]*[Оо]п\.?\s*(\d+)[,\s]*[Сс]пр\.?\s*(\d+)'
        match = re.search(pattern, archive_ref)
        
        if match:
            fond = match.group(1)
            opis = match.group(2)
            sprava = match.group(3)
            return f"ф{fond}оп{opis}спр{sprava}"
        
        # Fallback: remove spaces and punctuation, lowercase
        normalized = re.sub(r'[^\w]', '', archive_ref).lower()
        return normalized
    
    def _detect_image_number_range(self) -> tuple[int, int] | None:
        """
        Detect minimum and maximum image numbers from available image files.
        
        Returns:
            Tuple of (min_number, max_number) if numbers detected, or None
        """
        import glob
        from transcribe import extract_image_number
        
        mode = self.controller.get_data("mode")
        
        if mode == "local":
            local_data = self.controller.get_data("local", {})
            image_dir = local_data.get("image_dir")
            
            if not image_dir or not os.path.isdir(image_dir):
                return None
            
            # Scan image files - include all supported formats
            extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.png', '*.PNG', 
                        '*.webp', '*.WEBP', '*.heic', '*.HEIC', '*.heif', '*.HEIF']
            image_files = []
            for ext in extensions:
                pattern = os.path.join(image_dir, ext)
                image_files.extend(glob.glob(pattern))
            
            if not image_files:
                return None
            
            # Extract numbers from filenames
            numbers = []
            for img_path in image_files:
                filename = os.path.basename(img_path)
                number = extract_image_number(filename)
                if number is not None:
                    numbers.append(number)
            
            if numbers:
                return (min(numbers), max(numbers))
        
        # For GOOGLECLOUD mode, we'd need to initialize services which is complex
        # Skip for now - user can enter manually
        return None
    
    def _count_available_images(self) -> int:
        """
        Count total available image files.
        
        Returns:
            Number of image files found
        """
        mode = self.controller.get_data("mode")
        
        if mode != "local":
            return 0
        
        local_data = self.controller.get_data("local", {})
        image_dir = local_data.get("image_dir")
        
        if not image_dir or not os.path.isdir(image_dir):
            return 0
        
        import glob
        
        # Scan image files - include all supported formats
        extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.png', '*.PNG', 
                    '*.webp', '*.WEBP', '*.heic', '*.HEIC', '*.heif', '*.HEIF']
        image_files = []
        for ext in extensions:
            pattern = os.path.join(image_dir, ext)
            image_files.extend(glob.glob(pattern))
        
        return len(image_files)
    
    def _calculate_max_available_images(self, image_start: int, sort_method: str, 
                                       min_number: Optional[int], max_number: Optional[int]) -> Optional[int]:
        """
        Calculate maximum available images based on sort method and start position.
        
        Args:
            image_start: Starting image number or position
            sort_method: Sorting method selected
            min_number: Minimum extracted number (if available)
            max_number: Maximum extracted number (if available)
            
        Returns:
            Maximum available images, or None if cannot be determined
        """
        mode = self.controller.get_data("mode")
        
        if mode != "local":
            return None
        
        if sort_method == "number_extracted":
            # For number-based: max is (max_number - start + 1)
            if max_number is not None:
                max_available = max(0, max_number - image_start + 1)
                return max_available if max_available > 0 else None
        else:
            # For position-based: max is (total_files - start + 1)
            total_files = self._count_available_images()
            if total_files > 0:
                max_available = max(0, total_files - image_start + 1)
                return max_available if max_available > 0 else None
        
        return None
    
    def _display_selected_range(self, image_start: int, image_count: int, sort_method: str, lang: str):
        """
        Display the selected image range with actual file names.
        
        Args:
            image_start: Starting image number or position
            image_count: Number of images to process
            sort_method: Sorting method selected
            lang: Language code
        """
        mode = self.controller.get_data("mode")
        
        if mode == "googlecloud":
            # For GOOGLECLOUD mode, try to list files from Drive
            self._display_selected_range_googlecloud(image_start, image_count, sort_method, lang)
            return
        
        local_data = self.controller.get_data("local", {})
        image_dir = local_data.get("image_dir")
        
        if not image_dir or not os.path.isdir(image_dir):
            return
        
        import glob
        from transcribe import extract_image_number
        
        # Scan image files - include all supported formats
        extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.png', '*.PNG', 
                    '*.webp', '*.WEBP', '*.heic', '*.HEIC', '*.heif', '*.HEIF']
        image_files = []
        for ext in extensions:
            pattern = os.path.join(image_dir, ext)
            image_files.extend(glob.glob(pattern))
        
        if not image_files:
            return
        
        if sort_method == "number_extracted":
            # For number_extracted: filter by extracted number
            numbered_files = []
            for img_path in image_files:
                filename = os.path.basename(img_path)
                number = extract_image_number(filename)
                if number is not None:
                    numbered_files.append((number, filename))
            
            if not numbered_files:
                self.console.print(f"\n[yellow][dim]Warning: No files with extractable numbers found[/dim][/yellow]")
                return
            
            # Sort by number
            numbered_files.sort(key=lambda x: x[0])
            
            # Find files in range
            image_end = image_start + image_count - 1
            selected_files = []
            for number, filename in numbered_files:
                if image_start <= number <= image_end:
                    selected_files.append((number, filename))
            
            if selected_files:
                start_filename = selected_files[0][1]
                end_filename = selected_files[-1][1]
                # Show prominent summary with start and end filenames
                self.console.print(f"\n[cyan]Selected range: {start_filename} ... {end_filename}[/cyan]")
                self.console.print(f"[dim]Range: {image_start}-{image_end} (numbers {selected_files[0][0]}-{selected_files[-1][0]})[/dim]")
                file_names = [f[1] for f in selected_files]
                if len(file_names) <= 10:
                    self.console.print(f"[dim]All files: {', '.join(file_names)}[/dim]")
                else:
                    self.console.print(f"[dim]All files ({len(file_names)} total): {', '.join(file_names[:5])} ... {', '.join(file_names[-2:])}[/dim]")
            else:
                self.console.print(f"\n[yellow][dim]Warning: No files found in range {image_start}-{image_end}[/dim][/yellow]")
        else:
            # For other methods: use position-based selection
            # Convert to list of dicts for sorting
            all_images = []
            for img_path in image_files:
                filename = os.path.basename(img_path)
                stat = os.stat(img_path)
                all_images.append({
                    'name': filename,
                    'path': img_path,
                    'created': stat.st_ctime,
                    'modified': stat.st_mtime
                })
            
            # Sort based on method
            if sort_method == "name_asc":
                all_images.sort(key=lambda x: x['name'])
            elif sort_method == "created_date":
                all_images.sort(key=lambda x: x['created'])
            elif sort_method == "modified_date":
                all_images.sort(key=lambda x: x['modified'])
            
            # Select by position
            start_pos = max(0, image_start - 1)
            end_pos = min(len(all_images), start_pos + image_count)
            selected_files = all_images[start_pos:end_pos]
            
            if selected_files:
                start_filename = selected_files[0]['name']
                end_filename = selected_files[-1]['name']
                # Show prominent summary with start and end filenames
                self.console.print(f"\n[cyan]Selected range: {start_filename} ... {end_filename}[/cyan]")
                self.console.print(f"[dim]Positions: {image_start}-{image_start + len(selected_files) - 1} (sorted {sort_method})[/dim]")
                file_names = [f['name'] for f in selected_files]
                if len(file_names) <= 10:
                    self.console.print(f"[dim]All files: {', '.join(file_names)}[/dim]")
                else:
                    self.console.print(f"[dim]All files ({len(file_names)} total): {', '.join(file_names[:5])} ... {', '.join(file_names[-2:])}[/dim]")
            else:
                self.console.print(f"\n[yellow][dim]Warning: No files found at positions {image_start}-{image_start + image_count - 1}[/dim][/yellow]")
    
    def _display_selected_range_googlecloud(self, image_start: int, image_count: int, sort_method: str, lang: str):
        """
        Display the selected image range for GOOGLECLOUD mode by listing files from Drive.
        
        Args:
            image_start: Starting image number or position
            image_count: Number of images to process
            sort_method: Sorting method selected
            lang: Language code
        """
        try:
            # Try to get Drive service from context (might be initialized for title page extraction)
            googlecloud_data = self.controller.get_data("googlecloud", {})
            drive_folder_id = googlecloud_data.get("drive_folder_id")
            
            if not drive_folder_id:
                # Can't list files without folder ID
                self.console.print(f"\n[dim]Selected range: positions {image_start}-{image_start + image_count - 1} (files will be determined when accessing Drive)[/dim]")
                return
            
            # Try to initialize Drive service
            config = {
                'adc_file': googlecloud_data.get('adc_file', 'application_default_credentials.json'),
                'project_id': googlecloud_data.get('project_id'),
                'region': googlecloud_data.get('region', 'global')
            }
            
            # Use the same initialization method as context collection step
            from wizard.steps.context_collection_step import ContextCollectionStep
            temp_context_step = ContextCollectionStep(self.controller)
            services = temp_context_step._initialize_google_services(config)
            
            if not services:
                # Can't initialize services - show summary without filenames
                self.console.print(f"\n[dim]Selected range: positions {image_start}-{image_start + image_count - 1} (files will be determined when accessing Drive)[/dim]")
                return
            
            drive_service, _ = services
            
            # List image files from Drive
            query = f"'{drive_folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png' or mimeType='image/webp' or mimeType='image/heic' or mimeType='image/heif') and trashed=false"
            
            # Map sort method to Drive API orderBy
            order_by_map = {
                'name_asc': 'name',
                'created_date': 'createdTime',
                'modified_date': 'modifiedTime'
            }
            order_by = order_by_map.get(sort_method, 'name')
            
            # Fetch files (limit to reasonable number for wizard display)
            max_fetch = image_start + image_count + 50  # Fetch a bit more than needed
            all_images = []
            page_token = None
            
            while len(all_images) < max_fetch:
                try:
                    fields = "nextPageToken,files(id,name"
                    if sort_method == 'created_date':
                        fields += ",createdTime"
                    elif sort_method == 'modified_date':
                        fields += ",modifiedTime"
                    fields += ")"
                    
                    resp = drive_service.files().list(
                        q=query,
                        fields=fields,
                        orderBy=order_by,
                        pageSize=100,
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
                    logging.debug(f"Error fetching files from Drive: {e}")
                    break
            
            if not all_images:
                self.console.print(f"\n[dim]Selected range: positions {image_start}-{image_start + image_count - 1} (no images found in Drive folder)[/dim]")
                return
            
            if sort_method == "number_extracted":
                # For number_extracted: filter by extracted number
                from transcribe import extract_image_number
                numbered_files = []
                for img in all_images:
                    filename = img['name']
                    number = extract_image_number(filename)
                    if number is not None:
                        numbered_files.append((number, filename))
                
                if not numbered_files:
                    self.console.print(f"\n[dim]Selected range: positions {image_start}-{image_start + image_count - 1} (no files with extractable numbers found)[/dim]")
                    return
                
                # Sort by number
                numbered_files.sort(key=lambda x: x[0])
                
                # Find files in range
                image_end = image_start + image_count - 1
                selected_files = []
                for number, filename in numbered_files:
                    if image_start <= number <= image_end:
                        selected_files.append((number, filename))
                
                if selected_files:
                    start_filename = selected_files[0][1]
                    end_filename = selected_files[-1][1]
                    self.console.print(f"\n[cyan]Selected range: {start_filename} ... {end_filename}[/cyan]")
                    self.console.print(f"[dim]Range: {image_start}-{image_end} (numbers {selected_files[0][0]}-{selected_files[-1][0]})[/dim]")
                else:
                    self.console.print(f"\n[yellow][dim]Warning: No files found in range {image_start}-{image_end}[/dim][/yellow]")
            else:
                # For position-based: select by position
                start_pos = max(0, image_start - 1)
                end_pos = min(len(all_images), start_pos + image_count)
                selected_files = all_images[start_pos:end_pos]
                
                if selected_files:
                    start_filename = selected_files[0]['name']
                    end_filename = selected_files[-1]['name']
                    self.console.print(f"\n[cyan]Selected range: {start_filename} ... {end_filename}[/cyan]")
                    self.console.print(f"[dim]Positions: {image_start}-{image_start + len(selected_files) - 1} (sorted {sort_method})[/dim]")
                else:
                    self.console.print(f"\n[yellow][dim]Warning: No files found at positions {image_start}-{image_start + image_count - 1}[/dim][/yellow]")
                    
        except Exception as e:
            # If anything fails, at least show a summary
            logging.debug(f"Error displaying selected range for GOOGLECLOUD: {e}")
            self.console.print(f"\n[dim]Selected range: positions {image_start}-{image_start + image_count - 1} (files will be determined when accessing Drive)[/dim]")
    
    def _list_available_templates(self) -> list[Dict[str, str]]:
        """
        List available prompt templates.
        
        Returns:
            List of template dictionaries with 'name' and 'description'
        """
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "templates")
        
        if not os.path.isdir(templates_dir):
            return []
        
        templates = []
        for filename in os.listdir(templates_dir):
            if filename.endswith(".md"):
                template_name = filename[:-3]  # Remove .md extension
                
                # Try to read first few lines for description
                template_path = os.path.join(templates_dir, filename)
                description = "Prompt template"
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("#"):
                            description = first_line[1:].strip()
                except Exception:
                    pass
                
                templates.append({
                    "name": template_name,
                    "description": description
                })
        
        return templates
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate collected data.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if "prompt_template" not in data:
            errors.append("Prompt template not selected")
        
        if "archive_index" not in data or not data["archive_index"]:
            errors.append("Archive index not specified")
        
        if "image_start_number" in data:
            if not isinstance(data["image_start_number"], int) or data["image_start_number"] < 1:
                errors.append("image_start_number must be a positive integer")
        
        if "image_count" in data:
            if not isinstance(data["image_count"], int) or data["image_count"] < 1:
                errors.append("image_count must be a positive integer")
        
        mode = self.controller.get_data("mode")
        if mode == "googlecloud":
            if "batch_size_for_doc" in data:
                if not isinstance(data["batch_size_for_doc"], int) or data["batch_size_for_doc"] < 1:
                    errors.append("batch_size_for_doc must be a positive integer")
        
        return len(errors) == 0, errors
