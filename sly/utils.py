"""Utility classes and functions for sly slideshow creator."""

import time
from typing import Any


class CustomProgressBar:
    """
    A custom progress bar class for tracking and displaying the progress of video rendering.
    """

    def __init__(self, rich_progress: Any, rich_task: Any) -> None:
        """
        Initialize the custom progress bar.

        Args:
            rich_progress: Rich progress instance
            rich_task: Rich task instance
        """
        self.rich_progress = rich_progress
        self.rich_task = rich_task
        self.t0 = time.time()
        self.duration = None

    def __call__(self, t: float) -> int:
        """
        Update progress bar with current time.

        Args:
            t (float): Current time in seconds

        Returns:
            int: Animation progress percentage
        """
        if self.duration is None:
            self.duration = t
        progress_percentage = t / self.duration if self.duration > 0 else 0
        self.rich_progress.update(
            self.rich_task,
            completed=80 + (progress_percentage * 20),
            description=f"[blue]Writing video: {t:.1f}s / {self.duration:.1f}s",
        )
        return self.make_animation(t / self.duration)

    def make_animation(self, progress: float) -> int:
        """
        Create animation based on progress.

        Args:
            progress (float): Progress value between 0 and 1

        Returns:
            int: Animation value as percentage
        """
        return int(100 * progress)

    def __enter__(self) -> "CustomProgressBar":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Context manager exit."""
        pass
