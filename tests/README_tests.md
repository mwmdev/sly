# Sly Slideshow Tests

This directory contains comprehensive tests for the Sly slideshow application, including tests that use real image and audio assets.

## Test Assets

The `tests/assets/` directory contains real test files:

### Images
- `photo_1.jpg` through `photo_6.jpg` - Real photo files of various sizes and orientations
- These are actual photographs that test realistic image processing scenarios
- File sizes range from ~2MB to ~5MB each

### Audio
- `audio.mp3` - Real MP3 audio file (~2.8MB)
- `audio.wav` - Real WAV audio file (~22MB)
- These test realistic soundtrack integration

## Test Categories

### Unit Tests
Basic functionality tests with focused scope:
```bash
pytest -m unit
```

### Integration Tests  
Tests using real files and complete workflows:
```bash
pytest -m integration
```

### Property-Based Tests
Advanced testing using Hypothesis for edge case discovery:
```bash
pytest tests/test_property_based.py
```

### Performance Tests
Slower tests that measure performance:
```bash
pytest -m slow
```

### Real Assets Showcase
Comprehensive tests demonstrating real asset usage:
```bash
pytest tests/test_real_assets_showcase.py -v
```

## Running All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sly --cov-report=html

# Run fast tests only (skip slow performance tests)
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_slideshow.py
```

## Test Structure

```
tests/
├── assets/              # Real test files
│   ├── photo_1.jpg      # Real photos
│   ├── photo_2.jpg
│   ├── ...
│   ├── audio.mp3        # Real audio files
│   └── audio.wav
├── conftest.py          # Shared fixtures and configuration
├── test_slideshow.py    # Core business logic tests
├── test_video_utils.py  # Video processing tests
├── test_integration.py  # Real file integration tests
├── test_property_based.py # Advanced property-based tests
├── test_real_assets_showcase.py # Comprehensive real asset tests
├── test_utils.py        # Additional testing patterns
├── test_config.py       # Configuration tests
├── test_image_utils.py  # Image processing tests
└── test_cli.py          # CLI interface tests
```

## Key Features

### Real Asset Testing
- Tests use actual photos and audio files instead of synthetic data
- Realistic file sizes and formats
- Tests handle real-world image properties (EXIF data, various resolutions)

### Comprehensive Coverage
- Core business logic (SlideshowCreator)
- Video processing (create_title_slide, process_images, apply_transitions)
- Image utilities (resize_and_crop, rotate_image, get_image_files)
- Configuration loading and validation
- CLI argument parsing and validation
- Error handling and edge cases

### Advanced Testing Patterns
- Property-based testing with Hypothesis
- Integration testing with real files
- Performance benchmarking
- Concurrency testing
- Memory usage testing
- Error recovery testing

### Test Quality Features
- Shared fixtures reduce duplication
- Proper test isolation and cleanup
- Descriptive test names and documentation
- Parameterized tests for comprehensive coverage
- Custom assertions for domain-specific validation

## Dependencies

The tests require these additional packages:
- `pytest-mock` - Enhanced mocking capabilities
- `hypothesis` - Property-based testing
- `psutil` - Memory usage testing (for performance tests)

Install with:
```bash
pip install pytest-mock hypothesis psutil
```

## Best Practices Demonstrated

1. **Balanced Mocking**: Uses real files where appropriate, mocks external dependencies
2. **Test Categories**: Clear separation of unit, integration, and performance tests
3. **Realistic Scenarios**: Tests with actual image and audio files
4. **Error Boundaries**: Comprehensive error handling tests
5. **Performance Awareness**: Tests include performance benchmarks
6. **Documentation**: Well-documented test purpose and expected behavior 