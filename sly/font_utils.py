"""Font utilities for discovering and listing system fonts."""

import os
import platform
from pathlib import Path
from typing import List, Dict, Set
import glob

from rich.console import Console
from rich.table import Table


def get_system_font_paths() -> List[str]:
    """
    Get font paths for the current operating system.
    
    Returns:
        List[str]: List of font directory paths for the current system
    """
    system = platform.system().lower()
    font_paths = []
    
    if system == "windows":
        # Windows font paths
        font_paths.extend([
            "C:/Windows/Fonts/",
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/"),
        ])
    elif system == "darwin":  # macOS
        # macOS font paths
        font_paths.extend([
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/"),
        ])
    else:  # Linux, NixOS, and other Unix-like systems
        # Standard Linux font paths
        font_paths.extend([
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            "/usr/share/fonts/truetype/",
            "/usr/share/fonts/opentype/",
            "/usr/local/share/fonts/truetype/",
            "/usr/local/share/fonts/opentype/",
            os.path.expanduser("~/.fonts/"),  # Legacy
            os.path.expanduser("~/.local/share/fonts/"),  # Modern
        ])
        
        # NixOS-specific paths
        if os.path.exists("/etc/NIXOS"):
            font_paths.extend([
                "/run/current-system/sw/share/fonts/",
                "/nix/var/nix/profiles/system/sw/share/fonts/",
            ])
        
        # Flatpak fonts (common on modern Linux)
        flatpak_fonts = os.path.expanduser("~/.local/share/flatpak/exports/share/fonts/")
        if os.path.exists(flatpak_fonts):
            font_paths.append(flatpak_fonts)
    
    # Filter out paths that don't exist
    return [path for path in font_paths if os.path.exists(path)]


def find_fonts_in_directory(directory: str) -> List[Dict[str, str]]:
    """
    Find all font files in a directory and its subdirectories.
    
    Args:
        directory: Directory path to search for fonts
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with font name and path
    """
    fonts = []
    font_extensions = {'.ttf', '.otf', '.woff', '.woff2', '.eot', '.pfb', '.pfm', '.ttc'}
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in font_extensions):
                    font_path = os.path.join(root, file)
                    font_name = os.path.splitext(file)[0]
                    fonts.append({
                        'name': font_name,
                        'path': font_path,
                        'extension': os.path.splitext(file)[1].lower()
                    })
    except (PermissionError, OSError):
        # Skip directories we can't access
        pass
    
    return fonts


def discover_system_fonts() -> List[Dict[str, str]]:
    """
    Discover all fonts available on the system.
    
    Returns:
        List[Dict[str, str]]: List of font dictionaries with name, path, and extension
    """
    all_fonts = []
    font_paths = get_system_font_paths()
    
    for path in font_paths:
        fonts_in_path = find_fonts_in_directory(path)
        all_fonts.extend(fonts_in_path)
    
    # Remove duplicates based on font name (keep first occurrence)
    seen_names = set()
    unique_fonts = []
    
    for font in all_fonts:
        if font['name'] not in seen_names:
            seen_names.add(font['name'])
            unique_fonts.append(font)
    
    # Sort by font name
    return sorted(unique_fonts, key=lambda x: x['name'].lower())


def list_fonts() -> None:
    """
    List all available system fonts in a formatted table.
    """
    console = Console()
    
    console.print("[blue]Discovering system fonts...[/blue]")
    fonts = discover_system_fonts()
    
    if not fonts:
        console.print("[yellow]No fonts found on this system.[/yellow]")
        return
    
    # Create table
    table = Table(title="Available System Fonts")
    table.add_column("Font Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Path", style="green")
    
    for font in fonts:
        # Get font type from extension
        font_type = {
            '.ttf': 'TrueType',
            '.otf': 'OpenType', 
            '.woff': 'Web Font',
            '.woff2': 'Web Font 2',
            '.eot': 'Embedded OpenType',
            '.pfb': 'PostScript',
            '.pfm': 'PostScript',
            '.ttc': 'TrueType Collection'
        }.get(font['extension'], 'Unknown')
        
        table.add_row(
            font['name'],
            font_type,
            font['path']
        )
    
    console.print(table)
    console.print(f"\n[green]Found {len(fonts)} unique fonts[/green]")


def find_font_by_name(font_name: str) -> str:
    """
    Find a font file by name (case-insensitive).
    
    Args:
        font_name: Name of the font to find
        
    Returns:
        str: Path to the font file if found, empty string otherwise
    """
    fonts = discover_system_fonts()
    
    for font in fonts:
        if font['name'].lower() == font_name.lower():
            return font['path']
    
    return ""


def get_font_suggestions(partial_name: str, limit: int = 5) -> List[str]:
    """
    Get font name suggestions based on partial match.
    
    Args:
        partial_name: Partial font name to match
        limit: Maximum number of suggestions to return
        
    Returns:
        List[str]: List of font names that partially match
    """
    fonts = discover_system_fonts()
    suggestions = []
    
    partial_lower = partial_name.lower()
    
    for font in fonts:
        if partial_lower in font['name'].lower():
            suggestions.append(font['name'])
            if len(suggestions) >= limit:
                break
    
    return suggestions 