import argparse
import json
from pathlib import Path
from statistics import median

DEFAULT_BALLPARK_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json"
)
DEFAULT_DEFENSE_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json"
)
DEFAULT_OBSERVED_MANIFEST_PATH = Path(
    "data/baseball/parsed/strat365/1980/observed-results/observed-player-results-batch-v0.manifest.json"
)
DEFAULT_BALLPARK_NAME = "Comiskey Park 1980"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a BIE draft strategy brief from current draft signals."
    )
    parser.add_argument("--ballpark-aware", type=Path, default=DEFAULT_BALLPARK_AWARE_PATH)
    parser.add_argument("--defense-aware", type=Path, default=DEFAULT_DEFENSE_AWARE_PATH)
    parser.add_argument("--observed-manifest", type=Path, default=DEFAULT_OBSERVED_MANIFEST_PATH)
    parser.add_argument("--ballpark", default=DEFAULT_BALLPARK_NAME)
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def score_value(score):
    if not isinstance(score, dict):
        return None
    value = score.get("score")
    if value is None:
        value = (score.get("scoreFraction") or {}).get("decimal")
    return value


def player_id(row):
    return row.get("player", {}).get("playerId")


def player_name(row):
    return row.get("player", {}).get("playerName", "UNKNOWN")


def salary_raw(row):
    return (row.get("salary") or {}).get("raw", "n/a")


def salary_millions(row):
    return ((row.get("salary") or {}).get("millions") or {}).get("decimal")


def find_fit(row, ballpark_name):
    for fit in row.get("ballparkFits") or []:
        if fit.get("ballparkName") == ballpark_name:
            return fit
    return None


def rank_at_ballpark(row, ballpark_name):
    fit = find_fit(row, ballpark_name)
    if not fit:
        return row.get("ballparkAwareRank")
    return (fit.get("ballparkImpact") or {}).get("parkAdjustedRank")


def park_rank_delta(row, ballpark_name):
    defense_rank = row.get("defenseAwareRank")
    park_rank = rank_at_ballpark(row, ballpark_name)
    if defense_rank is None or park_rank is None:
        return None
    return defense_rank - park_rank


def park_score(row, ballpark_name):
    fit = find_fit(row, ballpark_name)
    if not fit:
        return None
    return score_value((fit.get("ballparkImpact") or {}).get("fitScore"))


def build_defense_lookup(payload):
    lookup = {}
    for group in ["hitters", "pitchers"]:
        for row in payload.get(group, []):
            lookup[player_id(row)] = row
    return lookup


def joined_rows(ballpark_payload, defense_payload, group):
    defense_lookup = build_defense_lookup(defense_payload)
    rows = []
    for row in ballpark_payload.get(group, []):
        item = dict(row)
        item["_defenseAware"] = defense_lookup.get(player_id(row), {})
        rows.append(item)
    return rows


def role_label(row):
    if row.get("role") == "hitter":
        hitter = row.get("hitter") or {}
        return hitter.get("primaryPosition", "unknown")
    pitcher = row.get("pitcher") or {}
    return pitcher.get("pitchingRole", "unknown")


def neutral_score(row):
    return score_value((row.get("_defenseAware") or {}).get("neutralDraftScore"))


def defensive_score(row):
    return score_value((row.get("_defenseAware") or {}).get("defensiveScore"))


def top_by_park_rank(rows, ballpark_name, limit):
    return sorted(
        rows,
        key=lambda row: rank_at_ballpark(row, ballpark_name) or 9999,
    )[:limit]


def premium_anchors(rows, ballpark_name, limit):
    return sorted(
        rows,
        key=lambda row: (
            -(neutral_score(row) or -1),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:limit]


def low_cost_values(rows, ballpark_name, limit, max_salary=1.5):
    candidates = [
        row for row in rows
        if salary_millions(row) is not None and salary_millions(row) <= max_salary
    ]
    return top_by_park_rank(candidates, ballpark_name, limit)


def defensive_anchors(rows, ballpark_name, limit):
    return sorted(
        rows,
        key=lambda row: (
            -(defensive_score(row) or -1),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:limit]


def playable_defensive_anchors(rows, ballpark_name, limit):
    candidates = [
        row for row in rows
        if (defensive_score(row) or 0) >= 75
        and (
            (neutral_score(row) or 0) >= 60
            or (rank_at_ballpark(row, ballpark_name) or 9999) <= 100
        )
    ]
    return sorted(
        candidates,
        key=lambda row: (
            -(defensive_score(row) or -1),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:limit]


def actionable_positive_movers(rows, ballpark_name, limit):
    candidates = [
        row for row in rows
        if park_rank_delta(row, ballpark_name) is not None
        and park_rank_delta(row, ballpark_name) >= 20
        and (neutral_score(row) or 0) >= 55
        and (rank_at_ballpark(row, ballpark_name) or 9999) <= 150
    ]
    return sorted(
        candidates,
        key=lambda row: (
            rank_at_ballpark(row, ballpark_name) or 9999,
            -park_rank_delta(row, ballpark_name),
        ),
    )[:limit]


def positive_movement_cautions(rows, ballpark_name, limit):
    candidates = [
        row for row in rows
        if park_rank_delta(row, ballpark_name) is not None
        and park_rank_delta(row, ballpark_name) >= 20
        and (neutral_score(row) or 0) < 55
    ]
    return sorted(
        candidates,
        key=lambda row: (
            -park_rank_delta(row, ballpark_name),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:limit]


def positive_movers(rows, ballpark_name, limit):
    candidates = [
        row for row in rows
        if park_rank_delta(row, ballpark_name) is not None and park_rank_delta(row, ballpark_name) > 0
    ]
    return sorted(candidates, key=lambda row: -park_rank_delta(row, ballpark_name))[:limit]


def negative_movers(rows, ballpark_name, limit):
    candidates = [
        row for row in rows
        if park_rank_delta(row, ballpark_name) is not None and park_rank_delta(row, ballpark_name) < 0
    ]
    return sorted(candidates, key=lambda row: park_rank_delta(row, ballpark_name))[:limit]


def pitcher_role_targets(rows, ballpark_name, limit, prefix):
    candidates = [
        row for row in rows
        if role_label(row).startswith(prefix)
    ]
    return top_by_park_rank(candidates, ballpark_name, limit)


def fit_factors(rows, ballpark_name):
    for row in rows:
        fit = find_fit(row, ballpark_name)
        if fit:
            return fit.get("factors") or {}, fit.get("bucket")
    return {}, "unknown"


def summarize_park(rows, ballpark_name):
    factors, bucket = fit_factors(rows, ballpark_name)
    return {
        "bucket": bucket,
        "singleLeft": factors.get("singleLeft"),
        "singleRight": factors.get("singleRight"),
        "homeRunLeft": factors.get("homeRunLeft"),
        "homeRunRight": factors.get("homeRunRight"),
    }


def movement_summary(rows, ballpark_name):
    deltas = [
        park_rank_delta(row, ballpark_name)
        for row in rows
        if park_rank_delta(row, ballpark_name) is not None
    ]
    if not deltas:
        return {}
    return {
        "median": median(deltas),
        "positive20": sum(1 for value in deltas if value >= 20),
        "negative20": sum(1 for value in deltas if value <= -20),
        "positive40": sum(1 for value in deltas if value >= 40),
        "negative40": sum(1 for value in deltas if value <= -40),
    }


def observed_summary(path):
    if not path.exists():
        return None
    payload = load_json(path)
    return {
        "csvFiles": payload.get("csvFiles"),
        "parsedFiles": payload.get("parsedFiles"),
        "rows": payload.get("rows"),
        "hitters": payload.get("hitters"),
        "pitchers": payload.get("pitchers"),
        "warnings": payload.get("warnings"),
    }


def bullet_player(row, ballpark_name):
    delta = park_rank_delta(row, ballpark_name)
    delta_text = "n/a" if delta is None else f"{delta:+}"
    return (
        f"- {player_name(row)} | {row.get('role')} {role_label(row)} | "
        f"{salary_raw(row)} | DA {row.get('defenseAwareRank')} | "
        f"{ballpark_name} {rank_at_ballpark(row, ballpark_name)} | "
        f"delta {delta_text} | card {neutral_score(row):.1f}"
        if neutral_score(row) is not None
        else
        f"- {player_name(row)} | {row.get('role')} {role_label(row)} | "
        f"{salary_raw(row)} | DA {row.get('defenseAwareRank')} | "
        f"{ballpark_name} {rank_at_ballpark(row, ballpark_name)} | delta {delta_text}"
    )


def print_list(title, rows, ballpark_name):
    print(f"### {title}")
    print()
    if not rows:
        print("- n/a")
    else:
        for row in rows:
            print(bullet_player(row, ballpark_name))
    print()


def main():
    args = parse_args()

    ballpark_payload = load_json(args.ballpark_aware)
    defense_payload = load_json(args.defense_aware)

    hitters = joined_rows(ballpark_payload, defense_payload, "hitters")
    pitchers = joined_rows(ballpark_payload, defense_payload, "pitchers")

    park = summarize_park(hitters + pitchers, args.ballpark)
    hitter_moves = movement_summary(hitters, args.ballpark)
    pitcher_moves = movement_summary(pitchers, args.ballpark)
    obs = observed_summary(args.observed_manifest)

    print("# BIE Draft Strategy Brief v0")
    print()
    print(f"Season: {ballpark_payload.get('season')}")
    print(f"Ballpark context: {args.ballpark}")
    print(f"Ballpark bucket: {park.get('bucket')}")
    print(
        "Factors: "
        f"1B-L {park.get('singleLeft')} | 1B-R {park.get('singleRight')} | "
        f"HR-L {park.get('homeRunLeft')} | HR-R {park.get('homeRunRight')}"
    )
    print(f"Hitters considered: {len(hitters)}")
    print(f"Pitchers considered: {len(pitchers)}")
    print()

    print("## Executive Summary")
    print()
    print(
        "BIE currently profiles this as a context-sensitive draft environment: "
        "use defense-aware value as the primary board, then treat Comiskey movement "
        "as a supporting lens rather than a final verdict."
    )
    print()
    print(
        "The highest-value hitter list is dominated by low-cost middle-infield and "
        "defense-assisted profiles. That is a cap-efficiency signal, not a complete "
        "lineup-building answer."
    )
    print()
    print(
        "Pitcher value is concentrated in relief and hybrid roles. Starter targets "
        "need separate scrutiny because the v0 model does not yet enforce workload."
    )
    print()

    print("## Park Thesis")
    print()
    print(
        f"{args.ballpark} is classified as `{park.get('bucket')}` in the current "
        "ballpark-aware model. The practical draft read is: do not chase park movement "
        "alone. Prefer players who remain strong after salary and defense are included."
    )
    print()
    print("Hitter park movement summary:")
    print(f"- Median rank delta: {hitter_moves.get('median')}")
    print(f"- Hitters moving up 20+ ranks: {hitter_moves.get('positive20')}")
    print(f"- Hitters moving down 20+ ranks: {hitter_moves.get('negative20')}")
    print(f"- Hitters moving up 40+ ranks: {hitter_moves.get('positive40')}")
    print(f"- Hitters moving down 40+ ranks: {hitter_moves.get('negative40')}")
    print()
    print("Pitcher park movement summary:")
    print(f"- Median rank delta: {pitcher_moves.get('median')}")
    print(f"- Pitchers moving up 20+ ranks: {pitcher_moves.get('positive20')}")
    print(f"- Pitchers moving down 20+ ranks: {pitcher_moves.get('negative20')}")
    print(f"- Pitchers moving up 40+ ranks: {pitcher_moves.get('positive40')}")
    print(f"- Pitchers moving down 40+ ranks: {pitcher_moves.get('negative40')}")
    print()

    print("## Draft Strategy")
    print()
    print("### Hitter Strategy")
    print()
    print("- Treat top value hitters as roster-shape enablers, not automatic lineup anchors.")
    print("- Separate premium card anchors from low-cost defensive/value pieces.")
    print("- Treat defensive anchors as playable only when card strength or overall rank also holds up.")
    print("- Be skeptical of expensive power bats with large negative Comiskey movement.")
    print("- Treat positive park movement as a watchlist signal unless card strength is also credible.")
    print()
    print("### Pitcher Strategy")
    print()
    print("- Use the defense-aware pitcher board as the primary baseline.")
    print("- Separate relief value from starter workload needs.")
    print("- Flag relief-heavy value as role-dependent until roster construction is modeled.")
    print("- Treat Comiskey pitcher fit as supportive evidence, especially when card strength is already high.")
    print()

    print("## Candidate Buckets")
    print()
    print_list("Top Hitter Value Candidates", top_by_park_rank(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Premium Hitter Card Anchors", premium_anchors(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Low-Cost Hitter Role Players", low_cost_values(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Playable Hitter Defensive Anchors", playable_defensive_anchors(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Comiskey Hitter Movement Candidates", actionable_positive_movers(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Comiskey Hitter Movement Cautions", positive_movement_cautions(hitters, args.ballpark, args.top), args.ballpark)
    print_list("Negative Comiskey Hitter Movers", negative_movers(hitters, args.ballpark, args.top), args.ballpark)

    print_list("Top Pitcher Value Candidates", top_by_park_rank(pitchers, args.ballpark, args.top), args.ballpark)
    print_list("Premium Pitcher Card Anchors", premium_anchors(pitchers, args.ballpark, args.top), args.ballpark)
    print_list("Starting Pitcher Targets", pitcher_role_targets(pitchers, args.ballpark, args.top, "S"), args.ballpark)
    print_list("Relief Pitcher Targets", pitcher_role_targets(pitchers, args.ballpark, args.top, "R"), args.ballpark)
    print_list("Positive Comiskey Pitcher Movers", positive_movers(pitchers, args.ballpark, args.top), args.ballpark)
    print_list("Negative Comiskey Pitcher Movers", negative_movers(pitchers, args.ballpark, args.top), args.ballpark)

    print("## Observed Calibration Read")
    print()
    if obs:
        print(f"- Observed files: {obs.get('csvFiles')}")
        print(f"- Observed player-seasons: {obs.get('rows')}")
        print(f"- Observed hitters: {obs.get('hitters')}")
        print(f"- Observed pitchers: {obs.get('pitchers')}")
        print(f"- Warnings: {obs.get('warnings')}")
        print()
    print(
        "Calibration is currently useful for model caution, not statistical certainty. "
        "The observed Aquarium sample is enough to show that positive Comiskey movement "
        "does not guarantee production and that strong players can survive negative "
        "park movement."
    )
    print()

    print("## Product Implications")
    print()
    print("- BIE should present rankings as explainable evidence, not absolute draft orders.")
    print("- The next product layer should synthesize roster construction from these buckets.")
    print("- The 1968 transition should start by proving card, ballpark, and signal generation parity.")
    print("- UI remains premature until strategy synthesis is stable.")
    print()

    print("## Next Analytical Questions")
    print()
    print("1. Which candidate buckets overlap enough to become draft priorities?")
    print("2. Which premium anchors are worth paying for after park movement?")
    print("3. How much salary should be allocated to relief versus starting pitching?")
    print("4. Which low-cost value candidates are playable versus fake value?")
    print("5. Which 1980 assumptions must be retested before applying BIE to 1968?")


if __name__ == "__main__":
    main()
