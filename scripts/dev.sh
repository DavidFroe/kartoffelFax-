#!/usr/bin/env bash
# Local development helper for KartoffelFax.
# Usage: scripts/dev.sh {setup|test|lint|run}
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON="${VENV_DIR}/bin/python"

ensure_venv() {
  if [[ ! -x "${PYTHON}" ]]; then
    echo "Creating virtual environment at ${VENV_DIR} ..."
    python3 -m venv "${VENV_DIR}"
    "${PYTHON}" -m pip install --upgrade pip
  fi
}

cmd="${1:-}"
shift || true
case "${cmd}" in
  setup)
    ensure_venv
    echo "Installing project + dev dependencies ..."
    "${PYTHON}" -m pip install -e "${ROOT_DIR}[dev]"
    ;;
  test)
    ensure_venv
    "${PYTHON}" -m pytest "$@"
    ;;
  lint)
    ensure_venv
    "${PYTHON}" -m ruff check . "$@"
    ;;
  run)
    ensure_venv
    "${PYTHON}" -m uvicorn kartoffelfax.main:app --app-dir "${ROOT_DIR}/backend" --reload
    ;;
  *)
    echo "Usage: $0 {setup|test|lint|run}" >&2
    exit 1
    ;;
esac
