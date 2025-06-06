"""Video creation utilities for sly slideshow creator."""

import traceback
from pathlib import Path
from typing import List, Optional
import numpy as np
from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip
from PIL import Image, ImageFont, ImageDraw
from rich.console import Console

from .image_utils import rotate_image, resize_and_crop

console = Console()


def create_title_slide(
    title: str,
    width: int,
    height: int,
    duration: float,
    font_path: Optional[str] = None,
    font_size: Optional[int] = None,
) -> ImageClip:
    """
    Create a title slide for the slideshow.

    Args:
        title (str): The title text to display on the slide.
        width (int): The width of the slide.
        height (int): The height of the slide.
        duration (float): The duration of the title slide in seconds.
        font_path (str, optional): Path to a custom font file. Defaults to None.
        font_size (int, optional): Font size for the title. Defaults to None (auto-calculated).

    Returns:
        ImageClip: A moviepy ImageClip object representing the title slide.
    """
    try:
        # Create a black background
        image = Image.new("RGB", (width, height), color="black")
        draw = ImageDraw.Draw(image)

        # Load font
        if font_size is None:
            font_size = min(width, height) // 10
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                console.print(
                    f"[red]Error loading font from {font_path}. Using default font.[/red]"
                )
                font = ImageFont.load_default()
        else:
            console.print("[blue]No font specified. Using default font.[/blue]")
            font = ImageFont.load_default()

        # Get text size
        left, top, right, bottom = draw.textbbox((0, 0), title, font=font)
        text_width = right - left
        text_height = bottom - top

        # Calculate position to center the text
        position = ((width - text_width) // 2, (height - text_height) // 2)

        # Draw text
        draw.text(position, title, font=font, fill="white")

        # Convert to ImageClip
        image_array = np.array(image)
        clip = ImageClip(image_array).set_duration(duration)

        # Add only a fade-in effect
        clip = clip.fadein(duration / 2)

        return clip
    except Exception as e:
        console.print(f"[red]Error in create_title_slide: {str(e)}[/red]")
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        raise


def process_images(
    image_files: List[Path], width: int, height: int, duration: float
) -> List[ImageClip]:
    """
    Process images by rotating, resizing, and converting them into ImageClips.

    Args:
        image_files (List[Path]): List of image file paths.
        width (int): Target width for resizing.
        height (int): Target height for resizing.
        duration (float): Duration for each image clip.

    Returns:
        List[ImageClip]: List of processed ImageClips.
    """
    processed_images = []
    for image_file in image_files:
        with Image.open(image_file) as img:
            img = rotate_image(img)
            img = resize_and_crop(img, width, height)
            processed_images.append(ImageClip(np.array(img)).set_duration(duration))
    return processed_images


def apply_transitions(
    clips: List[ImageClip],
    transition_duration: float,
    title_slide: Optional[ImageClip] = None,
) -> List[ImageClip]:
    """
    Apply transitions between clips and add a title slide if provided.

    Args:
        clips (List[ImageClip]): List of image clips.
        transition_duration (float): Duration of the transition effect.
        title_slide (ImageClip, optional): Title slide to add at the beginning.

    Returns:
        List[ImageClip]: List of clips with transitions applied.
    """
    final_clips = []
    if title_slide:
        black_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).set_duration(1)
        final_clips.extend(
            [
                black_clip,
                title_slide.fadein(transition_duration).fadeout(transition_duration),
                black_clip,
            ]
        )

        # Add a pause after the title slide fades to black
        pause_duration = 1  # Duration of the pause in seconds
        pause_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).set_duration(
            pause_duration
        )
        final_clips.append(pause_clip)

    for i, clip in enumerate(clips):
        if i == 0:
            # Ensure the first image slide fades in
            final_clips.append(clip.fadein(transition_duration))
        elif i == len(clips) - 1:
            if i > 0:
                transition = CompositeVideoClip(
                    [
                        clips[i - 1],
                        clip.set_start(
                            clip.duration - transition_duration
                        ).crossfadein(transition_duration),
                    ]
                ).set_duration(clip.duration)
                final_clips.append(transition)
            final_clips.append(clip.fadeout(transition_duration))
        else:
            transition = CompositeVideoClip(
                [
                    clips[i - 1],
                    clip.set_start(clip.duration - transition_duration).crossfadein(
                        transition_duration
                    ),
                ]
            ).set_duration(clip.duration)
            final_clips.append(transition)
            final_clips.append(clip.set_duration(clip.duration - transition_duration))
    return final_clips
