{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "boltzgen-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    boltzgen = (import ../../boltzgen.nix { }).boltzgen pkgs.python3;

    local-python = pkgs.python3.withPackages (python-packages: with python-packages; [
      boltzgen
      numpy
      pyopencl setuptools
      matplotlib
    ]);

  in with pkgs; [
    local-python
    opencl-info
  ];

  shellHook = ''
    export NIX_SHELL_NAME="${name}"
    export PYOPENCL_COMPILER_OUTPUT=1
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
