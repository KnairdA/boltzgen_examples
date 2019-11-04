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
        rev    = "78f5edec8151db38ebf933e915fcca5f65b1cad5";
        sha256 = "1cyp5b5v8r24ih2dxhjhlp7frnqlwzslah2pzfi745f3ii370r42";
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
