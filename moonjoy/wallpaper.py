"""Cross-platform desktop wallpaper setter."""

import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile

from PIL import Image


def _prepare_image(image_path: str, fit_mode: str = "fit") -> str:
    """Convert image to a format the OS can use as wallpaper (BMP on Windows, PNG elsewhere).
    Returns the path to the prepared file."""
    # Determine target format
    if sys.platform == "win32":
        ext = ".bmp"
        fmt = "BMP"
    else:
        ext = ".png"
        fmt = "PNG"

    tmp_dir = os.path.join(tempfile.gettempdir(), "moonjoy_wallpaper")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"wallpaper{ext}")

    img = Image.open(image_path)
    img = img.convert("RGB")

    # Get screen size approximation (used for fit modes)
    try:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            sw, sh = 1920, 1080  # reasonable default
    except Exception:
        sw, sh = 1920, 1080

    if fit_mode == "fill":
        img = _fill(img, sw, sh)
    elif fit_mode == "fit":
        img = _fit(img, sw, sh)
    elif fit_mode == "stretch":
        img = img.resize((sw, sh), Image.LANCZOS)
    # "center" - leave as-is

    img.save(tmp_path, fmt)
    return tmp_path


def _fit(img: Image.Image, sw: int, sh: int) -> Image.Image:
    """Scale to fit within screen, centered on black background."""
    img.thumbnail((sw, sh), Image.LANCZOS)
    bg = Image.new("RGB", (sw, sh), (0, 0, 0))
    x = (sw - img.width) // 2
    y = (sh - img.height) // 2
    bg.paste(img, (x, y))
    return bg


def _fill(img: Image.Image, sw: int, sh: int) -> Image.Image:
    """Scale to fill screen, cropping excess."""
    ratio = max(sw / img.width, sh / img.height)
    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - sw) // 2
    top = (new_h - sh) // 2
    return img.crop((left, top, left + sw, top + sh))


def set_wallpaper(image_path: str, fit_mode: str = "fit") -> bool:
    """Set the desktop wallpaper. Returns True on success."""
    try:
        prepared = _prepare_image(image_path, fit_mode)
    except Exception as e:
        print(f"Failed to prepare image: {e}")
        return False

    system = platform.system()

    try:
        if system == "Windows":
            return _set_wallpaper_windows(prepared)
        elif system == "Darwin":
            return _set_wallpaper_macos(prepared)
        elif system == "Linux":
            return _set_wallpaper_linux(prepared)
        else:
            print(f"Unsupported platform: {system}")
            return False
    except Exception as e:
        print(f"Failed to set wallpaper: {e}")
        return False


def _set_wallpaper_windows(path: str) -> bool:
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02
    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    return bool(result)


def _set_wallpaper_macos(path: str) -> bool:
    script = f'''
    tell application "System Events"
        tell every desktop
            set picture to "{path}"
        end tell
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0


def _set_wallpaper_linux(path: str) -> bool:
    """Try multiple Linux desktop environment methods."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    # GNOME / Unity / Budgie / Pop!_OS
    if any(d in desktop for d in ("gnome", "unity", "budgie", "pop")):
        result = subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri",
             f"file://{path}"],
            capture_output=True, timeout=10
        )
        # Also set for dark mode on newer GNOME
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark",
             f"file://{path}"],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # KDE Plasma
    if "kde" in desktop or "plasma" in desktop:
        script = f"""
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {{
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", "file://{path}");
}}
"""
        result = subprocess.run(
            ["qdbus", "org.kde.plasmashell", "/PlasmaShell",
             "org.kde.PlasmaShell.evaluateScript", script],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # XFCE
    if "xfce" in desktop:
        result = subprocess.run(
            ["xfconf-query", "-c", "xfce4-desktop", "-p",
             "/backdrop/screen0/monitor0/workspace0/last-image", "-s", path],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # MATE
    if "mate" in desktop:
        result = subprocess.run(
            ["gsettings", "set", "org.mate.background", "picture-filename", path],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # Cinnamon
    if "cinnamon" in desktop:
        result = subprocess.run(
            ["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri",
             f"file://{path}"],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # Fallback: try feh (common on i3, bspwm, etc.)
    if shutil.which("feh"):
        result = subprocess.run(
            ["feh", "--bg-fill", path],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    # Fallback: try nitrogen
    if shutil.which("nitrogen"):
        result = subprocess.run(
            ["nitrogen", "--set-zoom-fill", "--save", path],
            capture_output=True, timeout=10
        )
        return result.returncode == 0

    print("Could not detect desktop environment for wallpaper setting")
    return False
