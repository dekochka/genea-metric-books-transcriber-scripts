"""
Pre-Flight Validator

Comprehensive validation before processing starts.
Validates authentication, paths, context, prompt assembly, and images.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from wizard.i18n import t


@dataclass
class ValidationResult:
    """Result of pre-flight validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def has_issues(self) -> bool:
        """Check if there are any issues (errors or warnings)."""
        return len(self.errors) > 0 or len(self.warnings) > 0


class PreFlightValidator:
    """Validates configuration before processing starts."""
    
    def __init__(self):
        """Initialize pre-flight validator."""
        self.console = Console()
        self.lang = 'en'  # Default language
    
    def validate(self, config: Dict[str, Any], mode: str, lang: str = 'en') -> ValidationResult:
        """
        Perform comprehensive pre-flight validation.
        
        Args:
            config: Configuration dictionary
            mode: Processing mode ('local' or 'googlecloud')
            lang: Language code ('en' or 'uk') for i18n support
            
        Returns:
            ValidationResult with errors, warnings, and suggestions
        """
        result = ValidationResult(is_valid=True)
        self.lang = lang
        
        # Validate authentication
        self._validate_authentication(config, mode, result)
        
        # Validate paths
        self._validate_paths(config, mode, result)
        
        # Validate context
        self._validate_context(config, result)
        
        # Validate prompt assembly
        self._validate_prompt_assembly(config, result)
        
        # Validate images
        self._validate_images(config, mode, result)
        
        # Determine overall validity
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def _validate_authentication(self, config: Dict[str, Any], mode: str, result: ValidationResult):
        """Validate authentication credentials."""
        if mode == 'local':
            # Check API key
            local_config = config.get('local', {})
            api_key = local_config.get('api_key') or os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                result.errors.append(t('validation.api_key_not_found', self.lang))
            elif len(api_key) < 10:
                result.warnings.append(t('validation.api_key_too_short', self.lang))
            else:
                # Test API key with a simple request
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    # Try to list models (lightweight test)
                    list(client.models.list())
                    # If we get here, API key is valid
                except Exception as e:
                    result.errors.append(t('validation.api_key_validation_failed', self.lang, error=str(e)))
        
        elif mode == 'googlecloud':
            # Check ADC file exists
            gc_config = config.get('googlecloud', {})
            adc_file = gc_config.get('adc_file')
            
            if not adc_file:
                result.errors.append(t('validation.adc_file_not_specified', self.lang))
            elif not os.path.exists(adc_file):
                result.errors.append(t('validation.adc_file_not_found', self.lang, path=adc_file))
            else:
                # Try to validate credentials
                # Note: ADC files can be either service account JSON or OAuth user credentials
                # OAuth user credentials don't have client_email/token_uri, so we check for both formats
                try:
                    import json
                    with open(adc_file, 'r') as f:
                        creds_data = json.load(f)
                    
                    # Check if it's a service account (has client_email)
                    if 'client_email' in creds_data:
                        from google.oauth2 import service_account
                        credentials = service_account.Credentials.from_service_account_file(adc_file)
                        if not credentials.valid:
                            result.warnings.append(t('validation.adc_credentials_invalid', self.lang))
                    # Check if it's OAuth user credentials (has refresh_token)
                    elif 'refresh_token' in creds_data:
                        # OAuth user credentials are valid - they'll be refreshed at runtime
                        # Just check that required fields exist
                        if 'client_id' not in creds_data or 'client_secret' not in creds_data:
                            result.warnings.append(t('validation.adc_oauth_missing_fields', self.lang))
                        else:
                            # OAuth credentials look valid
                            pass
                    else:
                        result.warnings.append(t('validation.adc_format_unrecognized', self.lang))
                except json.JSONDecodeError:
                    result.errors.append(t('validation.adc_not_valid_json', self.lang, path=adc_file))
                except Exception as e:
                    # Don't fail validation for credential format issues - they might work at runtime
                    # OAuth user credentials often fail service_account validation but work fine
                    result.warnings.append(t('validation.adc_validation_partial', self.lang, error=str(e)))
    
    def _validate_paths(self, config: Dict[str, Any], mode: str, result: ValidationResult):
        """Validate file paths and directories."""
        if mode == 'local':
            local_config = config.get('local', {})
            
            # Image directory
            image_dir = local_config.get('image_dir')
            if not image_dir:
                result.errors.append(t('validation.image_dir_not_specified', self.lang))
            elif not os.path.isdir(image_dir):
                result.errors.append(t('validation.image_dir_not_exists', self.lang, path=image_dir))
            elif not os.access(image_dir, os.R_OK):
                result.errors.append(t('validation.image_dir_not_readable', self.lang, path=image_dir))
            
            # Output directory
            output_dir = local_config.get('output_dir', 'logs')
            output_dir_abs = os.path.abspath(output_dir)
            parent_dir = os.path.dirname(output_dir_abs)
            
            if parent_dir and not os.path.isdir(parent_dir):
                result.errors.append(t('validation.output_dir_parent_not_exists', self.lang, path=parent_dir))
            elif os.path.exists(output_dir_abs) and not os.access(output_dir_abs, os.W_OK):
                result.warnings.append(t('validation.output_dir_not_writable', self.lang, path=output_dir))
            elif not os.path.exists(output_dir_abs):
                result.suggestions.append(t('validation.output_dir_will_be_created', self.lang, path=output_dir))
        
        elif mode == 'googlecloud':
            # For GOOGLECLOUD mode, paths are less critical
            # But we can check ADC file (already done in authentication)
            pass
    
    def _validate_context(self, config: Dict[str, Any], result: ValidationResult):
        """Validate context data."""
        context = config.get('context', {})
        
        # Archive reference
        if not context.get('archive_reference'):
            result.warnings.append(t('validation.archive_reference_not_provided', self.lang))
        
        # Document type
        if not context.get('document_type'):
            result.warnings.append(t('validation.document_type_not_provided', self.lang))
        
        # Date range
        if not context.get('date_range'):
            result.warnings.append(t('validation.date_range_not_provided', self.lang))
        
        # Main villages
        main_villages = context.get('main_villages', [])
        if not main_villages:
            result.warnings.append(t('validation.no_main_villages', self.lang))
        elif len(main_villages) == 0:
            result.warnings.append(t('validation.main_villages_empty', self.lang))
        
        # Validate village structure
        for i, village in enumerate(main_villages):
            if not isinstance(village, dict):
                result.errors.append(t('validation.main_village_not_dict', self.lang, index=i+1))
            elif 'name' not in village:
                result.errors.append(t('validation.main_village_missing_name', self.lang, index=i+1))
        
        # Additional villages (optional, but validate structure if present)
        additional_villages = context.get('additional_villages', [])
        for i, village in enumerate(additional_villages):
            if not isinstance(village, dict):
                result.errors.append(t('validation.additional_village_not_dict', self.lang, index=i+1))
            elif 'name' not in village:
                result.errors.append(t('validation.additional_village_missing_name', self.lang, index=i+1))
        
        # Title page filename (if specified, check if it exists)
        title_page_filename = context.get('title_page_filename')
        if title_page_filename:
            mode = config.get('mode', 'local')
            if mode == 'local':
                image_dir = config.get('local', {}).get('image_dir')
                if image_dir:
                    title_page_path = os.path.join(image_dir, title_page_filename)
                    if not os.path.exists(title_page_path):
                        result.warnings.append(t('validation.title_page_not_found', self.lang, path=title_page_path))
    
    def _validate_prompt_assembly(self, config: Dict[str, Any], result: ValidationResult):
        """Validate prompt template and assembly."""
        # Check if prompt_template is specified
        template_name = config.get('prompt_template')
        if not template_name:
            # Legacy mode with prompt_file - skip template validation
            return
        
        # Check template exists
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "templates")
        template_path = os.path.join(templates_dir, f"{template_name}.md")
        
        if not os.path.exists(template_path):
            result.errors.append(t('validation.prompt_template_not_found', self.lang, path=template_path))
            return
        
        # Try to assemble prompt
        try:
            from wizard.prompt_assembler import PromptAssemblyEngine
            
            assembler = PromptAssemblyEngine()
            context = config.get('context', {})
            
            # Try to assemble (this will catch missing variables)
            assembled = assembler.assemble(template_name, context)
            
            # Check for unreplaced variables (warnings)
            import re
            remaining_vars = re.findall(r'\{\{(\w+)\}\}', assembled)
            if remaining_vars:
                result.warnings.append(t('validation.unreplaced_template_vars', self.lang, vars=', '.join(remaining_vars)))
            
        except FileNotFoundError as e:
            result.errors.append(t('validation.prompt_template_file_not_found', self.lang, error=str(e)))
        except Exception as e:
            result.errors.append(t('validation.prompt_assembly_failed', self.lang, error=str(e)))
    
    def _validate_images(self, config: Dict[str, Any], mode: str, result: ValidationResult):
        """Validate image files."""
        if mode == 'local':
            local_config = config.get('local', {})
            image_dir = local_config.get('image_dir')
            
            if not image_dir or not os.path.isdir(image_dir):
                # Already reported in path validation
                return
            
            # List image files (aligned with Google AI API supported MIME types)
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
            image_files = [
                f for f in os.listdir(image_dir)
                if os.path.splitext(f.lower())[1] in image_extensions
            ]
            
            if not image_files:
                result.errors.append(t('validation.no_image_files', self.lang, path=image_dir))
                return
            
            # Check image range
            image_start = config.get('image_start_number', 1)
            image_count = config.get('image_count', 1)
            
            # Extract numbers from filenames using the same logic as the main code
            from transcribe import extract_image_number
            
            # Extract numbers from all image files
            extracted_numbers = []
            for filename in image_files:
                number = extract_image_number(filename)
                if number is not None:
                    extracted_numbers.append(number)
            
            # If we found numeric patterns, validate against extracted numbers
            if extracted_numbers:
                extracted_numbers = sorted(set(extracted_numbers))
                min_number = min(extracted_numbers)
                max_number = max(extracted_numbers)
                
                # Check if requested range exists
                requested_end = image_start + image_count - 1
                
                if image_start < min_number:
                    result.errors.append(
                        t('validation.image_start_less_than_min', self.lang, start=image_start, min=min_number)
                    )
                elif image_start > max_number:
                    result.errors.append(
                        t('validation.image_start_exceeds_max', self.lang, start=image_start, max=max_number)
                    )
                elif requested_end > max_number:
                    result.warnings.append(
                        t('validation.image_range_extends_beyond', self.lang, start=image_start, end=requested_end, max=max_number)
                    )
                
                # Check if specific numbers in range exist
                missing_numbers = []
                for num in range(image_start, image_start + image_count):
                    if num not in extracted_numbers:
                        missing_numbers.append(num)
                
                if missing_numbers:
                    if len(missing_numbers) <= 5:
                        result.warnings.append(
                            t('validation.some_image_numbers_missing', self.lang, numbers=missing_numbers)
                        )
                    else:
                        result.warnings.append(
                            t('validation.many_image_numbers_missing', self.lang, missing=len(missing_numbers), total=image_count)
                        )
            else:
                # No numeric patterns detected - use position-based validation
                # Sort files naturally (by number if possible)
                try:
                    # Try to extract numbers from filenames for sorting
                    def extract_number(filename):
                        import re
                        numbers = re.findall(r'\d+', filename)
                        return int(numbers[0]) if numbers else 0
                    
                    image_files_sorted = sorted(image_files, key=extract_number)
                except:
                    image_files_sorted = sorted(image_files)
                
                expected_count = len(image_files_sorted)
                if image_count > expected_count:
                    result.warnings.append(
                        t('validation.requested_images_exceed_available', self.lang, requested=image_count, available=expected_count)
                    )
                
                # For position-based selection, check if start position is valid
                if image_start > len(image_files_sorted):
                    result.errors.append(
                        t('validation.image_start_exceeds_available', self.lang, start=image_start, available=len(image_files_sorted))
                    )
        
        elif mode == 'googlecloud':
            # For GOOGLECLOUD mode, we can't validate images without API access
            # But we can check if drive_folder_id is specified
            gc_config = config.get('googlecloud', {})
            drive_folder_id = gc_config.get('drive_folder_id')
            
            if not drive_folder_id:
                result.errors.append(t('validation.drive_folder_id_not_specified', self.lang))
            elif len(drive_folder_id) < 10:
                result.warnings.append(t('validation.drive_folder_id_too_short', self.lang))
    
    def display_results(self, result: ValidationResult):
        """
        Display validation results in a user-friendly format.
        
        Args:
            result: ValidationResult to display
        """
        if result.is_valid and not result.warnings:
            self.console.print(f"[green]{t('validation.all_checks_passed', self.lang)}[/green]")
            return
        
        # Create table for results
        table = Table(title=t('validation.results_title', self.lang), show_header=True, header_style="bold cyan")
        table.add_column(t('validation.type_column', self.lang), style="bold")
        table.add_column(t('validation.message_column', self.lang), style="white")
        
        # Add errors
        for error in result.errors:
            table.add_row(f"[red]{t('validation.type_error', self.lang)}[/red]", error)
        
        # Add warnings
        for warning in result.warnings:
            table.add_row(f"[yellow]{t('validation.type_warning', self.lang)}[/yellow]", warning)
        
        # Add suggestions
        for suggestion in result.suggestions:
            table.add_row(f"[blue]{t('validation.type_info', self.lang)}[/blue]", suggestion)
        
        self.console.print(table)
        
        # Summary
        if result.errors:
            self.console.print(f"\n[red]{t('validation.failed_with_errors', self.lang, count=len(result.errors))}[/red]")
        elif result.warnings:
            self.console.print(f"\n[yellow]{t('validation.passed_with_warnings', self.lang, count=len(result.warnings))}[/yellow]")
        else:
            self.console.print(f"\n[green]{t('validation.passed', self.lang)}[/green]")
