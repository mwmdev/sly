"""Unit tests for sly.image_utils module."""

import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from PIL import Image

from sly.image_utils import get_image_files, rotate_image, resize_and_crop


class TestGetImageFiles:
    """Test cases for get_image_files function."""

    def test_get_image_files_name_order(self):
        """Test getting image files ordered by name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image files
            image_files = ["c.jpg", "a.png", "b.gif"]
            for filename in image_files:
                Path(temp_dir, filename).touch()

            result = get_image_files(temp_dir, "name")
            result_names = [f.name for f in result]

            assert result_names == ["a.png", "b.gif", "c.jpg"]

    def test_get_image_files_date_order(self):
        """Test getting image files ordered by date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image files with different timestamps
            files = []
            for i, filename in enumerate(["old.jpg", "new.png"]):
                filepath = Path(temp_dir, filename)
                filepath.touch()
                # Modify the timestamp
                os.utime(filepath, (1000 + i, 1000 + i))
                files.append(filepath)

            result = get_image_files(temp_dir, "date")
            result_names = [f.name for f in result]

            assert result_names == ["old.jpg", "new.png"]

    def test_get_image_files_random_order(self):
        """Test getting image files in random order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image files
            image_files = ["a.jpg", "b.png", "c.gif"]
            for filename in image_files:
                Path(temp_dir, filename).touch()

            with patch("random.shuffle") as mock_shuffle:
                result = get_image_files(temp_dir, "random")
                mock_shuffle.assert_called_once()

    def test_get_image_files_empty_directory(self):
        """Test that FileNotFoundError is raised for directory with no images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-image file
            Path(temp_dir, "not_an_image.txt").touch()

            with pytest.raises(FileNotFoundError, match="No image files found"):
                get_image_files(temp_dir, "name")

    def test_get_image_files_various_extensions(self):
        """Test that all supported image extensions are recognized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with various image extensions
            extensions = [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".tiff",
                ".tif",
                ".webp",
            ]
            for i, ext in enumerate(extensions):
                Path(temp_dir, f"image{i}{ext}").touch()

            result = get_image_files(temp_dir, "name")
            assert len(result) == len(extensions)


class TestRotateImage:
    """Test cases for rotate_image function."""

    def test_rotate_image_no_exif(self):
        """Test that image without EXIF data is returned unchanged."""
        # Create a simple test image
        image = Image.new("RGB", (100, 50), color="red")

        result = rotate_image(image)

        assert result.size == (100, 50)

    def test_rotate_image_orientation_3(self):
        """Test image rotation for orientation 3 (180 degrees)."""
        image = Image.new("RGB", (100, 50), color="red")

        # Mock EXIF data with orientation 3
        mock_exif = {0x0112: 3}  # Orientation tag

        with patch.object(image, "getexif", return_value=mock_exif):
            with patch.object(image, "rotate") as mock_rotate:
                mock_rotate.return_value = image

                rotate_image(image)
                mock_rotate.assert_called_once_with(180, expand=True)

    def test_rotate_image_orientation_6(self):
        """Test image rotation for orientation 6 (270 degrees)."""
        image = Image.new("RGB", (100, 50), color="red")

        # Mock EXIF data with orientation 6
        mock_exif = {0x0112: 6}

        with patch.object(image, "getexif", return_value=mock_exif):
            with patch.object(image, "rotate") as mock_rotate:
                mock_rotate.return_value = image

                rotate_image(image)
                mock_rotate.assert_called_once_with(270, expand=True)

    def test_rotate_image_orientation_8(self):
        """Test image rotation for orientation 8 (90 degrees)."""
        image = Image.new("RGB", (100, 50), color="red")

        # Mock EXIF data with orientation 8
        mock_exif = {0x0112: 8}

        with patch.object(image, "getexif", return_value=mock_exif):
            with patch.object(image, "rotate") as mock_rotate:
                mock_rotate.return_value = image

                rotate_image(image)
                mock_rotate.assert_called_once_with(90, expand=True)


class TestResizeAndCrop:
    """Test cases for resize_and_crop function."""

    def test_resize_and_crop_wider_target(self):
        """Test resizing when target aspect ratio is wider than image."""
        # Create a square image (1:1 ratio)
        image = Image.new("RGB", (100, 100), color="red")

        # Target is wider (2:1 ratio)
        result = resize_and_crop(image, 200, 100)

        assert result.size == (200, 100)

    def test_resize_and_crop_taller_target(self):
        """Test resizing when target aspect ratio is taller than image."""
        # Create a wide image (2:1 ratio)
        image = Image.new("RGB", (200, 100), color="red")

        # Target is square (1:1 ratio)
        result = resize_and_crop(image, 100, 100)

        assert result.size == (100, 100)

    def test_resize_and_crop_same_ratio(self):
        """Test resizing when image and target have same aspect ratio."""
        # Create a square image
        image = Image.new("RGB", (50, 50), color="red")

        # Target is also square but larger
        result = resize_and_crop(image, 100, 100)

        assert result.size == (100, 100)

    def test_resize_and_crop_maintains_aspect_ratio(self):
        """Test that the function properly maintains aspect ratio through cropping."""
        # Create a rectangular image
        image = Image.new("RGB", (300, 200), color="red")  # 3:2 ratio

        # Target square format
        result = resize_and_crop(image, 100, 100)

        # Should be cropped to square
        assert result.size == (100, 100)

    def test_resize_and_crop_with_real_photos(self, real_images):
        """Test resize and crop functionality with real photo files."""
        if not real_images:
            pytest.skip("No real images available for testing")

        # Test with first real image
        image_path = real_images[0]
        with Image.open(image_path) as img:
            original_size = img.size

            # Test various common slideshow resolutions
            test_resolutions = [
                (640, 480),  # Standard definition
                (1280, 720),  # HD
                (1920, 1080),  # Full HD
            ]

            for target_width, target_height in test_resolutions:
                result = resize_and_crop(img, target_width, target_height)

                # Should always produce exact target dimensions
                assert result.size == (target_width, target_height)

                # Should preserve the image mode (RGB for photos)
                assert result.mode == img.mode

                # Result should be a valid image
                assert isinstance(result, Image.Image)
