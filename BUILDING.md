# Building ACC

This document describes how to build ACC executables and installers for distribution.

## Prerequisites

### All Platforms
- Python 3.9+ (3.12 recommended)
- Git

### Windows
- Inno Setup 6.2.2+ (for creating installers)
- Visual C++ Build Tools (for some dependencies)

### macOS
- Xcode Command Line Tools
- Homebrew
- create-dmg: `brew install create-dmg`

### Linux
- Qt5 development packages
- AppImage tools (linuxdeploy, appimagetool)

## Quick Start

### Local Build

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
python build.py
```

The executable will be created in `dist/ACC/`.

### Windows Installer

```bash
# Install Inno Setup from https://jrsoftware.org/isinfo.php
# Then run:
python build.py
```

The installer will be created in `InnoSetup/Output/`.

### macOS DMG

```bash
# Install create-dmg
brew install create-dmg

# Build
python build.py

# The workflow will package it into a DMG
```

### Linux AppImage

```bash
# Install tools
curl -LO https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
curl -LO https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage appimagetool-x86_64.AppImage
sudo mv linuxdeploy-x86_64.AppImage /usr/local/bin/linuxdeploy
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool

# Build
python build.py
packaging/linux/create_appimage.sh v0.1.0-build1
```

## GitHub Actions CI/CD

### Automatic Builds

Builds are automatically triggered on:
- **Tag push**: Creates a GitHub Release with installers
- **Manual trigger**: Via GitHub Actions UI

### Manual Build

1. Go to GitHub Actions
2. Select "Manual Build" workflow
3. Click "Run workflow"
4. Optionally specify a build number

### Creating a Release

1. Update version in `version.py`:
   ```python
   __version__ = "0.2.0"
   ```

2. Commit and push:
   ```bash
   git add version.py
   git commit -m "Bump version to 0.2.0"
   git push
   ```

3. Create and push tag:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. GitHub Actions will automatically:
   - Run tests
   - Build for Windows, macOS, and Linux
   - Create SHA256 checksums
   - Create GitHub Release with all artifacts

## Build Outputs

### Windows
- `ACC-Windows-Installer-vX.X.X-buildN.zip`
  - Contains: `ACC_vX.X.X_buildN_Installer.exe`
- `ACC-Windows-Portable-vX.X.X-buildN.zip` (if installer fails)
  - Contains: Portable application directory

### macOS
- `ACC-macOS-Installer-vX.X.X-buildN.dmg`
  - Drag-and-drop installer

### Linux
- `ACC-Linux-vX.X.X-buildN.AppImage`
  - Self-contained executable

## Build Configuration

### version.py
```python
__version__ = "0.1.0"  # Semantic versioning
__app_name__ = "ACC"
__author__ = "jikhanjung"
```

### build.py
Main build script that:
- Runs PyInstaller with appropriate flags
- Creates build_info.json with version/build metadata
- Triggers platform-specific packaging

### InnoSetup/ACC.iss.template
Windows installer configuration:
- Installation directory: `%APPDATA%\ACC`
- Start Menu shortcuts
- Desktop icon (optional)
- Uninstaller

## Troubleshooting

### PyInstaller Issues

**Problem**: Missing modules in built executable
```bash
# Add hidden imports
pyinstaller --hidden-import=module_name ...
```

**Problem**: Large executable size
```bash
# Use UPX compression (install UPX first)
pyinstaller --upx-dir=/path/to/upx ...
```

### Windows Installer Issues

**Problem**: Antivirus false positives
- Use conservative compression (already set in template)
- Submit to antivirus vendors for whitelisting
- Code sign the executable (requires certificate)

### macOS Signing

To distribute outside of App Store:
```bash
# Get Developer ID certificate
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID" ACC.app
```

### Linux AppImage Issues

**Problem**: Missing libraries
- Add required libraries to AppDir/usr/lib
- Update create_appimage.sh to copy dependencies

## Version Management

ACC uses semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Pre-release versions:
- `v0.1.0-alpha.1`: Alpha release
- `v0.1.0-beta.1`: Beta release
- `v0.1.0-rc.1`: Release candidate

## Build Number

Build numbers are automatically assigned by GitHub Actions:
- Local builds: "local"
- CI builds: GitHub run number

## Advanced Topics

### Custom PyInstaller Spec File

For advanced customization, modify the spec file:
```bash
pyi-makespec --onedir --windowed acc_gui.py
# Edit ACC.spec
pyinstaller ACC.spec
```

### Code Signing

#### Windows (Authenticode)
```bash
signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com ACC.exe
```

#### macOS (Developer ID)
```bash
codesign --sign "Developer ID Application: Your Name" ACC.app
```

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [Inno Setup Documentation](https://jrsoftware.org/isinfo.php)
- [AppImage Documentation](https://docs.appimage.org/)
- [GitHub Actions Documentation](https://docs.github.com/actions)

## Support

For build issues, please:
1. Check this documentation
2. Review GitHub Actions logs
3. Open an issue on GitHub
