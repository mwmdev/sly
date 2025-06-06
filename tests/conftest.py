"""Shared pytest fixtures and configuration for sly tests."""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from PIL import Image
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def assets_dir():
    """Return path to test assets directory."""
    return Path(__file__).parent / "assets"


@pytest.fixture
def real_images(assets_dir):
    """Provide paths to real test images."""
    if not assets_dir.exists():
        pytest.skip(f"Assets directory {assets_dir} does not exist")

    image_files = sorted(assets_dir.glob("photo_*.jpg"))
    if not image_files:
        pytest.skip(f"No photo_*.jpg files found in {assets_dir}")

    return image_files


@pytest.fixture
def real_audio_files(assets_dir):
    """Provide paths to real audio test files."""
    if not assets_dir.exists():
        pytest.skip(f"Assets directory {assets_dir} does not exist")

    audio_files = {"mp3": assets_dir / "audio.mp3", "wav": assets_dir / "audio.wav"}

    # Check if audio files exist
    for format_name, file_path in audio_files.items():
        if not file_path.exists():
            pytest.skip(f"Audio file {file_path} does not exist")

    return audio_files


@pytest.fixture
def sample_image():
    """Create a simple test image."""
    return Image.new("RGB", (100, 100), color="red")


@pytest.fixture
def sample_images():
    """Create multiple test images with different properties."""
    images = []
    colors = ["red", "green", "blue", "yellow"]
    sizes = [(100, 100), (200, 150), (150, 200), (300, 100)]

    for i, (color, size) in enumerate(zip(colors, sizes)):
        img = Image.new("RGB", size, color=color)
        # Add some pattern to make it more realistic
        pixels = img.load()
        for x in range(min(size[0], 20)):
            for y in range(min(size[1], 20)):
                pixels[x, y] = (x * 10, y * 10, (x + y) * 5)
        images.append(img)

    return images


@pytest.fixture
def image_files_dir(temp_dir, sample_images):
    """Create a directory with sample image files."""
    image_dir = Path(temp_dir) / "images"
    image_dir.mkdir()

    image_paths = []
    for i, img in enumerate(sample_images):
        img_path = image_dir / f"test_image_{i:03d}.jpg"
        img.save(img_path)
        image_paths.append(img_path)

    return str(image_dir), image_paths


@pytest.fixture
def real_images_dir(temp_dir, real_images):
    """Create a temporary directory with copies of real test images."""
    image_dir = Path(temp_dir) / "real_images"
    image_dir.mkdir()

    copied_images = []
    for image_file in real_images:
        dest_path = image_dir / image_file.name
        shutil.copy2(image_file, dest_path)
        copied_images.append(dest_path)

    return str(image_dir), copied_images


@pytest.fixture
def mock_moviepy_clip():
    """Create a mock MoviePy clip for testing."""
    mock_clip = Mock()
    mock_clip.duration = 3.0
    mock_clip.size = (1920, 1080)

    # Set up method chains
    mock_clip.set_duration.return_value = mock_clip
    mock_clip.fadein.return_value = mock_clip
    mock_clip.fadeout.return_value = mock_clip
    mock_clip.set_start.return_value = mock_clip
    mock_clip.crossfadein.return_value = mock_clip
    mock_clip.set_audio.return_value = mock_clip

    return mock_clip


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file for testing."""
    config_path = Path(temp_dir) / "test_config.toml"
    config_content = """
# Test configuration
image-duration = 3.5
slideshow-width = 1280
slideshow-height = 720
transition-duration = 1.5
fps = 30.0
image-order = "name"

[advanced]
codec = "libx264"
quality = "high"
"""
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically clean up any test files after each test."""
    yield
    # Clean up any files that might have been created during testing
    # This runs after each test


# Performance testing helpers
@pytest.fixture
def performance_images(temp_dir, real_images):
    """Create multiple images for performance testing using real images."""
    image_dir = Path(temp_dir) / "perf_images"
    image_dir.mkdir()

    # Use real images, duplicating them to get more files for performance testing
    image_paths = []
    for i in range(4):  # Create 4 copies of each real image (6*4 = 24 images)
        for j, real_image in enumerate(real_images):
            dest_name = f"perf_{i:02d}_{j:02d}_{real_image.name}"
            dest_path = image_dir / dest_name
            shutil.copy2(real_image, dest_path)
            image_paths.append(dest_path)

    return str(image_dir)


@pytest.fixture
def mixed_content_dir(temp_dir, real_images, real_audio_files):
    """Create a directory with real images, audio files, and other content."""
    content_dir = Path(temp_dir) / "mixed_content"
    content_dir.mkdir()

    # Copy real images
    for image_file in real_images:
        shutil.copy2(image_file, content_dir / image_file.name)

    # Copy audio files
    for audio_name, audio_path in real_audio_files.items():
        shutil.copy2(audio_path, content_dir / f"soundtrack.{audio_name}")

    # Add some non-media files
    (content_dir / "readme.txt").write_text("This is a readme file")
    (content_dir / "config.json").write_text('{"setting": "value"}')
    (content_dir / ".DS_Store").write_text("Mac system file")

    return str(content_dir)


# Error testing helpers
@pytest.fixture
def corrupted_image_dir(temp_dir):
    """Create a directory with a corrupted image file."""
    image_dir = Path(temp_dir) / "corrupted"
    image_dir.mkdir()

    # Create a file that looks like an image but isn't
    fake_image = image_dir / "fake.jpg"
    fake_image.write_text("This is not actually an image file")

    return str(image_dir)


# Configuration for pytest
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")

    # Configure Hypothesis for faster test runs
    try:
        from hypothesis import settings

        settings.register_profile("fast", max_examples=20, deadline=500)
        settings.load_profile("fast")
    except ImportError:
        pass  # Hypothesis not available


# Custom assertion helpers
def assert_image_dimensions(image, expected_width, expected_height):
    """Helper function to assert image dimensions."""
    assert image.size == (
        expected_width,
        expected_height,
    ), f"Expected image size {(expected_width, expected_height)}, got {image.size}"


def assert_file_exists_and_readable(file_path):
    """Helper function to assert file exists and is readable."""
    path = Path(file_path)
    assert path.exists(), f"File {file_path} does not exist"
    assert path.is_file(), f"Path {file_path} is not a file"
    assert os.access(path, os.R_OK), f"File {file_path} is not readable"
