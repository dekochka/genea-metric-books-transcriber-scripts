"""
Integration tests for retry logic with timeout mechanism.

Tests verify timeout mechanism integrates correctly with retry logic:
- Timeout on first attempt triggers retry
- All retries exhausted when all timeout
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from transcribe import transcribe_image, TimeoutContext


@pytest.mark.integration
class TestTimeoutIntegration:
    """Integration tests for timeout mechanism with retry logic."""

    @patch('time.sleep')
    @patch('transcribe.logging')
    def test_retry_logic_with_timeout_on_first_attempt(self, mock_logging, mock_sleep):
        """Test retry logic when first attempt times out but second succeeds.

        Verifies SIGNAL-07: timeout on first attempt triggers retry.
        First call times out (TimeoutError), second succeeds with valid response.
        Confirms retry mechanism preserves exponential backoff and succeeds.

        Integration scenario:
        - Attempt 1: TimeoutError after 60s timeout
        - Attempt 2: Success with valid response
        - Expected: Function returns successful response, retry happened
        """
        # Mock client and models
        mock_genai_client = Mock()
        mock_models = Mock()
        mock_genai_client.models = mock_models

        # First attempt: simulate timeout by raising TimeoutError
        # Second attempt: return successful response
        mock_response_success = Mock()
        mock_response_success.text = "Successfully transcribed text"
        mock_usage_metadata = Mock()
        mock_usage_metadata.prompt_token_count = 100
        mock_usage_metadata.candidates_token_count = 50
        mock_usage_metadata.total_token_count = 150
        mock_usage_metadata.cached_content_token_count = 0
        mock_response_success.usage_metadata = mock_usage_metadata
        # Mock candidates list
        mock_candidate = Mock()
        mock_candidate.finish_reason = "STOP"
        mock_response_success.candidates = [mock_candidate]

        # Use side_effect to control behavior per call
        call_count = [0]

        def generate_content_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: simulate timeout
                raise TimeoutError("Vertex AI call for test.jpg timed out after 60s (elapsed: 60.1s)")
            else:
                # Second call: success
                return mock_response_success

        mock_models.generate_content.side_effect = generate_content_side_effect

        # Mock time.time() for elapsed time calculations
        with patch('transcribe.time.time', side_effect=[0, 0, 0, 0, 60.1, 60.1, 60.1, 60.1, 90, 90, 92, 92, 92, 92, 92]):
            # Call transcribe_image
            text, elapsed_time, usage_metadata = transcribe_image(
                genai_client=mock_genai_client,
                image_bytes=b"fake image bytes",
                file_name="test.jpg",
                prompt_text="Transcribe this image",
                ocr_model_id="gemini-2.0-flash-exp"
            )

        # Verify success after retry
        assert text == "Successfully transcribed text"
        assert mock_models.generate_content.call_count == 2, \
            f"Expected 2 calls (1 timeout + 1 success), got {mock_models.generate_content.call_count}"

        # Verify sleep was called once (retry delay between attempts)
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(30)  # First retry delay is 30 seconds

    @patch('time.sleep')
    @patch('transcribe.logging')
    def test_all_retries_exhausted_with_timeout(self, mock_logging, mock_sleep):
        """Test behavior when all retry attempts timeout.

        Verifies SIGNAL-08: all retries exhausted scenario.
        All three attempts timeout, function returns error message.

        Integration scenario:
        - Attempt 1: TimeoutError after 60s timeout
        - Attempt 2: TimeoutError after 120s timeout
        - Attempt 3: TimeoutError after 300s timeout
        - Expected: Function returns error message after all retries exhausted
        """
        # Mock client and models
        mock_genai_client = Mock()
        mock_models = Mock()
        mock_genai_client.models = mock_models

        # All attempts: simulate timeout
        def generate_content_side_effect(*args, **kwargs):
            raise TimeoutError("Vertex AI call timed out")

        mock_models.generate_content.side_effect = generate_content_side_effect

        # Mock time.time() for elapsed time calculations (multiple timeout scenarios)
        time_values = [0, 0, 0, 0]  # function start, attempt 1 start
        time_values.extend([60.1, 60.1, 60.1, 60.1])  # attempt 1 timeout
        time_values.extend([90, 90, 90, 90])  # after retry delay
        time_values.extend([210, 210, 210, 210])  # attempt 2 timeout (90 + 120)
        time_values.extend([240, 240, 240, 240])  # after retry delay
        time_values.extend([540, 540, 540, 540])  # attempt 3 timeout (240 + 300)

        with patch('transcribe.time.time', side_effect=time_values):
            # Call transcribe_image
            text, elapsed_time, usage_metadata = transcribe_image(
                genai_client=mock_genai_client,
                image_bytes=b"fake image bytes",
                file_name="test.jpg",
                prompt_text="Transcribe this image",
                ocr_model_id="gemini-2.0-flash-exp"
            )

        # Verify all retries exhausted
        assert mock_models.generate_content.call_count == 3, \
            f"Expected 3 calls (all timeouts), got {mock_models.generate_content.call_count}"

        # Verify error message returned
        assert text.startswith("[Error during transcription:"), \
            f"Expected error message, got: {text}"
        assert "timed out" in text.lower() or "timeout" in text.lower(), \
            f"Expected timeout error message, got: {text}"

        # Verify elapsed_time and usage_metadata are None for failed transcription
        assert elapsed_time is None
        assert usage_metadata is None

        # Verify sleep was called twice (retry delays between attempts)
        assert mock_sleep.call_count == 2
        # First retry delay: 30s, second: 60s (exponential backoff)
        assert mock_sleep.call_args_list[0][0][0] == 30
        assert mock_sleep.call_args_list[1][0][0] == 60

    @patch('time.sleep')
    @patch('transcribe.logging')
    def test_timeout_preserves_exponential_backoff_timeouts(self, mock_logging, mock_sleep):
        """Test that timeout values follow exponential backoff pattern during retries.

        Verifies SIGNAL-02: exponential backoff preserved.
        Ensures retry attempts use correct timeout values: 60s, 120s, 300s.

        Integration scenario:
        - Each attempt uses different timeout value from exponential backoff list
        - Expected: Timeout values are [60, 120, 300] for attempts 1, 2, 3
        """
        # Mock client and models
        mock_genai_client = Mock()
        mock_models = Mock()
        mock_genai_client.models = mock_models

        # Track timeout values used in each attempt
        timeout_values_used = []

        def generate_content_side_effect(*args, **kwargs):
            # All attempts timeout to observe all timeout values
            raise TimeoutError("Vertex AI call timed out")

        mock_models.generate_content.side_effect = generate_content_side_effect

        # Mock TimeoutContext to capture timeout_seconds
        original_timeout_context = TimeoutContext

        class MockTimeoutContext:
            def __init__(self, timeout_seconds, operation_name):
                timeout_values_used.append(timeout_seconds)
                self.ctx = original_timeout_context(timeout_seconds, operation_name)

            def __enter__(self):
                return self.ctx.__enter__()

            def __exit__(self, exc_type, exc_val, exc_tb):
                return self.ctx.__exit__(exc_type, exc_val, exc_tb)

        # Mock time.time() for elapsed time calculations
        time_values = [0, 0, 0, 0]  # function start, attempt 1 start
        time_values.extend([60.1, 60.1, 60.1, 60.1])  # attempt 1 timeout
        time_values.extend([90, 90, 90, 90])  # after retry delay
        time_values.extend([210, 210, 210, 210])  # attempt 2 timeout
        time_values.extend([240, 240, 240, 240])  # after retry delay
        time_values.extend([540, 540, 540, 540])  # attempt 3 timeout

        with patch('transcribe.TimeoutContext', MockTimeoutContext):
            with patch('transcribe.time.time', side_effect=time_values):
                # Call transcribe_image
                text, elapsed_time, usage_metadata = transcribe_image(
                    genai_client=mock_genai_client,
                    image_bytes=b"fake image bytes",
                    file_name="test.jpg",
                    prompt_text="Transcribe this image",
                    ocr_model_id="gemini-2.0-flash-exp"
                )

        # Verify exponential backoff timeout values
        expected_timeouts = [60, 120, 300]
        assert timeout_values_used == expected_timeouts, \
            f"Expected timeout values {expected_timeouts}, got {timeout_values_used}"
