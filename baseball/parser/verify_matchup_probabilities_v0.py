from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
MATCHUP_DIR = Path("data/baseball/parsed/strat365/1980/matchup-probabilities")
MATCHUP_PATH = MATCHUP_DIR / "1980.matchup-probabilities.jsonl"
MANIFEST_PATH = MATCHUP_DIR / "1980.matchup-probabilities.manifest.json"

EXPECTED_SCHEMA_VERSION = "bie.matchup-probabilities.v0"
EXPECTED_ROWS = 123318
EXPECTED_STATUS_COUNTS = {
    "partial_unresolved_open_split": 1307,
    "exact": 122011,
}
EXPECTED_BATS_THROWS_COUNTS = {
    "L_vs_R": 28077,
    "L_vs_L": 12936,
    "R_vs_R": 46795,
    "R_vs_L": 21560,
    "S_vs_R": 9550,
    "S_vs_L": 4400,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing fraction payload")
    return Fraction(payload["numerator"], payload["denominator"])


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


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])

    hitters = {int(p["playerId"]): p for p in players if p.get("role") == "hitter"}
    pitchers = {int(p["playerId"]): p for p in players if p.get("role") == "pitcher"}

    manifest = read_json(MANIFEST_PATH)

    row_count = 0
    status_counts: Counter[str] = Counter()
    bats_throws_counts: Counter[str] = Counter()
    effective_counts: Counter[str] = Counter()
    failures: list[str] = []

    seen_matchups: set[str] = set()

    with MATCHUP_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            row_count += 1
            row = json.loads(line)

            if row.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
                failures.append(f"row {row_count}: schemaVersion={row.get('schemaVersion')}")

            matchup_id = row.get("matchupId")
            if matchup_id in seen_matchups:
                failures.append(f"duplicate matchupId={matchup_id}")
            seen_matchups.add(matchup_id)

            hitter = row.get("hitter", {})
            pitcher = row.get("pitcher", {})

            hitter_id = int(hitter.get("playerId"))
            pitcher_id = int(pitcher.get("playerId"))

            source_hitter = hitters.get(hitter_id)
            source_pitcher = pitchers.get(pitcher_id)

            if source_hitter is None:
                failures.append(f"row {row_count}: unknown hitterId={hitter_id}")
                continue

            if source_pitcher is None:
                failures.append(f"row {row_count}: unknown pitcherId={pitcher_id}")
                continue

            if hitter.get("bats") != source_hitter.get("bats"):
                failures.append(f"row {row_count}: hitter bats mismatch")

            if pitcher.get("throws") != source_pitcher.get("throws"):
                failures.append(f"row {row_count}: pitcher throws mismatch")

            expected_hitter_side = hitter_side_for_pitcher(source_pitcher["throws"])
            expected_effective_side = effective_batter_side(source_hitter["bats"], source_pitcher["throws"])
            expected_pitcher_side = pitcher_side_for_batter(expected_effective_side)

            if hitter.get("selectedSide") != expected_hitter_side:
                failures.append(f"row {row_count}: hitter selected side mismatch")

            if row.get("effectiveBatterSide") != expected_effective_side:
                failures.append(f"row {row_count}: effective batter side mismatch")

            if pitcher.get("selectedSide") != expected_pitcher_side:
                failures.append(f"row {row_count}: pitcher selected side mismatch")

            status = row.get("probabilityStatus")
            status_counts[status] += 1

            bats_throws_counts[f'{source_hitter["bats"]}_vs_{source_pitcher["throws"]}'] += 1
            effective_counts[f'{expected_effective_side}_batter_vs_{source_pitcher["throws"]}_pitcher'] += 1

            weights = row.get("weights", {})
            exact_total = frac(weights.get("exactWeightTotal"))
            on_base = frac(weights.get("onBaseCandidateWeight"))
            hit = frac(weights.get("hitCandidateWeight"))
            out = frac(weights.get("outCandidateWeight"))

            if exact_total > 1:
                failures.append(f"row {row_count}: exact total > 1")

            if hit > on_base:
                failures.append(f"row {row_count}: hit > on-base")

            if hit + out > exact_total:
                failures.append(f"row {row_count}: hit + out > exact total")

            if status == "exact" and exact_total != Fraction(1, 1):
                failures.append(f"row {row_count}: exact status with total {exact_total}")

            if status == "partial_unresolved_open_split" and exact_total >= Fraction(1, 1):
                failures.append(f"row {row_count}: partial status with total {exact_total}")

    print("BIE Matchup Probability Verification")
    print("=" * 72)
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Manifest rows: {manifest.get('matchupRows')}")
    print(f"JSONL rows: {row_count}")
    print(f"Unique matchup IDs: {len(seen_matchups)}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Bats/throws counts: {dict(bats_throws_counts)}")
    print(f"Effective counts: {dict(effective_counts)}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)

    print("-" * 72)

    if (
        len(hitters) == 442
        and len(pitchers) == 279
        and manifest.get("matchupRows") == EXPECTED_ROWS
        and row_count == EXPECTED_ROWS
        and len(seen_matchups) == EXPECTED_ROWS
        and dict(status_counts) == EXPECTED_STATUS_COUNTS
        and dict(bats_throws_counts) == EXPECTED_BATS_THROWS_COUNTS
        and not failures
    ):
        print("MATCHUP PROBABILITIES VERIFIED")
    else:
        print("MATCHUP PROBABILITIES NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
