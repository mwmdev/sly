"""Unit tests for sly.config module."""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from sly.config import load_config_file, get_config_path


class TestLoadConfigFile:
    """Test cases for load_config_file function."""

    def test_load_valid_config_file(self):
        """Test loading a valid TOML config file."""
        config_content = """
        image-duration = 5.0
        slideshow-width = 1280
        slideshow-height = 720
        """

        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("toml.load") as mock_toml_load:
                mock_toml_load.return_value = {
                    "image-duration": 5.0,
                    "slideshow-width": 1280,
                    "slideshow-height": 720,
                }

                result = load_config_file("test_config.toml")

                assert result["image-duration"] == 5.0
                assert result["slideshow-width"] == 1280
                assert result["slideshow-height"] == 720

    def test_load_nonexistent_config_file(self):
        """Test loading a non-existent config file returns empty dict."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = load_config_file("nonexistent.toml")
            assert result == {}

    def test_load_invalid_config_file(self):
        """Test loading an invalid TOML file returns empty dict."""
        with patch("builtins.open", mock_open(read_data="invalid toml content")):
            with patch("toml.load", side_effect=Exception("Invalid TOML")):
                result = load_config_file("invalid.toml")
                assert result == {}


class TestGetConfigPath:
    """Test cases for get_config_path function."""

    def test_custom_path_exists(self):
        """Test that custom path is returned when it exists."""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            result = get_config_path(temp_path)
            assert result == temp_path
        finally:
            os.unlink(temp_path)

    def test_custom_path_not_exists(self):
        """Test fallback when custom path doesn't exist."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "config.toml"

            result = get_config_path("nonexistent.toml")
            assert result == "config.toml"

    def test_default_config_exists(self):
        """Test that default config.toml is returned when it exists."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "config.toml"

            result = get_config_path()
            assert result == "config.toml"

    def test_user_config_exists(self):
        """Test that user config is returned when default doesn't exist."""
        user_config_path = os.path.expanduser("~/.config/sly/config.toml")

        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == user_config_path

            result = get_config_path()
            assert result == user_config_path

    def test_no_config_exists(self):
        """Test that default path is returned when no config exists."""
        with patch("os.path.exists", return_value=False):
            result = get_config_path()
            assert result == "config.toml"
