"""Unit tests for sly.image_utils module."""

import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from PIL import Image

from sly.image_utils import get_image_files, get_media_files, rotate_image, resize_and_crop, is_video_file, is_image_file


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


class TestGetMediaFiles:
    """Test cases for get_media_files function (images and videos)."""

    def test_get_media_files_mixed_content(self):
        """Test getting mixed image and video files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test media files
            media_files = ["photo.jpg", "video.mp4", "image.png", "movie.avi"]
            for filename in media_files:
                Path(temp_dir, filename).touch()

            result = get_media_files(temp_dir, "name")
            result_names = [f.name for f in result]

            assert sorted(result_names) == ["image.png", "movie.avi", "photo.jpg", "video.mp4"]

    def test_get_media_files_video_extensions(self):
        """Test that all supported video extensions are recognized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with various video extensions
            video_extensions = [
                ".mp4", ".avi", ".mov", ".mkv", ".wmv", 
                ".flv", ".webm", ".m4v", ".3gp", ".mpg", ".mpeg"
            ]
            for i, ext in enumerate(video_extensions):
                Path(temp_dir, f"video{i}{ext}").touch()

            result = get_media_files(temp_dir, "name")
            assert len(result) == len(video_extensions)

    def test_get_media_files_images_only(self):
        """Test getting only image files when no videos present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test image files
            image_files = ["a.jpg", "b.png", "c.gif"]
            for filename in image_files:
                Path(temp_dir, filename).touch()

            result = get_media_files(temp_dir, "name")
            result_names = [f.name for f in result]

            assert result_names == ["a.jpg", "b.png", "c.gif"]

    def test_get_media_files_videos_only(self):
        """Test getting only video files when no images present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test video files
            video_files = ["movie1.mp4", "movie2.avi", "movie3.mov"]
            for filename in video_files:
                Path(temp_dir, filename).touch()

            result = get_media_files(temp_dir, "name")
            result_names = [f.name for f in result]

            assert result_names == ["movie1.mp4", "movie2.avi", "movie3.mov"]

    def test_get_media_files_empty_directory(self):
        """Test that FileNotFoundError is raised for directory with no media files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-media file
            Path(temp_dir, "document.txt").touch()

            with pytest.raises(FileNotFoundError, match="No image or video files found"):
                get_media_files(temp_dir, "name")

    def test_get_media_files_date_order(self):
        """Test getting media files ordered by date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test media files with different timestamps
            files = []
            for i, filename in enumerate(["old.jpg", "newer.mp4", "newest.png"]):
                filepath = Path(temp_dir, filename)
                filepath.touch()
                # Modify the timestamp
                os.utime(filepath, (1000 + i, 1000 + i))
                files.append(filepath)

            result = get_media_files(temp_dir, "date")
            result_names = [f.name for f in result]

            assert result_names == ["old.jpg", "newer.mp4", "newest.png"]


class TestFileTypeDetection:
    """Test cases for file type detection functions."""

    def test_is_video_file_positive_cases(self):
        """Test video file detection for valid video files."""
        video_files = [
            Path("movie.mp4"),
            Path("clip.avi"),
            Path("video.mov"),
            Path("film.mkv"),
            Path("recording.wmv"),
            Path("stream.flv"),
            Path("content.webm"),
            Path("mobile.m4v"),
            Path("phone.3gp"),
            Path("old.mpg"),
            Path("classic.mpeg"),
        ]
        
        for video_file in video_files:
            assert is_video_file(video_file), f"{video_file} should be detected as video"

    def test_is_video_file_negative_cases(self):
        """Test video file detection for non-video files."""
        non_video_files = [
            Path("photo.jpg"),
            Path("image.png"),
            Path("document.txt"),
            Path("archive.zip"),
            Path("song.mp3"),
            Path("presentation.ppt"),
        ]
        
        for non_video_file in non_video_files:
            assert not is_video_file(non_video_file), f"{non_video_file} should not be detected as video"

    def test_is_image_file_positive_cases(self):
        """Test image file detection for valid image files."""
        image_files = [
            Path("photo.jpg"),
            Path("picture.jpeg"),
            Path("graphic.png"),
            Path("animation.gif"),
            Path("bitmap.bmp"),
            Path("scan.tiff"),
            Path("document.tif"),
            Path("web.webp"),
        ]
        
        for image_file in image_files:
            assert is_image_file(image_file), f"{image_file} should be detected as image"

    def test_is_image_file_negative_cases(self):
        """Test image file detection for non-image files."""
        non_image_files = [
            Path("video.mp4"),
            Path("movie.avi"),
            Path("document.txt"),
            Path("archive.zip"),
            Path("song.mp3"),
            Path("presentation.ppt"),
        ]
        
        for non_image_file in non_image_files:
            assert not is_image_file(non_image_file), f"{non_image_file} should not be detected as image"

    def test_case_insensitive_detection(self):
        """Test that file type detection is case insensitive."""
        # Test uppercase extensions
        assert is_video_file(Path("VIDEO.MP4"))
        assert is_video_file(Path("movie.AVI"))
        assert is_image_file(Path("PHOTO.JPG"))
        assert is_image_file(Path("image.PNG"))

        # Test mixed case extensions
        assert is_video_file(Path("clip.Mp4"))
        assert is_image_file(Path("pic.JpG"))
