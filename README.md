# Sly - Beautiful Slideshow Creator

[![PyPI version](https://badge.fury.io/py/sly-slideshow.svg)](https://badge.fury.io/py/sly-slideshow)
[![Tests](https://github.com/yourusername/sly/workflows/Tests/badge.svg)](https://github.com/yourusername/sly/actions)
[![Coverage](https://codecov.io/gh/yourusername/sly/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/sly)

A powerful command-line tool for creating beautiful slideshows from images and videos with transitions, titles, and soundtracks.

## Features

- 🖼️ **Multiple Media Formats**: Support for images (JPG, PNG, GIF, BMP, TIFF, WebP) and videos (MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V, 3GP, MPG, MPEG)
- 🎬 **Multiple Transition Types**: Choose between crossfade (smooth overlap) and fade (fade to black) transitions
- 🎥 **Mixed Media Support**: Seamlessly combine images and videos in the same slideshow
- ⏱️ **Flexible Video Duration**: Control how video lengths are handled (original, fixed, or limited duration)
- 📝 **Title Slides**: Add custom titles with font support
- 🎵 **Soundtrack Support**: Add background music to your slideshows
- ⚙️ **Configurable**: Extensive customization via config files or CLI
- 🚀 **Fast Processing**: Multi-threaded video rendering
- 📐 **Auto Orientation**: Automatic image rotation based on EXIF data
- 🎨 **Smart Cropping**: Intelligent resizing while maintaining aspect ratios

## Installation

### From PyPI (Recommended)

```bash
pip install sly-slideshow
```

### From Source

```bash
git clone https://github.com/yourusername/sly
cd sly
pip install -e .
```

### For NixOS Users

```bash
nix-shell
pip install -e .
```

## Quick Start

Create a slideshow from images and videos in the current directory:

```bash
sly --path ./media --output my_slideshow.mp4 --title "My Vacation"
```

## Usage

### Basic Usage

```bash
# Create slideshow from current directory (includes both images and videos)
sly

# Specify media directory and output file
sly --path ./media --output vacation.mp4

# Add a title slide
sly --path ./media --title "Summer Vacation 2024"

# Add background music
sly --path ./media --soundtrack music.mp3

# Custom duration and transitions
sly --path ./media --image-duration 5 --transition-duration 2 --transition-type crossfade
```

### Working with Videos

```bash
# Use original video durations (default)
sly --path ./media --video-duration-mode original

# Make all videos use the same duration as images
sly --path ./media --video-duration-mode fixed --image-duration 4

# Limit long videos to 3x the image duration
sly --path ./media --video-duration-mode limit --image-duration 3

# Process only images (ignore videos)
sly --path ./media --images-only
```

### Transition Types

```bash
# Smooth crossfade transitions (default)
sly --path ./media --transition-type crossfade --transition-duration 1.5

# Fade to black transitions
sly --path ./media --transition-type fade --transition-duration 1.0
```

### Font Management

```bash
# List all available system fonts
sly --list-fonts

# Use a specific font for titles
sly --path ./photos --title "My Vacation" --font "Arial"
```

### Advanced Options

```bash
sly --path ./media \
    --output slideshow.mp4 \
    --title "My Media Collection" \
    --font ./fonts/arial.ttf \
    --font-size 72 \
    --image-duration 4.0 \
    --transition-duration 1.5 \
    --transition-type crossfade \
    --video-duration-mode original \
    --slideshow-width 1920 \
    --slideshow-height 1080 \
    --fps 30 \
    --image-order random \
    --soundtrack background.mp3 \
    --include-videos \
    --verbose
```

### Configuration File

Create a `config.toml` file for default settings:

```toml
# Default slideshow settings
image-duration = 3.0
transition-duration = 1.0
transition-type = "crossfade"
slideshow-width = 1920
slideshow-height = 1080
fps = 24.0
image-order = "name"
output = "slideshow.mp4"

# Video settings
video-duration-mode = "original"
include-videos = true

# Optional defaults
title = "My Slideshow"
font-size = 72
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Path to media directory (images/videos) | `.` |
| `--output` | `-o` | Output video filename | `slideshow.mp4` |
| `--title` | `-t` | Title for the slideshow | None |
| `--font` | `-f` | Path to .ttf font file | System default |
| `--font-size` | `-fs` | Font size for title | Auto-calculated |
| `--image-duration` | `-id` | Duration per image (seconds) | `3.0` |
| `--transition-duration` | `-td` | Transition effect duration | `1.0` |
| `--transition-type` | `-tt` | Transition type: `fade`, `crossfade` | `crossfade` |
| `--video-duration-mode` | `-vdm` | Video duration: `original`, `fixed`, `limit` | `original` |
| `--include-videos` | `-iv` | Include video files in slideshow | `True` |
| `--images-only` | `-imo` | Process only images, ignore videos | `False` |
| `--slideshow-width` | `-sw` | Video width in pixels | `1920` |
| `--slideshow-height` | `-sh` | Video height in pixels | `1080` |
| `--fps` | `-fps` | Frames per second | `24.0` |
| `--image-order` | `-io` | Media order: `name`, `date`, `random` | `name` |
| `--soundtrack` | `-st` | Background audio file | None |
| `--config` | `-c` | Custom config file path | `config.toml` |
| `--verbose` | `-v` | Verbose output | `False` |
| `--list-fonts` | `-lf` | List all available system fonts | N/A |

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/sly
cd sly

# For NixOS users
nix-shell

# For other systems, create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sly --cov-report=html

# Run specific test file
pytest tests/test_image_utils.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy sly
```

### Package Structure

```
sly/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── LICENSE                 # MIT license
├── shell.nix              # NixOS development environment
├── sly/                   # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration handling
│   ├── image_utils.py     # Media file detection and image processing
│   ├── video_utils.py     # Video/media processing and transitions
│   ├── slideshow.py       # Main slideshow orchestration
│   └── utils.py           # General utilities
└── tests/                 # Test suite
    ├── __init__.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_image_utils.py
    └── test_*.py
```

## Publishing to PyPI

### Build and Upload

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

### Version Management

Update version in `pyproject.toml` and `sly/__init__.py` before building.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format your code (`black .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Requirements

- Python 3.8+
- FFmpeg (for video processing)
- See `pyproject.toml` for Python dependencies

## Changelog

### 0.2.0 (Current)
- **Video Support**: Full support for video files (MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V, 3GP, MPG, MPEG)
- **Mixed Media**: Seamlessly combine images and videos in the same slideshow
- **Multiple Transition Types**: Choose between crossfade (smooth overlap) and fade (fade to black) transitions
- **Flexible Video Duration**: Control video lengths with original, fixed, or limited duration modes
- **Enhanced CLI**: New options for video handling and transition types
- **Improved Error Handling**: Better fallback mechanisms for video processing
- **Updated Documentation**: Comprehensive examples for mixed media workflows

### 0.1.0
- Initial release
- Modular package structure
- Comprehensive test suite
- PyPI-ready packaging
- NixOS support
