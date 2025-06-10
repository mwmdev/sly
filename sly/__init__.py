"""
Sly - A powerful slideshow creation tool

Create beautiful slideshows from images and videos with transitions, titles, and soundtracks.
"""

__version__ = "0.2.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .slideshow import SlideshowCreator
from .config import load_config_file
from .image_utils import get_image_files, get_media_files, rotate_image, resize_and_crop, is_video_file, is_image_file
from .video_utils import create_title_slide, apply_transitions, process_images, process_media_files

__all__ = [
    "SlideshowCreator",
    "load_config_file",
    "get_image_files",
    "get_media_files",
    "rotate_image",
    "resize_and_crop",
    "is_video_file",
    "is_image_file",
    "create_title_slide",
    "apply_transitions",
    "process_images",
    "process_media_files",
]
