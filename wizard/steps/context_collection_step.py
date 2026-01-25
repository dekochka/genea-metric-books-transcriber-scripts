"""
Context Collection Step

Step 2: Collects context information (villages, surnames, archive info).
Supports optional title page extraction (Phase 4) and manual entry.
"""

import os
import re
from typing import Dict, Any, List
import questionary
from rich.console import Console
from rich.panel import Panel

from wizard.steps.base_step import WizardStep


class ContextCollectionStep(WizardStep):
    """Step 2: Collect context information."""
    
    def __init__(self, controller):
        """Initialize context collection step."""
        super().__init__(controller)
        self.console = Console()
    
    def run(self) -> Dict[str, Any]:
        """
        Collect context information.
        
        For Phase 3: Manual collection only.
        Phase 4 will add title page extraction option.
        
        Returns:
            Dictionary with context data:
            - archive_reference
            - document_type
            - date_range
            - main_villages (list of dicts with 'name' and 'variants')
            - additional_villages (list of dicts)
            - common_surnames (list of strings)
            - title_page_filename (optional, for Phase 4)
        """
        self.console.print("\n[bold cyan]Context Information Collection[/bold cyan]")
        self.console.print("[dim]Provide information about the document and villages.[/dim]\n")
        
        # For Phase 3, only manual collection
        # Phase 4 will add: "Do you want to extract from title page?"
        context = self._collect_context_manually()
        
        return {"context": context}
    
    def _collect_context_manually(self) -> Dict[str, Any]:
        """
        Collect context information manually via prompts.
        
        Returns:
            Context dictionary
        """
        context = {}
        
        # Archive reference
        self.console.print("[bold]Archive Reference[/bold]")
        self.console.print("[dim]Example: Ф. 487, оп. 1, спр. 545[/dim]")
        archive_ref = questionary.text(
            "Archive Reference:",
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['archive_reference'] = archive_ref.strip() if archive_ref else ""
        
        # Document type
        self.console.print("\n[bold]Document Type[/bold]")
        self.console.print("[dim]Example: Метрична книга про народження[/dim]")
        doc_type = questionary.text(
            "Document Type:",
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['document_type'] = doc_type.strip() if doc_type else ""
        
        # Date range
        self.console.print("\n[bold]Date Range[/bold]")
        self.console.print("[dim]Example: 1888-1924 or 1888 (липень - грудень) - 1924[/dim]")
        date_range = questionary.text(
            "Date Range:",
            validate=lambda x: len(x.strip()) > 0 if x else False
        ).ask()
        context['date_range'] = date_range.strip() if date_range else ""
        
        # Main villages
        self.console.print("\n[bold]Main Villages[/bold]")
        self.console.print("[dim]Enter villages that are primarily related to this document.[/dim]")
        self.console.print("[dim]For each village, you can provide variants (Latin spellings).[/dim]")
        self.console.print("[dim]Format: VillageName (variant1, variant2) or just VillageName[/dim]")
        
        main_villages = self._collect_villages("Main Villages")
        context['main_villages'] = main_villages
        
        # Additional villages
        self.console.print("\n[bold]Additional Villages[/bold]")
        self.console.print("[dim]Enter villages that may appear but are not the main focus (optional).[/dim]")
        has_additional = questionary.confirm(
            "Do you want to add additional villages?",
            default=False
        ).ask()
        
        if has_additional:
            additional_villages = self._collect_villages("Additional Villages")
            context['additional_villages'] = additional_villages
        else:
            context['additional_villages'] = []
        
        # Common surnames
        self.console.print("\n[bold]Common Surnames[/bold]")
        self.console.print("[dim]Enter surnames commonly found in these villages (optional).[/dim]")
        has_surnames = questionary.confirm(
            "Do you want to add common surnames?",
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
        villages = []
        
        while True:
            village_input = questionary.text(
                f"{label} (press Enter when done):",
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
            
            self.console.print(f"  [green]✓[/green] Added: {name}" + 
                             (f" (variants: {', '.join(variants)})" if variants else ""))
        
        return villages
    
    def _collect_surnames(self) -> List[str]:
        """
        Collect common surnames.
        
        Returns:
            List of surname strings
        """
        surnames = []
        
        while True:
            surname_input = questionary.text(
                "Common Surname (press Enter when done):",
                default=""
            ).ask()
            
            if not surname_input or not surname_input.strip():
                break
            
            surnames.append(surname_input.strip())
            self.console.print(f"  [green]✓[/green] Added: {surname_input.strip()}")
        
        return surnames
    
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
