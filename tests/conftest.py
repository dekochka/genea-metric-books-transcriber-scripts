"""
Pytest configuration and shared fixtures for transcription tool tests.
"""
import os
import sys
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test data directory
TEST_IMAGE_DIR = os.path.join(project_root, 'data_samples', 'test_input_sample')

@pytest.fixture
def test_image_dir():
    """Fixture providing path to test image directory."""
    return TEST_IMAGE_DIR

@pytest.fixture
def test_images():
    """Fixture providing list of test image filenames."""
    return [
        'cover-title-page.jpg',
        'image00001.jpg',
        'image00002.jpg',
        'image00003.jpg'
    ]
