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
        
        # Mode-specific configuration
        if mode == "local":
            if "local" in wizard_data:
                config["local"] = wizard_data["local"]
        elif mode == "googlecloud":
            if "googlecloud" in wizard_data:
                config["googlecloud"] = wizard_data["googlecloud"]
        
        # Context section (will be populated in Phase 3)
        # For now, create empty context structure
        if "context" in wizard_data:
            config["context"] = wizard_data["context"]
        
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
