#!/usr/bin/env bash
set -euo pipefail

APP_ID="dr-r"
APP_DISPLAY_NAME="Dr.R"
APP_COMMENT="RUIYI TECH 打造的锁定式临床科研浏览器"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist/${APP_ID}"
BUILD_DIR="${PROJECT_ROOT}/build"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[build_deb] 缺少依赖: $1" >&2
    echo "请先安装 PyInstaller / PyQt5 / PyQtWebEngine 等打包依赖，再重试" >&2
    echo "例如: pip install PyQt5 PyQtWebEngine pyinstaller" >&2
    exit 1
  fi
}

require_cmd pyinstaller
require_cmd dpkg-deb

python3 - "$PROJECT_ROOT" <<'PY'
import sys
from pathlib import Path

from branding_assets import write_dr_r_icon

project_root = Path(sys.argv[1])
write_dr_r_icon(project_root / 'dr-r-icon.png')
PY

VERSION_INPUT="${1:-}"
if [[ -z "${VERSION_INPUT}" ]]; then
  if VERSION_INPUT="$(python3 "${PROJECT_ROOT}/clinical-research-platform.py" --print-version)"; then
    :
  else
    VERSION_INPUT="1.0.0"
  fi
fi
VERSION="${VERSION_INPUT}"
PKG_ROOT="${BUILD_DIR}/${APP_ID}_${VERSION}_amd64"

rm -rf "${BUILD_DIR}"/tmp "${PKG_ROOT}"
mkdir -p "${BUILD_DIR}"

# 1. 构建可执行文件
pyinstaller "${PROJECT_ROOT}/clinical-research-platform.spec" --clean

# 2. 组装 Debian 目录结构
install -d "${PKG_ROOT}/DEBIAN"
install -d "${PKG_ROOT}/opt/${APP_ID}"
install -d "${PKG_ROOT}/usr/local/bin"
install -d "${PKG_ROOT}/usr/share/applications"
install -d "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps"

cp -r "${DIST_DIR}"/* "${PKG_ROOT}/opt/${APP_ID}/"
install -m 644 "${PROJECT_ROOT}/dr-r-icon.png" "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/${APP_ID}.png"

cat > "${PKG_ROOT}/usr/local/bin/${APP_ID}" <<'LAUNCHER'
#!/usr/bin/env bash
exec /opt/dr-r/dr-r "$@"
LAUNCHER
chmod +x "${PKG_ROOT}/usr/local/bin/${APP_ID}"

cat > "${PKG_ROOT}/usr/share/applications/${APP_ID}.desktop" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_DISPLAY_NAME}
Comment=${APP_COMMENT}
Exec=/usr/local/bin/${APP_ID}
Icon=${APP_ID}
Terminal=false
Categories=Utility;Medical;
StartupNotify=true
DESKTOP

cat > "${PKG_ROOT}/DEBIAN/control" <<CONTROL
Package: ${APP_ID}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: RUIYI TECH <support@ruiyitech.com>
Description: ${APP_COMMENT}
CONTROL

# 3. 打包
OUTPUT_DEB="${BUILD_DIR}/${APP_ID}_${VERSION}_amd64.deb"
dpkg-deb --build "${PKG_ROOT}" "${OUTPUT_DEB}"
echo "生成完成: ${OUTPUT_DEB}"
