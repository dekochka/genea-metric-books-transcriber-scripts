"""
Processing Settings Step

Step 3: Collects processing parameters (image range, batch size, etc.).
"""

import os
from typing import Any, Dict
import questionary
from rich.console import Console

from wizard.steps.base_step import WizardStep


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
        self.console.print("\n[bold]Step 3: Processing Settings[/bold]\n")
        
        data = {}
        
        # Prompt template selection
        templates = self._list_available_templates()
        if templates:
            template_choice = questionary.select(
                "Select prompt template:",
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
                "Enter prompt template name (e.g., 'metric-book-birth'):",
                default="metric-book-birth"
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
            self.console.print(f"[dim]Auto-generated archive index: {archive_index}[/dim]")
        else:
            # Fallback: ask user if no archive reference available
            archive_index = questionary.text(
                "Enter archive index (e.g., 'ф487оп1спр545'):",
            ).ask()
            if archive_index:
                data["archive_index"] = archive_index
        
        # Image start number
        image_start = questionary.text(
            "Enter starting image number (default: 1):",
            default="1"
        ).ask()
        
        try:
            data["image_start_number"] = int(image_start) if image_start else 1
        except ValueError:
            data["image_start_number"] = 1
        
        # Image count
        image_count = questionary.text(
            "Enter number of images to process:",
        ).ask()
        
        try:
            data["image_count"] = int(image_count) if image_count else 1
        except ValueError:
            data["image_count"] = 1
        
        # Batch size (only for googlecloud mode)
        mode = self.controller.get_data("mode")
        if mode == "googlecloud":
            batch_size = questionary.text(
                "Enter batch size for Google Doc writing (default: 3):",
                default="3"
            ).ask()
            
            try:
                data["batch_size_for_doc"] = int(batch_size) if batch_size else 3
            except ValueError:
                data["batch_size_for_doc"] = 3
            
            # Max images (optional)
            max_images = questionary.text(
                "Enter maximum images to fetch from Drive (or press Enter to skip):",
                default=""
            ).ask()
            
            if max_images:
                try:
                    data["max_images"] = int(max_images)
                except ValueError:
                    pass
        
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
