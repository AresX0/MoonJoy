"""MoonJoy entry point — run as `python -m moonjoy [mode]`."""

import sys


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gui"

    if mode in ("screensaver", "/s", "/S"):
        from moonjoy.screensaver import run_screensaver
        run_screensaver()
    elif mode in ("wallpaper", "wp"):
        from moonjoy.wallpaper_daemon import run_wallpaper_daemon
        run_wallpaper_daemon()
    elif mode in ("configure", "config", "/c", "/C"):
        from moonjoy.gui import run_gui
        run_gui()
    elif mode in ("gui", "settings"):
        from moonjoy.gui import run_gui
        run_gui()
    elif mode in ("preview", "/p", "/P"):
        # Windows screensaver preview mode — just launch the screensaver
        from moonjoy.screensaver import run_screensaver
        run_screensaver()
    else:
        print("MoonJoy — NASA Image Screensaver & Wallpaper Rotator")
        print()
        print("Usage: python -m moonjoy [mode]")
        print()
        print("Modes:")
        print("  gui / settings    Open the settings window (default)")
        print("  screensaver       Launch fullscreen screensaver")
        print("  wallpaper / wp    Start wallpaper rotation daemon")
        print("  config            Open settings window")
        sys.exit(0)


if __name__ == "__main__":
    main()
