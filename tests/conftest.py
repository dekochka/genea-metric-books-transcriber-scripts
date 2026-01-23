"""
Pytest configuration and shared fixtures for transcription tool tests.
"""
import os
import sys
import pytest
import gc

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Memory-efficient fixture: use tmp_path instead of real directory
# This avoids scanning large real directories that could cause memory issues

@pytest.fixture
def test_image_dir(tmp_path):
    """Fixture providing temporary directory with minimal test images."""
    # Create only a few small test images to minimize memory usage
    for i in range(1, 4):  # Only 3 small test images
        (tmp_path / f"image{i:05d}.jpg").write_bytes(b"fake image data")
    return str(tmp_path)

@pytest.fixture
def test_images():
    """Fixture providing list of test image filenames."""
    return [
        'cover-title-page.jpg',
        'image00001.jpg',
        'image00002.jpg',
        'image00003.jpg'
    ]

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Auto-cleanup fixture to help with memory management."""
    yield
    # Force garbage collection after each test
    gc.collect()
