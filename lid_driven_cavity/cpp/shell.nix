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
        rev = "4a2885ad3ae0396486d288df94339d0c45e6db8b";
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
