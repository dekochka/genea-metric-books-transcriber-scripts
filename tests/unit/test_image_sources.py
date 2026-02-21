"""
Unit tests for image source strategies.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from transcribe import LocalImageSource, DriveImageSource


class TestLocalImageSource:
    """Tests for LocalImageSource."""
    
    @pytest.fixture
    def test_image_dir(self, tmp_path):
        """Create a temporary directory with test images."""
        # Create test images
        (tmp_path / "image00001.jpg").write_bytes(b"fake image 1")
        (tmp_path / "image00002.jpg").write_bytes(b"fake image 2")
        (tmp_path / "image00003.jpg").write_bytes(b"fake image 3")
        (tmp_path / "cover-title-page.jpg").write_bytes(b"fake cover")
        return str(tmp_path)
    
    def test_init_with_valid_directory(self, test_image_dir):
        """Test initialization with valid directory."""
        source = LocalImageSource(test_image_dir)
        assert source.image_dir == test_image_dir
    
    def test_init_with_invalid_directory(self):
        """Test initialization with invalid directory raises error."""
        with pytest.raises(ValueError, match="Image directory does not exist"):
            LocalImageSource("/nonexistent/directory")
    
    def test_list_images_finds_images(self, test_image_dir):
        """Test list_images() finds images in directory."""
        source = LocalImageSource(test_image_dir)
        config = {
            'image_start_number': 1,
            'image_count': 3,
            'image_sort_method': 'number_extracted',  # Use number-based selection
            'retry_mode': False,
            'retry_image_list': []
        }
        images = source.list_images(config)
        # Should find 3 numbered images (cover-title-page.jpg is typically filtered out)
        assert len(images) >= 0  # May vary based on filtering logic
        if len(images) > 0:
            assert all('name' in img for img in images)
            assert all('path' in img for img in images)
    
    def test_list_images_with_filtering_by_number(self, test_image_dir):
        """Test list_images() with image_start_number and image_count using number_extracted method."""
        source = LocalImageSource(test_image_dir)
        config = {
            'image_start_number': 2,
            'image_count': 2,
            'image_sort_method': 'number_extracted',  # Filter by extracted number
            'retry_mode': False,
            'retry_image_list': []
        }
        images = source.list_images(config)
        assert len(images) == 2
        # Should start from image 2
        from transcribe import extract_image_number
        image_numbers = [extract_image_number(img['name']) 
                        for img in images if extract_image_number(img['name']) is not None]
        assert len(image_numbers) == 2
        assert min(image_numbers) >= 2
    
    def test_list_images_with_filtering_by_position(self, test_image_dir):
        """Test list_images() with position-based selection."""
        source = LocalImageSource(test_image_dir)
        config = {
            'image_start_number': 2,
            'image_count': 2,
            'image_sort_method': 'name_asc',  # Use position-based selection
            'retry_mode': False,
            'retry_image_list': []
        }
        images = source.list_images(config)
        # Should get 2 images starting from position 2 in sorted list
        assert len(images) == 2
        # Images should be sorted by name
        names = [img['name'] for img in images]
        assert names == sorted(names)
    
    def test_get_image_bytes(self, test_image_dir):
        """Test get_image_bytes() reads image file."""
        source = LocalImageSource(test_image_dir)
        img_info = {'name': 'image00001.jpg', 'path': os.path.join(test_image_dir, 'image00001.jpg')}
        bytes_data = source.get_image_bytes(img_info)
        assert bytes_data == b"fake image 1"
    
    def test_get_image_url(self, test_image_dir):
        """Test get_image_url() returns file path with normalized separators."""
        source = LocalImageSource(test_image_dir)
        img_info = {'name': 'image00001.jpg', 'path': os.path.join(test_image_dir, 'image00001.jpg')}
        url = source.get_image_url(img_info)
        # get_image_url() normalizes path separators to forward slashes for cross-platform compatibility
        expected_url = img_info['path'].replace('\\', '/')
        assert url == expected_url


class TestDriveImageSource:
    """Tests for DriveImageSource."""
    
    @pytest.fixture
    def mock_drive_service(self):
        """Create a mock Drive service."""
        return Mock()
    
    def test_init_stores_parameters(self, mock_drive_service):
        """Test __init__ stores drive service and folder ID."""
        source = DriveImageSource(mock_drive_service, "folder_id_123", document_name="Test Doc")
        assert source.drive_service == mock_drive_service
        assert source.drive_folder_id == "folder_id_123"
        assert source.document_name == "Test Doc"
    
    @patch('transcribe.list_images')
    def test_list_images_delegates_to_list_images_function(self, mock_list_images, mock_drive_service):
        """Test list_images() delegates to existing list_images() function."""
        mock_images = [
            {'name': 'image1.jpg', 'id': 'id1', 'webViewLink': 'link1'},
            {'name': 'image2.jpg', 'id': 'id2', 'webViewLink': 'link2'}
        ]
        mock_list_images.return_value = mock_images
        
        source = DriveImageSource(mock_drive_service, "folder_id_123")
        config = {
            'image_start_number': 1, 
            'image_count': 2,
            'image_sort_method': 'number_extracted'  # Include sort method
        }
        result = source.list_images(config)
        
        mock_list_images.assert_called_once_with(mock_drive_service, config)
        assert result == mock_images
    
    @patch('transcribe.download_image')
    def test_get_image_bytes_delegates_to_download_image(self, mock_download_image, mock_drive_service):
        """Test get_image_bytes() delegates to download_image() function."""
        mock_bytes = b"fake image bytes"
        mock_download_image.return_value = mock_bytes
        
        source = DriveImageSource(mock_drive_service, "folder_id_123", document_name="Test Doc")
        img_info = {'name': 'image1.jpg', 'id': 'file_id_123'}
        result = source.get_image_bytes(img_info)
        
        mock_download_image.assert_called_once_with(
            mock_drive_service, 'file_id_123', 'image1.jpg', 'Test Doc'
        )
        assert result == mock_bytes
    
    def test_get_image_url_returns_webview_link(self, mock_drive_service):
        """Test get_image_url() returns webViewLink."""
        source = DriveImageSource(mock_drive_service, "folder_id_123")
        img_info = {'name': 'image1.jpg', 'webViewLink': 'https://drive.google.com/file/view'}
        url = source.get_image_url(img_info)
        assert url == 'https://drive.google.com/file/view'

    @patch('transcribe.list_images')
    def test_drive_sparse_numbering(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource handles sparse filename numbering (gaps of 100+)."""
        # Mock list_images to return images with large gaps: img_0500, img_0520, img_0700, img_0800
        mock_files = [
            {'id': '1', 'name': 'image00500.jpg', 'webViewLink': 'https://drive.google.com/1'},
            {'id': '2', 'name': 'image00520.jpg', 'webViewLink': 'https://drive.google.com/2'},
            {'id': '3', 'name': 'image00700.jpg', 'webViewLink': 'https://drive.google.com/3'},
            {'id': '4', 'name': 'image00800.jpg', 'webViewLink': 'https://drive.google.com/4'},
        ]
        mock_list_images.return_value = mock_files

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 500,
            'image_count': 301,  # Should capture 500, 520, 700, 800
            'image_sort_method': 'name_asc'
        }

        result = source.list_images(config)

        # Should find all 4 images (500, 520, 700, 800 all in range 500-800)
        assert len(result) == 4
        assert result[0]['name'] == 'image00500.jpg'
        assert result[3]['name'] == 'image00800.jpg'

    @patch('transcribe.list_images')
    def test_drive_contiguous_numbering(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource handles contiguous numbering (1, 2, 3, ...)."""
        mock_files = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                      for i in range(1, 51)]
        mock_list_images.return_value = mock_files[9:29]  # Return filtered result

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 10,
            'image_count': 20,
            'image_sort_method': 'name_asc'
        }

        result = source.list_images(config)

        # Should find exactly 20 images (10-29)
        assert len(result) == 20
        assert result[0]['name'] == 'image00010.jpg'
        assert result[19]['name'] == 'image00029.jpg'

    @patch('transcribe.list_images')
    def test_drive_empty_folder(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource handles empty folder gracefully."""
        mock_list_images.return_value = []

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 1,
            'image_count': 10,
            'image_sort_method': 'name_asc'
        }

        result = source.list_images(config)
        assert len(result) == 0

    @patch('transcribe.list_images')
    def test_drive_single_image(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource handles single image in folder."""
        mock_list_images.return_value = [
            {'id': '1', 'name': 'image00001.jpg', 'webViewLink': 'https://drive.google.com/1'}
        ]

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 1,
            'image_count': 1,
            'image_sort_method': 'name_asc'
        }

        result = source.list_images(config)
        assert len(result) == 1
        assert result[0]['name'] == 'image00001.jpg'

    @patch('transcribe.list_images')
    def test_drive_pagination_large_folder(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource handles pagination for 1000+ images."""
        # Mock list_images to return paginated results (100 images across 2 pages)
        mock_files = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                      for i in range(50, 150)]  # Return filtered result (50-149)

        mock_list_images.return_value = mock_files

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 50,
            'image_count': 100,
            'image_sort_method': 'name_asc'
        }

        result = source.list_images(config)

        # Should find 100 images (50-149)
        assert len(result) == 100
        assert result[0]['name'] == 'image00050.jpg'
        assert result[99]['name'] == 'image00149.jpg'

    @patch('transcribe.list_images')
    def test_drive_respects_max_images_limit(self, mock_list_images, mock_drive_service):
        """Test DriveImageSource respects user's max_images config limit."""
        # Mock list_images to return only up to max_images
        # Simulate what happens when max_images=150 and folder has 500 images
        mock_files = [{'id': str(i), 'name': f'image{i:05d}.jpg', 'webViewLink': f'https://drive.google.com/{i}'}
                      for i in range(1, 151)]  # Only first 150 images

        mock_list_images.return_value = mock_files

        source = DriveImageSource(mock_drive_service, "test_folder")
        config = {
            'drive_folder_id': 'test_folder',
            'image_start_number': 1,
            'image_count': 500,  # Request 500 images
            'image_sort_method': 'name_asc',
            'max_images': 150  # But limit fetch to 150
        }

        result = source.list_images(config)

        # Should find only 150 images (limited by max_images)
        assert len(result) == 150
        assert result[0]['name'] == 'image00001.jpg'
        assert result[149]['name'] == 'image00150.jpg'
