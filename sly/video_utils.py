"""Video creation utilities for sly slideshow creator."""

import traceback
from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from moviepy.editor import ImageClip, VideoFileClip, CompositeVideoClip, ColorClip  # type: ignore
from PIL import Image, ImageFont, ImageDraw
from PIL.ImageFont import FreeTypeFont
from rich.console import Console

from .image_utils import rotate_image, resize_and_crop, is_video_file, is_image_file

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
        font: Union[FreeTypeFont, ImageFont.ImageFont]
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


def process_media_files(
    media_files: List[Path], 
    width: int, 
    height: int, 
    image_duration: float,
    video_duration_mode: str = "original"
) -> List[Union[ImageClip, VideoFileClip]]:
    """
    Process media files (images and videos) by resizing and converting them into clips.

    Args:
        media_files (List[Path]): List of media file paths.
        width (int): Target width for resizing.
        height (int): Target height for resizing.
        image_duration (float): Duration for each image clip.
        video_duration_mode (str): How to handle video durations:
            - "original": Use original video duration
            - "fixed": Use image_duration for all videos
            - "limit": Cap videos at image_duration * 3

    Returns:
        List[Union[ImageClip, VideoFileClip]]: List of processed clips.
    """
    processed_clips = []
    
    for media_file in media_files:
        try:
            if is_video_file(media_file):
                # Process video file
                video_clip = VideoFileClip(str(media_file))
                
                # Resize video to target dimensions while maintaining aspect ratio
                video_clip = video_clip.resize(height=height).resize(width=width)
                
                # Handle video duration based on mode
                if video_duration_mode == "fixed":
                    video_clip = video_clip.set_duration(image_duration)
                elif video_duration_mode == "limit":
                    max_duration = image_duration * 3
                    if video_clip.duration > max_duration:
                        video_clip = video_clip.subclip(0, max_duration)
                # For "original" mode, keep the original duration
                
                processed_clips.append(video_clip)
                console.print(f"[green]Processed video: {media_file.name} ({video_clip.duration:.1f}s)[/green]")
                
            elif is_image_file(media_file):
                # Process image file (existing logic)
                with Image.open(media_file) as img:
                    img = rotate_image(img)
                    img = resize_and_crop(img, width, height)
                    image_clip = ImageClip(np.array(img)).set_duration(image_duration)
                    processed_clips.append(image_clip)
                    console.print(f"[blue]Processed image: {media_file.name}[/blue]")
            else:
                console.print(f"[yellow]Skipping unsupported file: {media_file.name}[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error processing {media_file.name}: {str(e)}[/red]")
            continue
            
    return processed_clips


def process_images(
    image_files: List[Path], width: int, height: int, duration: float
) -> List[ImageClip]:
    """
    Process images by rotating, resizing, and converting them into ImageClips.
    Kept for backward compatibility.

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
    clips: List[Union[ImageClip, VideoFileClip]],
    transition_duration: float,
    title_slide: Optional[ImageClip] = None,
) -> List[Union[ImageClip, VideoFileClip, ColorClip]]:
    """
    Apply basic fade effects to clips and add title slide if provided.
    
    This approach applies simple fade-in/fade-out effects and prepares clips
    for crossfade transitions to be handled during concatenation.

    Args:
        clips (List[Union[ImageClip, VideoFileClip]]): List of media clips.
        transition_duration (float): Duration of the transition effect.
        title_slide (ImageClip, optional): Title slide to add at the beginning.

    Returns:
        List[Union[ImageClip, VideoFileClip, ColorClip]]: List of clips prepared for concatenation.
    """
    if not clips:
        return []
        
    final_clips = []
    
    # Add title slide if provided
    if title_slide:
        black_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).set_duration(0.5)
        final_clips.append(black_clip)
        final_clips.append(title_slide.fadein(transition_duration).fadeout(transition_duration))
        
        # Add a brief pause after the title slide
        pause_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).set_duration(0.5)
        final_clips.append(pause_clip)

    # Process each clip - just add them as-is, transitions will be handled during concatenation
    for clip in clips:
        final_clips.append(clip)
    
    return final_clips
