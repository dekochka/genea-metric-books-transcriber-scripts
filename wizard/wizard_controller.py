"""
Wizard Controller

Main orchestrator for the configuration wizard flow.
Manages step progression and data collection.
"""

import os
from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from wizard.steps.base_step import WizardStep


class WizardController:
    """Main controller for the configuration wizard."""
    
    def __init__(self):
        """Initialize the wizard controller."""
        self.steps: list[WizardStep] = []
        self.collected_data: Dict[str, Any] = {}
        self.console = Console()
    
    def add_step(self, step: WizardStep):
        """
        Add a step to the wizard flow.
        
        Args:
            step: WizardStep instance to add
        """
        self.steps.append(step)
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get collected data from previous steps.
        
        Args:
            key: Data key to retrieve
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        return self.collected_data.get(key, default)
    
    def set_data(self, key: str, value: Any):
        """
        Store data for use in subsequent steps.
        
        Args:
            key: Data key
            value: Data value
        """
        self.collected_data[key] = value
    
    def run(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Run the complete wizard flow.
        
        Args:
            output_path: Optional path for generated config file
            
        Returns:
            Path to generated config file, or None if cancelled
        """
        try:
            # Display welcome message
            self._display_welcome()
            
            # Run each step
            for i, step in enumerate(self.steps, 1):
                step_name = step.__class__.__name__
                self.console.print(f"\n[bold cyan]Step {i}/{len(self.steps)}: {step_name}[/bold cyan]")
                
                # Run step
                step_data = step.run()
                
                # Validate step data
                is_valid, errors = step.validate(step_data)
                if not is_valid:
                    self.console.print("[red]Validation errors:[/red]")
                    for error in errors:
                        self.console.print(f"  • {error}")
                    
                    # Ask if user wants to retry or cancel
                    import questionary
                    retry = questionary.confirm(
                        "Would you like to retry this step?",
                        default=True
                    ).ask()
                    
                    if retry:
                        # Retry current step
                        step_data = step.run()
                        is_valid, errors = step.validate(step_data)
                        if not is_valid:
                            self.console.print("[red]Validation failed again. Cancelling wizard.[/red]")
                            return None
                    else:
                        self.console.print("[yellow]Wizard cancelled by user.[/yellow]")
                        return None
                
                # Store step data
                self.collected_data.update(step_data)
            
            # Generate config file
            self.console.print("\n[bold green]✓ All steps completed successfully![/bold green]")
            
            # Import here to avoid circular dependencies
            from wizard.config_generator import ConfigGenerator
            
            generator = ConfigGenerator()
            
            # Get output path if not provided
            if not output_path:
                import questionary
                output_path = questionary.path(
                    "Where should the config file be saved?",
                    default="config/my-project.yaml"
                ).ask()
            
            if not output_path:
                self.console.print("[yellow]No output path provided. Cancelling.[/yellow]")
                return None
            
            # Generate config
            config_path = generator.generate(self.collected_data, output_path)
            
            self.console.print(f"\n[green]✓ Configuration saved to: {config_path}[/green]")
            
            return config_path
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Wizard cancelled by user.[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            import traceback
            self.console.print(traceback.format_exc())
            return None
    
    def _display_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("Genealogical Transcription Wizard\n", style="bold cyan")
        welcome_text.append("This wizard will guide you through creating a configuration file.\n", style="white")
        welcome_text.append("You can press Ctrl+C at any time to cancel.\n", style="dim")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))
