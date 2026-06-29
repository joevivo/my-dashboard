from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
SUMMARY_DIR = Path("data/baseball/parsed/strat365/1980/card-probability-summaries")

EXPECTED_SCHEMA_VERSION = "bie.card-probability-summary.v0"
EXPECTED_SIDE_TOTAL_COUNTS = {
    "1/1": 1433,
    "53/54": 6,
    "107/108": 3,
}
EXPECTED_STATUS_COUNTS = {
    "exact": 53877,
    "non_probability_flag": 862,
    "unresolved_open_split": 9,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def fraction_from_payload(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing fraction payload")
    numerator = payload.get("numerator")
    denominator = payload.get("denominator")
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise ValueError(f"invalid fraction payload: {payload}")
    return Fraction(numerator, denominator)


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    paths = list(SUMMARY_DIR.glob("*.card-probability-summary.json"))
    parsed_ids = {
        int(path.name.replace(".card-probability-summary.json", "")): path
        for path in paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    side_count = 0
    unresolved_side_count = 0
    side_total_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    non_probability_flag_total = 0
    unresolved_row_total = 0
    exact_weight_total = Fraction(0, 1)
    failures: list[str] = []

    for player_id, expected_player in sorted(expected_ids.items()):
        path = parsed_ids.get(player_id)
        if not path:
            continue

        data = read_json(path)

        if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
            failures.append(f"{player_id}: schemaVersion={data.get('schemaVersion')}")

        role = data.get("role")
        expected_role = expected_player.get("role")

        if role != expected_role:
            failures.append(f"{player_id}: role mismatch {role} != {expected_role}")

        role_counts[role] += 1

        sides = data.get("sides", [])
        if len(sides) != 2:
            failures.append(f"{player_id}: expected 2 sides, found {len(sides)}")

        for side in sides:
            side_count += 1

            exact_total = fraction_from_payload(side.get("exactWeightTotal"))
            exact_weight_total += exact_total
            side_total_counts[f"{exact_total.numerator}/{exact_total.denominator}"] += 1

            if exact_total > 1:
                failures.append(f"{player_id}: side {side.get('side')} exact total > 1: {exact_total}")

            unresolved_rows = side.get("unresolvedOutcomeRows", [])
            unresolved_row_total += len(unresolved_rows)

            if unresolved_rows:
                unresolved_side_count += 1

            for status, count in side.get("probabilityStatusCounts", {}).items():
                status_counts[status] += count

            for _flag, count in side.get("nonProbabilityFlagCounts", {}).items():
                non_probability_flag_total += count

            hit = fraction_from_payload(side.get("hitCandidateWeight"))
            on_base = fraction_from_payload(side.get("onBaseCandidateWeight"))
            out = fraction_from_payload(side.get("outCandidateWeight"))

            if hit > on_base:
                failures.append(f"{player_id}: side {side.get('side')} hit weight > on-base weight")

            if hit + out > exact_total:
                failures.append(f"{player_id}: side {side.get('side')} hit + out exceeds exact total")

    print("BIE Card Probability Summary Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Card sides: {side_count}")
    print(f"Unresolved sides: {unresolved_side_count}")
    print(f"Unresolved rows: {unresolved_row_total}")
    print(f"Non-probability flags: {non_probability_flag_total}")
    print(f"Side exact total counts: {dict(side_total_counts)}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Exact weight total: {exact_weight_total}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)

    print("-" * 72)

    if (
        len(expected_ids) == 721
        and len(parsed_ids) == 721
        and not missing
        and not extra
        and role_counts.get("hitter") == 442
        and role_counts.get("pitcher") == 279
        and side_count == 1442
        and unresolved_side_count == 9
        and unresolved_row_total == 9
        and non_probability_flag_total == 862
        and dict(side_total_counts) == EXPECTED_SIDE_TOTAL_COUNTS
        and dict(status_counts) == EXPECTED_STATUS_COUNTS
        and exact_weight_total == Fraction(51907, 36)
        and not failures
    ):
        print("CARD PROBABILITY SUMMARIES VERIFIED")
    else:
        print("CARD PROBABILITY SUMMARIES NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
