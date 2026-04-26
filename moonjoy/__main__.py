"""MoonJoy entry point — run as `python -m moonjoy [mode]`."""

import sys


def main():
    args = sys.argv[1:]
    flags = {arg for arg in args if arg.startswith("--")}
    positional = [arg for arg in args if not arg.startswith("--")]
    mode = positional[0] if positional else "gui"

    if mode in ("screensaver", "/s", "/S"):
        from moonjoy.screensaver import run_screensaver
        run_screensaver()
    elif mode in ("wallpaper", "wp"):
        from moonjoy.wallpaper_daemon import run_wallpaper_daemon
        sys.exit(run_wallpaper_daemon(quiet="--quiet" in flags))
    elif mode in ("service", "autostart-enable", "enable-autostart"):
        from moonjoy.autostart import enable_wallpaper_autostart
        print(enable_wallpaper_autostart())
    elif mode in ("service-remove", "autostart-disable", "disable-autostart"):
        from moonjoy.autostart import disable_wallpaper_autostart
        print(disable_wallpaper_autostart())
    elif mode in ("configure", "config", "/c", "/C"):
        from moonjoy.gui import run_gui
        run_gui(start_minimized="--minimized" in flags)
    elif mode in ("gui", "settings"):
        from moonjoy.gui import run_gui
        run_gui(start_minimized="--minimized" in flags)
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
        print("  service           Enable wallpaper autostart for this user")
        print("  service-remove    Disable wallpaper autostart for this user")
        print("  config            Open settings window")
        sys.exit(0)


if __name__ == "__main__":
    main()
