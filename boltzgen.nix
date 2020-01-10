{ pkgs ? import <nixpkgs> { }, ... }:

let in {
  boltzgen = python : python.pkgs.buildPythonPackage rec {
    pname = "boltzgen";
    version = "0.1";

    src = builtins.fetchGit {
      url = "https://code.kummerlaender.eu/boltzgen/";
      rev = "b5a24f31871d900342a3c47398cc75e22bad0b6f";
    };

    propagatedBuildInputs = with pkgs.python37Packages; [
      sympy
      numpy
      Mako
    ];

    doCheck = false;
  };
}
