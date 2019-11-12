{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "boltzgen-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    boltzgen = (import ../../boltzgen.nix { }).boltzgen pkgs.python3;

    local-python = pkgs.python3.withPackages (python-packages: with python-packages; [
      boltzgen
    ]);

  in with pkgs; [
    local-python
    gcc9
    cmake
  ];

  shellHook = ''
    export NIX_SHELL_NAME="${name}"
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
