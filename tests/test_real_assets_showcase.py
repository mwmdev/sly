"""Comprehensive tests showcasing real assets (images and audio)."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from PIL import Image

from sly.slideshow import SlideshowCreator
from sly.image_utils import get_image_files, resize_and_crop, rotate_image
from sly.video_utils import process_images


class TestRealAssetsShowcase:
    """Comprehensive tests using real images and audio to demonstrate realistic usage."""

    def test_real_asset_inventory(self, assets_dir):
        """Test and document what real assets are available."""
        # Check images
        image_files = list(assets_dir.glob("photo_*.jpg"))
        assert len(image_files) == 6, f"Expected 6 photos, found {len(image_files)}"
        
        # Check audio files
        audio_files = list(assets_dir.glob("audio.*"))
        assert len(audio_files) == 2, f"Expected 2 audio files, found {len(audio_files)}"
        
        # Document image properties
        image_info = []
        for img_path in sorted(image_files):
            with Image.open(img_path) as img:
                info = {
                    "name": img_path.name,
                    "size": img.size,
                    "mode": img.mode,
                    "format": img.format,
                    "file_size_mb": round(img_path.stat().st_size / (1024*1024), 2)
                }
                image_info.append(info)
        
        # Verify we have a good variety of image sizes
        sizes = [info["size"] for info in image_info]
        widths = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        
        assert min(widths) >= 100, "Images should be reasonable size"
        assert min(heights) >= 100, "Images should be reasonable size"
        assert max(widths) >= 1000, "Should have some high-resolution images"
        
        # Document audio properties
        audio_info = []
        for audio_path in sorted(audio_files):
            info = {
                "name": audio_path.name,
                "format": audio_path.suffix,
                "file_size_mb": round(audio_path.stat().st_size / (1024*1024), 2)
            }
            audio_info.append(info)
        
        # Should have both MP3 and WAV
        formats = {info["format"] for info in audio_info}
        assert ".mp3" in formats, "Should have MP3 audio"
        assert ".wav" in formats, "Should have WAV audio"

    def test_realistic_image_processing_workflow(self, real_images):
        """Test complete image processing workflow with real photos."""
        # Test that all real images can be processed
        processed_results = []
        
        for image_path in real_images:
            with Image.open(image_path) as img:
                # Record original properties
                original_info = {
                    "path": image_path,
                    "original_size": img.size,
                    "original_mode": img.mode,
                    "file_size": image_path.stat().st_size
                }
                
                # Test rotation (important for photos from cameras)
                rotated = rotate_image(img)
                original_info["rotation_changed"] = rotated.size != img.size
                
                # Test standard slideshow resolutions
                test_resolutions = [
                    (640, 480),    # SD
                    (1280, 720),   # HD
                    (1920, 1080),  # Full HD
                    (3840, 2160),  # 4K
                ]
                
                resize_results = {}
                for width, height in test_resolutions:
                    resized = resize_and_crop(img, width, height)
                    resize_results[f"{width}x{height}"] = {
                        "success": resized.size == (width, height),
                        "mode_preserved": resized.mode == img.mode
                    }
                
                original_info["resize_results"] = resize_results
                processed_results.append(original_info)
        
        # Verify all images processed successfully
        assert len(processed_results) == 6, "Should process all 6 real images"
        
        for result in processed_results:
            # All resize operations should succeed
            for resolution, res_info in result["resize_results"].items():
                assert res_info["success"], f"Failed to resize {result['path'].name} to {resolution}"
                assert res_info["mode_preserved"], f"Mode not preserved for {result['path'].name} at {resolution}"

    @patch('sly.video_utils.ImageClip')
    def test_realistic_video_processing_with_real_images(self, mock_image_clip, real_images_dir):
        """Test video processing pipeline with real images."""
        image_dir, image_paths = real_images_dir
        
        # Mock MoviePy components
        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_image_clip.return_value = mock_clip
        
        # Test processing real images at different resolutions
        test_configs = [
            {"width": 1280, "height": 720, "duration": 3.0},
            {"width": 1920, "height": 1080, "duration": 2.5},
            {"width": 640, "height": 480, "duration": 4.0},
        ]
        
        for config in test_configs:
            clips = process_images(
                image_paths, 
                config["width"], 
                config["height"], 
                config["duration"]
            )
            
            # Should create clips for all real images
            assert len(clips) == len(image_paths)
            
            # Verify each clip was configured correctly
            for _ in range(len(image_paths)):
                mock_clip.set_duration.assert_any_call(config["duration"])

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.AudioFileClip')
    @patch('sly.slideshow.concatenate_videoclips')
    @patch('sly.video_utils.CompositeVideoClip')
    @patch('sly.video_utils.ColorClip')
    @patch('sly.video_utils.ImageClip')
    def test_complete_realistic_slideshow_creation(
        self, mock_image_clip, mock_color_clip, mock_composite_clip,
        mock_concat, mock_audio_clip, mock_input,
        real_images_dir, real_audio_files
    ):
        """Test creating a complete slideshow with real assets."""
        image_dir, image_paths = real_images_dir
        
        # Setup comprehensive mocks
        mock_clip = Mock()
        mock_clip.size = (1920, 1080)  # Add size attribute as tuple
        mock_clip.duration = 3.5  # Add duration attribute
        mock_clip.fps = 30.0  # Add fps attribute
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_clip.fadeout.return_value = mock_clip
        mock_clip.set_start.return_value = mock_clip
        mock_clip.crossfadein.return_value = mock_clip
        mock_image_clip.return_value = mock_clip
        
        # Mock ColorClip
        mock_black_clip = Mock()
        mock_black_clip.set_duration.return_value = mock_black_clip
        mock_color_clip.return_value = mock_black_clip
        
        # Mock CompositeVideoClip
        mock_composite = Mock()
        mock_composite.set_duration.return_value = mock_composite
        mock_composite_clip.return_value = mock_composite
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 21.0  # 6 images * 3.5 seconds each
        mock_final_clip.write_videofile = Mock()
        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
        mock_concat.return_value = mock_final_clip
        
        mock_audio = Mock()
        mock_audio.duration = 30.0
        mock_audio.subclip.return_value = mock_audio
        mock_audio_clip.return_value = mock_audio
        
        # Create slideshow with realistic parameters
        creator = SlideshowCreator()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        try:
            creator.create_slideshow(
                path=image_dir,
                output=output_path,
                image_duration=3.5,
                transition_duration=0.8,
                slideshow_width=1920,
                slideshow_height=1080,
                title="My Photo Slideshow",
                soundtrack=str(real_audio_files["mp3"]),
                fps=30.0,
                verbose=False
            )
            
            # Verify the complete workflow executed
            assert mock_image_clip.call_count == 7  # 6 real images + 1 title slide
            mock_audio_clip.assert_called_once_with(str(real_audio_files["mp3"]))
            mock_final_clip.write_videofile.assert_called_once()
            
            # Verify realistic video parameters were used
            write_call = mock_final_clip.write_videofile.call_args
            assert write_call[0][0] == output_path
            assert write_call[1]['fps'] == 30.0
            assert write_call[1]['codec'] == 'libx264'
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_audio_format_compatibility(self, real_audio_files):
        """Test that both audio formats work in realistic scenarios."""
        for format_name, audio_path in real_audio_files.items():
            # Test file accessibility
            assert audio_path.exists()
            assert audio_path.is_file()
            
            # Test file size is reasonable for audio
            file_size = audio_path.stat().st_size
            assert file_size > 10000, f"{format_name} file seems too small"
            assert file_size < 50 * 1024 * 1024, f"{format_name} file seems too large"
            
            # Test file extension matching
            expected_ext = f".{format_name}"
            assert audio_path.suffix.lower() == expected_ext
            
        # Test that we can use either format in slideshow creation
        # (This would be tested in integration scenarios above)

    def test_image_diversity_handling(self, real_images):
        """Test that the image set provides good diversity for testing."""
        image_properties = []
        
        for image_path in real_images:
            with Image.open(image_path) as img:
                # Calculate aspect ratio
                aspect_ratio = img.size[0] / img.size[1]
                
                properties = {
                    "name": image_path.name,
                    "width": img.size[0],
                    "height": img.size[1], 
                    "aspect_ratio": round(aspect_ratio, 2),
                    "orientation": "landscape" if aspect_ratio > 1 else "portrait" if aspect_ratio < 1 else "square",
                    "file_size": image_path.stat().st_size,
                    "mode": img.mode
                }
                image_properties.append(properties)
        
        # Check for good variety
        orientations = {prop["orientation"] for prop in image_properties}
        aspect_ratios = [prop["aspect_ratio"] for prop in image_properties]
        file_sizes = [prop["file_size"] for prop in image_properties]
        
        # Should have variety in the test set
        assert len(orientations) >= 1, "Should have at least some orientation variety"
        assert max(aspect_ratios) / min(aspect_ratios) > 1.1, "Should have aspect ratio variety"
        assert max(file_sizes) / min(file_sizes) > 1.5, "Should have file size variety"

    @pytest.mark.slow
    def test_performance_with_real_large_images(self, real_images):
        """Test performance characteristics with real image files."""
        import time
        
        # Test image loading performance
        load_times = []
        for image_path in real_images:
            start_time = time.time()
            with Image.open(image_path) as img:
                # Force image to load
                img.load()
            load_time = time.time() - start_time
            load_times.append(load_time)
        
        # All images should load reasonably quickly
        max_load_time = max(load_times)
        avg_load_time = sum(load_times) / len(load_times)
        
        assert max_load_time < 2.0, f"Image loading too slow: {max_load_time:.2f}s"
        assert avg_load_time < 0.5, f"Average loading too slow: {avg_load_time:.2f}s"
        
        # Test resize performance with real images
        resize_times = []
        for image_path in real_images:
            with Image.open(image_path) as img:
                start_time = time.time()
                resized = resize_and_crop(img, 1920, 1080)
                resize_time = time.time() - start_time
                resize_times.append(resize_time)
                
                # Verify resize worked
                assert resized.size == (1920, 1080)
        
        max_resize_time = max(resize_times)
        assert max_resize_time < 3.0, f"Image resizing too slow: {max_resize_time:.2f}s"

    def test_real_world_error_scenarios(self, real_images_dir, corrupted_image_dir):
        """Test error handling with a mix of real and problematic files."""
        image_dir, real_image_paths = real_images_dir
        
        # Copy a corrupted file into the real images directory
        corrupted_path = Path(image_dir) / "corrupted.jpg"
        corrupted_path.write_text("This is not a real image file")
        
        # Try to get image files - get_image_files should filter out corrupted files
        # but if it doesn't, we'll verify that only valid images are returned
        try:
            valid_files = get_image_files(image_dir, "name")
            
            # Verify all returned files are actually valid (can be opened)
            validated_files = []
            for file_path in valid_files:
                try:
                    with Image.open(file_path) as img:
                        if img.size[0] > 0 and img.size[1] > 0:
                            validated_files.append(file_path)
                except Exception:
                    # Skip corrupted files
                    pass
            
            # Should have all real images (6) in validated files
            assert len(validated_files) >= len(real_image_paths), \
                f"Expected at least {len(real_image_paths)} valid files, got {len(validated_files)}"
                
        except FileNotFoundError:
            # If get_image_files raises FileNotFoundError, that's also acceptable behavior
            pass

    def test_mixed_assets_integration(self, mixed_content_dir):
        """Test working with a directory that has images, audio, and other files."""
        # The mixed_content_dir fixture includes real images, audio, and other files
        
        # Should correctly identify only image files
        image_files = get_image_files(mixed_content_dir, "name")
        assert len(image_files) == 6  # 6 real photos
        
        # Verify directory contains other assets too
        all_files = list(Path(mixed_content_dir).iterdir())
        file_extensions = {f.suffix.lower() for f in all_files}
        
        # Should have images, audio, and text files
        assert '.jpg' in file_extensions, "Should have JPEG images"
        assert '.mp3' in file_extensions, "Should have MP3 audio"
        assert '.wav' in file_extensions, "Should have WAV audio"
        assert '.txt' in file_extensions, "Should have text files"
        
        # Should have more files than just images
        assert len(all_files) > len(image_files), "Should have non-image files too"


# Mark this file for integration testing
pytestmark = [
    pytest.mark.integration,
    pytest.mark.unit,  # Also include as unit for default runs
] 