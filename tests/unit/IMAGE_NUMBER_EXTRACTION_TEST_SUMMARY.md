# Image Number Extraction - Test Coverage Summary

## Overview

This document summarizes the test coverage for image number extraction functionality, including the improvements made to handle various filename patterns and special symbols.

## Test File

**File:** `tests/unit/test_image_number_extraction.py`

**Total Test Classes:** 6
**Total Test Methods:** ~40+

---

## Test Scenarios Covered

### 1. Basic Pattern Recognition (`TestExtractImageNumber`)

#### Standard Patterns
- ✅ **`image (N).jpg`** - Parentheses format
  - Examples: `image (7).jpg`, `image (10).jpeg`, `image (155).JPG`
  - Case-insensitive support

- ✅ **`imageXXXXX.jpg`** - Prefix with zero-padded numbers
  - Examples: `image00001.jpg`, `image00101.jpg`, `image00155.jpeg`
  - Handles 5-digit zero-padded format

- ✅ **`XXXXX.jpg`** - Number-only filenames
  - Examples: `52.jpg`, `102.jpeg`, `155.JPG`
  - Simple numeric filenames

- ✅ **`PREFIX_XXXXX.jpg`** - Underscore separator (original pattern)
  - Examples: `007821451_00155.jpeg`, `004933159_00216.jpeg`
  - Extracts number after last underscore

#### Improved Pattern Detection (NEW)

- ✅ **`PREFIX-XXXXX.jpg`** - Dash separator
  - Examples: `007821451-00155.jpeg`, `prefix-12345.jpg`
  - Detects number after last dash

- ✅ **`PREFIX.XXXXX.jpg`** - Dot separator
  - Examples: `007821451.00155.jpeg`, `prefix.12345.jpg`
  - Detects number after last dot

- ✅ **Multiple Separators** - Handles mixed separators
  - Examples: `prefix-part1-part2-00155.jpeg`, `007821451.section.page.00155.jpeg`
  - Uses last separator found

#### Special Formats

- ✅ **`IMG_YYYYMMDD_XXXX.jpg`** - Date-based format
  - Examples: `IMG_20250814_0036.jpg`, `IMG_20250101_1234.jpeg`
  - Extracts number after date

- ✅ **`image - YYYY-MM-DDTHHMMSS.mmm.jpg`** - Timestamp format
  - Returns `None` (no meaningful number to extract)
  - Examples: `image - 2025-07-20T112914.366.jpg`

### 2. Edge Cases (`TestImageNumberExtractionEdgeCases`)

- ✅ **Case Insensitivity** - Extension case variations
  - `.jpg`, `.jpeg`, `.JPG`, `.JPEG` all handled

- ✅ **Multiple Underscores** - Uses last underscore
  - `prefix_part1_part2_00155.jpeg` → extracts `155`

- ✅ **Leading Zeros** - Correctly converts to integer
  - `007821451_00155.jpeg` → `155` (not `00155`)

- ✅ **Single Digit Numbers** - Handles minimal numbers
  - `image1.jpg` → `1`, `prefix_5.jpeg` → `5`

- ✅ **Large Numbers** - Handles very large numbers
  - `image99999.jpg` → `99999`
  - `prefix_123456.jpeg` → `123456`

- ✅ **Invalid Patterns** - Returns None for non-matching files
  - `no-number.jpg` → `None`
  - `image.jpg` → `None`
  - `just-text.jpeg` → `None`

- ✅ **Unicode in Prefix** - Handles non-ASCII characters
  - `ф487оп1спр526_00155.jpeg` → `155`
  - `中文_prefix_00155.jpeg` → `155`

- ✅ **Special Characters** - Handles various special chars
  - `prefix@#$%_00155.jpeg` → `155`
  - `prefix!@#_00155.jpeg` → `155`

### 3. Real-World Examples (`TestImageNumberExtractionRegression`)

- ✅ **Issue Case: 007821451_00155.jpeg**
  - Verifies extraction of `155` (not `782145100155`)
  - Tests related files: `00156`, `00209`, `00215`

- ✅ **Leading Zeros in Prefix**
  - `007821451_00155.jpeg` → `155`
  - `000000123_00155.jpeg` → `155`

- ✅ **Large Prefix, Small Number**
  - `999999999_00155.jpeg` → `155`
  - `123456789_00001.jpeg` → `1`

### 4. Scanning Functionality (`TestScanAvailableImageNumbers`)

- ✅ **Scan Local Images** - Detects all numbers in directory
  - Scans multiple pattern types
  - Returns sorted list of numbers
  - Provides pattern description

- ✅ **Pattern Description** - Identifies filename pattern
  - Detects `PREFIX_XXXXX` pattern
  - Provides helpful description

- ✅ **Empty Directory** - Handles no images gracefully
  - Returns empty list
  - Provides appropriate message

- ✅ **No Numeric Patterns** - Handles non-numeric files
  - Returns empty list
  - Indicates no patterns found

- ✅ **Error Handling** - Graceful error handling
  - Returns empty list on errors
  - Provides error message

### 5. Consistency Tests (`TestImageNumberExtractionConsistency`)

- ✅ **Consistency with list_images** - Matches extraction logic
  - Verifies same results across codebase
  - Tests multiple pattern types

- ✅ **Return Type Validation** - All extractions return integers
  - Verifies type consistency
  - Tests all pattern types

---

## Key Improvements Tested

### 1. Enhanced Pattern Detection
- **Before:** Only detected `_` separator
- **After:** Detects `_`, `-`, `.` and other separators
- **Test Coverage:** ✅ All separator types tested

### 2. Last Separator Priority
- **Behavior:** Uses last separator found (most specific)
- **Example:** `prefix-part1_part2-00155.jpeg` → uses `-` (last)
- **Test Coverage:** ✅ Multiple separator scenarios

### 3. Improved Error Messages
- **Feature:** Shows available numbers when none found
- **Test Coverage:** ✅ Scanning function tests

### 4. Wizard Auto-Detection
- **Feature:** Detects minimum image number in wizard
- **Test Coverage:** ✅ Integration with LocalImageSource

---

## Test Statistics

### Pattern Types Covered
- Standard patterns: 7 types
- Improved patterns: 3 types (dash, dot, mixed)
- Special formats: 2 types (date, timestamp)
- **Total:** 12+ pattern types

### Edge Cases Covered
- Case variations: ✅
- Multiple separators: ✅
- Leading zeros: ✅
- Unicode characters: ✅
- Special characters: ✅
- Invalid inputs: ✅
- Empty/null cases: ✅

### Real-World Scenarios
- Issue case (007821451_00155): ✅
- Large prefix numbers: ✅
- Various naming conventions: ✅

---

## Regression Tests

### Specific Issue Fixed
**Problem:** Config had `image_start_number: 782145100155` but files were `007821451_00155.jpeg`
- **Root Cause:** User included prefix in image_start_number
- **Solution:** Improved extraction + auto-detection + better error messages
- **Test Coverage:** ✅ Specific regression test included

---

## Integration Points

### Functions Tested
1. `extract_image_number(filename)` - Core extraction function
2. `scan_available_image_numbers(image_source, config)` - Scanning function

### Integration with
- `LocalImageSource.list_images()` - Uses extract_image_number
- `DriveImageSource.list_images()` - Uses extract_image_number
- `ProcessingSettingsStep._detect_min_image_number()` - Uses extract_image_number
- Error handling in `main()` - Uses scan_available_image_numbers

---

## Running the Tests

```bash
# Run all image number extraction tests
pytest tests/unit/test_image_number_extraction.py -v

# Run specific test class
pytest tests/unit/test_image_number_extraction.py::TestExtractImageNumber -v

# Run with coverage
pytest tests/unit/test_image_number_extraction.py --cov=transcribe --cov-report=term-missing
```

---

## Summary of Scenarios Covered in This Chat

### 1. Root Cause Analysis
- ✅ Identified issue: Config had `782145100155` but files were `007821451_00155.jpeg`
- ✅ Found that extraction was working but user set wrong number
- ✅ Determined need for better pattern detection and user guidance

### 2. Pattern Detection Improvements
- ✅ Enhanced `extract_image_number()` to detect numbers before `-`, `.`, and other separators
- ✅ Improved logic to use last separator found
- ✅ Updated all extraction points to use improved function

### 3. Error Message Improvements
- ✅ Added `scan_available_image_numbers()` function
- ✅ Enhanced error messages to show available numbers
- ✅ Provides suggested `image_start_number` value

### 4. Wizard Enhancements
- ✅ Added `_detect_min_image_number()` to ProcessingSettingsStep
- ✅ Auto-detects minimum image number from files
- ✅ Sets as default with ability to override

### 5. Comprehensive Testing
- ✅ Created unit tests covering all pattern types
- ✅ Tests edge cases and boundary conditions
- ✅ Includes regression tests for specific issue
- ✅ Tests consistency across codebase

---

## Test Coverage Metrics

- **Pattern Types:** 12+ different filename patterns
- **Edge Cases:** 10+ boundary conditions
- **Real-World Examples:** 5+ actual use cases
- **Integration Points:** 4+ code integration points
- **Total Test Methods:** 40+ individual test cases

---

**Last Updated:** January 2026
**Related Issue:** Image number extraction for files like `007821451_00155.jpeg`
**Status:** ✅ Comprehensive test coverage implemented
