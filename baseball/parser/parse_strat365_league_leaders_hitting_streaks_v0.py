#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


PRE_RE = re.compile(
    r"<pre\b[^>]*>(.*?)</pre>",
    flags=re.IGNORECASE | re.DOTALL,
)

TAG_RE = re.compile(r"<[^>]+>", flags=re.DOTALL)

CELL_RE = re.compile(
    r"^\s*"
    r"(?P<player>.+?)"
    r"\s{2,}"
    r"(?P<team>[A-Z0-9*]{3})"
    r"\s+"
    r"(?:(?P<current>\*)\s*)?"
    r"(?P<games>\d+)"
    r"\s*$"
)


def text_from_html(raw_html: str) -> str:
    for match in PRE_RE.finditer(raw_html):
        block = html.unescape(TAG_RE.sub("", match.group(1)))
        if re.search(r"HITTING\s+STREAK", block, re.IGNORECASE):
            return block

    fallback = re.sub(
        r"(?i)<br\s*/?>",
        "\n",
        raw_html,
    )
    fallback = TAG_RE.sub("", fallback)
    return html.unescape(fallback)


def parse_hitting_streaks(raw_html: str) -> list[dict]:
    text = text_from_html(raw_html)
    lines = text.splitlines()

    header_index = None
    streak_start = None
    streak_end = None

    for index, line in enumerate(lines):
        match = re.search(
            r"-+\s*HITTING\s+STREAK\s*-+",
            line,
            re.IGNORECASE,
        )
        if not match:
            continue

        header_index = index
        streak_start = match.start()

        right = re.search(
            r"-+\s*PINCH\s+HIT\s+BAT\s+AVG\s*-+",
            line,
            re.IGNORECASE,
        )

        streak_end = right.start() if right else None
        break

    if header_index is None or streak_start is None:
        raise ValueError("HITTING STREAK section not found")

    results = []

    for line in lines[header_index + 1 :]:
        if re.search(
            r"-+\s*SLUGGING\s+PCT\s*-+",
            line,
            re.IGNORECASE,
        ):
            break

        cell = line[
            streak_start:
            streak_end if streak_end is not None else len(line)
        ].rstrip()

        if not cell.strip():
            continue

        if re.match(
            r"^\s*OTHERS\s+TIED\s+WITH",
            cell,
            re.IGNORECASE,
        ):
            continue

        match = CELL_RE.match(cell)

        if not match:
            continue

        player_name = match.group("player").strip()
        team = match.group("team").strip()
        current_marker = match.group("current")
        streak_games = int(match.group("games"))

        results.append(
            {
                "displayOrder": len(results) + 1,
                "playerName": player_name,
                "teamAbbreviation": team,
                "streakGames": streak_games,
                "isCurrent": current_marker == "*",
                "rawCurrentMarker": current_marker,
                "rawText": cell.strip(),
            }
        )

    if not results:
        raise ValueError("No hitting-streak rows parsed")

    return results


def build_output(input_path: Path) -> dict:
    raw_html = input_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    streaks = parse_hitting_streaks(raw_html)
    current = [row for row in streaks if row["isCurrent"]]

    return {
        "schemaVersion": "strat365-league-leaders-hitting-streaks-v0",
        "artifactType": "league-leaders-hitting-streak-evidence",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(input_path).replace("\\", "/"),
            "sourceFamily": "leagueLeaders",
        },
        "semanticRules": {
            "asteriskMeansCurrent": True,
            "completedStreakIsNotCurrentFormClaim": True,
        },
        "counts": {
            "streakRows": len(streaks),
            "currentStreakRows": len(current),
        },
        "hittingStreaks": streaks,
        "currentHittingStreaks": current,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    result = build_output(input_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "streakRows": result["counts"]["streakRows"],
                "currentStreakRows":
                    result["counts"]["currentStreakRows"],
            }
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
