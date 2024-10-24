import argparse
import random
from pathlib import Path
from typing import List
import numpy as np
from moviepy.editor import concatenate_videoclips, ImageClip, CompositeVideoClip, AudioFileClip, ColorClip
import traceback
from PIL import Image, ExifTags, ImageFont, ImageDraw
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import os
import multiprocessing
import time
import toml

import logging
# from venv import logger

logging.basicConfig(level=logging.ERROR)  # Only show error messages

console = Console()

def load_config_file(config_path: str) -> dict:
    """
    Load configuration from a TOML file.

    Args:
        config_path (str): Path to the config file.

    Returns:
        dict: Configuration dictionary.
    """
    try:
        with open(config_path, 'r') as file:
            return toml.load(file)
    except FileNotFoundError:
        console.print(f"[yellow]Config file not found at {config_path}. Using default values or command-line arguments.[/yellow]")
        return {}
    except Exception as e:
        console.print(f"[red]Error loading config file: {str(e)}[/red]")
        return {}

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the slideshow creation script.

    Returns:
        argparse.Namespace: An object containing all the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Create a slideshow from a folder of images")
    parser.add_argument("--config", "-c", type=str, help="Path to a custom config file")
    parser.add_argument("--path", "-p", type=str, default=None, help="Path to the images directory")
    parser.add_argument("--image-duration", "-id", type=float, default=None, help="Duration of each image in seconds")
    parser.add_argument("--image-order", "-io", type=str, default=None, help="Order of images: 'name', 'date', or 'random'")
    parser.add_argument("--transition-duration", "-td", type=float, default=None, help="Duration of transition effect in seconds")
    parser.add_argument("--slideshow-width", "-sw", type=int, default=None, help="Width of the slideshow in pixels")
    parser.add_argument("--slideshow-height", "-sh", type=int, default=None, help="Height of the slideshow in pixels")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output file name")
    parser.add_argument("--title", "-t", type=str, default=None, help="Title of the slideshow")
    parser.add_argument("--font", "-f", type=str, default=None, help="Path to a .ttf font file for the title")
    parser.add_argument("--font-size", "-fs", type=int, default=None, help="Font size for the title")
    parser.add_argument("--soundtrack", "-st", type=str, default=None, help="Audio file for soundtrack")
    parser.add_argument("--fps", "-fps", type=float, default=None, help="Frames per second for the output video")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print more information")

    args = parser.parse_args()

    # Determine config file path
    config_path = args.config or "config.toml"
    if not os.path.exists(config_path):
        config_path = os.path.expanduser("~/.config/sly/config.toml")
    
    # Load config file
    config = load_config_file(config_path)

    # Override config values with command line arguments if provided
    for key, value in vars(args).items():
        if value is None and key in config:
            setattr(args, key, config[key])

    # Print final argument values
    if args.verbose:
        console.print(f"Loaded: {config_path}")
        for key, value in vars(args).items():
            if value:
                console.print(f"- {key}: [blue]{value}[/blue]")

    return args

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
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".jpg_", ".tiff", ".tif", ".webp"}
    image_files = [f for f in Path(path).iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        raise FileNotFoundError(f"No image files found in the specified directory: {path}")

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
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            if exif.get(orientation) == 3:
                image = image.rotate(180, expand=True)
            elif exif.get(orientation) == 6:
                image = image.rotate(270, expand=True)
            elif exif.get(orientation) == 8:
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

def create_title_slide(title: str, width: int, height: int, duration: float, font_path: str = None, font_size: int = None) -> ImageClip:
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
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)

        # Load font
        if font_size is None:
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

def process_images(image_files: List[Path], width: int, height: int, duration: float) -> List[ImageClip]:
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
            processed_images.append(ImageClip(np.array(img)).with_duration(duration))
    return processed_images

def apply_transitions(clips: List[ImageClip], transition_duration: float, title_slide: ImageClip = None) -> List[ImageClip]:
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
        black_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).with_duration(1)
        final_clips.extend([black_clip, title_slide.fadein(transition_duration).fadeout(transition_duration), black_clip])
        
        # Add a pause after the title slide fades to black
        pause_duration = 1  # Duration of the pause in seconds
        pause_clip = ColorClip(size=clips[0].size, color=(0, 0, 0)).with_duration(pause_duration)
        final_clips.append(pause_clip)

    for i, clip in enumerate(clips):
        if i == 0:
            # Ensure the first image slide fades in
            final_clips.append(clip.fadein(transition_duration))
        elif i == len(clips) - 1:
            if i > 0:
                transition = CompositeVideoClip([
                    clips[i - 1],
                    clip.with_start(clip.duration - transition_duration).crossfadein(transition_duration)
                ]).with_duration(clip.duration)
                final_clips.append(transition)
            final_clips.append(clip.fadeout(transition_duration))
        else:
            transition = CompositeVideoClip([
                clips[i - 1],
                clip.with_start(clip.duration - transition_duration).crossfadein(transition_duration)
            ]).with_duration(clip.duration)
            final_clips.append(transition)
            final_clips.append(clip.with_duration(clip.duration - transition_duration))
    return final_clips

def create_slideshow(args: argparse.Namespace):
    """
    Create a slideshow based on the provided arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
    start_time = time.time()

    if os.path.exists(args.output):
        overwrite = input(f"The file '{args.output}' already exists. Do you want to overwrite it? [Y/n]: ").lower()
        if overwrite and overwrite != 'y':
            console.print("[yellow]Operation cancelled. Exiting...[/yellow]")
            return

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
            title_slide = None
            if args.title:
                progress.update(overall_task, description="[blue]Creating title slide")
                title_slide = create_title_slide(args.title, args.slideshow_width, args.slideshow_height,
                                                 args.image_duration, args.font, args.font_size)
                progress.update(overall_task, advance=10)

            progress.update(overall_task, description="[blue]Processing images")
            try:
                image_files = get_image_files(args.path, args.image_order)
            except FileNotFoundError as e:
                console.print(f"[red]{str(e)}[/red]")
                return  # Exit the function

            clips = process_images(image_files, args.slideshow_width, args.slideshow_height, args.image_duration)
            progress.update(overall_task, advance=20)

            progress.update(overall_task, description="[blue]Applying transitions")
            final_clips = apply_transitions(clips, args.transition_duration, title_slide)
            progress.update(overall_task, advance=20)

            progress.update(overall_task, description="[blue]Concatenating clips")
            final_clip = concatenate_videoclips(final_clips)
            progress.update(overall_task, advance=10)

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

            fps = args.fps if args.fps is not None else 24.0

            progress.update(overall_task, description="[blue]Rendering video")
            num_cores = multiprocessing.cpu_count()
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
            progress.update(overall_task, completed=100)

        except Exception as e:
            console.print(f"[red]An error occurred: {str(e)}[/red]")
            raise

    duration = time.time() - start_time
    console.print(
        f"[green]{args.output} rendered successfully!\n"
        f"Duration: {final_clip.duration:.2f} seconds\n"
    )

if __name__ == "__main__":
    start_time = time.time()
    args = parse_arguments()
    create_slideshow(args)

