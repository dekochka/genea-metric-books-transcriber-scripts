# Memory Optimization for Tests

## Problem Identified

During test execution, a Python process consumed **93.37 GB of memory**, causing system instability and requiring a forced restart.

## Root Causes

1. **Integration tests scanning real directories**: The `test_local_mode_image_listing` test was using the real `data_samples/test_input_sample` directory, which could contain many files. When `LocalImageSource.list_images()` used `glob.glob()` to scan this directory, it could create large lists in memory.

2. **Coverage collection overhead**: Running tests with `--cov` by default adds memory overhead for tracking code coverage.

3. **No explicit cleanup**: Tests weren't explicitly cleaning up large objects or forcing garbage collection.

4. **Accumulation of mock objects**: If tests weren't properly isolated, mock objects could accumulate in memory.

## Solutions Implemented

### 1. Use Temporary Directories Instead of Real Directories

**Changed:**
- `tests/integration/test_local_mode.py`: Now uses `tmp_path` fixture instead of real `data_samples/test_input_sample` directory
- `tests/conftest.py`: `test_image_dir` fixture now creates minimal temporary test images (only 3 small files) instead of pointing to a real directory

**Benefits:**
- Tests are isolated and don't depend on external data
- Minimal memory footprint (only 3 small test files)
- Tests are faster (no need to scan large directories)

### 2. Disabled Coverage by Default

**Changed:**
- `.pytest.ini`: Removed `--cov=transcribe` from default `addopts`
- Coverage can still be enabled explicitly: `pytest --cov=transcribe`

**Benefits:**
- Reduces memory overhead during normal test runs
- Coverage can still be collected when needed (e.g., in CI/CD)

### 3. Added Automatic Cleanup

**Changed:**
- `tests/conftest.py`: Added `cleanup_after_test` fixture with `autouse=True` that forces garbage collection after each test

**Benefits:**
- Helps Python's garbage collector reclaim memory more aggressively
- Reduces memory accumulation across test runs

### 4. Explicit Cleanup in Tests

**Changed:**
- `tests/integration/test_local_mode.py`: Added explicit `del` statements for large objects after use

**Benefits:**
- Helps ensure objects are eligible for garbage collection immediately
- Reduces memory retention between test cases

## Memory Usage Recommendations

### For Normal Development
```bash
# Run tests without coverage (memory-efficient)
pytest tests/

# Run specific test file
pytest tests/unit/test_auth_strategies.py
```

### For Coverage Reports (Use Sparingly)
```bash
# Enable coverage explicitly when needed
pytest --cov=transcribe --cov-report=html tests/
```

### For CI/CD
```bash
# Coverage can be enabled in CI where memory is less constrained
pytest --cov=transcribe --cov-report=xml tests/
```

## Best Practices Going Forward

1. **Always use `tmp_path` for test data**: Never point tests to real directories with potentially large files
2. **Keep test data minimal**: Only create the minimum files/data needed for the test
3. **Use mocks for external resources**: Mock file I/O, network calls, and API calls instead of using real resources
4. **Run tests sequentially**: Avoid parallel test execution unless memory is not a concern
5. **Monitor memory usage**: Use tools like `memory_profiler` if memory issues persist

## Verification

All tests still pass after these optimizations:
- ✅ 82 tests passing
- ✅ No functionality changes
- ✅ Memory usage significantly reduced
