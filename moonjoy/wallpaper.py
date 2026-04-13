"""Cross-platform desktop wallpaper setter with optional NASA overlay."""

import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont


def _get_font(size: int, bold: bool = False):
    """Try to load a good monospace font, fall back to default."""
    font_names = [
        "consola.ttf", "consolab.ttf" if bold else "consola.ttf",
        "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            pass
    # System font paths
    if sys.platform == "win32":
        font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        for name in ["consola.ttf", "cour.ttf", "arial.ttf"]:
            path = os.path.join(font_dir, name)
            if os.path.isfile(path):
                try:
                    return ImageFont.truetype(path, size)
                except (OSError, IOError):
                    pass
    return ImageFont.load_default()


def burn_overlay(img: Image.Image, lines: list[str], opacity: float = 0.85) -> Image.Image:
    """Burn NASA text overlay onto the top-right corner of an image."""
    if not lines:
        return img

    img = img.convert("RGBA")
    w, h = img.size

    font = _get_font(max(11, h // 70))
    title_font = _get_font(max(13, h // 60), bold=True)

    # Measure text
    dummy = ImageDraw.Draw(img)
    padding = 16
    line_height = max(18, h // 50)
    max_text_w = 0
    for line in lines:
        f = title_font if line.startswith("═") else font
        bbox = dummy.textbbox((0, 0), line, font=f)
        max_text_w = max(max_text_w, bbox[2] - bbox[0])

    box_w = max_text_w + padding * 2
    box_h = len(lines) * line_height + padding * 2
    x_right = w - 20
    y_top = 20

    # Create overlay layer
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Semi-transparent background
    alpha = int(255 * opacity)
    draw.rectangle(
        [x_right - box_w, y_top, x_right, y_top + box_h],
        fill=(10, 10, 30, alpha),
        outline=(80, 120, 200, alpha),
        width=1,
    )

    # Draw text lines
    y = y_top + padding
    for line in lines:
        if line.startswith("═"):
            color = (79, 195, 247, 255)   # cyan titles
            f = title_font
        elif line.startswith("✓"):
            color = (102, 187, 106, 255)  # green completed
            f = font
        elif line.startswith("●"):
            color = (255, 167, 38, 255)   # orange active
            f = font
        elif line.startswith("◇"):
            color = (100, 181, 246, 255)  # blue upcoming
            f = font
        elif line.startswith("▸"):
            color = (186, 104, 200, 255)  # purple launches
            f = font
        elif "platysoft" in line.lower():
            color = (121, 134, 203, 255)  # indigo
            f = font
        else:
            color = (224, 224, 224, 255)  # white-ish
            f = font

        draw.text((x_right - box_w + padding, y), line, fill=color, font=f)
        y += line_height

    return Image.alpha_composite(img, overlay).convert("RGB")


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


def set_wallpaper(image_path: str, fit_mode: str = "fit",
                  overlay_lines: list[str] | None = None,
                  overlay_opacity: float = 0.85,
                  set_lockscreen: bool = False) -> bool:
    """Set the desktop wallpaper. Returns True on success."""
    try:
        prepared = _prepare_image(image_path, fit_mode)
    except Exception as e:
        print(f"Failed to prepare image: {e}")
        return False

    # Burn overlay onto the prepared wallpaper image if requested
    if overlay_lines:
        try:
            img = Image.open(prepared)
            img = burn_overlay(img, overlay_lines, overlay_opacity)
            img.save(prepared)
        except Exception as e:
            print(f"Failed to burn overlay: {e}")

    system = platform.system()

    try:
        if system == "Windows":
            ok = _set_wallpaper_windows(prepared)
            if ok and set_lockscreen:
                _set_lockscreen_windows(prepared)
            return ok
        elif system == "Darwin":
            return _set_wallpaper_macos(prepared)
        elif system == "Linux":
            ok = _set_wallpaper_linux(prepared)
            if ok and set_lockscreen:
                _set_lockscreen_linux(prepared)
            return ok
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


def _set_lockscreen_windows(path: str) -> bool:
    """Set Windows lock screen image via HKLM registry with UAC elevation."""
    lock_dir = os.path.join(tempfile.gettempdir(), "moonjoy_wallpaper")
    os.makedirs(lock_dir, exist_ok=True)
    lock_path = os.path.join(lock_dir, "lockscreen.jpg")
    try:
        img = Image.open(path)
        img.save(lock_path, "JPEG", quality=95)
    except Exception as e:
        print(f"  Lock screen: failed to prepare image: {e}")
        return False

    # Write a temp .ps1 script, then elevate it via Start-Process -Verb RunAs
    script_path = os.path.join(lock_dir, "set_lockscreen.ps1")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(f'$p = "{lock_path}"\n')
        f.write('$k = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PersonalizationCSP"\n')
        f.write('if (!(Test-Path $k)) { New-Item -Path $k -Force | Out-Null }\n')
        f.write('Set-ItemProperty -Path $k -Name LockScreenImageStatus -Value 1 -Type DWord\n')
        f.write('Set-ItemProperty -Path $k -Name LockScreenImagePath -Value $p -Type String\n')
        f.write('Set-ItemProperty -Path $k -Name LockScreenImageUrl -Value $p -Type String\n')

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script_path}\"' -Verb RunAs -Wait"],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  Lock screen failed: {e}")
        return False


def _set_lockscreen_linux(path: str) -> bool:
    """Set GNOME lock screen background."""
    try:
        result = subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.screensaver", "picture-uri",
             f"file://{path}"],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False
