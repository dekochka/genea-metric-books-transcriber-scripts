"""
Internationalization (i18n) support for Wizard Mode.

Provides translation functionality for English and Ukrainian languages.
"""

from typing import Dict

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        # Language selection
        'lang.select': 'Select language / Виберіть мову:',
        'lang.english': 'English',
        'lang.ukrainian': 'Українська',
        
        # Wizard Controller
        'wizard.welcome.title': 'Genealogical Transcription Wizard',
        'wizard.welcome.description': 'This wizard will guide you through creating a configuration file.',
        'wizard.welcome.cancel_hint': 'You can press Ctrl+C at any time to cancel.',
        'wizard.welcome.disclaimer': '⚠️ IMPORTANT: AI makes many inaccuracies in translating names and surnames - use as an approximate translation of handwritten text and verify with the source! According to estimates, the most accurate model for interpreting handwritten text is Gemini 3.0 Flash (Gemini 3.0 Pro).',
        'wizard.step_progress': 'Step {step}/{total}: {name}',
        'wizard.validation_errors': 'Validation errors:',
        'wizard.retry_prompt': 'Would you like to retry this step?',
        'wizard.validation_failed_again': 'Validation failed again. Cancelling wizard.',
        'wizard.cancelled_by_user': 'Wizard cancelled by user.',
        'wizard.all_steps_completed': '✓ All steps completed successfully!',
        'wizard.config_save_prompt': 'Where should the config file be saved?',
        'wizard.config_save_default': 'config/my-project.yaml',
        'wizard.no_output_path': 'No output path provided. Cancelling.',
        'wizard.config_saved': '✓ Configuration saved to: {path}',
        'wizard.preflight_validation': 'Running pre-flight validation...',
        'wizard.validation_errors_continue': 'There are validation errors. Do you want to continue anyway?',
        'wizard.validation_cancelled': 'Validation cancelled. Please fix the issues and try again.',
        'wizard.validation_warnings_continue': 'There are validation warnings. Do you want to continue?',
        'wizard.validation_warnings_cancelled': 'Validation cancelled. Please review the warnings.',
        'wizard.validation_failed_error': '⚠ Validation failed with error: {error}',
        'wizard.continuing_anyway': 'Continuing anyway...',
        'wizard.error': 'Error: {error}',
        
        # Mode Selection Step
        'mode_selection.title': 'Step 1: Select Processing Mode',
        'mode_selection.description': 'Choose how you want to process images:',
        'mode_selection.prompt': 'Select processing mode:',
        'mode_selection.local': 'Local (process images from local folder)',
        'mode_selection.googlecloud': 'Google Cloud (process images from Google Drive folder)',
        
        # Local Mode Settings
        'local.image_dir_prompt': 'Enter path to directory containing images:',
        'local.image_dir_default': 'data_samples/test_input_sample',
        'local.use_env_key': 'Use GEMINI_API_KEY environment variable?',
        'local.api_key_hint': 'Get your API key from: https://aistudio.google.com/api-keys',
        'local.api_key_prompt': 'Enter Gemini API key:',
        'local.no_api_key_warning': '⚠ Warning: No API key provided. You\'ll need to set GEMINI_API_KEY environment variable before running transcription.',
        'local.output_dir_prompt': 'Enter output directory for logs (or press Enter for default \'logs\'):',
        'local.output_dir_default': 'logs',
        'local.save_logs_to_source': 'Save logs to source image directory?',
        'local.ocr_model_prompt': 'Select OCR model:',
        'local.ocr_model_recommended': 'gemini-3-flash-preview (recommended)',
        
        # Google Cloud Mode Settings
        'googlecloud.project_id_title': 'Google Cloud Project ID',
        'googlecloud.project_id_hint': 'Find this in Google Cloud Console: https://console.cloud.google.com/',
        'googlecloud.project_id_example': 'Example: ru-ocr-genea or my-transcription-project',
        'googlecloud.project_id_prompt': 'Enter Google Cloud Project ID:',
        'googlecloud.project_id_default': 'ru-ocr-genea',
        'googlecloud.drive_folder_title': 'Google Drive Folder',
        'googlecloud.drive_folder_hint': 'Get folder ID from Drive folder URL: https://drive.google.com/drive/folders/FOLDER_ID',
        'googlecloud.drive_folder_hint2': 'You can paste the full URL or just the folder ID',
        'googlecloud.drive_folder_prompt': 'Enter Google Drive folder URL or folder ID:',
        'googlecloud.drive_folder_error': 'Error: Drive folder ID is required.',
        'googlecloud.drive_folder_extract_error': 'Error: Could not extract folder ID. Please provide a valid URL or folder ID.',
        'googlecloud.save_logs_to_source': 'Save logs to source Google Drive folder?',
        'googlecloud.region_title': 'Vertex AI Region',
        'googlecloud.region_hint': 'Select the region where Vertex AI is available',
        'googlecloud.region_prompt': 'Select Vertex AI region:',
        'googlecloud.region_global': 'global (recommended)',
        'googlecloud.adc_file_title': 'Application Default Credentials (ADC) File',
        'googlecloud.adc_file_hint': 'Path to credentials file created by: gcloud auth application-default login',
        'googlecloud.adc_file_hint2': 'Usually located at: ~/.config/gcloud/application_default_credentials.json',
        'googlecloud.adc_file_prompt': 'Enter path to ADC file (or press Enter for default \'application_default_credentials.json\'):',
        'googlecloud.adc_file_default': 'application_default_credentials.json',
        'googlecloud.document_name_title': 'Document Name',
        'googlecloud.document_name_hint': 'Name for the Google Doc that will be created (optional)',
        'googlecloud.document_name_hint2': 'If left empty, will use the Drive folder name',
        'googlecloud.document_name_prompt': 'Enter document name (or press Enter to use folder name):',
        
        # Validation Messages
        'validation.mode_not_selected': 'Mode not selected. ACTION: Select processing mode (local or googlecloud) in config. IMPACT: Script cannot run without mode selection.',
        'validation.local_settings_missing': 'Local mode settings missing. ACTION: Add \'local\' section to config with image_dir and api_key. IMPACT: Script cannot run in local mode.',
        'validation.image_dir_not_specified': 'Image directory not specified. ACTION: Set \'image_dir\' in config.local section pointing to folder with images. IMPACT: Script cannot find images to process.',
        'validation.image_dir_not_exists': 'Image directory does not exist: {path}. ACTION: Check path is correct or create directory. IMPACT: Script cannot find images to process.',
        'validation.image_dir_not_readable': 'Image directory is not readable: {path}. ACTION: Check file permissions (chmod +r) or run with appropriate user. IMPACT: Script cannot read images.',
        'validation.googlecloud_settings_missing': 'Google Cloud mode settings missing. ACTION: Add \'googlecloud\' section to config with required fields. IMPACT: Script cannot run in googlecloud mode.',
        'validation.googlecloud_settings_empty': 'Google Cloud mode settings missing - please complete all required fields. ACTION: Fill in project_id, adc_file, and drive_folder_id. IMPACT: Script cannot authenticate or access Google Drive.',
        'validation.project_id_not_specified': 'Project ID not specified. ACTION: Set \'project_id\' in config.googlecloud section. IMPACT: Script cannot initialize Google Cloud services.',
        'validation.drive_folder_id_not_specified': 'Drive folder ID not specified. ACTION: Set \'drive_folder_id\' in config.googlecloud section (get from Google Drive folder URL). IMPACT: Script cannot find images in Google Drive.',
        'validation.drive_folder_id_too_short': 'drive_folder_id appears to be invalid (too short). ACTION: Verify folder ID from Google Drive URL (should be ~33 characters). IMPACT: Script may fail to access correct folder.',
        'validation.no_image_files': 'No image files found in {path}. Supported formats: PNG, JPEG, WEBP, HEIC, HEIF. ACTION: Add image files with supported extensions to directory. IMPACT: Script has no images to process.',
        
        # Authentication Validation
        'validation.api_key_not_found': 'API key not found. ACTION: Set \'api_key\' in config.local or export GEMINI_API_KEY environment variable. Get key from https://aistudio.google.com/api-keys. IMPACT: Script cannot authenticate with Gemini API.',
        'validation.api_key_too_short': 'API key appears to be invalid (too short). ACTION: Verify API key is complete and correctly copied from https://aistudio.google.com/api-keys. IMPACT: API authentication will fail.',
        'validation.api_key_validation_failed': 'API key validation failed: {error}. ACTION: Check API key is valid and has not expired. Regenerate if needed at https://aistudio.google.com/api-keys. IMPACT: Script cannot authenticate with Gemini API.',
        'validation.adc_file_not_specified': 'ADC file not specified for GOOGLECLOUD mode. ACTION: Set \'adc_file\' in config.googlecloud section (default: application_default_credentials.json). IMPACT: Script cannot authenticate with Google Cloud.',
        'validation.adc_file_not_found': 'ADC file not found: {path}. ACTION: Run \'gcloud auth application-default login\' or provide path to valid credentials file. IMPACT: Script cannot authenticate with Google Cloud.',
        'validation.adc_credentials_invalid': 'ADC credentials may be expired or invalid. ACTION: Run \'gcloud auth application-default login\' to refresh credentials. IMPACT: Script may fail during Google Cloud authentication.',
        'validation.adc_oauth_missing_fields': 'ADC file appears to be OAuth credentials but missing client_id or client_secret. ACTION: Ensure OAuth credentials file contains all required fields, or use service account JSON instead. IMPACT: OAuth authentication may fail at runtime.',
        'validation.adc_format_unrecognized': 'ADC file format not recognized (neither service account nor OAuth user credentials). ACTION: Use valid service account JSON or OAuth credentials file. Run \'gcloud auth application-default login\' to generate valid file. IMPACT: Script cannot authenticate with Google Cloud.',
        'validation.adc_not_valid_json': 'ADC file is not valid JSON: {path}. ACTION: Check file format or regenerate using \'gcloud auth application-default login\'. IMPACT: Script cannot parse credentials file.',
        'validation.adc_validation_partial': 'Could not fully validate ADC credentials: {error}. ACTION: Credentials may still work at runtime. If authentication fails, run \'gcloud auth application-default login\' to refresh. IMPACT: Low - credentials may work despite validation warning.',
        
        # Path Validation
        'validation.output_dir_parent_not_exists': 'Output directory parent does not exist: {path}. ACTION: Create parent directory or adjust output_dir path in config. IMPACT: Script cannot create output directory and will fail.',
        'validation.output_dir_not_writable': 'Output directory may not be writable: {path}. ACTION: Check directory permissions (chmod +w) or run with appropriate user. IMPACT: Script cannot write output files (logs, transcriptions).',
        'validation.output_dir_will_be_created': 'Output directory will be created: {path}. ACTION: None required - directory will be created automatically. IMPACT: None - informational only.',
        
        # Context Validation
        'validation.archive_reference_not_provided': 'Archive reference not provided. ACTION: Add \'archive_reference\' to config.context (e.g., "Ф. 487, оп. 1, спр. 545"). IMPACT: Prompt quality may be reduced, AI may have less context for accurate transcription.',
        'validation.document_type_not_provided': 'Document type not provided. ACTION: Add \'document_type\' to config.context (e.g., "Метрична книга про народження"). IMPACT: Prompt quality may be reduced, AI may misinterpret document structure.',
        'validation.date_range_not_provided': 'Date range not provided. ACTION: Add \'date_range\' to config.context (e.g., "1850-1875"). IMPACT: Prompt quality may be reduced, AI may have less temporal context.',
        'validation.no_main_villages': 'No main villages specified. ACTION: Add \'main_villages\' list to config.context with village names. IMPACT: Transcription accuracy may be reduced, especially for village names and locations.',
        'validation.main_villages_empty': 'Main villages list is empty. ACTION: Add at least one village to \'main_villages\' list in config.context. IMPACT: Transcription accuracy may be reduced for village names.',
        'validation.main_village_not_dict': 'Main village {index} is not a dictionary. ACTION: Ensure each village in main_villages is a dict with \'name\' field (e.g., {{"name": "VillageName"}}). IMPACT: Script may fail when processing village data.',
        'validation.main_village_missing_name': 'Main village {index} missing \'name\' field. ACTION: Add \'name\' field to village dictionary (e.g., {{"name": "VillageName"}}). IMPACT: Script cannot use village name in prompts.',
        'validation.additional_village_not_dict': 'Additional village {index} is not a dictionary. ACTION: Ensure each village in additional_villages is a dict with \'name\' field. IMPACT: Script may fail when processing village data.',
        'validation.additional_village_missing_name': 'Additional village {index} missing \'name\' field. ACTION: Add \'name\' field to village dictionary. IMPACT: Script cannot use village name in prompts.',
        'validation.title_page_not_found': 'Title page file not found: {path}. ACTION: Verify filename matches exactly or remove title_page_filename from config if not using. IMPACT: Context extraction from title page will be skipped (manual entry still works).',
        
        # Prompt Assembly Validation
        'validation.prompt_template_not_found': 'Prompt template not found: {path}. ACTION: Check template name in config.prompt_template matches file in prompts/templates/ directory. IMPACT: Script cannot assemble prompt and will fail.',
        'validation.prompt_template_file_not_found': 'Prompt template file not found: {error}. ACTION: Verify template file exists and path is correct. IMPACT: Script cannot load template and will fail.',
        'validation.prompt_assembly_failed': 'Prompt assembly failed: {error}. ACTION: Check template syntax and ensure all required context variables are provided in config.context. IMPACT: Script cannot generate prompt and will fail.',
        'validation.unreplaced_template_vars': 'Unreplaced template variables found: {vars}. ACTION: Add missing variables to config.context or remove from template if optional. IMPACT: Prompt may be incomplete, AI may receive undefined placeholders.',
        
        # Image Validation
        'validation.image_start_less_than_min': 'Image start number {start} is less than minimum available number {min}. ACTION: Set image_start_number to {min} or higher, or add images with lower numbers. IMPACT: Script will skip requested images and may process wrong range.',
        'validation.image_start_exceeds_max': 'Image start number {start} exceeds maximum available number {max}. ACTION: Set image_start_number to {max} or lower, or add more images. IMPACT: Script has no images to process in requested range.',
        'validation.image_range_extends_beyond': 'Requested range {start}-{end} extends beyond maximum available number {max}. ACTION: Reduce image_count or add more images. IMPACT: Script will process fewer images than requested (only up to {max}).',
        'validation.some_image_numbers_missing': 'Some requested image numbers are missing: {numbers}. ACTION: Add missing images or adjust image_start_number/image_count to skip gaps. IMPACT: Script will skip missing images, may produce incomplete transcriptions.',
        'validation.many_image_numbers_missing': 'Many requested image numbers are missing ({missing} out of {total}). ACTION: Check image numbering, add missing images, or adjust range. IMPACT: Script will skip many images, transcriptions may be significantly incomplete.',
        'validation.requested_images_exceed_available': 'Requested {requested} images, but only {available} found in directory. ACTION: Reduce image_count to {available} or add more images. IMPACT: Script will process only {available} images instead of {requested}.',
        'validation.image_start_exceeds_available': 'Image start position {start} exceeds available images ({available}). ACTION: Set image_start_number to {available} or lower. IMPACT: Script has no images to process.',
        
        # Display Messages
        'validation.all_checks_passed': '✓ All validation checks passed!',
        'validation.results_title': 'Pre-Flight Validation Results',
        'validation.type_column': 'Type',
        'validation.message_column': 'Message',
        'validation.type_error': 'ERROR',
        'validation.type_warning': 'WARNING',
        'validation.type_info': 'INFO',
        'validation.failed_with_errors': '✗ Validation failed with {count} error(s)',
        'validation.passed_with_warnings': '⚠ Validation passed with {count} warning(s)',
        'validation.passed': '✓ Validation passed',
        
        # Context Collection Step
        'context.title': 'Context Information Collection',
        'context.description': 'Provide information about the document and villages.',
        'context.title_page_prompt': 'Do you want to extract context from a title page image?',
        'context.title_page_yes': 'Yes - Extract from title page image',
        'context.title_page_no': 'No - Enter information manually',
        'context.archive_reference_title': 'Archive Reference',
        'context.archive_reference_example': 'Example: Ф. 487, оп. 1, спр. 545',
        'context.archive_reference_prompt': 'Archive Reference:',
        'context.document_type_title': 'Document Type',
        'context.document_type_example': 'Example: Метрична книга про народження',
        'context.document_type_prompt': 'Document Type:',
        'context.date_range_title': 'Date Range',
        'context.date_range_example': 'Example: 1888-1924 or 1888 (липень - грудень) - 1924',
        'context.date_range_prompt': 'Date Range:',
        'context.main_villages_title': 'Main Villages',
        'context.main_villages_hint1': 'Enter villages that are primarily related to this document.',
        'context.main_villages_hint2': 'For each village, you can provide variants (Latin spellings).',
        'context.main_villages_hint3': 'Format: VillageName (variant1, variant2) or just VillageName',
        'context.additional_villages_title': 'Additional Villages',
        'context.additional_villages_hint': 'Enter villages that may appear but are not the main focus (optional).',
        'context.additional_villages_prompt': 'Do you want to add additional villages?',
        'context.common_surnames_title': 'Common Surnames',
        'context.common_surnames_hint': 'Enter surnames commonly found in these villages (optional).',
        'context.common_surnames_prompt': 'Do you want to add common surnames?',
        'context.village_prompt': 'Enter village name (or press Enter to finish):',
        'context.surname_prompt': 'Enter surname (or press Enter to finish):',
        'context.added': 'Added: {item}',
        'context.title_page_select': 'Select title page image (or enter manually):',
        'context.extracting': 'Extracting context from title page...',
        'context.extracted_title': 'Extracted Context from Title Page:',
        'context.archive_reference_label': 'Archive Reference:',
        'context.document_type_label': 'Document Type:',
        'context.date_range_label': 'Date Range:',
        'context.main_villages_label': 'Main Villages:',
        'context.main_villages_none': 'Main Villages: None',
        'context.additional_villages_label': 'Additional Villages:',
        'context.common_surnames_label': 'Common Surnames:',
        'context.review_prompt': 'What would you like to do?',
        'context.review_accept': 'Accept all extracted data',
        'context.review_edit': 'Edit some fields',
        'context.review_reject': 'Reject and enter manually',
        'context.enter_filename_manually': 'Enter filename manually',
        'context.title_page_filename_prompt': 'Enter title page filename:',
        'context.title_page_filename_manual': 'Enter title page filename manually:',
        
        # Processing Settings Step
        'processing.title': 'Step 3: Processing Settings',
        'processing.template_prompt': 'Select prompt template:',
        'processing.template_name_prompt': 'Enter prompt template name (e.g., \'metric-book-birth\'):',
        'processing.template_name_default': 'metric-book-birth',
        'processing.archive_index_auto': 'Auto-generated archive index: {index}',
        'processing.archive_index_prompt': 'Enter archive index (e.g., \'ф487оп1спр545\'):',
        'processing.image_start_prompt': 'Enter starting image number (default: 1):',
        'processing.image_start_position_prompt': 'Enter starting position in sorted list (1-indexed, default: 1):',
        'processing.image_start_default': '1',
        'processing.image_count_prompt': 'Enter number of images to process:',
        'processing.image_count_prompt_with_max': 'Enter number of images to process (max available: {max}):',
        'processing.batch_size_prompt': 'Enter batch size for Google Doc writing (default: 3):',
        'processing.batch_size_default': '3',
        'processing.max_images_prompt': 'Enter maximum images to fetch from Drive (or press Enter to skip):',
        'processing.sort_method_prompt': 'Select image sorting method:',
        'processing.sort_method_number_extracted': 'By extracted number - Sort by numeric pattern in filename (recommended when pattern detected)',
        'processing.sort_method_name_asc': 'By name (ascending) - Natural filename order',
        'processing.sort_method_created': 'By created date - Oldest first',
        'processing.sort_method_modified': 'By modified date - Oldest first',
        'processing.sort_method_description': 'Choose how images should be sorted. "By extracted number" is recommended when numeric patterns are detected.',
        
        # Log Messages
        'log.run_summary': 'RUN SUMMARY',
        'log.status_completed': 'Status: COMPLETED SUCCESSFULLY',
        'log.status_interrupted': 'Status: INTERRUPTED BY ERROR',
        'log.error_type': 'Error Type:',
        'log.error_message': 'Error Message:',
        'log.resume_hint': 'Resume: Update config \'image_start_number\' to {number}',
        'log.statistics': 'Statistics:',
        'log.total_images_processed': 'Total images processed:',
        'log.successful_transcriptions': 'Successful transcriptions:',
        'log.failed_transcriptions': 'Failed transcriptions:',
        'log.start_time': 'Start time:',
        'log.end_time': 'End time:',
        'log.total_duration': 'Total duration: {seconds:.1f} seconds ({minutes:.1f} minutes)',
        'log.metrics': 'Metrics:',
        'log.metrics_not_available': 'Metrics: (Not available)',
        'log.outputs_produced': 'Outputs Produced:',
        'log.no_outputs': '(No outputs generated)',
        'log.processing_images': 'Processing {count} images...',
        'log.processing_image': 'Processing: {name}...',
        'log.processing_image_detail': 'Processing image {current}/{total}: \'{name}\'',
        'log.processed': 'Processed:',
        'log.est_cost': 'Est. cost:',
        'log.output_type_log_file': 'Log File',
        'log.output_type_markdown': 'Markdown File',
        'log.output_type_word': 'Word Document',
        'log.output_type_google_doc': 'Google Doc',
    },
    'uk': {
        # Language selection
        'lang.select': 'Select language / Виберіть мову:',
        'lang.english': 'English',
        'lang.ukrainian': 'Українська',
        
        # Wizard Controller
        'wizard.welcome.title': 'Майстер налаштування транскрипції',
        'wizard.welcome.description': 'Цей майстер допоможе вам створити файл конфігурації.',
        'wizard.welcome.cancel_hint': 'Ви можете натиснути Ctrl+C у будь-який час для скасування.',
        'wizard.welcome.disclaimer': '⚠️ ВАЖЛИВО: Штучний інтелект допускає багато неточностей у перекладі імен та прізвищ - використовувати як приблизний переклад рукописного тексту та перевіряти з джерелом! За оцінками найточніша модель інтерпретації рукописного тексту Gemini 3.0 Flash (Gemini 3.0 Pro).',
        'wizard.step_progress': 'Крок {step}/{total}: {name}',
        'wizard.validation_errors': 'Помилки валідації:',
        'wizard.retry_prompt': 'Чи хочете повторити цей крок?',
        'wizard.validation_failed_again': 'Валідація знову не вдалася. Скасування майстра.',
        'wizard.cancelled_by_user': 'Майстер скасовано користувачем.',
        'wizard.all_steps_completed': '✓ Всі кроки успішно завершено!',
        'wizard.config_save_prompt': 'Куди зберегти файл конфігурації?',
        'wizard.config_save_default': 'config/my-project.yaml',
        'wizard.no_output_path': 'Шлях для збереження не вказано. Скасування.',
        'wizard.config_saved': '✓ Конфігурацію збережено в: {path}',
        'wizard.preflight_validation': 'Запуск попередньої валідації...',
        'wizard.validation_errors_continue': 'Є помилки валідації. Чи хочете продовжити все одно?',
        'wizard.validation_cancelled': 'Валідацію скасовано. Будь ласка, виправте проблеми та спробуйте знову.',
        'wizard.validation_warnings_continue': 'Є попередження валідації. Чи хочете продовжити?',
        'wizard.validation_warnings_cancelled': 'Валідацію скасовано. Будь ласка, перегляньте попередження.',
        'wizard.validation_failed_error': '⚠ Валідація не вдалася з помилкою: {error}',
        'wizard.continuing_anyway': 'Продовжуємо все одно...',
        'wizard.error': 'Помилка: {error}',
        
        # Mode Selection Step
        'mode_selection.title': 'Крок 1: Вибір режиму обробки',
        'mode_selection.description': 'Виберіть, як ви хочете обробляти зображення:',
        'mode_selection.prompt': 'Виберіть режим обробки:',
        'mode_selection.local': 'Локальний (обробка зображень з локальної папки)',
        'mode_selection.googlecloud': 'Google Cloud (обробка зображень з папки Google Drive)',
        
        # Local Mode Settings
        'local.image_dir_prompt': 'Введіть шлях до папки зі зображеннями:',
        'local.image_dir_default': 'data_samples/test_input_sample',
        'local.use_env_key': 'Використовувати змінну середовища GEMINI_API_KEY?',
        'local.api_key_hint': 'Отримайте API ключ на: https://aistudio.google.com/api-keys',
        'local.api_key_prompt': 'Введіть API ключ Gemini:',
        'local.no_api_key_warning': '⚠ Попередження: API ключ не надано. Вам потрібно буде встановити змінну середовища GEMINI_API_KEY перед запуском транскрипції.',
        'local.output_dir_prompt': 'Введіть папку для логів (або натисніть Enter для значення за замовчуванням \'logs\'):',
        'local.output_dir_default': 'logs',
        'local.save_logs_to_source': 'Зберегти логи в папку з вихідними зображеннями?',
        'local.ocr_model_prompt': 'Виберіть модель OCR:',
        'local.ocr_model_recommended': 'gemini-3-flash-preview (рекомендовано)',
        
        # Google Cloud Mode Settings
        'googlecloud.project_id_title': 'ID проєкту Google Cloud',
        'googlecloud.project_id_hint': 'Знайдіть це в консолі Google Cloud: https://console.cloud.google.com/',
        'googlecloud.project_id_example': 'Приклад: ru-ocr-genea або my-transcription-project',
        'googlecloud.project_id_prompt': 'Введіть ID проєкту Google Cloud:',
        'googlecloud.project_id_default': 'ru-ocr-genea',
        'googlecloud.drive_folder_title': 'Папка Google Drive',
        'googlecloud.drive_folder_hint': 'Отримайте ID папки з URL папки Drive: https://drive.google.com/drive/folders/FOLDER_ID',
        'googlecloud.drive_folder_hint2': 'Ви можете вставити повний URL або просто ID папки',
        'googlecloud.drive_folder_prompt': 'Введіть URL папки Google Drive або ID папки:',
        'googlecloud.drive_folder_error': 'Помилка: ID папки Drive обов\'язковий.',
        'googlecloud.drive_folder_extract_error': 'Помилка: Не вдалося витягти ID папки. Будь ласка, надайте дійсний URL або ID папки.',
        'googlecloud.save_logs_to_source': 'Зберегти логи в вихідну папку Google Drive?',
        'googlecloud.region_title': 'Регіон Vertex AI',
        'googlecloud.region_hint': 'Виберіть регіон, де доступний Vertex AI',
        'googlecloud.region_prompt': 'Виберіть регіон Vertex AI:',
        'googlecloud.region_global': 'global (рекомендовано)',
        'googlecloud.adc_file_title': 'Файл облікових даних за замовчуванням (ADC)',
        'googlecloud.adc_file_hint': 'Шлях до файлу облікових даних, створеного командою: gcloud auth application-default login',
        'googlecloud.adc_file_hint2': 'Зазвичай розташований за адресою: ~/.config/gcloud/application_default_credentials.json',
        'googlecloud.adc_file_prompt': 'Введіть шлях до файлу ADC (або натисніть Enter для значення за замовчуванням \'application_default_credentials.json\'):',
        'googlecloud.adc_file_default': 'application_default_credentials.json',
        'googlecloud.document_name_title': 'Назва документа',
        'googlecloud.document_name_hint': 'Назва для Google Doc, який буде створено (необов\'язково)',
        'googlecloud.document_name_hint2': 'Якщо залишити порожнім, буде використано назву папки Drive',
        'googlecloud.document_name_prompt': 'Введіть назву документа (або натисніть Enter, щоб використати назву папки):',
        
        # Validation Messages
        'validation.mode_not_selected': 'Режим не вибрано. ДІЯ: Виберіть режим обробки (local або googlecloud) у конфігурації. ВПЛИВ: Скрипт не може працювати без вибору режиму.',
        'validation.local_settings_missing': 'Налаштування локального режиму відсутні. ДІЯ: Додайте розділ \'local\' до конфігурації з image_dir та api_key. ВПЛИВ: Скрипт не може працювати в локальному режимі.',
        'validation.image_dir_not_specified': 'Папка зі зображеннями не вказана. ДІЯ: Встановіть \'image_dir\' у розділі config.local, вказавши шлях до папки зі зображеннями. ВПЛИВ: Скрипт не може знайти зображення для обробки.',
        'validation.image_dir_not_exists': 'Папка зі зображеннями не існує: {path}. ДІЯ: Перевірте правильність шляху або створіть директорію. ВПЛИВ: Скрипт не може знайти зображення для обробки.',
        'validation.image_dir_not_readable': 'Папка зі зображеннями недоступна для читання: {path}. ДІЯ: Перевірте права доступу (chmod +r) або запустіть від відповідного користувача. ВПЛИВ: Скрипт не може читати зображення.',
        'validation.googlecloud_settings_missing': 'Налаштування режиму Google Cloud відсутні. ДІЯ: Додайте розділ \'googlecloud\' до конфігурації з необхідними полями. ВПЛИВ: Скрипт не може працювати в режимі googlecloud.',
        'validation.googlecloud_settings_empty': 'Налаштування режиму Google Cloud відсутні - будь ласка, заповніть всі обов\'язкові поля. ДІЯ: Заповніть project_id, adc_file та drive_folder_id. ВПЛИВ: Скрипт не може автентифікуватися або отримати доступ до Google Drive.',
        'validation.project_id_not_specified': 'ID проєкту не вказано. ДІЯ: Встановіть \'project_id\' у розділі config.googlecloud. ВПЛИВ: Скрипт не може ініціалізувати сервіси Google Cloud.',
        'validation.drive_folder_id_not_specified': 'ID папки Drive не вказано. ДІЯ: Встановіть \'drive_folder_id\' у розділі config.googlecloud (отримайте з URL папки Google Drive). ВПЛИВ: Скрипт не може знайти зображення в Google Drive.',
        'validation.drive_folder_id_too_short': 'drive_folder_id здається недійсним (занадто короткий). ДІЯ: Перевірте ID папки з URL Google Drive (має бути ~33 символи). ВПЛИВ: Скрипт може не отримати доступ до правильної папки.',
        'validation.no_image_files': 'Файли зображень не знайдено в {path}. Підтримувані формати: PNG, JPEG, WEBP, HEIC, HEIF. ДІЯ: Додайте файли зображень з підтримуваними розширеннями до директорії. ВПЛИВ: Скрипт не має зображень для обробки.',
        
        # Authentication Validation
        'validation.api_key_not_found': 'API ключ не знайдено. ДІЯ: Встановіть \'api_key\' у config.local або експортуйте змінну середовища GEMINI_API_KEY. Отримайте ключ на https://aistudio.google.com/api-keys. ВПЛИВ: Скрипт не може автентифікуватися з API Gemini.',
        'validation.api_key_too_short': 'API ключ здається недійсним (занадто короткий). ДІЯ: Перевірте, що API ключ повний і правильно скопійований з https://aistudio.google.com/api-keys. ВПЛИВ: Автентифікація API не вдасться.',
        'validation.api_key_validation_failed': 'Валідація API ключа не вдалася: {error}. ДІЯ: Перевірте, що API ключ дійсний і не застарів. Згенеруйте новий за потреби на https://aistudio.google.com/api-keys. ВПЛИВ: Скрипт не може автентифікуватися з API Gemini.',
        'validation.adc_file_not_specified': 'ADC файл не вказано для режиму GOOGLECLOUD. ДІЯ: Встановіть \'adc_file\' у розділі config.googlecloud (за замовчуванням: application_default_credentials.json). ВПЛИВ: Скрипт не може автентифікуватися з Google Cloud.',
        'validation.adc_file_not_found': 'ADC файл не знайдено: {path}. ДІЯ: Запустіть \'gcloud auth application-default login\' або надайте шлях до валідного файлу облікових даних. ВПЛИВ: Скрипт не може автентифікуватися з Google Cloud.',
        'validation.adc_credentials_invalid': 'Облікові дані ADC можуть бути застарілими або недійсними. ДІЯ: Запустіть \'gcloud auth application-default login\' для оновлення облікових даних. ВПЛИВ: Скрипт може не вдатися під час автентифікації Google Cloud.',
        'validation.adc_oauth_missing_fields': 'ADC файл здається обліковими даними OAuth, але відсутні client_id або client_secret. ДІЯ: Переконайтеся, що файл облікових даних OAuth містить всі необхідні поля, або використовуйте JSON облікового запису служби. ВПЛИВ: Автентифікація OAuth може не вдатися під час виконання.',
        'validation.adc_format_unrecognized': 'Формат ADC файлу не розпізнано (не є ні обліковим записом служби, ні обліковими даними користувача OAuth). ДІЯ: Використовуйте валідний JSON облікового запису служби або файл облікових даних OAuth. Запустіть \'gcloud auth application-default login\' для генерації валідного файлу. ВПЛИВ: Скрипт не може автентифікуватися з Google Cloud.',
        'validation.adc_not_valid_json': 'ADC файл не є валідним JSON: {path}. ДІЯ: Перевірте формат файлу або згенеруйте новий за допомогою \'gcloud auth application-default login\'. ВПЛИВ: Скрипт не може розпарсити файл облікових даних.',
        'validation.adc_validation_partial': 'Не вдалося повністю перевірити облікові дані ADC: {error}. ДІЯ: Облікові дані можуть все ще працювати під час виконання. Якщо автентифікація не вдасться, запустіть \'gcloud auth application-default login\' для оновлення. ВПЛИВ: Низький - облікові дані можуть працювати попри попередження валідації.',
        
        # Path Validation
        'validation.output_dir_parent_not_exists': 'Батьківська директорія вихідного каталогу не існує: {path}. ДІЯ: Створіть батьківську директорію або змініть шлях output_dir у конфігурації. ВПЛИВ: Скрипт не може створити вихідний каталог і не вдасться.',
        'validation.output_dir_not_writable': 'Вихідний каталог може бути недоступним для запису: {path}. ДІЯ: Перевірте права доступу до директорії (chmod +w) або запустіть від відповідного користувача. ВПЛИВ: Скрипт не може записати вихідні файли (логи, транскрипції).',
        'validation.output_dir_will_be_created': 'Вихідний каталог буде створено: {path}. ДІЯ: Не потрібно - директорія буде створена автоматично. ВПЛИВ: Немає - лише інформаційне повідомлення.',
        
        # Context Validation
        'validation.archive_reference_not_provided': 'Архівна довідка не надана. ДІЯ: Додайте \'archive_reference\' до config.context (наприклад, "Ф. 487, оп. 1, спр. 545"). ВПЛИВ: Якість підказки може бути знижена, AI може мати менше контексту для точної транскрипції.',
        'validation.document_type_not_provided': 'Тип документа не надано. ДІЯ: Додайте \'document_type\' до config.context (наприклад, "Метрична книга про народження"). ВПЛИВ: Якість підказки може бути знижена, AI може неправильно інтерпретувати структуру документа.',
        'validation.date_range_not_provided': 'Діапазон дат не надано. ДІЯ: Додайте \'date_range\' до config.context (наприклад, "1850-1875"). ВПЛИВ: Якість підказки може бути знижена, AI може мати менше часового контексту.',
        'validation.no_main_villages': 'Основні села не вказано. ДІЯ: Додайте список \'main_villages\' до config.context з назвами сіл. ВПЛИВ: Точність транскрипції може бути знижена, особливо для назв сіл та локацій.',
        'validation.main_villages_empty': 'Список основних сіл порожній. ДІЯ: Додайте принаймні одне село до списку \'main_villages\' у config.context. ВПЛИВ: Точність транскрипції може бути знижена для назв сіл.',
        'validation.main_village_not_dict': 'Основне село {index} не є словником. ДІЯ: Переконайтеся, що кожне село в main_villages є словником з полем \'name\' (наприклад, {{"name": "VillageName"}}). ВПЛИВ: Скрипт може не вдатися під час обробки даних сіл.',
        'validation.main_village_missing_name': 'Основне село {index} не містить поля \'name\'. ДІЯ: Додайте поле \'name\' до словника села (наприклад, {{"name": "VillageName"}}). ВПЛИВ: Скрипт не може використовувати назву села в підказках.',
        'validation.additional_village_not_dict': 'Додаткове село {index} не є словником. ДІЯ: Переконайтеся, що кожне село в additional_villages є словником з полем \'name\'. ВПЛИВ: Скрипт може не вдатися під час обробки даних сіл.',
        'validation.additional_village_missing_name': 'Додаткове село {index} не містить поля \'name\'. ДІЯ: Додайте поле \'name\' до словника села. ВПЛИВ: Скрипт не може використовувати назву села в підказках.',
        'validation.title_page_not_found': 'Файл титульної сторінки не знайдено: {path}. ДІЯ: Перевірте, що ім\'я файлу точно відповідає, або видаліть title_page_filename з конфігурації, якщо не використовується. ВПЛИВ: Витягнення контексту з титульної сторінки буде пропущено (ручне введення все ще працює).',
        
        # Prompt Assembly Validation
        'validation.prompt_template_not_found': 'Шаблон підказки не знайдено: {path}. ДІЯ: Перевірте, що ім\'я шаблону в config.prompt_template відповідає файлу в директорії prompts/templates/. ВПЛИВ: Скрипт не може зібрати підказку і не вдасться.',
        'validation.prompt_template_file_not_found': 'Файл шаблону підказки не знайдено: {error}. ДІЯ: Перевірте, що файл шаблону існує і шлях правильний. ВПЛИВ: Скрипт не може завантажити шаблон і не вдасться.',
        'validation.prompt_assembly_failed': 'Збірка підказки не вдалася: {error}. ДІЯ: Перевірте синтаксис шаблону та переконайтеся, що всі необхідні змінні контексту надані в config.context. ВПЛИВ: Скрипт не може згенерувати підказку і не вдасться.',
        'validation.unreplaced_template_vars': 'Знайдено незамінені змінні шаблону: {vars}. ДІЯ: Додайте відсутні змінні до config.context або видаліть з шаблону, якщо вони необов\'язкові. ВПЛИВ: Підказка може бути неповною, AI може отримати невизначені заповнювачі.',
        
        # Image Validation
        'validation.image_start_less_than_min': 'Початковий номер зображення {start} менший за мінімальний доступний номер {min}. ДІЯ: Встановіть image_start_number на {min} або вище, або додайте зображення з нижчими номерами. ВПЛИВ: Скрипт пропустить запитані зображення і може обробити неправильний діапазон.',
        'validation.image_start_exceeds_max': 'Початковий номер зображення {start} перевищує максимальний доступний номер {max}. ДІЯ: Встановіть image_start_number на {max} або нижче, або додайте більше зображень. ВПЛИВ: Скрипт не має зображень для обробки в запитаному діапазоні.',
        'validation.image_range_extends_beyond': 'Запитаний діапазон {start}-{end} виходить за межі максимального доступного номера {max}. ДІЯ: Зменшіть image_count або додайте більше зображень. ВПЛИВ: Скрипт обробить менше зображень, ніж запитано (лише до {max}).',
        'validation.some_image_numbers_missing': 'Деякі запитані номери зображень відсутні: {numbers}. ДІЯ: Додайте відсутні зображення або змініть image_start_number/image_count, щоб пропустити прогалини. ВПЛИВ: Скрипт пропустить відсутні зображення, транскрипції можуть бути неповними.',
        'validation.many_image_numbers_missing': 'Багато запитаних номерів зображень відсутні ({missing} з {total}). ДІЯ: Перевірте нумерацію зображень, додайте відсутні зображення або змініть діапазон. ВПЛИВ: Скрипт пропустить багато зображень, транскрипції можуть бути значно неповними.',
        'validation.requested_images_exceed_available': 'Запитано {requested} зображень, але знайдено лише {available} у каталозі. ДІЯ: Зменшіть image_count до {available} або додайте більше зображень. ВПЛИВ: Скрипт обробить лише {available} зображень замість {requested}.',
        'validation.image_start_exceeds_available': 'Початкова позиція зображення {start} перевищує доступні зображення ({available}). ДІЯ: Встановіть image_start_number на {available} або нижче. ВПЛИВ: Скрипт не має зображень для обробки.',
        
        # Display Messages
        'validation.all_checks_passed': '✓ Всі перевірки валідації пройдено!',
        'validation.results_title': 'Результати попередньої валідації',
        'validation.type_column': 'Тип',
        'validation.message_column': 'Повідомлення',
        'validation.type_error': 'ПОМИЛКА',
        'validation.type_warning': 'ПОПЕРЕДЖЕННЯ',
        'validation.type_info': 'ІНФОРМАЦІЯ',
        'validation.failed_with_errors': '✗ Валідація не вдалася з {count} помилкою(ами)',
        'validation.passed_with_warnings': '⚠ Валідація пройдена з {count} попередженням(ами)',
        'validation.passed': '✓ Валідація пройдена',
        
        # Context Collection Step
        'context.title': 'Збір інформації про контекст',
        'context.description': 'Надайте інформацію про документ та села.',
        'context.title_page_prompt': 'Чи хочете витягти контекст зі зображення титульної сторінки?',
        'context.title_page_yes': 'Так - Витягти зі зображення титульної сторінки',
        'context.title_page_no': 'Ні - Ввести інформацію вручну',
        'context.archive_reference_title': 'Архівна довідка',
        'context.archive_reference_example': 'Приклад: Ф. 487, оп. 1, спр. 545',
        'context.archive_reference_prompt': 'Архівна довідка:',
        'context.document_type_title': 'Тип документа',
        'context.document_type_example': 'Приклад: Метрична книга про народження',
        'context.document_type_prompt': 'Тип документа:',
        'context.date_range_title': 'Діапазон дат',
        'context.date_range_example': 'Приклад: 1888-1924 або 1888 (липень - грудень) - 1924',
        'context.date_range_prompt': 'Діапазон дат:',
        'context.main_villages_title': 'Основні села',
        'context.main_villages_hint1': 'Введіть села, які в основному пов\'язані з цим документом.',
        'context.main_villages_hint2': 'Для кожного села ви можете надати варіанти (латинські написання).',
        'context.main_villages_hint3': 'Формат: НазваСела (варіант1, варіант2) або просто НазваСела',
        'context.additional_villages_title': 'Додаткові села',
        'context.additional_villages_hint': 'Введіть села, які можуть з\'являтися, але не є основним фокусом (необов\'язково).',
        'context.additional_villages_prompt': 'Чи хочете додати додаткові села?',
        'context.common_surnames_title': 'Поширені прізвища',
        'context.common_surnames_hint': 'Введіть прізвища, які часто зустрічаються в цих селах (необов\'язково).',
        'context.common_surnames_prompt': 'Чи хочете додати поширені прізвища?',
        'context.village_prompt': 'Введіть назву села (або натисніть Enter для завершення):',
        'context.surname_prompt': 'Введіть прізвище (або натисніть Enter для завершення):',
        'context.added': 'Додано: {item}',
        'context.title_page_select': 'Виберіть зображення титульної сторінки (або введіть вручну):',
        'context.extracting': 'Витягнення контексту з титульної сторінки...',
        'context.extracted_title': 'Витягнутий контекст з титульної сторінки:',
        'context.archive_reference_label': 'Архівна довідка:',
        'context.document_type_label': 'Тип документа:',
        'context.date_range_label': 'Діапазон дат:',
        'context.main_villages_label': 'Основні села:',
        'context.main_villages_none': 'Основні села: Відсутні',
        'context.additional_villages_label': 'Додаткові села:',
        'context.common_surnames_label': 'Поширені прізвища:',
        'context.review_prompt': 'Що ви хочете зробити?',
        'context.review_accept': 'Прийняти всі витягнуті дані',
        'context.review_edit': 'Редагувати деякі поля',
        'context.review_reject': 'Відхилити та ввести вручну',
        'context.enter_filename_manually': 'Ввести назву файлу вручну',
        'context.title_page_filename_prompt': 'Введіть назву файлу титульної сторінки:',
        'context.title_page_filename_manual': 'Введіть назву файлу титульної сторінки вручну:',
        
        # Processing Settings Step
        'processing.title': 'Крок 3: Налаштування обробки',
        'processing.template_prompt': 'Виберіть шаблон запиту:',
        'processing.template_name_prompt': 'Введіть назву шаблону запиту (наприклад, \'metric-book-birth\'):',
        'processing.template_name_default': 'metric-book-birth',
        'processing.archive_index_auto': 'Автоматично згенерований індекс архіву: {index}',
        'processing.archive_index_prompt': 'Введіть індекс архіву (наприклад, \'ф487оп1спр545\'):',
        'processing.image_start_prompt': 'Введіть початковий номер зображення (за замовчуванням: 1):',
        'processing.image_start_position_prompt': 'Введіть початкову позицію в відсортованому списку (індексовано з 1, за замовчуванням: 1):',
        'processing.image_start_default': '1',
        'processing.image_count_prompt': 'Введіть кількість зображень для обробки:',
        'processing.image_count_prompt_with_max': 'Введіть кількість зображень для обробки (максимум доступно: {max}):',
        'processing.batch_size_prompt': 'Введіть розмір пакета для запису в Google Doc (за замовчуванням: 3):',
        'processing.batch_size_default': '3',
        'processing.max_images_prompt': 'Введіть максимальну кількість зображень для завантаження з Drive (або натисніть Enter, щоб пропустити):',
        'processing.sort_method_prompt': 'Виберіть метод сортування зображень:',
        'processing.sort_method_number_extracted': 'За витягнутим номером - Сортування за числовим шаблоном у назві файлу (рекомендовано, коли шаблон виявлено)',
        'processing.sort_method_name_asc': 'За назвою (за зростанням) - Природний порядок імен файлів',
        'processing.sort_method_created': 'За датою створення - Спочатку найстаріші',
        'processing.sort_method_modified': 'За датою зміни - Спочатку найстаріші',
        'processing.sort_method_description': 'Виберіть, як слід сортувати зображення. "За витягнутим номером" рекомендується, коли виявлено числові шаблони.',
        
        # Log Messages
        'log.run_summary': 'ПІДСУМОК ВИКОНАННЯ',
        'log.status_completed': 'Статус: УСПІШНО ЗАВЕРШЕНО',
        'log.status_interrupted': 'Статус: ПЕРЕРВАНО ПОМИЛКОЮ',
        'log.error_type': 'Тип помилки:',
        'log.error_message': 'Повідомлення про помилку:',
        'log.resume_hint': 'Продовжити: Оновіть конфігурацію \'image_start_number\' до {number}',
        'log.statistics': 'Статистика:',
        'log.total_images_processed': 'Всього зображень оброблено:',
        'log.successful_transcriptions': 'Успішних транскрипцій:',
        'log.failed_transcriptions': 'Невдалих транскрипцій:',
        'log.start_time': 'Час початку:',
        'log.end_time': 'Час завершення:',
        'log.total_duration': 'Загальна тривалість: {seconds:.1f} секунд ({minutes:.1f} хвилин)',
        'log.metrics': 'Метрики:',
        'log.metrics_not_available': 'Метрики: (Недоступно)',
        'log.outputs_produced': 'Створені виходи:',
        'log.no_outputs': '(Виходи не створені)',
        'log.processing_images': 'Обробка {count} зображень...',
        'log.processing_image': 'Обробка: {name}...',
        'log.processing_image_detail': 'Обробка зображення {current}/{total}: \'{name}\'',
        'log.processed': 'Оброблено:',
        'log.est_cost': 'Орієнтовна вартість:',
        'log.output_type_log_file': 'Файл логу',
        'log.output_type_markdown': 'Markdown файл',
        'log.output_type_word': 'Документ Word',
        'log.output_type_google_doc': 'Google Doc',
    }
}


def t(key: str, lang: str = 'en', **kwargs) -> str:
    """
    Get translation for a key.
    
    Args:
        key: Translation key (e.g., 'wizard.welcome.title')
        lang: Language code ('en' or 'uk')
        **kwargs: Format arguments for string interpolation
        
    Returns:
        Translated string, or key if translation not found
    """
    translations = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    translation = translations.get(key, key)
    
    # Format string if kwargs provided
    if kwargs:
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails, return translation as-is
            return translation
    
    return translation


def get_available_languages() -> list[str]:
    """Get list of available language codes."""
    return list(TRANSLATIONS.keys())


def is_valid_language(lang: str) -> bool:
    """Check if language code is valid."""
    return lang in TRANSLATIONS
