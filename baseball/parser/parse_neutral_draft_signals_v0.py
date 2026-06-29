from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any, Callable


PROFILE_PATH = Path("data/baseball/parsed/strat365/1980/matchup-player-profiles/1980.matchup-player-profiles.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-signals")
OUTPUT_PATH = OUTPUT_DIR / "1980.neutral-draft-signals.json"

SCHEMA_VERSION = "bie.neutral-draft-signals.v0"
PARSER_VERSION = "bie-neutral-draft-signal-parser-v0.1"


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


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


def avg(profile: dict[str, Any], key: str) -> Fraction:
    return frac(profile.get("averages", {}).get(key))


def outcome(profile: dict[str, Any], key: str) -> Fraction:
    return frac(profile.get("outcomeAverages", {}).get(key))


def percentile_scores(
    profiles: list[dict[str, Any]],
    getter: Callable[[dict[str, Any]], Fraction],
    *,
    higher_is_better: bool,
) -> dict[int, Fraction]:
    values = [(int(profile["player"]["playerId"]), getter(profile)) for profile in profiles]
    n = len(values)

    if n <= 1:
        return {player_id: Fraction(50, 1) for player_id, _value in values}

    scores: dict[int, Fraction] = {}

    for player_id, value in values:
        if higher_is_better:
            better_or_equal = sum(1 for _other_id, other_value in values if other_value <= value)
        else:
            better_or_equal = sum(1 for _other_id, other_value in values if other_value >= value)

        scores[player_id] = Fraction(100 * (better_or_equal - 1), n - 1)

    return scores


def weighted_score(components: dict[str, Fraction], weights: dict[str, Fraction]) -> Fraction:
    total = Fraction(0, 1)

    for key, weight in weights.items():
        total += components[key] * weight

    return total


def render_player(profile: dict[str, Any], components: dict[str, Fraction], total_score: Fraction, role: str) -> dict[str, Any]:
    player = profile["player"]

    result = {
        "player": player,
        "role": role,
        "rankable": True,
        "exactMatchups": profile.get("exactMatchups"),
        "partialMatchups": profile.get("partialMatchups"),
        "draftScore": score_payload(total_score),
        "componentScores": {
            key: score_payload(value)
            for key, value in sorted(components.items())
        },
        "sourceAverages": {
            "onBaseCandidateWeight": fraction_payload(avg(profile, "onBaseCandidateWeight")),
            "hitCandidateWeight": fraction_payload(avg(profile, "hitCandidateWeight")),
            "outCandidateWeight": fraction_payload(avg(profile, "outCandidateWeight")),
            "homeRunWeight": fraction_payload(outcome(profile, "HOME_RUN")),
            "strikeoutWeight": fraction_payload(outcome(profile, "STRIKEOUT")),
        },
    }

    return result


def render_unresolved(profile: dict[str, Any], role: str) -> dict[str, Any]:
    return {
        "player": profile["player"],
        "role": role,
        "rankable": False,
        "exactMatchups": profile.get("exactMatchups"),
        "partialMatchups": profile.get("partialMatchups"),
        "reason": "No exact matchup rows available because all source matchups contain unresolved open splits.",
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(PROFILE_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitter_profiles = data.get("hitterProfiles", [])
    pitcher_profiles = data.get("pitcherProfiles", [])

    rankable_hitters = [profile for profile in hitter_profiles if profile.get("exactMatchups", 0) > 0]
    unresolved_hitters = [profile for profile in hitter_profiles if profile.get("exactMatchups", 0) == 0]

    rankable_pitchers = [profile for profile in pitcher_profiles if profile.get("exactMatchups", 0) > 0]
    unresolved_pitchers = [profile for profile in pitcher_profiles if profile.get("exactMatchups", 0) == 0]

    hitter_component_maps = {
        "on_base": percentile_scores(rankable_hitters, lambda p: avg(p, "onBaseCandidateWeight"), higher_is_better=True),
        "hit": percentile_scores(rankable_hitters, lambda p: avg(p, "hitCandidateWeight"), higher_is_better=True),
        "power": percentile_scores(rankable_hitters, lambda p: outcome(p, "HOME_RUN"), higher_is_better=True),
        "contact": percentile_scores(rankable_hitters, lambda p: outcome(p, "STRIKEOUT"), higher_is_better=False),
    }

    hitter_weights = {
        "on_base": Fraction(40, 100),
        "hit": Fraction(25, 100),
        "power": Fraction(20, 100),
        "contact": Fraction(15, 100),
    }

    pitcher_component_maps = {
        "on_base_prevention": percentile_scores(rankable_pitchers, lambda p: avg(p, "onBaseCandidateWeight"), higher_is_better=False),
        "hit_prevention": percentile_scores(rankable_pitchers, lambda p: avg(p, "hitCandidateWeight"), higher_is_better=False),
        "home_run_prevention": percentile_scores(rankable_pitchers, lambda p: outcome(p, "HOME_RUN"), higher_is_better=False),
        "strikeout": percentile_scores(rankable_pitchers, lambda p: outcome(p, "STRIKEOUT"), higher_is_better=True),
    }

    pitcher_weights = {
        "on_base_prevention": Fraction(35, 100),
        "hit_prevention": Fraction(25, 100),
        "home_run_prevention": Fraction(20, 100),
        "strikeout": Fraction(20, 100),
    }

    hitter_signals = []

    for profile in rankable_hitters:
        player_id = int(profile["player"]["playerId"])
        components = {
            key: score_map[player_id]
            for key, score_map in hitter_component_maps.items()
        }
        hitter_signals.append(render_player(profile, components, weighted_score(components, hitter_weights), "hitter"))

    pitcher_signals = []

    for profile in rankable_pitchers:
        player_id = int(profile["player"]["playerId"])
        components = {
            key: score_map[player_id]
            for key, score_map in pitcher_component_maps.items()
        }
        pitcher_signals.append(render_player(profile, components, weighted_score(components, pitcher_weights), "pitcher"))

    hitter_signals.sort(key=lambda row: row["draftScore"]["score"], reverse=True)
    pitcher_signals.sort(key=lambda row: row["draftScore"]["score"], reverse=True)

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFile": str(PROFILE_PATH).replace("\\", "/"),
        "model": {
            "name": "neutral_draft_signal_v0",
            "limitations": [
                "No Strat salary adjustment yet.",
                "No position scarcity adjustment yet.",
                "No fielding adjustment yet.",
                "No ballpark adjustment yet.",
                "No usage or role adjustment yet.",
            ],
            "hitterWeights": {key: float(value) for key, value in hitter_weights.items()},
            "pitcherWeights": {key: float(value) for key, value in pitcher_weights.items()},
        },
        "counts": {
            "rankableHitters": len(hitter_signals),
            "unresolvedHitters": len(unresolved_hitters),
            "rankablePitchers": len(pitcher_signals),
            "unresolvedPitchers": len(unresolved_pitchers),
        },
        "hitters": hitter_signals,
        "pitchers": pitcher_signals,
        "unresolved": {
            "hitters": [render_unresolved(profile, "hitter") for profile in unresolved_hitters],
            "pitchers": [render_unresolved(profile, "pitcher") for profile in unresolved_pitchers],
        },
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Neutral Draft Signal Parser v0")
    print("=" * 72)
    print(f"Rankable hitters: {len(hitter_signals)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitcher_signals)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")

    print()
    print("Top hitter draft signals")
    print("-" * 72)
    for row in hitter_signals[:15]:
        player = row["player"]
        print(f'{row["draftScore"]["score"]:7.3f}  {player["playerName"]} team={player["team"]}')

    print()
    print("Top pitcher draft signals")
    print("-" * 72)
    for row in pitcher_signals[:15]:
        player = row["player"]
        print(f'{row["draftScore"]["score"]:7.3f}  {player["playerName"]} team={player["team"]}')

    print(f"\nOutput: {OUTPUT_PATH}")
    print("=" * 72)

    if len(hitter_signals) != 440 or len(unresolved_hitters) != 2 or len(pitcher_signals) != 279 or unresolved_pitchers:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
