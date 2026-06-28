from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import time

from baseball.capture.strat365.session import Strat365Session
from baseball.config.strat365 import CAPTURE_VERSION


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def capture_cards(season: int, limit=None, sleep_seconds: float = 0.25):
    base_dir = Path(f"data/baseball/raw/strat365/{season}")
    players_path = base_dir / "players" / f"{season}_players_discovered.json"
    cards_dir = base_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    if not players_path.exists():
        raise FileNotFoundError(f"Missing discovered players file: {players_path}")

    payload = json.loads(players_path.read_text(encoding="utf-8"))
    players = payload["players"]

    if limit:
        players = players[:limit]

    session = Strat365Session()

    succeeded = 0
    failed = 0
    results = []

    for index, player in enumerate(players, start=1):
        player_id = player["playerId"]
        url = player["sourceUrl"]

        html_path = cards_dir / f"{player_id}.html"
        meta_path = cards_dir / f"{player_id}.capture.json"

        try:
            html = session.get(url)
            html_path.write_text(html, encoding="utf-8")

            meta = {
                "provider": "strat365",
                "season": season,
                "playerId": player_id,
                "playerName": player.get("playerName", ""),
                "sourceUrl": url,
                "htmlFile": str(html_path),
                "capturedAt": now_utc(),
                "captureVersion": CAPTURE_VERSION,
                "bytes": len(html.encode("utf-8", errors="replace")),
                "sha256": sha256_text(html),
                "status": "captured"
            }

            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            results.append(meta)
            succeeded += 1

            print(f"[{index}/{len(players)}] OK {player_id} {player.get('playerName', '')}")

        except Exception as exc:
            failed += 1

            error = {
                "provider": "strat365",
                "season": season,
                "playerId": player_id,
                "playerName": player.get("playerName", ""),
                "sourceUrl": url,
                "capturedAt": now_utc(),
                "captureVersion": CAPTURE_VERSION,
                "status": "failed",
                "error": str(exc)
            }

            meta_path.write_text(json.dumps(error, indent=2), encoding="utf-8")
            results.append(error)

            print(f"[{index}/{len(players)}] FAIL {player_id} {player.get('playerName', '')}: {exc}")

        if sleep_seconds:
            time.sleep(sleep_seconds)

    summary = {
        "provider": "strat365",
        "season": season,
        "captureVersion": CAPTURE_VERSION,
        "capturedAt": now_utc(),
        "playersAttempted": len(players),
        "playersCaptured": succeeded,
        "playersFailed": failed,
        "cardsDirectory": str(cards_dir),
        "results": results
    }

    summary_path = base_dir / "card_capture_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print("BIE Card Capture Summary")
    print("------------------------")
    print(f"Season    : {season}")
    print(f"Attempted : {len(players)}")
    print(f"Captured  : {succeeded}")
    print(f"Failed    : {failed}")
    print(f"Summary   : {summary_path}")

    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    args = parser.parse_args()

    capture_cards(
        season=args.season,
        limit=args.limit,
        sleep_seconds=args.sleep_seconds
    )


if __name__ == "__main__":
    main()
