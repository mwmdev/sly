"""Main slideshow creation orchestration for sly."""

import os
import time
import multiprocessing
from typing import Optional
from moviepy.editor import concatenate_videoclips, AudioFileClip, CompositeVideoClip  # type: ignore
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from .image_utils import get_image_files, get_media_files
from .video_utils import create_title_slide, process_images, process_media_files, apply_transitions

console = Console()


def create_transition_sequence(clips, transition_duration, transition_type="crossfade"):
    """
    Create a sequence of clips with the specified transition type.
    
    Args:
        clips: List of video/image clips
        transition_duration: Duration of the transition
        transition_type: Type of transition ('fade' or 'crossfade')
        
    Returns:
        Single concatenated clip with transitions
    """
    if not clips:
        return None
    
    if len(clips) == 1:
        return clips[0].fadein(transition_duration).fadeout(transition_duration)
    
    if transition_type == "fade":
        return create_fade_sequence(clips, transition_duration)
    elif transition_type == "crossfade":
        return create_crossfade_sequence(clips, transition_duration)
    else:
        console.print(f"[yellow]Unknown transition type '{transition_type}', using crossfade[/yellow]")
        return create_crossfade_sequence(clips, transition_duration)


def create_fade_sequence(clips, transition_duration):
    """
    Create a sequence with fade-to-black transitions between clips.
    """
    processed_clips = []
    
    for i, clip in enumerate(clips):
        if i == 0:
            # First clip: fade in only
            processed_clips.append(clip.fadein(transition_duration))
        elif i == len(clips) - 1:
            # Last clip: fade out only
            processed_clips.append(clip.fadeout(transition_duration))
        else:
            # Middle clips: fade in and out for smooth transitions
            processed_clips.append(clip.fadein(transition_duration / 2).fadeout(transition_duration / 2))
    
    try:
        return concatenate_videoclips(processed_clips)
    except Exception as e:
        console.print(f"[red]Error creating fade sequence: {str(e)}[/red]")
        return concatenate_videoclips(clips)


def create_crossfade_sequence(clips, transition_duration):
    """
    Create a sequence with true crossfade transitions between clips.
    """
    if len(clips) == 1:
        return clips[0].fadein(transition_duration).fadeout(transition_duration)
    
    # For crossfade, we need to create overlapping clips
    result_clips = []
    
    for i, clip in enumerate(clips):
        if i == 0:
            # First clip: fade in at start, but don't fade out (crossfade will handle it)
            result_clips.append(clip.fadein(transition_duration))
        elif i == len(clips) - 1:
            # Last clip: fade out at end, crossfade will handle fade in
            result_clips.append(clip.fadeout(transition_duration))
        else:
            # Middle clips: no fades, crossfade will handle transitions
            result_clips.append(clip)
    
    # Use concatenate_videoclips with crossfade by reducing clip durations and overlapping
    try:
        # For true crossfade, we need to create composite clips with overlapping timing
        composite_clips = []
        current_time = 0
        
        for i, clip in enumerate(result_clips):
            if i == 0:
                # First clip: starts at 0, full duration minus transition overlap
                composite_clips.append(clip.set_start(current_time))
                current_time += clip.duration - transition_duration
            elif i == len(result_clips) - 1:
                # Last clip: starts with crossfade overlap, add fade in effect
                composite_clips.append(clip.crossfadein(transition_duration).set_start(current_time))
            else:
                # Middle clips: crossfade in and setup for crossfade out
                composite_clips.append(clip.crossfadein(transition_duration).set_start(current_time))
                current_time += clip.duration - transition_duration
        
        if len(composite_clips) > 1:
            final_clip = CompositeVideoClip(composite_clips)
            return final_clip
        else:
            return composite_clips[0]
            
    except Exception as e:
        console.print(f"[yellow]Crossfade failed ({str(e)}), using simple concatenation[/yellow]")
        # Fallback to simple concatenation with fades
        return concatenate_videoclips(result_clips)


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
        transition_type: str = "crossfade",
        slideshow_width: int = 1920,
        slideshow_height: int = 1080,
        title: Optional[str] = None,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        soundtrack: Optional[str] = None,
        fps: float = 24.0,
        verbose: bool = False,
        video_duration_mode: str = "original",
        include_videos: bool = True,
    ) -> None:
        """
        Create a slideshow based on the provided parameters.

        Args:
            path (str): Path to the media directory (images and videos)
            output (str): Output file name
            image_duration (float): Duration of each image in seconds
            image_order (str): Order of media files: 'name', 'date', or 'random'
            transition_duration (float): Duration of transition effect in seconds
            transition_type (str): Type of transition: 'fade' (fade to black) or 'crossfade' (direct crossfade)
            slideshow_width (int): Width of the slideshow in pixels
            slideshow_height (int): Height of the slideshow in pixels
            title (str, optional): Title of the slideshow
            font (str, optional): Path to a .ttf font file for the title
            font_size (int, optional): Font size for the title
            soundtrack (str, optional): Audio file for soundtrack
            fps (float): Frames per second for the output video
            verbose (bool): Print more information
            video_duration_mode (str): How to handle video durations:
                - "original": Use original video duration
                - "fixed": Use image_duration for all videos
                - "limit": Cap videos at image_duration * 3
            include_videos (bool): Whether to include video files in slideshow
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

                progress.update(overall_task, description="[blue]Processing media files")
                try:
                    if include_videos:
                        media_files = get_media_files(path, image_order)
                        clips = process_media_files(
                            media_files, slideshow_width, slideshow_height, 
                            image_duration, video_duration_mode
                        )
                    else:
                        image_files = get_image_files(path, image_order)
                        clips = process_images(
                            image_files, slideshow_width, slideshow_height, image_duration
                        )
                except FileNotFoundError as e:
                    console.print(f"[red]{str(e)}[/red]")
                    return  # Exit the function

                progress.update(overall_task, advance=20)

                progress.update(overall_task, description="[blue]Creating slideshow with transitions")
                
                # Handle title slide separately if provided
                slideshow_clips = []
                if title_slide:
                    # Add title slide elements
                    from moviepy.editor import ColorClip
                    black_clip = ColorClip(size=title_slide.size, color=(0, 0, 0)).set_duration(0.5)
                    slideshow_clips.append(black_clip)
                    slideshow_clips.append(title_slide.fadein(transition_duration).fadeout(transition_duration))
                    pause_clip = ColorClip(size=title_slide.size, color=(0, 0, 0)).set_duration(0.5)
                    slideshow_clips.append(pause_clip)
                
                # Create main slideshow with transitions
                main_slideshow = create_transition_sequence(clips, transition_duration, transition_type)
                if main_slideshow:
                    slideshow_clips.append(main_slideshow)
                
                # Combine all clips
                if len(slideshow_clips) > 1:
                    final_clip = concatenate_videoclips(slideshow_clips)
                else:
                    final_clip = slideshow_clips[0] if slideshow_clips else clips[0]
                    
                progress.update(overall_task, advance=30)

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
