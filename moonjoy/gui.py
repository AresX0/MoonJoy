"""MoonJoy Settings GUI - configure screensaver and wallpaper rotator."""

import sys
import tkinter as tk
from tkinter import ttk

from .config import load_config, save_config


class SettingsApp:
    """Tkinter GUI for MoonJoy settings."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MoonJoy — NASA Screensaver & Wallpaper")
        self.root.resizable(False, False)
        self.config = load_config()

        # Dark theme colors
        self.bg = "#1a1a2e"
        self.fg = "#e0e0e0"
        self.accent = "#4fc3f7"
        self.btn_bg = "#16213e"
        self.entry_bg = "#0f3460"

        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=self.bg)
        style.configure("Dark.TLabel", background=self.bg, foreground=self.fg, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.bg, foreground=self.accent, font=("Segoe UI", 14, "bold"))
        style.configure("Section.TLabel", background=self.bg, foreground="#ce93d8", font=("Segoe UI", 11, "bold"))
        style.configure("Dark.TButton", background=self.btn_bg, foreground=self.fg, font=("Segoe UI", 10))
        style.configure("Accent.TButton", background=self.accent, foreground="#000", font=("Segoe UI", 10, "bold"))
        style.configure("Dark.TCheckbutton", background=self.bg, foreground=self.fg, font=("Segoe UI", 10))
        style.configure("Dark.TCombobox", fieldbackground=self.entry_bg, foreground=self.fg)

        main = ttk.Frame(root, style="Dark.TFrame", padding=20)
        main.pack(fill="both", expand=True)

        # Title
        ttk.Label(main, text="🌙 MoonJoy", style="Title.TLabel").pack(anchor="w")
        ttk.Label(main, text="NASA Image Screensaver & Wallpaper Rotator",
                  style="Dark.TLabel").pack(anchor="w")
        link_label = tk.Label(main, text="by Platysoft — platysoft.com",
                              bg=self.bg, fg="#7986cb", font=("Segoe UI", 9),
                              cursor="hand2")
        link_label.pack(anchor="w", pady=(0, 15))
        link_label.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://platysoft.com/"))

        # ── Screensaver section ──────────────────────────────────────────
        ttk.Label(main, text="Screensaver", style="Section.TLabel").pack(anchor="w", pady=(10, 5))

        row1 = ttk.Frame(main, style="Dark.TFrame")
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Slide interval (seconds):", style="Dark.TLabel").pack(side="left")
        self.slide_var = tk.StringVar(value=str(self.config.get("slideshow_interval", 10)))
        slide_entry = tk.Entry(row1, textvariable=self.slide_var, width=8,
                               bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                               relief="flat", font=("Segoe UI", 10))
        slide_entry.pack(side="right")

        # Shuffle
        self.shuffle_var = tk.BooleanVar(value=self.config.get("shuffle", True))
        ttk.Checkbutton(main, text="Shuffle images", variable=self.shuffle_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        # Overlay
        self.overlay_var = tk.BooleanVar(value=self.config.get("show_overlay", True))
        ttk.Checkbutton(main, text="Show NASA mission overlay", variable=self.overlay_var,
                        style="Dark.TCheckbutton").pack(anchor="w", pady=2)

        row_scroll = ttk.Frame(main, style="Dark.TFrame")
        row_scroll.pack(fill="x", pady=2)
        ttk.Label(row_scroll, text="Overlay scroll speed (seconds):", style="Dark.TLabel").pack(side="left")
        self.scroll_var = tk.StringVar(value=str(self.config.get("overlay_scroll_speed", 30)))
        tk.Entry(row_scroll, textvariable=self.scroll_var, width=8,
                 bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                 relief="flat", font=("Segoe UI", 10)).pack(side="right")

        # ── Wallpaper section ────────────────────────────────────────────
        ttk.Label(main, text="Wallpaper Rotator", style="Section.TLabel").pack(anchor="w", pady=(15, 5))

        row2 = ttk.Frame(main, style="Dark.TFrame")
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Change interval (seconds):", style="Dark.TLabel").pack(side="left")
        self.wall_var = tk.StringVar(value=str(self.config.get("wallpaper_interval", 300)))
        tk.Entry(row2, textvariable=self.wall_var, width=8,
                 bg=self.entry_bg, fg=self.fg, insertbackground=self.fg,
                 relief="flat", font=("Segoe UI", 10)).pack(side="right")

        row3 = ttk.Frame(main, style="Dark.TFrame")
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Fit mode:", style="Dark.TLabel").pack(side="left")
        self.fit_var = tk.StringVar(value=self.config.get("fit_mode", "fit"))
        fit_combo = ttk.Combobox(row3, textvariable=self.fit_var,
                                 values=["fit", "fill", "stretch", "center"],
                                 state="readonly", width=10, style="Dark.TCombobox")
        fit_combo.pack(side="right")

        # ── Buttons ──────────────────────────────────────────────────────
        sep = ttk.Frame(main, style="Dark.TFrame", height=2)
        sep.pack(fill="x", pady=15)

        btn_row = ttk.Frame(main, style="Dark.TFrame")
        btn_row.pack(fill="x")

        launch_ss = tk.Button(btn_row, text="▶ Launch Screensaver", command=self._launch_screensaver,
                              bg="#2e7d32", fg="white", activebackground="#388e3c",
                              relief="flat", font=("Segoe UI", 10, "bold"), padx=12, pady=6)
        launch_ss.pack(side="left", padx=(0, 5))

        launch_wp = tk.Button(btn_row, text="▶ Start Wallpaper Rotator", command=self._launch_wallpaper,
                              bg="#1565c0", fg="white", activebackground="#1976d2",
                              relief="flat", font=("Segoe UI", 10, "bold"), padx=12, pady=6)
        launch_wp.pack(side="left", padx=5)

        save_btn = tk.Button(btn_row, text="💾 Save Settings", command=self._save,
                             bg=self.btn_bg, fg=self.fg, activebackground="#1a3a6a",
                             relief="flat", font=("Segoe UI", 10), padx=12, pady=6)
        save_btn.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(main, textvariable=self.status_var,
                                     bg=self.bg, fg="#66bb6a", font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", pady=(10, 0))

    def _save(self):
        """Save current settings to config file."""
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
        self.config["fit_mode"] = self.fit_var.get()

        save_config(self.config)
        self.status_var.set("✓ Settings saved!")
        self.root.after(3000, lambda: self.status_var.set(""))

    def _launch_screensaver(self):
        """Save settings and launch the screensaver."""
        self._save()
        import subprocess
        subprocess.Popen([sys.executable, "-m", "moonjoy", "screensaver"])
        self.status_var.set("Screensaver launched!")

    def _launch_wallpaper(self):
        """Save settings and launch the wallpaper rotator."""
        self._save()
        import subprocess
        subprocess.Popen([sys.executable, "-m", "moonjoy", "wallpaper"])
        self.status_var.set("Wallpaper rotator started!")


def run_gui():
    """Entry point for the settings GUI."""
    root = tk.Tk()
    root.geometry("520x520")
    SettingsApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
