"""
BIE Capture v0.2.1 — Authenticated Strat365 Card Capture

Purpose:
Capture authenticated Strat365 player card HTML using a saved Playwright
browser storage state.

Responsibilities:
- Load authenticated browser state from .bie-auth/
- Capture player card HTML exactly as the authenticated browser sees it
- Save authenticated evidence under the gitignored authenticated evidence path
- Write capture metadata with provenance and validation markers
- Validate authenticated card structure using role-aware semantics

Non-responsibilities:
- No parsing
- No GBX/FBX derivation
- No ballpark logic
- No analytics
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from playwright.sync_api import sync_playwright


BASE_URL = "https://365.strat-o-matic.com"
CAPTURE_VERSION = "0.2.1"

DEFAULT_AUTH_STATE = Path(".bie-auth/strat365-storage-state.json")

COMMON_CARD_MARKERS = [
    "Balance",
]

HITTER_CARD_MARKERS = [
    "Defense",
    "Running",
]

PITCHER_CARD_MARKERS = [
    "Pitcher",
    "Throws",
    "Hold",
]

RESULT_MARKERS = [
    "SINGLE",
    "HOMERUN",
    "HR",
    "DO",
    "TR",
    "GB",
    "Fly",
    "Strikeout",
    "Walk",
]

MIN_RESULT_MARKERS = 4

GATED_MARKER = "must have purchased and be logged in"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def player_url(player_id: int, season: int) -> str:
    return f"{BASE_URL}/player/{player_id}/{season}/4/{season}"


def output_paths(player_id: int, season: int) -> tuple[Path, Path]:
    out_dir = Path("data/baseball/raw/strat365/authenticated") / str(season) / "cards"
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / f"{player_id}.html"
    meta_path = out_dir / f"{player_id}.capture.json"
    return html_path, meta_path


def marker_map(html_lower: str, markers: list[str]) -> dict[str, bool]:
    return {marker: (marker.lower() in html_lower) for marker in markers}


def count_present(markers: dict[str, bool]) -> int:
    return sum(1 for present in markers.values() if present)


def infer_role_from_html(html_lower: str) -> str:
    if "pitcher" in html_lower and ("throws" in html_lower or "starter" in html_lower or "relief" in html_lower):
        return "pitcher"

    if "defense" in html_lower and "running" in html_lower:
        return "hitter"

    return "unknown"


def summarize_html(html: str, role: str | None = None) -> dict[str, Any]:
    lower = html.lower()

    common_markers = marker_map(lower, COMMON_CARD_MARKERS)
    hitter_markers = marker_map(lower, HITTER_CARD_MARKERS)
    pitcher_markers = marker_map(lower, PITCHER_CARD_MARKERS)
    result_markers = marker_map(lower, RESULT_MARKERS)

    gated_shell = GATED_MARKER in lower
    table_count = len(re.findall(r"<table\b", html, flags=re.I))

    role_from_html = infer_role_from_html(lower)
    validation_role = role or role_from_html

    common_marker_count = count_present(common_markers)
    hitter_marker_count = count_present(hitter_markers)
    pitcher_marker_count = count_present(pitcher_markers)
    result_marker_count = count_present(result_markers)

    has_common_structure = (
        not gated_shell
        and table_count > 0
        and common_marker_count == len(COMMON_CARD_MARKERS)
        and result_marker_count >= MIN_RESULT_MARKERS
    )

    if validation_role == "hitter":
        has_role_structure = hitter_marker_count == len(HITTER_CARD_MARKERS)
    elif validation_role == "pitcher":
        # Pitcher cards may say starter, relief, or both. They do not use hitter
        # Defense/Running labels, so validation must not require them.
        has_role_structure = pitcher_marker_count >= 2
    else:
        has_role_structure = (
            hitter_marker_count == len(HITTER_CARD_MARKERS)
            or pitcher_marker_count >= 2
        )

    has_authenticated_card_structure = has_common_structure and has_role_structure

    markers = {
        **common_markers,
        **hitter_markers,
        **pitcher_markers,
        **result_markers,
    }

    return {
        "bytes": len(html.encode("utf-8", errors="replace")),
        "sha256": sha256_text(html),
        "gatedShell": gated_shell,
        "tableCount": table_count,
        "markers": markers,
        "roleFromHtml": role_from_html,
        "validationRole": validation_role,
        "commonMarkerCount": common_marker_count,
        "hitterMarkerCount": hitter_marker_count,
        "pitcherMarkerCount": pitcher_marker_count,
        "resultMarkerCount": result_marker_count,
        "minResultMarkers": MIN_RESULT_MARKERS,
        "hasRequiredCardEvidence": has_authenticated_card_structure,
        "status": (
            "validated_authenticated_card"
            if has_authenticated_card_structure
            else "validation_failed"
        ),
    }


def player_universe_path(season: int) -> Path:
    return (
        Path("data/baseball/raw/strat365")
        / str(season)
        / "players"
        / f"{season}_players_universe.json"
    )


def legacy_players_path(season: int) -> Path:
    return (
        Path("data/baseball/raw/strat365")
        / str(season)
        / "players"
        / f"{season}_players_discovered.json"
    )


def read_player_record(player_id: int, season: int) -> dict[str, Any]:
    candidates = [player_universe_path(season), legacy_players_path(season)]

    for path in candidates:
        if not path.exists():
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue

        for player in payload.get("players", []):
            try:
                if int(player.get("playerId")) == int(player_id):
                    return player
            except Exception:
                continue

    return {}


def capture_authenticated_card(
    player_id: int,
    season: int,
    auth_state_path: Path,
    headless: bool,
) -> dict[str, Any]:
    if not auth_state_path.exists():
        raise FileNotFoundError(
            f"Missing auth state file: {auth_state_path}. "
            "Run capture_auth_state.py first."
        )

    url = player_url(player_id, season)
    html_path, meta_path = output_paths(player_id, season)
    player_record = read_player_record(player_id, season)

    player_name = player_record.get("playerName", "")
    role = player_record.get("role")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=str(auth_state_path),
            viewport={"width": 1440, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1000)

        html = page.content()
        browser.close()

    summary = summarize_html(html, role=role)
    html_path.write_text(html, encoding="utf-8")

    meta = {
        "provider": "strat365",
        "season": season,
        "playerId": player_id,
        "playerName": player_name,
        "role": role,
        "team": player_record.get("team"),
        "sourceUrl": url,
        "htmlFile": str(html_path),
        "capturedAt": now_utc(),
        "captureVersion": CAPTURE_VERSION,
        "captureMethod": "playwright-storage-state",
        "authStateFile": str(auth_state_path),
        "bytes": summary["bytes"],
        "sha256": summary["sha256"],
        "gatedShell": summary["gatedShell"],
        "tableCount": summary["tableCount"],
        "markers": summary["markers"],
        "roleFromHtml": summary["roleFromHtml"],
        "validationRole": summary["validationRole"],
        "commonMarkerCount": summary["commonMarkerCount"],
        "hitterMarkerCount": summary["hitterMarkerCount"],
        "pitcherMarkerCount": summary["pitcherMarkerCount"],
        "resultMarkerCount": summary["resultMarkerCount"],
        "minResultMarkers": summary["minResultMarkers"],
        "hasRequiredCardEvidence": summary["hasRequiredCardEvidence"],
        "status": summary["status"],
    }

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "htmlPath": str(html_path),
        "metaPath": str(meta_path),
        **meta,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture an authenticated Strat365 player card."
    )
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--player-id", required=True, type=int)
    parser.add_argument(
        "--auth-state",
        default=str(DEFAULT_AUTH_STATE),
        help="Path to Playwright storage state JSON.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser visibly instead of headless.",
    )

    args = parser.parse_args()

    result = capture_authenticated_card(
        player_id=args.player_id,
        season=args.season,
        auth_state_path=Path(args.auth_state),
        headless=not args.headed,
    )

    print("BIE Capture v0.2.1 Authenticated Card Capture")
    print("=" * 72)
    print(f"Player: {result['playerId']} {result.get('playerName', '')}")
    print(f"Role: {result.get('role')} / html={result.get('roleFromHtml')} / validation={result.get('validationRole')}")
    print(f"Season: {result['season']}")
    print(f"URL: {result['sourceUrl']}")
    print(f"HTML: {result['htmlPath']}")
    print(f"Metadata: {result['metaPath']}")
    print(f"Status: {result['status']}")
    print(f"Gated shell: {result['gatedShell']}")
    print(f"HTML table count: {result['tableCount']}")
    print(f"Common marker count: {result['commonMarkerCount']}")
    print(f"Hitter marker count: {result['hitterMarkerCount']}")
    print(f"Pitcher marker count: {result['pitcherMarkerCount']}")
    print(f"Result marker count: {result['resultMarkerCount']}")
    print(f"Bytes: {result['bytes']}")
    print(f"SHA256: {result['sha256']}")
    print()

    print("Marker check")
    print("-" * 72)
    for marker, present in result["markers"].items():
        print(f"{marker:10} {present}")

    if result["status"] != "validated_authenticated_card":
        print()
        print("AUTHENTICATED CAPTURE VALIDATION FAILED")
        return 2

    print()
    print("AUTHENTICATED CAPTURE VALIDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
