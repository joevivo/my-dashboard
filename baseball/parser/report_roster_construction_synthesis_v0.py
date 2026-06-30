import argparse
import json
from pathlib import Path

DEFAULT_BALLPARK_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json"
)
DEFAULT_DEFENSE_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json"
)
DEFAULT_BALLPARK_NAME = "Comiskey Park 1980"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate BIE roster construction synthesis from current draft signals."
    )
    parser.add_argument("--ballpark-aware", type=Path, default=DEFAULT_BALLPARK_AWARE_PATH)
    parser.add_argument("--defense-aware", type=Path, default=DEFAULT_DEFENSE_AWARE_PATH)
    parser.add_argument("--ballpark", default=DEFAULT_BALLPARK_NAME)
    parser.add_argument("--top", type=int, default=8)
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def player_id(row):
    return row.get("player", {}).get("playerId")


def player_name(row):
    return row.get("player", {}).get("playerName", "UNKNOWN")


def score_value(score):
    if not isinstance(score, dict):
        return None
    return score.get("score") or (score.get("scoreFraction") or {}).get("decimal")


def salary_raw(row):
    return (row.get("salary") or {}).get("raw", "n/a")


def salary_millions(row):
    return ((row.get("salary") or {}).get("millions") or {}).get("decimal")


def find_fit(row, ballpark_name):
    for fit in row.get("ballparkFits") or []:
        if fit.get("ballparkName") == ballpark_name:
            return fit
    return None


def park_rank(row, ballpark_name):
    fit = find_fit(row, ballpark_name)
    if fit:
        return (fit.get("ballparkImpact") or {}).get("parkAdjustedRank")
    return row.get("ballparkAwareRank")


def park_delta(row, ballpark_name):
    da = row.get("defenseAwareRank")
    pr = park_rank(row, ballpark_name)
    if da is None or pr is None:
        return None
    return da - pr


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
        return (row.get("hitter") or {}).get("primaryPosition", "unknown")
    return (row.get("pitcher") or {}).get("pitchingRole", "unknown")


def neutral_score(row):
    return score_value((row.get("_defenseAware") or {}).get("neutralDraftScore"))


def defensive_score(row):
    return score_value((row.get("_defenseAware") or {}).get("defensiveScore"))


def by_park_rank(rows, ballpark_name):
    return sorted(rows, key=lambda row: park_rank(row, ballpark_name) or 9999)


def low_cost(rows, max_salary):
    return [
        row for row in rows
        if salary_millions(row) is not None and salary_millions(row) <= max_salary
    ]


def salary_band(rows, low, high):
    return [
        row for row in rows
        if salary_millions(row) is not None and low <= salary_millions(row) <= high
    ]


def premium(rows, min_score=85):
    return [row for row in rows if (neutral_score(row) or 0) >= min_score]


def starters(rows):
    return [row for row in rows if role_label(row).startswith("S")]


def relievers(rows):
    return [row for row in rows if role_label(row).startswith("R")]


def playable_defense(rows):
    return [
        row for row in rows
        if (defensive_score(row) or 0) >= 75
        and ((neutral_score(row) or 0) >= 60 or (row.get("defenseAwareRank") or 9999) <= 100)
    ]


def movement_candidates(rows, ballpark_name):
    return [
        row for row in rows
        if park_delta(row, ballpark_name) is not None
        and park_delta(row, ballpark_name) >= 20
        and (neutral_score(row) or 0) >= 55
        and (park_rank(row, ballpark_name) or 9999) <= 150
    ]


def movement_cautions(rows, ballpark_name):
    return [
        row for row in rows
        if park_delta(row, ballpark_name) is not None
        and park_delta(row, ballpark_name) >= 20
        and (neutral_score(row) or 0) < 55
    ]


def negative_movers(rows, ballpark_name):
    return [
        row for row in rows
        if park_delta(row, ballpark_name) is not None
        and park_delta(row, ballpark_name) <= -40
    ]


def bullet(row, ballpark_name):
    delta = park_delta(row, ballpark_name)
    delta_text = "n/a" if delta is None else f"{delta:+}"
    card = neutral_score(row)
    card_text = "n/a" if card is None else f"{card:.1f}"
    return (
        f"- {player_name(row)} | {row.get('role')} {role_label(row)} | "
        f"{salary_raw(row)} | DA {row.get('defenseAwareRank')} | "
        f"park {park_rank(row, ballpark_name)} | delta {delta_text} | card {card_text}"
    )


def print_players(title, rows, ballpark_name, limit):
    print(f"### {title}")
    print()
    if not rows:
        print("- n/a")
    else:
        for row in rows[:limit]:
            print(bullet(row, ballpark_name))
    print()


def main():
    args = parse_args()

    ballpark_payload = load_json(args.ballpark_aware)
    defense_payload = load_json(args.defense_aware)

    hitters = joined_rows(ballpark_payload, defense_payload, "hitters")
    pitchers = joined_rows(ballpark_payload, defense_payload, "pitchers")

    hitter_value = by_park_rank(hitters, args.ballpark)
    pitcher_value = by_park_rank(pitchers, args.ballpark)

    low_cost_hitters = by_park_rank(low_cost(hitters, 1.5), args.ballpark)
    low_cost_pitchers = by_park_rank(low_cost(pitchers, 1.5), args.ballpark)
    mid_salary_hitters = by_park_rank(salary_band(hitters, 1.5, 5.0), args.ballpark)
    mid_salary_pitchers = by_park_rank(salary_band(pitchers, 1.5, 5.0), args.ballpark)

    premium_hitters = by_park_rank(premium(hitters, 85), args.ballpark)
    premium_pitchers = by_park_rank(premium(pitchers, 90), args.ballpark)

    starter_targets = by_park_rank(starters(pitchers), args.ballpark)
    relief_targets = by_park_rank(relievers(pitchers), args.ballpark)

    defensive_hitters = by_park_rank(playable_defense(hitters), args.ballpark)
    hitter_movement_candidates = by_park_rank(movement_candidates(hitters, args.ballpark), args.ballpark)
    hitter_movement_cautions = sorted(
        movement_cautions(hitters, args.ballpark),
        key=lambda row: -(park_delta(row, args.ballpark) or 0),
    )
    hitter_negative_movers = sorted(
        negative_movers(hitters, args.ballpark),
        key=lambda row: park_delta(row, args.ballpark) or 0,
    )

    print("# BIE Roster Construction Synthesis v0")
    print()
    print(f"Season: {ballpark_payload.get('season')}")
    print(f"Ballpark context: {args.ballpark}")
    print("Roster model: analytical synthesis only; no optimizer or draft-order enforcement.")
    print()

    print("## Executive Construction Read")
    print()
    print(
        "The current Comiskey profile favors a roster spine built from low-cost middle-infield value, "
        "selective premium bats that survive park penalties, and a relief-forward pitching pool. "
        "The model is not yet enforcing innings, injuries, platoons, or positional scarcity, so the "
        "output should be read as roster architecture rather than a final roster."
    )
    print()

    print("## Recommended Roster Archetypes")
    print()
    print("### Archetype A: Value Spine + Selective Premium Anchor")
    print()
    print("- Build the cheap defensive/value spine first.")
    print("- Pay for one premium hitter only if the card strength remains elite after Comiskey movement.")
    print("- Use mid-salary hitters to cover positions that the low-cost pool does not solve.")
    print("- Risk: can become offensively thin if cheap value pieces are mistaken for lineup anchors.")
    print()
    print("### Archetype B: Pitching-Supported Run Suppression")
    print()
    print("- Lean into Comiskey's run-suppressing shape.")
    print("- Use strong relief and hybrid pitcher values aggressively.")
    print("- Add enough starter workload to avoid overfitting to relief rankings.")
    print("- Risk: v0 pitcher value is relief-heavy and does not yet enforce innings.")
    print()
    print("### Archetype C: Balanced Card Strength")
    print()
    print("- Use defense-aware rank as the primary board.")
    print("- Blend premium card anchors with low-cost role players.")
    print("- Treat park movement as tie-breaker, not doctrine.")
    print("- Risk: may miss extreme salary efficiency if too much cap is spent on recognizable names.")
    print()

    print("## Budget Sketches")
    print()
    print("These are planning shapes, not optimizer outputs.")
    print()
    print("| Shape | Hitters | Starters | Relief | Bench/Flex | Use Case |")
    print("|---|---:|---:|---:|---:|---|")
    print("| Value Spine | $38-44M | $18-24M | $10-16M | $4-8M | Maximize cap flexibility |")
    print("| Pitching-Supported | $34-40M | $22-28M | $12-18M | $3-7M | Lean into run suppression |")
    print("| Premium Anchor | $42-50M | $16-23M | $8-14M | $3-6M | Pay for one elite bat |")
    print()

    print("## Draft Priorities")
    print()
    print("1. Lock in scarce playable value, especially SS/2B profiles that BIE repeatedly surfaces.")
    print("2. Decide whether to buy one premium hitter anchor or spread salary across balanced bats.")
    print("3. Separate starter workload from relief dominance before final pitcher selection.")
    print("4. Treat positive Comiskey hitter movement as a watchlist unless card strength is credible.")
    print("5. Avoid overpaying for power bats with severe negative Comiskey movement.")
    print()

    print("## Candidate Pools")
    print()
    print_players("Low-Cost Hitter Spine", low_cost_hitters, args.ballpark, args.top)
    print_players("Mid-Salary Hitter Fillers", mid_salary_hitters, args.ballpark, args.top)
    print_players("Premium Hitter Anchors", premium_hitters, args.ballpark, args.top)
    print_players("Playable Defensive Hitters", defensive_hitters, args.ballpark, args.top)
    print_players("Comiskey Hitter Movement Candidates", hitter_movement_candidates, args.ballpark, args.top)
    print_players("Comiskey Hitter Movement Cautions", hitter_movement_cautions, args.ballpark, args.top)
    print_players("Large Negative Comiskey Hitter Movers", hitter_negative_movers, args.ballpark, args.top)
    print_players("Low-Cost Pitcher Values", low_cost_pitchers, args.ballpark, args.top)
    print_players("Mid-Salary Pitcher Values", mid_salary_pitchers, args.ballpark, args.top)
    print_players("Premium Pitcher Anchors", premium_pitchers, args.ballpark, args.top)
    print_players("Starter Workload Targets", starter_targets, args.ballpark, args.top)
    print_players("Relief Targets", relief_targets, args.ballpark, args.top)

    print("## Model Cautions")
    print()
    print("- This is not yet an optimizer.")
    print("- It does not enforce 25-player roster rules.")
    print("- It does not model injuries or plate appearance allocation.")
    print("- It does not model bullpen fatigue or innings requirements.")
    print("- It does not yet model platoon deployment.")
    print("- It does not yet use league draft order or opponent rosters.")
    print()

    print("## Next Product Step")
    print()
    print(
        "Turn this synthesis into a roster-template evaluator: given a proposed roster, "
        "score whether it matches a chosen archetype and where it violates workload, "
        "position coverage, salary allocation, or model-risk constraints."
    )


if __name__ == "__main__":
    main()
