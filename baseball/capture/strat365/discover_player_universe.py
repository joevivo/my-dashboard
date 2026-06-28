"""
BIE Capture v0.2.1 — Strat365 Role-Aware Player Universe Discovery

Purpose:
Discover both hitter and pitcher player records from the Strat365 public
player browser before authenticated card capture.

Responsibilities:
- Discover hitters with position_id=10
- Discover pitchers with position_id=1
- Preserve raw row text and source URL
- Preserve role-specific fields where safely observable
- Write separate hitter/pitcher manifests
- Write combined player universe manifest

Non-responsibilities:
- No authenticated capture
- No card parsing
- No baseball intelligence
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import time
from typing import Any

from bs4 import BeautifulSoup

from baseball.capture.strat365.session import Strat365Session


BASE_URL = "https://365.strat-o-matic.com"
DISCOVERY_VERSION = "0.2.1"

ROLE_CONFIG = {
    "hitters": {
        "position_id": "10",
        "role": "hitter",
    },
    "pitchers": {
        "position_id": "1",
        "role": "pitcher",
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def source_url(player_id: int, season: int) -> str:
    return f"{BASE_URL}/player/{player_id}/{season}/4/{season}"


def parse_player_rows(html: str, season: int, role: str, position_id: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    players_by_id: dict[int, dict[str, Any]] = {}

    for a in soup.find_all("a"):
        href = a.get("href") or ""
        match = re.search(r"/player/(\d+)/", href)
        if not match:
            continue

        player_id = int(match.group(1))
        row = a.find_parent("tr")
        cells = row.find_all("td") if row else []
        cell_texts = [clean(cell.get_text(" ", strip=True)) for cell in cells]
        row_text = clean(row.get_text(" ", strip=True)) if row else clean(a.get_text(" ", strip=True))

        player = {
            "provider": "strat365",
            "season": season,
            "playerId": player_id,
            "playerName": clean(a.get_text(" ", strip=True)),
            "sourceUrl": source_url(player_id, season),
            "rowText": row_text,
            "role": role,
            "positionId": position_id,
            "status": "discovered",
        }

        # Current observed browser table:
        # Hitters:  name, team, bats, position, ...
        # Pitchers: name, team, throws, pitching role/rating, ...
        if len(cell_texts) > 1:
            player["team"] = cell_texts[1]

        if role == "hitter":
            if len(cell_texts) > 2:
                player["bats"] = cell_texts[2]
            if len(cell_texts) > 3:
                player["position"] = cell_texts[3]
        elif role == "pitcher":
            if len(cell_texts) > 2:
                player["throws"] = cell_texts[2]
            if len(cell_texts) > 3:
                player["pitchingRole"] = cell_texts[3]

        players_by_id[player_id] = player

    return list(players_by_id.values())


def discover_role(
    session: Strat365Session,
    season: int,
    role_name: str,
    start_row_step: int,
    max_start_row: int,
    sleep_seconds: float,
) -> dict[str, Any]:
    config = ROLE_CONFIG[role_name]
    path = f"/playerset/browse/{season}"

    all_players: dict[int, dict[str, Any]] = {}
    pages = []

    start_row = 0

    while True:
        request_payload = {
            "start_row": str(start_row),
            "position_id": config["position_id"],
        }

        html = session.post(path, data=request_payload)
        page_players = parse_player_rows(
            html=html,
            season=season,
            role=config["role"],
            position_id=config["position_id"],
        )

        new_count = 0
        for player in page_players:
            player_id = int(player["playerId"])
            if player_id not in all_players:
                all_players[player_id] = player
                new_count += 1

        pages.append({
            "startRow": start_row,
            "requestPayload": request_payload,
            "playersFoundOnPage": len(page_players),
            "newPlayersOnPage": new_count,
            "html": html,
        })

        print(
            f"{role_name} start_row {start_row}: "
            f"found {len(page_players)}, {new_count} new, total {len(all_players)}"
        )

        start_row += start_row_step

        if not page_players or new_count == 0:
            break

        if start_row > max_start_row:
            raise RuntimeError(f"Pagination safety stop reached for {role_name}")

        if sleep_seconds:
            time.sleep(sleep_seconds)

    players = sorted(all_players.values(), key=lambda item: item["playerId"])

    return {
        "provider": "strat365",
        "season": season,
        "discoveryVersion": DISCOVERY_VERSION,
        "roleName": role_name,
        "role": config["role"],
        "positionId": config["position_id"],
        "discoveredAt": now_utc(),
        "requestPath": path,
        "startRowStep": start_row_step,
        "pageCount": len(pages),
        "playerCount": len(players),
        "players": players,
        "rawPages": pages,
    }


def write_role_outputs(season: int, role_name: str, payload: dict[str, Any]) -> Path:
    out_dir = Path("data/baseball/raw/strat365") / str(season) / "players"
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / f"{season}_{role_name}_discovered.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_universe(season: int, role_payloads: list[dict[str, Any]]) -> Path:
    out_dir = Path("data/baseball/raw/strat365") / str(season) / "players"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_players: dict[int, dict[str, Any]] = {}
    duplicate_ids = []

    for payload in role_payloads:
        for player in payload.get("players", []):
            player_id = int(player["playerId"])
            if player_id in all_players:
                duplicate_ids.append(player_id)
            all_players[player_id] = player

    players = sorted(all_players.values(), key=lambda item: (item.get("role", ""), item["playerId"]))

    role_counts = {}
    for player in players:
        role = player.get("role", "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1

    universe = {
        "provider": "strat365",
        "season": season,
        "discoveryVersion": DISCOVERY_VERSION,
        "discoveredAt": now_utc(),
        "playerCount": len(players),
        "roleCounts": role_counts,
        "duplicatePlayerIdsAcrossRoles": sorted(set(duplicate_ids)),
        "sourceFiles": [
            f"data/baseball/raw/strat365/{season}/players/{season}_{payload['roleName']}_discovered.json"
            for payload in role_payloads
        ],
        "players": players,
    }

    path = out_dir / f"{season}_players_universe.json"
    path.write_text(json.dumps(universe, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover Strat365 hitter and pitcher player universe for a season."
    )
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--start-row-step", type=int, default=50)
    parser.add_argument("--max-start-row", type=int, default=5000)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument(
        "--roles",
        nargs="+",
        default=["hitters", "pitchers"],
        choices=sorted(ROLE_CONFIG.keys()),
    )

    args = parser.parse_args()

    print("BIE Role-Aware Player Universe Discovery")
    print("=" * 72)
    print(f"Season: {args.season}")
    print(f"Roles: {', '.join(args.roles)}")
    print()

    session = Strat365Session()

    role_payloads = []
    for role_name in args.roles:
        payload = discover_role(
            session=session,
            season=args.season,
            role_name=role_name,
            start_row_step=args.start_row_step,
            max_start_row=args.max_start_row,
            sleep_seconds=args.sleep_seconds,
        )
        path = write_role_outputs(args.season, role_name, payload)
        role_payloads.append(payload)

        print()
        print(f"Wrote {role_name}: {path}")
        print(f"{role_name} player count: {payload['playerCount']}")
        print()

    universe_path = write_universe(args.season, role_payloads)

    total = sum(payload["playerCount"] for payload in role_payloads)

    print("Universe summary")
    print("-" * 72)
    print(f"Universe: {universe_path}")
    for payload in role_payloads:
        print(f"{payload['role']:8} {payload['playerCount']}")
    print(f"Total role records: {total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
