"""Unit tests for sly.font_utils module."""

import os
import platform
import pytest
from unittest.mock import patch, MagicMock

from sly.font_utils import (
    get_system_font_paths,
    find_fonts_in_directory,
    discover_system_fonts,
    find_font_by_name,
    get_font_suggestions,
    list_fonts
)


class TestGetSystemFontPaths:
    """Test cases for get_system_font_paths function."""

    @patch('platform.system')
    @patch('os.path.exists')
    def test_windows_font_paths(self, mock_exists, mock_system):
        """Test Windows font paths are returned correctly."""
        mock_system.return_value = "Windows"
        mock_exists.return_value = True
        
        paths = get_system_font_paths()
        
        assert "C:/Windows/Fonts/" in paths
        assert any("AppData/Local/Microsoft/Windows/Fonts/" in path for path in paths)

    @patch('platform.system')
    @patch('os.path.exists')
    def test_macos_font_paths(self, mock_exists, mock_system):
        """Test macOS font paths are returned correctly."""
        mock_system.return_value = "Darwin"
        mock_exists.return_value = True
        
        paths = get_system_font_paths()
        
        assert "/System/Library/Fonts/" in paths
        assert "/Library/Fonts/" in paths

    @patch('platform.system')
    @patch('os.path.exists')
    def test_linux_font_paths(self, mock_exists, mock_system):
        """Test Linux font paths are returned correctly."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = True
        
        paths = get_system_font_paths()
        
        assert "/usr/share/fonts/" in paths
        assert "/usr/local/share/fonts/" in paths

    @patch('platform.system')
    @patch('os.path.exists')
    def test_nixos_font_paths(self, mock_exists, mock_system):
        """Test NixOS-specific font paths are included."""
        mock_system.return_value = "Linux"
        
        def mock_exists_side_effect(path):
            if path == "/etc/NIXOS":
                return True
            return path in ["/usr/share/fonts/", "/run/current-system/sw/share/fonts/"]
        
        mock_exists.side_effect = mock_exists_side_effect
        
        paths = get_system_font_paths()
        
        assert "/run/current-system/sw/share/fonts/" in paths

    @patch('platform.system')
    @patch('os.path.exists')
    def test_nonexistent_paths_filtered(self, mock_exists, mock_system):
        """Test that non-existent paths are filtered out."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = False
        
        paths = get_system_font_paths()
        
        assert len(paths) == 0


class TestFindFontsInDirectory:
    """Test cases for find_fonts_in_directory function."""

    @patch('os.walk')
    def test_find_fonts_basic(self, mock_walk):
        """Test finding fonts in a directory."""
        mock_walk.return_value = [
            ('/test/fonts', [], ['Arial.ttf', 'Times.otf', 'readme.txt'])
        ]
        
        fonts = find_fonts_in_directory('/test/fonts')
        
        assert len(fonts) == 2
        assert fonts[0]['name'] == 'Arial'
        assert fonts[0]['extension'] == '.ttf'
        assert fonts[1]['name'] == 'Times'
        assert fonts[1]['extension'] == '.otf'

    @patch('os.walk')
    def test_find_fonts_subdirectories(self, mock_walk):
        """Test finding fonts in subdirectories."""
        mock_walk.return_value = [
            ('/test/fonts', ['truetype'], []),
            ('/test/fonts/truetype', [], ['Comic.ttf'])
        ]
        
        fonts = find_fonts_in_directory('/test/fonts')
        
        assert len(fonts) == 1
        assert fonts[0]['name'] == 'Comic'

    @patch('os.walk')
    def test_find_fonts_various_extensions(self, mock_walk):
        """Test finding fonts with various extensions."""
        mock_walk.return_value = [
            ('/test/fonts', [], ['font1.ttf', 'font2.otf', 'font3.woff', 'font4.ttc'])
        ]
        
        fonts = find_fonts_in_directory('/test/fonts')
        
        assert len(fonts) == 4
        extensions = [font['extension'] for font in fonts]
        assert '.ttf' in extensions
        assert '.otf' in extensions
        assert '.woff' in extensions
        assert '.ttc' in extensions

    @patch('os.walk')
    def test_find_fonts_permission_error(self, mock_walk):
        """Test handling permission errors gracefully."""
        mock_walk.side_effect = PermissionError("Access denied")
        
        fonts = find_fonts_in_directory('/restricted/fonts')
        
        assert len(fonts) == 0


class TestDiscoverSystemFonts:
    """Test cases for discover_system_fonts function."""

    @patch('sly.font_utils.get_system_font_paths')
    @patch('sly.font_utils.find_fonts_in_directory')
    def test_discover_fonts_basic(self, mock_find_fonts, mock_get_paths):
        """Test basic font discovery."""
        mock_get_paths.return_value = ['/test/fonts1', '/test/fonts2']
        mock_find_fonts.side_effect = [
            [{'name': 'Arial', 'path': '/test/fonts1/Arial.ttf', 'extension': '.ttf'}],
            [{'name': 'Times', 'path': '/test/fonts2/Times.otf', 'extension': '.otf'}]
        ]
        
        fonts = discover_system_fonts()
        
        assert len(fonts) == 2
        assert fonts[0]['name'] == 'Arial'
        assert fonts[1]['name'] == 'Times'

    @patch('sly.font_utils.get_system_font_paths')
    @patch('sly.font_utils.find_fonts_in_directory')
    def test_discover_fonts_remove_duplicates(self, mock_find_fonts, mock_get_paths):
        """Test that duplicate font names are removed."""
        mock_get_paths.return_value = ['/test/fonts1', '/test/fonts2']
        mock_find_fonts.side_effect = [
            [{'name': 'Arial', 'path': '/test/fonts1/Arial.ttf', 'extension': '.ttf'}],
            [{'name': 'Arial', 'path': '/test/fonts2/Arial.otf', 'extension': '.otf'}]
        ]
        
        fonts = discover_system_fonts()
        
        assert len(fonts) == 1
        assert fonts[0]['name'] == 'Arial'
        assert fonts[0]['path'] == '/test/fonts1/Arial.ttf'  # First occurrence kept


class TestFindFontByName:
    """Test cases for find_font_by_name function."""

    @patch('sly.font_utils.discover_system_fonts')
    def test_find_font_exact_match(self, mock_discover):
        """Test finding font by exact name match."""
        mock_discover.return_value = [
            {'name': 'Arial', 'path': '/fonts/Arial.ttf', 'extension': '.ttf'},
            {'name': 'Times', 'path': '/fonts/Times.otf', 'extension': '.otf'}
        ]
        
        path = find_font_by_name('Arial')
        
        assert path == '/fonts/Arial.ttf'

    @patch('sly.font_utils.discover_system_fonts')
    def test_find_font_case_insensitive(self, mock_discover):
        """Test finding font with case-insensitive matching."""
        mock_discover.return_value = [
            {'name': 'Arial', 'path': '/fonts/Arial.ttf', 'extension': '.ttf'}
        ]
        
        path = find_font_by_name('arial')
        
        assert path == '/fonts/Arial.ttf'

    @patch('sly.font_utils.discover_system_fonts')
    def test_find_font_not_found(self, mock_discover):
        """Test behavior when font is not found."""
        mock_discover.return_value = [
            {'name': 'Arial', 'path': '/fonts/Arial.ttf', 'extension': '.ttf'}
        ]
        
        path = find_font_by_name('NonExistent')
        
        assert path == ""


class TestGetFontSuggestions:
    """Test cases for get_font_suggestions function."""

    @patch('sly.font_utils.discover_system_fonts')
    def test_get_suggestions_partial_match(self, mock_discover):
        """Test getting font suggestions for partial name match."""
        mock_discover.return_value = [
            {'name': 'Arial', 'path': '/fonts/Arial.ttf', 'extension': '.ttf'},
            {'name': 'Arial Black', 'path': '/fonts/ArialBlack.ttf', 'extension': '.ttf'},
            {'name': 'Times', 'path': '/fonts/Times.otf', 'extension': '.otf'}
        ]
        
        suggestions = get_font_suggestions('Ari')
        
        assert len(suggestions) == 2
        assert 'Arial' in suggestions
        assert 'Arial Black' in suggestions

    @patch('sly.font_utils.discover_system_fonts')
    def test_get_suggestions_limit(self, mock_discover):
        """Test that suggestion limit is respected."""
        mock_discover.return_value = [
            {'name': f'Font{i}', 'path': f'/fonts/Font{i}.ttf', 'extension': '.ttf'}
            for i in range(10)
        ]
        
        suggestions = get_font_suggestions('Font', limit=3)
        
        assert len(suggestions) == 3


class TestListFonts:
    """Test cases for list_fonts function."""

    @patch('sly.font_utils.discover_system_fonts')
    def test_list_fonts_with_fonts(self, mock_discover):
        """Test listing fonts when fonts are available."""
        mock_discover.return_value = [
            {'name': 'Arial', 'path': '/fonts/Arial.ttf', 'extension': '.ttf'}
        ]
        
        # Test that the function runs without error
        list_fonts()
        
        # Verify discover_system_fonts was called
        mock_discover.assert_called_once()

    @patch('sly.font_utils.discover_system_fonts')
    def test_list_fonts_no_fonts(self, mock_discover):
        """Test listing fonts when no fonts are available."""
        mock_discover.return_value = []
        
        # Test that the function runs without error
        list_fonts()
        
        # Verify discover_system_fonts was called
        mock_discover.assert_called_once() 