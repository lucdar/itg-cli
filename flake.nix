{
  description = "A CLI tool that automates common administrative tasks for ITGmania/StepMania";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      # Parse the version from __init__.py so it stays in sync
      version = builtins.elemAt (builtins.match ".*__version__ = \"([^\"]+)\".*" (
        builtins.readFile ./src/itg_cli/__init__.py
      )) 0;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python312; # itg-cli requires python >=3.10,<3.13

          # Dependencies not available in nixpkgs, built from PyPI sdists.
          # Hashes come from uv.lock (converted with `nix hash convert`).
          msdparser = python.pkgs.buildPythonPackage rec {
            pname = "msdparser";
            version = "2.0.0";
            pyproject = true;
            src = python.pkgs.fetchPypi {
              inherit pname version;
              hash = "sha256-m7bPS3BcdoULHOIoI8dotiuiu2PRwkB7vj4sI+OL6OM=";
            };
            build-system = [ python.pkgs.setuptools ];
            # sdist ships no tests
            doCheck = false;
          };

          simfile = python.pkgs.buildPythonPackage rec {
            pname = "simfile";
            version = "2.1.1";
            pyproject = true;
            src = python.pkgs.fetchPypi {
              inherit pname version;
              hash = "sha256-p4hfg5XN0PGc152jTlZ12neKoOjdp2VDzwdeIbhixLc=";
            };
            build-system = [ python.pkgs.setuptools ];
            dependencies = [
              msdparser
              python.pkgs.fs
            ];
            # tests require pyfakefs test fixtures not shipped in the sdist
            doCheck = false;
          };

          pyrfc6266 = python.pkgs.buildPythonPackage rec {
            pname = "pyrfc6266";
            version = "1.0.2";
            pyproject = true;
            src = python.pkgs.fetchPypi {
              inherit pname version;
              hash = "sha256-PEFha2ofLpom338AX7qmNPlgEhdpzMREWs+0BOn4/Uw=";
            };
            build-system = [ python.pkgs.setuptools ];
            dependencies = [ python.pkgs.pyparsing ];
            # upstream pins pyparsing~=3.0.7; newer versions work fine
            pythonRelaxDeps = [ "pyparsing" ];
            doCheck = false;
          };

          itg-cli = python.pkgs.buildPythonApplication {
            pname = "itg-cli";
            inherit version;
            pyproject = true;
            src = ./.;

            build-system = [ python.pkgs.setuptools ];

            dependencies =
              [
                simfile
                pyrfc6266
              ]
              ++ (with python.pkgs; [
                gdown
                requests
                rich
                setuptools
                tomlkit
                tqdm
                typer
              ]);

            # nixpkgs ships setuptools >=80; the <80 pin only matters for
            # unpatched PyPI installs (pkg_resources compatibility)
            pythonRelaxDeps = [ "setuptools" ];

            # fs emits a pkg_resources deprecation warning on import with
            # setuptools >=81; silence it so every CLI run isn't noisy
            makeWrapperArgs = [
              "--set-default PYTHONWARNINGS ignore::UserWarning:fs"
            ];

            nativeCheckInputs = [ python.pkgs.pytestCheckHook ];

            meta = {
              description = "A CLI tool that automates common administrative tasks for ITGmania/StepMania";
              homepage = "https://github.com/celex3/itg-cli";
              license = nixpkgs.lib.licenses.mit;
              mainProgram = "itg-cli";
            };
          };
        in
        {
          default = itg-cli;
          inherit itg-cli;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python312
            ];
          };
        }
      );
    };
}
