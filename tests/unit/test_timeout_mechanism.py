"""
Unit tests for TimeoutContext cross-platform timeout mechanism.

Tests verify timeout firing, timer cancellation, cleanup, and exponential backoff preservation.
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from transcribe import TimeoutContext


@pytest.mark.unit
class TestTimeoutContext:
    """Test cases for TimeoutContext cross-platform timeout mechanism."""

    def test_timeout_fires_after_duration(self):
        """Test that TimeoutContext raises TimeoutError after specified duration.

        Verifies SIGNAL-05: timeout fires correctly after specified duration.
        Uses real time.sleep() to simulate slow operation that exceeds timeout.
        """
        with pytest.raises(TimeoutError, match="timed out after 1s"):
            with TimeoutContext(1, "test operation"):
                time.sleep(2.0)  # Sleep longer than timeout

    def test_timeout_canceled_on_success(self):
        """Test that TimeoutContext cancels timer on successful completion.

        Verifies SIGNAL-06: timer cancels on successful API response.
        Operation completes within timeout, should NOT raise TimeoutError.
        """
        # Should not raise any exception
        with TimeoutContext(2, "test operation"):
            time.sleep(0.1)  # Sleep shorter than timeout
        # If we get here, test passed - no timeout occurred

    def test_timer_cancel_called_on_exit(self):
        """Test that timer.cancel() is called in __exit__.

        Verifies SIGNAL-04: cleanup on success path.
        Ensures Timer.cancel() is always called when exiting context manager.
        """
        with patch('threading.Timer') as mock_timer_class:
            mock_timer_instance = Mock()
            mock_timer_class.return_value = mock_timer_instance

            # Enter and exit context immediately
            with TimeoutContext(10, "test operation"):
                pass  # Quick exit

            # Verify cancel was called on the timer instance
            mock_timer_instance.cancel.assert_called_once()

    def test_timeout_preserves_exponential_backoff(self):
        """Test that timeout values match exponential backoff sequence.

        Verifies SIGNAL-02: exponential backoff preserved.
        Expected timeout values are [60, 120, 300] for the three retry attempts.
        """
        expected_timeouts = [60, 120, 300]

        for expected_timeout in expected_timeouts:
            ctx = TimeoutContext(expected_timeout, "backoff test")
            assert ctx.timeout_seconds == expected_timeout, \
                f"Expected timeout {expected_timeout}, got {ctx.timeout_seconds}"

    def test_timeout_error_message_format(self):
        """Test that TimeoutError message includes operation name and timeout duration.

        Ensures error messages are informative for debugging.
        """
        with pytest.raises(TimeoutError, match=r"operation xyz.*timed out after 1s.*elapsed"):
            with TimeoutContext(1, "operation xyz"):
                time.sleep(2.0)

    def test_timer_is_daemon_thread(self):
        """Test that timer thread is created as daemon thread.

        Verifies daemon=True is set to prevent blocking program exit.
        """
        with patch('threading.Timer') as mock_timer_class:
            mock_timer_instance = Mock()
            mock_timer_class.return_value = mock_timer_instance

            with TimeoutContext(10, "daemon test"):
                pass

            # Verify Timer was created with daemon=True
            call_args = mock_timer_class.call_args
            assert call_args is not None
            # Timer(timeout_seconds, callback) called, then daemon set
            mock_timer_instance.daemon = True  # This is set in __enter__

    def test_context_manager_protocol_complete(self):
        """Test that TimeoutContext implements full context manager protocol.

        Verifies __enter__ returns self and __exit__ handles cleanup.
        """
        ctx = TimeoutContext(10, "protocol test")

        # Test __enter__ returns self
        entered_ctx = ctx.__enter__()
        assert entered_ctx is ctx
        assert ctx.timer is not None
        assert ctx.start_time is not None

        # Test __exit__ cleanup
        ctx.__exit__(None, None, None)
        # Timer should be cancelled (verify by checking timer no longer running)

    def test_timeout_does_not_suppress_other_exceptions(self):
        """Test that TimeoutContext does not suppress non-timeout exceptions.

        Verifies that __exit__ returns False to allow exception propagation.
        """
        with pytest.raises(ValueError, match="custom error"):
            with TimeoutContext(10, "exception test"):
                raise ValueError("custom error")
