"""Build script for MoonJoy — Windows, macOS, and Linux."""
# Run: python build.py [platform]
# Requires: pip install pyinstaller

import os
import platform
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(PROJECT_DIR, "Images")

def build(target_platform: str | None = None):
    if target_platform is None:
        target_platform = platform.system().lower()

    print(f"Building MoonJoy for {target_platform}...")
    print(f"Project: {PROJECT_DIR}")
    print(f"Images:  {IMAGES_DIR}")

    # Common PyInstaller args
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "MoonJoy",
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
        # Add the Images directory as data
        "--add-data", f"{IMAGES_DIR}{os.pathsep}Images",
        # Entry point
        os.path.join(PROJECT_DIR, "moonjoy", "__main__.py"),
    ]

    # Icon per platform
    icon_path = os.path.join(PROJECT_DIR, "assets", "icon")
    if target_platform == "windows" and os.path.isfile(icon_path + ".ico"):
        args.extend(["--icon", icon_path + ".ico"])
    elif target_platform == "darwin" and os.path.isfile(icon_path + ".icns"):
        args.extend(["--icon", icon_path + ".icns"])
    elif os.path.isfile(icon_path + ".png"):
        args.extend(["--icon", icon_path + ".png"])

    # Platform-specific
    if target_platform == "windows":
        # Build as .scr (screensaver) — it's just a renamed .exe
        args.extend(["--distpath", os.path.join(PROJECT_DIR, "dist", "windows")])
    elif target_platform == "darwin":
        args.extend([
            "--distpath", os.path.join(PROJECT_DIR, "dist", "macos"),
            "--osx-bundle-identifier", "com.moonjoy.screensaver",
        ])
    else:
        args.extend(["--distpath", os.path.join(PROJECT_DIR, "dist", "linux")])

    print(f"\nRunning: {' '.join(args)}\n")
    result = subprocess.run(args)

    if result.returncode != 0:
        print(f"\nBuild failed with code {result.returncode}")
        sys.exit(result.returncode)

    # Post-build steps
    if target_platform == "windows":
        _post_build_windows()
    elif target_platform == "darwin":
        _post_build_macos()
    else:
        _post_build_linux()

    print("\nBuild complete!")


def _post_build_windows():
    """Create .scr copy and install script for Windows screensaver."""
    dist = os.path.join(PROJECT_DIR, "dist", "windows", "MoonJoy")
    exe = os.path.join(dist, "MoonJoy.exe")
    scr = os.path.join(dist, "MoonJoy.scr")

    if os.path.isfile(exe):
        import shutil
        shutil.copy2(exe, scr)
        print(f"  Created screensaver: {scr}")

    # Create install script
    install_bat = os.path.join(dist, "install_screensaver.bat")
    with open(install_bat, "w") as f:
        f.write('@echo off\n')
        f.write('echo Installing MoonJoy Screensaver...\n')
        f.write('copy /Y "%~dp0MoonJoy.scr" "%SystemRoot%\\System32\\MoonJoy.scr"\n')
        f.write('if exist "%~dp0Images" xcopy /E /I /Y "%~dp0Images" "%SystemRoot%\\System32\\Images"\n')
        f.write('echo.\n')
        f.write('echo MoonJoy Screensaver installed!\n')
        f.write('echo Right-click desktop > Personalize > Lock screen > Screen saver settings\n')
        f.write('echo Select "MoonJoy" from the list.\n')
        f.write('pause\n')
    print(f"  Created installer: {install_bat}")

    uninstall_bat = os.path.join(dist, "uninstall_screensaver.bat")
    with open(uninstall_bat, "w") as f:
        f.write('@echo off\n')
        f.write('echo Uninstalling MoonJoy Screensaver...\n')
        f.write('del /F "%SystemRoot%\\System32\\MoonJoy.scr" 2>nul\n')
        f.write('echo MoonJoy Screensaver uninstalled.\n')
        f.write('pause\n')
    print(f"  Created uninstaller: {uninstall_bat}")


def _post_build_macos():
    """Create macOS launcher scripts."""
    dist = os.path.join(PROJECT_DIR, "dist", "macos", "MoonJoy")

    # Create launch script
    launch = os.path.join(dist, "launch_screensaver.command")
    with open(launch, "w") as f:
        f.write('#!/bin/bash\n')
        f.write('cd "$(dirname "$0")"\n')
        f.write('./MoonJoy screensaver\n')
    os.chmod(launch, 0o755)

    launch_wp = os.path.join(dist, "start_wallpaper.command")
    with open(launch_wp, "w") as f:
        f.write('#!/bin/bash\n')
        f.write('cd "$(dirname "$0")"\n')
        f.write('./MoonJoy wallpaper &\n')
        f.write('echo "Wallpaper rotator started in background (PID $!)"\n')
        f.write('echo "Run: kill $! to stop"\n')
    os.chmod(launch_wp, 0o755)

    # Create launchd plist for wallpaper auto-start
    plist = os.path.join(dist, "com.moonjoy.wallpaper.plist")
    with open(plist, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n')
        f.write('  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
        f.write('<plist version="1.0">\n')
        f.write('<dict>\n')
        f.write('  <key>Label</key>\n')
        f.write('  <string>com.moonjoy.wallpaper</string>\n')
        f.write('  <key>ProgramArguments</key>\n')
        f.write('  <array>\n')
        f.write('    <string>/Applications/MoonJoy/MoonJoy</string>\n')
        f.write('    <string>wallpaper</string>\n')
        f.write('  </array>\n')
        f.write('  <key>RunAtLoad</key>\n')
        f.write('  <true/>\n')
        f.write('  <key>KeepAlive</key>\n')
        f.write('  <true/>\n')
        f.write('</dict>\n')
        f.write('</plist>\n')

    print(f"  Created launcher scripts and launchd plist")


def _post_build_linux():
    """Create Linux desktop entry and systemd service."""
    dist = os.path.join(PROJECT_DIR, "dist", "linux", "MoonJoy")

    # Desktop entry
    desktop = os.path.join(dist, "moonjoy.desktop")
    with open(desktop, "w") as f:
        f.write('[Desktop Entry]\n')
        f.write('Name=MoonJoy\n')
        f.write('Comment=NASA Image Screensaver & Wallpaper Rotator\n')
        f.write('Exec=/opt/moonjoy/MoonJoy gui\n')
        f.write('Type=Application\n')
        f.write('Categories=Utility;Graphics;\n')
        f.write('Terminal=false\n')

    # Systemd user service for wallpaper rotation
    service = os.path.join(dist, "moonjoy-wallpaper.service")
    with open(service, "w") as f:
        f.write('[Unit]\n')
        f.write('Description=MoonJoy Wallpaper Rotator\n')
        f.write('After=graphical-session.target\n')
        f.write('\n')
        f.write('[Service]\n')
        f.write('Type=simple\n')
        f.write('ExecStart=/opt/moonjoy/MoonJoy wallpaper\n')
        f.write('Restart=on-failure\n')
        f.write('RestartSec=10\n')
        f.write('\n')
        f.write('[Install]\n')
        f.write('WantedBy=graphical-session.target\n')

    # Install script
    install_sh = os.path.join(dist, "install.sh")
    with open(install_sh, "w") as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')
        f.write('echo "Installing MoonJoy..."\n')
        f.write('sudo mkdir -p /opt/moonjoy\n')
        f.write('sudo cp -r "$(dirname "$0")"/* /opt/moonjoy/\n')
        f.write('sudo chmod +x /opt/moonjoy/MoonJoy\n')
        f.write('\n')
        f.write('# Desktop entry\n')
        f.write('cp /opt/moonjoy/moonjoy.desktop ~/.local/share/applications/ 2>/dev/null || true\n')
        f.write('\n')
        f.write('# Wallpaper service (optional)\n')
        f.write('mkdir -p ~/.config/systemd/user/\n')
        f.write('cp /opt/moonjoy/moonjoy-wallpaper.service ~/.config/systemd/user/\n')
        f.write('echo ""\n')
        f.write('echo "MoonJoy installed to /opt/moonjoy/"\n')
        f.write('echo ""\n')
        f.write('echo "Run:  /opt/moonjoy/MoonJoy gui          — Settings"\n')
        f.write('echo "Run:  /opt/moonjoy/MoonJoy screensaver  — Screensaver"\n')
        f.write('echo "Run:  /opt/moonjoy/MoonJoy wallpaper    — Wallpaper rotator"\n')
        f.write('echo ""\n')
        f.write('echo "To auto-start wallpaper rotation:"\n')
        f.write('echo "  systemctl --user enable moonjoy-wallpaper"\n')
        f.write('echo "  systemctl --user start moonjoy-wallpaper"\n')
    os.chmod(install_sh, 0o755)

    print(f"  Created desktop entry, systemd service, and install script")


if __name__ == "__main__":
    target = sys.argv[1].lower() if len(sys.argv) > 1 else None
    build(target)
