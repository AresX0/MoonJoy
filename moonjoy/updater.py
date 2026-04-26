"""GitHub release update helpers for MoonJoy."""

import os
import re
import shlex
import subprocess
import sys
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen
import json


RELEASES_LATEST_URL = "https://api.github.com/repos/AresX0/MoonJoy/releases/latest"


class UpdateError(RuntimeError):
    """Raised when checking or installing updates fails."""


def _version_tuple(value: str) -> tuple[int, ...]:
    """Parse semantic-ish version strings into a tuple for comparison."""
    cleaned = value.strip().lstrip("v")
    numbers = [int(x) for x in re.findall(r"\d+", cleaned)]
    return tuple(numbers) if numbers else (0,)


def is_newer_version(latest: str, current: str) -> bool:
    """Return True when *latest* is newer than *current*."""
    return _version_tuple(latest) > _version_tuple(current)


def get_latest_release() -> dict:
    """Fetch latest release metadata from GitHub."""
    req = Request(
        RELEASES_LATEST_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "MoonJoy-Updater",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"Unable to fetch latest release: {exc}") from exc


def select_release_asset(release: dict) -> dict | None:
    """Select the best installer asset for the current platform."""
    suffix_map = {
        "win32": "win64.msi",
        "darwin": "macOS.dmg",
        "linux": "linux-amd64.deb",
    }
    suffix = suffix_map.get(sys.platform, "")
    if not suffix:
        return None

    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(suffix):
            return asset
    return None


def download_file(url: str, filename: str) -> str:
    """Download a file to a temp location and return the local path."""
    out_dir = os.path.join(tempfile.gettempdir(), "moonjoy_updates")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    req = Request(url, headers={"User-Agent": "MoonJoy-Updater"})
    try:
        with urlopen(req, timeout=60) as response, open(out_path, "wb") as handle:
            handle.write(response.read())
    except (URLError, OSError) as exc:
        raise UpdateError(f"Download failed: {exc}") from exc

    return out_path


def install_windows_msi(msi_path: str) -> None:
    """Launch elevated MSI install. Existing versions are removed via MajorUpgrade."""
    if sys.platform != "win32":
        raise UpdateError("Windows MSI install is only supported on Windows")

    arg_list = f'/i "{msi_path}" /passive /norestart'
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            "Start-Process msiexec.exe "
            f"-ArgumentList '{arg_list}' "
            "-Verb RunAs"
        ),
    ]

    creationflags = (
        getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )

    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as exc:
        raise UpdateError(f"Failed to launch installer: {exc}") from exc


def install_macos_dmg(dmg_path: str) -> None:
    """Mount DMG and replace /Applications/MoonJoy.app with admin privileges."""
    if sys.platform != "darwin":
        raise UpdateError("DMG install is only supported on macOS")

    mount_dir = tempfile.mkdtemp(prefix="moonjoy_dmg_")
    app_path = os.path.join(mount_dir, "MoonJoy.app")

    try:
        attach = subprocess.run(
            ["hdiutil", "attach", dmg_path, "-nobrowse", "-mountpoint", mount_dir],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if attach.returncode != 0:
            raise UpdateError(f"Failed to mount DMG: {attach.stderr.strip()}")

        if not os.path.isdir(app_path):
            raise UpdateError("Mounted DMG does not contain MoonJoy.app")

        copy_cmd = (
            "rm -rf /Applications/MoonJoy.app && "
            f"ditto {shlex.quote(app_path)} /Applications/MoonJoy.app"
        )
        script = f'do shell script {json.dumps(copy_cmd)} with administrator privileges'
        install = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if install.returncode != 0:
            raise UpdateError(f"Install failed: {install.stderr.strip() or install.stdout.strip()}")

        subprocess.Popen(["open", "/Applications/MoonJoy.app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise UpdateError(f"Failed to install macOS update: {exc}") from exc
    finally:
        subprocess.run(
            ["hdiutil", "detach", mount_dir, "-force"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        try:
            os.rmdir(mount_dir)
        except OSError:
            pass


def install_linux_deb(deb_path: str) -> None:
    """Install .deb update using privilege escalation (pkexec preferred)."""
    if sys.platform != "linux":
        raise UpdateError("DEB install is only supported on Linux")

    commands = [
        ["pkexec", "dpkg", "-i", deb_path],
        ["sudo", "dpkg", "-i", deb_path],
    ]

    last_error = ""
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
        except OSError:
            continue
        if result.returncode == 0:
            return
        last_error = result.stderr.strip() or result.stdout.strip()

    raise UpdateError(
        "Failed to install .deb update automatically. "
        f"Last error: {last_error or 'no supported privilege helper (pkexec/sudo) found.'}"
    )
