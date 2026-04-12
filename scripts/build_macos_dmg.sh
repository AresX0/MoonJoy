#!/usr/bin/env bash
# build_macos_dmg.sh — Build a .dmg installer for MoonJoy on macOS
set -e

APP_NAME="MoonJoy"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}-macOS"

echo "=== Building MoonJoy macOS .dmg ==="

# Step 1: Build with PyInstaller
echo "[1/3] Building app with PyInstaller..."
python3 -m PyInstaller \
    --name "$APP_NAME" \
    --onedir \
    --windowed \
    --noconfirm \
    --clean \
    --osx-bundle-identifier "com.moonjoy.app" \
    --distpath dist/macos \
    moonjoy/__main__.py

# Step 2: Create DMG staging area
echo "[2/3] Staging DMG contents..."
STAGING="dist/dmg_staging"
rm -rf "$STAGING"
mkdir -p "$STAGING"

# Copy app bundle
if [ -d "dist/macos/${APP_NAME}.app" ]; then
    cp -r "dist/macos/${APP_NAME}.app" "$STAGING/"
else
    # Create a basic .app wrapper if PyInstaller didn't make one
    APP_BUNDLE="$STAGING/${APP_NAME}.app"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"
    cp -r dist/macos/${APP_NAME}/* "$APP_BUNDLE/Contents/MacOS/"

    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.moonjoy.app</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
fi

# Add convenience symlink to Applications
ln -sf /Applications "$STAGING/Applications"

# Step 3: Create DMG
echo "[3/3] Creating DMG..."
DMG_PATH="dist/${DMG_NAME}.dmg"
rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -ov -format UDZO "$DMG_PATH"

echo "Done! DMG: $DMG_PATH"
