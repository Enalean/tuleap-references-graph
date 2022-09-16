{pkgs ? import (
  fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/0e304ff0d9db453a4b230e9386418fd974d5804a.tar.gz";
    sha256 = "sha256:0c91rbax0yh9xbg2l6qx9nfmisz4g6c36rlg8zjclfm3yqc8hkfl";
  }
) {}}:

pkgs.mkShellNoCC {
  buildInputs = [
    pkgs.python39Packages.virtualenv
    pkgs.python39Packages.jupyter
    pkgs.python39Packages.igraph
    pkgs.python39Packages.matplotlib
    pkgs.gitMinimal
  ];
}
