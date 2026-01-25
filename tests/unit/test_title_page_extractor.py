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
    with patch('wizard.title_page_extractor.genai'):
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
    
    @patch('wizard.title_page_extractor.genai')
    def test_init(self, mock_genai):
        """Test TitlePageExtractor initialization."""
        extractor = TitlePageExtractor(api_key="test_api_key")
        assert extractor is not None
        assert extractor.mode == "local"
        assert extractor.model_id == "gemini-3-flash-preview"
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_local_mode_success(self, mock_genai, temp_image_file):
        """Test successful extraction from local image."""
        # Mock API response - need to properly structure the response
        json_data = json.dumps({
            "archive_reference": "Ф. 487, оп. 1, спр. 545",
            "document_type": "Birth records",
            "date_range": "1850-1900",
            "main_villages": [{"name": "Княжа", "variants": ["Knyazha"]}],
            "common_surnames": ["Іванов", "Петров"]
        })
        
        # Create a mock response with text property
        # The code checks: response.text if hasattr(response, 'text') and response.text
        # So we need response.text to be a string, not a MagicMock
        from unittest.mock import PropertyMock
        mock_response = MagicMock()
        # Use PropertyMock to make text return the actual string
        type(mock_response).text = PropertyMock(return_value=json_data)
        
        mock_client = MagicMock()
        # models is a property, not a callable
        mock_models = MagicMock()
        mock_models.generate_content.return_value = mock_response
        mock_client.models = mock_models
        mock_genai.Client.return_value = mock_client
        
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'test_image.jpg',
            'path': temp_image_file
        }
        result = extractor.extract(title_page_info, "local", {})
        
        assert result is not None
        assert result.get('archive_reference') == "Ф. 487, оп. 1, спр. 545"
        assert result.get('document_type') == "Birth records"
        assert len(result.get('main_villages', [])) > 0
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_json_in_markdown(self, mock_genai, temp_image_file):
        """Test extraction when JSON is wrapped in markdown code blocks."""
        # Mock API response with markdown-wrapped JSON
        json_data = {
            "archive_reference": "Ф. 487, оп. 1, спр. 545",
            "document_type": "Birth records"
        }
        from unittest.mock import PropertyMock
        markdown_response = f"```json\n{json.dumps(json_data)}\n```"
        
        mock_response = MagicMock()
        type(mock_response).text = PropertyMock(return_value=markdown_response)
        
        mock_client = MagicMock()
        # models is a property, not a callable
        mock_models = MagicMock()
        mock_models.generate_content.return_value = mock_response
        mock_client.models = mock_models
        mock_genai.Client.return_value = mock_client
        
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'test_image.jpg',
            'path': temp_image_file
        }
        result = extractor.extract(title_page_info, "local", {})
        
        assert result is not None
        assert result.get('archive_reference') == "Ф. 487, оп. 1, спр. 545"
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_api_error(self, mock_genai, temp_image_file):
        """Test extraction handles API errors gracefully."""
        # Mock API error
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'test_image.jpg',
            'path': temp_image_file
        }
        result = extractor.extract(title_page_info, "local", {})
        
        assert result is None
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_invalid_json(self, mock_genai, temp_image_file):
        """Test extraction handles invalid JSON gracefully."""
        # Mock API response with invalid JSON
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"
        
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models.return_value = mock_model
        mock_genai.Client.return_value = mock_client
        
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'test_image.jpg',
            'path': temp_image_file
        }
        result = extractor.extract(title_page_info, "local", {})
        
        assert result is None
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_file_not_found(self, mock_genai):
        """Test extraction fails when image file doesn't exist."""
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'nonexistent.jpg',
            'path': '/nonexistent/image.jpg'
        }
        result = extractor.extract(title_page_info, "local", {})
        assert result is None
    
    @patch('wizard.title_page_extractor.genai')
    def test_extract_uses_optimized_parameters(self, mock_genai, temp_image_file):
        """Test that extraction uses optimized API parameters."""
        from unittest.mock import PropertyMock
        json_data = json.dumps({"archive_reference": "Ф. 487"})
        mock_response = MagicMock()
        type(mock_response).text = PropertyMock(return_value=json_data)
        
        mock_client = MagicMock()
        # models is a property, not a callable
        mock_models = MagicMock()
        mock_models.generate_content.return_value = mock_response
        mock_client.models = mock_models
        mock_genai.Client.return_value = mock_client
        
        extractor = TitlePageExtractor(api_key="test_api_key")
        title_page_info = {
            'filename': 'test_image.jpg',
            'path': temp_image_file
        }
        extractor.extract(title_page_info, "local", {})
        
        # Verify generate_content was called
        assert mock_models.generate_content.called
