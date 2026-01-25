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
from wizard.i18n import t


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
        lang = self.controller.get_language()
        self.console.print(f"\n[bold]{t('mode_selection.title', lang)}[/bold]")
        self.console.print(f"{t('mode_selection.description', lang)}\n")
        
        # Select mode
        mode = questionary.select(
            t('mode_selection.prompt', lang),
            choices=[
                questionary.Choice(
                    t('mode_selection.local', lang),
                    value="local"
                ),
                questionary.Choice(
                    t('mode_selection.googlecloud', lang),
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
        lang = self.controller.get_language()
        local_data = {}
        
        # Image directory
        image_dir = questionary.path(
            t('local.image_dir_prompt', lang),
            default=t('local.image_dir_default', lang)
        ).ask()
        
        if not image_dir:
            return {}
        
        # Expand user home directory if needed
        image_dir = os.path.expanduser(image_dir)
        local_data["image_dir"] = image_dir
        
        # API key - check if env var is set first
        env_api_key = os.environ.get('GEMINI_API_KEY')
        
        if env_api_key:
            # Environment variable is set - ask if user wants to use it
            use_env_key = questionary.confirm(
                t('local.use_env_key', lang),
                default=True
            ).ask()
            
            if not use_env_key:
                # User wants to provide their own key instead
                self.console.print(f"[dim]{t('local.api_key_hint', lang)}[/dim]")
                api_key = questionary.text(
                    t('local.api_key_prompt', lang),
                    default=""
                ).ask()
                if api_key:
                    local_data["api_key"] = api_key
            # If use_env_key is True, we don't set api_key in local_data, 
            # so the code will use the env var at runtime
        else:
            # Environment variable is not set - ask for API key directly
            self.console.print(f"[dim]{t('local.api_key_hint', lang)}[/dim]")
            api_key = questionary.text(
                t('local.api_key_prompt', lang),
                default=""
            ).ask()
            if api_key:
                local_data["api_key"] = api_key
            else:
                # User didn't provide key and env var is not set
                self.console.print(f"[yellow]{t('local.no_api_key_warning', lang)}[/yellow]")
        
        # Output directory (optional)
        output_dir = questionary.path(
            t('local.output_dir_prompt', lang),
            default=t('local.output_dir_default', lang)
        ).ask()
        
        if output_dir:
            local_data["output_dir"] = os.path.expanduser(output_dir)
        
        # Ask if logs should be saved to source image directory
        save_logs_to_source = questionary.confirm(
            t('local.save_logs_to_source', lang),
            default=True
        ).ask()
        
        if save_logs_to_source is not None:
            local_data["save_logs_to_source"] = save_logs_to_source
        
        # OCR model (optional, with default)
        ocr_model = questionary.select(
            t('local.ocr_model_prompt', lang),
            choices=[
                questionary.Choice(t('local.ocr_model_recommended', lang), value="gemini-3-flash-preview"),
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
        lang = self.controller.get_language()
        gc_data = {}
        
        # Project ID
        self.console.print(f"\n[bold]{t('googlecloud.project_id_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('googlecloud.project_id_hint', lang)}[/dim]")
        self.console.print(f"[dim]{t('googlecloud.project_id_example', lang)}[/dim]")
        project_id = questionary.text(
            t('googlecloud.project_id_prompt', lang),
            default=t('googlecloud.project_id_default', lang)
        ).ask()
        
        if not project_id:
            return {}
        
        gc_data["project_id"] = project_id
        
        # Drive folder ID (from URL or direct)
        self.console.print(f"\n[bold]{t('googlecloud.drive_folder_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('googlecloud.drive_folder_hint', lang)}[/dim]")
        self.console.print(f"[dim]{t('googlecloud.drive_folder_hint2', lang)}[/dim]")
        drive_input = questionary.text(
            t('googlecloud.drive_folder_prompt', lang),
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        
        if not drive_input:
            self.console.print(f"[red]{t('googlecloud.drive_folder_error', lang)}[/red]")
            return {}  # Return empty to trigger retry
        
        # Extract folder ID from URL if provided
        folder_id = self._extract_folder_id(drive_input)
        if not folder_id:
            self.console.print(f"[red]{t('googlecloud.drive_folder_extract_error', lang)}[/red]")
            return {}  # Return empty to trigger retry
        
        gc_data["drive_folder_id"] = folder_id
        
        # Ask if logs should be saved to source Google Drive folder
        save_logs_to_source = questionary.confirm(
            t('googlecloud.save_logs_to_source', lang),
            default=True
        ).ask()
        
        if save_logs_to_source is not None:
            gc_data["save_logs_to_source"] = save_logs_to_source
        
        # Region (optional, with default)
        self.console.print(f"\n[bold]{t('googlecloud.region_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('googlecloud.region_hint', lang)}[/dim]")
        region = questionary.select(
            t('googlecloud.region_prompt', lang),
            choices=[
                questionary.Choice(t('googlecloud.region_global', lang), value="global"),
                questionary.Choice("us-central1", value="us-central1"),
                questionary.Choice("us-east1", value="us-east1"),
            ],
            default="global"
        ).ask()
        
        if region:
            gc_data["region"] = region
        
        # ADC file (optional)
        self.console.print(f"\n[bold]{t('googlecloud.adc_file_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('googlecloud.adc_file_hint', lang)}[/dim]")
        self.console.print(f"[dim]{t('googlecloud.adc_file_hint2', lang)}[/dim]")
        adc_file = questionary.path(
            t('googlecloud.adc_file_prompt', lang),
            default=t('googlecloud.adc_file_default', lang)
        ).ask()
        
        if adc_file:
            gc_data["adc_file"] = os.path.expanduser(adc_file)
        
        # Document name (optional)
        self.console.print(f"\n[bold]{t('googlecloud.document_name_title', lang)}[/bold]")
        self.console.print(f"[dim]{t('googlecloud.document_name_hint', lang)}[/dim]")
        self.console.print(f"[dim]{t('googlecloud.document_name_hint2', lang)}[/dim]")
        document_name = questionary.text(
            t('googlecloud.document_name_prompt', lang),
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
        lang = self.controller.get_language()
        errors = []
        
        if "mode" not in data:
            errors.append(t('validation.mode_not_selected', lang))
            return False, errors
        
        mode = data["mode"]
        
        if mode == "local":
            if "local" not in data:
                errors.append(t('validation.local_settings_missing', lang))
            else:
                local = data["local"]
                if "image_dir" not in local:
                    errors.append(t('validation.image_dir_not_specified', lang))
                elif not os.path.isdir(local["image_dir"]):
                    errors.append(t('validation.image_dir_not_exists', lang, path=local['image_dir']))
        
        elif mode == "googlecloud":
            if "googlecloud" not in data:
                errors.append(t('validation.googlecloud_settings_missing', lang))
            else:
                gc = data["googlecloud"]
                if not gc:  # Empty dict
                    errors.append(t('validation.googlecloud_settings_empty', lang))
                else:
                    if "project_id" not in gc:
                        errors.append(t('validation.project_id_not_specified', lang))
                    if "drive_folder_id" not in gc:
                        errors.append(t('validation.drive_folder_id_not_specified', lang))
        
        return len(errors) == 0, errors
