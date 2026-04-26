"""MoonJoy Settings GUI - configure screensaver and wallpaper rotator."""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import webbrowser

from moonjoy.autostart import (
    disable_wallpaper_autostart,
    enable_wallpaper_autostart,
    is_wallpaper_autostart_enabled,
    spawn_wallpaper_background,
)
from moonjoy.config import load_config, save_config
from moonjoy.updater import (
    UpdateError,
    download_file,
    get_latest_release,
    install_linux_deb,
    install_macos_dmg,
    install_windows_msi,
    is_newer_version,
    select_release_asset,
)


def _asset_path(filename: str) -> str:
    """Return the path to a bundled asset file."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", filename)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", filename)


class SettingsApp:
    """Tkinter GUI for MoonJoy settings."""

    def __init__(self, root: tk.Tk, start_minimized: bool = False):
        self.root = root
        self.root.title("MoonJoy — Screensaver & Wallpaper")
        self.root.resizable(False, False)
        self.config = load_config()

        # Dark theme colors
        self.bg = "#1a1a2e"
        self.fg = "#e0e0e0"
        self.accent = "#4fc3f7"
        self.btn_bg = "#16213e"
        self.entry_bg = "#0f3460"

        self.root.configure(bg=self.bg)

        # Cross-platform font: Segoe UI on Windows, system default on Linux/macOS
        _font = "Segoe UI" if sys.platform == "win32" else "sans-serif"
        self._fn = _font

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=self.bg)
        style.configure("Dark.TLabel", background=self.bg, foreground=self.fg, font=(_font, 10))
        style.configure("Title.TLabel", background=self.bg, foreground=self.accent, font=(_font, 14, "bold"))
        style.configure("Section.TLabel", background=self.bg, foreground="#ce93d8", font=(_font, 11, "bold"))
        style.configure("Dark.TButton", background=self.btn_bg, foreground=self.fg, font=(_font, 10))
        style.configure("Accent.TButton", background=self.accent, foreground="#000", font=(_font, 10, "bold"))
        style.configure("Dark.TCheckbutton", background=self.bg, foreground=self.fg, font=(_font, 10))
        style.configure("Dark.TCombobox", fieldbackground=self.entry_bg, foreground=self.fg)

        main = ttk.Frame(root, style="Dark.TFrame", padding=20)
        main.pack(fill="both", expand=True)

        # Logo + Title row
        header = ttk.Frame(main, style="Dark.TFrame")
        header.pack(anchor="w", pady=(0, 5))

        logo_path = _asset_path("logo.png")
        self._logo_image = None
        if os.path.isfile(logo_path):
            try:
                self._logo_image = tk.PhotoImage(file=logo_path).subsample(4)
                tk.Label(header, image=self._logo_image, bg=self.bg).pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_col = ttk.Frame(header, style="Dark.TFrame")
        title_col.pack(side="left")
        ttk.Label(title_col, text="MoonJoy", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_col, text="Space Image Screensaver & Wallpaper Rotator",
                  style="Dark.TLabel").pack(anchor="w")
        link_label = tk.Label(title_col, text="by Platysoft — platysoft.com",
                              bg=self.bg, fg="#7986cb", font=(self._fn, 9),
                              cursor="hand2")
        link_label.pack(anchor="w")
        link_label.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://platysoft.com/"))

        # ── Images folder ────────────────────────────────────────────────
        ttk.Label(main, text="Images Folder", style="Section.TLabel").pack(anchor="w", pady=(10, 5))
        folder_row = ttk.Frame(main, style="Dark.TFrame")
        folder_row.pack(fill="x", pady=2)
        self.images_var = tk.StringVar(value=self.config.get("images_dir", ""))
        images_entry = tk.Entry(folder_row, textvariable=self.images_var,
                                bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                                relief="flat", font=(self._fn, 10))
        images_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        browse_btn = tk.Button(folder_row, text="Browse…", command=self._browse_images,
                               bg=self.btn_bg, fg=self.fg, activebackground="#1a3a6a",
                               relief="flat", font=(self._fn, 9), padx=8, pady=2)
        browse_btn.pack(side="right")

        # ── Screensaver section ──────────────────────────────────────────
        ttk.Label(main, text="Screensaver", style="Section.TLabel").pack(anchor="w", pady=(10, 5))

        row1 = ttk.Frame(main, style="Dark.TFrame")
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Slide interval (seconds):", style="Dark.TLabel").pack(side="left")
        self.slide_var = tk.StringVar(value=str(self.config.get("slideshow_interval", 10)))
        slide_entry = tk.Entry(row1, textvariable=self.slide_var, width=8,
                               bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                               relief="flat", font=(self._fn, 10))
        slide_entry.pack(side="right")

        # Shuffle
        self.shuffle_var = tk.BooleanVar(value=self.config.get("shuffle", True))
        ttk.Checkbutton(main, text="Shuffle images", variable=self.shuffle_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        # Overlay
        self.overlay_var = tk.BooleanVar(value=self.config.get("show_overlay", True))
        ttk.Checkbutton(main, text="Show mission overlay", variable=self.overlay_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        row_scroll = ttk.Frame(main, style="Dark.TFrame")
        row_scroll.pack(fill="x", pady=2)
        ttk.Label(row_scroll, text="Overlay scroll speed (seconds):", style="Dark.TLabel").pack(side="left")
        self.scroll_var = tk.StringVar(value=str(self.config.get("overlay_scroll_speed", 30)))
        tk.Entry(row_scroll, textvariable=self.scroll_var, width=8,
                 bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                 relief="flat", font=(self._fn, 10)).pack(side="right")

        # ── Wallpaper section ────────────────────────────────────────────
        ttk.Label(main, text="Wallpaper Rotator", style="Section.TLabel").pack(anchor="w", pady=(15, 5))

        row2 = ttk.Frame(main, style="Dark.TFrame")
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Change interval (seconds):", style="Dark.TLabel").pack(side="left")
        self.wall_var = tk.StringVar(value=str(self.config.get("wallpaper_interval", 300)))
        tk.Entry(row2, textvariable=self.wall_var, width=8,
                 bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                 relief="flat", font=(self._fn, 10)).pack(side="right")

        row3 = ttk.Frame(main, style="Dark.TFrame")
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Fit mode:", style="Dark.TLabel").pack(side="left")
        self.fit_var = tk.StringVar(value=self.config.get("fit_mode", "fit"))
        fit_combo = ttk.Combobox(row3, textvariable=self.fit_var,
                                 values=["fit", "fill", "stretch", "center"],
                                 state="readonly", width=10, style="Dark.TCombobox")
        fit_combo.pack(side="right")

        self.wp_overlay_var = tk.BooleanVar(value=self.config.get("wallpaper_overlay", True))
        ttk.Checkbutton(main, text="Show overlay on desktop wallpaper",
                        variable=self.wp_overlay_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        self.autostart_var = tk.BooleanVar(value=is_wallpaper_autostart_enabled())
        ttk.Checkbutton(main, text="Run wallpaper rotator at login",
                        variable=self.autostart_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        self.minimize_var = tk.BooleanVar(
            value=self.config.get("minimize_on_wallpaper_start", True)
        )
        ttk.Checkbutton(main, text="Minimize settings window after starting rotator",
                        variable=self.minimize_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        self.lockscreen_var = tk.BooleanVar(value=self.config.get("apply_to_lockscreen", True))
        ttk.Checkbutton(main, text="Apply to lock screen (Windows)",
                        variable=self.lockscreen_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        # ── Buttons ──────────────────────────────────────────────────────
        sep = ttk.Frame(main, style="Dark.TFrame", height=2)
        sep.pack(fill="x", pady=15)

        btn_row = ttk.Frame(main, style="Dark.TFrame")
        btn_row.pack(fill="x")

        launch_ss = tk.Button(btn_row, text="▶ Launch Screensaver", command=self._launch_screensaver,
                              bg="#2e7d32", fg="white", activebackground="#388e3c",
                              relief="flat", font=(self._fn, 10, "bold"), padx=12, pady=6)
        launch_ss.pack(side="left", padx=(0, 5))

        launch_wp = tk.Button(btn_row, text="▶ Start Wallpaper Rotator", command=self._launch_wallpaper,
                              bg="#1565c0", fg="white", activebackground="#1976d2",
                              relief="flat", font=(self._fn, 10, "bold"), padx=12, pady=6)
        launch_wp.pack(side="left", padx=5)

        save_btn = tk.Button(btn_row, text="💾 Save Settings", command=self._save,
                             bg=self.btn_bg, fg=self.fg, activebackground="#1a3a6a",
                             relief="flat", font=(self._fn, 10), padx=12, pady=6)
        save_btn.pack(side="right")

        # Second button row for update
        btn_row2 = ttk.Frame(main, style="Dark.TFrame")
        btn_row2.pack(fill="x", pady=(5, 0))

        update_btn = tk.Button(btn_row2, text="⬆ Check for Updates", command=self._check_update,
                               bg="#6a1b9a", fg="white", activebackground="#7b1fa2",
                               relief="flat", font=(self._fn, 10), padx=12, pady=6)
        update_btn.pack(side="left")

        # Status bar
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(main, textvariable=self.status_var,
                                     bg=self.bg, fg="#66bb6a", font=(self._fn, 9))
        self.status_label.pack(anchor="w", pady=(10, 0))

        if start_minimized:
            self.root.after(0, self.root.iconify)

    def _browse_images(self):
        """Open a folder picker for the images directory."""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Images Folder")
        if folder:
            self.images_var.set(folder)

    def _save(self):
        """Save current settings to config file."""
        self.config["images_dir"] = self.images_var.get().strip()
        try:
            self.config["slideshow_interval"] = max(1, int(float(self.slide_var.get())))
        except ValueError:
            pass
        try:
            self.config["wallpaper_interval"] = max(1, int(float(self.wall_var.get())))
        except ValueError:
            pass
        try:
            self.config["overlay_scroll_speed"] = max(1, int(float(self.scroll_var.get())))
        except ValueError:
            pass

        self.config["shuffle"] = self.shuffle_var.get()
        self.config["show_overlay"] = self.overlay_var.get()
        self.config["wallpaper_overlay"] = self.wp_overlay_var.get()
        self.config["apply_to_lockscreen"] = self.lockscreen_var.get()
        self.config["wallpaper_autostart"] = self.autostart_var.get()
        self.config["minimize_on_wallpaper_start"] = self.minimize_var.get()
        self.config["fit_mode"] = self.fit_var.get()

        save_config(self.config)

        try:
            message = (
                enable_wallpaper_autostart()
                if self.autostart_var.get()
                else disable_wallpaper_autostart()
            )
        except Exception as exc:
            self.status_var.set(f"Autostart update failed: {exc}")
            self.root.after(5000, lambda: self.status_var.set(""))
            return

        self.status_var.set(f"✓ Settings saved! {message}")
        self.root.after(3000, lambda: self.status_var.set(""))

    def _launch_screensaver(self):
        """Save settings and launch the screensaver."""
        self._save()
        import subprocess
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable, "screensaver"])
        else:
            subprocess.Popen([sys.executable, "-m", "moonjoy", "screensaver"])
        self.status_var.set("Screensaver launched!")

    def _launch_wallpaper(self):
        """Save settings and launch the wallpaper rotator."""
        self._save()
        try:
            spawn_wallpaper_background()
        except Exception as exc:
            messagebox.showerror("MoonJoy", f"Failed to start wallpaper rotator:\n{exc}")
            self.status_var.set("Wallpaper rotator failed to start")
            return

        if self.minimize_var.get():
            self.root.iconify()
            self.status_var.set("Wallpaper rotator started in background. Window minimized.")
        else:
            self.status_var.set("Wallpaper rotator started in background.")

    def _check_update(self):
        """Check GitHub for a newer release and offer to download it."""
        import threading
        self.status_var.set("Checking for updates…")
        threading.Thread(target=self._do_update_check, daemon=True).start()

    def _do_update_check(self):
        """Background thread: fetch latest release info from GitHub."""
        from moonjoy import __version__
        try:
            data = get_latest_release()
        except UpdateError as e:
            self.root.after(0, lambda: self.status_var.set(str(e)))
            return

        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            self.root.after(0, lambda: self.status_var.set("No release found"))
            return

        if not is_newer_version(latest_tag, __version__):
            self.root.after(0, lambda: self.status_var.set(f"✓ Already on latest version ({__version__})"))
            return

        asset = select_release_asset(data)
        download_url = data.get("html_url", "")
        if asset:
            download_url = asset.get("browser_download_url", download_url)

        def _install_platform_update() -> None:
            if not asset:
                messagebox.showerror("Update Failed", "No installer asset found in the latest release.")
                return
            try:
                self.status_var.set(f"Downloading MoonJoy {latest_tag} installer…")
                local_installer = download_file(download_url, asset.get("name", f"MoonJoy-{latest_tag}"))
                if sys.platform == "win32":
                    install_windows_msi(local_installer)
                elif sys.platform == "darwin":
                    install_macos_dmg(local_installer)
                elif sys.platform == "linux":
                    install_linux_deb(local_installer)
                else:
                    raise UpdateError("Automatic install is not supported on this platform")
            except UpdateError as exc:
                messagebox.showerror("Update Failed", str(exc))
                self.status_var.set("Update failed")
                return

            self.status_var.set("Installer started. MoonJoy will close for update.")
            self.root.after(800, self.root.destroy)

        def _prompt():
            self.status_var.set(f"New version available: {latest_tag} (current: {__version__})")
            if sys.platform in ("win32", "darwin", "linux") and asset:
                if messagebox.askyesno(
                    "Update Available",
                    f"MoonJoy {latest_tag} is available.\n"
                    f"You have {__version__}.\n\n"
                    "Install now? This will replace the old version.",
                ):
                    _install_platform_update()
                return

            if messagebox.askyesno(
                "Update Available",
                f"MoonJoy {latest_tag} is available.\n"
                f"You have {__version__}.\n\n"
                "Open download page?",
            ):
                webbrowser.open(download_url)

        self.root.after(0, _prompt)


def run_gui(start_minimized: bool = False):
    """Entry point for the settings GUI."""
    root = tk.Tk()
    root.geometry("520x680")
    icon_path = _asset_path("icon.ico" if sys.platform == "win32" else "logo.png")
    if os.path.isfile(icon_path):
        try:
            if sys.platform == "win32":
                root.iconbitmap(icon_path)
            else:
                root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception:
            pass
    SettingsApp(root, start_minimized=start_minimized)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
