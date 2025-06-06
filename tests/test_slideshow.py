"""Unit tests for sly.slideshow module."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from PIL import Image

from sly.slideshow import SlideshowCreator


class TestSlideshowCreator:
    """Test cases for SlideshowCreator class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.creator = SlideshowCreator()

    @patch('builtins.input', return_value='y')
    def test_create_slideshow_with_real_images(self, mock_input, real_images_dir, real_audio_files):
        """Test slideshow creation with real images and audio files."""
        image_dir, image_paths = real_images_dir
        
        with patch('sly.slideshow.get_image_files') as mock_get_files:
            with patch('sly.slideshow.process_images') as mock_process:
                with patch('sly.slideshow.apply_transitions') as mock_transitions:
                    with patch('sly.slideshow.concatenate_videoclips') as mock_concat:
                        # Use real image files
                        mock_get_files.return_value = image_paths[:3]  # Use first 3 real images
                        
                        mock_clips = [Mock(), Mock(), Mock()]
                        mock_process.return_value = mock_clips
                        
                        mock_final_clips = [Mock(), Mock(), Mock()]
                        mock_transitions.return_value = mock_final_clips
                        
                        mock_final_clip = Mock()
                        mock_final_clip.duration = 9.0
                        mock_final_clip.write_videofile = Mock()
                        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
                        mock_concat.return_value = mock_final_clip

                        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                            output_path = temp_output.name

                        try:
                            # Execute with real files
                            self.creator.create_slideshow(
                                path=image_dir,
                                output=output_path,
                                image_duration=3.0,
                                slideshow_width=1920,
                                slideshow_height=1080,
                                soundtrack=str(real_audio_files["mp3"])
                            )

                            # Verify workflow with real file paths
                            mock_get_files.assert_called_once_with(image_dir, "name")
                            mock_process.assert_called_once_with(image_paths[:3], 1920, 1080, 3.0)
                            mock_transitions.assert_called_once_with(mock_clips, 1.0, None)
                            mock_concat.assert_called_once_with(mock_final_clips)
                            mock_final_clip.write_videofile.assert_called_once()

                        finally:
                            if os.path.exists(output_path):
                                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_basic_workflow(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_input
    ):
        """Test the basic slideshow creation workflow."""
        # Setup mocks
        mock_image_files = [Path(f"image{i}.jpg") for i in range(2)]
        mock_get_files.return_value = mock_image_files
        
        mock_clips = [Mock(), Mock()]
        mock_process.return_value = mock_clips
        
        mock_final_clips = [Mock(), Mock(), Mock()]
        mock_transitions.return_value = mock_final_clips
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 10.0
        mock_final_clip.write_videofile = Mock()
        mock_concat.return_value = mock_final_clip

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Execute
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path,
                image_duration=3.0,
                slideshow_width=1920,
                slideshow_height=1080
            )

            # Verify workflow
            mock_get_files.assert_called_once_with("./test_images", "name")
            mock_process.assert_called_once_with(mock_image_files, 1920, 1080, 3.0)
            mock_transitions.assert_called_once_with(mock_clips, 1.0, None)
            mock_concat.assert_called_once_with(mock_final_clips)
            mock_final_clip.write_videofile.assert_called_once()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.create_title_slide')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_with_title(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_title, mock_input
    ):
        """Test slideshow creation with title slide."""
        # Setup mocks
        mock_title_slide = Mock()
        mock_title.return_value = mock_title_slide
        
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.return_value = [Mock()]
        mock_transitions.return_value = [Mock()]
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 10.0
        mock_final_clip.write_videofile = Mock()
        mock_concat.return_value = mock_final_clip

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Execute with title
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path,
                title="Test Slideshow",
                font="/path/to/font.ttf",
                font_size=48
            )

            # Verify title slide creation
            mock_title.assert_called_once_with(
                "Test Slideshow", 1920, 1080, 3.0, "/path/to/font.ttf", 48
            )
            # Verify transitions was called with title slide
            args, kwargs = mock_transitions.call_args
            assert len(args[0]) == 1  # clips list should have 1 item
            assert args[1] == 1.0  # transition_duration
            assert args[2] == mock_title_slide  # title_slide

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.AudioFileClip')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_with_soundtrack(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_audio_clip, mock_input
    ):
        """Test slideshow creation with soundtrack."""
        # Setup mocks
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.return_value = [Mock()]
        mock_transitions.return_value = [Mock()]
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 10.0
        mock_final_clip.write_videofile = Mock()
        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
        mock_concat.return_value = mock_final_clip

        mock_audio = Mock()
        mock_audio.duration = 15.0
        mock_audio.subclip.return_value = mock_audio
        mock_audio_clip.return_value = mock_audio

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Execute with soundtrack
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path,
                soundtrack="test_music.mp3"
            )

            # Verify audio processing
            mock_audio_clip.assert_called_once_with("test_music.mp3")
            # Since audio.duration (15.0) > final_clip.duration (10.0), subclip should be called
            mock_audio.subclip.assert_called_once_with(0, 10.0)
            mock_final_clip.set_audio.assert_called_once_with(mock_audio)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.AudioFileClip')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_audio_loop(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_audio_clip, mock_input
    ):
        """Test slideshow creation with short audio that needs looping."""
        # Setup mocks
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.return_value = [Mock()]
        mock_transitions.return_value = [Mock()]
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 15.0
        mock_final_clip.write_videofile = Mock()
        mock_final_clip.set_audio = Mock(return_value=mock_final_clip)
        mock_concat.return_value = mock_final_clip

        mock_audio = Mock()
        mock_audio.duration = 5.0  # Shorter than video
        mock_looped_audio = Mock()
        mock_audio.audio_loop.return_value = mock_looped_audio
        mock_audio_clip.return_value = mock_audio

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Execute
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path,
                soundtrack="short_music.mp3"
            )

            # Verify audio looping
            mock_audio.audio_loop.assert_called_once_with(duration=15.0)
            mock_final_clip.set_audio.assert_called_once_with(mock_looped_audio)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.get_image_files')
    def test_create_slideshow_no_images_found(self, mock_get_files, mock_input):
        """Test handling when no images are found in directory."""
        mock_get_files.side_effect = FileNotFoundError("No image files found")

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Should handle the exception gracefully
            self.creator.create_slideshow(
                path="./empty_dir",
                output=output_path
            )
            # Function should return early, no video file should be created
            # (In a real scenario, you might want to verify this doesn't create output)

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='n')
    def test_create_slideshow_file_exists_no_overwrite(self, mock_input):
        """Test handling when output file exists and user chooses not to overwrite."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # File already exists, user says no to overwrite
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path
            )

            # Should return early without processing
            mock_input.assert_called_once()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_file_exists_overwrite(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_input
    ):
        """Test handling when output file exists and user chooses to overwrite."""
        # Setup mocks
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.return_value = [Mock()]
        mock_transitions.return_value = [Mock()]
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 10.0
        mock_final_clip.write_videofile = Mock()
        mock_concat.return_value = mock_final_clip

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # File exists, user says yes to overwrite
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path
            )

            # Should proceed with processing
            mock_input.assert_called_once()
            mock_final_clip.write_videofile.assert_called_once()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    def test_create_slideshow_processing_error(self, mock_process, mock_get_files, mock_input):
        """Test error handling during image processing."""
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.side_effect = Exception("Processing failed")

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            # Should raise the exception
            with pytest.raises(Exception):
                self.creator.create_slideshow(
                    path="./test_images",
                    output=output_path
                )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch('builtins.input', return_value='y')
    @patch('sly.slideshow.multiprocessing.cpu_count', return_value=8)
    @patch('sly.slideshow.get_image_files')
    @patch('sly.slideshow.process_images')
    @patch('sly.slideshow.apply_transitions')
    @patch('sly.slideshow.concatenate_videoclips')
    def test_create_slideshow_threading_optimization(
        self, mock_concat, mock_transitions, mock_process, mock_get_files, mock_cpu_count, mock_input
    ):
        """Test that the function properly calculates thread count for rendering."""
        # Setup mocks
        mock_get_files.return_value = [Path("image1.jpg")]
        mock_process.return_value = [Mock()]
        mock_transitions.return_value = [Mock()]
        
        mock_final_clip = Mock()
        mock_final_clip.duration = 10.0
        mock_final_clip.write_videofile = Mock()
        mock_concat.return_value = mock_final_clip

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name

        try:
            self.creator.create_slideshow(
                path="./test_images",
                output=output_path
            )

            # Verify thread count calculation (75% of 8 cores = 6 threads)
            call_args = mock_final_clip.write_videofile.call_args
            assert call_args[1]['threads'] == 6

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path) 