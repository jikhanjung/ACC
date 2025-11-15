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

# Create desktop file
echo "Creating desktop entry..."
cat > "$APPDIR/usr/share/applications/ACC.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ACC
Comment=Area Affinity in Concentric Circles
Exec=ACC
Icon=ACC
Categories=Science;Education;DataVisualization;
Terminal=false
EOF

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

# Copy icon if it exists (placeholder for now)
# If you have an icon file, uncomment and adjust:
# cp images/acc_icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/ACC.png"
# ln -s usr/share/icons/hicolor/256x256/apps/ACC.png "$APPDIR/ACC.png"

# Create a simple icon placeholder if no icon exists
if [ ! -f "$APPDIR/ACC.png" ]; then
    echo "No icon found, using placeholder"
    # You can add icon later
    touch "$APPDIR/ACC.png"
fi

# Build AppImage
echo "Building AppImage..."
cd build_linux
ARCH=x86_64 appimagetool AppDir "ACC-Linux-$VERSION_TAG.AppImage"

echo "=== AppImage created successfully ==="
echo "Location: build_linux/ACC-Linux-$VERSION_TAG.AppImage"
