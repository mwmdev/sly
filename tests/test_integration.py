"""Integration tests for sly slideshow application with real files."""

import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image
import time
from unittest.mock import patch, Mock

from sly.slideshow import SlideshowCreator
from sly.image_utils import get_image_files, rotate_image, resize_and_crop
from sly.video_utils import create_title_slide, process_images
from sly.config import load_config_file, get_config_path


class TestRealImageProcessing:
    """Integration tests using real image files."""

    def test_get_image_files_with_real_files(self, real_images_dir):
        """Test get_image_files with real image files."""
        image_dir, image_paths = real_images_dir
        
        # Test name ordering
        files = get_image_files(image_dir, "name")
        filenames = [f.name for f in files]
        expected_names = ["photo_1.jpg", "photo_2.jpg", "photo_3.jpg", "photo_4.jpg", "photo_5.jpg", "photo_6.jpg"]
        assert filenames == expected_names
        
        # Test that all files exist and are readable
        for file_path in files:
            assert file_path.exists()
            with Image.open(file_path) as img:
                assert img.size[0] > 0
                assert img.size[1] > 0
                # Real images should have reasonable dimensions
                assert img.size[0] >= 100
                assert img.size[1] >= 100

    def test_get_image_files_date_ordering(self, real_images_dir):
        """Test date-based ordering with real files."""
        image_dir, image_paths = real_images_dir
        
        # Modify timestamps to test date ordering
        files = list(Path(image_dir).glob("*.jpg"))
        
        # Set different timestamps
        base_time = time.time()
        for i, file_path in enumerate(files):
            os.utime(file_path, (base_time + i*100, base_time + i*100))
        
        # Test date ordering
        ordered_files = get_image_files(image_dir, "date")
        
        # Verify ordering by checking timestamps
        timestamps = [os.path.getmtime(f) for f in ordered_files]
        assert timestamps == sorted(timestamps)

    def test_image_transformations_with_real_images(self, real_images_dir):
        """Test image rotation and resizing with real images."""
        image_dir, image_paths = real_images_dir
        files = get_image_files(image_dir, "name")
        
        for file_path in files:
            with Image.open(file_path) as img:
                original_size = img.size
                
                # Test rotation (should work even without EXIF)
                rotated = rotate_image(img)
                assert rotated.size is not None
                
                # Test resize and crop with real images
                resized = resize_and_crop(img, 100, 100)
                assert resized.size == (100, 100)
                
                # Test different aspect ratios
                wide_resized = resize_and_crop(img, 200, 100)
                assert wide_resized.size == (200, 100)
                
                tall_resized = resize_and_crop(img, 100, 200)
                assert tall_resized.size == (100, 200)
                
                # Test that we preserve image quality with real photos
                large_resized = resize_and_crop(img, 1920, 1080)
                assert large_resized.size == (1920, 1080)
                assert large_resized.mode == img.mode  # Should preserve color mode

    def test_process_images_with_real_files(self, real_images_dir):
        """Test image processing pipeline with real files."""
        image_dir, image_paths = real_images_dir
        files = get_image_files(image_dir, "name")
        
        # Mock MoviePy ImageClip to avoid video dependencies
        with patch('sly.video_utils.ImageClip') as mock_clip:
            mock_instance = mock_clip.return_value
            mock_instance.set_duration.return_value = mock_instance
            
            clips = process_images(files, 640, 480, 2.0)
            
            assert len(clips) == len(files)
            assert mock_clip.call_count == len(files)
            
            # Verify that each clip was given the correct duration
            for _ in range(len(files)):
                mock_instance.set_duration.assert_any_call(2.0)

    def test_real_image_metadata_preservation(self, real_images):
        """Test that real image metadata is handled properly."""
        for image_path in real_images:
            with Image.open(image_path) as img:
                # Test that we can read real image properties
                assert img.format in ['JPEG', 'JPG']
                assert img.mode in ['RGB', 'RGBA', 'L']
                
                # Test EXIF data handling (real photos might have EXIF)
                try:
                    exif = img.getexif()
                    rotated = rotate_image(img)
                    # Should handle EXIF rotation if present
                    assert isinstance(rotated, Image.Image)
                except Exception:
                    # If no EXIF data, should still work
                    rotated = rotate_image(img)
                    assert isinstance(rotated, Image.Image)

    def test_empty_directory_handling(self):
        """Test handling of directory with no images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-image files
            (Path(temp_dir) / "text.txt").write_text("not an image")
            (Path(temp_dir) / "data.json").write_text("{}")
            
            with pytest.raises(FileNotFoundError, match="No image files found"):
                get_image_files(temp_dir, "name")

    def test_mixed_file_types_directory(self, mixed_content_dir):
        """Test directory with mixed file types including real images and audio."""
        # mixed_content_dir already has real images, audio files, and other content
        
        # Should only return image files
        files = get_image_files(mixed_content_dir, "name")
        assert len(files) == 6  # Only the 6 real image files
        
        for file_path in files:
            assert file_path.suffix.lower() == '.jpg'
            assert file_path.name.startswith('photo_')
            
        # Verify the directory also contains non-image files (audio, text, etc.)
        all_files = list(Path(mixed_content_dir).iterdir())
        assert len(all_files) > 6  # Should have more than just images
        
        # Check for audio files
        audio_files = [f for f in all_files if f.suffix.lower() in ['.mp3', '.wav']]
        assert len(audio_files) == 2


class TestRealAudioIntegration:
    """Integration tests using real audio files."""
    
    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.AudioFileClip')
    @patch('sly.slideshow.concatenate_videoclips')
    @patch('sly.video_utils.ImageClip')
    @patch('sly.video_utils.CompositeVideoClip')
    @patch('sly.video_utils.ColorClip')
    def test_slideshow_with_real_mp3_soundtrack(
        self, mock_color_clip, mock_composite, mock_image_clip, mock_concat, mock_audio_clip, mock_input,
        real_images_dir, real_audio_files
    ):
        """Test slideshow creation with real MP3 soundtrack."""
        image_dir, image_paths = real_images_dir
        mp3_path = str(real_audio_files["mp3"])
        
        # Setup mocks with proper attributes for MoviePy
        mock_clip = mock_image_clip.return_value
        mock_clip.size = (1920, 1080)  # Proper tuple for size
        mock_clip.fps = 30.0  # Numeric fps value
        mock_clip.duration = 3.0  # Numeric duration
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_clip.fadeout.return_value = mock_clip
        mock_clip.set_start.return_value = mock_clip
        mock_clip.crossfadein.return_value = mock_clip
        
        mock_final_clip = mock_concat.return_value
        mock_final_clip.duration = 18.0  # 6 images * 3 seconds each
        mock_final_clip.write_videofile = Mock()
        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
        
        mock_audio = mock_audio_clip.return_value
        mock_audio.duration = 25.0  # Longer than video
        mock_audio.subclip.return_value = mock_audio
        
        # Setup CompositeVideoClip and ColorClip mocks
        mock_composite_clip = mock_composite.return_value
        mock_composite_clip.set_duration.return_value = mock_composite_clip
        mock_composite_clip.size = (1920, 1080)
        mock_composite_clip.fps = 30.0
        
        mock_black_clip = mock_color_clip.return_value
        mock_black_clip.set_duration.return_value = mock_black_clip
        mock_black_clip.size = (1920, 1080)
        
        # Create slideshow with real audio
        creator = SlideshowCreator()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        try:
            creator.create_slideshow(
                path=image_dir,
                output=output_path,
                soundtrack=mp3_path,
                image_duration=3.0
            )
            
            # Verify audio was loaded with real file path
            mock_audio_clip.assert_called_once_with(mp3_path)
            
            # Verify audio was trimmed to video length
            mock_audio.subclip.assert_called_once_with(0, 18.0)
            
            # Verify final clip got audio
            mock_final_clip.set_audio.assert_called_once()
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.AudioFileClip')
    @patch('sly.slideshow.concatenate_videoclips')
    @patch('sly.video_utils.ImageClip')
    @patch('sly.video_utils.CompositeVideoClip')
    @patch('sly.video_utils.ColorClip')
    def test_slideshow_with_real_wav_soundtrack(
        self, mock_color_clip, mock_composite, mock_image_clip, mock_concat, mock_audio_clip, mock_input,
        real_images_dir, real_audio_files
    ):
        """Test slideshow creation with real WAV soundtrack."""
        image_dir, image_paths = real_images_dir
        wav_path = str(real_audio_files["wav"])
        
        # Setup mocks for short audio that needs looping
        mock_clip = mock_image_clip.return_value
        mock_clip.size = (1920, 1080)  # Proper tuple for size
        mock_clip.fps = 30.0  # Numeric fps value
        mock_clip.duration = 3.0  # Numeric duration
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_clip.fadeout.return_value = mock_clip
        mock_clip.set_start.return_value = mock_clip
        mock_clip.crossfadein.return_value = mock_clip
        
        mock_final_clip = mock_concat.return_value
        mock_final_clip.duration = 20.0
        mock_final_clip.write_videofile = Mock()
        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
        
        mock_audio = mock_audio_clip.return_value
        mock_audio.duration = 10.0  # Shorter than video, needs looping
        mock_looped_audio = mock_audio_clip.return_value
        mock_audio.audio_loop.return_value = mock_looped_audio
        
        # Setup CompositeVideoClip and ColorClip mocks
        mock_composite_clip = mock_composite.return_value
        mock_composite_clip.set_duration.return_value = mock_composite_clip
        mock_composite_clip.size = (1920, 1080)
        mock_composite_clip.fps = 30.0
        
        mock_black_clip = mock_color_clip.return_value
        mock_black_clip.set_duration.return_value = mock_black_clip
        mock_black_clip.size = (1920, 1080)
        
        creator = SlideshowCreator()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        try:
            creator.create_slideshow(
                path=image_dir,
                output=output_path,
                soundtrack=wav_path,
                image_duration=3.0
            )
            
            # Verify audio was loaded with real WAV file
            mock_audio_clip.assert_called_once_with(wav_path)
            
            # Verify audio looping was applied
            mock_audio.audio_loop.assert_called_once_with(duration=20.0)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_audio_file_accessibility(self, real_audio_files):
        """Test that real audio files are accessible and have expected properties."""
        for audio_format, audio_path in real_audio_files.items():
            # Verify files exist and are readable
            assert audio_path.exists()
            assert audio_path.is_file()
            assert os.access(audio_path, os.R_OK)
            
            # Verify file sizes are reasonable (not empty, not too large)
            file_size = audio_path.stat().st_size
            assert file_size > 1000  # At least 1KB
            assert file_size < 100 * 1024 * 1024  # Less than 100MB
            
            # Verify correct file extensions
            if audio_format == "mp3":
                assert audio_path.suffix.lower() == ".mp3"
            elif audio_format == "wav":
                assert audio_path.suffix.lower() == ".wav"


class TestConfigIntegration:
    """Integration tests for configuration loading with real files."""

    def test_config_file_loading_real_file(self):
        """Test loading configuration from a real TOML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as temp_file:
            # Write real TOML content
            temp_file.write("""
# Slideshow configuration
image-duration = 4.5
slideshow-width = 1280
slideshow-height = 720
transition-duration = 0.5

[advanced]
fps = 30.0
image-order = "date"
""")
            temp_file.flush()
            
            try:
                config = load_config_file(temp_file.name)
                
                assert config["image-duration"] == 4.5
                assert config["slideshow-width"] == 1280
                assert config["slideshow-height"] == 720
                assert config["transition-duration"] == 0.5
                assert config["advanced"]["fps"] == 30.0
                assert config["advanced"]["image-order"] == "date"
                
            finally:
                os.unlink(temp_file.name)

    def test_config_path_resolution(self):
        """Test configuration path resolution with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config file
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("image-duration = 2.5\n")
            
            # Test that existing file is found
            result_path = get_config_path(str(config_path))
            assert result_path == str(config_path)
            
            # Test that non-existent file falls back to default
            non_existent = Path(temp_dir) / "missing.toml"
            result_path = get_config_path(str(non_existent))
            assert result_path == "config.toml"  # Default fallback

    def test_malformed_config_file(self):
        """Test handling of malformed TOML files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as temp_file:
            # Write invalid TOML
            temp_file.write("""
# This is invalid TOML
image-duration = 
slideshow-width = "not a number"
[incomplete section
""")
            temp_file.flush()
            
            try:
                # Should return empty dict for invalid TOML
                config = load_config_file(temp_file.name)
                assert config == {}
                
            finally:
                os.unlink(temp_file.name)


class TestEndToEndWorkflow:
    """End-to-end tests that simulate real usage scenarios."""

    @pytest.fixture
    def complete_test_environment(self):
        """Set up a complete test environment with images and config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample images
            image_dir = Path(temp_dir) / "images"
            image_dir.mkdir()
            
            for i in range(3):
                img = Image.new('RGB', (800, 600), color=(i*80, (i+1)*60, (i+2)*40))
                # Add some visual content
                pixels = img.load()
                for x in range(100):
                    for y in range(100):
                        pixels[x, y] = (x*2, y*2, (x+y))
                
                img.save(image_dir / f"photo_{i:03d}.jpg")
            
            # Create config file
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("""
image-duration = 2.0
transition-duration = 0.5
slideshow-width = 640
slideshow-height = 480
fps = 24.0
""")
            
            yield {
                "temp_dir": temp_dir,
                "image_dir": str(image_dir),
                "config_path": str(config_path),
                "output_path": str(Path(temp_dir) / "output.mp4")
            }

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.concatenate_videoclips')
    @patch('sly.video_utils.ImageClip')
    @patch('sly.video_utils.CompositeVideoClip')
    @patch('sly.video_utils.ColorClip')
    def test_complete_slideshow_creation_workflow(
        self, mock_color_clip, mock_composite, mock_image_clip, mock_concat, mock_input, complete_test_environment
    ):
        """Test the complete slideshow creation workflow with real files."""
        env = complete_test_environment
        
        # Setup mocks to avoid actual video creation
        mock_clip = mock_image_clip.return_value
        mock_clip.size = (640, 480)  # Proper tuple for size
        mock_clip.fps = 24.0  # Numeric fps value
        mock_clip.duration = 2.0  # Numeric duration
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_clip.fadeout.return_value = mock_clip
        mock_clip.set_start.return_value = mock_clip
        mock_clip.crossfadein.return_value = mock_clip
        
        mock_final_clip = mock_concat.return_value
        mock_final_clip.duration = 8.0
        mock_final_clip.write_videofile = Mock()
        
        # Create slideshow
        creator = SlideshowCreator()
        
        # Should not raise exceptions
        creator.create_slideshow(
            path=env["image_dir"],
            output=env["output_path"],
            image_duration=2.0,
            transition_duration=0.5,
            slideshow_width=640,
            slideshow_height=480
        )
        
        # Verify that the workflow executed
        assert mock_image_clip.call_count == 3  # 3 images processed
        mock_final_clip.write_videofile.assert_called_once()

    def test_error_handling_with_corrupted_images(self):
        """Test error handling with corrupted image files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a "corrupted" image file (just text)
            corrupted_image = Path(temp_dir) / "corrupted.jpg"
            corrupted_image.write_text("This is not an image file")
            
            # Should raise an exception when trying to process
            with pytest.raises(Exception):  # PIL will raise an exception
                files = [corrupted_image]
                with patch('sly.video_utils.ImageClip'):
                    process_images(files, 640, 480, 2.0)

    def test_performance_with_multiple_images(self):
        """Test performance characteristics with multiple images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create more images to test performance
            num_images = 10
            
            start_time = time.time()
            
            for i in range(num_images):
                img = Image.new('RGB', (400, 300), color=(i*25, i*20, i*15))
                img.save(Path(temp_dir) / f"perf_test_{i:03d}.jpg")
            
            creation_time = time.time() - start_time
            
            # Test file discovery performance
            start_time = time.time()
            files = get_image_files(temp_dir, "name")
            discovery_time = time.time() - start_time
            
            assert len(files) == num_images
            assert creation_time < 5.0  # Should create files quickly
            assert discovery_time < 1.0  # Should discover files quickly

    def test_large_image_handling(self):
        """Test handling of large images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a larger image
            large_img = Image.new('RGB', (4000, 3000), color='purple')
            large_img.save(Path(temp_dir) / "large_image.jpg")
            
            files = get_image_files(temp_dir, "name")
            assert len(files) == 1
            
            # Test that it can be processed without issues
            with Image.open(files[0]) as img:
                resized = resize_and_crop(img, 1920, 1080)
                assert resized.size == (1920, 1080)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_image_slideshow(self):
        """Test creating slideshow with only one image."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create single image
            img = Image.new('RGB', (800, 600), color='orange')
            img.save(Path(temp_dir) / "single.jpg")
            
            files = get_image_files(temp_dir, "name")
            assert len(files) == 1
            
            # Should handle single image without errors
            with patch('sly.video_utils.ImageClip') as mock_clip:
                mock_instance = mock_clip.return_value
                mock_instance.set_duration.return_value = mock_instance
                
                clips = process_images(files, 640, 480, 3.0)
                assert len(clips) == 1

    def test_very_small_images(self):
        """Test handling of very small images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create tiny image
            tiny_img = Image.new('RGB', (10, 10), color='cyan')
            tiny_img.save(Path(temp_dir) / "tiny.jpg")
            
            files = get_image_files(temp_dir, "name")
            
            with Image.open(files[0]) as img:
                # Should be able to resize even tiny images
                resized = resize_and_crop(img, 1920, 1080)
                assert resized.size == (1920, 1080)

    def test_unusual_aspect_ratios(self):
        """Test handling of images with unusual aspect ratios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create images with extreme aspect ratios
            very_wide = Image.new('RGB', (2000, 100), color='red')
            very_tall = Image.new('RGB', (100, 2000), color='blue')
            
            very_wide.save(Path(temp_dir) / "very_wide.jpg")
            very_tall.save(Path(temp_dir) / "very_tall.jpg")
            
            files = get_image_files(temp_dir, "name")
            
            for file_path in files:
                with Image.open(file_path) as img:
                    # Should handle extreme ratios without errors
                    square = resize_and_crop(img, 500, 500)
                    assert square.size == (500, 500)
                    
                    wide = resize_and_crop(img, 1000, 200)
                    assert wide.size == (1000, 200) 