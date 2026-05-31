{
  description = "Flake providing a daily auto-updating FreeCAD package";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  outputs = {nixpkgs, ...}: {
    packages."x86_64-linux"."freecad-daily" = let
      repoInfo = builtins.fromJSON (builtins.readFile ./repo.json);
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in
      pkgs.freecad.overrideAttrs (final: prev: {
        version = repoInfo.version;
        src = pkgs.fetchFromGitHub {
          owner = "FreeCAD";
          repo = "FreeCAD";
          tag = repoInfo.commitHash;
          hash = repoInfo.sriHash;
          fetchSubmodules = true;
        };
      });
  };
}
