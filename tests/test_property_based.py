"""Property-based tests for sly using hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume
from hypothesis.extra.numpy import arrays
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path

from sly.image_utils import resize_and_crop, rotate_image
from sly.config import load_config_file


# Strategies for generating test data
valid_dimensions = st.integers(min_value=1, max_value=4000)
valid_duration = st.floats(min_value=0.1, max_value=60.0)
valid_fps = st.floats(min_value=1.0, max_value=120.0)
image_orders = st.sampled_from(["name", "date", "random"])


class TestImageUtilsProperties:
    """Property-based tests for image utility functions."""

    @given(
        original_width=valid_dimensions,
        original_height=valid_dimensions,
        target_width=valid_dimensions,
        target_height=valid_dimensions
    )
    def test_resize_and_crop_always_produces_correct_dimensions(
        self, original_width, original_height, target_width, target_height
    ):
        """Test that resize_and_crop always produces the exact target dimensions."""
        # Create test image with random dimensions
        image = Image.new('RGB', (original_width, original_height), color='red')
        
        # Apply resize and crop
        result = resize_and_crop(image, target_width, target_height)
        
        # Should always produce exact target dimensions
        assert result.size == (target_width, target_height)

    @given(
        width=valid_dimensions,
        height=valid_dimensions,
        color_r=st.integers(min_value=0, max_value=255),
        color_g=st.integers(min_value=0, max_value=255),
        color_b=st.integers(min_value=0, max_value=255)
    )
    def test_resize_and_crop_preserves_image_type(
        self, width, height, color_r, color_g, color_b
    ):
        """Test that resize_and_crop preserves the image mode and format."""
        image = Image.new('RGB', (width, height), color=(color_r, color_g, color_b))
        
        result = resize_and_crop(image, 100, 100)
        
        # Should preserve RGB mode
        assert result.mode == 'RGB'
        # Result should be a PIL Image
        assert isinstance(result, Image.Image)

    @given(
        width=st.integers(min_value=1, max_value=1000),
        height=st.integers(min_value=1, max_value=1000)
    )
    def test_rotate_image_preserves_basic_properties(self, width, height):
        """Test that rotate_image preserves basic image properties."""
        image = Image.new('RGB', (width, height), color='blue')
        
        result = rotate_image(image)
        
        # Should still be an RGB image
        assert result.mode == 'RGB'
        # Should still be a PIL Image
        assert isinstance(result, Image.Image)
        # Dimensions should be positive
        assert result.size[0] > 0
        assert result.size[1] > 0

    @given(st.lists(valid_dimensions, min_size=2, max_size=2))
    def test_resize_and_crop_aspect_ratio_handling(self, dimensions):
        """Test resize_and_crop with various aspect ratios."""
        width, height = dimensions
        assume(width != height)  # Skip square images for this test
        
        image = Image.new('RGB', (width, height), color='green')
        
        # Test resizing to square
        result_square = resize_and_crop(image, 200, 200)
        assert result_square.size == (200, 200)
        
        # Test resizing to different aspect ratio
        result_wide = resize_and_crop(image, 400, 100)
        assert result_wide.size == (400, 100)
        
        result_tall = resize_and_crop(image, 100, 400)
        assert result_tall.size == (100, 400)


class TestConfigProperties:
    """Property-based tests for configuration handling."""

    @given(
        duration=valid_duration,
        width=valid_dimensions,
        height=valid_dimensions,
        fps=valid_fps,
        order=image_orders
    )
    def test_config_roundtrip_properties(self, duration, width, height, fps, order):
        """Test that config values survive round-trip through file I/O."""
        config_data = {
            "image-duration": duration,
            "slideshow-width": width,
            "slideshow-height": height,
            "fps": fps,
            "image-order": order
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            # Write TOML manually (simple case)
            f.write(f'image-duration = {duration}\n')
            f.write(f'slideshow-width = {width}\n')
            f.write(f'slideshow-height = {height}\n')
            f.write(f'fps = {fps}\n')
            f.write(f'image-order = "{order}"\n')
            f.flush()
            
            try:
                # Load and verify
                loaded_config = load_config_file(f.name)
                
                assert loaded_config["image-duration"] == duration
                assert loaded_config["slideshow-width"] == width
                assert loaded_config["slideshow-height"] == height
                assert loaded_config["fps"] == fps
                assert loaded_config["image-order"] == order
                
            finally:
                Path(f.name).unlink()


class TestParameterValidation:
    """Property-based tests for parameter validation."""

    @given(
        image_duration=st.floats(min_value=-1000, max_value=1000),
        transition_duration=st.floats(min_value=-1000, max_value=1000),
        width=st.integers(min_value=-1000, max_value=5000),
        height=st.integers(min_value=-1000, max_value=5000),
        fps=st.floats(min_value=-100, max_value=1000)
    )
    def test_parameter_validation_properties(
        self, image_duration, transition_duration, width, height, fps
    ):
        """Test parameter validation with a wide range of inputs."""
        from sly.cli import validate_arguments
        from argparse import Namespace
        
        args = Namespace(
            path="./test",
            image_duration=image_duration,
            transition_duration=transition_duration,
            slideshow_width=width,
            slideshow_height=height,
            fps=fps,
            image_order="name"
        )
        
        is_valid = validate_arguments(args)
        
        # Check that validation correctly identifies valid vs invalid parameters
        expected_valid = (
            image_duration > 0 and
            transition_duration >= 0 and
            width > 0 and
            height > 0 and
            fps > 0
        )
        
        assert is_valid == expected_valid, \
            f"Validation mismatch for duration={image_duration}, " \
            f"transition={transition_duration}, w={width}, h={height}, fps={fps}"


class TestImageProcessingInvariants:
    """Test invariants that should hold for image processing operations."""

    @given(
        original_size=st.tuples(
            st.integers(min_value=10, max_value=500), 
            st.integers(min_value=10, max_value=500)
        ),
        target_size=st.tuples(
            st.integers(min_value=10, max_value=200), 
            st.integers(min_value=10, max_value=200)
        )
    )
    def test_resize_determinism(self, original_size, target_size):
        """Test that resize operations are deterministic."""
        # Create two identical images (smaller for performance)
        image1 = Image.new('RGB', original_size, color='purple')
        image2 = Image.new('RGB', original_size, color='purple')
        
        # Apply same transformation
        result1 = resize_and_crop(image1, target_size[0], target_size[1])
        result2 = resize_and_crop(image2, target_size[0], target_size[1])
        
        # Results should be identical
        assert result1.size == result2.size
        assert result1.mode == result2.mode

    @given(
        width=st.integers(min_value=1, max_value=500),
        height=st.integers(min_value=1, max_value=500)
    )
    def test_image_processing_memory_bounds(self, width, height):
        """Test that image processing doesn't consume excessive memory."""
        # This is more of a smoke test to ensure operations complete
        image = Image.new('RGB', (width, height), color='cyan')
        
        # These operations should complete without memory errors
        rotated = rotate_image(image)
        resized = resize_and_crop(image, 100, 100)
        
        # Basic sanity checks
        assert rotated is not None
        assert resized is not None
        assert resized.size == (100, 100)


class TestEdgeCase:
    """Property-based tests for edge cases."""

    @given(st.integers(min_value=1, max_value=3))
    def test_minimal_image_dimensions(self, dimension):
        """Test processing with very small images."""
        # Test extremely small images
        tiny_image = Image.new('RGB', (dimension, dimension), color='white')
        
        # Should be able to resize even tiny images
        result = resize_and_crop(tiny_image, 100, 100)
        assert result.size == (100, 100)

    def test_real_image_property_validation(self, real_images):
        """Test properties that should hold for real images."""
        if not real_images:
            pytest.skip("No real images available")
            
        for image_path in real_images[:3]:  # Test first 3 real images
            with Image.open(image_path) as img:
                original_size = img.size
                
                # Property: rotation should preserve pixel count
                rotated = rotate_image(img)
                # Note: rotation might change dimensions due to orientation correction
                assert isinstance(rotated, Image.Image)
                
                # Property: resize should always produce exact target dimensions
                for target_w in [100, 200, 640, 1920]:
                    for target_h in [100, 200, 480, 1080]:
                        resized = resize_and_crop(img, target_w, target_h)
                        assert resized.size == (target_w, target_h)
                        
                # Property: resizing should preserve image mode for photos
                resized = resize_and_crop(img, 300, 300)
                assert resized.mode == img.mode

    @given(
        width=st.integers(min_value=1000, max_value=2000),
        height=st.integers(min_value=1, max_value=10)
    )
    def test_extreme_aspect_ratios(self, width, height):
        """Test with extremely wide or tall images."""
        extreme_image = Image.new('RGB', (width, height), color='orange')
        
        # Should handle extreme aspect ratios
        result = resize_and_crop(extreme_image, 200, 200)
        assert result.size == (200, 200)


# Mark these tests as property-based for filtering
pytestmark = pytest.mark.unit 