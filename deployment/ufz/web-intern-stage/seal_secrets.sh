#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_DIR="${SECRETS_DIR:-${SCRIPT_DIR}/secrets}"
TEMPLATES_DIR="${TEMPLATES_DIR:-${SCRIPT_DIR}/templates}"
PUBKEY_FILE="${PUBKEY_FILE:-${SCRIPT_DIR}/sealedsecret_pubkey/pub.pem}"
KUBESEAL_BIN="${KUBESEAL_BIN:-kubeseal}"

log() {
  printf '[seal_secrets] %s\n' "$*"
}

fail() {
  printf '[seal_secrets] ERROR: %s\n' "$*" >&2
  exit 1
}

command -v "$KUBESEAL_BIN" >/dev/null 2>&1 || fail "kubeseal not found: ${KUBESEAL_BIN}"
[[ -d "$SECRETS_DIR" ]] || fail "secrets directory not found: ${SECRETS_DIR}"
[[ -d "$TEMPLATES_DIR" ]] || fail "templates directory not found: ${TEMPLATES_DIR}"
[[ -f "$PUBKEY_FILE" ]] || fail "public key not found: ${PUBKEY_FILE}"

shopt -s nullglob

input_files=(
  "$SECRETS_DIR"/*.yaml
  "$SECRETS_DIR"/*.yml
  "$SECRETS_DIR"/*.json
)

if [[ ${#input_files[@]} -eq 0 ]]; then
  log "no secret manifests found in ${SECRETS_DIR}"
  exit 0
fi

sealed_count=0

for input_file in "${input_files[@]}"; do
  [[ -f "$input_file" ]] || continue

  output_file="${TEMPLATES_DIR}/$(basename "$input_file")"

  if ! grep -Eq '^kind:[[:space:]]+Secret([[:space:]]*)$' "$input_file"; then
	fail "input file is not a Kubernetes Secret manifest: ${input_file}"
  fi

  log "sealing $(basename "$input_file") -> ${output_file}"
  "$KUBESEAL_BIN" \
	--cert "$PUBKEY_FILE" \
	--format yaml \
	< "$input_file" \
	> "$output_file"

  sealed_count=$((sealed_count + 1))
done

log "done; sealed ${sealed_count} secret manifest(s)"

