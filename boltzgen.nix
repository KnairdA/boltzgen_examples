{ pkgs ? import <nixpkgs> { }, ... }:

let in {
  boltzgen = python : python.pkgs.buildPythonPackage rec {
    pname = "boltzgen";
    version = "0.1";

    src = builtins.fetchGit {
      url = "https://code.kummerlaender.eu/boltzgen/";
      rev = "25c210daa7c45d937bcc336ca887bfba71000a23";
    };

    propagatedBuildInputs = with pkgs.python37Packages; [
      sympy
      numpy
      Mako
    ];

    doCheck = false;
  };
}
