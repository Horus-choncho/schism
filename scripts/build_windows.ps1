# VibePad Schism Windows Portable Distribution Build Script.
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

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Path $PSScriptRoot -Parent
Set-Location -Path $ProjectRoot

Write-Host "🔨 Building VibePad Schism Windows Executable..."

python -m PyInstaller `
    --name="VibePadSchism" `
    --onedir `
    --windowed `
    --icon="src/ui/logo.png" `
    --add-data="src/ui/logo.png;src/ui" `
    --hidden-import="scipy.special.cython_special" `
    --hidden-import="scipy.stats" `
    --hidden-import="statsmodels.stats.anova" `
    --hidden-import="statsmodels.api" `
    --hidden-import="pyqtgraph" `
    --hidden-import="PyQt6" `
    --clean `
    --noconfirm `
    src/main.py

$OutputDir = Join-Path $ProjectRoot "dist\VibePadSchism-Windows-Portable"
$ZipPath = Join-Path $ProjectRoot "dist\VibePadSchism-Windows-Portable.zip"

if (Test-Path -Path $OutputDir) {
    Remove-Item -Path $OutputDir -Recurse -Force
}
if (Test-Path -Path $ZipPath) {
    Remove-Item -Path $ZipPath -Force
}

Move-Item -Path (Join-Path $ProjectRoot "dist\VibePadSchism") -Destination $OutputDir

Write-Host "📦 Compressing Portable Package to ZIP Archive..."
Compress-Archive -Path "$OutputDir\*" -DestinationPath $ZipPath -Force

Write-Host "✅ Windows Portable Package successfully created at: $ZipPath"
