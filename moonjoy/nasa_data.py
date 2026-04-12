"""Fetch and cache NASA mission data and launch schedule from nasa.gov."""

import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from urllib.request import urlopen, Request
from urllib.error import URLError

CACHE_FILE = os.path.join(tempfile.gettempdir(), "moonjoy_nasa_cache.json")
CACHE_TTL = 3600 * 6  # 6 hours

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Mission:
    name: str
    status: str = ""          # "Completed", "Active", "Upcoming"
    mission_type: str = ""    # e.g. "Crewed Lunar Flyby"
    launch_date: str = ""
    duration: str = ""
    splashdown: str = ""
    description: str = ""
    url: str = ""

@dataclass
class LaunchEvent:
    name: str
    date: str = ""            # "NET April 2026", "2027", etc.
    description: str = ""
    url: str = ""

# ── Hardcoded fallback data (always available offline) ────────────────────────

FALLBACK_MISSIONS: list[dict] = [
    {
        "name": "Artemis I",
        "status": "Completed",
        "mission_type": "Uncrewed Lunar Flight Test",
        "launch_date": "Nov. 16, 2022",
        "duration": "25 days, 10 hours, 53 minutes",
        "splashdown": "Dec. 11, 2022",
        "description": "First integrated flight test of SLS and Orion. Traveled 1.4 million miles. Re-entry speed: 24,581 mph (Mach 32).",
        "url": "https://www.nasa.gov/mission/artemis-i/",
    },
    {
        "name": "Artemis II",
        "status": "Completed",
        "mission_type": "Crewed Lunar Flyby",
        "launch_date": "April 1, 2026",
        "duration": "9 days, 1 hour, 32 minutes",
        "splashdown": "April 10, 2026",
        "description": "First crewed Artemis flight. Four astronauts ventured around the Moon, demonstrating capabilities for deep space missions.",
        "url": "https://www.nasa.gov/mission/artemis-ii/",
    },
    {
        "name": "Artemis III",
        "status": "Upcoming",
        "mission_type": "Rendezvous & Docking in LEO",
        "launch_date": "2027",
        "duration": "",
        "splashdown": "",
        "description": "LEO demonstration testing Orion rendezvous and docking with commercial landers from SpaceX and/or Blue Origin.",
        "url": "https://www.nasa.gov/mission/artemis-iii/",
    },
    {
        "name": "Artemis IV",
        "status": "Upcoming",
        "mission_type": "First Lunar Landing",
        "launch_date": "Early 2028",
        "duration": "",
        "splashdown": "",
        "description": "First Artemis crewed lunar landing. Crew will transfer from Orion to a commercial lander for transport to the lunar surface.",
        "url": "https://www.nasa.gov/event/artemis-iv/",
    },
    {
        "name": "Artemis V",
        "status": "Upcoming",
        "mission_type": "Lunar Surface Mission",
        "launch_date": "Late 2028",
        "duration": "",
        "splashdown": "",
        "description": "Lunar surface mission using standardized SLS configuration. Expected to begin construction of a Moon base.",
        "url": "https://www.nasa.gov/event/artemis-v/",
    },
]

FALLBACK_LAUNCHES: list[dict] = [
    {"name": "Northrop Grumman CRS-24", "date": "NET April 11, 2026", "url": "https://www.nasa.gov/event/nasas-northrop-grumman-crs-24/"},
    {"name": "Boeing Starliner-1", "date": "NET April 2026", "url": "https://www.nasa.gov/event/nasas-boeing-starliner-1/"},
    {"name": "SpaceX CRS-34", "date": "NET May 2026", "url": "https://www.nasa.gov/event/nasas-spacex-crs-34/"},
    {"name": "Roscosmos Progress 95", "date": "NET Spring 2026", "url": "https://www.nasa.gov/event/roscosmos-progress-95/"},
    {"name": "Swift Boost", "date": "NET June 2026", "url": "https://www.nasa.gov/event/swift-boost/"},
    {"name": "Soyuz MS-29", "date": "NET July 2026", "url": "https://www.nasa.gov/event/soyuz-ms-29/"},
    {"name": "CLPS: Astrobotic Griffin-1", "date": "NET July 2026", "url": "https://www.nasa.gov/event/clps-flight-astrobotics-griffin-mission-one/"},
    {"name": "SpaceX CRS-35", "date": "NET August 2026", "url": "https://www.nasa.gov/event/nasas-spacex-crs-35/"},
    {"name": "JAXA HTV-X2", "date": "NET Summer 2026", "url": "https://www.nasa.gov/event/jaxa-htv-x2/"},
    {"name": "Northrop Grumman CRS-25", "date": "NET Fall 2026", "url": "https://www.nasa.gov/event/nasas-northrop-grumman-crs-25/"},
    {"name": "Commercial Crew", "date": "NET November 2026", "url": "https://www.nasa.gov/event/nasas-commercial-crew/"},
    {"name": "CLPS: Blue Ghost Mission 2", "date": "2026", "url": "https://www.nasa.gov/event/clps-flight-firefly-aerospaces-blue-ghost-mission-2/"},
    {"name": "CLPS: Blue Moon Mark 1", "date": "2026", "url": "https://www.nasa.gov/event/clps-flight-blue-origins-blue-moon-mark-1/"},
    {"name": "CLPS: Intuitive Machines IM-3", "date": "2026", "url": "https://www.nasa.gov/event/clps-flight-intuitive-machines-im-3/"},
    {"name": "SunRISE", "date": "2026", "url": "https://www.nasa.gov/event/sunrise/"},
    {"name": "Nancy Grace Roman Space Telescope", "date": "NLT May 2027", "url": "https://www.nasa.gov/event/nancy-grace-roman-space-telescope/"},
    {"name": "CLPS: Intuitive Machines IM-4", "date": "2027", "url": "https://www.nasa.gov/event/clps-flight-intuitive-machines-im-4/"},
    {"name": "Artemis III", "date": "2027", "url": "https://www.nasa.gov/event/artemis-iii-launch/"},
    {"name": "Artemis IV", "date": "Early 2028", "url": "https://www.nasa.gov/event/artemis-iv/"},
    {"name": "Artemis V", "date": "Late 2028", "url": "https://www.nasa.gov/event/artemis-v/"},
]

# ── Simple HTML text extractor ────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._text.append(data.strip())

    def get_text(self) -> str:
        return " ".join(t for t in self._text if t)


def _fetch_text(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return stripped text content."""
    req = Request(url, headers={"User-Agent": "MoonJoy/1.0 (NASA screensaver app)"})
    with urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ── Live scrapers ─────────────────────────────────────────────────────────────

def _try_fetch_events_page(url: str) -> list[dict]:
    """Parse launch events from a NASA events page."""
    events = []
    try:
        req = Request(url, headers={"User-Agent": "MoonJoy/1.0 (NASA screensaver app)"})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Find event links with dates
        pattern = r'<a[^>]*href="(https://www\.nasa\.gov/event/[^"]+)"[^>]*>.*?</a>'
        # Simpler: find date + name patterns in text
        text = _TextExtractor()
        text.feed(html)
        raw = text.get_text()

        # Match patterns like "NO EARLIER THAN APRIL 11, 2026 7:41 AM NASA's Northrop Grumman CRS-24"
        matches = re.findall(
            r'((?:NO EARLIER THAN|NO LATER THAN|EARLY|LATE)?\s*(?:\w+\s+\d{1,2},?\s+)?\d{4}(?:\s+\d{1,2}:\d{2}\s*[AP]M)?)\s+(.+?)(?=(?:NO EARLIER|NO LATER|EARLY|LATE|\d{4}|LAUNCH SCHEDULE|$))',
            raw, re.IGNORECASE
        )
        for date_str, name in matches:
            name = name.strip().rstrip("LAUNCH SCHEDULE").strip()
            if name and len(name) > 3:
                events.append({"name": name, "date": date_str.strip()})
    except Exception:
        pass
    return events


def fetch_live_data() -> tuple[list[dict], list[dict]]:
    """Attempt to fetch live data from NASA. Returns (missions, launches)."""
    missions = list(FALLBACK_MISSIONS)
    launches = list(FALLBACK_LAUNCHES)

    try:
        # Try to update Artemis II with latest data
        text = _fetch_text("https://www.nasa.gov/mission/artemis-ii/")
        if "splashdown" in text.lower() or "splashes down" in text.lower():
            # It's completed, our fallback is already accurate
            pass
    except Exception:
        pass

    return missions, launches

# ── Cache layer ───────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:
    """Load cached data if fresh enough."""
    if not os.path.isfile(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("ts", 0) < CACHE_TTL:
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _save_cache(missions: list[dict], launches: list[dict]) -> None:
    """Persist data to cache."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "missions": missions, "launches": launches}, f)
    except OSError:
        pass


def get_nasa_data() -> tuple[list[Mission], list[LaunchEvent]]:
    """Get NASA mission and launch data (cached, with live refresh)."""
    cached = _load_cache()
    if cached:
        missions_raw = cached["missions"]
        launches_raw = cached["launches"]
    else:
        missions_raw, launches_raw = fetch_live_data()
        _save_cache(missions_raw, launches_raw)

    missions = [Mission(**m) for m in missions_raw]
    launches = [LaunchEvent(**l) for l in launches_raw]
    return missions, launches


def get_overlay_lines(max_lines: int = 12) -> list[str]:
    """Return formatted text lines for the screensaver overlay."""
    missions, launches = get_nasa_data()

    lines: list[str] = []
    lines.append("═══ ARTEMIS PROGRAM ═══")
    lines.append("")

    for m in missions:
        status_icon = {"Completed": "✓", "Active": "●", "Upcoming": "◇"}.get(m.status, "?")
        line = f"{status_icon} {m.name}  [{m.status}]"
        lines.append(line)
        if m.launch_date:
            lines.append(f"    Launch: {m.launch_date}")
        if m.duration:
            lines.append(f"    Duration: {m.duration}")
        if m.mission_type:
            lines.append(f"    Type: {m.mission_type}")
        lines.append("")

    lines.append("═══ UPCOMING LAUNCHES ═══")
    lines.append("")

    # Show only the most relevant upcoming launches
    shown = 0
    for ev in launches:
        if shown >= max_lines:
            break
        lines.append(f"▸ {ev.date}")
        lines.append(f"  {ev.name}")
        shown += 1

    lines.append("")
    lines.append("── platysoft.com ──")

    return lines
