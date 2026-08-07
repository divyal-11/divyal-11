"""
fetch_contributions.py

GitHub serves your contribution calendar as a public HTML fragment at
https://github.com/users/<username>/contributions -- the same markup the
profile page itself uses. No GraphQL API and no personal access token needed.

Usage:
    python fetch_contributions.py <github-username>
    # writes: ../data/contributions.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-art-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub's markup has changed shape over the years; this handles both the
    # older <rect class="ContributionCalendar-day"> and newer <td> layouts.
    cells = soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day")
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        level = cell.get("data-level")
        count_attr = cell.get("data-count")
        if count_attr is not None:
            count = int(count_attr)
        else:
            tooltip_id = cell.get("aria-labelledby") or cell.get("id")
            count = None  # fallback below uses tooltip text if present
        days.append(
            {
                "date": date,
                "level": int(level) if level is not None else None,
                "count": count,
            }
        )

    # Some layouts put the count in a paired <tool-tip> element instead of
    # data-count; fill those in from tooltip text ("N contributions on ...").
    if any(d["count"] is None for d in days):
        tooltip_text = {}
        for tip in soup.select("tool-tip, .sr-only"):
            tid = tip.get("id")
            if tid:
                tooltip_text[tid] = tip.get_text(strip=True)
        for cell, d in zip(cells, days):
            if d["count"] is None:
                tid = cell.get("id")
                text = tooltip_text.get(tid, "")
                digits = "".join(ch for ch in text.split(" ")[0] if ch.isdigit())
                d["count"] = int(digits) if digits else 0

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] or 0 for d in days)

    current_streak = 0
    for d in reversed(days):
        if (d["count"] or 0) > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if (d["count"] or 0) > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"] or 0, default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + (d["count"] or 0)

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly,
    }


def main(username: str) -> None:
    html = fetch_html(username)
    days = parse_days(html)
    stats = compute_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {DATA_PATH} ({len(days)} days, {stats['total_last_year']} contributions)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_contributions.py <github-username>")
        sys.exit(1)
    main(sys.argv[1])
