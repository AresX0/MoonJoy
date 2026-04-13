"""Generate website screenshot images for the MoonJoy product page."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "moonjoy")
os.makedirs(OUT, exist_ok=True)

# ── Fonts ────────────────────────────────────────────────────────────────────
FONT_DIR = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")

def font(size, bold=False):
    for name in (["segoeuib.ttf", "segoeui.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        p = os.path.join(FONT_DIR, name)
        if os.path.isfile(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def mono(size):
    for name in ["consola.ttf", "cour.ttf"]:
        p = os.path.join(FONT_DIR, name)
        if os.path.isfile(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def rounded_rect(draw, xy, radius, fill, outline=None):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GUI — Dark Settings Window
# ═══════════════════════════════════════════════════════════════════════════════
def gen_gui():
    W, H = 560, 720
    bg = "#1a1a2e"
    fg = "#e0e0e0"
    accent = "#4fc3f7"
    section = "#ce93d8"
    btn_bg = "#16213e"
    entry_bg = "#0f3460"

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    y = 20
    # Title bar
    d.rectangle([0, 0, W, 38], fill="#111125")
    d.text((14, 9), "MoonJoy — Screensaver & Wallpaper", fill="#aaa", font=font(12))
    d.text((W-60, 9), "— □ ✕", fill="#888", font=font(12))

    y = 52
    # Logo placeholder (circle)
    d.ellipse([20, y, 80, y+60], fill="#2a2a5a", outline=accent)
    d.text((32, y+15), "MJ", fill=accent, font=font(22, bold=True))

    # Title text
    d.text((95, y+5), "MoonJoy", fill=accent, font=font(20, bold=True))
    d.text((95, y+30), "Space Image Screensaver & Wallpaper Rotator", fill="#aaa", font=font(11))
    d.text((95, y+48), "by Platysoft — platysoft.com", fill="#7986cb", font=font(10))

    y = 135
    # Images Folder section
    d.text((20, y), "Images Folder", fill=section, font=font(14, bold=True))
    y += 28
    rounded_rect(d, [20, y, 430, y+30], 4, entry_bg)
    d.text((28, y+6), "C:\\Users\\Photos\\Space", fill="#888", font=font(11))
    rounded_rect(d, [440, y, 535, y+30], 4, btn_bg, outline="#333")
    d.text((455, y+6), "Browse…", fill=fg, font=font(11))

    y += 50
    # Screensaver section
    d.text((20, y), "Screensaver", fill=section, font=font(14, bold=True))
    y += 28
    d.text((20, y), "Slide interval (seconds):", fill=fg, font=font(11))
    rounded_rect(d, [460, y-3, 535, y+22], 4, entry_bg)
    d.text((480, y+1), "10", fill=fg, font=font(11))
    y += 32
    d.text((20, y), "☑ Shuffle images", fill=fg, font=font(11))
    d.rectangle([20, y+2, 32, y+14], outline=accent)
    d.text((22, y-1), "✓", fill=accent, font=font(12))
    y += 26
    d.text((20, y), "☑ Show mission overlay", fill=fg, font=font(11))
    d.rectangle([20, y+2, 32, y+14], outline=accent)
    d.text((22, y-1), "✓", fill=accent, font=font(12))
    y += 28
    d.text((20, y), "Overlay scroll speed (seconds):", fill=fg, font=font(11))
    rounded_rect(d, [460, y-3, 535, y+22], 4, entry_bg)
    d.text((480, y+1), "30", fill=fg, font=font(11))

    y += 45
    # Wallpaper section
    d.text((20, y), "Wallpaper Rotator", fill=section, font=font(14, bold=True))
    y += 28
    d.text((20, y), "Change interval (seconds):", fill=fg, font=font(11))
    rounded_rect(d, [460, y-3, 535, y+22], 4, entry_bg)
    d.text((474, y+1), "300", fill=fg, font=font(11))
    y += 32
    d.text((20, y), "Fit mode:", fill=fg, font=font(11))
    rounded_rect(d, [440, y-3, 535, y+22], 4, entry_bg, outline="#333")
    d.text((452, y+1), "fit       ▾", fill=fg, font=font(11))
    y += 32
    d.text((20, y), "☑ Show overlay on desktop wallpaper", fill=fg, font=font(11))
    d.rectangle([20, y+2, 32, y+14], outline=accent)
    d.text((22, y-1), "✓", fill=accent, font=font(12))
    y += 26
    d.text((20, y), "☑ Apply to lock screen (Windows)", fill=fg, font=font(11))
    d.rectangle([20, y+2, 32, y+14], outline=accent)
    d.text((22, y-1), "✓", fill=accent, font=font(12))

    y += 50
    # Separator
    d.line([20, y, W-20, y], fill="#333", width=1)
    y += 20

    # Buttons
    rounded_rect(d, [20, y, 190, y+36], 4, "#2e7d32")
    d.text((35, y+8), "▶ Launch Screensaver", fill="white", font=font(11, bold=True))

    rounded_rect(d, [200, y, 400, y+36], 4, "#1565c0")
    d.text((210, y+8), "▶ Start Wallpaper Rotator", fill="white", font=font(11, bold=True))

    rounded_rect(d, [420, y, 540, y+36], 4, btn_bg, outline="#333")
    d.text((432, y+8), "💾 Save Settings", fill=fg, font=font(11))

    y += 48
    rounded_rect(d, [20, y, 200, y+36], 4, "#6a1b9a")
    d.text((32, y+8), "⬆ Check for Updates", fill="white", font=font(11))

    y += 50
    d.text((20, y), "✓ Settings saved!", fill="#66bb6a", font=font(10))

    img.save(os.path.join(OUT, "gui-dark.png"), "PNG")
    print("  ✓ gui-dark.png")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Screensaver — fullscreen with overlay
# ═══════════════════════════════════════════════════════════════════════════════
def gen_screensaver():
    W, H = 1280, 720
    # Dark space background gradient
    img = Image.new("RGB", (W, H), "#050510")
    d = ImageDraw.Draw(img)

    # Starfield
    import random
    random.seed(42)
    for _ in range(200):
        x, y = random.randint(0, W), random.randint(0, H)
        bright = random.randint(100, 255)
        size = random.choice([1, 1, 1, 2])
        d.ellipse([x, y, x+size, y+size], fill=(bright, bright, bright+20 if bright<236 else 255))

    # Moon-like circle
    cx, cy, r = 400, 350, 160
    for ring in range(r, 0, -1):
        ratio = ring / r
        c = int(60 + 120 * (1 - ratio))
        d.ellipse([cx-ring, cy-ring, cx+ring, cy+ring], fill=(c, c, c+10 if c<246 else 255))
    # Craters
    for (dx, dy, cr) in [(50, -40, 20), (-30, 60, 15), (70, 30, 12), (-60, -20, 10)]:
        d.ellipse([cx+dx-cr, cy+dy-cr, cx+dx+cr, cy+dy+cr], fill=(80, 80, 85))

    # Overlay panel on the right
    overlay_x = W - 320
    overlay_y = 20
    ow, oh = 300, 500
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([overlay_x, overlay_y, overlay_x+ow, overlay_y+oh], fill=(10, 10, 30, 216), outline=(80, 120, 200, 200))

    mf = mono(13)
    mfb = mono(14)
    lines = [
        ("═══ ARTEMIS PROGRAM ═══", "#4fc3f7", True),
        ("", None, False),
        ("✓ Artemis I  [Completed]", "#66bb6a", False),
        ("    Launch: Nov. 16, 2022", "#e0e0e0", False),
        ("    Duration: 25d 10h 53m", "#e0e0e0", False),
        ("    Type: Uncrewed Lunar Test", "#e0e0e0", False),
        ("", None, False),
        ("✓ Artemis II  [Completed]", "#66bb6a", False),
        ("    Launch: April 1, 2026", "#e0e0e0", False),
        ("    Duration: 9d 1h 32m", "#e0e0e0", False),
        ("    Type: Crewed Lunar Flyby", "#e0e0e0", False),
        ("", None, False),
        ("◇ Artemis III  [Upcoming]", "#64b5f6", False),
        ("    Launch: 2027", "#e0e0e0", False),
        ("", None, False),
        ("◇ Artemis IV  [Upcoming]", "#64b5f6", False),
        ("    Launch: Early 2028", "#e0e0e0", False),
        ("", None, False),
        ("═══ UPCOMING LAUNCHES ═══", "#4fc3f7", True),
        ("", None, False),
        ("▸ NET April 11, 2026", "#ba68c8", False),
        ("  Northrop Grumman CRS-24", "#ba68c8", False),
        ("▸ NET April 2026", "#ba68c8", False),
        ("  Boeing Starliner-1", "#ba68c8", False),
        ("▸ NET May 2026", "#ba68c8", False),
        ("  SpaceX CRS-34", "#ba68c8", False),
        ("", None, False),
        ("── platysoft.com ──", "#7986cb", False),
    ]

    ly = overlay_y + 14
    for text, color, bold in lines:
        if text and color:
            od.text((overlay_x + 14, ly), text, fill=color, font=mfb if bold else mf)
        ly += 17

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(os.path.join(OUT, "screensaver.png"), "PNG")
    print("  ✓ screensaver.png")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Wallpaper with overlay burned on
# ═══════════════════════════════════════════════════════════════════════════════
def gen_wallpaper_overlay():
    W, H = 1280, 720
    # Earth-from-space style gradient
    img = Image.new("RGB", (W, H), "#01050f")
    d = ImageDraw.Draw(img)

    import random
    random.seed(99)
    for _ in range(150):
        x, y = random.randint(0, W), random.randint(0, H)
        b = random.randint(80, 220)
        d.point((x, y), fill=(b, b, b+20 if b<236 else 255))

    # Blue-green Earth arc at bottom-left
    cx, cy, r = -200, H+300, 600
    for ring in range(r, r-120, -1):
        ratio = (ring - (r-120)) / 120
        blue = int(20 + 100 * ratio)
        green = int(10 + 60 * ratio)
        d.ellipse([cx-ring, cy-ring, cx+ring, cy+ring], fill=(0, green, blue))

    # Atmosphere glow
    for ring in range(r, r+40):
        alpha_ratio = 1 - (ring - r) / 40
        c = int(40 * alpha_ratio)
        d.ellipse([cx-ring, cy-ring, cx+ring, cy+ring], outline=(30, 80+c, 180+min(c,75)))

    # Now burn the overlay using the actual burn_overlay function
    from moonjoy.nasa_data import get_overlay_lines
    from moonjoy.wallpaper import burn_overlay
    lines = get_overlay_lines(max_lines=8)
    img = burn_overlay(img, lines, opacity=0.85, page=0)

    img.save(os.path.join(OUT, "wallpaper-overlay.png"), "PNG")
    print("  ✓ wallpaper-overlay.png")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Overlay detail — close-up crop of overlay panel
# ═══════════════════════════════════════════════════════════════════════════════
def gen_overlay_detail():
    W, H = 600, 700
    img = Image.new("RGBA", (W, H), (10, 10, 30, 255))
    d = ImageDraw.Draw(img)

    # Border
    d.rectangle([0, 0, W-1, H-1], outline=(80, 120, 200, 255), width=2)

    mf = mono(16)
    mfb = mono(17)

    lines = [
        ("═══ ARTEMIS PROGRAM ═══", "#4fc3f7", True),
        ("", None, False),
        ("✓ Artemis I  [Completed]", "#66bb6a", False),
        ("    Launch: Nov. 16, 2022", "#e0e0e0", False),
        ("    Duration: 25 days, 10 hours, 53 min", "#e0e0e0", False),
        ("    Type: Uncrewed Lunar Flight Test", "#e0e0e0", False),
        ("", None, False),
        ("✓ Artemis II  [Completed]", "#66bb6a", False),
        ("    Launch: April 1, 2026", "#e0e0e0", False),
        ("    Duration: 9 days, 1 hour, 32 min", "#e0e0e0", False),
        ("    Type: Crewed Lunar Flyby", "#e0e0e0", False),
        ("", None, False),
        ("◇ Artemis III  [Upcoming]", "#64b5f6", False),
        ("    Launch: 2027", "#e0e0e0", False),
        ("    Type: Rendezvous & Docking in LEO", "#e0e0e0", False),
        ("", None, False),
        ("◇ Artemis IV  [Upcoming]", "#64b5f6", False),
        ("    Launch: Early 2028", "#e0e0e0", False),
        ("    Type: First Lunar Landing", "#e0e0e0", False),
        ("", None, False),
        ("◇ Artemis V  [Upcoming]", "#64b5f6", False),
        ("    Launch: Late 2028", "#e0e0e0", False),
        ("    Type: Lunar Surface Mission", "#e0e0e0", False),
        ("", None, False),
        ("═══ UPCOMING LAUNCHES ═══", "#4fc3f7", True),
        ("", None, False),
        ("▸ NET April 11, 2026", "#ba68c8", False),
        ("  Northrop Grumman CRS-24", "#ba68c8", False),
        ("▸ NET April 2026", "#ba68c8", False),
        ("  Boeing Starliner-1", "#ba68c8", False),
        ("▸ NET May 2026", "#ba68c8", False),
        ("  SpaceX CRS-34", "#ba68c8", False),
        ("", None, False),
        ("── platysoft.com ──", "#7986cb", False),
    ]

    ly = 20
    for text, color, bold in lines:
        if text and color:
            d.text((20, ly), text, fill=color, font=mfb if bold else mf)
        ly += 20

    img.convert("RGB").save(os.path.join(OUT, "overlay-detail.png"), "PNG")
    print("  ✓ overlay-detail.png")


if __name__ == "__main__":
    print("Generating website screenshots...")
    gen_gui()
    gen_screensaver()
    gen_wallpaper_overlay()
    gen_overlay_detail()
    print("Done! Images saved to:", OUT)
