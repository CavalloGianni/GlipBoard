#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${HOME}/.local/share/glipboard"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${APPLICATIONS_DIR}/glipboard.desktop"
LAUNCHER_PATH="${APP_DIR}/run-glipboard.sh"
ICON_PATH=""

if [[ -f "${PROJECT_DIR}/image (2).png" ]]; then
  ICON_PATH="${PROJECT_DIR}/image (2).png"
fi

mkdir -p "${APP_DIR}" "${APPLICATIONS_DIR}"

cat > "${LAUNCHER_PATH}" <<EOF
#!/usr/bin/env bash
cd "${PROJECT_DIR}"
exec python3 gtk_app.py
EOF

chmod +x "${LAUNCHER_PATH}"

{
  echo "[Desktop Entry]"
  echo "Type=Application"
  echo "Version=1.0"
  echo "Name=GlipBoard"
  echo "Comment=Clipboard manager for Pop!_OS"
  echo "Exec=${LAUNCHER_PATH}"
  echo "Terminal=false"
  echo "Categories=Utility;"
  if [[ -n "${ICON_PATH}" ]]; then
    echo "Icon=${ICON_PATH}"
  fi
  echo "StartupNotify=true"
} > "${DESKTOP_FILE}"

chmod +x "${DESKTOP_FILE}"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APPLICATIONS_DIR}" >/dev/null 2>&1 || true
fi

echo "GlipBoard installato localmente."
echo "Launcher desktop: ${DESKTOP_FILE}"
