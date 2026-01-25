"""
Mode Selection Step

Step 1: Collects processing mode (LOCAL/GOOGLECLOUD) and mode-specific settings.
"""

import os
import re
from typing import Any, Dict
import questionary
from rich.console import Console

from wizard.steps.base_step import WizardStep


class ModeSelectionStep(WizardStep):
    """Step 1: Select processing mode and collect mode-specific settings."""
    
    def __init__(self, controller):
        """Initialize mode selection step."""
        super().__init__(controller)
        self.console = Console()
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the step and collect user input.
        
        Returns:
            Dictionary with mode and mode-specific settings
        """
        self.console.print("\n[bold]Step 1: Select Processing Mode[/bold]")
        self.console.print("Choose how you want to process images:\n")
        
        # Select mode
        mode = questionary.select(
            "Select processing mode:",
            choices=[
                questionary.Choice(
                    "Local (process images from local folder)",
                    value="local"
                ),
                questionary.Choice(
                    "Google Cloud (process images from Google Drive folder)",
                    value="googlecloud"
                ),
            ]
        ).ask()
        
        if not mode:
            return {}
        
        data = {"mode": mode}
        
        # Collect mode-specific settings
        if mode == "local":
            data.update(self._collect_local_settings())
        else:  # googlecloud
            data.update(self._collect_googlecloud_settings())
        
        return data
    
    def _collect_local_settings(self) -> Dict[str, Any]:
        """Collect settings for LOCAL mode."""
        local_data = {}
        
        # Image directory
        image_dir = questionary.path(
            "Enter path to directory containing images:",
            default="data_samples/test_input_sample"
        ).ask()
        
        if not image_dir:
            return {}
        
        # Expand user home directory if needed
        image_dir = os.path.expanduser(image_dir)
        local_data["image_dir"] = image_dir
        
        # API key (optional - can use env var)
        use_env_key = questionary.confirm(
            "Use GEMINI_API_KEY environment variable?",
            default=True
        ).ask()
        
        if not use_env_key:
            self.console.print("[dim]Get your API key from: https://aistudio.google.com/api-keys[/dim]")
            api_key = questionary.text(
                "Enter Gemini API key (or press Enter to skip and use env var):",
                default=""
            ).ask()
            if api_key:
                local_data["api_key"] = api_key
        
        # Output directory (optional)
        output_dir = questionary.path(
            "Enter output directory for logs (or press Enter for default 'logs'):",
            default="logs"
        ).ask()
        
        if output_dir:
            local_data["output_dir"] = os.path.expanduser(output_dir)
        
        # OCR model (optional, with default)
        ocr_model = questionary.select(
            "Select OCR model:",
            choices=[
                questionary.Choice("gemini-3-flash-preview (recommended)", value="gemini-3-flash-preview"),
                questionary.Choice("gemini-flash-latest", value="gemini-flash-latest"),
                questionary.Choice("gemini-flash-lite-latest", value="gemini-flash-lite-latest"),
                questionary.Choice("gemini-3-pro-preview", value="gemini-3-pro-preview"),
            ],
            default="gemini-3-flash-preview"
        ).ask()
        
        if ocr_model:
            local_data["ocr_model_id"] = ocr_model
        
        return {"local": local_data}
    
    def _collect_googlecloud_settings(self) -> Dict[str, Any]:
        """Collect settings for GOOGLECLOUD mode."""
        gc_data = {}
        
        # Project ID
        project_id = questionary.text(
            "Enter Google Cloud Project ID:",
            default="ru-ocr-genea"
        ).ask()
        
        if not project_id:
            return {}
        
        gc_data["project_id"] = project_id
        
        # Drive folder ID (from URL or direct)
        drive_input = questionary.text(
            "Enter Google Drive folder URL or folder ID:",
        ).ask()
        
        if not drive_input:
            return {}
        
        # Extract folder ID from URL if provided
        folder_id = self._extract_folder_id(drive_input)
        if not folder_id:
            self.console.print("[yellow]Could not extract folder ID. Please provide a valid URL or folder ID.[/yellow]")
            return {}
        
        gc_data["drive_folder_id"] = folder_id
        
        # Region (optional, with default)
        region = questionary.select(
            "Select Vertex AI region:",
            choices=[
                questionary.Choice("global (recommended)", value="global"),
                questionary.Choice("us-central1", value="us-central1"),
                questionary.Choice("us-east1", value="us-east1"),
            ],
            default="global"
        ).ask()
        
        if region:
            gc_data["region"] = region
        
        # ADC file (optional)
        adc_file = questionary.path(
            "Enter path to ADC file (or press Enter for default 'application_default_credentials.json'):",
            default="application_default_credentials.json"
        ).ask()
        
        if adc_file:
            gc_data["adc_file"] = os.path.expanduser(adc_file)
        
        # Document name (optional)
        document_name = questionary.text(
            "Enter document name (or press Enter to use folder name):",
            default=""
        ).ask()
        
        if document_name:
            gc_data["document_name"] = document_name
        
        # OCR model (optional, with default)
        ocr_model = questionary.select(
            "Select OCR model:",
            choices=[
                questionary.Choice("gemini-3-flash-preview (recommended)", value="gemini-3-flash-preview"),
                questionary.Choice("gemini-flash-latest", value="gemini-flash-latest"),
                questionary.Choice("gemini-flash-lite-latest", value="gemini-flash-lite-latest"),
                questionary.Choice("gemini-3-pro-preview", value="gemini-3-pro-preview"),
            ],
            default="gemini-3-flash-preview"
        ).ask()
        
        if ocr_model:
            gc_data["ocr_model_id"] = ocr_model
        
        return {"googlecloud": gc_data}
    
    def _extract_folder_id(self, input_str: str) -> str:
        """
        Extract folder ID from Google Drive URL or return as-is if already an ID.
        
        Args:
            input_str: URL or folder ID
            
        Returns:
            Folder ID
        """
        # If it looks like a URL, extract ID
        url_pattern = r'folders/([a-zA-Z0-9_-]+)'
        match = re.search(url_pattern, input_str)
        if match:
            return match.group(1)
        
        # If it's a short alphanumeric string, assume it's already an ID
        if re.match(r'^[a-zA-Z0-9_-]+$', input_str.strip()):
            return input_str.strip()
        
        return ""
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate collected data.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if "mode" not in data:
            errors.append("Mode not selected")
            return False, errors
        
        mode = data["mode"]
        
        if mode == "local":
            if "local" not in data:
                errors.append("Local mode settings missing")
            else:
                local = data["local"]
                if "image_dir" not in local:
                    errors.append("Image directory not specified")
                elif not os.path.isdir(local["image_dir"]):
                    errors.append(f"Image directory does not exist: {local['image_dir']}")
        
        elif mode == "googlecloud":
            if "googlecloud" not in data:
                errors.append("Google Cloud mode settings missing")
            else:
                gc = data["googlecloud"]
                if "project_id" not in gc:
                    errors.append("Project ID not specified")
                if "drive_folder_id" not in gc:
                    errors.append("Drive folder ID not specified")
        
        return len(errors) == 0, errors
