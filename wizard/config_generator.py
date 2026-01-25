"""
Configuration Generator

Generates YAML configuration files from wizard-collected data.
Includes context section and processing settings.
"""

import os
import yaml
from typing import Dict, Any
from rich.console import Console


class ConfigGenerator:
    """Generates YAML configuration files from wizard data."""
    
    def __init__(self):
        """Initialize config generator."""
        self.console = Console()
    
    def generate(self, wizard_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate YAML config file from wizard data.
        
        Args:
            wizard_data: Complete data collected from wizard
            output_path: Path where config should be saved
            
        Returns:
            Path to generated config file
        """
        # Build config structure
        config = self._build_config_structure(wizard_data)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write YAML file
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return output_path
    
    def _build_config_structure(self, wizard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build YAML structure from wizard data.
        
        Args:
            wizard_data: Complete wizard data
            
        Returns:
            Configuration dictionary ready for YAML serialization
        """
        config = {}
        
        # Mode
        mode = wizard_data.get("mode", "local")
        config["mode"] = mode
        
        # Language preference (if set in wizard)
        if "language" in wizard_data:
            config["language"] = wizard_data["language"]
        
        # Mode-specific configuration
        if mode == "local":
            if "local" in wizard_data:
                # Remove any non-serializable objects (like service clients)
                local_config = wizard_data["local"].copy()
                # Remove service objects that can't be serialized (by name)
                local_config = {k: v for k, v in local_config.items() 
                               if k not in ['drive_service', 'genai_client', 'docs_service']}
                config["local"] = local_config
        elif mode == "googlecloud":
            if "googlecloud" in wizard_data:
                # Remove any non-serializable objects (like service clients, thread locks)
                gc_config = wizard_data["googlecloud"].copy()
                # Remove service objects that can't be serialized (by name)
                gc_config = {k: v for k, v in gc_config.items() 
                            if k not in ['drive_service', 'genai_client', 'docs_service']}
                config["googlecloud"] = gc_config
        
        # Context section
        if "context" in wizard_data:
            context = wizard_data["context"]
            # Format context section properly
            config["context"] = self._format_context_section(context)
        
        # Processing settings
        if "prompt_template" in wizard_data:
            config["prompt_template"] = wizard_data["prompt_template"]
        
        if "archive_index" in wizard_data:
            config["archive_index"] = wizard_data["archive_index"]
        
        if "image_start_number" in wizard_data:
            config["image_start_number"] = wizard_data["image_start_number"]
        
        if "image_count" in wizard_data:
            config["image_count"] = wizard_data["image_count"]
        
        if mode == "googlecloud":
            if "batch_size_for_doc" in wizard_data:
                config["batch_size_for_doc"] = wizard_data["batch_size_for_doc"]
            
            if "max_images" in wizard_data:
                config["max_images"] = wizard_data["max_images"]
        
        # Defaults
        config["retry_mode"] = wizard_data.get("retry_mode", False)
        config["retry_image_list"] = wizard_data.get("retry_image_list", [])
        
        return config
    
    def _format_context_section(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context section for YAML output.
        
        Args:
            context: Raw context dictionary from wizard
            
        Returns:
            Formatted context dictionary
        """
        formatted = {}
        
        # Simple string fields
        if context.get('archive_reference'):
            formatted['archive_reference'] = context['archive_reference']
        
        if context.get('document_type'):
            formatted['document_type'] = context['document_type']
        
        if context.get('date_range'):
            formatted['date_range'] = context['date_range']
        
        # Title page filename (optional)
        if context.get('title_page_filename'):
            formatted['title_page_filename'] = context['title_page_filename']
        
        # Main villages - format as list of dicts
        if context.get('main_villages'):
            formatted['main_villages'] = context['main_villages']
        
        # Additional villages - format as list of dicts
        if context.get('additional_villages'):
            formatted['additional_villages'] = context['additional_villages']
        
        # Common surnames - format as list
        if context.get('common_surnames'):
            formatted['common_surnames'] = context['common_surnames']
        
        return formatted
