# Schengen Travel Tracker

A lightweight, fully offline tool for tracking your 90-day Schengen allowance across a rolling 180-day window. Built for travellers who spend extended time in Europe and need to stay on the right side of the rules.

Runs as a local web server on your Mac (or any machine with Python 3). No internet connection required, no accounts, no subscriptions. Data is stored in a plain JSON file you can back up anywhere.

---

## The Schengen 90/180 Rule

Non-EU nationals may spend a maximum of **90 days in any rolling 180-day period** inside the Schengen Area. Both your entry day and your exit day count as full days. The 180-day window is not fixed — it rolls back from any given date, so the calculation is more nuanced than it first appears.

Schengen countries covered: Austria, Belgium, Croatia, Czech Republic, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Italy, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Netherlands, Norway, Poland, Portugal, Slovakia, Slovenia, Spain, Sweden, Switzerland.

---

## Features

- **Two-person tracking** — follow Person 1 and Person 2 independently or together, with individually editable names
- **Real-time status cards** — days used, days remaining, and the 180-day period your trips sit within
- **Planned trip analysis** — add future trips and see the peak rolling-window count, with warnings if any day of the trip would exceed or reach the 90-day limit
- **Projected peak** — the summary card accounts for ongoing and planned trips at their full extent, not just confirmed days up to today
- **Next available entry** — when at or over limit, shows the first date you can re-enter and how many consecutive days are available from that date, accounting for old trips dropping off the rolling window
- **Available days on entry** — when adding a trip, shows how many days each person has available from the chosen start date, with the latest possible end date
- **Transit day support** — trips that share a boundary day (e.g. France ends 10 Jun, Spain starts 10 Jun) count that day only once
- **Overlap protection** — the app blocks true date overlaps when adding or editing trips, while allowing same-day transitions
- **Older trip archiving** — trips entirely outside the current 180-day window are hidden by default behind a toggle, keeping the view focused
- **Dark mode** — follows your system preference automatically
- **Fully offline** — no CDN calls, no external dependencies; works without an internet connection

---

## Requirements

- Python 3 (pre-installed on macOS)
- No third-party packages required

---

## Getting Started

1. Download `SchengenTravelTracker.py` and place it in a folder of your choice.
2. Open a terminal and run:

```bash
python3 SchengenTravelTracker.py
```

3. Your browser opens automatically at `http://localhost:8765`.
4. Press **Ctrl+C** in the terminal to stop the server.

---

## Data Storage

All data is saved to **`SchengenTravelTracker_data.json`** in the same folder as the script. This is a human-readable JSON file — back it up by copying it alongside the `.py` file to a USB drive, cloud folder, or anywhere else.

The file is created automatically the first time you add a trip or rename a person. Until then, nothing is written to disk.

---

## Usage Notes

- **Entry and exit days** both count as full days (per EU Regulation 610/2013).
- **Status card figures** include the full extent of ongoing and planned trips — not just days confirmed up to today — so the displayed remaining days reflect your committed travel position.
- **Planned trip warnings** use all other trips (past, ongoing, and planned) as context, giving the same picture as the status card.
- **Available days** are calculated by simulating a forward stay day by day, so old trips dropping off the rolling window are naturally accounted for. This means the figure can be higher than a simple `90 − days used` snapshot.
- **Person names** default to Person 1 and Person 2 — click the pencil icon to rename them.

---

## Version History

| Version | Date | Notes |
|---|---|---|
| v2026.06.01 | Jun 2026 | Initial release |

---

## Licence

This project is licensed under the **GNU General Public License v3.0**.

You are free to use, modify, and distribute this software provided that any derivative works are also released under the GPL v3.0. See the [LICENSE](LICENSE) file for the full terms, or visit [gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0).

© 2026 Kit Norriss
