# sly: CLI Slideshow Generator

`sly` is a lightweight and flexible command-line tool for creating slideshows from your image collections. With support for tansition effect, soundtrack, and title slide, `sly` makes it easy to quickly turn your photos into nice-looking videos.

## Features

- Create slideshows from a folder of images
- Customize image duration and transition effects
- Add background music to your slideshow
- Include a title slide with custom fonts
- Support for various image ordering options (by name, date, or random)
- Adjustable output resolution and frame rate
- Progress bar for real-time rendering updates

## Installation

### Prerequisites

- Python 3.7+
- FFmpeg


### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mwmdev/sly.git
   cd sly
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Using Nix

If you're using NixOS or have Nix package manager installed, you can use the provided `shell.nix` file to set up the environment.

## Usage

Basic usage:

```bash
python sly.py --path ./path/to/images --output ./path/to/output.mp4
```

### Options

- `--path`, `-p`: Path to the images directory (default: current directory)
- `--image-duration`, `-id`: The number of seconds each image will be displayed (default: 5)
- `--image-order`, `-io`: Order of images (choices: name, date, random; default: date)
- `--transition-duration`, `-td`: The number of seconds the transition effect will take to complete (default: 2)
- `--slideshow-width`, `-sw`: The width of the slideshow in pixels (default: 1920)
- `--slideshow-height`, `-sh`: The height of the slideshow in pixels (default: 1080)
- `--output`, `-o`: The name of the output file (default: slideshow.mp4)
- `--title`: The title of the slideshow (optional)
- `--font`: Path to a .ttf font file for the title (optional)
- `--soundtrack`, `-st`: The path to the audio file for the soundtrack (optional)
- `--fps`: The number of frames per second for the output video (default: 24.0)

### Examples

1. Create a slideshow with default settings:
   ```bash
   python sly.py --path /path/to/vacation/photos
   ```

2. Create a slideshow with custom duration and random order:
   ```bash
   python sly.py --path /path/to/photos --image-duration 3 --image-order random
   ```

3. Create a slideshow with a title and a custom font:
   ```bash
   python sly.py --path /path/to/photos --title "Summer Vacation 2023" --font /path/to/font.ttf
   ```

4. Create a high-resolution slideshow with custom FPS:
   ```bash
   python sly.py --path /path/to/photos --slideshow-width 3840 --slideshow-height 2160 --fps 30
   ```

5. Create a slideshow with a soundtrack:
   ```bash
   python sly.py --path /path/to/photos --soundtrack /path/to/soundtrack.mp3
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [MoviePy](https://zulko.github.io/moviepy/) for video editing capabilities
- [Pillow](https://python-pillow.org/) for image processing
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## Support

If you encounter any problems or have any suggestions, please open an issue on the GitHub repository.

---

Happy slideshow creating with sly! 📸 🎞️
