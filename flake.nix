{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    with nixpkgs.lib;
    with flake-utils.lib;

    eachSystem allSystems (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        devShells.default =
          with pkgs;
          mkShell {
            nativeBuildInputs = [
              python3
              python3Packages.pip
              python3Packages.virtualenv
              sqlite
            ];
            shellHook = ''
              virtualenv venv
              source venv/bin/activate
              pip install -r requirements.txt
            '';
          };
      }
    );
}
