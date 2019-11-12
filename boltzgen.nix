{ pkgs ? import <nixpkgs> { }, ... }:

let in {
  boltzgen = python : python.pkgs.buildPythonPackage rec {
    pname = "boltzgen";
    version = "0.1";

    src = builtins.fetchGit {
      url = "https://code.kummerlaender.eu/boltzgen/";
      rev = "aa509dd4ebbb9d1d8ad6ebfe05111228fd9ae7c0";
    };

    propagatedBuildInputs = with pkgs.python37Packages; [
      sympy
      numpy
      Mako
    ];

    doCheck = false;
  };
}
