#!/usr/bin/env bash
# VibePad Schism Linux Debian Package (.deb) Build Script.
#
# Copyright (C) 2026 OpenPrism-Qt Team
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🔨 Building VibePad Schism Linux PyInstaller Bundle..."

python3 -m PyInstaller \
    --name="vibepad-schism" \
    --onedir \
    --windowed \
    --add-data="src/ui/logo.png:src/ui" \
    --hidden-import="scipy.special.cython_special" \
    --hidden-import="scipy.stats" \
    --hidden-import="statsmodels.stats.anova" \
    --hidden-import="statsmodels.api" \
    --hidden-import="pyqtgraph" \
    --hidden-import="PyQt6" \
    --clean \
    --noconfirm \
    src/main.py

STAGING_DIR="dist/deb_staging"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}/DEBIAN"
mkdir -p "${STAGING_DIR}/opt/vibepad-schism"
mkdir -p "${STAGING_DIR}/usr/share/applications"
mkdir -p "${STAGING_DIR}/usr/share/pixmaps"
mkdir -p "${STAGING_DIR}/usr/bin"

echo "📂 Staging Debian Package File Layout..."

cp -r dist/vibepad-schism/* "${STAGING_DIR}/opt/vibepad-schism/"
cp src/ui/logo.png "${STAGING_DIR}/usr/share/pixmaps/vibepad-schism.png"

ln -sf /opt/vibepad-schism/vibepad-schism "${STAGING_DIR}/usr/bin/vibepad-schism"

cat << 'EOF' > "${STAGING_DIR}/DEBIAN/control"
Package: vibepad-schism
Version: 1.0.0
Section: science
Priority: optional
Architecture: amd64
Maintainer: OpenPrism-Qt Team <support@openprism.org>
Description: VibePad Schism Scientific Analysis & Graphing Desktop Suite
 Open-source desktop scientific spreadsheet, 4PL curve fitting, Two-Way ANOVA,
 Kaplan-Meier survival analysis, and vector plotting application.
EOF

cat << 'EOF' > "${STAGING_DIR}/usr/share/applications/vibepad-schism.desktop"
[Desktop Entry]
Name=VibePad Schism
Comment=Scientific Data Analysis and Curve Fitting Desktop Suite
Exec=/opt/vibepad-schism/vibepad-schism
Icon=vibepad-schism
Terminal=false
Type=Application
Categories=Science;Education;DataVisualization;
Keywords=scientific;graphing;anova;survival;curve-fitting;
EOF

chmod 755 "${STAGING_DIR}/DEBIAN/control"
chmod 755 "${STAGING_DIR}/usr/share/applications/vibepad-schism.desktop"

echo "📦 Compiling .deb package via dpkg-deb..."
dpkg-deb --build --root-owner-group "${STAGING_DIR}" "dist/vibepad-schism_1.0.0_amd64.deb"

echo "✅ Linux .deb package successfully created at: dist/vibepad-schism_1.0.0_amd64.deb"
