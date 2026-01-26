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
        'validation.mode_not_selected': 'Mode not selected',
        'validation.local_settings_missing': 'Local mode settings missing',
        'validation.image_dir_not_specified': 'Image directory not specified',
        'validation.image_dir_not_exists': 'Image directory does not exist: {path}',
        'validation.googlecloud_settings_missing': 'Google Cloud mode settings missing',
        'validation.googlecloud_settings_empty': 'Google Cloud mode settings missing - please complete all required fields',
        'validation.project_id_not_specified': 'Project ID not specified',
        'validation.drive_folder_id_not_specified': 'Drive folder ID not specified',
        
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
        'processing.image_start_default': '1',
        'processing.image_count_prompt': 'Enter number of images to process:',
        'processing.batch_size_prompt': 'Enter batch size for Google Doc writing (default: 3):',
        'processing.batch_size_default': '3',
        'processing.max_images_prompt': 'Enter maximum images to fetch from Drive (or press Enter to skip):',
        
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
        'validation.mode_not_selected': 'Режим не вибрано',
        'validation.local_settings_missing': 'Налаштування локального режиму відсутні',
        'validation.image_dir_not_specified': 'Папка зі зображеннями не вказана',
        'validation.image_dir_not_exists': 'Папка зі зображеннями не існує: {path}',
        'validation.googlecloud_settings_missing': 'Налаштування режиму Google Cloud відсутні',
        'validation.googlecloud_settings_empty': 'Налаштування режиму Google Cloud відсутні - будь ласка, заповніть всі обов\'язкові поля',
        'validation.project_id_not_specified': 'ID проєкту не вказано',
        'validation.drive_folder_id_not_specified': 'ID папки Drive не вказано',
        
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
        'processing.image_start_default': '1',
        'processing.image_count_prompt': 'Введіть кількість зображень для обробки:',
        'processing.batch_size_prompt': 'Введіть розмір пакета для запису в Google Doc (за замовчуванням: 3):',
        'processing.batch_size_default': '3',
        'processing.max_images_prompt': 'Введіть максимальну кількість зображень для завантаження з Drive (або натисніть Enter, щоб пропустити):',
        
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
