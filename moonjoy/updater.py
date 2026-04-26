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
    """Mount DMG and replace /Applications/MoonJoy.app with admin privileges.

    The replace step runs in a detached shell script that waits a few
    seconds so the currently-running MoonJoy.app can quit before its bundle
    is overwritten. Without this delay, ditto/rm would race against the
    running process and corrupt the install.
    """
    if sys.platform != "darwin":
        raise UpdateError("DMG install is only supported on macOS")

    mount_dir = tempfile.mkdtemp(prefix="moonjoy_dmg_")
    app_path = os.path.join(mount_dir, "MoonJoy.app")

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
        subprocess.run(["hdiutil", "detach", mount_dir, "-force"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        raise UpdateError("Mounted DMG does not contain MoonJoy.app")

    # Stage the new app outside the mount so we can detach the DMG before
    # the running process exits.
    staging_dir = tempfile.mkdtemp(prefix="moonjoy_stage_")
    staged_app = os.path.join(staging_dir, "MoonJoy.app")
    copy_stage = subprocess.run(
        ["ditto", app_path, staged_app],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    subprocess.run(["hdiutil", "detach", mount_dir, "-force"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        os.rmdir(mount_dir)
    except OSError:
        pass
    if copy_stage.returncode != 0:
        raise UpdateError(f"Failed to stage update: {copy_stage.stderr.strip()}")

    # Build deferred install script that runs after the GUI exits.
    script_path = os.path.join(staging_dir, "install.sh")
    with open(script_path, "w", encoding="utf-8") as handle:
        handle.write(
            "#!/bin/bash\n"
            "sleep 3\n"
            f"STAGED={shlex.quote(staged_app)}\n"
            "DEST=/Applications/MoonJoy.app\n"
            "rm -rf \"$DEST\"\n"
            "ditto \"$STAGED\" \"$DEST\"\n"
            "rm -rf \"$(dirname \"$STAGED\")\"\n"
            "open \"$DEST\"\n"
        )
    os.chmod(script_path, 0o755)

    osascript_cmd = f'do shell script {json.dumps("/bin/bash " + shlex.quote(script_path) + " >/tmp/moonjoy-update.log 2>&1 &")} with administrator privileges'
    auth = subprocess.run(
        ["osascript", "-e", osascript_cmd],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if auth.returncode != 0:
        raise UpdateError(
            f"Authorization failed: {auth.stderr.strip() or auth.stdout.strip()}"
        )


def install_linux_deb(deb_path: str) -> None:
    """Install .deb update using a graphical privilege helper.

    Tries pkexec first (works in headless GUI sessions). Falls back to
    common graphical sudo wrappers; we deliberately avoid plain ``sudo``
    because it would block on a tty password prompt that the GUI cannot
    answer.
    """
    if sys.platform != "linux":
        raise UpdateError("DEB install is only supported on Linux")

    # All commands here must be non-interactive when called from a GUI.
    candidates = [
        ["pkexec", "dpkg", "-i", deb_path],
        ["gksudo", "--", "dpkg", "-i", deb_path],
        ["kdesudo", "--", "dpkg", "-i", deb_path],
    ]

    last_error = ""
    for cmd in candidates:
        helper = cmd[0]
        if not _which(helper):
            continue
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except OSError as exc:
            last_error = str(exc)
            continue
        if result.returncode == 0:
            return
        last_error = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"

    raise UpdateError(
        "Failed to install .deb update automatically. "
        f"Install manually with: sudo dpkg -i {deb_path}\n"
        f"Last error: {last_error or 'no graphical privilege helper (pkexec/gksudo/kdesudo) found.'}"
    )


def _which(program: str) -> str | None:
    from shutil import which
    return which(program)
