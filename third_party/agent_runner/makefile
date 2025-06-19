.PHONY: types build

types:
	nix-shell tauri-shell.nix --command 'npx openapi-generator-cli generate -i open-api-spec.yaml -g rust -o ./src-tauri/agent_client'
	nix-shell tauri-shell.nix --command 'typeshare ./src-tauri/src/types.rs --lang typescript --output-file ./src/components/types/src_tauri.ts --go-package tmp'
	nix-shell tauri-shell.nix --command 'npx openapi-typescript open-api-spec.yaml --output src/components/types/agent-spec.ts'
	nix-shell tauri-shell.nix --command 'npx openapi-typescript-codegen   --input open-api-spec.yaml   --output src/lib/api   --client fetch'


build:
	nix-shell tauri-shell.nix --command 'yarn run tauri build'

dev:
	nix-shell tauri-shell.nix --command 'yarn run tauri dev'

install:
	nix-shell tauri-shell.nix --command 'yarn install'

lint:
	nix-shell tauri-shell.nix --command 'yarn run check'

all: types lint build
