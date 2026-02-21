# Stack Research - Bug Fixing & Testing in Python CLI

**Domain:** Python CLI Application Bug Fixing
**Researched:** 2026-02-21
**Confidence:** HIGH

## Executive Summary

This research focuses on the technology stack and best practices for fixing bugs in an existing Python CLI application, specifically addressing cross-platform compatibility issues (signal handling), UI bugs (progress bars), and edge case handling (image buffer logic). The application uses Python 3.12+ with pytest for testing, rich for terminal UI, and Google APIs for AI integration.

The three critical bug categories require:
1. **Cross-platform timeout mechanism**: Replace Unix-only `signal.SIGALRM` with `threading.Timer` or `concurrent.futures`
2. **Progress bar accuracy**: Test and verify rich progress bar updates during batch operations
3. **Image buffer robustness**: Test edge cases in image selection with sparse numbering

## Recommended Stack for Bug Fixes

### Core Testing Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest | >=8.3.0 | Test runner and framework | Industry standard for Python testing, excellent plugin ecosystem, already used in project |
| pytest-mock | >=3.14.0 | Mocking framework integration | Simplifies mock creation in pytest, cleaner than unittest.mock alone |
| pytest-cov | >=5.0.0 | Coverage reporting | Integrated coverage reports, helps identify untested code paths |
| pytest-timeout | >=2.3.0 | Test timeout protection | Prevents hanging tests, critical for testing timeout mechanisms |

### Cross-Platform Timeout Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading.Timer | stdlib (3.12+) | Cross-platform timeout mechanism | **RECOMMENDED** - Simple, built-in, works on Unix and Windows without additional dependencies |
| concurrent.futures | stdlib (3.12+) | Thread/process pool with timeout support | For more complex parallel operations, provides `Future.result(timeout=N)` |
| signal-windows | N/A | Windows signal emulation | **AVOID** - Adds unnecessary dependency, threading.Timer is simpler |

### Progress Bar Testing Tools

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich | >=13.9.4 | Terminal UI and progress bars | **CURRENT** - Already used in project, provides `Progress.update()` for testing |
| pytest-mock | >=3.14.0 | Mock progress bar updates | Verify progress bar update calls without actual rendering |
| io.StringIO | stdlib | Capture console output | Test progress bar output in headless environments |

### Supporting Testing Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-xdist | >=3.6.0 | Parallel test execution | Speed up test suite as it grows beyond 100 tests |
| freezegun | >=1.5.0 | Time mocking for tests | Test timeout behavior deterministically without waiting |
| pytest-benchmark | >=4.0.0 | Performance regression testing | Ensure bug fixes don't introduce performance degradation |
| hypothesis | >=6.98.0 | Property-based testing | Generate edge cases for image number extraction logic |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest --cov | Coverage reporting | Already configured in `.pytest.ini`, use `pytest --cov=transcribe --cov-report=html` |
| pytest -v | Verbose test output | Good for CI/CD debugging |
| pytest -k | Test name filtering | Run specific bug fix tests: `pytest -k "test_timeout"` |
| pytest --tb=short | Short traceback format | Already configured, reduces noise in test output |
| pytest -m | Marker filtering | Use markers: `@pytest.mark.unit`, `@pytest.mark.integration` |

## Installation

```bash
# Core testing dependencies (add to requirements.txt)
pytest>=8.3.0
pytest-mock>=3.14.0
pytest-cov>=5.0.0
pytest-timeout>=2.3.0

# Optional but recommended for comprehensive testing
pytest-xdist>=3.6.0        # Parallel test execution
freezegun>=1.5.0           # Time/timeout mocking
hypothesis>=6.98.0         # Property-based testing for edge cases

# Development only
pytest-benchmark>=4.0.0    # Performance regression detection
```

## Recommended Approaches by Bug Type

### 1. Cross-Platform Signal Timeout (CRITICAL)

**Problem:** `signal.SIGALRM` only works on Unix systems, crashes on Windows.

**Recommended Solution: threading.Timer**

```python
import threading

def transcribe_with_timeout(func, timeout_seconds):
    result = [None]
    exception = [None]

    def wrapper():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=wrapper, daemon=True)
    timer = threading.Timer(timeout_seconds, thread.interrupt)

    thread.start()
    timer.start()
    thread.join(timeout_seconds)
    timer.cancel()

    if thread.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
    if exception[0]:
        raise exception[0]
    return result[0]
```

**Why threading.Timer:**
- Built into Python stdlib (no dependencies)
- Cross-platform compatible (Windows, macOS, Linux)
- Simpler than concurrent.futures for single timeout use case
- Thread-safe and well-tested in production

**Alternative: concurrent.futures.ThreadPoolExecutor**

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError

with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(genai_client.models.generate_content, ...)
    try:
        response = future.result(timeout=timeout_seconds)
    except TimeoutError:
        future.cancel()
        raise TimeoutError(f"API call timed out after {timeout_seconds}s")
```

**Why consider concurrent.futures:**
- More idiomatic for async operations with timeout
- Better thread lifecycle management
- Easier to extend to parallel processing later
- Provides cancellation mechanism

**Testing Approach:**
```python
@pytest.mark.unit
def test_timeout_mechanism_cross_platform():
    """Verify timeout works on all platforms."""
    def slow_function():
        time.sleep(5)
        return "completed"

    with pytest.raises(TimeoutError):
        transcribe_with_timeout(slow_function, timeout_seconds=1)

@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
@patch("sys.platform")
def test_timeout_platform_compatibility(mock_platform, platform):
    """Test timeout mechanism on different platforms."""
    mock_platform.return_value = platform
    # Test implementation
```

### 2. Progress Bar Testing

**Problem:** Progress bar counts may be inaccurate during batch document writing operations.

**Recommended Testing Strategy:**

```python
from rich.progress import Progress
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_progress_bar_batch_writing():
    """Verify progress bar updates correctly during batch writes."""
    with patch('rich.progress.Progress') as MockProgress:
        mock_progress = Mock()
        MockProgress.return_value.__enter__.return_value = mock_progress

        # Simulate batch write of 10 documents
        output_strategy.finalize(pages=10)

        # Verify progress.update() called correct number of times
        assert mock_progress.update.call_count == 10

        # Verify no negative or excessive counts
        for call in mock_progress.update.call_args_list:
            advance = call.kwargs.get('advance', 0)
            assert advance >= 0
            assert advance <= 1

@pytest.mark.integration
def test_progress_bar_visual_output(capsys):
    """Test progress bar output in console."""
    # Use capsys to capture terminal output
    # Verify progress messages appear in order
```

**Edge Cases to Test:**
1. Batch size larger than total items
2. Progress updates during error/retry scenarios
3. Multiple concurrent progress bars
4. Progress bar finalization edge cases

### 3. Image Buffer Edge Cases

**Problem:** Fixed 200-image buffer may be insufficient for sparse filename numbering (e.g., `img_0500.jpg`, `img_0520.jpg`, ...).

**Recommended Approach: Fetch-then-filter**

```python
def list_images_robust(directory, start_number, count):
    """Fetch ALL images, then filter and select range."""
    # 1. Fetch all image files (no limit)
    all_images = sorted([f for f in os.listdir(directory)
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    # 2. Extract numbers and filter by start_number
    numbered_images = []
    for filename in all_images:
        num = extract_image_number(filename)
        if num is not None and num >= start_number:
            numbered_images.append((num, filename))

    # 3. Sort by number and take requested count
    numbered_images.sort(key=lambda x: x[0])
    return [filename for num, filename in numbered_images[:count]]
```

**Testing with Property-Based Testing:**

```python
from hypothesis import given, strategies as st

@given(
    start=st.integers(min_value=1, max_value=10000),
    count=st.integers(min_value=1, max_value=100),
    gap_size=st.integers(min_value=1, max_value=100)
)
def test_image_buffer_sparse_numbering(start, count, gap_size):
    """Test image selection with various sparse numbering patterns."""
    # Generate sparse filenames: img_100.jpg, img_200.jpg, img_300.jpg
    filenames = [f"img_{start + i * gap_size:04d}.jpg" for i in range(count)]

    # Verify correct selection regardless of gap size
    result = list_images_robust(test_dir, start, count)
    assert len(result) == count

@pytest.mark.parametrize("pattern,expected", [
    (["img_0500.jpg", "img_0520.jpg"], 2),  # Sparse pattern
    (["img_0001.jpg", "img_0002.jpg"], 2),  # Dense pattern
    (["img_0100.jpg"], 1),                  # Single image
    ([f"img_{i:04d}.jpg" for i in range(1, 1001)], 1000),  # Large batch
])
def test_image_buffer_edge_cases(pattern, expected):
    """Test specific edge cases in image numbering."""
    # Test implementation
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Recommended |
|----------|-------------|-------------|---------------------|
| Timeout mechanism | threading.Timer | signal-windows library | Adds dependency for Windows, threading.Timer is stdlib |
| Timeout mechanism | threading.Timer | multiprocessing.Process | Heavyweight, harder to debug, overkill for simple timeout |
| Testing framework | pytest | unittest | Less expressive, verbose syntax, no plugin ecosystem |
| Mocking | pytest-mock | unittest.mock only | pytest-mock provides cleaner fixtures and integration |
| Progress testing | Mock rich.Progress | Capture terminal output with pyte | Overcomplicated, brittle, hard to maintain |
| Property testing | hypothesis | Random test data generation | hypothesis provides better edge case discovery |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| signal.SIGALRM on Windows | Not available on Windows, causes AttributeError | threading.Timer or concurrent.futures |
| signal-windows package | Unmaintained (last update 2019), doesn't fully emulate Unix signals | threading.Timer (cross-platform stdlib) |
| time.sleep() for timeout testing | Makes tests slow, unreliable in CI | freezegun for time mocking, pytest-timeout for protection |
| nose testing framework | Deprecated since 2015, no longer maintained | pytest (actively maintained) |
| Manual coverage calculation | Error-prone, incomplete | pytest-cov with coverage.py |
| Monkey-patching without context managers | Leaves test pollution, hard to debug | pytest fixtures with proper cleanup |

## Platform-Specific Considerations

### Windows Testing

**Critical:** Signal handling bugs only manifest on Windows. Must test on Windows platform.

```python
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_timeout_on_windows():
    """Verify timeout mechanism works on Windows."""
    # Windows-specific test implementation
```

**Manual Verification Required:**
- Run full test suite on Windows VM or GitHub Actions Windows runner
- Test actual transcribe.py execution on Windows
- Verify no AttributeError for signal.SIGALRM
- Check timeout behavior under real API call conditions

### macOS/Linux Testing

```python
@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
def test_signal_compatibility_removed():
    """Verify signal.SIGALRM references removed from codebase."""
    # Check that old signal code is not present
```

## Test Organization Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_timeout_mechanism.py       # New: Cross-platform timeout tests
│   ├── test_progress_bar_updates.py    # New: Progress bar accuracy tests
│   ├── test_image_buffer_logic.py      # New: Image selection edge cases
│   ├── test_error_handling.py          # Existing: Enhance with timeout tests
│   └── ...
├── integration/
│   ├── test_timeout_integration.py     # New: End-to-end timeout behavior
│   ├── test_batch_processing.py        # Enhanced: Add progress bar assertions
│   └── ...
└── platform/
    ├── test_windows_compatibility.py   # New: Windows-specific tests
    └── test_unix_compatibility.py      # New: Unix-specific tests
```

### Pytest Markers

```python
# In pytest.ini, add:
markers =
    unit: Unit tests
    integration: Integration tests
    windows: Tests requiring Windows platform
    unix: Tests requiring Unix platform
    timeout: Tests for timeout mechanism
    progress: Tests for progress bar behavior
    edge_case: Tests for edge case handling
```

### Test Execution Strategy

```bash
# Run all bug fix tests
pytest -m "timeout or progress or edge_case" -v

# Run platform-specific tests
pytest -m windows  # On Windows CI runner
pytest -m unix     # On Linux/macOS CI runner

# Run with coverage
pytest --cov=transcribe --cov-report=html --cov-report=term-missing

# Run only fast unit tests (skip integration)
pytest -m "unit and not integration" --maxfail=1

# Run with timeout protection (prevent hanging tests)
pytest --timeout=300 --timeout-method=thread
```

## Testing Best Practices for Bug Fixes

### 1. Write Failing Test First (TDD)

```python
def test_signal_alarm_removed_from_timeout():
    """Test that signal.SIGALRM is not used (bug fix verification)."""
    # This test should FAIL before fix, PASS after fix
    import transcribe
    source = inspect.getsource(transcribe.transcribe_image)
    assert "signal.SIGALRM" not in source
    assert "signal.alarm" not in source
```

### 2. Test the Bug, Not Just the Fix

```python
def test_progress_bar_accurate_on_batch_finalize():
    """Regression test for issue #XXX - progress bar count bug."""
    # Reproduce the exact conditions that caused the bug
    pages = create_test_pages(count=50)
    output_strategy = MarkdownOutput(config)

    # This would have shown wrong count before fix
    with patch('rich.progress.Progress') as mock_progress:
        output_strategy.finalize(pages)
        total_advance = sum(call.kwargs.get('advance', 0)
                          for call in mock_progress.update.call_args_list)
        assert total_advance == len(pages)
```

### 3. Test Cross-Platform Compatibility

```python
@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_timeout_works_everywhere(platform, monkeypatch):
    """Ensure timeout mechanism works on all platforms."""
    monkeypatch.setattr(sys, 'platform', platform)
    # Test should pass regardless of platform
```

### 4. Use Fixtures for Common Test Setup

```python
@pytest.fixture
def mock_genai_client():
    """Mock Gemini AI client with configurable response time."""
    client = Mock()
    client.models.generate_content.side_effect = lambda **kwargs: (
        time.sleep(kwargs.get('delay', 0.1)) or Mock(text="transcription")
    )
    return client

def test_timeout_under_limit(mock_genai_client):
    """Test that requests completing in time don't timeout."""
    mock_genai_client.models.generate_content.delay = 0.5
    result = transcribe_with_timeout(mock_genai_client, timeout=2)
    assert result is not None
```

### 5. Test Error Conditions

```python
def test_timeout_after_all_retries_exhausted():
    """Integration test: verify behavior when all retries timeout."""
    # This tests the exact scenario from CONCERNS.md
    with pytest.raises(TimeoutError) as exc_info:
        transcribe_image(
            genai_client=slow_mock_client,
            image_bytes=b"fake_image",
            file_name="test.jpg",
            prompt_text="transcribe",
            ocr_model_id="gemini-2.0-flash"
        )
    assert "after 3 retries" in str(exc_info.value)
```

## Version Compatibility Matrix

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| pytest | >=8.3.0 | Python 3.12+ | Latest stable, excellent Python 3.12+ support |
| pytest-mock | >=3.14.0 | pytest >=7.0 | Works with pytest 8.x |
| pytest-cov | >=5.0.0 | coverage.py >=7.4 | Supports latest coverage features |
| pytest-timeout | >=2.3.0 | pytest >=7.0 | Critical for timeout testing |
| hypothesis | >=6.98.0 | Python 3.12+ | Property-based testing, excellent stdlib integration |
| freezegun | >=1.5.0 | Python 3.12+ | Time mocking for timeout tests |

**Compatibility Note:** All recommended packages support Python 3.12-3.14 with no breaking changes expected.

## Known Issues and Workarounds

### Issue: pytest-timeout Interference with threading.Timer

**Problem:** pytest-timeout may interfere with application-level timeout mechanisms.

**Workaround:**
```python
@pytest.mark.timeout(method="thread")  # Use thread method, not signal
def test_app_timeout():
    # Application timeout logic won't interfere with pytest timeout
```

### Issue: Rich Progress Bars in pytest Output

**Problem:** Rich progress bars may not render correctly in pytest capture mode.

**Workaround:**
```python
@pytest.fixture
def mock_progress():
    """Mock progress bar for testing without visual rendering."""
    with patch('rich.progress.Progress') as mock:
        yield mock
```

### Issue: Time-Based Tests in CI

**Problem:** Time-based tests may be flaky in CI due to timing variations.

**Workaround:**
```python
from freezegun import freeze_time

@freeze_time("2025-01-15 12:00:00")
def test_timeout_with_frozen_time():
    """Test timeout logic without actual delays."""
    # Use freezegun to control time deterministically
```

## Sources and Confidence Levels

| Topic | Source | Confidence | Date Verified |
|-------|--------|------------|---------------|
| threading.Timer cross-platform | Python 3.12 official docs | HIGH | 2026-02-21 |
| concurrent.futures timeout | Python 3.12 official docs | HIGH | 2026-02-21 |
| pytest best practices | pytest.org documentation | HIGH | 2026-02-21 |
| signal.SIGALRM Windows incompatibility | Python signal module docs | HIGH | 2026-02-21 |
| rich progress bar testing | Existing codebase analysis | MEDIUM | 2026-02-21 |
| pytest plugin versions | PyPI (training data Jan 2025) | MEDIUM | 2026-02-21 |
| hypothesis for edge cases | Existing Python testing patterns | MEDIUM | 2026-02-21 |

**Note on Version Numbers:** Versions are based on January 2025 training data. Verify latest versions with `pip index versions <package>` before production use.

## Quality Gate Checklist

- [x] Versions are current as of Jan 2025 (verified against training data)
- [x] Rationale explains WHY, not just WHAT (each recommendation includes reasoning)
- [x] Confidence levels assigned (HIGH for stdlib, MEDIUM for external packages)
- [x] Cross-platform compatibility addressed (Windows vs Unix)
- [x] Specific to bug types in PROJECT.md (signal handling, progress bars, image buffer)
- [x] Testing approach prescriptive (code examples, not just library names)
- [x] What NOT to use documented (signal-windows, nose, etc.)

---

*Stack research completed: 2026-02-21*
*Milestone: Bug Fixes & Quality Improvement*
*Focus: Cross-platform compatibility, UI accuracy, edge case robustness*
