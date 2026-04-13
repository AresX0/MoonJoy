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
    wallpaper_overlay = config.get("wallpaper_overlay", True)
    overlay_opacity = config.get("overlay_opacity", 0.85)
    set_lockscreen = config.get("apply_to_lockscreen", True)

    # Pre-fetch overlay lines if overlay is enabled
    overlay_lines = None
    if wallpaper_overlay:
        try:
            from moonjoy.nasa_data import get_overlay_lines
            overlay_lines = get_overlay_lines(max_lines=12)
        except Exception:
            overlay_lines = None

    print(f"MoonJoy Wallpaper Rotator")
    print(f"  Found {len(images)} images")
    print(f"  Changing every {interval} seconds")
    print(f"  Fit mode: {fit_mode}")
    print(f"  Overlay: {'on' if overlay_lines else 'off'}")
    print(f"  Lock screen: {'on' if set_lockscreen else 'off'}")
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
    overlay_page = 0
    while running:
        path = images[idx % len(images)]
        success = set_wallpaper(path, fit_mode,
                                overlay_lines=overlay_lines,
                                overlay_opacity=overlay_opacity,
                                set_lockscreen=set_lockscreen,
                                overlay_page=overlay_page)
        if success:
            print(f"  Wallpaper: {path}")
        else:
            print(f"  Failed: {path}")

        idx += 1
        overlay_page += 1

        # Sleep in small increments so we can respond to signals
        elapsed = 0.0
        while running and elapsed < interval:
            time.sleep(min(1.0, interval - elapsed))
            elapsed += 1.0

    print("Wallpaper rotator stopped.")


if __name__ == "__main__":
    run_wallpaper_daemon()
