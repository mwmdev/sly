"""Image processing utilities for sly slideshow creator."""

import random
from pathlib import Path
from typing import List
from PIL import Image


def get_image_files(path: str, order: str) -> List[Path]:
    """
    Get a list of image files from the specified path, ordered as requested.

    Args:
        path (str): The directory path containing the images.
        order (str): The order to sort the images ("name", "date", or "random").

    Returns:
        List[Path]: A list of Path objects representing the image files.

    Raises:
        FileNotFoundError: If no image files are found in the specified directory.
    """
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".jpg_",
        ".tiff",
        ".tif",
        ".webp",
    }
    image_files = [
        f for f in Path(path).iterdir() if f.suffix.lower() in image_extensions
    ]

    if not image_files:
        raise FileNotFoundError(
            f"No image files found in the specified directory: {path}"
        )

    if order == "name":
        image_files.sort(key=lambda x: x.name)
    elif order == "date":
        image_files.sort(key=lambda x: x.stat().st_mtime)
    elif order == "random":
        random.shuffle(image_files)

    return image_files


def rotate_image(image: Image.Image) -> Image.Image:
    """
    Rotate the image based on its EXIF orientation data.

    Args:
        image (Image.Image): The input image.

    Returns:
        Image.Image: The rotated image.
    """
    try:
        exif = image.getexif()
        if exif is not None:
            orientation = exif.get(0x0112)  # Orientation tag
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError, TypeError):
        # No EXIF data or no orientation info
        pass
    return image


def resize_and_crop(
    image: Image.Image, target_width: int, target_height: int
) -> Image.Image:
    """
    Resize and crop the image to fit the target dimensions while maintaining aspect ratio.

    Args:
        image (Image.Image): The input image.
        target_width (int): The desired width of the output image.
        target_height (int): The desired height of the output image.

    Returns:
        Image.Image: The resized and cropped image.
    """
    img_ratio = image.width / image.height
    target_ratio = target_width / target_height

    if target_ratio > img_ratio:
        # Crop height
        new_height = int(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    else:
        # Crop width
        new_width = int(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))

    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
