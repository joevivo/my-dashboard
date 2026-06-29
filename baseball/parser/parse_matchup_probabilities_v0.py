from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
SUMMARY_DIR = Path("data/baseball/parsed/strat365/1980/card-probability-summaries")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/matchup-probabilities")
OUTPUT_PATH = OUTPUT_DIR / "1980.matchup-probabilities.jsonl"
MANIFEST_PATH = OUTPUT_DIR / "1980.matchup-probabilities.manifest.json"

SCHEMA_VERSION = "bie.matchup-probabilities.v0"
PARSER_VERSION = "bie-matchup-probability-parser-v0.1"


BASE_OUTCOMES = [
    "SINGLE",
    "DOUBLE",
    "TRIPLE",
    "HOME_RUN",
    "WALK",
    "HBP",
    "STRIKEOUT",
    "GROUNDBALL",
    "FLYBALL",
    "LINEOUT",
    "LINEOUT_MAX",
    "POPOUT",
    "FOULOUT",
    "GROUNDBALL_X",
    "FLYBALL_X",
    "CATCHER_X",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def fraction_from_payload(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": round(float(value), 12),
    }


def hitter_side_for_pitcher(pitcher_throws: str) -> str:
    if pitcher_throws == "L":
        return "vs_left_pitcher"
    if pitcher_throws == "R":
        return "vs_right_pitcher"
    raise ValueError(f"Unsupported pitcher throws value: {pitcher_throws}")


def effective_batter_side(hitter_bats: str, pitcher_throws: str) -> str:
    if hitter_bats in ("L", "R"):
        return hitter_bats

    if hitter_bats == "S":
        if pitcher_throws == "R":
            return "L"
        if pitcher_throws == "L":
            return "R"

    raise ValueError(f"Unsupported bats/throws values: bats={hitter_bats} throws={pitcher_throws}")


def pitcher_side_for_batter(effective_side: str) -> str:
    if effective_side == "L":
        return "vs_left_batter"
    if effective_side == "R":
        return "vs_right_batter"
    raise ValueError(f"Unsupported effective batter side: {effective_side}")


def load_summaries() -> dict[int, dict[str, Any]]:
    summaries = {}

    for path in SUMMARY_DIR.glob("*.card-probability-summary.json"):
        data = read_json(path)
        player_id = int(data["player"]["playerId"])
        side_map = {side["side"]: side for side in data.get("sides", [])}

        summaries[player_id] = {
            "player": data["player"],
            "role": data["role"],
            "sides": side_map,
        }

    return summaries


def side_weight(side: dict[str, Any], key: str) -> Fraction:
    return fraction_from_payload(side.get(key))


def side_outcome(side: dict[str, Any], label: str) -> Fraction:
    return fraction_from_payload(side.get("baseOutcomeWeights", {}).get(label))


def combine_half(hitter_value: Fraction, pitcher_value: Fraction) -> Fraction:
    return (hitter_value + pitcher_value) * Fraction(1, 2)


def player_payload(player: dict[str, Any]) -> dict[str, Any]:
    return {
        "playerId": player.get("playerId"),
        "playerName": player.get("playerName"),
        "team": player.get("team"),
    }


def build_matchup(
    hitter: dict[str, Any],
    pitcher: dict[str, Any],
    summaries: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    hitter_summary = summaries[int(hitter["playerId"])]
    pitcher_summary = summaries[int(pitcher["playerId"])]

    hitter_side_key = hitter_side_for_pitcher(pitcher["throws"])
    batter_side = effective_batter_side(hitter["bats"], pitcher["throws"])
    pitcher_side_key = pitcher_side_for_batter(batter_side)

    hitter_side = hitter_summary["sides"][hitter_side_key]
    pitcher_side = pitcher_summary["sides"][pitcher_side_key]

    base_outcome_weights = {}
    for label in BASE_OUTCOMES:
        value = combine_half(side_outcome(hitter_side, label), side_outcome(pitcher_side, label))
        if value:
            base_outcome_weights[label] = fraction_payload(value)

    exact_weight_total = combine_half(
        side_weight(hitter_side, "exactWeightTotal"),
        side_weight(pitcher_side, "exactWeightTotal"),
    )

    hitter_unresolved = hitter_side.get("unresolvedOutcomeRows", [])
    pitcher_unresolved = pitcher_side.get("unresolvedOutcomeRows", [])

    probability_status = "exact"
    if hitter_unresolved or pitcher_unresolved:
        probability_status = "partial_unresolved_open_split"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "matchupId": f'{hitter["playerId"]}_vs_{pitcher["playerId"]}',
        "probabilityStatus": probability_status,
        "hitter": {
            **player_payload(hitter),
            "bats": hitter.get("bats"),
            "selectedSide": hitter_side_key,
        },
        "pitcher": {
            **player_payload(pitcher),
            "throws": pitcher.get("throws"),
            "pitchingRole": pitcher.get("pitchingRole"),
            "selectedSide": pitcher_side_key,
        },
        "effectiveBatterSide": batter_side,
        "probabilityBasis": {
            "scope": "neutral_matchup",
            "hitterCardWeight": "1/2",
            "pitcherCardWeight": "1/2",
            "doesNotInclude": [
                "ballpark_effect_resolution",
                "defensive_x_chart_resolution",
                "clutch_context",
                "base_out_state_resolution",
                "lineup_context",
            ],
        },
        "weights": {
            "exactWeightTotal": fraction_payload(exact_weight_total),
            "onBaseCandidateWeight": fraction_payload(
                combine_half(
                    side_weight(hitter_side, "onBaseCandidateWeight"),
                    side_weight(pitcher_side, "onBaseCandidateWeight"),
                )
            ),
            "hitCandidateWeight": fraction_payload(
                combine_half(
                    side_weight(hitter_side, "hitCandidateWeight"),
                    side_weight(pitcher_side, "hitCandidateWeight"),
                )
            ),
            "outCandidateWeight": fraction_payload(
                combine_half(
                    side_weight(hitter_side, "outCandidateWeight"),
                    side_weight(pitcher_side, "outCandidateWeight"),
                )
            ),
            "baseOutcomeWeights": base_outcome_weights,
        },
        "unresolved": {
            "hitterRows": hitter_unresolved,
            "pitcherRows": pitcher_unresolved,
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])

    hitters = [p for p in players if p.get("role") == "hitter"]
    pitchers = [p for p in players if p.get("role") == "pitcher"]

    summaries = load_summaries()

    row_count = 0
    status_counts: Counter[str] = Counter()
    bats_throws_counts: Counter[str] = Counter()

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for hitter in hitters:
            for pitcher in pitchers:
                matchup = build_matchup(hitter, pitcher, summaries)
                handle.write(json.dumps(matchup, separators=(",", ":")) + "\n")

                row_count += 1
                status_counts[matchup["probabilityStatus"]] += 1
                bats_throws_counts[f'{hitter["bats"]}_vs_{pitcher["throws"]}'] += 1

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceSummaryDir": str(SUMMARY_DIR).replace("\\", "/"),
        "outputPath": str(OUTPUT_PATH).replace("\\", "/"),
        "hitters": len(hitters),
        "pitchers": len(pitchers),
        "matchupRows": row_count,
        "probabilityStatusCounts": dict(status_counts),
        "batsThrowsCounts": dict(bats_throws_counts),
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("BIE Matchup Probability Parser v0")
    print("=" * 72)
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Matchup rows: {row_count}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Bats/throws counts: {dict(bats_throws_counts)}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 72)

    if row_count != 123318:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
