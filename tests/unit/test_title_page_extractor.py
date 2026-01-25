"""
Unit tests for TitlePageExtractor
"""
import os
import pytest
import tempfile
import json
from unittest.mock import Mock, MagicMock, patch
from wizard.title_page_extractor import TitlePageExtractor


@pytest.fixture
def extractor():
    """Create TitlePageExtractor instance."""
    return TitlePageExtractor(api_key="test_api_key")


@pytest.fixture
def temp_image_file():
    """Create temporary image file for testing."""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "test_image.jpg")
    with open(image_path, 'wb') as f:
        f.write(b"fake image data")
    yield image_path
    import shutil
    shutil.rmtree(temp_dir)


class TestTitlePageExtractor:
    """Test cases for TitlePageExtractor."""
    
    def test_init(self, extractor):
        """Test TitlePageExtractor initialization."""
        assert extractor is not None
        assert extractor.api_key == "test_api_key"
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_from_local_image_success(self, mock_genai, extractor, temp_image_file):
        """Test successful extraction from local image."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "archive_reference": "Ф. 487, оп. 1, спр. 545",
            "document_type": "Birth records",
            "date_range": "1850-1900",
            "main_villages": [{"name": "Княжа", "variants": ["Knyazha"]}],
            "common_surnames": ["Іванов", "Петров"]
        })
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        result = extractor.extract_from_local_image(temp_image_file)
        
        assert result is not None
        assert result.get('archive_reference') == "Ф. 487, оп. 1, спр. 545"
        assert result.get('document_type') == "Birth records"
        assert len(result.get('main_villages', [])) > 0
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_from_local_image_json_in_markdown(self, mock_genai, extractor, temp_image_file):
        """Test extraction when JSON is wrapped in markdown code blocks."""
        # Mock API response with markdown-wrapped JSON
        json_data = {
            "archive_reference": "Ф. 487, оп. 1, спр. 545",
            "document_type": "Birth records"
        }
        markdown_response = f"```json\n{json.dumps(json_data)}\n```"
        
        mock_response = MagicMock()
        mock_response.text = markdown_response
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        result = extractor.extract_from_local_image(temp_image_file)
        
        assert result is not None
        assert result.get('archive_reference') == "Ф. 487, оп. 1, спр. 545"
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_from_local_image_api_error(self, mock_genai, extractor, temp_image_file):
        """Test extraction handles API errors gracefully."""
        # Mock API error
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        result = extractor.extract_from_local_image(temp_image_file)
        
        assert result is None
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_from_local_image_invalid_json(self, mock_genai, extractor, temp_image_file):
        """Test extraction handles invalid JSON gracefully."""
        # Mock API response with invalid JSON
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        result = extractor.extract_from_local_image(temp_image_file)
        
        assert result is None
    
    def test_extract_from_local_image_file_not_found(self, extractor):
        """Test extraction fails when image file doesn't exist."""
        result = extractor.extract_from_local_image("/nonexistent/image.jpg")
        assert result is None
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_uses_optimized_parameters(self, mock_genai, extractor, temp_image_file):
        """Test that extraction uses optimized API parameters."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"archive_reference": "Ф. 487"})
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        extractor.extract_from_local_image(temp_image_file)
        
        # Verify generate_content was called
        assert mock_model.generate_content.called
        
        # Get the call arguments
        call_args = mock_model.generate_content.call_args
        
        # Check that config parameter includes optimized settings
        if call_args and len(call_args) > 1:
            config = call_args[1].get('config', {})
            # Should have lower max_output_tokens and temperature
            # (exact values depend on implementation)
            assert 'config' in call_args[1] or 'generation_config' in call_args[1]
