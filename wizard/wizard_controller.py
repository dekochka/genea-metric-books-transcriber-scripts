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
import questionary

from wizard.steps.base_step import WizardStep
from wizard.i18n import t, get_available_languages


class WizardController:
    """Main controller for the configuration wizard."""
    
    def __init__(self, lang: str = 'en'):
        """
        Initialize the wizard controller.
        
        Args:
            lang: Language code ('en' or 'uk')
        """
        self.steps: list[WizardStep] = []
        self.collected_data: Dict[str, Any] = {}
        self.console = Console()
        self.lang = lang
    
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
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.lang
    
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
                self.console.print(f"\n[bold cyan]{t('wizard.step_progress', self.lang, step=i, total=len(self.steps), name=step_name)}[/bold cyan]")
                
                # Run step
                step_data = step.run()
                
                # Validate step data
                is_valid, errors = step.validate(step_data)
                if not is_valid:
                    self.console.print(f"[red]{t('wizard.validation_errors', self.lang)}[/red]")
                    for error in errors:
                        self.console.print(f"  • {error}")
                    
                    # Ask if user wants to retry or cancel
                    retry = questionary.confirm(
                        t('wizard.retry_prompt', self.lang),
                        default=True
                    ).ask()
                    
                    if retry:
                        # Retry current step
                        step_data = step.run()
                        is_valid, errors = step.validate(step_data)
                        if not is_valid:
                            self.console.print(f"[red]{t('wizard.validation_failed_again', self.lang)}[/red]")
                            return None
                    else:
                        self.console.print(f"[yellow]{t('wizard.cancelled_by_user', self.lang)}[/yellow]")
                        return None
                
                # Store step data (handle None return from cancelled step)
                if step_data is not None:
                    self.collected_data.update(step_data)
            
            # Store language preference in collected data
            self.collected_data["language"] = self.lang
            
            # Generate config file
            self.console.print(f"\n[bold green]{t('wizard.all_steps_completed', self.lang)}[/bold green]")
            
            # Import here to avoid circular dependencies
            from wizard.config_generator import ConfigGenerator
            
            generator = ConfigGenerator()
            
            # Get output path if not provided
            if not output_path:
                output_path = questionary.path(
                    t('wizard.config_save_prompt', self.lang),
                    default=t('wizard.config_save_default', self.lang)
                ).ask()
            
            if not output_path:
                self.console.print(f"[yellow]{t('wizard.no_output_path', self.lang)}[/yellow]")
                return None
            
            # Generate config
            config_path = generator.generate(self.collected_data, output_path)
            
            self.console.print(f"\n[green]{t('wizard.config_saved', self.lang, path=config_path)}[/green]")
            
            # Run pre-flight validation
            self.console.print(f"\n[bold cyan]{t('wizard.preflight_validation', self.lang)}[/bold cyan]")
            from wizard.preflight_validator import PreFlightValidator
            from transcribe import load_config, detect_mode
            
            try:
                # Load the generated config for validation
                config = load_config(config_path)
                mode = detect_mode(config)
                
                validator = PreFlightValidator()
                result = validator.validate(config, mode, self.lang)
                
                # Display results
                validator.display_results(result)
                
                # If there are errors, ask user if they want to continue
                if result.errors:
                    continue_anyway = questionary.confirm(
                        f"\n{t('wizard.validation_errors_continue', self.lang)}",
                        default=False
                    ).ask()
                    
                    if not continue_anyway:
                        self.console.print(f"[yellow]{t('wizard.validation_cancelled', self.lang)}[/yellow]")
                        return None
                elif result.warnings:
                    # Just show warnings, but allow to continue
                    continue_anyway = questionary.confirm(
                        f"\n{t('wizard.validation_warnings_continue', self.lang)}",
                        default=True
                    ).ask()
                    
                    if not continue_anyway:
                        self.console.print(f"[yellow]{t('wizard.validation_warnings_cancelled', self.lang)}[/yellow]")
                        return None
                
            except Exception as e:
                self.console.print(f"[yellow]{t('wizard.validation_failed_error', self.lang, error=e)}[/yellow]")
                self.console.print(f"[dim]{t('wizard.continuing_anyway', self.lang)}[/dim]")
            
            return config_path
            
        except KeyboardInterrupt:
            self.console.print(f"\n[yellow]{t('wizard.cancelled_by_user', self.lang)}[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"\n[red]{t('wizard.error', self.lang, error=e)}[/red]")
            import traceback
            self.console.print(traceback.format_exc())
            return None
    
    def _display_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append(f"{t('wizard.welcome.title', self.lang)}\n", style="bold cyan")
        welcome_text.append(f"{t('wizard.welcome.description', self.lang)}\n", style="white")
        welcome_text.append(f"{t('wizard.welcome.cancel_hint', self.lang)}\n\n", style="dim")
        welcome_text.append(f"{t('wizard.welcome.disclaimer', self.lang)}\n", style="bold yellow")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))


def select_language() -> str:
    """
    Prompt user to select language.
    
    Returns:
        Language code ('en' or 'uk')
    """
    lang = questionary.select(
        t('lang.select', 'en'),
        choices=[
            questionary.Choice(t('lang.english', 'en'), value='en'),
            questionary.Choice(t('lang.ukrainian', 'en'), value='uk'),
        ],
        default='en'
    ).ask()
    
    return lang if lang else 'en'
