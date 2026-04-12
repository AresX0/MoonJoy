#!/usr/bin/env bash
# build_linux_deb.sh — Build a .deb package for MoonJoy on Debian/Ubuntu
set -e

APP_NAME="moonjoy"
VERSION="1.0.0"
ARCH="amd64"
MAINTAINER="Platysoft <info@platysoft.com>"
DESCRIPTION="NASA Image Screensaver & Wallpaper Rotator with Artemis Mission Data"
PKG_DIR="dist/${APP_NAME}_${VERSION}_${ARCH}"
INSTALL_PREFIX="/opt/moonjoy"

echo "=== Building MoonJoy .deb package ==="

# Step 1: Build with PyInstaller
echo "[1/4] Building binary with PyInstaller..."
python3 -m PyInstaller \
    --name MoonJoy \
    --onedir \
    --windowed \
    --noconfirm \
    --clean \
    --distpath dist/linux \
    moonjoy/__main__.py

# Step 2: Create .deb directory structure
echo "[2/4] Creating .deb package structure..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/moonjoy"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/bin"

# Copy built files
cp -r dist/linux/MoonJoy/* "$PKG_DIR/opt/moonjoy/"

# Step 3: Create control file
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-tk
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 MoonJoy is a cross-platform screensaver and wallpaper rotator featuring
 NASA Artemis mission images with live mission data overlay.
EOF

# Post-install script
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
chmod +x /opt/moonjoy/MoonJoy
ln -sf /opt/moonjoy/MoonJoy /usr/bin/moonjoy
echo "MoonJoy installed! Run 'moonjoy gui' or 'moonjoy screensaver'"
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Pre-remove script
cat > "$PKG_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
rm -f /usr/bin/moonjoy
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/moonjoy.desktop" << EOF
[Desktop Entry]
Name=MoonJoy
Comment=NASA Image Screensaver & Wallpaper Rotator
Exec=/opt/moonjoy/MoonJoy gui
Type=Application
Categories=Utility;Graphics;
Terminal=false
StartupNotify=true
EOF

# Symlink
mkdir -p "$PKG_DIR/usr/bin"

# Step 4: Build .deb
echo "[3/4] Building .deb..."
dpkg-deb --build --root-owner-group "$PKG_DIR"

DEB_FILE="dist/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo "[4/4] Done! Package: $DEB_FILE"
echo ""
echo "Install with:  sudo dpkg -i $DEB_FILE"
echo "Remove with:   sudo dpkg -r $APP_NAME"
