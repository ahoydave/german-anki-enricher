#!/bin/bash
# Shared setup for devcontainer scripts — source this, don't run directly.

check_prerequisites() {
  local ok=true

  if ! command -v docker &>/dev/null; then
    echo "ERROR: docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/" >&2
    ok=false
  elif ! docker info &>/dev/null; then
    echo "ERROR: Docker is not running. Start Docker Desktop and try again." >&2
    ok=false
  fi

  if ! command -v devcontainer &>/dev/null; then
    echo "ERROR: devcontainer CLI not found. Install it with:" >&2
    echo "  npm install -g @devcontainers/cli" >&2
    ok=false
  fi

  if ! command -v jq &>/dev/null; then
    echo "ERROR: jq not found. Install it with: brew install jq" >&2
    ok=false
  fi

  if [ ! -f "$SETTINGS" ]; then
    echo "ERROR: $SETTINGS not found. Create it with your Anthropic credentials." >&2
    ok=false
  fi

  [ "$ok" = true ]
}

start_container() {
  echo "Starting dev container..."
  OUTPUT=$(devcontainer up --workspace-folder "$WORKSPACE")
  echo "$OUTPUT"
  CONTAINER_ID=$(echo "$OUTPUT" | jq -r '.containerId')
  CONTAINER_WORKSPACE=$(echo "$OUTPUT" | jq -r '.remoteWorkspaceFolder')
}

build_env_args() {
  ENV_ARGS=()
  while IFS='=' read -r key value; do
    ENV_ARGS+=(-e "$key=$value")
  done < <(jq -r '.env | to_entries[] | "\(.key)=\(.value)"' "$SETTINGS")

  GH_TOKEN=$(gh auth token 2>/dev/null) && ENV_ARGS+=(-e "GH_TOKEN=$GH_TOKEN")
}
