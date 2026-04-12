"""Recursively scan the Images directory for all image files."""

import os
import random

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}


def get_images_dir() -> str:
    """Return the path to the Images directory next to this package."""
    package_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(package_dir)
    images_dir = os.path.join(project_dir, "Images")
    if not os.path.isdir(images_dir):
        # When running from a frozen PyInstaller bundle
        if hasattr(os.sys, "_MEIPASS"):
            images_dir = os.path.join(os.sys._MEIPASS, "Images")
        if not os.path.isdir(images_dir):
            images_dir = os.path.join(os.getcwd(), "Images")
    return images_dir


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
