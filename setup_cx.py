"""cx_Freeze setup for building Windows MSI, macOS app, and Linux binaries."""

import sys
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["moonjoy", "PIL", "tkinter"],
    "excludes": ["unittest", "test", "pytest"],
    "include_files": [],  # Images are NOT bundled — users supply their own
}

# MSI-specific options
bdist_msi_options = {
    "upgrade_code": "{7A3B62D0-9F1E-4C8A-B5D2-MOONJOY00001}",
    "add_to_path": True,
    "initial_target_dir": r"[ProgramFiles64Folder]\MoonJoy",
    "all_users": False,
}

# macOS DMG options
bdist_dmg_options = {
    "volume_label": "MoonJoy",
    "applications_shortcut": True,
}

# Base: "Win32GUI" hides console on Windows for GUI apps
base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        script="moonjoy/__main__.py",
        base=base,
        target_name="MoonJoy",
        shortcut_name="MoonJoy",
        shortcut_dir="DesktopFolder",
        icon="assets/icon.ico" if sys.platform == "win32" else None,
    ),
]

setup(
    name="MoonJoy",
    version="1.0.0",
    description="NASA Image Screensaver & Wallpaper Rotator with Artemis Mission Data",
    author="Platysoft",
    author_email="info@platysoft.com",
    url="https://platysoft.com/",
    options={
        "build_exe": build_options,
        "bdist_msi": bdist_msi_options,
        "bdist_dmg": bdist_dmg_options,
    },
    executables=executables,
)
