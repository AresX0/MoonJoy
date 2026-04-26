"""Background wallpaper rotator daemon."""

import os
import signal
import sys
import time

from moonjoy.config import _config_path, load_config
from moonjoy.image_scanner import scan_images
from moonjoy.wallpaper import set_wallpaper


def _lock_path() -> str:
    return os.path.join(os.path.dirname(_config_path()), "wallpaper_daemon.pid")


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _acquire_lock() -> tuple[int, str] | tuple[None, str]:
    """Acquire a simple single-instance lock file for the wallpaper daemon."""
    lock_path = _lock_path()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            return fd, lock_path
        except FileExistsError:
            try:
                with open(lock_path, "r", encoding="utf-8") as handle:
                    existing_pid = int(handle.read().strip() or "0")
            except (OSError, ValueError):
                existing_pid = 0

            if existing_pid and _pid_exists(existing_pid):
                return None, lock_path

            try:
                os.remove(lock_path)
            except OSError:
                return None, lock_path


def run_wallpaper_daemon(quiet: bool = False) -> int:
    """Rotate desktop wallpaper at the configured interval."""
    lock_fd, lock_path = _acquire_lock()
    if lock_fd is None:
        if not quiet:
            print("MoonJoy wallpaper rotator is already running.")
        return 0

    config = load_config()
    from moonjoy.image_scanner import get_images_dir
    images_dir = get_images_dir(config.get("images_dir", ""))
    images = scan_images(images_dir=images_dir, shuffle=config.get("shuffle", True))

    def log(message: str = ""):
        if not quiet:
            print(message)

    if not images:
        log(f"No images found in: {images_dir}")
        os.close(lock_fd)
        try:
            os.remove(lock_path)
        except OSError:
            pass
        return 1

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

    log("MoonJoy Wallpaper Rotator")
    log(f"  Found {len(images)} images")
    log(f"  Changing every {interval} seconds")
    log(f"  Fit mode: {fit_mode}")
    log(f"  Overlay: {'on' if overlay_lines else 'off'}")
    log(f"  Lock screen: {'on' if set_lockscreen else 'off'}")
    log("  Press Ctrl+C to stop\n")

    # Graceful shutdown
    running = True

    def _stop(signum, frame):
        nonlocal running
        running = False
        log("\nStopping wallpaper rotator...")

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    idx = 0
    overlay_page = 0
    shuffle = config.get("shuffle", True)
    while running:
        # Once we've shown every image, rescan & reshuffle for a fresh cycle
        if idx >= len(images):
            images = scan_images(images_dir=images_dir, shuffle=shuffle)
            if not images:
                log("  No images found, stopping.")
                break
            idx = 0
            log(f"  Completed full cycle — reshuffled {len(images)} images")

        path = images[idx]
        success = set_wallpaper(path, fit_mode,
                                overlay_lines=overlay_lines,
                                overlay_opacity=overlay_opacity,
                                set_lockscreen=set_lockscreen,
                                overlay_page=overlay_page)
        if success:
            log(f"  [{idx+1}/{len(images)}] Wallpaper: {path}")
        else:
            log(f"  [{idx+1}/{len(images)}] Failed: {path}")

        idx += 1
        overlay_page += 1

        # Sleep in small increments so we can respond to signals
        elapsed = 0.0
        while running and elapsed < interval:
            time.sleep(min(1.0, interval - elapsed))
            elapsed += 1.0

    log("Wallpaper rotator stopped.")
    os.close(lock_fd)
    try:
        os.remove(lock_path)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(run_wallpaper_daemon())
