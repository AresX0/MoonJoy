"""Background wallpaper rotator daemon."""

import signal
import sys
import time

from moonjoy.config import load_config
from moonjoy.image_scanner import scan_images
from moonjoy.wallpaper import set_wallpaper


def run_wallpaper_daemon():
    """Rotate desktop wallpaper at the configured interval."""
    config = load_config()
    from moonjoy.image_scanner import get_images_dir
    images_dir = get_images_dir(config.get("images_dir", ""))
    images = scan_images(images_dir=images_dir, shuffle=config.get("shuffle", True))

    if not images:
        print(f"No images found in: {images_dir}")
        sys.exit(1)

    interval = config.get("wallpaper_interval", 300)
    fit_mode = config.get("fit_mode", "fit")

    print(f"MoonJoy Wallpaper Rotator")
    print(f"  Found {len(images)} images")
    print(f"  Changing every {interval} seconds")
    print(f"  Fit mode: {fit_mode}")
    print(f"  Press Ctrl+C to stop\n")

    # Graceful shutdown
    running = True
    def _stop(signum, frame):
        nonlocal running
        running = False
        print("\nStopping wallpaper rotator...")

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    idx = 0
    while running:
        path = images[idx % len(images)]
        success = set_wallpaper(path, fit_mode)
        if success:
            print(f"  Wallpaper: {path}")
        else:
            print(f"  Failed: {path}")

        idx += 1

        # Sleep in small increments so we can respond to signals
        elapsed = 0.0
        while running and elapsed < interval:
            time.sleep(min(1.0, interval - elapsed))
            elapsed += 1.0

    print("Wallpaper rotator stopped.")


if __name__ == "__main__":
    run_wallpaper_daemon()
