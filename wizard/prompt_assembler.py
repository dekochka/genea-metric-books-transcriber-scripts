"""
Prompt Assembly Engine

Assembles final prompt from static template and dynamic context.
Replaces template variables with context data.
"""

import os
import re
from typing import Dict, Any, List, Optional
import logging


class PromptAssemblyEngine:
    """Assembles prompts from templates and context data."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize prompt assembly engine.
        
        Args:
            templates_dir: Directory containing prompt templates (default: prompts/templates)
        """
        if templates_dir is None:
            # Default to prompts/templates relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_dir = os.path.join(project_root, "prompts", "templates")
        
        self.templates_dir = templates_dir
        logging.info(f"PromptAssemblyEngine initialized with templates_dir: {templates_dir}")
    
    def assemble(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Assemble prompt from template and context.
        
        Args:
            template_name: Name of template (e.g., "metric-book-birth")
            context: Context dictionary with villages, surnames, etc.
            
        Returns:
            Assembled prompt text ready for use
        """
        # Load template
        template = self._load_template(template_name)
        
        # Replace variables
        assembled = self._replace_variables(template, context)
        
        return assembled
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        List available prompt templates.
        
        Returns:
            List of dictionaries with 'name' and 'description' keys
        """
        if not os.path.isdir(self.templates_dir):
            logging.warning(f"Templates directory does not exist: {self.templates_dir}")
            return []
        
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".md"):
                template_name = filename[:-3]  # Remove .md extension
                
                # Try to read first line for description
                template_path = os.path.join(self.templates_dir, filename)
                description = "Prompt template"
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("#"):
                            description = first_line[1:].strip()
                except Exception as e:
                    logging.debug(f"Could not read description from {template_path}: {e}")
                
                templates.append({
                    "name": template_name,
                    "description": description
                })
        
        return templates
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get metadata about a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Dictionary with template metadata
        """
        template_path = os.path.join(self.templates_dir, f"{template_name}.md")
        
        if not os.path.exists(template_path):
            return {"exists": False}
        
        info = {
            "exists": True,
            "path": template_path,
            "name": template_name
        }
        
        # Try to extract description
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith("#"):
                    info["description"] = first_line[1:].strip()
        except Exception:
            pass
        
        return info
    
    def _load_template(self, template_name: str) -> str:
        """
        Load template file.
        
        Args:
            template_name: Name of template (without .md extension)
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = os.path.join(self.templates_dir, f"{template_name}.md")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _replace_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Replace all template variables with context values.
        
        Args:
            template: Template text with variables
            context: Context dictionary
            
        Returns:
            Template with variables replaced
        """
        result = template
        
        # Simple variable replacements
        replacements = {
            '{{ARCHIVE_REFERENCE}}': context.get('archive_reference', ''),
            '{{DOCUMENT_DESCRIPTION}}': context.get('document_type', ''),
            '{{DATE_RANGE}}': context.get('date_range', ''),
        }
        
        # Format villages
        main_villages = self._format_villages(
            context.get('main_villages', []),
            is_main=True
        )
        replacements['{{MAIN_VILLAGES}}'] = main_villages
        
        additional_villages = self._format_villages(
            context.get('additional_villages', []),
            is_main=False
        )
        replacements['{{ADDITIONAL_VILLAGES}}'] = additional_villages
        
        # Format surnames
        surnames = self._format_surnames(context.get('common_surnames', []))
        replacements['{{COMMON_SURNAMES}}'] = surnames
        
        # Extract fond number from archive reference
        archive_ref = context.get('archive_reference', '')
        fond_match = re.search(r'Ф\.\s*(\d+)', archive_ref)
        if fond_match:
            replacements['{{FOND_NUMBER}}'] = fond_match.group(1)
        else:
            replacements['{{FOND_NUMBER}}'] = ''
        
        # Main village name (first main village)
        main_villages_list = context.get('main_villages', [])
        if main_villages_list:
            if isinstance(main_villages_list[0], dict):
                replacements['{{MAIN_VILLAGE_NAME}}'] = main_villages_list[0].get('name', '')
                variants = main_villages_list[0].get('variants', [])
                if variants:
                    replacements['{{MAIN_VILLAGE_NAME_LATIN}}'] = variants[0]
                else:
                    replacements['{{MAIN_VILLAGE_NAME_LATIN}}'] = ''
            else:
                # Fallback: if it's a string
                replacements['{{MAIN_VILLAGE_NAME}}'] = str(main_villages_list[0])
                replacements['{{MAIN_VILLAGE_NAME_LATIN}}'] = str(main_villages_list[0])
        else:
            replacements['{{MAIN_VILLAGE_NAME}}'] = ''
            replacements['{{MAIN_VILLAGE_NAME_LATIN}}'] = ''
        
        # Perform replacements
        for var, value in replacements.items():
            result = result.replace(var, value)
        
        # Log warning for any remaining variables
        remaining_vars = re.findall(r'\{\{(\w+)\}\}', result)
        if remaining_vars:
            logging.warning(f"Unreplaced template variables found: {remaining_vars}")
        
        return result
    
    def _format_villages(self, villages: List[Any], is_main: bool = True) -> str:
        """
        Format village list for template insertion.
        
        Args:
            villages: List of village dictionaries or strings
            is_main: True for main villages, False for additional
            
        Returns:
            Formatted markdown string
        """
        if not villages:
            return ""
        
        lines = []
        
        for village in villages:
            if isinstance(village, dict):
                name = village.get('name', '')
                variants = village.get('variants', [])
                
                if variants:
                    variants_str = ', '.join(variants)
                    lines.append(f"    *   {name} (v. {variants_str})")
                else:
                    lines.append(f"    *   {name}")
            else:
                # Fallback: if it's a string
                lines.append(f"    *   {village}")
        
        return '\n'.join(lines)
    
    def _format_surnames(self, surnames: List[str]) -> str:
        """
        Format surname list for template insertion.
        
        Args:
            surnames: List of surname strings
            
        Returns:
            Formatted string (comma-separated)
        """
        if not surnames:
            return ""
        
        # Join with comma and space
        return ', '.join(str(s) for s in surnames if s)
