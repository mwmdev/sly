with import <nixpkgs> {};

pkgs.mkShell {
  buildInputs = with pkgs; [
    # System dependencies
    ffmpeg
    git
    
    # Python and pip
    python311
    python311Packages.pip
    python311Packages.setuptools
    python311Packages.wheel
    python311Packages.virtualenv
    
    # System libraries that might be needed by Python packages
    pkg-config
    libffi
    openssl
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
    export PYGAME_DETECT_AVX2=1
    
    # Create and activate virtual environment
    if [ ! -d ".venv" ]; then
      echo "Creating virtual environment..."
      python -m venv .venv
    fi
    
    source .venv/bin/activate
    
    # Install Python dependencies from requirements.txt
    if [ -f "requirements.txt" ]; then
      echo "Installing Python dependencies from requirements.txt..."
      pip install -r requirements.txt
    fi
  '';
}
