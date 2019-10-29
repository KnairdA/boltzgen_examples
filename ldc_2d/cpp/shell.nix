{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "boltzgen-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    boltzgen = pkgs.python3.pkgs.buildPythonPackage rec {
      pname = "boltzgen";
      version = "0.1";

      src = pkgs.fetchFromGitHub {
        owner  = "KnairdA";
        repo   = "boltzgen";
        rev    = "v0.1.1";
        sha256 = "03fv7krhgc43gfjill8wb4aafr8xi69i2yh9zr68knnmrkrb8vpi";
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
    ]);

  in [
    local-python
    pkgs.gcc9
    pkgs.cmake
  ];

  shellHook = ''
    export NIX_SHELL_NAME="${name}"
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
