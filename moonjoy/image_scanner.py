"""Recursively scan the Images directory for all image files."""

import os
import random
import sys

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}


def get_images_dir(config_dir: str = "") -> str:
    """Return the path to the Images directory.

    Search order:
    1. Explicit config_dir if provided
    2. Next to the running executable (frozen builds)
    3. Next to this package (development)
    4. Current working directory
    """
    if config_dir and os.path.isdir(config_dir):
        return config_dir

    candidates = []

    # Frozen exe: look next to the exe itself (e.g. C:\Program Files\Platysoft\MoonJoy\Images)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "Images"))

    # Development: next to the package
    package_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(package_dir)
    candidates.append(os.path.join(project_dir, "Images"))

    # Fallback: current working directory
    candidates.append(os.path.join(os.getcwd(), "Images"))

    for path in candidates:
        if os.path.isdir(path):
            return path

    # Return the first candidate even if it doesn't exist yet
    return candidates[0]


def scan_images(images_dir: str | None = None, shuffle: bool = True) -> list[str]:
    """Recursively find all image files under the images directory."""
    if images_dir is None:
        images_dir = get_images_dir()

    found = []
    for root, _dirs, files in os.walk(images_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                found.append(os.path.join(root, f))

    if shuffle:
        random.shuffle(found)
    return found
