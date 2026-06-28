"""
BIE Component:
Capture

Purpose:
Discover Strat365 players for a season from the public player browser.

Produces:
Discovered player JSON
Raw browser HTML

Does NOT:
Capture card HTML
Parse cards
Normalize outcomes
Derive intelligence

Version:
0.3
"""

from pathlib import Path
from bs4 import BeautifulSoup
import argparse
import json
import re
from datetime import datetime, timezone

from baseball.capture.strat365.session import Strat365Session

PLAYER_RE = re.compile(r"/player/(\d+)/[^'\"\)]*")


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def clean(text):
    return " ".join((text or "").replace("\xa0", " ").split())


def clean_player_url(session, href):
    match = PLAYER_RE.search(href)
    if not match:
        return session.url(href)
    return session.url(match.group(0))


def discover_players(html, session, season):
    soup = BeautifulSoup(html, "lxml")
    players = {}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = PLAYER_RE.search(href)
        if not match:
            continue

        player_id = int(match.group(1))
        row = link.find_parent("tr")
        cells = row.find_all("td") if row else []

        players[player_id] = {
            "provider": "strat365",
            "season": season,
            "playerId": player_id,
            "playerName": clean(link.get_text(" ", strip=True)),
            "sourceUrl": clean_player_url(session, href),
            "rowText": clean(row.get_text(" ", strip=True)) if row else "",
            "team": clean(cells[1].get_text(" ", strip=True)) if len(cells) > 1 else "",
            "bats": clean(cells[2].get_text(" ", strip=True)) if len(cells) > 2 else "",
            "position": clean(cells[3].get_text(" ", strip=True)) if len(cells) > 3 else "",
            "status": "discovered"
        }

    return list(players.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--start-row-step", type=int, default=50)
    parser.add_argument("--expected-count", type=int, default=None)
    args = parser.parse_args()

    session = Strat365Session()
    path = f"/playerset/browse/{args.season}"

    out_dir = Path(f"data/baseball/raw/strat365/{args.season}/players")
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / f"{args.season}_player_browser.html"
    json_path = out_dir / f"{args.season}_players_discovered.json"

    all_players = {}
    raw_pages = []

    start_row = 0
    while True:
        html = session.post(path, data={"start_row": str(start_row)})
        raw_pages.append({"startRow": start_row, "html": html})

        page_players = discover_players(html, session, args.season)
        new_count = 0

        for player in page_players:
            if player["playerId"] not in all_players:
                all_players[player["playerId"]] = player
                new_count += 1

        print(f"start_row {start_row}: found {len(page_players)} players, {new_count} new")

        start_row += args.start_row_step

        if args.expected_count and len(all_players) >= args.expected_count:
            break

        if not page_players or new_count == 0:
            break

        if start_row > 5000:
            raise RuntimeError("Pagination safety stop reached")

    combined_html = "\n\n<!-- BIE PAGE BREAK -->\n\n".join(p["html"] for p in raw_pages)
    raw_path.write_text(combined_html, encoding="utf-8")

    players = list(all_players.values())

    payload = {
        "provider": "strat365",
        "season": args.season,
        "discoveredAt": now_utc(),
        "startRowStep": args.start_row_step,
        "pageCount": len(raw_pages),
        "playerCount": len(players),
        "players": players
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Saved raw HTML: {raw_path}")
    print(f"Saved discovered players: {json_path}")
    print(f"Players discovered: {len(players)}")


if __name__ == "__main__":
    main()
