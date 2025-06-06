# Sly - Beautiful Slideshow Creator

[![PyPI version](https://badge.fury.io/py/sly-slideshow.svg)](https://badge.fury.io/py/sly-slideshow)
[![Tests](https://github.com/yourusername/sly/workflows/Tests/badge.svg)](https://github.com/yourusername/sly/actions)
[![Coverage](https://codecov.io/gh/yourusername/sly/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/sly)

A powerful command-line tool for creating beautiful slideshows from images with transitions, titles, and soundtracks.

## Features

- 🖼️ **Multiple Image Formats**: Support for JPG, PNG, GIF, BMP, TIFF, WebP
- 🎬 **Smooth Transitions**: Professional crossfade transitions between images  
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

Create a slideshow from images in the current directory:

```bash
sly --path ./photos --output my_slideshow.mp4 --title "My Vacation"
```

## Usage

### Basic Usage

```bash
# Create slideshow from current directory
sly

# Specify image directory and output file
sly --path ./photos --output vacation.mp4

# Add a title slide
sly --path ./photos --title "Summer Vacation 2024"

# Add background music
sly --path ./photos --soundtrack music.mp3

# Custom duration and transitions
sly --path ./photos --image-duration 5 --transition-duration 2
```

### Advanced Options

```bash
sly --path ./photos \
    --output slideshow.mp4 \
    --title "My Photos" \
    --font ./fonts/arial.ttf \
    --font-size 72 \
    --image-duration 4.0 \
    --transition-duration 1.5 \
    --slideshow-width 1920 \
    --slideshow-height 1080 \
    --fps 30 \
    --image-order random \
    --soundtrack background.mp3 \
    --verbose
```

### Configuration File

Create a `config.toml` file for default settings:

```toml
# Default slideshow settings
image-duration = 3.0
transition-duration = 1.0
slideshow-width = 1920
slideshow-height = 1080
fps = 24.0
image-order = "name"
output = "slideshow.mp4"

# Optional defaults
title = "My Slideshow"
font-size = 72
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Path to images directory | `.` |
| `--output` | `-o` | Output video filename | `slideshow.mp4` |
| `--title` | `-t` | Title for the slideshow | None |
| `--font` | `-f` | Path to .ttf font file | System default |
| `--font-size` | `-fs` | Font size for title | Auto-calculated |
| `--image-duration` | `-id` | Duration per image (seconds) | `3.0` |
| `--transition-duration` | `-td` | Transition effect duration | `1.0` |
| `--slideshow-width` | `-sw` | Video width in pixels | `1920` |
| `--slideshow-height` | `-sh` | Video height in pixels | `1080` |
| `--fps` | `-fps` | Frames per second | `24.0` |
| `--image-order` | `-io` | Image order: `name`, `date`, `random` | `name` |
| `--soundtrack` | `-st` | Background audio file | None |
| `--config` | `-c` | Custom config file path | `config.toml` |
| `--verbose` | `-v` | Verbose output | `False` |

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
│   ├── image_utils.py     # Image processing utilities
│   ├── video_utils.py     # Video creation utilities
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

### 0.1.0
- Initial release
- Modular package structure
- Comprehensive test suite
- PyPI-ready packaging
- NixOS support
