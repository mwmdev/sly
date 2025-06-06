"""
Sly - A powerful slideshow creation tool

Create beautiful slideshows from images with transitions, titles, and soundtracks.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .slideshow import SlideshowCreator
from .config import load_config_file
from .image_utils import get_image_files, rotate_image, resize_and_crop
from .video_utils import create_title_slide, apply_transitions, process_images

__all__ = [
    "SlideshowCreator",
    "load_config_file",
    "get_image_files",
    "rotate_image",
    "resize_and_crop",
    "create_title_slide",
    "apply_transitions",
    "process_images",
]
