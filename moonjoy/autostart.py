"""Background launch and autostart helpers for MoonJoy wallpaper rotation."""

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "MoonJoyWallpaper"


def _pythonw_path() -> str:
    """Prefer pythonw.exe on Windows so background runs stay hidden."""
    if sys.platform != "win32":
        return sys.executable

    exe_path = Path(sys.executable)
    pythonw = exe_path.with_name("pythonw.exe")
    if pythonw.is_file():
        return str(pythonw)
    return str(exe_path)


def wallpaper_command_args() -> list[str]:
    """Return the command used to run the wallpaper daemon in background mode."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "wallpaper", "--quiet"]
    return [_pythonw_path(), "-m", "moonjoy", "wallpaper", "--quiet"]


def spawn_wallpaper_background() -> subprocess.Popen:
    """Launch the wallpaper daemon detached from the current UI process."""
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        creationflags = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(wallpaper_command_args(), **kwargs)


def is_wallpaper_autostart_enabled() -> bool:
    """Return whether wallpaper autostart is enabled for the current user."""
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
            finally:
                winreg.CloseKey(key)
            return value == subprocess.list2cmdline(wallpaper_command_args())
        except OSError:
            return False

    if sys.platform == "darwin":
        return _launch_agent_path().is_file()

    service_path = _systemd_service_path()
    if service_path.is_file():
        return True
    return _xdg_autostart_path().is_file()


def enable_wallpaper_autostart() -> str:
    """Enable wallpaper autostart for the current user."""
    if sys.platform == "win32":
        import winreg

        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH)
        try:
            winreg.SetValueEx(
                key,
                RUN_VALUE_NAME,
                0,
                winreg.REG_SZ,
                subprocess.list2cmdline(wallpaper_command_args()),
            )
        finally:
            winreg.CloseKey(key)
        return "Wallpaper autostart enabled for this Windows user."

    if sys.platform == "darwin":
        plist_path = _launch_agent_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "Label": "com.platysoft.moonjoy.wallpaper",
            "ProgramArguments": wallpaper_command_args(),
            "RunAtLoad": True,
            # Only restart on crash so a clean exit (e.g. another instance
            # already holds the single-instance lock) does not loop.
            "KeepAlive": {"SuccessfulExit": False, "Crashed": True},
            "ThrottleInterval": 30,
            "ProcessType": "Background",
            "StandardOutPath": "/tmp/moonjoy-wallpaper.log",
            "StandardErrorPath": "/tmp/moonjoy-wallpaper.log",
        }
        with open(plist_path, "wb") as handle:
            plistlib.dump(payload, handle)
        _run_optional(["launchctl", "unload", str(plist_path)])
        _run_optional(["launchctl", "load", str(plist_path)])
        return "Wallpaper autostart enabled via LaunchAgent."

    service_path = _systemd_service_path()
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(_systemd_service_text(), encoding="utf-8")
    _run_optional(["systemctl", "--user", "daemon-reload"])
    _run_optional(["systemctl", "--user", "enable", "moonjoy-wallpaper.service"])
    _run_optional(["systemctl", "--user", "restart", "moonjoy-wallpaper.service"])

    if shutil.which("systemctl"):
        return "Wallpaper autostart enabled via systemd user service."

    desktop_path = _xdg_autostart_path()
    desktop_path.parent.mkdir(parents=True, exist_ok=True)
    desktop_path.write_text(_xdg_autostart_text(), encoding="utf-8")
    return "Wallpaper autostart enabled via XDG autostart entry."


def disable_wallpaper_autostart() -> str:
    """Disable wallpaper autostart for the current user."""
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, RUN_VALUE_NAME)
            finally:
                winreg.CloseKey(key)
        except OSError:
            pass
        return "Wallpaper autostart disabled for this Windows user."

    if sys.platform == "darwin":
        plist_path = _launch_agent_path()
        _run_optional(["launchctl", "unload", str(plist_path)])
        if plist_path.exists():
            plist_path.unlink()
        return "Wallpaper autostart disabled."

    _run_optional(["systemctl", "--user", "disable", "--now", "moonjoy-wallpaper.service"])
    service_path = _systemd_service_path()
    if service_path.exists():
        service_path.unlink()
    desktop_path = _xdg_autostart_path()
    if desktop_path.exists():
        desktop_path.unlink()
    return "Wallpaper autostart disabled."


def _launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.platysoft.moonjoy.wallpaper.plist"


def _systemd_service_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / "moonjoy-wallpaper.service"


def _xdg_autostart_path() -> Path:
    return Path.home() / ".config" / "autostart" / "moonjoy-wallpaper.desktop"


def _systemd_service_text() -> str:
    command = _shell_join(wallpaper_command_args())
    return (
        "[Unit]\n"
        "Description=MoonJoy Wallpaper Rotator\n"
        "After=graphical-session.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={command}\n"
        "Restart=on-failure\n"
        "RestartSec=10\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def _xdg_autostart_text() -> str:
    command = _shell_join(wallpaper_command_args())
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=MoonJoy Wallpaper Rotator\n"
        "Comment=Start MoonJoy wallpaper rotation in background\n"
        f"Exec=sh -lc '{escape(command)}'\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def _shell_join(args: list[str]) -> str:
    return " ".join(shlex_quote(part) for part in args)


def shlex_quote(value: str) -> str:
    """Small shell quoting helper that avoids importing shlex on Windows."""
    if value == "":
        return "''"
    if all(ch.isalnum() or ch in "@%_+=:,./-" for ch in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _run_optional(command: list[str]) -> None:
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        pass