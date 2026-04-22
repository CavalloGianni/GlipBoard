#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_NAME="glipboard"
VERSION="$(sed -n 's/.*"version": "\([^"]*\)".*/\1/p' "${PROJECT_DIR}/package.json" | head -n 1)"
DESCRIPTION="$(sed -n 's/.*"description": "\([^"]*\)".*/\1/p' "${PROJECT_DIR}/package.json" | head -n 1)"
DIST_DIR="${PROJECT_DIR}/dist"
BUILD_DIR="${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_build"
DEB_PATH="${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"
APP_DIR="${BUILD_DIR}/usr/share/glipboard"
ICON_DIR="${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps"
APPLICATIONS_DIR="${BUILD_DIR}/usr/share/applications"
BIN_DIR="${BUILD_DIR}/usr/bin"
DEBIAN_DIR="${BUILD_DIR}/DEBIAN"

if [[ -z "${VERSION}" ]]; then
  echo "Impossibile leggere la versione da package.json" >&2
  exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb non trovato. Installa dpkg prima di costruire il pacchetto." >&2
  exit 1
fi

rm -rf "${BUILD_DIR}"
mkdir -p "${APP_DIR}/scripts" "${ICON_DIR}" "${APPLICATIONS_DIR}" "${BIN_DIR}" "${DEBIAN_DIR}" "${DIST_DIR}"

install -m 0644 "${PROJECT_DIR}/gtk_app.py" "${APP_DIR}/gtk_app.py"
install -m 0644 "${PROJECT_DIR}/tray_helper.py" "${APP_DIR}/tray_helper.py"
install -m 0644 "${PROJECT_DIR}/README.md" "${APP_DIR}/README.md"
install -m 0644 "${PROJECT_DIR}/logo.2816x1536.png" "${APP_DIR}/logo.2816x1536.png"
install -m 0755 "${PROJECT_DIR}/scripts/wl-watch-event.sh" "${APP_DIR}/scripts/wl-watch-event.sh"
install -m 0644 "${PROJECT_DIR}/logo.2816x1536.png" "${ICON_DIR}/glipboard.png"

cat > "${BIN_DIR}/glipboard" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/share/glipboard/gtk_app.py
EOF

cat > "${APPLICATIONS_DIR}/glipboard.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=GlipBoard
Comment=Clipboard manager for Pop!_OS
Exec=glipboard
Icon=glipboard
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

cat > "${DEBIAN_DIR}/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: Gianni Cavallo <noreply@example.com>
Depends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1, wl-clipboard, gir1.2-ayatanaappindicator3-0.1
Description: ${DESCRIPTION}
 GlipBoard is a clipboard manager for Pop!_OS built with Python GTK4/libadwaita.
EOF

cat > "${DEBIAN_DIR}/postinst" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
EOF

cat > "${DEBIAN_DIR}/postrm" <<'EOF'
#!/usr/bin/env bash
set -e

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
EOF

chmod 0755 "${BIN_DIR}/glipboard" "${DEBIAN_DIR}/postinst" "${DEBIAN_DIR}/postrm"

dpkg-deb --build "${BUILD_DIR}" "${DEB_PATH}" >/dev/null
rm -rf "${BUILD_DIR}"

echo "Pacchetto creato:"
echo "${DEB_PATH}"
