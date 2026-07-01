from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SEASON = 1968
INPUT_PATH = Path("data/baseball/parsed/strat365/1968/draft-signals/1968.browser-baseline-draft-signals.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1968/card-capture-pools")
JSON_PATH = OUTPUT_DIR / "1968.focused-draft-card-capture-pool.json"
MD_PATH = OUTPUT_DIR / "1968.focused-draft-card-capture-pool.md"

def score(item: dict[str, Any]) -> float:
    return float(item.get("browserBaselineDraftScore", {}).get("score", 0) or 0)

def salary(item: dict[str, Any]) -> float:
    return float(item.get("salary", {}).get("millions", 0) or 0)

def defense_score(item: dict[str, Any]) -> float:
    return float(item.get("browserDefenseScore", {}).get("score", 0) or 0)

def player_id(item: dict[str, Any]) -> int:
    return int(item["player"]["playerId"])

def player_name(item: dict[str, Any]) -> str:
    return str(item["player"]["playerName"])

def team(item: dict[str, Any]) -> str:
    return str(item["player"].get("team", ""))

def take_ranked(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return sorted(items, key=score, reverse=True)[:limit]

def compact_player(item: dict[str, Any], category: str) -> dict[str, Any]:
    return {
        "playerId": player_id(item),
        "playerName": player_name(item),
        "team": team(item),
        "role": item.get("role"),
        "salaryMillions": salary(item),
        "browserBaselineDraftScore": score(item),
        "browserDefenseScore": defense_score(item) if item.get("role") == "hitter" else None,
        "category": category,
    }

def add_category(pool: dict[int, dict[str, Any]], category: str, items: list[dict[str, Any]]) -> None:
    for item in items:
        pid = player_id(item)
        compact = compact_player(item, category)
        if pid not in pool:
            compact["categories"] = [category]
            pool[pid] = compact
        elif category not in pool[pid]["categories"]:
            pool[pid]["categories"].append(category)

def main() -> None:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    hitters = list(data.get("hitters", []))
    pitchers = list(data.get("pitchers", []))

    pool: dict[int, dict[str, Any]] = {}

    add_category(pool, "top_30_hitters", take_ranked(hitters, 30))
    add_category(pool, "top_30_pitchers", take_ranked(pitchers, 30))

    add_category(pool, "cheap_hitter_value_le_3m", take_ranked([h for h in hitters if salary(h) <= 3.0], 25))
    add_category(pool, "cheap_pitcher_value_le_2m", take_ranked([p for p in pitchers if salary(p) <= 2.0], 25))

    add_category(pool, "premium_hitters_ge_8m", take_ranked([h for h in hitters if salary(h) >= 8.0], 20))
    add_category(pool, "premium_pitchers_ge_6m", take_ranked([p for p in pitchers if salary(p) >= 6.0], 20))

    add_category(pool, "hitter_defense_anchors", sorted(hitters, key=defense_score, reverse=True)[:25])

    players = sorted(pool.values(), key=lambda x: (-x["browserBaselineDraftScore"], x["playerName"]))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "schemaVersion": "bie.focused-draft-card-capture-pool.v0",
        "season": SEASON,
        "sourceFile": str(INPUT_PATH),
        "selectionPolicy": {
            "top_30_hitters": 30,
            "top_30_pitchers": 30,
            "cheap_hitter_value_le_3m": 25,
            "cheap_pitcher_value_le_2m": 25,
            "premium_hitters_ge_8m": 20,
            "premium_pitchers_ge_6m": 20,
            "hitter_defense_anchors": 25
        },
        "counts": {
            "uniquePlayers": len(players),
            "hitters": sum(1 for p in players if p["role"] == "hitter"),
            "pitchers": sum(1 for p in players if p["role"] == "pitcher")
        },
        "players": players
    }

    JSON_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    lines = [
        "# 1968 Focused Draft Card Capture Pool",
        "",
        f"Unique players: {output['counts']['uniquePlayers']}",
        f"Hitters: {output['counts']['hitters']}",
        f"Pitchers: {output['counts']['pitchers']}",
        "",
        "## Top 20 by browser-baseline score",
        "",
        "| Player ID | Player | Role | Salary | Score | Categories |",
        "|---:|---|---|---:|---:|---|",
    ]

    for p in players[:20]:
        lines.append(
            f"| {p['playerId']} | {p['playerName']} | {p['role']} | "
            f"{p['salaryMillions']:.2f} | {p['browserBaselineDraftScore']:.2f} | "
            f"{', '.join(p['categories'])} |"
        )

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Focused capture pool created")
    print(f"Unique players: {output['counts']['uniquePlayers']}")
    print(f"Hitters: {output['counts']['hitters']}")
    print(f"Pitchers: {output['counts']['pitchers']}")
    print("First 12 player IDs:")
    print(" ".join(str(p["playerId"]) for p in players[:12]))
    print(f"JSON: {JSON_PATH}")
    print(f"MD: {MD_PATH}")

if __name__ == "__main__":
    main()
