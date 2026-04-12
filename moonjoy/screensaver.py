"""Fullscreen slideshow screensaver with NASA mission overlay."""

import os
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from itertools import cycle

from PIL import Image, ImageTk

from moonjoy.config import load_config
from moonjoy.image_scanner import scan_images
from moonjoy.nasa_data import get_overlay_lines


class ScreensaverWindow:
    """Fullscreen slideshow that acts as a screensaver."""

    def __init__(self, root: tk.Tk, images: list[str], config: dict):
        self.root = root
        self.images = images
        self.config = config
        self.interval_ms = int(config.get("slideshow_interval", 10) * 1000)
        self.image_cycle = cycle(images)
        self.current_photo = None

        # Fullscreen setup
        self.root.attributes("-fullscreen", True)
        self.root.configure(background="black", cursor="none")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.focus_force()

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.root, width=self.screen_w, height=self.screen_h,
            bg="black", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Image item on canvas
        self.img_item = self.canvas.create_image(
            self.screen_w // 2, self.screen_h // 2, anchor="center"
        )

        # ── NASA overlay (top-right corner) ─────────────────────────────
        self.show_overlay = config.get("show_overlay", True)
        self._overlay_items: list[int] = []
        self._overlay_bg_item: int | None = None
        self._overlay_lines: list[str] = []
        self._overlay_scroll_offset = 0

        if self.show_overlay:
            # Load overlay data in background thread to avoid blocking
            self._overlay_font = tkfont.Font(family="Consolas", size=11, weight="normal")
            self._overlay_title_font = tkfont.Font(family="Consolas", size=12, weight="bold")
            threading.Thread(target=self._load_overlay_data, daemon=True).start()

        # Exit on any input
        self.root.bind("<Motion>", self._on_activity)
        self.root.bind("<KeyPress>", self._on_activity)
        self.root.bind("<ButtonPress>", self._on_activity)
        self._start_pos = None

        # Start slideshow
        self._show_next()

    # ── Overlay ───────────────────────────────────────────────────────────

    def _load_overlay_data(self):
        """Fetch NASA data and schedule overlay rendering on main thread."""
        try:
            self._overlay_lines = get_overlay_lines(max_lines=15)
        except Exception:
            self._overlay_lines = ["NASA data unavailable"]
        self.root.after(100, self._draw_overlay)
        # Start scroll animation
        scroll_speed = int(self.config.get("overlay_scroll_speed", 30) * 1000)
        self.root.after(scroll_speed, self._scroll_overlay)

    def _draw_overlay(self):
        """Render the NASA info overlay in the top-right corner."""
        # Clear previous overlay items
        for item in self._overlay_items:
            self.canvas.delete(item)
        self._overlay_items.clear()
        if self._overlay_bg_item is not None:
            self.canvas.delete(self._overlay_bg_item)

        if not self._overlay_lines:
            return

        # Determine visible lines (scrolling window)
        max_visible = max(1, (self.screen_h - 60) // 20)
        total = len(self._overlay_lines)
        start = self._overlay_scroll_offset % total if total > max_visible else 0
        visible_lines = []
        for i in range(min(max_visible, total)):
            idx = (start + i) % total
            visible_lines.append(self._overlay_lines[idx])

        # Calculate overlay dimensions
        padding = 16
        line_height = 20
        max_text_w = 0
        for line in visible_lines:
            w = self._overlay_font.measure(line)
            max_text_w = max(max_text_w, w)

        box_w = max_text_w + padding * 2
        box_h = len(visible_lines) * line_height + padding * 2
        x_right = self.screen_w - 20
        y_top = 20

        # Semi-transparent background (using stipple for transparency effect)
        self._overlay_bg_item = self.canvas.create_rectangle(
            x_right - box_w, y_top,
            x_right, y_top + box_h,
            fill="#0a0a2e", outline="#1a3a6a", width=1, stipple="gray75"
        )
        self._overlay_items.append(self._overlay_bg_item)

        # Draw text lines
        y = y_top + padding
        for line in visible_lines:
            if line.startswith("═══"):
                font = self._overlay_title_font
                color = "#4fc3f7"
            elif line.startswith("✓"):
                font = self._overlay_font
                color = "#66bb6a"
            elif line.startswith("●"):
                font = self._overlay_font
                color = "#ffa726"
            elif line.startswith("◇"):
                font = self._overlay_font
                color = "#90caf9"
            elif line.startswith("▸"):
                font = self._overlay_font
                color = "#ce93d8"
            elif line.startswith("    "):
                font = self._overlay_font
                color = "#b0bec5"
            else:
                font = self._overlay_font
                color = "#e0e0e0"

            item = self.canvas.create_text(
                x_right - padding, y,
                anchor="ne", text=line, font=font, fill=color
            )
            self._overlay_items.append(item)
            y += line_height

    def _scroll_overlay(self):
        """Scroll the overlay content periodically."""
        if not self._overlay_lines:
            return
        max_visible = max(1, (self.screen_h - 60) // 20)
        if len(self._overlay_lines) > max_visible:
            self._overlay_scroll_offset += 1
            self._draw_overlay()
        scroll_speed = int(self.config.get("overlay_scroll_speed", 30) * 1000)
        self.root.after(scroll_speed, self._scroll_overlay)

    # ── Screensaver core ──────────────────────────────────────────────────

    def _on_activity(self, event):
        """Exit screensaver on user activity."""
        if event.type == tk.EventType.Motion:
            if self._start_pos is None:
                self._start_pos = (event.x, event.y)
                return
            dx = abs(event.x - self._start_pos[0])
            dy = abs(event.y - self._start_pos[1])
            if dx < 5 and dy < 5:
                return
        self.root.destroy()

    def _load_image(self, path: str) -> ImageTk.PhotoImage | None:
        """Load and scale an image to fit the screen."""
        try:
            img = Image.open(path)
            img = img.convert("RGB")
            ratio = min(self.screen_w / img.width, self.screen_h / img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Failed to load {path}: {e}")
            return None

    def _show_next(self):
        """Display the next image in the cycle."""
        for _ in range(min(len(self.images), 50)):
            path = next(self.image_cycle)
            photo = self._load_image(path)
            if photo:
                self.current_photo = photo
                self.canvas.itemconfig(self.img_item, image=self.current_photo)
                # Re-draw overlay on top of new image
                if self.show_overlay and self._overlay_lines:
                    self._draw_overlay()
                break
        self.root.after(self.interval_ms, self._show_next)


def run_screensaver():
    """Entry point for screensaver mode."""
    config = load_config()
    images = scan_images(shuffle=config.get("shuffle", True))

    if not images:
        print("No images found in Images directory!")
        sys.exit(1)

    root = tk.Tk()
    root.title("MoonJoy Screensaver")
    ScreensaverWindow(root, images, config)
    root.mainloop()


if __name__ == "__main__":
    run_screensaver()
