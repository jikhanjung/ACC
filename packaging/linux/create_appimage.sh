#!/bin/bash
set -e

# ACC AppImage Creation Script
# Usage: ./create_appimage.sh <version-tag>
# Example: ./create_appimage.sh v0.1.0-build1

if [ -z "$1" ]; then
    echo "Usage: $0 <version-tag>"
    echo "Example: $0 v0.1.0-build1"
    exit 1
fi

VERSION_TAG=$1
echo "Creating AppImage for ACC $VERSION_TAG"

# Create AppDir structure
APPDIR="build_linux/AppDir"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller output
echo "Copying ACC executable..."
if [ ! -d "dist/ACC" ]; then
    echo "ERROR: dist/ACC directory not found. Run build.py first."
    exit 1
fi

cp -r dist/ACC/* "$APPDIR/usr/bin/"

# Create desktop file in AppDir root (required by appimagetool)
echo "Creating desktop entry..."
cat > "$APPDIR/ACC.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ACC
Comment=Area Affinity in Concentric Circles - Hierarchical cluster visualization
Exec=ACC
Icon=ACC
Categories=Science;Education;DataVisualization;
Terminal=false
EOF

# Also copy to standard location
cp "$APPDIR/ACC.desktop" "$APPDIR/usr/share/applications/ACC.desktop"

# Create AppRun script
echo "Creating AppRun script..."
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec "${HERE}/usr/bin/ACC" "$@"
EOF

chmod +x "$APPDIR/AppRun"

# Create a simple PNG icon (1x1 transparent pixel)
echo "Creating placeholder icon..."
# Create a minimal 256x256 PNG icon using ImageMagick if available, or a 1x1 pixel fallback
if command -v convert &> /dev/null; then
    convert -size 256x256 xc:transparent "$APPDIR/ACC.png"
    cp "$APPDIR/ACC.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/ACC.png"
else
    # Minimal valid PNG (1x1 transparent pixel) - base64 encoded
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" | base64 -d > "$APPDIR/ACC.png"
    cp "$APPDIR/ACC.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/ACC.png"
fi

# Build AppImage
echo "Building AppImage..."
cd build_linux
ARCH=x86_64 appimagetool AppDir "ACC-Linux-$VERSION_TAG.AppImage"

echo "=== AppImage created successfully ==="
echo "Location: build_linux/ACC-Linux-$VERSION_TAG.AppImage"
