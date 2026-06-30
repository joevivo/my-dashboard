import argparse
import json
from collections import defaultdict
from pathlib import Path

from report_observed_player_calibration_v0 import era, fmt, name, ops, role, signals, whip

DEFAULT_MANIFEST_PATH = Path(
    "data/baseball/parsed/strat365/1980/observed-results/"
    "observed-player-results-batch-v0.manifest.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate observed player calibration across a batch manifest."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def load_manifest(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_batch_rows(manifest):
    rows = []
    for file_entry in manifest.get("files", []):
        output_path = Path(file_entry["outputJson"])
        payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
        for row in payload.get("rows", []):
            item = dict(row)
            item["_batchSourceJson"] = str(output_path)
            rows.append(item)
    return rows


def player_key(row):
    player = row.get("player", {})
    player_id = player.get("playerId")
    if player_id is not None:
        return f"id:{player_id}"
    return f"name:{player.get('playerName', 'UNKNOWN')}"


def avg(values):
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def min_or_none(values):
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return min(clean)


def max_or_none(values):
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return max(clean)


def aggregate_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[player_key(row)].append(row)

    aggregates = []
    for player_rows in grouped.values():
        first = player_rows[0]
        player_role = role(first)
        da_values = []
        park_values = []
        delta_values = []

        for row in player_rows:
            da, park, delta = signals(row)
            da_values.append(da)
            park_values.append(park)
            delta_values.append(delta)

        hitter_ops = [ops(row) for row in player_rows]
        pitcher_era = [era(row) for row in player_rows]
        pitcher_whip = [whip(row) for row in player_rows]

        aggregates.append(
            {
                "player": name(first),
                "role": player_role,
                "seasons": len(player_rows),
                "rows": player_rows,
                "avgOps": avg(hitter_ops),
                "bestOps": max_or_none(hitter_ops),
                "worstOps": min_or_none(hitter_ops),
                "avgEra": avg(pitcher_era),
                "bestEra": min_or_none(pitcher_era),
                "worstEra": max_or_none(pitcher_era),
                "avgWhip": avg(pitcher_whip),
                "defenseAwareRank": avg(da_values),
                "ballparkAwareRank": avg(park_values),
                "avgBallparkDelta": avg(delta_values),
            }
        )

    return aggregates


def rank_bucket(aggregate):
    rank = aggregate.get("ballparkAwareRank")
    if rank is None:
        return "unknown"
    if rank <= 100:
        return "strong"
    if rank >= 200:
        return "weak"
    return "middle"


def actual_bucket(aggregate):
    if aggregate["role"] == "hitter":
        value = aggregate.get("avgOps")
        if value is None:
            return "unknown"
        if value >= 0.800:
            return "strong"
        if value < 0.700:
            return "weak"
        return "middle"

    value = aggregate.get("avgEra")
    if value is None:
        return "unknown"
    if value <= 3.50:
        return "strong"
    if value >= 4.50:
        return "weak"
    return "middle"


def aggregate_sort_value(aggregate):
    if aggregate["role"] == "hitter":
        value = aggregate.get("avgOps")
        return value if value is not None else -1
    value = aggregate.get("avgEra")
    return -(value if value is not None else 999)


def actual_label(aggregate):
    if aggregate["role"] == "hitter":
        return f"avg OPS {fmt(aggregate.get('avgOps'), 3)}"
    return (
        f"avg ERA {fmt(aggregate.get('avgEra'), 2)} | "
        f"avg WHIP {fmt(aggregate.get('avgWhip'), 2)}"
    )


def print_hitter_aggregate(aggregate):
    print(
        "- "
        f"{aggregate['player']} | seasons {aggregate['seasons']} | "
        f"avg OPS {fmt(aggregate.get('avgOps'), 3)} | "
        f"best {fmt(aggregate.get('bestOps'), 3)} | "
        f"worst {fmt(aggregate.get('worstOps'), 3)} | "
        f"DA rank {fmt(aggregate.get('defenseAwareRank'), 1)} | "
        f"park rank {fmt(aggregate.get('ballparkAwareRank'), 1)} | "
        f"avg delta {fmt(aggregate.get('avgBallparkDelta'), 1)}"
    )


def print_pitcher_aggregate(aggregate):
    print(
        "- "
        f"{aggregate['player']} | seasons {aggregate['seasons']} | "
        f"avg ERA {fmt(aggregate.get('avgEra'), 2)} | "
        f"best {fmt(aggregate.get('bestEra'), 2)} | "
        f"worst {fmt(aggregate.get('worstEra'), 2)} | "
        f"avg WHIP {fmt(aggregate.get('avgWhip'), 2)} | "
        f"DA rank {fmt(aggregate.get('defenseAwareRank'), 1)} | "
        f"park rank {fmt(aggregate.get('ballparkAwareRank'), 1)} | "
        f"avg delta {fmt(aggregate.get('avgBallparkDelta'), 1)}"
    )


def print_any_aggregate(aggregate):
    if aggregate["role"] == "hitter":
        print_hitter_aggregate(aggregate)
    else:
        print_pitcher_aggregate(aggregate)


def print_model_actual_section(title, aggregates, model_bucket, outcome_bucket, top):
    matches = [
        aggregate
        for aggregate in aggregates
        if rank_bucket(aggregate) == model_bucket and actual_bucket(aggregate) == outcome_bucket
    ]

    print(f"## {title}")
    for aggregate in sorted(matches, key=aggregate_sort_value, reverse=True)[:top]:
        print_any_aggregate(aggregate)
    if not matches:
        print("- n/a")
    print()


def print_park_section(title, aggregates, min_delta, outcome_bucket, top):
    matches = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("avgBallparkDelta") is not None
        and aggregate["avgBallparkDelta"] >= min_delta
        and actual_bucket(aggregate) == outcome_bucket
    ]

    print(f"## {title}")
    for aggregate in sorted(
        matches,
        key=lambda item: (item.get("avgBallparkDelta") or 0, aggregate_sort_value(item)),
        reverse=True,
    )[:top]:
        print_any_aggregate(aggregate)
    if not matches:
        print("- n/a")
    print()


def print_negative_park_strong_actual(aggregates, top):
    matches = [
        aggregate
        for aggregate in aggregates
        if aggregate.get("avgBallparkDelta") is not None
        and aggregate["avgBallparkDelta"] < 0
        and actual_bucket(aggregate) == "strong"
    ]

    print("## Big Negative Park Movement / Strong Actual")
    for aggregate in sorted(
        matches,
        key=lambda item: (abs(item.get("avgBallparkDelta") or 0), aggregate_sort_value(item)),
        reverse=True,
    )[:top]:
        print_any_aggregate(aggregate)
    if not matches:
        print("- n/a")
    print()


def main():
    args = parse_args()
    manifest = load_manifest(args.manifest)
    rows = load_batch_rows(manifest)
    aggregates = aggregate_rows(rows)

    repeated = [aggregate for aggregate in aggregates if aggregate["seasons"] > 1]
    hitter_player_seasons = len([row for row in rows if role(row) == "hitter"])
    pitcher_player_seasons = len([row for row in rows if role(row) == "pitcher"])
    hitters = [aggregate for aggregate in aggregates if aggregate["role"] == "hitter"]
    pitchers = [aggregate for aggregate in aggregates if aggregate["role"] == "pitcher"]
    repeated_hitters = [aggregate for aggregate in repeated if aggregate["role"] == "hitter"]
    repeated_pitchers = [aggregate for aggregate in repeated if aggregate["role"] == "pitcher"]

    print("# BIE Observed Player Aggregate Calibration v0")
    print()
    print("Manifest")
    print(f"Manifest: {args.manifest}")
    print(f"Observed files: {manifest.get('counts', {}).get('csvFiles')}")
    print(f"Player-seasons: {len(rows)}")
    print(f"Unique players: {len(aggregates)}")
    print(f"Repeated players: {len(repeated)}")
    print(f"Hitter player-seasons: {hitter_player_seasons}")
    print(f"Pitcher player-seasons: {pitcher_player_seasons}")
    print(f"Unique hitters: {len(hitters)}")
    print(f"Unique pitchers: {len(pitchers)}")
    print()

    print("## Repeated Hitters")
    for aggregate in sorted(repeated_hitters, key=lambda item: item.get("avgOps") or -1, reverse=True):
        print_hitter_aggregate(aggregate)
    if not repeated_hitters:
        print("- n/a")
    print()

    print("## Repeated Pitchers")
    for aggregate in sorted(repeated_pitchers, key=lambda item: item.get("avgEra") if item.get("avgEra") is not None else 999):
        print_pitcher_aggregate(aggregate)
    if not repeated_pitchers:
        print("- n/a")
    print()

    print_model_actual_section("Strong Model / Strong Actual", aggregates, "strong", "strong", args.top)
    print_model_actual_section("Strong Model / Weak Actual", aggregates, "strong", "weak", args.top)
    print_model_actual_section("Weak Model / Strong Actual", aggregates, "weak", "strong", args.top)

    print_park_section("Big Positive Park Movement / Strong Actual", aggregates, 25, "strong", args.top)
    print_park_section("Big Positive Park Movement / Weak Actual", aggregates, 25, "weak", args.top)
    print_negative_park_strong_actual(aggregates, args.top)


if __name__ == "__main__":
    main()
