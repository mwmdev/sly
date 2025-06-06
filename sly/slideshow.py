"""Main slideshow creation orchestration for sly."""

import os
import time
import multiprocessing
from typing import Optional
from moviepy.editor import concatenate_videoclips, AudioFileClip  # type: ignore
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from .image_utils import get_image_files
from .video_utils import create_title_slide, process_images, apply_transitions

console = Console()


class SlideshowCreator:
    """Main class for creating slideshows from images."""

    def __init__(self) -> None:
        """Initialize the slideshow creator."""
        pass

    def create_slideshow(
        self,
        path: str,
        output: str,
        image_duration: float = 3.0,
        image_order: str = "name",
        transition_duration: float = 1.0,
        slideshow_width: int = 1920,
        slideshow_height: int = 1080,
        title: Optional[str] = None,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        soundtrack: Optional[str] = None,
        fps: float = 24.0,
        verbose: bool = False,
    ) -> None:
        """
        Create a slideshow based on the provided parameters.

        Args:
            path (str): Path to the images directory
            output (str): Output file name
            image_duration (float): Duration of each image in seconds
            image_order (str): Order of images: 'name', 'date', or 'random'
            transition_duration (float): Duration of transition effect in seconds
            slideshow_width (int): Width of the slideshow in pixels
            slideshow_height (int): Height of the slideshow in pixels
            title (str, optional): Title of the slideshow
            font (str, optional): Path to a .ttf font file for the title
            font_size (int, optional): Font size for the title
            soundtrack (str, optional): Audio file for soundtrack
            fps (float): Frames per second for the output video
            verbose (bool): Print more information
        """
        start_time = time.time()

        # Check if output file exists
        if os.path.exists(output):
            overwrite = input(
                f"The file '{output}' already exists. Do you want to overwrite it? [Y/n]: "
            ).lower()
            if overwrite and overwrite != "y":
                console.print("[yellow]Operation cancelled. Exiting...[/yellow]")
                return

        with Progress(
            SpinnerColumn(),
            BarColumn(bar_width=None),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            expand=True,
        ) as progress:
            overall_task = progress.add_task("[blue]Creating slideshow", total=100)

            try:
                title_slide = None
                if title:
                    progress.update(
                        overall_task, description="[blue]Creating title slide"
                    )
                    title_slide = create_title_slide(
                        title,
                        slideshow_width,
                        slideshow_height,
                        image_duration,
                        font,
                        font_size,
                    )
                    progress.update(overall_task, advance=10)

                progress.update(overall_task, description="[blue]Processing images")
                try:
                    image_files = get_image_files(path, image_order)
                except FileNotFoundError as e:
                    console.print(f"[red]{str(e)}[/red]")
                    return  # Exit the function

                clips = process_images(
                    image_files, slideshow_width, slideshow_height, image_duration
                )
                progress.update(overall_task, advance=20)

                progress.update(overall_task, description="[blue]Applying transitions")
                final_clips = apply_transitions(clips, transition_duration, title_slide)
                progress.update(overall_task, advance=20)

                progress.update(overall_task, description="[blue]Concatenating clips")
                final_clip = concatenate_videoclips(final_clips)
                progress.update(overall_task, advance=10)

                if soundtrack:
                    progress.update(overall_task, description="[blue]Adding soundtrack")
                    try:
                        audio = AudioFileClip(soundtrack)
                        if audio.duration < final_clip.duration:
                            audio = audio.audio_loop(duration=final_clip.duration)
                        else:
                            audio = audio.subclip(0, final_clip.duration)
                        final_clip = final_clip.set_audio(audio)
                    except Exception as e:
                        console.print(f"[red]Error adding soundtrack: {str(e)}[/red]")
                    progress.update(overall_task, advance=10)

                progress.update(overall_task, description="[blue]Rendering video")
                num_cores = multiprocessing.cpu_count()
                num_threads = max(1, int(num_cores * 0.75))

                final_clip.write_videofile(
                    output,
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
            f"[green]{output} rendered successfully!\n"
            f"Duration: {final_clip.duration:.2f} seconds\n"
            f"Render time: {duration:.2f} seconds"
        )
