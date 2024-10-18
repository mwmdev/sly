import argparse
import random
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np
from moviepy.editor import concatenate_videoclips, ImageClip, CompositeVideoClip, AudioFileClip, ColorClip
import traceback
from PIL import Image, ExifTags, ImageFont, ImageDraw
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, Spinner, BarColumn, TimeElapsedColumn
from rich.live import Live
import re
import os
import multiprocessing
import time

import logging
from venv import logger

logging.basicConfig(level=logging.ERROR)  # Only show error messages

console = Console()

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the slideshow creation script.

    Returns:
        argparse.Namespace: An object containing all the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Create a slideshow from a folder of images")
    parser.add_argument("--path", "-p", type=str, default=".", help="Path to the images directory")
    parser.add_argument("--image-duration", "-id", type=float, default=5, help="Duration of each image in seconds")
    parser.add_argument("--image-order", "-io", type=str, default="date", choices=["name", "date", "random"],
                        help="Order of images")
    parser.add_argument("--transition-duration", "-td", type=float, default=2,
                        help="Duration of transition effect in seconds")
    parser.add_argument("--slideshow-width", "-sw", type=int, default=1920, help="Width of the slideshow in pixels")
    parser.add_argument("--slideshow-height", "-sh", type=int, default=1080, help="Height of the slideshow in pixels")
    parser.add_argument("--output", "-o", type=str, default="slideshow.mp4", help="Output file name")
    parser.add_argument("--title", type=str, default="", help="Title of the slideshow")
    parser.add_argument("--font", type=str, default=None, help="Path to a .ttf font file for the title")
    parser.add_argument("--soundtrack", "-st", type=str, default="", help="Audio file for soundtrack")
    parser.add_argument("--fps", type=float, default=24.0, help="Frames per second for the output video")
    return parser.parse_args()

def get_image_files(path: str, order: str) -> List[Path]:
    """
    Get a list of image files from the specified path, ordered as requested.

    Args:
        path (str): The directory path containing the images.
        order (str): The order to sort the images ("name", "date", or "random").

    Returns:
        List[Path]: A list of Path objects representing the image files.
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".jpg_"}
    image_files = [f for f in Path(path).iterdir() if f.suffix.lower() in image_extensions]

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
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # No EXIF data or no orientation info
        pass
    return image

def resize_and_crop(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
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

    return image.resize((target_width, target_height), Image.LANCZOS)

def create_title_slide(title: str, width: int, height: int, duration: float, font_path: str = None) -> ImageClip:
    """
    Create a title slide for the slideshow.

    Args:
        title (str): The title text to display on the slide.
        width (int): The width of the slide.
        height (int): The height of the slide.
        duration (float): The duration of the title slide in seconds.
        font_path (str, optional): Path to a custom font file. Defaults to None.

    Returns:
        ImageClip: A moviepy ImageClip object representing the title slide.
    """
    try:
        # Create a black background
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)

        # Load font
        font_size = min(width, height) // 10
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                console.print(f"[red]Error loading font from {font_path}. Using default font.[/red]")
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
        draw.text(position, title, font=font, fill='white')

        # Convert to ImageClip
        image_array = np.array(image)
        clip = ImageClip(image_array).with_duration(duration)  # Changed from set_duration to with_duration

        # Add only a fade-in effect
        clip = clip.fadein(duration/2)

        return clip
    except Exception as e:
        console.print(f"[red]Error in create_title_slide: {str(e)}[/red]")
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        raise

class CustomProgressBar:
    """
    A custom progress bar class for tracking and displaying the progress of video rendering.
    """
    def __init__(self, rich_progress, rich_task):
        self.rich_progress = rich_progress
        self.rich_task = rich_task
        self.t0 = time.time()
        self.duration = None

    def __call__(self, t):
        if self.duration is None:
            self.duration = t
        progress_percentage = t / self.duration if self.duration > 0 else 0
        self.rich_progress.update(
            self.rich_task,
            completed=80 + (progress_percentage * 20),
            description=f"[blue]Writing video: {t:.1f}s / {self.duration:.1f}s"
        )
        return self.make_animation(t / self.duration)

    def make_animation(self, progress):
        return int(100 * progress)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

def create_slideshow(args: argparse.Namespace):
    """
    Create a slideshow based on the provided arguments.

    This function orchestrates the entire process of creating a slideshow,
    including processing images, creating transitions, adding a title slide
    and soundtrack (if specified), and rendering the final video.

    Args:
        args (argparse.Namespace): The parsed command-line arguments containing
                                   all the parameters for slideshow creation.
    """
    start_time = time.time()

    with Progress(
            SpinnerColumn(),
            BarColumn(bar_width=None),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            expand=True
    ) as progress:
        overall_task = progress.add_task("[blue]Creating slideshow", total=100)

        try:
            # Create title slide if specified
            if args.title:
                progress.update(overall_task, description="[blue]Creating title slide")
                try:
                    title_slide = create_title_slide(args.title, args.slideshow_width, args.slideshow_height,
                                                     args.image_duration, args.font)
                except Exception as e:
                    console.print(f"[red]Error creating title slide: {str(e)}[/red]")
                progress.update(overall_task, advance=10)

            # Process images
            progress.update(overall_task, description="[blue]Processing images")
            image_files = get_image_files(args.path, args.image_order)
            processed_images = []
            for i, image_file in enumerate(image_files):
                progress.update(overall_task, description=f"[blue]Processing image: {image_file.name}")
                with Image.open(image_file) as img:
                    img = rotate_image(img)
                    img = resize_and_crop(img, args.slideshow_width, args.slideshow_height)
                    processed_images.append((np.array(img), args.image_duration))
                progress.update(overall_task, advance=20 / len(image_files))

            # Create video clips
            progress.update(overall_task, description="[blue]Creating video clips")
            clips = []
            for i, (img, duration) in enumerate(processed_images):
                clips.append(ImageClip(img).with_duration(duration))  # Changed from set_duration to with_duration
                progress.update(overall_task, advance=10 / len(processed_images))

            # Apply transitions
            progress.update(overall_task, description="[blue]Applying transitions")
            final_clips = []
            for i, clip in enumerate(clips):
                if i == 0:
                    progress.update(overall_task, description="[blue]Applying transitions: First image")
                    if args.title:
                        # Black screen for 1 second
                        black_clip = ColorClip(size=(args.slideshow_width, args.slideshow_height), color=(0, 0, 0))
                        final_clips.append(black_clip.with_duration(1))
                        
                        # Title slide with fade in and fade out
                        title_slide = create_title_slide(args.title, args.slideshow_width, args.slideshow_height, 
                                                         args.image_duration + 2 * args.transition_duration, args.font)
                        title_slide = title_slide.fadein(args.transition_duration).fadeout(args.transition_duration)
                        final_clips.append(title_slide)
                        
                        # Black screen for 1 second
                        final_clips.append(black_clip.with_duration(1))
                        
                        # First image with fade-in
                        final_clips.append(clip.fadein(args.transition_duration))
                    else:
                        # If no title, fade in the first image from black
                        black_clip = ColorClip(size=(args.slideshow_width, args.slideshow_height), color=(0, 0, 0))
                        final_clips.append(black_clip.with_duration(args.transition_duration))
                        final_clips.append(clip.fadein(args.transition_duration))
                elif i == len(clips) - 1:
                    progress.update(overall_task,
                                    description=f"[blue]Applying transitions: Last image ({image_files[i].name})")
                    if i > 0:
                        transition = CompositeVideoClip([
                            clips[i - 1],
                            clip.with_start(args.image_duration - args.transition_duration)
                            .crossfadein(args.transition_duration)
                        ]).with_duration(args.image_duration)
                        final_clips.append(transition)
                    final_clips.append(clip.with_duration(args.image_duration).fadeout(args.transition_duration))
                else:
                    progress.update(overall_task, description=f"[blue]Applying transitions: {image_files[i].name}")
                    transition = CompositeVideoClip([
                        clips[i - 1],
                        clip.with_start(args.image_duration - args.transition_duration)
                        .crossfadein(args.transition_duration)
                    ]).with_duration(args.image_duration)
                    final_clips.append(transition)
                    final_clips.append(clip.with_duration(args.image_duration - args.transition_duration))
                progress.update(overall_task, advance=20 / len(clips))

            # Concatenate clips
            progress.update(overall_task, description="[blue]Concatenating clips")
            final_clip = concatenate_videoclips(final_clips)
            progress.update(overall_task, advance=10)

            # Add soundtrack if specified
            if args.soundtrack:
                progress.update(overall_task, description="[blue]Adding soundtrack")
                try:
                    audio = AudioFileClip(args.soundtrack)
                    if audio.duration < final_clip.duration:
                        audio = audio.audio_loop(duration=final_clip.duration)
                    else:
                        audio = audio.subclip(0, final_clip.duration)
                    final_clip = final_clip.set_audio(audio)
                except Exception as e:
                    console.print(f"[red]Error adding soundtrack: {str(e)}[/red]")
                progress.update(overall_task, advance=10)

            # Ensure we have a valid fps value
            fps = args.fps if args.fps is not None else 24.0

            # Write final output file
            progress.update(overall_task, description="[blue]Rendering video")
            custom_progress_bar = CustomProgressBar(progress, overall_task)

            # Determine the number of CPU cores
            num_cores = multiprocessing.cpu_count()

            # Use 75% of available cores, but at least 1
            num_threads = max(1, int(num_cores * 0.75))

            final_clip.write_videofile(
                args.output,
                fps=fps,  
                codec="libx264",
                audio_codec="aac",
                threads=num_threads,
                preset="medium",
                ffmpeg_params=["-crf", "18"],
            )
            progress.update(overall_task, completed=100)  # Ensure we reach 100%

        except Exception as e:
            console.print(f"[red]An error occurred: {str(e)}[/red]")
            raise

    # Final output
    duration = time.time() - start_time
    console.print(
        f"[green]{args.output} rendered successfully!\n"
        f"Duration: {final_clip.duration:.2f} seconds\n"
        )

if __name__ == "__main__":
    start_time = time.time()
    args = parse_arguments()
    create_slideshow(args)
