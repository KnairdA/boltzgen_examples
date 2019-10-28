{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "pycl-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    boltzgen = pkgs.python3.pkgs.buildPythonPackage rec {
      pname = "boltzgen";
      version = "0.1";

      src = pkgs.fetchFromGitHub {
        owner  = "KnairdA";
        repo   = "boltzgen";
        rev    = "v0.1";
        sha256 = "072kx4jrzd0g9rn63hjb0yic7qhbga47lp2vbz7rq3gvkqv1hz4d";
      };

      propagatedBuildInputs = with pkgs.python37Packages; [
        sympy
        numpy
        Mako
      ];
    };

    local-python = pkgs.python3.withPackages (python-packages: with python-packages; [
      boltzgen
      numpy
      pyopencl setuptools
      matplotlib
    ]);

  in [
    local-python
    pkgs.opencl-info
  ];

  shellHook = ''
    export NIX_SHELL_NAME="${name}"
    export PYOPENCL_COMPILER_OUTPUT=1
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
