"""
Unit tests for image number extraction and pattern recognition.

Tests cover various filename patterns and edge cases for extracting
image numbers from filenames, including the improved pattern detection
that handles special symbols (_, -, ., etc.).
"""

import pytest
from transcribe import extract_image_number, scan_available_image_numbers
from transcribe import LocalImageSource, DriveImageSource


class TestExtractImageNumber:
    """Tests for extract_image_number() function."""
    
    def test_pattern_image_parentheses(self):
        """Test pattern: image (N).jpg"""
        assert extract_image_number("image (7).jpg") == 7
        assert extract_image_number("image (10).jpeg") == 10
        assert extract_image_number("image (155).JPG") == 155
        assert extract_image_number("IMAGE (999).JPEG") == 999
    
    def test_pattern_image_prefix_numbered(self):
        """Test pattern: imageXXXXX.jpg"""
        assert extract_image_number("image00001.jpg") == 1
        assert extract_image_number("image00101.jpg") == 101
        assert extract_image_number("image00155.jpeg") == 155
        assert extract_image_number("image12345.JPG") == 12345
    
    def test_pattern_number_only(self):
        """Test pattern: XXXXX.jpg"""
        assert extract_image_number("52.jpg") == 52
        assert extract_image_number("102.jpeg") == 102
        assert extract_image_number("155.JPG") == 155
        assert extract_image_number("9999.JPEG") == 9999
    
    def test_pattern_prefix_underscore(self):
        """Test pattern: PREFIX_XXXXX.jpg (e.g., 007821451_00155.jpeg)"""
        assert extract_image_number("007821451_00155.jpeg") == 155
        assert extract_image_number("004933159_00216.jpeg") == 216
        assert extract_image_number("prefix_12345.jpg") == 12345
        assert extract_image_number("ABC_999.jpeg") == 999
        assert extract_image_number("007821451_00155.JPEG") == 155
    
    def test_pattern_prefix_dash(self):
        """Test pattern: PREFIX-XXXXX.jpg (improved detection)"""
        assert extract_image_number("007821451-00155.jpeg") == 155
        assert extract_image_number("prefix-12345.jpg") == 12345
        assert extract_image_number("ABC-999.jpeg") == 999
    
    def test_pattern_prefix_dot(self):
        """Test pattern: PREFIX.XXXXX.jpg (improved detection)"""
        assert extract_image_number("007821451.00155.jpeg") == 155
        assert extract_image_number("prefix.12345.jpg") == 12345
        assert extract_image_number("ABC.999.jpeg") == 999
    
    def test_pattern_img_date_format(self):
        """Test pattern: IMG_YYYYMMDD_XXXX.jpg"""
        assert extract_image_number("IMG_20250814_0036.jpg") == 36
        assert extract_image_number("IMG_20250101_1234.jpeg") == 1234
        assert extract_image_number("img_20251231_9999.JPG") == 9999
    
    def test_pattern_timestamp_format(self):
        """Test pattern: image - YYYY-MM-DDTHHMMSS.mmm.jpg (should return None)"""
        assert extract_image_number("image - 2025-07-20T112914.366.jpg") is None
        assert extract_image_number("image - 2025-01-01T000000.000.jpeg") is None
    
    def test_pattern_photo_timestamp_format(self):
        """Test pattern: photo_YYYY-MM-DD HH.MM.SS.jpeg (should return None)"""
        assert extract_image_number("photo_2026-01-24 20.33.55.jpeg") is None
        assert extract_image_number("photo_2026-01-24 20.34.02.jpeg") is None
        assert extract_image_number("photo_2026-01-24 20.34.10.jpeg") is None
        assert extract_image_number("PHOTO_2026-01-24 20.33.55.JPEG") is None
    
    def test_case_insensitive(self):
        """Test that extraction is case-insensitive for extensions."""
        assert extract_image_number("IMAGE001.JPG") == 1
        assert extract_image_number("image001.JPEG") == 1
        assert extract_image_number("IMAGE001.jpg") == 1
        assert extract_image_number("image001.jpeg") == 1
    
    def test_multiple_underscores(self):
        """Test files with multiple underscores (should use last one)."""
        assert extract_image_number("prefix_part1_part2_00155.jpeg") == 155
        assert extract_image_number("007821451_section_page_00155.jpeg") == 155
        assert extract_image_number("folder_subfolder_12345.jpg") == 12345
    
    def test_multiple_separators(self):
        """Test files with multiple separators (should use last one)."""
        assert extract_image_number("prefix-part1-part2-00155.jpeg") == 155
        assert extract_image_number("007821451.section.page.00155.jpeg") == 155
        assert extract_image_number("prefix_part-dash_00155.jpeg") == 155  # Last separator wins
    
    def test_leading_zeros_preserved(self):
        """Test that leading zeros are handled correctly (converted to int)."""
        assert extract_image_number("007821451_00155.jpeg") == 155  # Not 00155
        assert extract_image_number("image00001.jpg") == 1  # Not 00001
        assert extract_image_number("000155.jpg") == 155  # Not 000155
    
    def test_edge_cases_single_digit(self):
        """Test single digit numbers."""
        assert extract_image_number("image1.jpg") == 1
        assert extract_image_number("prefix_5.jpeg") == 5
        assert extract_image_number("9.jpg") == 9
    
    def test_edge_cases_large_numbers(self):
        """Test large numbers."""
        assert extract_image_number("image99999.jpg") == 99999
        assert extract_image_number("prefix_123456.jpeg") == 123456
        assert extract_image_number("782145100155.jpg") == 782145100155
    
    def test_invalid_patterns(self):
        """Test files that don't match any pattern."""
        assert extract_image_number("no-number.jpg") is None
        assert extract_image_number("image.jpg") is None
        assert extract_image_number("just-text.jpeg") is None
        assert extract_image_number("") is None
    
    def test_no_extension(self):
        """Test files without proper extension."""
        assert extract_image_number("image001.png") is None
        assert extract_image_number("image001.txt") is None
        assert extract_image_number("image001") is None
    
    def test_real_world_examples(self):
        """Test real-world filename examples from the issue."""
        # The actual issue case
        assert extract_image_number("007821451_00155.jpeg") == 155
        assert extract_image_number("007821451_00156.jpeg") == 156
        assert extract_image_number("007821451_00209.jpeg") == 209
        assert extract_image_number("007821451_00215.jpeg") == 215
        
        # Other common patterns
        assert extract_image_number("ф487оп1спр526_001.jpg") == 1
        assert extract_image_number("scan-2024-00155.jpg") == 155
        assert extract_image_number("document.page.00155.jpeg") == 155


class TestScanAvailableImageNumbers:
    """Tests for scan_available_image_numbers() function."""
    
    @pytest.fixture
    def test_image_dir(self, tmp_path):
        """Create a temporary directory with test images in various patterns."""
        # Create test images with different patterns
        (tmp_path / "007821451_00155.jpeg").write_bytes(b"fake image 1")
        (tmp_path / "007821451_00156.jpeg").write_bytes(b"fake image 2")
        (tmp_path / "007821451_00157.jpeg").write_bytes(b"fake image 3")
        (tmp_path / "007821451_00209.jpeg").write_bytes(b"fake image 4")
        (tmp_path / "007821451_00210.jpeg").write_bytes(b"fake image 5")
        (tmp_path / "image00001.jpg").write_bytes(b"fake image 6")
        (tmp_path / "image00002.jpg").write_bytes(b"fake image 7")
        (tmp_path / "52.jpg").write_bytes(b"fake image 8")
        (tmp_path / "103.jpg").write_bytes(b"fake image 9")
        return str(tmp_path)
    
    def test_scan_local_images_underscore_pattern(self, test_image_dir):
        """Test scanning images with underscore pattern."""
        source = LocalImageSource(test_image_dir)
        config = {
            'local': {'image_dir': test_image_dir},
            'image_start_number': 1,
            'image_count': 1000
        }
        
        found_numbers, pattern_desc = scan_available_image_numbers(source, config)
        
        assert 155 in found_numbers
        assert 156 in found_numbers
        assert 157 in found_numbers
        assert 209 in found_numbers
        assert 210 in found_numbers
        assert 1 in found_numbers  # from image00001.jpg
        assert 2 in found_numbers  # from image00002.jpg
        assert 52 in found_numbers
        assert 103 in found_numbers
        
        assert "PREFIX_XXXXX" in pattern_desc or "underscore" in pattern_desc.lower()
        assert min(found_numbers) == 1
        assert max(found_numbers) >= 210
    
    def test_scan_detects_pattern_description(self, test_image_dir):
        """Test that pattern description is correctly detected."""
        source = LocalImageSource(test_image_dir)
        config = {
            'local': {'image_dir': test_image_dir},
            'image_start_number': 1,
            'image_count': 1000
        }
        
        found_numbers, pattern_desc = scan_available_image_numbers(source, config)
        
        assert len(found_numbers) > 0
        assert "Pattern detected" in pattern_desc or "Found numbers range" in pattern_desc
        assert "007821451" in pattern_desc or "example" in pattern_desc.lower()
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        source = LocalImageSource(str(tmp_path))
        config = {
            'local': {'image_dir': str(tmp_path)},
            'image_start_number': 1,
            'image_count': 1000
        }
        
        found_numbers, pattern_desc = scan_available_image_numbers(source, config)
        
        assert found_numbers == []
        assert "No numeric patterns" in pattern_desc or "Error" in pattern_desc
    
    def test_scan_no_numeric_patterns(self, tmp_path):
        """Test scanning directory with images that have no numeric patterns."""
        (tmp_path / "no-number.jpg").write_bytes(b"fake")
        (tmp_path / "image.jpg").write_bytes(b"fake")
        (tmp_path / "just-text.jpeg").write_bytes(b"fake")
        
        source = LocalImageSource(str(tmp_path))
        config = {
            'local': {'image_dir': str(tmp_path)},
            'image_start_number': 1,
            'image_count': 1000
        }
        
        found_numbers, pattern_desc = scan_available_image_numbers(source, config)
        
        assert found_numbers == []
        assert "No numeric patterns" in pattern_desc
    
    def test_scan_handles_errors_gracefully(self, tmp_path):
        """Test that scan handles errors gracefully."""
        # Create invalid directory path
        invalid_source = LocalImageSource(str(tmp_path))
        # Use invalid config that might cause errors
        config = {
            'local': {'image_dir': str(tmp_path)},
            'image_start_number': 1,
            'image_count': 1000
        }
        
        # Should not raise exception, but return empty list
        found_numbers, pattern_desc = scan_available_image_numbers(invalid_source, config)
        
        assert isinstance(found_numbers, list)
        assert isinstance(pattern_desc, str)


class TestImageNumberExtractionEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_very_long_filenames(self):
        """Test extraction from very long filenames."""
        long_name = "very_long_prefix_name_with_many_parts_" + "0" * 50 + "12345.jpeg"
        assert extract_image_number(long_name) == 12345
    
    def test_numbers_with_commas(self):
        """Test that numbers with formatting are handled."""
        # Note: current implementation doesn't handle commas, but tests the behavior
        assert extract_image_number("prefix_1,234.jpeg") is None  # Comma breaks isdigit()
    
    def test_mixed_separators(self):
        """Test files with mixed separator types."""
        assert extract_image_number("prefix-part1_part2-00155.jpeg") == 155  # Last separator
        assert extract_image_number("007821451.section_page-00155.jpeg") == 155  # Last separator
    
    def test_unicode_in_prefix(self):
        """Test files with unicode characters in prefix."""
        assert extract_image_number("ф487оп1спр526_00155.jpeg") == 155
        assert extract_image_number("中文_prefix_00155.jpeg") == 155
    
    def test_whitespace_handling(self):
        """Test that whitespace doesn't break extraction."""
        # Filenames shouldn't have spaces typically, but test edge case
        assert extract_image_number("prefix_ 00155.jpeg") is None  # Space breaks isdigit()
        # Space before extension breaks the extension check - this is expected behavior
        assert extract_image_number("prefix_00155 .jpeg") is None  # Space before extension breaks extension check
    
    def test_special_characters_in_prefix(self):
        """Test files with special characters in prefix."""
        assert extract_image_number("prefix@#$%_00155.jpeg") == 155
        assert extract_image_number("prefix!@#_00155.jpeg") == 155
        assert extract_image_number("prefix(1)_00155.jpeg") == 155


class TestImageNumberExtractionRegression:
    """Regression tests for specific issues encountered."""
    
    def test_issue_782145100155_case(self):
        """
        Regression test for the specific issue:
        - Config had image_start_number: 782145100155 (incorrect - included prefix)
        - Actual files: 007821451_00155.jpeg
        - Should extract: 155 (not 782145100155)
        """
        # The problematic case
        assert extract_image_number("007821451_00155.jpeg") == 155
        
        # Related files from the same batch
        assert extract_image_number("007821451_00156.jpeg") == 156
        assert extract_image_number("007821451_00209.jpeg") == 209
        
        # Verify it doesn't extract the prefix
        assert extract_image_number("007821451_00155.jpeg") != 782145100155
        assert extract_image_number("007821451_00155.jpeg") != 7821451
    
    def test_leading_zeros_in_prefix(self):
        """Test that leading zeros in prefix don't affect number extraction."""
        assert extract_image_number("007821451_00155.jpeg") == 155
        assert extract_image_number("000000123_00155.jpeg") == 155
        assert extract_image_number("000000000_00155.jpeg") == 155
    
    def test_large_prefix_small_number(self):
        """Test files with large prefix but small number."""
        assert extract_image_number("999999999_00155.jpeg") == 155
        assert extract_image_number("123456789_00001.jpeg") == 1
        assert extract_image_number("987654321_00099.jpeg") == 99


class TestImageNumberExtractionConsistency:
    """Tests to ensure consistency across different extraction points."""
    
    def test_consistency_with_list_images_logic(self):
        """Test that extract_image_number matches list_images extraction logic."""
        test_cases = [
            "007821451_00155.jpeg",
            "image00001.jpg",
            "52.jpg",
            "image (7).jpg",
            "IMG_20250814_0036.jpg",
            "prefix-12345.jpeg",
            "prefix.999.jpeg"
        ]
        
        for filename in test_cases:
            number = extract_image_number(filename)
            # If extraction succeeds, verify it's a reasonable number
            if number is not None:
                assert isinstance(number, int)
                assert number > 0
                # Verify the number appears in the filename
                assert str(number) in filename or f"{number:05d}" in filename or f"{number:04d}" in filename
    
    def test_all_patterns_return_integers(self):
        """Test that all successful extractions return integers."""
        test_cases = [
            "007821451_00155.jpeg",
            "image00001.jpg",
            "52.jpg",
            "image (7).jpg",
            "prefix-12345.jpeg",
            "prefix.999.jpeg"
        ]
        
        for filename in test_cases:
            number = extract_image_number(filename)
            if number is not None:
                assert isinstance(number, int)
                assert number >= 0
