{ pkgs ? import <nixpkgs> { }, ... }:

pkgs.stdenvNoCC.mkDerivation rec {
  name = "boltzgen-env";
  env = pkgs.buildEnv { name = name; paths = buildInputs; };

  buildInputs = let
    custom-python = let
      packageOverrides = self: super: {
        pyopencl = super.pyopencl.overridePythonAttrs(old: rec {
          buildInputs = with pkgs; [
            opencl-headers ocl-icd python37Packages.pybind11
            libGLU_combined
          ];
        # Enable OpenGL integration and fix build
          preBuild = ''
            python configure.py --cl-enable-gl
            export HOME=/tmp/pyopencl
          '';
        });
      };
    in pkgs.python3.override { inherit packageOverrides; };

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

    local-python = custom-python.withPackages (python-packages: with python-packages; [
      boltzgen
      numpy
      pyopencl setuptools
      pyopengl pyrr
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
