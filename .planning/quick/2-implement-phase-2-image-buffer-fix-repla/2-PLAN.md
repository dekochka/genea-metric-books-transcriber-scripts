---
phase: quick-2
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - transcribe.py
  - tests/unit/test_image_sources.py
autonomous: true
requirements: [BUFFER-01, BUFFER-02, BUFFER-03, BUFFER-04, BUFFER-05, BUFFER-06, BUFFER-07, BUFFER-08, BUFFER-09, BUFFER-10, BUFFER-11, BUFFER-12]

must_haves:
  truths:
    - "Tool correctly processes folders with sparse filename numbering (e.g., img_0500, img_0520, img_0700)"
    - "DriveImageSource handles folders with 1000+ images without Drive API timeouts"
    - "Existing configuration files work without modification"
    - "Performance remains acceptable (<30s for 1000-image folder enumeration)"
  artifacts:
    - path: "transcribe.py"
      provides: "fetch-all-then-filter implementation in list_images() function"
      min_lines: 80
      pattern: "# Fetch ALL images with pagination"
    - path: "tests/unit/test_image_sources.py"
      provides: "Comprehensive unit tests for sparse/contiguous/empty patterns"
      exports: ["test_drive_sparse_numbering", "test_drive_contiguous_numbering", "test_drive_empty_folder", "test_drive_single_image", "test_drive_pagination_large_folder"]
  key_links:
    - from: "transcribe.py:list_images()"
      to: "Drive API files().list()"
      via: "pagination loop fetching all images before filtering"
      pattern: "while.*pageToken|resp\\.get\\('nextPageToken'\\)"
    - from: "transcribe.py:list_images()"
      to: "image number extraction logic"
      via: "filter images by extracted number after fetch"
      pattern: "extract_image_number|image_start_number <= number"
---

<objective>
Replace 200-image buffer limitation with robust fetch-all-then-filter approach in DriveImageSource.list_images() to handle sparse filename numbering patterns.

Purpose: Users with sparse numbering patterns (gaps of 100+ between image numbers) can process their folders without missing images. Current 200-image buffer fails when start_number=500, count=20 because the buffer only fetches up to image 720, missing higher-numbered files.

Output:
- Updated list_images() function with fetch-all-then-filter logic
- Pagination support for 1000+ image folders
- Comprehensive unit tests validating sparse, contiguous, empty, and large folder scenarios
- Backward compatibility preserved (no config changes required)
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/research/ARCHITECTURE.md
@transcribe.py
@tests/unit/test_image_sources.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace buffer-based fetching with fetch-all-then-filter in list_images()</name>
  <files>transcribe.py</files>
  <action>
Modify the list_images() function (lines 2411-2700) to implement fetch-all-then-filter approach:

**Current problematic logic (lines 2437-2447):**
```python
# Auto-calculate max_images if not provided
max_images = config.get('max_images')
if max_images is None:
    image_start_number = config.get('image_start_number', 1)
    image_count = config.get('image_count', 1)
    # Buffer of 200 images to account for images that don't match the pattern
    calculated_max = image_start_number + image_count + 200
    # But cap at reasonable maximum (1,000) to avoid excessive API calls
    max_images = min(calculated_max, 1000)
```

**New approach:**
1. Remove max_images calculation entirely - fetch ALL images from folder with pagination
2. Update pagination loop (lines 2476-2531) to continue until no more pageToken (remove max_images limit check)
3. Keep existing filtering logic (lines 2569-2700) that filters by image_start_number and image_count - this is correct
4. Add logging to indicate fetch-all approach: "Fetching all images from folder (pagination enabled for 1000+ images)"

**PRESERVE unchanged:**
- Interface signature: list_images(drive_service, config: dict) - no breaking changes (BUFFER-02)
- All filename pattern extraction logic (lines 2578-2641) - already handles sparse patterns correctly
- Retry mode logic (lines 2542-2567) - independent of buffer issue
- Sort method handling (lines 2457-2466) - independent of buffer issue
- Filtering by image_start_number and image_count (lines 2644-2646) - this is the correct behavior

**Implementation details:**
- Remove lines 2437-2448 (max_images calculation)
- Change line 2476 from `while len(all_images) < max_images:` to `while True:`
- Remove line 2534 `all_images = all_images[:max_images]` (no longer needed)
- Add early logging after drive_folder_id extraction: `logging.info(f"Fetching all images from folder {drive_folder_id} (pagination enabled for large folders)")`

**Why this works for sparse patterns:**
- Old: Buffer limited to start + count + 200, so img_0500 to img_0700 would fetch up to ~920 images, missing img_0800+
- New: Fetch ALL images first (1, 2, 500, 520, 700, 800...), THEN filter by start_number <= number < start_number + count
- Trade-off: Slightly slower for large folders but acceptable (<30s for 1000 images per BUFFER-09)

**Pagination already handles 1000+ images:**
- Existing pageSize=100 with nextPageToken iteration (lines 2491-2502) already supports pagination
- No changes needed - just remove artificial max_images cap to let pagination complete fully
  </action>
  <verify>
Run existing image source tests to confirm no regression:
```bash
pytest tests/unit/test_image_sources.py -v
```

Manually verify the change compiles and logging is correct:
```bash
python -c "import transcribe; print('Import successful')"
```
  </verify>
  <done>
- list_images() function no longer uses max_images calculation with 200-image buffer
- Pagination loop fetches ALL images from folder until no nextPageToken
- Filtering by image_start_number and image_count happens AFTER full fetch
- Logging indicates fetch-all approach with pagination support
- No changes to function signature or return type (backward compatible)
  </done>
</task>

<task type="auto">
  <name>Task 2: Add comprehensive unit tests for buffer fix validation</name>
  <files>tests/unit/test_image_sources.py</files>
  <action>
Add unit tests to tests/unit/test_image_sources.py validating all buffer-related requirements:

**Test 1: Sparse numbering patterns (BUFFER-03, BUFFER-05)**
```python
def test_drive_sparse_numbering(mock_drive_service):
    """Test DriveImageSource handles sparse filename numbering (gaps of 100+)."""
    # Mock Drive API to return images with large gaps: img_0500, img_0520, img_0700, img_0800
    mock_files = [
        {'id': '1', 'name': 'image00500.jpg', 'webViewLink': 'https://drive.google.com/1'},
        {'id': '2', 'name': 'image00520.jpg', 'webViewLink': 'https://drive.google.com/2'},
        {'id': '3', 'name': 'image00700.jpg', 'webViewLink': 'https://drive.google.com/3'},
        {'id': '4', 'name': 'image00800.jpg', 'webViewLink': 'https://drive.google.com/4'},
    ]
    mock_drive_service.files().list().execute.return_value = {
        'files': mock_files,
        'nextPageToken': None
    }

    config = {
        'drive_folder_id': 'test_folder',
        'image_start_number': 500,
        'image_count': 301,  # Should capture 500, 520, 700, 800
        'image_sort_method': 'name_asc'
    }

    result = list_images(mock_drive_service, config)

    # Should find all 4 images (500, 520, 700, 800 all in range 500-800)
    assert len(result) == 4
    assert result[0]['name'] == 'image00500.jpg'
    assert result[3]['name'] == 'image00800.jpg'
```

**Test 2: Contiguous numbering (BUFFER-06)**
```python
def test_drive_contiguous_numbering(mock_drive_service):
    """Test DriveImageSource handles contiguous numbering (1, 2, 3, ...)."""
    mock_files = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                  for i in range(1, 51)]
    mock_drive_service.files().list().execute.return_value = {
        'files': mock_files,
        'nextPageToken': None
    }

    config = {
        'drive_folder_id': 'test_folder',
        'image_start_number': 10,
        'image_count': 20,
        'image_sort_method': 'name_asc'
    }

    result = list_images(mock_drive_service, config)

    # Should find exactly 20 images (10-29)
    assert len(result) == 20
    assert result[0]['name'] == 'image00010.jpg'
    assert result[19]['name'] == 'image00029.jpg'
```

**Test 3: Empty folder (BUFFER-08)**
```python
def test_drive_empty_folder(mock_drive_service):
    """Test DriveImageSource handles empty folder gracefully."""
    mock_drive_service.files().list().execute.return_value = {
        'files': [],
        'nextPageToken': None
    }

    config = {
        'drive_folder_id': 'test_folder',
        'image_start_number': 1,
        'image_count': 10,
        'image_sort_method': 'name_asc'
    }

    result = list_images(mock_drive_service, config)
    assert len(result) == 0
```

**Test 4: Single image (BUFFER-07)**
```python
def test_drive_single_image(mock_drive_service):
    """Test DriveImageSource handles single image in folder."""
    mock_drive_service.files().list().execute.return_value = {
        'files': [{'id': '1', 'name': 'image00001.jpg', 'webViewLink': 'https://drive.google.com/1'}],
        'nextPageToken': None
    }

    config = {
        'drive_folder_id': 'test_folder',
        'image_start_number': 1,
        'image_count': 1,
        'image_sort_method': 'name_asc'
    }

    result = list_images(mock_drive_service, config)
    assert len(result) == 1
    assert result[0]['name'] == 'image00001.jpg'
```

**Test 5: Pagination for large folders (BUFFER-04, BUFFER-09)**
```python
def test_drive_pagination_large_folder(mock_drive_service):
    """Test DriveImageSource handles pagination for 1000+ images."""
    # Simulate pagination: first call returns 100 images + token, second call returns 100 more
    mock_files_page1 = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                        for i in range(1, 101)]
    mock_files_page2 = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                        for i in range(101, 201)]

    # Mock pagination responses
    mock_drive_service.files().list().execute.side_effect = [
        {'files': mock_files_page1, 'nextPageToken': 'token123'},
        {'files': mock_files_page2, 'nextPageToken': None}
    ]

    config = {
        'drive_folder_id': 'test_folder',
        'image_start_number': 50,
        'image_count': 100,
        'image_sort_method': 'name_asc'
    }

    result = list_images(mock_drive_service, config)

    # Should find 100 images (50-149)
    assert len(result) == 100
    assert result[0]['name'] == 'image00050.jpg'
    assert result[99]['name'] == 'image00149.jpg'
```

**Mock setup:**
Use pytest fixtures with unittest.mock to create mock Drive service. Follow existing test patterns in test_image_sources.py.

**Coverage validation:**
These tests directly validate requirements BUFFER-01 through BUFFER-10. BUFFER-11 (backward compatibility) validated by existing tests still passing. BUFFER-12 (memory) validated implicitly by not loading image bytes in list_images().
  </action>
  <verify>
Run new tests to validate all scenarios:
```bash
pytest tests/unit/test_image_sources.py::test_drive_sparse_numbering -v
pytest tests/unit/test_image_sources.py::test_drive_contiguous_numbering -v
pytest tests/unit/test_image_sources.py::test_drive_empty_folder -v
pytest tests/unit/test_image_sources.py::test_drive_single_image -v
pytest tests/unit/test_image_sources.py::test_drive_pagination_large_folder -v
```

Run full test suite to ensure no regressions:
```bash
pytest tests/unit/test_image_sources.py -v
```
  </verify>
  <done>
- Five new unit tests added covering sparse, contiguous, empty, single-image, and pagination scenarios
- All tests pass with fetch-all-then-filter implementation
- Tests use mocked Drive API (no real Drive calls)
- Coverage includes all BUFFER-01 through BUFFER-10 requirements
- Existing tests continue to pass (backward compatibility confirmed)
  </done>
</task>

</tasks>

<verification>
Run complete test suite to validate fix and ensure no regressions:
```bash
# Unit tests for image sources
pytest tests/unit/test_image_sources.py -v

# Full unit test suite
pytest tests/unit/ -v

# Check for any integration test failures
pytest tests/integration/ -v -k "drive or image" 2>/dev/null || echo "No matching integration tests"
```

Verify backward compatibility with existing configs:
```bash
# Check that config parsing still works
python -c "
import transcribe
config = {
    'googlecloud': {
        'drive_folder_id': 'test123',
        'document_name': 'Test Document'
    },
    'image_start_number': 1,
    'image_count': 10
}
print('Config parsing: OK')
"
```

Performance validation (manual check):
- Fetch-all approach should complete in <30s for 1000-image folder
- This will be validated in actual usage (BUFFER-09)
- No automated performance test needed for quick task (can add in Phase 4 integration testing)
</verification>

<success_criteria>
**Code Changes:**
- [ ] list_images() removes 200-image buffer calculation (lines 2437-2448 deleted)
- [ ] Pagination loop fetches ALL images (no max_images limit)
- [ ] Filtering by image_start_number/count happens after full fetch
- [ ] Logging indicates fetch-all approach with pagination support

**Testing:**
- [ ] test_drive_sparse_numbering validates sparse patterns (gaps of 100+)
- [ ] test_drive_contiguous_numbering validates contiguous patterns
- [ ] test_drive_empty_folder validates empty folder gracefully handled
- [ ] test_drive_single_image validates single image works
- [ ] test_drive_pagination_large_folder validates 1000+ image pagination
- [ ] All existing image source tests still pass (backward compatibility)

**Requirements Satisfied:**
- [ ] BUFFER-01: Fetch-all-then-filter implemented
- [ ] BUFFER-02: Interface signature unchanged
- [ ] BUFFER-03: Sparse patterns handled correctly
- [ ] BUFFER-04: Pagination implemented
- [ ] BUFFER-05 through BUFFER-10: Validated by unit tests
- [ ] BUFFER-11: Backward compatibility confirmed by existing tests passing
- [ ] BUFFER-12: No memory issues (list_images only fetches metadata, not image bytes)

**Observable Behavior:**
- [ ] Users can process folders with start_number=500, count=20 without missing images
- [ ] Large folders (1000+ images) process without Drive API timeouts
- [ ] Existing configurations continue to work without modification
</success_criteria>

<output>
After completion, create `.planning/quick/2-implement-phase-2-image-buffer-fix-repla/2-SUMMARY.md`
</output>
