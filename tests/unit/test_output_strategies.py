"""
Unit tests for output strategies.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from transcribe import LogFileOutput, GoogleDocsOutput


class TestLogFileOutput:
    """Tests for LogFileOutput."""
    
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "logs"
        output_dir.mkdir()
        return str(output_dir)
    
    @pytest.fixture
    def mock_ai_logger(self):
        """Create a mock AI logger."""
        return Mock()
    
    def test_init_creates_output_dir(self, tmp_path, mock_ai_logger):
        """Test __init__ creates output directory if it doesn't exist."""
        output_dir = str(tmp_path / "new_logs")
        output = LogFileOutput(output_dir, mock_ai_logger)
        assert os.path.isdir(output_dir)
        assert output.output_dir == output_dir
    
    def test_initialize_creates_log_file(self, temp_output_dir, mock_ai_logger):
        """Test initialize() creates log file."""
        output = LogFileOutput(temp_output_dir, mock_ai_logger)
        config = {'archive_index': 'test123'}
        log_file = output.initialize(config)
        
        assert log_file is not None
        assert os.path.exists(log_file)
        assert log_file.startswith(temp_output_dir)
    
    def test_write_batch_appends_to_log(self, temp_output_dir, mock_ai_logger):
        """Test write_batch() appends transcriptions to log file."""
        output = LogFileOutput(temp_output_dir, mock_ai_logger)
        config = {'archive_index': 'test123'}
        log_file = output.initialize(config)
        
        pages = [
            {'name': 'image1.jpg', 'webViewLink': 'link1', 'text': 'Transcription 1'},
            {'name': 'image2.jpg', 'webViewLink': 'link2', 'text': 'Transcription 2'}
        ]
        output.write_batch(pages, 1, True)
        
        # Verify file was written
        assert os.path.exists(log_file)
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Transcription 1' in content
            assert 'Transcription 2' in content
    
    def test_finalize_adds_summary(self, temp_output_dir, mock_ai_logger):
        """Test finalize() adds session summary."""
        output = LogFileOutput(temp_output_dir, mock_ai_logger)
        config = {'archive_index': 'test123'}
        log_file = output.initialize(config)
        
        pages = [{'name': 'image1.jpg', 'text': 'Text 1'}]
        metrics = {'total_time': 10.5, 'avg_time_per_page': 10.5}
        output.finalize(pages, metrics)
        
        # Verify summary was added
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'SESSION SUMMARY' in content or 'Summary' in content.upper()


class TestGoogleDocsOutput:
    """Tests for GoogleDocsOutput."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock Google services."""
        return {
            'docs_service': Mock(),
            'drive_service': Mock(),
            'genai_client': Mock()
        }
    
    def test_init_stores_parameters(self, mock_services):
        """Test __init__ stores all necessary services and config."""
        config = {'document_name': 'Test Doc'}
        prompt_text = "Test prompt"
        
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            config,
            prompt_text
        )
        
        assert output.docs_service == mock_services['docs_service']
        assert output.drive_service == mock_services['drive_service']
        assert output.genai_client == mock_services['genai_client']
        assert output.config == config
        assert output.prompt_text == prompt_text
        assert output.doc_id is None
    
    @patch('transcribe.create_doc')
    def test_initialize_creates_document(self, mock_create_doc, mock_services):
        """Test initialize() creates Google Doc."""
        mock_create_doc.return_value = "doc_id_123"
        config = {'document_name': 'Test Doc'}
        
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            config,
            "prompt"
        )
        
        doc_id = output.initialize(config)
        
        mock_create_doc.assert_called_once()
        assert doc_id == "doc_id_123"
        assert output.doc_id == "doc_id_123"
    
    @patch('transcribe.write_to_doc')
    def test_write_batch_delegates_to_write_to_doc(self, mock_write_to_doc, mock_services):
        """Test write_batch() delegates to write_to_doc() function."""
        config = {'document_name': 'Test Doc', 'batch_size_for_doc': 10}
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            config,
            "prompt"
        )
        output.doc_id = "doc_id_123"
        output.start_time = datetime.now()
        
        pages = [
            {'name': 'image1.jpg', 'text': 'Text 1'},
            {'name': 'image2.jpg', 'text': 'Text 2'}
        ]
        output.write_batch(pages, 1, True)
        
        mock_write_to_doc.assert_called_once()
        call_args = mock_write_to_doc.call_args
        # Check positional args: (docs_service, drive_service, doc_id, pages, config, prompt_text, ...)
        assert call_args[0][0] == mock_services['docs_service']  # docs_service
        assert call_args[0][1] == mock_services['drive_service']  # drive_service
        assert call_args[0][2] == "doc_id_123"  # doc_id
        assert call_args[0][3] == pages  # pages
        # Check keyword args
        assert call_args[1]['write_overview'] is True  # First batch
        assert call_args[1]['start_idx'] == 0  # First batch starts at 0
    
    @patch('transcribe.update_overview_section')
    def test_finalize_delegates_to_update_overview_section(self, mock_update_overview, mock_services):
        """Test finalize() delegates to update_overview_section() function."""
        config = {'document_name': 'Test Doc'}
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            config,
            "prompt"
        )
        output.doc_id = "doc_id_123"
        output.start_time = datetime.now()
        
        pages = [{'name': 'image1.jpg', 'text': 'Text 1'}]
        metrics = {'total_time': 10.5}
        output.finalize(pages, metrics)
        
        mock_update_overview.assert_called_once()
        call_args = mock_update_overview.call_args
        # Check positional args: (docs_service, doc_id, all_pages, config, prompt_text, ...)
        assert call_args[0][0] == mock_services['docs_service']  # docs_service
        assert call_args[0][1] == "doc_id_123"  # doc_id
        assert call_args[0][2] == pages  # all_pages
        # Check keyword args
        assert call_args[1]['metrics'] == metrics
        assert call_args[1]['start_time'] == output.start_time
        assert 'end_time' in call_args[1]  # end_time should be set
    
    def test_write_batch_raises_error_if_not_initialized(self, mock_services):
        """Test write_batch() raises error if document not initialized."""
        config = {'document_name': 'Test Doc'}
        output = GoogleDocsOutput(
            mock_services['docs_service'],
            mock_services['drive_service'],
            mock_services['genai_client'],
            config,
            "prompt"
        )
        # doc_id is None (not initialized)
        
        with pytest.raises(ValueError, match="Document not initialized"):
            output.write_batch([], 1, True)
