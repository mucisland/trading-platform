#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[bootstrap] repository root: $ROOT_DIR"

echo "[bootstrap] TODO: verify required system tools"
echo "[bootstrap] TODO: create virtual environment if missing"
echo "[bootstrap] TODO: install pinned dependencies"
echo "[bootstrap] TODO: prepare config templates and local directories"

echo "[bootstrap] next step: ./scripts/session_init.sh && ./scripts/verify_env.sh"
