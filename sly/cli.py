"""Command-line interface for sly slideshow creator."""

import argparse
import logging
from typing import Optional

from rich.console import Console

from .config import load_config_file, get_config_path
from .slideshow import SlideshowCreator
from .font_utils import list_fonts

# Only show error messages
logging.basicConfig(level=logging.ERROR)

console = Console()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the slideshow creation script.

    Returns:
        argparse.Namespace: An object containing all the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Create a slideshow from a folder of images and videos", prog="sly"
    )
    parser.add_argument("--config", "-c", type=str, help="Path to a custom config file")
    parser.add_argument(
        "--path", "-p", type=str, default=None, help="Path to the media directory (images and videos)"
    )
    parser.add_argument(
        "--image-duration",
        "-id",
        type=float,
        default=None,
        help="Duration of each image in seconds",
    )
    parser.add_argument(
        "--image-order",
        "-io",
        type=str,
        default=None,
        help="Order of media files: 'name', 'date', or 'random'",
    )
    parser.add_argument(
        "--transition-duration",
        "-td",
        type=float,
        default=None,
        help="Duration of transition effect in seconds",
    )
    parser.add_argument(
        "--transition-type",
        "-tt",
        type=str,
        default=None,
        choices=["fade", "crossfade"],
        help="Type of transition: 'fade' (fade to black) or 'crossfade' (direct crossfade)",
    )
    parser.add_argument(
        "--slideshow-width",
        "-sw",
        type=int,
        default=None,
        help="Width of the slideshow in pixels",
    )
    parser.add_argument(
        "--slideshow-height",
        "-sh",
        type=int,
        default=None,
        help="Height of the slideshow in pixels",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output file name"
    )
    parser.add_argument(
        "--title", "-t", type=str, default=None, help="Title of the slideshow"
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        default=None,
        help="Path to a .ttf font file for the title",
    )
    parser.add_argument(
        "--font-size", "-fs", type=int, default=None, help="Font size for the title"
    )
    parser.add_argument(
        "--soundtrack", "-st", type=str, default=None, help="Audio file for soundtrack"
    )
    parser.add_argument(
        "--fps",
        "-fps",
        type=float,
        default=None,
        help="Frames per second for the output video",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print more information"
    )
    parser.add_argument(
        "--list-fonts", "-lf", action="store_true", help="List all available system fonts and their paths"
    )
    parser.add_argument(
        "--video-duration-mode",
        "-vdm",
        type=str,
        default=None,
        choices=["original", "fixed", "limit"],
        help="How to handle video durations: 'original' (keep original), 'fixed' (use image duration), 'limit' (cap at 3x image duration)",
    )
    parser.add_argument(
        "--include-videos",
        "-iv",
        action="store_true",
        default=None,
        help="Include video files in slideshow (default: True)",
    )
    parser.add_argument(
        "--images-only",
        "-imo",
        action="store_true",
        help="Process only image files, ignore videos",
    )

    args = parser.parse_args()

    # Determine config file path
    config_path = get_config_path(args.config)

    # Load config file
    config = load_config_file(config_path)

    # Override config values with command line arguments if provided
    for key, value in vars(args).items():
        if value is None and key.replace("_", "-") in config:
            setattr(args, key, config[key.replace("_", "-")])

    # Set defaults for required parameters if not provided
    if args.path is None:
        args.path = "."
    if args.image_duration is None:
        args.image_duration = 3.0
    if args.image_order is None:
        args.image_order = "name"
    if args.transition_duration is None:
        args.transition_duration = 1.0
    if args.transition_type is None:
        args.transition_type = "crossfade"
    if args.slideshow_width is None:
        args.slideshow_width = 1920
    if args.slideshow_height is None:
        args.slideshow_height = 1080
    if args.output is None:
        args.output = "slideshow.mp4"
    if args.fps is None:
        args.fps = 24.0
    if args.video_duration_mode is None:
        args.video_duration_mode = "original"
    
    # Handle video inclusion logic
    if args.images_only:
        args.include_videos = False
    elif args.include_videos is None:
        args.include_videos = True

    # Print final argument values
    if args.verbose:
        console.print(f"[green]Configuration loaded from: {config_path}[/green]")
        console.print("[blue]Final configuration:[/blue]")
        for key, value in vars(args).items():
            if value:
                console.print(f"  - {key}: [blue]{value}[/blue]")

    return args


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate the parsed arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        bool: True if arguments are valid, False otherwise
    """
    if not args.path:
        console.print("[red]Error: Path to media directory is required[/red]")
        return False

    if args.image_duration <= 0:
        console.print("[red]Error: Image duration must be positive[/red]")
        return False

    if args.transition_duration < 0:
        console.print("[red]Error: Transition duration cannot be negative[/red]")
        return False

    if args.slideshow_width <= 0 or args.slideshow_height <= 0:
        console.print("[red]Error: Slideshow dimensions must be positive[/red]")
        return False

    if args.fps <= 0:
        console.print("[red]Error: FPS must be positive[/red]")
        return False

    if args.image_order not in ["name", "date", "random"]:
        console.print(
            "[red]Error: Media order must be 'name', 'date', or 'random'[/red]"
        )
        return False

    return True


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        args = parse_arguments()

        # Handle --list-fonts argument
        if args.list_fonts:
            list_fonts()
            return

        if not validate_arguments(args):
            return

        creator = SlideshowCreator()
        creator.create_slideshow(
            path=args.path,
            output=args.output,
            image_duration=args.image_duration,
            image_order=args.image_order,
            transition_duration=args.transition_duration,
            transition_type=args.transition_type,
            slideshow_width=args.slideshow_width,
            slideshow_height=args.slideshow_height,
            title=args.title,
            font=args.font,
            font_size=args.font_size,
            soundtrack=args.soundtrack,
            fps=args.fps,
            verbose=args.verbose,
            video_duration_mode=args.video_duration_mode,
            include_videos=args.include_videos,
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if hasattr(locals().get('args'), 'verbose') and args.verbose:
            import traceback

            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")


if __name__ == "__main__":
    main()
