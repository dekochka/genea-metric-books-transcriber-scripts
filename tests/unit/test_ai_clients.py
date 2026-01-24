"""
Unit tests for AI client strategies.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from transcribe import GeminiDevClient, VertexAIClient


class TestGeminiDevClient:
    """Tests for GeminiDevClient."""
    
    @pytest.fixture
    def mock_genai_client(self):
        """Create a mock Google Genai client."""
        mock_client = Mock()
        mock_model = Mock()
        mock_client.models.generate_content.return_value = Mock(
            text="Test transcription text",
            usage_metadata=Mock(
                prompt_token_count=100,
                candidates_token_count=50
            )
        )
        mock_client.models.return_value = mock_model
        return mock_client
    
    @patch('transcribe.genai.Client')
    def test_init_creates_client(self, mock_client_class):
        """Test __init__ creates genai client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        client = GeminiDevClient("test-api-key", "gemini-1.5-pro")
        
        mock_client_class.assert_called_once_with(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.model_id == "gemini-1.5-pro"
    
    @patch('transcribe.genai.Client')
    @patch('time.time')
    @patch('time.sleep')
    @patch('transcribe.logging')
    def test_transcribe_success(self, mock_logging, mock_sleep, mock_time, mock_client_class):
        """Test transcribe() successfully transcribes image."""
        import time
        
        # Setup mocks
        mock_client = Mock()
        mock_models = Mock()
        mock_response = Mock()
        mock_response.text = "Transcribed text"
        mock_usage_metadata = Mock()
        mock_usage_metadata.prompt_token_count = 100
        mock_usage_metadata.candidates_token_count = 50
        mock_usage_metadata.total_token_count = 150
        mock_usage_metadata.cached_content_token_count = 0
        mock_response.usage_metadata = mock_usage_metadata
        
        # Mock the chain: client.models.generate_content()
        mock_models.generate_content.return_value = mock_response
        mock_client.models = mock_models
        mock_client_class.return_value = mock_client
        
        # Mock time.time() calls (multiple calls during function execution)
        # Provide enough time values for all time.time() calls in the function
        # The function calls time.time() multiple times: function_start, attempt_start, api_call_start, api_call_end, attempt_end, function_end, etc.
        mock_time.side_effect = [0, 0, 0, 1.5, 1.5, 1.5, 1.5, 1.5]  # Multiple calls
        
        # Create client and transcribe
        client = GeminiDevClient("test-api-key", "gemini-1.5-pro")
        image_bytes = b"fake image bytes"
        text, elapsed_time, usage_metadata = client.transcribe(image_bytes, "test.jpg", "prompt text")
        
        assert text == "Transcribed text"
        assert elapsed_time > 0
        assert usage_metadata is not None
        assert 'prompt_tokens' in usage_metadata
    
    @patch('transcribe.genai.Client')
    @patch('time.time')
    @patch('time.sleep')
    @patch('transcribe.logging')
    def test_transcribe_with_retry(self, mock_logging, mock_sleep, mock_time, mock_client_class):
        """Test transcribe() retries on failure."""
        import time
        
        # Setup mocks
        mock_client = Mock()
        mock_models = Mock()
        
        # First call fails with retryable error, second succeeds
        mock_response = Mock()
        mock_response.text = "Success after retry"
        mock_usage_metadata = Mock()
        mock_usage_metadata.prompt_token_count = 100
        mock_usage_metadata.candidates_token_count = 50
        mock_usage_metadata.total_token_count = 150
        mock_usage_metadata.cached_content_token_count = 0
        mock_response.usage_metadata = mock_usage_metadata
        
        # Use a retryable exception (ConnectionError, TimeoutError, or OSError)
        mock_models.generate_content.side_effect = [
            ConnectionError("API Error"),  # Retryable exception
            mock_response
        ]
        mock_client.models = mock_models
        mock_client_class.return_value = mock_client
        
        # Mock time.time() calls (multiple calls during retries)
        # Need many values for retry logic: function_start, attempt_start (x2), api_call_start (x2), api_call_end (x2), attempt_end (x2), function_end
        mock_time.side_effect = [0, 0, 0, 0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0]  # Multiple time calls
        
        client = GeminiDevClient("test-api-key", "gemini-1.5-pro")
        image_bytes = b"fake image bytes"
        text, elapsed_time, usage_metadata = client.transcribe(image_bytes, "test.jpg", "prompt text")
        
        assert text == "Success after retry"
        assert mock_models.generate_content.call_count == 2  # Retried once


class TestVertexAIClient:
    """Tests for VertexAIClient."""
    
    @patch('transcribe.transcribe_image')
    def test_transcribe_delegates_to_transcribe_image(self, mock_transcribe_image):
        """Test transcribe() delegates to existing transcribe_image() function."""
        mock_genai_client = Mock()
        mock_transcribe_image.return_value = ("Transcribed text", 1.5, Mock())
        
        client = VertexAIClient(mock_genai_client, "gemini-3-flash-preview")
        image_bytes = b"fake image bytes"
        text, elapsed_time, usage_metadata = client.transcribe(image_bytes, "test.jpg", "prompt text")
        
        mock_transcribe_image.assert_called_once_with(
            mock_genai_client, image_bytes, "test.jpg", "prompt text", "gemini-3-flash-preview"
        )
        assert text == "Transcribed text"
        assert elapsed_time == 1.5
    
    def test_init_stores_parameters(self):
        """Test __init__ stores genai client and model ID."""
        mock_genai_client = Mock()
        client = VertexAIClient(mock_genai_client, "gemini-3-flash-preview")
        assert client.genai_client == mock_genai_client
        assert client.model_id == "gemini-3-flash-preview"
