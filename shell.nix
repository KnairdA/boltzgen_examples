{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "boltzgen-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    boltzgen = pkgs.python3.pkgs.buildPythonPackage rec {
      pname = "boltzgen";
      version = "0.1";

      src = builtins.fetchGit {
        url = "https://code.kummerlaender.eu/boltzgen/";
        rev = "814e6253475c7955eb6a46d814e5a86974e58613";
      };

      propagatedBuildInputs = with pkgs.python37Packages; [
        sympy
        numpy
        Mako
      ];

      doCheck = false;
    };

    local-python = pkgs.python3.withPackages (python-packages: with python-packages; [
      boltzgen
      numpy
      pyopencl setuptools
      matplotlib
    ]);

  in with pkgs; [
    local-python
    opencl-info
    gcc9
    cmake
  ];

  shellHook = ''
    export NIX_SHELL_NAME="${name}"
    export PYOPENCL_COMPILER_OUTPUT=1
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
