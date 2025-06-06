{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    python3Packages.pip
    python3Packages.setuptools
    python3Packages.wheel
    
    # Core dependencies
    python3Packages.moviepy
    python3Packages.pillow
    python3Packages.numpy
    python3Packages.rich
    python3Packages.toml
    
    # Development dependencies
    python3Packages.pytest
    python3Packages.pytest-cov
    python3Packages.black
    python3Packages.flake8
    python3Packages.mypy
    
    # System dependencies for video processing
    ffmpeg
  ];

  shellHook = ''
    echo "Sly development environment loaded!"
    echo "Available commands:"
    echo "  pytest         - Run tests"
    echo "  pytest --cov   - Run tests with coverage"
    echo "  black .        - Format code"
    echo "  flake8 .       - Lint code"
    echo "  mypy sly       - Type checking"
    echo ""
    echo "To install in development mode:"
    echo "  pip install -e ."
    echo ""
    echo "To build for PyPI:"
    echo "  python -m build"
  '';
}
