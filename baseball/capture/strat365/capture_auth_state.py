"""
BIE Capture v0.2.1 Auth State Bootstrap

Purpose:
Open a real browser, allow manual Strat365 login, save authenticated
browser storage state locally, then verify whether Keith Hernandez's
card can be seen as authenticated evidence.

Security:
- Does not print cookies.
- Does not print storage tokens.
- Writes auth state only under .bie-auth/, which is gitignored.
- Writes authenticated HTML only under data/baseball/raw/strat365/authenticated/,
  which is gitignored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sys

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


ROOT = Path.cwd()
BASE_URL = "https://365.strat-o-matic.com"

SEASON = 1980
PLAYER_ID = 35273
PLAYER_NAME = "Hernandez, Keith"
PLAYER_URL = f"{BASE_URL}/player/{PLAYER_ID}/{SEASON}/4/{SEASON}"

AUTH_DIR = ROOT / ".bie-auth"
AUTH_STATE_PATH = AUTH_DIR / "strat365-storage-state.json"

OUT_DIR = ROOT / "data" / "baseball" / "raw" / "strat365" / "authenticated" / str(SEASON) / "cards"
HTML_PATH = OUT_DIR / f"{PLAYER_ID}.html"
META_PATH = OUT_DIR / f"{PLAYER_ID}.capture.json"

REQUIRED_MARKERS = [
    "Balance",
    "Defense",
    "Running",
    "SINGLE",
    "HOMERUN",
    "DO",
    "TR",
    "GB",
    "Fly",
    "Strikeout",
    "Walk",
]

GATED_MARKER = "must have purchased and be logged in"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def summarize_html(html: str) -> dict:
    lower = html.lower()

    return {
        "bytes": len(html.encode("utf-8", errors="replace")),
        "sha256": sha256_text(html),
        "gatedShell": GATED_MARKER in lower,
        "tableCount": len(re.findall(r"<table\\b", html, flags=re.I)),
        "markers": {marker: (marker.lower() in lower) for marker in REQUIRED_MARKERS},
    }


def main() -> int:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("BIE Capture v0.2.1 Auth Bootstrap")
    print("=" * 72)
    print(f"Repo root: {ROOT}")
    print(f"Auth state path: {AUTH_STATE_PATH}")
    print(f"Verification URL: {PLAYER_URL}")
    print()
    print("A Chromium browser will open.")
    print("Log into Strat365 in that browser until you can access your Baseball 365 team/card content.")
    print("When login is complete, return to this PowerShell window and press Enter.")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)

        input("After you are logged in inside the opened browser, press Enter here... ")

        print()
        print("Saving authenticated browser storage state...")
        context.storage_state(path=str(AUTH_STATE_PATH))

        print("Testing authenticated access to Keith Hernandez...")
        page.goto(PLAYER_URL, wait_until="networkidle", timeout=60000)

        try:
            page.wait_for_timeout(1500)
        except PlaywrightTimeoutError:
            pass

        html = page.content()
        summary = summarize_html(html)

        HTML_PATH.write_text(html, encoding="utf-8")

        meta = {
            "provider": "strat365",
            "season": SEASON,
            "playerId": PLAYER_ID,
            "playerName": PLAYER_NAME,
            "sourceUrl": PLAYER_URL,
            "htmlFile": str(HTML_PATH),
            "capturedAt": now_utc(),
            "captureVersion": "0.2.1-auth-bootstrap",
            "captureMethod": "playwright-authenticated-browser-context",
            "authStateFile": str(AUTH_STATE_PATH),
            "bytes": summary["bytes"],
            "sha256": summary["sha256"],
            "gatedShell": summary["gatedShell"],
            "tableCount": summary["tableCount"],
            "markers": summary["markers"],
            "status": "authenticated" if not summary["gatedShell"] and any(summary["markers"].values()) else "not_authenticated",
        }

        META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        browser.close()

    print()
    print("Verification summary")
    print("-" * 72)
    print(f"HTML written: {HTML_PATH}")
    print(f"Metadata written: {META_PATH}")
    print(f"Bytes: {summary['bytes']}")
    print(f"SHA256: {summary['sha256']}")
    print(f"Gated shell: {summary['gatedShell']}")
    print(f"HTML table count: {summary['tableCount']}")
    print()

    print("Required marker check")
    print("-" * 72)
    for marker, present in summary["markers"].items():
        print(f"{marker:10} {present}")

    print()
    if not summary["gatedShell"] and any(summary["markers"].values()):
        print("AUTHENTICATED CAPTURE APPEARS SUCCESSFUL")
        return 0

    print("AUTHENTICATED CAPTURE NOT YET VERIFIED")
    print("The browser state was saved, but the Keith Hernandez page still does not show card evidence.")
    print("Next likely causes: wrong account context, no active Baseball 365 team context, referer/team requirement, or alternate card endpoint.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
