#!/bin/bash
set -e

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
SETTINGS="$WORKSPACE/.claude/settings.local.json"

source "$(dirname "$0")/_devcontainer_common.sh"
check_prerequisites || exit 1

start_container
build_env_args

docker exec -it -u vscode -w "$CONTAINER_WORKSPACE" "${ENV_ARGS[@]}" "$CONTAINER_ID" zsh
