with import <nixpkgs> {};

let
  moviepy = python311Packages.buildPythonPackage rec {
    pname = "moviepy";
    version = "master";
    src = pkgs.fetchFromGitHub {
      owner = "Zulko";
      repo = "moviepy";
      rev = "master";
      sha256 = "sha256-y44h96xpP7g1wbplkfS+qF1vDIh6t6AINi+bIkXfjT8=";
    };
    propagatedBuildInputs = with python311Packages; [
      decorator
      imageio
      imageio-ffmpeg
      numpy
      proglog
      requests
      toml
      tqdm
    ];
    doCheck = false;
  };
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    ffmpeg
    git
    python311
    python311Packages.numpy
    python311Packages.decorator
    python311Packages.opencv4
    python311Packages.pillow
    python311Packages.pygame
    python311Packages.rich
    moviepy
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
  '';
}
