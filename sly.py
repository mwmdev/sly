import argparse
import random
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np
from moviepy.editor import concatenate_videoclips, ImageClip, CompositeVideoClip
import traceback
from PIL import Image, ExifTags, ImageFont, ImageDraw
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

import logging
logging.basicConfig(level=logging.INFO)

console = Console()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a slideshow from a folder of images")
    parser.add_argument("--path", "-p", type=str, default=".", help="Path to the images directory")
    parser.add_argument("--image-duration", "-id", type=float, default=5, help="Duration of each image in seconds")
    parser.add_argument("--image-order", "-io", type=str, default="date", choices=["name", "date", "random"],
                        help="Order of images")
    parser.add_argument("--transition-duration", "-td", type=float, default=2,
                        help="Duration of transition effect in seconds")
    parser.add_argument("--transition", "-t", type=str, default="fade", help="Transition effect name")
    parser.add_argument("--slideshow-width", "-sw", type=int, default=1920, help="Width of the slideshow in pixels")
    parser.add_argument("--slideshow-height", "-sh", type=int, default=1080, help="Height of the slideshow in pixels")
    parser.add_argument("--output", "-o", type=str, default="slideshow.mp4", help="Output file name")
    parser.add_argument("--title", type=str, default="", help="Title of the slideshow")
    parser.add_argument("--font", type=str, default=None, help="Path to a .ttf font file for the title")
    parser.add_argument("--soundtrack", "-st", type=str, default="", help="Audio file for soundtrack")
    parser.add_argument("--gpu", action="store_true", help="Use GPU acceleration")
    return parser.parse_args()


def get_image_files(path: str, order: str) -> List[Path]:
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    image_files = [f for f in Path(path).iterdir() if f.suffix.lower() in image_extensions]

    if order == "name":
        image_files.sort(key=lambda x: x.name)
    elif order == "date":
        image_files.sort(key=lambda x: x.stat().st_mtime)
    elif order == "random":
        random.shuffle(image_files)

    return image_files


def rotate_image(image: Image.Image) -> Image.Image:
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


def enhance_colors(image: Image.Image) -> Image.Image:
    # Convert to LAB color space
    lab = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2LAB)

    # Split the LAB image into L, A, and B channels
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    # Merge the CLAHE enhanced L-channel back with A and B channels
    limg = cv2.merge((cl, a, b))

    # Convert back to RGB color space
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)

    return Image.fromarray(enhanced)


def create_title_slide(title: str, width: int, height: int, duration: float, font_path: str = None) -> ImageClip:
    console.print("[cyan]Starting title slide creation...[/cyan]")
    try:
        # Create a black background
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)

        # Load font
        font_size = min(width, height) // 10
        if font_path:
            try:
                font = ImageFont.truetype(font_path, font_size)
                console.print(f"Using font from: {font_path}")
            except IOError:
                console.print(f"[yellow]Error loading font from {font_path}. Using default font.[/yellow]")
                font = ImageFont.load_default()
        else:
            console.print("[yellow]No font specified. Using default font.[/yellow]")
            font = ImageFont.load_default()

        # Get text size
        left, top, right, bottom = draw.textbbox((0, 0), title, font=font)
        text_width = right - left
        text_height = bottom - top

        # Calculate position to center the text
        position = ((width - text_width) // 2, (height - text_height) // 2)

        # Draw text
        draw.text(position, title, font=font, fill='white')

        console.print("Title slide image created successfully.")

        # Convert to ImageClip
        image_array = np.array(image)
        clip = ImageClip(image_array).set_duration(duration)

        # Add a fade-in effect
        clip = clip.fadein(duration/2)

        return clip
    except Exception as e:
        console.print(f"[bold red]Error in create_title_slide: {str(e)}[/bold red]")
        console.print(f"Traceback: {traceback.format_exc()}")
        raise

def process_images(args: argparse.Namespace, progress: Progress, task: TaskID) -> List[Tuple[np.ndarray, float]]:
    image_files = get_image_files(args.path, args.image_order)
    processed_images = []

    for image_file in image_files:
        with Image.open(image_file) as img:
            img = rotate_image(img)
            img = resize_and_crop(img, args.slideshow_width, args.slideshow_height)
            img = enhance_colors(img)
            processed_images.append((np.array(img), args.image_duration))
        progress.update(task, advance=1)

    return processed_images


def create_slideshow(args: argparse.Namespace):
    clips = []  # Initialize clips list
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        try:
            # Create title slide if specified
            title_slide = None
            if args.title:
                console.print("[cyan]Creating title slide...[/cyan]")
                try:
                    title_slide = create_title_slide(args.title, args.slideshow_width, args.slideshow_height, args.image_duration, args.font)
                    console.print("[green]Title slide created successfully[/green]")
                except Exception as e:
                    console.print(f"[bold red]Error creating title slide: {str(e)}[/bold red]")
                    console.print(f"Traceback: {traceback.format_exc()}")
                    console.print("[yellow]Continuing without title slide...[/yellow]")

            # Process images
            task_process = progress.add_task("[cyan]Processing images...",
                                             total=len(get_image_files(args.path, args.image_order)))
            processed_images = process_images(args, progress, task_process)

            # Create video clips
            task_create = progress.add_task("[green]Creating video clips...", total=len(processed_images))
            for i, (img, duration) in enumerate(processed_images):
                console.print(f"Creating clip {i + 1} of {len(processed_images)}")
                clip = ImageClip(img).set_duration(args.image_duration)
                clips.append(clip)
                progress.update(task_create, advance=1)

            # Apply transitions
            console.print("[yellow]Applying transitions...[/yellow]")
            final_clips = []

            # Handle title slide if it exists
            if title_slide:
                if clips:  # If there are image clips
                    transition = CompositeVideoClip([
                        title_slide,
                        clips[0].set_start(args.image_duration - args.transition_duration)
                        .crossfadein(args.transition_duration)
                    ]).set_duration(args.image_duration)
                    final_clips.append(transition)
                else:  # If title slide is the only clip
                    final_clips.append(title_slide)

            # Handle image clips
            for i, clip in enumerate(clips):
                if i == 0 and title_slide:
                    # First image after title slide: already handled in title slide transition
                    final_clips.append(clip.set_duration(args.image_duration - args.transition_duration))
                elif i == len(clips) - 1:  # Last image
                    if i > 0:  # If it's not the only image
                        # Add transition from previous clip to this one
                        transition = CompositeVideoClip([
                            clips[i-1],
                            clip.set_start(args.image_duration - args.transition_duration)
                            .crossfadein(args.transition_duration)
                        ]).set_duration(args.image_duration)
                        final_clips.append(transition)

                    # Add the last clip with full duration and fade out
                    final_clips.append(clip.set_duration(args.image_duration).fadeout(args.transition_duration))
                else:  # Middle images
                    # Add transition from previous clip to this one
                    transition = CompositeVideoClip([
                        clips[i-1],
                        clip.set_start(args.image_duration - args.transition_duration)
                        .crossfadein(args.transition_duration)
                    ]).set_duration(args.image_duration)
                    final_clips.append(transition)

                    # Add the clip with duration minus transition time
                    final_clips.append(clip.set_duration(args.image_duration - args.transition_duration))

            # Concatenate clips
            console.print("Concatenating clips...")
            task_concat = progress.add_task("[yellow]Concatenating clips...")
            try:
                final_clip = concatenate_videoclips(final_clips)
                console.print("Clips concatenated successfully")
                console.print(f"Final clip duration: {final_clip.duration} seconds")
            except Exception as e:
                console.print(f"[red]Error during concatenation process: {str(e)}[/red]")
                console.print(f"Traceback: {traceback.format_exc()}")
                raise
            progress.update(task_concat, completed=100)

            # Write final output file
            console.print("Writing final output file...")
            task_write = progress.add_task("[red]Writing final output file...")
            try:
                final_clip.write_videofile(
                    args.output,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    threads=4,
                    preset="medium",
                    ffmpeg_params=["-crf", "18"],
                )
                console.print("Final output file written successfully")
            except Exception as e:
                console.print(f"[red]Error writing final output file: {str(e)}[/red]")
                console.print(f"Traceback: {traceback.format_exc()}")
                raise
            progress.update(task_write, completed=100)

        except Exception as e:
            console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")
            console.print(f"Traceback: {traceback.format_exc()}")
            raise

    console.print("[bold green]Slideshow creation process completed.[/bold green]")

if __name__ == "__main__":
    args = parse_arguments()
    console.print("[bold green]Starting slideshow creation...[/bold green]")
    create_slideshow(args)
