"""Configuration management for MoonJoy."""

import json
import os
import sys

CONFIG_FILENAME = "moonjoy_config.json"

DEFAULTS = {
    "slideshow_interval": 10,       # seconds between slides in screensaver
    "wallpaper_interval": 300,      # seconds between wallpaper changes (5 min)
    "transition": "fade",           # fade or cut
    "shuffle": True,
    "fit_mode": "fit",              # fit, fill, stretch, center
    "show_overlay": True,           # show NASA mission info overlay
    "overlay_opacity": 0.85,        # overlay background opacity
    "overlay_scroll_speed": 30,     # seconds per full scroll cycle
}


def _config_path() -> str:
    """Platform-appropriate config file location."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    config_dir = os.path.join(base, "MoonJoy")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, CONFIG_FILENAME)


def load_config() -> dict:
    """Load config from disk, falling back to defaults."""
    cfg = dict(DEFAULTS)
    path = _config_path()
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                saved = json.load(f)
                cfg.update(saved)
            except (json.JSONDecodeError, ValueError):
                pass
    return cfg


def save_config(cfg: dict) -> None:
    """Persist config to disk."""
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
