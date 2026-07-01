"""
BIE Capture v0.2.1 — Authenticated Strat365 Batch Card Capture

Purpose:
Capture authenticated Strat365 player cards from the discovered role-aware
player universe using saved Playwright browser storage state.

Responsibilities:
- Read player universe when available
- Support limited batch capture
- Support targeted player-id capture
- Reuse one authenticated browser context
- Capture authenticated card HTML
- Validate captured evidence with role-aware semantics
- Write per-card metadata
- Write batch summary

Non-responsibilities:
- No parsing
- No baseball intelligence
- No GBX/FBX derivation
- No ballpark logic
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import time
from typing import Any

from playwright.sync_api import sync_playwright

from baseball.capture.strat365.capture_authenticated_card import (
    CAPTURE_VERSION,
    DEFAULT_AUTH_STATE,
    output_paths,
    player_url,
    summarize_html,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def discovered_players_path(season: int) -> Path:
    universe_path = (
        Path("data/baseball/raw/strat365")
        / str(season)
        / "players"
        / f"{season}_players_universe.json"
    )

    if universe_path.exists():
        return universe_path

    return (
        Path("data/baseball/raw/strat365")
        / str(season)
        / "players"
        / f"{season}_players_discovered.json"
    )


def load_discovered_players(season: int) -> list[dict[str, Any]]:
    path = discovered_players_path(season)

    if not path.exists():
        raise FileNotFoundError(f"Missing discovered players file: {path}")

    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    players = payload.get("players", [])

    if not isinstance(players, list) or not players:
        raise ValueError(f"No players found in discovered players file: {path}")

    return players


def select_players(
    players: list[dict[str, Any]],
    player_ids: list[int] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    if player_ids:
        by_id = {int(player["playerId"]): player for player in players}
        missing = [player_id for player_id in player_ids if player_id not in by_id]

        if missing:
            raise ValueError(f"Player IDs not found in discovery universe: {missing}")

        return [by_id[player_id] for player_id in player_ids]

    if limit is not None:
        return players[:limit]

    return players


def capture_one_with_page(page, season: int, player: dict[str, Any], force: bool) -> dict[str, Any]:
    player_id = int(player["playerId"])
    player_name = player.get("playerName", "")
    role = player.get("role")
    url = player.get("sourceUrl") or player_url(player_id, season)
    html_path, meta_path = output_paths(player_id, season)

    if html_path.exists() and meta_path.exists() and not force:
        try:
            existing_meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
            if existing_meta.get("status") == "validated_authenticated_card":
                return {
                    "provider": "strat365",
                    "season": season,
                    "playerId": player_id,
                    "playerName": player_name,
                    "role": role,
                    "team": player.get("team"),
                    "sourceUrl": url,
                    "htmlFile": str(html_path),
                    "metadataFile": str(meta_path),
                    "capturedAt": existing_meta.get("capturedAt"),
                    "captureVersion": existing_meta.get("captureVersion"),
                    "status": "skipped_existing_validated_authenticated_card",
                    "bytes": existing_meta.get("bytes"),
                    "sha256": existing_meta.get("sha256"),
                    "gatedShell": existing_meta.get("gatedShell"),
                    "tableCount": existing_meta.get("tableCount"),
                    "roleFromHtml": existing_meta.get("roleFromHtml"),
                    "validationRole": existing_meta.get("validationRole"),
                    "hasRequiredCardEvidence": existing_meta.get("hasRequiredCardEvidence"),
                }
        except Exception:
            pass

    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1000)

    html = page.content()
    summary = summarize_html(html, role=role)

    html_path.write_text(html, encoding="utf-8")

    meta = {
        "provider": "strat365",
        "season": season,
        "playerId": player_id,
        "playerName": player_name,
        "role": role,
        "team": player.get("team"),
        "sourceUrl": url,
        "htmlFile": str(html_path),
        "capturedAt": now_utc(),
        "captureVersion": CAPTURE_VERSION,
        "captureMethod": "playwright-storage-state-batch",
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
        "metadataFile": str(meta_path),
        **meta,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture authenticated Strat365 cards for a discovered season."
    )
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--player-ids", nargs="+", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument("--auth-state", default=str(DEFAULT_AUTH_STATE))
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    auth_state_path = Path(args.auth_state)
    if not auth_state_path.exists():
        raise FileNotFoundError(
            f"Missing auth state file: {auth_state_path}. Run capture_auth_state.py first."
        )

    all_players = load_discovered_players(args.season)
    players = select_players(all_players, args.player_ids, args.limit)

    started_at = now_utc()
    results = []

    print("BIE Capture v0.2.1 Authenticated Batch Capture")
    print("=" * 72)
    print(f"Season: {args.season}")
    print(f"Discovery source: {discovered_players_path(args.season)}")
    print(f"Players selected: {len(players)}")
    print(f"Targeted player IDs: {args.player_ids if args.player_ids else '(none)'}")
    print(f"Auth state: {auth_state_path}")
    print(f"Force recapture: {args.force}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
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

        for index, player in enumerate(players, start=1):
            player_id = int(player["playerId"])
            player_name = player.get("playerName", "")
            role = player.get("role", "unknown")

            try:
                result = capture_one_with_page(
                    page=page,
                    season=args.season,
                    player=player,
                    force=args.force,
                )
                results.append(result)

                status = result.get("status")
                html_role = result.get("roleFromHtml")
                print(f"[{index}/{len(players)}] {status} {player_id} {player_name} role={role} htmlRole={html_role}")

            except Exception as exc:
                error = {
                    "provider": "strat365",
                    "season": args.season,
                    "playerId": player_id,
                    "playerName": player_name,
                    "role": role,
                    "sourceUrl": player_url(player_id, args.season),
                    "capturedAt": now_utc(),
                    "captureVersion": CAPTURE_VERSION,
                    "status": "capture_failed",
                    "error": str(exc),
                }
                results.append(error)
                print(f"[{index}/{len(players)}] capture_failed {player_id} {player_name} role={role}: {exc}")

            if args.sleep_seconds:
                time.sleep(args.sleep_seconds)

        browser.close()

    validated = sum(1 for r in results if r.get("status") == "validated_authenticated_card")
    skipped_validated = sum(
        1 for r in results
        if r.get("status") == "skipped_existing_validated_authenticated_card"
    )
    failed = sum(1 for r in results if r.get("status") in {"capture_failed", "validation_failed"})

    role_counts = {}
    for item in results:
        role = item.get("role") or "unknown"
        role_counts[role] = role_counts.get(role, 0) + 1

    summary_dir = Path("data/baseball/raw/strat365/authenticated") / str(args.season)
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "authenticated_card_capture_summary.json"

    summary = {
        "provider": "strat365",
        "season": args.season,
        "captureVersion": CAPTURE_VERSION,
        "captureMethod": "playwright-storage-state-batch",
        "discoverySource": str(discovered_players_path(args.season)),
        "startedAt": started_at,
        "completedAt": now_utc(),
        "playersSelected": len(players),
        "targetedPlayerIds": args.player_ids,
        "roleCounts": role_counts,
        "validatedAuthenticatedCards": validated,
        "skippedExistingValidatedAuthenticatedCards": skipped_validated,
        "failed": failed,
        "authStateFile": str(auth_state_path),
        "results": results,
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print("Batch summary")
    print("-" * 72)
    print(f"Summary: {summary_path}")
    print(f"Players selected: {len(players)}")
    print(f"Role counts: {role_counts}")
    print(f"Validated authenticated cards: {validated}")
    print(f"Skipped existing validated cards: {skipped_validated}")
    print(f"Failed: {failed}")

    if failed:
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
