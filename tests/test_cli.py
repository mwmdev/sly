"""Unit tests for sly.cli module."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from sly.cli import parse_arguments, validate_arguments, main


class TestValidateArguments:
    """Test cases for validate_arguments function."""

    def test_validate_arguments_valid(self):
        """Test validation with valid arguments."""
        args = Namespace(
            path="./images",
            image_duration=3.0,
            transition_duration=1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=24.0,
            image_order="name",
        )

        assert validate_arguments(args) is True

    def test_validate_arguments_no_path(self):
        """Test validation fails when path is empty."""
        args = Namespace(
            path="",
            image_duration=3.0,
            transition_duration=1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=24.0,
            image_order="name",
        )

        assert validate_arguments(args) is False

    def test_validate_arguments_negative_image_duration(self):
        """Test validation fails with negative image duration."""
        args = Namespace(
            path="./images",
            image_duration=-1.0,
            transition_duration=1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=24.0,
            image_order="name",
        )

        assert validate_arguments(args) is False

    def test_validate_arguments_negative_transition_duration(self):
        """Test validation fails with negative transition duration."""
        args = Namespace(
            path="./images",
            image_duration=3.0,
            transition_duration=-1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=24.0,
            image_order="name",
        )

        assert validate_arguments(args) is False

    def test_validate_arguments_invalid_dimensions(self):
        """Test validation fails with invalid slideshow dimensions."""
        args = Namespace(
            path="./images",
            image_duration=3.0,
            transition_duration=1.0,
            slideshow_width=0,
            slideshow_height=1080,
            fps=24.0,
            image_order="name",
        )

        assert validate_arguments(args) is False

    def test_validate_arguments_invalid_fps(self):
        """Test validation fails with invalid FPS."""
        args = Namespace(
            path="./images",
            image_duration=3.0,
            transition_duration=1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=0,
            image_order="name",
        )

        assert validate_arguments(args) is False

    def test_validate_arguments_invalid_image_order(self):
        """Test validation fails with invalid image order."""
        args = Namespace(
            path="./images",
            image_duration=3.0,
            transition_duration=1.0,
            slideshow_width=1920,
            slideshow_height=1080,
            fps=24.0,
            image_order="invalid",
        )

        assert validate_arguments(args) is False


class TestParseArguments:
    """Test cases for parse_arguments function."""

    @patch("sys.argv", ["sly", "--path", "./test_images"])
    @patch("sly.cli.get_config_path")
    @patch("sly.cli.load_config_file")
    def test_parse_arguments_with_path(self, mock_load_config, mock_get_config_path):
        """Test parsing arguments with path specified."""
        mock_get_config_path.return_value = "config.toml"
        mock_load_config.return_value = {}

        args = parse_arguments()

        assert args.path == "./test_images"
        assert args.image_duration == 3.0  # default
        assert args.output == "slideshow.mp4"  # default

    @patch("sys.argv", ["sly", "--verbose"])
    @patch("sly.cli.get_config_path")
    @patch("sly.cli.load_config_file")
    def test_parse_arguments_verbose(self, mock_load_config, mock_get_config_path):
        """Test parsing arguments with verbose flag."""
        mock_get_config_path.return_value = "config.toml"
        mock_load_config.return_value = {}

        args = parse_arguments()

        assert args.verbose is True

    @patch("sys.argv", ["sly"])
    @patch("sly.cli.get_config_path")
    @patch("sly.cli.load_config_file")
    def test_parse_arguments_config_override(
        self, mock_load_config, mock_get_config_path
    ):
        """Test that config file values are used when CLI args are not provided."""
        mock_get_config_path.return_value = "config.toml"
        mock_load_config.return_value = {
            "image-duration": 5.0,
            "slideshow-width": 1280,
            "slideshow-height": 720,
        }

        args = parse_arguments()

        assert args.image_duration == 5.0
        assert args.slideshow_width == 1280
        assert args.slideshow_height == 720


class TestMain:
    """Test cases for main function."""

    @patch("sly.cli.parse_arguments")
    @patch("sly.cli.validate_arguments")
    @patch("sly.cli.SlideshowCreator")
    def test_main_success(self, mock_creator_class, mock_validate, mock_parse):
        """Test successful execution of main function."""
        # Mock arguments
        mock_args = MagicMock()
        mock_args.path = "./images"
        mock_args.output = "test.mp4"
        mock_args.verbose = False

        mock_parse.return_value = mock_args
        mock_validate.return_value = True

        # Mock slideshow creator
        mock_creator = MagicMock()
        mock_creator_class.return_value = mock_creator

        main()

        mock_creator.create_slideshow.assert_called_once()

    @patch("sly.cli.parse_arguments")
    @patch("sly.cli.validate_arguments")
    def test_main_validation_failure(self, mock_validate, mock_parse):
        """Test main function when validation fails."""
        mock_args = MagicMock()
        mock_parse.return_value = mock_args
        mock_validate.return_value = False

        # Should return early without creating slideshow
        with patch("sly.cli.SlideshowCreator") as mock_creator_class:
            main()
            mock_creator_class.assert_not_called()

    @patch("sly.cli.parse_arguments")
    @patch("sly.cli.validate_arguments")
    @patch("sly.cli.SlideshowCreator")
    def test_main_keyboard_interrupt(
        self, mock_creator_class, mock_validate, mock_parse
    ):
        """Test main function handles KeyboardInterrupt gracefully."""
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_parse.return_value = mock_args
        mock_validate.return_value = True

        # Mock slideshow creator to raise KeyboardInterrupt
        mock_creator = MagicMock()
        mock_creator.create_slideshow.side_effect = KeyboardInterrupt()
        mock_creator_class.return_value = mock_creator

        # Should not raise exception
        main()

    @patch("sly.cli.parse_arguments")
    @patch("sly.cli.validate_arguments")
    @patch("sly.cli.SlideshowCreator")
    def test_main_general_exception(
        self, mock_creator_class, mock_validate, mock_parse
    ):
        """Test main function handles general exceptions gracefully."""
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_parse.return_value = mock_args
        mock_validate.return_value = True

        # Mock slideshow creator to raise general exception
        mock_creator = MagicMock()
        mock_creator.create_slideshow.side_effect = Exception("Test error")
        mock_creator_class.return_value = mock_creator

        # Should not raise exception
        main()
