from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


DEFENSE_PATH = Path("data/baseball/parsed/strat365/1980/player-defense-metadata/1980.player-defense-metadata.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-signals")
OUTPUT_PATH = OUTPUT_DIR / "1980.defensive-draft-signals.json"

SCHEMA_VERSION = "bie.defensive-draft-signals.v0"
PARSER_VERSION = "bie-defensive-draft-signal-parser-v0.1"


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": round(float(value), 12),
    }


def score_payload(value: Fraction) -> dict[str, Any]:
    return {
        "score": round(float(value), 4),
        "scoreFraction": fraction_payload(value),
    }


def percentile_scores(values: list[tuple[str, int]], *, low_is_good: bool) -> dict[str, Fraction]:
    n = len(values)

    if n <= 1:
        return {key: Fraction(50, 1) for key, _value in values}

    scores: dict[str, Fraction] = {}

    for key, value in values:
        if low_is_good:
            better_or_equal = sum(1 for _other_key, other_value in values if other_value >= value)
        else:
            better_or_equal = sum(1 for _other_key, other_value in values if other_value <= value)

        scores[key] = Fraction(100 * (better_or_equal - 1), n - 1)

    return scores


def position_key(player_id: int, index: int) -> str:
    return f"{player_id}:{index}"


def score_hitter_positions(hitters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_positions: list[dict[str, Any]] = []

    for hitter in hitters:
        for index, position in enumerate(hitter.get("hitterDefense", {}).get("positions", [])):
            item = dict(position)
            item["player"] = hitter
            item["key"] = position_key(int(hitter["playerId"]), index)
            all_positions.append(item)

    by_position: dict[str, list[dict[str, Any]]] = {}
    for item in all_positions:
        by_position.setdefault(item["position"], []).append(item)

    scored_by_key: dict[str, dict[str, Any]] = {}

    for position, rows in by_position.items():
        range_scores = percentile_scores(
            [(row["key"], int(row["range"])) for row in rows],
            low_is_good=True,
        )
        error_scores = percentile_scores(
            [(row["key"], int(row["error"])) for row in rows],
            low_is_good=True,
        )

        arm_rows = [
            (row["key"], int(row["arm"]))
            for row in rows
            if row.get("arm") is not None
        ]
        arm_scores = percentile_scores(arm_rows, low_is_good=True) if arm_rows else {}

        for row in rows:
            key = row["key"]
            range_score = range_scores[key]
            error_score = error_scores[key]
            arm_score = arm_scores.get(key)

            if arm_score is None:
                defensive_score = range_score * Fraction(70, 100) + error_score * Fraction(30, 100)
            else:
                defensive_score = (
                    range_score * Fraction(55, 100)
                    + error_score * Fraction(25, 100)
                    + arm_score * Fraction(20, 100)
                )

            scored_by_key[key] = {
                "position": row["position"],
                "raw": row["raw"],
                "range": row["range"],
                "error": row["error"],
                "arm": row["arm"],
                "rangeScore": score_payload(range_score),
                "errorScore": score_payload(error_score),
                "armScore": score_payload(arm_score) if arm_score is not None else None,
                "defensiveScore": score_payload(defensive_score),
            }

    output: list[dict[str, Any]] = []

    for hitter in hitters:
        player_id = int(hitter["playerId"])
        scored_positions = [
            scored_by_key[position_key(player_id, index)]
            for index, _position in enumerate(hitter.get("hitterDefense", {}).get("positions", []))
        ]

        scored_positions.sort(
            key=lambda row: row["defensiveScore"]["score"],
            reverse=True,
        )

        best = scored_positions[0] if scored_positions else None

        output.append(
            {
                "player": {
                    "playerId": player_id,
                    "playerName": hitter.get("playerName"),
                    "team": hitter.get("team"),
                },
                "role": "hitter",
                "defenseUnavailable": hitter.get("hitterDefense", {}).get("defenseUnavailable") is True,
                "running": hitter.get("hitterDefense", {}).get("running"),
                "positionCount": len(scored_positions),
                "bestPosition": best,
                "positions": scored_positions,
            }
        )

    output.sort(
        key=lambda row: ((row.get("bestPosition") or {}).get("defensiveScore") or {}).get("score", -1),
        reverse=True,
    )

    return output


def score_pitchers(pitchers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pitcher_defense_scores = percentile_scores(
        [(str(row["playerId"]), int(row["pitcherDefense"]["pitcherDefense"])) for row in pitchers],
        low_is_good=True,
    )
    hold_scores = percentile_scores(
        [(str(row["playerId"]), int(row["pitcherDefense"]["hold"])) for row in pitchers],
        low_is_good=True,
    )
    wild_pitch_scores = percentile_scores(
        [(str(row["playerId"]), int(row["pitcherDefense"]["wildPitch"])) for row in pitchers],
        low_is_good=True,
    )
    balk_scores = percentile_scores(
        [(str(row["playerId"]), int(row["pitcherDefense"]["balk"])) for row in pitchers],
        low_is_good=True,
    )

    output: list[dict[str, Any]] = []

    for pitcher in pitchers:
        player_id = str(pitcher["playerId"])
        raw = pitcher["pitcherDefense"]

        pitcher_defense_score = pitcher_defense_scores[player_id]
        hold_score = hold_scores[player_id]
        wild_pitch_score = wild_pitch_scores[player_id]
        balk_score = balk_scores[player_id]

        defensive_score = (
            pitcher_defense_score * Fraction(45, 100)
            + hold_score * Fraction(30, 100)
            + wild_pitch_score * Fraction(15, 100)
            + balk_score * Fraction(10, 100)
        )

        output.append(
            {
                "player": {
                    "playerId": int(player_id),
                    "playerName": pitcher.get("playerName"),
                    "team": pitcher.get("team"),
                },
                "role": "pitcher",
                "raw": raw,
                "pitcherDefenseScore": score_payload(pitcher_defense_score),
                "holdScore": score_payload(hold_score),
                "wildPitchScore": score_payload(wild_pitch_score),
                "balkScore": score_payload(balk_score),
                "defensiveScore": score_payload(defensive_score),
            }
        )

    output.sort(
        key=lambda row: row["defensiveScore"]["score"],
        reverse=True,
    )

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(DEFENSE_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    players = data.get("players", [])
    hitters = [row for row in players if row.get("role") == "hitter"]
    pitchers = [row for row in players if row.get("role") == "pitcher"]

    hitter_signals = score_hitter_positions(hitters)
    pitcher_signals = score_pitchers(pitchers)

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFiles": {
            "playerDefenseMetadata": str(DEFENSE_PATH).replace("\\", "/"),
        },
        "model": {
            "name": "defensive_draft_signal_v0",
            "hitterPositionScore": "Infield positions use 70% range percentile + 30% error percentile. Catcher/outfield positions use 55% range percentile + 25% error percentile + 20% arm percentile.",
            "pitcherScore": "45% pitcher fielding percentile + 30% hold percentile + 15% wild-pitch percentile + 10% balk percentile.",
            "limitations": [
                "Does not yet apply actual GBX/FBX frequency by team context.",
                "Does not yet combine with salary-adjusted offensive/pitching draft score.",
                "Does not yet enforce roster position requirements.",
            ],
        },
        "counts": {
            "hitters": len(hitter_signals),
            "pitchers": len(pitcher_signals),
            "hitterDefenseUnavailable": sum(1 for row in hitter_signals if row["defenseUnavailable"]),
        },
        "hitters": hitter_signals,
        "pitchers": pitcher_signals,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Defensive Draft Signal Parser v0")
    print("=" * 80)
    print(f"Hitters: {len(hitter_signals)}")
    print(f"Pitchers: {len(pitcher_signals)}")
    print(f"Hitter defense unavailable: {output['counts']['hitterDefenseUnavailable']}")

    print()
    print("Top hitter defensive signals")
    print("-" * 80)
    for row in hitter_signals[:15]:
        best = row["bestPosition"]
        print(
            f'{best["defensiveScore"]["score"]:7.3f} '
            f'{best["raw"]:>12} '
            f'{row["player"]["playerName"]} team={row["player"]["team"]}'
        )

    print()
    print("Top pitcher defensive signals")
    print("-" * 80)
    for row in pitcher_signals[:15]:
        raw = row["raw"]
        print(
            f'{row["defensiveScore"]["score"]:7.3f} '
            f'p-{raw["pitcherDefense"]} hold={raw["hold"]} wp={raw["wildPitch"]} bk={raw["balk"]} '
            f'{row["player"]["playerName"]} team={row["player"]["team"]}'
        )

    print(f"\nOutput: {OUTPUT_PATH}")
    print("=" * 80)

    if len(hitter_signals) != 442 or len(pitcher_signals) != 279:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

