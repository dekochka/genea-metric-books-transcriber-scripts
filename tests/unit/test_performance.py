"""
Performance tests for comparing mode performance.
"""
import time
import pytest
from unittest.mock import Mock, patch
from transcribe import LocalImageSource, DriveImageSource, ModeFactory


class TestPerformanceComparison:
    """Performance comparison tests between modes."""
    
    @pytest.fixture
    def test_image_dir(self, tmp_path):
        """Create a temporary directory with test images."""
        # Create multiple test images (starting from 1, not 0, to match typical naming)
        for i in range(1, 11):  # image00001.jpg to image00010.jpg
            (tmp_path / f"image{i:05d}.jpg").write_bytes(b"fake image data")
        return str(tmp_path)
    
    def test_local_image_listing_performance(self, test_image_dir):
        """Test performance of local image listing."""
        source = LocalImageSource(test_image_dir)
        config = {
            'image_start_number': 1,
            'image_count': 10,
            'retry_mode': False,
            'retry_image_list': []
        }
        
        start_time = time.time()
        images = source.list_images(config)
        elapsed_time = time.time() - start_time
        
        # Should find images (may vary based on filtering, but should be > 0)
        assert len(images) > 0
        # Local file system should be fast (< 1 second for 10 images)
        assert elapsed_time < 1.0
    
    @patch('transcribe.list_images')
    def test_drive_image_listing_performance(self, mock_list_images):
        """Test performance of Drive image listing (mocked)."""
        mock_drive_service = Mock()
        mock_list_images.return_value = [
            {'name': f'image{i:05d}.jpg', 'id': f'id{i}', 'webViewLink': f'link{i}'}
            for i in range(10)
        ]
        
        source = DriveImageSource(mock_drive_service, "folder123")
        config = {'image_start_number': 1, 'image_count': 10}
        
        start_time = time.time()
        images = source.list_images(config)
        elapsed_time = time.time() - start_time
        
        assert len(images) == 10
        # Mocked call should be very fast
        assert elapsed_time < 0.1
    
    def test_local_image_bytes_reading_performance(self, test_image_dir):
        """Test performance of reading image bytes locally."""
        source = LocalImageSource(test_image_dir)
        img_info = {
            'name': 'image00001.jpg',
            'path': f"{test_image_dir}/image00001.jpg"
        }
        
        start_time = time.time()
        bytes_data = source.get_image_bytes(img_info)
        elapsed_time = time.time() - start_time
        
        assert bytes_data == b"fake image data"
        # Reading from local file system should be very fast
        assert elapsed_time < 0.1
    
    @patch('transcribe.download_image')
    def test_drive_image_bytes_download_performance(self, mock_download_image):
        """Test performance of downloading image bytes from Drive (mocked)."""
        mock_drive_service = Mock()
        mock_download_image.return_value = b"fake image data"
        
        source = DriveImageSource(mock_drive_service, "folder123", document_name="Test")
        img_info = {'name': 'image1.jpg', 'id': 'file_id_123'}
        
        start_time = time.time()
        bytes_data = source.get_image_bytes(img_info)
        elapsed_time = time.time() - start_time
        
        assert bytes_data == b"fake image data"
        # Mocked download should be fast, but real downloads would be slower
        assert elapsed_time < 0.1
    
    @patch('transcribe.LocalAuthStrategy')
    @patch('transcribe.LocalImageSource')
    @patch('transcribe.GeminiDevClient')
    @patch('transcribe.LogFileOutput')
    @patch('transcribe.logging.getLogger')
    def test_mode_factory_creation_performance(self, mock_logger, mock_output, mock_ai_client, mock_image_source, mock_auth):
        """Test performance of ModeFactory handler creation."""
        config = {
            'local': {
                'api_key': 'test-key',
                'image_dir': '/test/images',
                'output_dir': '/test/output',
                'ocr_model_id': 'gemini-1.5-pro'
            }
        }
        
        mock_auth_instance = Mock()
        mock_auth_instance.authenticate.return_value = 'test-key'
        mock_auth.return_value = mock_auth_instance
        
        start_time = time.time()
        handlers = ModeFactory.create_handlers('local', config)
        elapsed_time = time.time() - start_time
        
        assert handlers is not None
        # Factory creation should be fast (< 0.1 seconds)
        assert elapsed_time < 0.1
    
    def test_config_normalization_performance(self):
        """Test performance of config normalization."""
        legacy_config = {
            'project_id': 'test-project',
            'drive_folder_id': 'folder123',
            'adc_file': 'adc.json',
            'ocr_model_id': 'gemini-1.5-pro',
            'prompt_file': 'prompt.txt',
            'archive_index': 'test123',
            'image_start_number': 1,
            'image_count': 10
        }
        
        from transcribe import detect_mode, normalize_config
        
        start_time = time.time()
        mode = detect_mode(legacy_config)
        normalized = normalize_config(legacy_config, mode)
        elapsed_time = time.time() - start_time
        
        assert mode == 'googlecloud'
        assert 'googlecloud' in normalized
        # Normalization should be very fast
        assert elapsed_time < 0.01
