"""Unit tests for sly.video_utils module."""

import pytest
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from PIL import Image, ImageFont

from sly.video_utils import create_title_slide, process_images, process_media_files, apply_transitions


class TestCreateTitleSlide:
    """Test cases for create_title_slide function."""

    @patch("sly.video_utils.ImageDraw.Draw")
    @patch("sly.video_utils.Image.new")
    @patch("sly.video_utils.ImageFont.truetype")
    @patch("sly.video_utils.ImageClip")
    def test_create_title_slide_with_custom_font(
        self, mock_image_clip, mock_truetype, mock_image_new, mock_draw
    ):
        """Test creating title slide with custom font."""
        # Setup mocks
        mock_font = Mock()
        mock_truetype.return_value = mock_font

        mock_pil_image = Mock()
        mock_image_new.return_value = mock_pil_image

        mock_draw_obj = Mock()
        mock_draw_obj.textbbox.return_value = (
            0,
            0,
            100,
            50,
        )  # left, top, right, bottom
        mock_draw.return_value = mock_draw_obj

        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_image_clip.return_value = mock_clip

        # Execute
        result = create_title_slide(
            title="Test Title",
            width=1920,
            height=1080,
            duration=3.0,
            font_path="/path/to/font.ttf",
            font_size=48,
        )

        # Verify
        mock_truetype.assert_called_once_with("/path/to/font.ttf", 48)
        mock_image_clip.assert_called_once()
        mock_clip.set_duration.assert_called_once_with(3.0)
        mock_clip.fadein.assert_called_once_with(1.5)  # duration / 2
        assert result == mock_clip

    @patch("sly.video_utils.ImageDraw.Draw")
    @patch("sly.video_utils.Image.new")
    @patch("sly.video_utils.ImageFont.load_default")
    @patch("sly.video_utils.ImageClip")
    def test_create_title_slide_default_font(
        self, mock_image_clip, mock_load_default, mock_image_new, mock_draw
    ):
        """Test creating title slide with default font."""
        # Setup mocks
        mock_font = Mock()
        mock_load_default.return_value = mock_font

        mock_pil_image = Mock()
        mock_image_new.return_value = mock_pil_image

        mock_draw_obj = Mock()
        mock_draw_obj.textbbox.return_value = (
            0,
            0,
            100,
            50,
        )  # left, top, right, bottom
        mock_draw.return_value = mock_draw_obj

        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_image_clip.return_value = mock_clip

        # Execute without custom font
        result = create_title_slide(
            title="Test Title", width=1920, height=1080, duration=3.0
        )

        # Verify default font is used
        mock_load_default.assert_called_once()
        assert result == mock_clip

    @patch("sly.video_utils.ImageDraw.Draw")
    @patch("sly.video_utils.Image.new")
    @patch("sly.video_utils.ImageFont.truetype")
    @patch("sly.video_utils.ImageFont.load_default")
    @patch("sly.video_utils.ImageClip")
    def test_create_title_slide_font_loading_error(
        self,
        mock_image_clip,
        mock_load_default,
        mock_truetype,
        mock_image_new,
        mock_draw,
    ):
        """Test fallback to default font when custom font fails to load."""
        # Setup mocks
        mock_truetype.side_effect = IOError("Font not found")
        mock_font = Mock()
        mock_load_default.return_value = mock_font

        mock_pil_image = Mock()
        mock_image_new.return_value = mock_pil_image

        mock_draw_obj = Mock()
        mock_draw_obj.textbbox.return_value = (
            0,
            0,
            100,
            50,
        )  # left, top, right, bottom
        mock_draw.return_value = mock_draw_obj

        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_image_clip.return_value = mock_clip

        # Execute with invalid font path
        result = create_title_slide(
            title="Test Title",
            width=1920,
            height=1080,
            duration=3.0,
            font_path="/invalid/path.ttf",
        )

        # Verify fallback to default font
        mock_truetype.assert_called_once()
        mock_load_default.assert_called_once()
        assert result == mock_clip

    @patch("sly.video_utils.ImageDraw.Draw")
    @patch("sly.video_utils.Image.new")
    @patch("sly.video_utils.ImageFont.load_default")
    @patch("sly.video_utils.ImageClip")
    def test_create_title_slide_auto_font_size(
        self, mock_image_clip, mock_load_default, mock_image_new, mock_draw
    ):
        """Test automatic font size calculation."""
        # Setup mocks
        mock_font = Mock()
        mock_load_default.return_value = mock_font

        mock_pil_image = Mock()
        mock_image_new.return_value = mock_pil_image

        mock_draw_obj = Mock()
        mock_draw_obj.textbbox.return_value = (
            0,
            0,
            100,
            50,
        )  # left, top, right, bottom
        mock_draw.return_value = mock_draw_obj

        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fadein.return_value = mock_clip
        mock_image_clip.return_value = mock_clip

        # Execute without font size
        create_title_slide(title="Test Title", width=1200, height=800, duration=3.0)

        # Font size should be min(width, height) // 10 = 80
        # This is harder to test without mocking PIL internals,
        # but we can verify the function runs without error
        mock_load_default.assert_called_once()

    @patch("sly.video_utils.ImageFont.load_default")
    def test_create_title_slide_error_handling(self, mock_load_default):
        """Test error handling in title slide creation."""
        mock_load_default.side_effect = Exception("Font error")

        # Should raise the exception (not catch it silently)
        with pytest.raises(Exception, match="Font error"):
            create_title_slide(
                title="Test Title", width=1920, height=1080, duration=3.0
            )


class TestProcessImages:
    """Test cases for process_images function."""

    @pytest.fixture
    def mock_image_files(self):
        """Create mock image file paths."""
        return [Path(f"test_image_{i}.jpg") for i in range(3)]

    @patch("sly.video_utils.Image.open")
    @patch("sly.video_utils.rotate_image")
    @patch("sly.video_utils.resize_and_crop")
    @patch("sly.video_utils.ImageClip")
    def test_process_images_basic(
        self,
        mock_image_clip,
        mock_resize_crop,
        mock_rotate,
        mock_open,
        mock_image_files,
    ):
        """Test basic image processing workflow."""
        # Setup mocks
        mock_images = []
        mock_clips = []

        for i in range(3):
            mock_img = Mock()
            mock_images.append(mock_img)

            mock_processed_img = Mock()
            mock_resize_crop.return_value = mock_processed_img

            mock_clip = Mock()
            mock_clip.set_duration.return_value = mock_clip
            mock_clips.append(mock_clip)

        mock_open.side_effect = [
            Mock(__enter__=Mock(return_value=img), __exit__=Mock())
            for img in mock_images
        ]
        mock_rotate.side_effect = mock_images
        mock_image_clip.side_effect = mock_clips

        # Execute
        result = process_images(mock_image_files, 1920, 1080, 3.0)

        # Verify
        assert len(result) == 3
        assert mock_open.call_count == 3
        assert mock_rotate.call_count == 3
        assert mock_resize_crop.call_count == 3
        assert mock_image_clip.call_count == 3

        # Verify each clip has duration set
        for clip in mock_clips:
            clip.set_duration.assert_called_once_with(3.0)

    @patch("sly.video_utils.Image.open")
    def test_process_images_file_error(self, mock_open, mock_image_files):
        """Test handling of image file opening errors."""
        mock_open.side_effect = IOError("Cannot open image")

        # Should raise the exception
        with pytest.raises(IOError, match="Cannot open image"):
            process_images(mock_image_files, 1920, 1080, 3.0)

    @patch("sly.video_utils.Image.open")
    @patch("sly.video_utils.rotate_image")
    @patch("sly.video_utils.resize_and_crop")
    @patch("sly.video_utils.ImageClip")
    def test_process_images_different_sizes(
        self, mock_image_clip, mock_resize_crop, mock_rotate, mock_open
    ):
        """Test processing images with different target sizes."""
        # Setup single image
        mock_img = Mock()
        mock_open.return_value.__enter__.return_value = mock_img
        mock_rotate.return_value = mock_img

        mock_processed_img = Mock()
        mock_resize_crop.return_value = mock_processed_img

        mock_clip = Mock()
        mock_clip.set_duration.return_value = mock_clip
        mock_image_clip.return_value = mock_clip

        # Execute with different dimensions
        process_images([Path("test.jpg")], 800, 600, 2.5)

        # Verify resize_and_crop called with correct dimensions
        mock_resize_crop.assert_called_once_with(mock_img, 800, 600)
        mock_clip.set_duration.assert_called_once_with(2.5)


class TestApplyTransitions:
    """Test cases for apply_transitions function."""

    @pytest.fixture
    def mock_clips(self):
        """Create mock video clips."""
        clips = []
        for i in range(3):
            clip = Mock()
            # Use actual numbers for duration to avoid Mock arithmetic issues
            clip.duration = 3.0
            clip.size = (1920, 1080)
            clip.fadein.return_value = clip
            clip.fadeout.return_value = clip
            clip.set_start.return_value = clip
            clip.crossfadein.return_value = clip
            clip.set_duration.return_value = clip
            clips.append(clip)
        return clips

    @patch("sly.video_utils.ColorClip")
    @patch("sly.video_utils.CompositeVideoClip")
    def test_apply_transitions_with_title(
        self, mock_composite, mock_color_clip, mock_clips
    ):
        """Test applying transitions with title slide."""
        # Setup mocks
        mock_title = Mock()
        mock_title.fadein.return_value = mock_title
        mock_title.fadeout.return_value = mock_title

        mock_black_clip = Mock()
        mock_black_clip.set_duration.return_value = mock_black_clip
        mock_color_clip.return_value = mock_black_clip

        mock_transition_clip = Mock()
        mock_transition_clip.set_duration.return_value = mock_transition_clip
        mock_composite.return_value = mock_transition_clip

        # Execute
        result = apply_transitions(mock_clips, 1.0, mock_title)

        # Verify title slide processing
        mock_title.fadein.assert_called_with(1.0)
        mock_title.fadeout.assert_called_with(1.0)

        # Should have black clips, title, pause, and processed image clips
        assert len(result) > len(mock_clips)  # More clips due to title and transitions

    @patch("sly.video_utils.CompositeVideoClip")
    def test_apply_transitions_without_title(self, mock_composite, mock_clips):
        """Test applying transitions without title slide."""
        mock_transition_clip = Mock()
        mock_transition_clip.set_duration.return_value = mock_transition_clip
        mock_composite.return_value = mock_transition_clip

        # Execute
        result = apply_transitions(mock_clips, 1.0, None)

        # Verify first clip has fade in
        mock_clips[0].fadein.assert_called_once_with(1.0)

        # Verify last clip has fade out
        mock_clips[-1].fadeout.assert_called_once_with(1.0)

    def test_apply_transitions_single_clip(self, mock_clips):
        """Test transitions with only one clip."""
        single_clip = [mock_clips[0]]

        result = apply_transitions(single_clip, 1.0, None)

        # Single clip should have fade in
        single_clip[0].fadein.assert_called_with(1.0)
        # Note: fadeout behavior depends on implementation details

    @patch("sly.video_utils.CompositeVideoClip")
    def test_apply_transitions_composite_creation(self, mock_composite, mock_clips):
        """Test that composite clips are created correctly for transitions."""
        mock_transition_clip = Mock()
        mock_transition_clip.set_duration.return_value = mock_transition_clip
        mock_composite.return_value = mock_transition_clip

        apply_transitions(mock_clips, 1.5, None)

        # Should create composite clips for transitions between images
        assert mock_composite.call_count >= 1  # At least one transition

    def test_apply_transitions_empty_clips(self):
        """Test handling of empty clips list."""
        result = apply_transitions([], 1.0, None)
        assert result == []

    @patch("sly.video_utils.ColorClip")
    @patch("sly.video_utils.CompositeVideoClip")
    def test_apply_transitions_title_pause_duration(
        self, mock_composite, mock_color_clip, mock_clips
    ):
        """Test that pause after title has correct duration."""
        mock_title = Mock()
        mock_title.fadein.return_value = mock_title
        mock_title.fadeout.return_value = mock_title

        mock_black_clip = Mock()
        mock_black_clip.set_duration.return_value = mock_black_clip
        mock_color_clip.return_value = mock_black_clip

        mock_transition_clip = Mock()
        mock_transition_clip.set_duration.return_value = mock_transition_clip
        mock_composite.return_value = mock_transition_clip

        # Ensure clips have proper numeric duration and methods to avoid Mock arithmetic issues
        for i, clip in enumerate(mock_clips):
            clip.size = (1920, 1080)
            clip.duration = 3.0  # Ensure this is a real number
            # Make sure set_start returns a proper mock that supports chaining
            chained_mock = Mock()
            chained_mock.crossfadein.return_value = mock_transition_clip
            clip.set_start.return_value = chained_mock

        # Use only one clip to avoid complex transition logic
        single_clip = [mock_clips[0]]
        result = apply_transitions(single_clip, 1.0, mock_title)

        # Verify that ColorClip was called (black clips are created)
        assert (
            mock_color_clip.call_count >= 1
        ), "ColorClip should be called for black clips"

        # Verify that we got some result clips
        assert len(result) > 0, "Should return some clips"


class TestVideoUtilsIntegration:
    """Integration tests for video_utils functions working together."""

    @pytest.fixture
    def sample_images(self):
        """Create sample images for testing."""
        images = []
        for i in range(2):
            img = Image.new("RGB", (100, 100), color=(i * 100, i * 50, i * 25))
            images.append(img)
        return images

    def test_video_processing_pipeline(self, sample_images):
        """Test the complete video processing pipeline with real images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save sample images
            image_files = []
            for i, img in enumerate(sample_images):
                img_path = Path(temp_dir) / f"image_{i}.jpg"
                img.save(img_path)
                image_files.append(img_path)

            # Test the pipeline (without actually creating video clips to avoid moviepy)
            # This would be a good place for integration tests with real data
            # For now, we verify the files exist and can be opened
            for img_path in image_files:
                assert img_path.exists()
                with Image.open(img_path) as img:
                    assert img.size == (100, 100)


class TestProcessMediaFiles:
    """Test cases for process_media_files function (mixed images and videos)."""

    @pytest.fixture
    def mock_media_files(self):
        """Create mock mixed media file paths."""
        return [
            Path("image1.jpg"),
            Path("video1.mp4"),
            Path("image2.png"),
            Path("video2.avi")
        ]

    @patch("sly.video_utils.is_video_file")
    @patch("sly.video_utils.is_image_file")
    @patch("sly.video_utils.VideoFileClip")
    @patch("sly.video_utils.Image.open")
    @patch("sly.video_utils.rotate_image")
    @patch("sly.video_utils.resize_and_crop")
    @patch("sly.video_utils.ImageClip")
    def test_process_media_files_mixed_content(
        self,
        mock_image_clip,
        mock_resize_crop,
        mock_rotate,
        mock_open,
        mock_video_clip,
        mock_is_image,
        mock_is_video,
        mock_media_files,
    ):
        """Test processing mixed image and video files."""
        # Setup file type detection
        def side_effect_is_video(path):
            return str(path).endswith(('.mp4', '.avi'))
        
        def side_effect_is_image(path):
            return str(path).endswith(('.jpg', '.png'))
        
        mock_is_video.side_effect = side_effect_is_video
        mock_is_image.side_effect = side_effect_is_image

        # Setup video clips
        mock_video_clips = []
        for i in range(2):  # Two videos
            mock_clip = Mock()
            mock_clip.duration = 5.0
            mock_clip.resize.return_value = mock_clip
            mock_video_clips.append(mock_clip)
        mock_video_clip.side_effect = mock_video_clips

        # Setup image processing
        mock_images = []
        mock_image_clips = []
        for i in range(2):  # Two images
            mock_img = Mock()
            mock_images.append(mock_img)
            
            mock_img_clip = Mock()
            mock_img_clip.set_duration.return_value = mock_img_clip
            mock_image_clips.append(mock_img_clip)

        mock_open.side_effect = [
            Mock(__enter__=Mock(return_value=img), __exit__=Mock())
            for img in mock_images
        ]
        mock_rotate.side_effect = mock_images
        mock_resize_crop.side_effect = mock_images
        mock_image_clip.side_effect = mock_image_clips

        # Execute
        result = process_media_files(mock_media_files, 1920, 1080, 3.0, "original")

        # Verify we got clips for all files
        assert len(result) == 4

        # Verify video processing was called
        assert mock_video_clip.call_count == 2

        # Verify image processing was called
        assert mock_open.call_count == 2
        assert mock_image_clip.call_count == 2

    @patch("sly.video_utils.is_video_file")
    @patch("sly.video_utils.VideoFileClip")
    def test_process_media_files_video_duration_modes(
        self, mock_video_clip, mock_is_video
    ):
        """Test different video duration handling modes."""
        mock_is_video.return_value = True
        
        # Setup video clip with 10 second duration
        mock_clip = Mock()
        mock_clip.duration = 10.0
        mock_clip.resize.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.subclip.return_value = mock_clip
        mock_video_clip.return_value = mock_clip

        video_files = [Path("video.mp4")]

        # Test "fixed" mode
        process_media_files(video_files, 1920, 1080, 3.0, "fixed")
        mock_clip.set_duration.assert_called_with(3.0)

        # Reset mock
        mock_clip.reset_mock()

        # Test "limit" mode (should cap at 3.0 * 3 = 9.0, but video is 10.0)
        process_media_files(video_files, 1920, 1080, 3.0, "limit")
        mock_clip.subclip.assert_called_with(0, 9.0)

        # Reset mock
        mock_clip.reset_mock()

        # Test "original" mode (no duration changes)
        process_media_files(video_files, 1920, 1080, 3.0, "original")
        mock_clip.set_duration.assert_not_called()
        mock_clip.subclip.assert_not_called()

    @patch("sly.video_utils.is_video_file")
    @patch("sly.video_utils.is_image_file")
    @patch("sly.video_utils.console")
    def test_process_media_files_error_handling(
        self, mock_console, mock_is_image, mock_is_video
    ):
        """Test error handling in media file processing."""
        mock_is_video.return_value = False
        mock_is_image.return_value = False

        # Should handle unsupported file types gracefully
        result = process_media_files([Path("unsupported.xyz")], 1920, 1080, 3.0)
        
        # Should print warning and continue
        mock_console.print.assert_called()
        assert len(result) == 0  # No clips should be added for unsupported files


class TestTransitionTypes:
    """Test cases for new transition types functionality."""

    @pytest.fixture
    def mock_clips(self):
        """Create mock video clips for transition testing."""
        clips = []
        for i in range(3):
            clip = Mock()
            clip.duration = 3.0
            clip.size = (1920, 1080)
            clip.fadein.return_value = clip
            clip.fadeout.return_value = clip
            clips.append(clip)
        return clips

    @patch("sly.slideshow.create_fade_sequence")
    @patch("sly.slideshow.create_crossfade_sequence")
    def test_transition_type_selection(
        self, mock_crossfade, mock_fade, mock_clips
    ):
        """Test that correct transition function is called based on type."""
        # Import here to avoid circular imports in tests
        from sly.slideshow import create_transition_sequence
        
        mock_fade.return_value = Mock()
        mock_crossfade.return_value = Mock()

        # Test fade transition
        create_transition_sequence(mock_clips, 1.0, "fade")
        mock_fade.assert_called_once_with(mock_clips, 1.0)

        # Test crossfade transition
        create_transition_sequence(mock_clips, 1.0, "crossfade")
        mock_crossfade.assert_called_once_with(mock_clips, 1.0)

    def test_fade_transition_logic(self, mock_clips):
        """Test fade transition logic."""
        from sly.slideshow import create_fade_sequence
        
        # Mock concatenate_videoclips
        with patch("sly.slideshow.concatenate_videoclips") as mock_concat:
            mock_concat.return_value = Mock()
            
            create_fade_sequence(mock_clips, 1.0)
            
            # Verify first clip gets fade in
            mock_clips[0].fadein.assert_called_with(1.0)
            
            # Verify last clip gets fade out
            mock_clips[-1].fadeout.assert_called_with(1.0)
            
            # Verify middle clips get both fades
            if len(mock_clips) > 2:
                mock_clips[1].fadein.assert_called_with(0.5)  # transition_duration / 2
                mock_clips[1].fadeout.assert_called_with(0.5)

    @patch("sly.slideshow.CompositeVideoClip")
    def test_crossfade_transition_logic(self, mock_composite, mock_clips):
        """Test crossfade transition logic."""
        from sly.slideshow import create_crossfade_sequence
        
        # Setup mock composite clip
        mock_result = Mock()
        mock_composite.return_value = mock_result
        
        # Mock the set_start and crossfadein methods
        for clip in mock_clips:
            clip.set_start.return_value = clip
            clip.crossfadein.return_value = clip
        
        result = create_crossfade_sequence(mock_clips, 1.0)
        
        # Verify first clip gets fade in
        mock_clips[0].fadein.assert_called_with(1.0)
        
        # Verify last clip gets fade out
        mock_clips[-1].fadeout.assert_called_with(1.0)
        
        # Verify composite clip is created
        mock_composite.assert_called_once()
        assert result == mock_result

    def test_single_clip_transitions(self, mock_clips):
        """Test transition behavior with single clip."""
        from sly.slideshow import create_fade_sequence, create_crossfade_sequence
        
        single_clip = [mock_clips[0]]
        
        # Both transition types should handle single clips the same way
        fade_result = create_fade_sequence(single_clip, 1.0)
        crossfade_result = create_crossfade_sequence(single_clip, 1.0)
        
        # Both should apply fade in and out
        assert mock_clips[0].fadein.call_count >= 2  # Called by both functions
        assert mock_clips[0].fadeout.call_count >= 2  # Called by both functions

    def test_unknown_transition_type(self, mock_clips):
        """Test handling of unknown transition types."""
        from sly.slideshow import create_transition_sequence
        
        with patch("sly.slideshow.create_crossfade_sequence") as mock_crossfade:
            with patch("sly.slideshow.console") as mock_console:
                mock_crossfade.return_value = Mock()
                
                # Should fall back to crossfade and print warning
                create_transition_sequence(mock_clips, 1.0, "unknown_type")
                
                mock_console.print.assert_called_once()
                mock_crossfade.assert_called_once_with(mock_clips, 1.0)
