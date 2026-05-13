{
  description = "A Nix-flake-based Node.js + Django development environment";
  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1";
  outputs = {self, ...} @ inputs: let
    supportedSystems = [
      "x86_64-linux"
      "aarch64-linux"
      "aarch64-darwin"
    ];
    forEachSupportedSystem = f:
      inputs.nixpkgs.lib.genAttrs supportedSystems (
        system:
          f {
            inherit system;
            pkgs = import inputs.nixpkgs {
              inherit system;
              overlays = [inputs.self.overlays.default];
            };
          }
      );
  in {
    overlays.default = final: prev: rec {
      nodejs = prev.nodejs;
      yarn = prev.yarn.override {inherit nodejs;};
    };
    devShells = forEachSupportedSystem (
      {
        pkgs,
        system,
      }: {
        default = pkgs.mkShellNoCC {
          packages = with pkgs; [
            nodejs
            nodePackages.pnpm
            typescript-language-server
            vscode-css-languageserver
            superhtml
            yarn
            self.formatter.${system}
            (python313.withPackages (ps:
              with ps; [
                django
                djangorestframework
                django-cors-headers
                django-filter
                djangorestframework-simplejwt
                drf-spectacular

                psycopg2
                sqlparse

                asgiref
                attrs
                pillow
                python-dotenv
                pyyaml
                pyjwt
                inflection
                uritemplate

                jsonschema
                jsonschema-specifications
                referencing
                rpds-py

                tzdata
                pip
              ]))
          ];
        };
      }
    );
    formatter = forEachSupportedSystem ({pkgs, ...}: pkgs.nixfmt);
  };
}
