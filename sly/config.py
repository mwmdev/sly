"""Configuration handling for sly slideshow creator."""

import os
from typing import Dict, Any, Optional
import toml
from rich.console import Console

console = Console()


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a TOML file.

    Args:
        config_path (str): Path to the config file.

    Returns:
        dict: Configuration dictionary.
    """
    try:
        with open(config_path, "r") as file:
            config_data: Dict[str, Any] = toml.load(file)
            return config_data
    except FileNotFoundError:
        console.print(
            f"[yellow]Config file not found at {config_path}. "
            f"Using default values or command-line arguments.[/yellow]"
        )
        return {}
    except Exception as e:
        console.print(f"[red]Error loading config file: {str(e)}[/red]")
        return {}


def get_config_path(custom_path: Optional[str] = None) -> str:
    """
    Determine the configuration file path.

    Args:
        custom_path (str, optional): Custom config file path provided by user.

    Returns:
        str: Path to the configuration file to use.
    """
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # Default config in current directory
    default_config = "config.toml"
    if os.path.exists(default_config):
        return default_config

    # User config directory
    user_config = os.path.expanduser("~/.config/sly/config.toml")
    if os.path.exists(user_config):
        return user_config

    # Return the default path even if it doesn't exist
    return default_config
