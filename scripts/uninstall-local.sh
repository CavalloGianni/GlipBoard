#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${HOME}/.local/share/glipboard"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${APPLICATIONS_DIR}/glipboard.desktop"

rm -f "${DESKTOP_FILE}"
rm -rf "${APP_DIR}"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APPLICATIONS_DIR}" >/dev/null 2>&1 || true
fi

echo "GlipBoard rimosso dall'installazione locale."
