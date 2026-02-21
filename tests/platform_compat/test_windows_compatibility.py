"""
Platform-specific tests for Windows compatibility.

These tests verify that the transcription tool can run on Windows without
AttributeError from Unix-only signal.SIGALRM. Tests are skipped on non-Windows
platforms using pytest.mark.skipif.
"""

import sys
import pytest
import inspect
from unittest.mock import Mock

# Import the transcribe module to verify cross-platform compatibility
import transcribe


@pytest.mark.platform
class TestWindowsCompatibility:
    """
    Platform-specific tests verifying Windows compatibility.

    These tests run only on Windows (sys.platform == "win32") and verify:
    1. signal.SIGALRM is not used in transcribe_image function
    2. transcribe module can be imported without AttributeError
    """

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_no_signal_module_imports(self):
        """
        Verify that transcribe_image does not reference signal.SIGALRM or signal.alarm.

        This test inspects the source code of transcribe_image to ensure it uses
        threading.Timer instead of Unix-only signal module for timeout handling.
        Satisfies SIGNAL-10 (no AttributeError on Windows).
        """
        # Get the source code of transcribe_image function
        source_code = inspect.getsource(transcribe.transcribe_image)

        # Verify signal.SIGALRM is not used (Unix-only)
        assert "signal.SIGALRM" not in source_code, \
            "transcribe_image should not use signal.SIGALRM (Unix-only)"

        # Verify signal.alarm is not used (Unix-only)
        assert "signal.alarm" not in source_code, \
            "transcribe_image should not use signal.alarm (Unix-only)"

        # Verify threading.Timer is used instead (cross-platform)
        assert "threading.Timer" in source_code or "TimeoutContext" in source_code, \
            "transcribe_image should use threading.Timer or TimeoutContext for cross-platform timeout"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_transcribe_runs_on_windows(self):
        """
        Verify that transcribe module can be imported on Windows without AttributeError.

        This test creates a mock Vertex AI client and verifies that the transcribe
        module can be instantiated without errors. Satisfies SIGNAL-10 (no AttributeError
        on Windows during import or instantiation).
        """
        # Create mock genai client
        mock_client = Mock()
        mock_client.models = Mock()

        # Attempt to create VertexAIClient instance
        # This should not raise AttributeError on Windows
        try:
            # Test basic import and function access
            assert hasattr(transcribe, 'transcribe_image'), \
                "transcribe module should have transcribe_image function"

            # Verify TimeoutContext class exists (replacement for signal-based timeout)
            assert hasattr(transcribe, 'TimeoutContext'), \
                "transcribe module should have TimeoutContext class"

            # Test that TimeoutContext can be instantiated
            timeout_ctx = transcribe.TimeoutContext(timeout_seconds=60, operation_name="test")
            assert timeout_ctx is not None, \
                "TimeoutContext should be instantiable on Windows"

        except AttributeError as e:
            pytest.fail(f"Windows compatibility test failed with AttributeError: {e}")
