.PHONY: types build

types:
	nix-shell tauri-shell.nix --command 'typeshare ./src-tauri/src/types.rs --lang typescript --output-folder ./src/types --go-package tmp'

build:
	nix-shell tauri-shell.nix --command 'yarn run tauri build'

dev:
	nix-shell tauri-shell.nix --command 'yarn run tauri dev'

