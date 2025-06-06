{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    python3Packages.pip
    python3Packages.setuptools
    python3Packages.wheel
    
    # System dependencies for video processing
    ffmpeg
  ];

  shellHook = ''
    echo "Sly development environment loaded!"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
      echo "Creating virtual environment..."
      python -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip and install dependencies
    echo "Installing/upgrading dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install pytest pytest-cov black flake8 mypy
    
    echo ""
    echo "Virtual environment activated!"
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
    echo ""
    echo "To run the application:"
    echo "sly"
  '';
}
