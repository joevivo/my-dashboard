import argparse
import csv
import json
from pathlib import Path

DEFAULT_BALLPARK_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json"
)
DEFAULT_DEFENSE_AWARE_PATH = Path(
    "data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json"
)
DEFAULT_BALLPARK_NAME = "Comiskey Park 1980"
DEFAULT_CAP_MILLIONS = 80.0


ARCHETYPES = {
    "value-spine": {
        "name": "Value Spine + Selective Premium Anchor",
        "salary": {
            "hitters": (38.0, 44.0),
            "starters": (18.0, 24.0),
            "relief": (10.0, 16.0),
            "benchFlex": (4.0, 8.0),
        },
        "principle": "Cheap defensive/value spine plus one selective premium hitter.",
    },
    "pitching-supported": {
        "name": "Pitching-Supported Run Suppression",
        "salary": {
            "hitters": (34.0, 40.0),
            "starters": (22.0, 28.0),
            "relief": (12.0, 18.0),
            "benchFlex": (3.0, 7.0),
        },
        "principle": "Lean into run suppression with stronger pitching allocation.",
    },
    "premium-anchor": {
        "name": "Premium Anchor",
        "salary": {
            "hitters": (42.0, 50.0),
            "starters": (16.0, 23.0),
            "relief": (8.0, 14.0),
            "benchFlex": (3.0, 6.0),
        },
        "principle": "Pay for one elite bat while preserving a balanced support structure.",
    },
}


REQUIRED_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate a proposed Strat roster against a BIE roster archetype."
    )
    parser.add_argument("roster_csv", type=Path)
    parser.add_argument("--ballpark-aware", type=Path, default=DEFAULT_BALLPARK_AWARE_PATH)
    parser.add_argument("--defense-aware", type=Path, default=DEFAULT_DEFENSE_AWARE_PATH)
    parser.add_argument("--ballpark", default=DEFAULT_BALLPARK_NAME)
    parser.add_argument("--archetype", choices=sorted(ARCHETYPES), default="value-spine")
    parser.add_argument(
        "--compare-archetypes",
        action="store_true",
        help="Compare the roster against every supported archetype.",
    )
    parser.add_argument("--cap", type=float, default=DEFAULT_CAP_MILLIONS)
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_name(value):
    return " ".join((value or "").strip().lower().replace(".", "").split())


def player_id(row):
    return row.get("player", {}).get("playerId")


def player_name(row):
    return row.get("player", {}).get("playerName", "UNKNOWN")


def score_value(score):
    if not isinstance(score, dict):
        return None
    return score.get("score") or (score.get("scoreFraction") or {}).get("decimal")


def salary_millions(row):
    return ((row.get("salary") or {}).get("millions") or {}).get("decimal")


def salary_raw(row):
    return (row.get("salary") or {}).get("raw", "n/a")


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


def build_player_lookup(ballpark_payload, defense_payload):
    defense_lookup = build_defense_lookup(defense_payload)
    by_id = {}
    by_name = {}

    for group in ["hitters", "pitchers"]:
        for row in ballpark_payload.get(group, []):
            item = dict(row)
            item["_defenseAware"] = defense_lookup.get(player_id(row), {})
            by_id[str(player_id(row))] = item
            by_name[normalize_name(player_name(row))] = item

    return by_id, by_name


def role_label(row):
    if row.get("role") == "hitter":
        return (row.get("hitter") or {}).get("primaryPosition", "unknown")
    return (row.get("pitcher") or {}).get("pitchingRole", "unknown")


def neutral_score(row):
    return score_value((row.get("_defenseAware") or {}).get("neutralDraftScore"))


def defensive_score(row):
    return score_value((row.get("_defenseAware") or {}).get("defensiveScore"))


def load_roster(path, by_id, by_name):
    rows = []
    unresolved = []

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            lookup_id = (raw.get("playerId") or raw.get("player_id") or "").strip()
            lookup_name = raw.get("playerName") or raw.get("player") or raw.get("name") or ""
            slot = (raw.get("slot") or raw.get("rosterSlot") or "").strip()

            # Tolerate simple roster CSV rows like:
            # playerName,slot
            # Foli, Tim,SS
            #
            # csv.DictReader parses that as:
            # {"playerName": "Foli", "slot": " Tim", None: ["SS"]}
            extra_fields = raw.get(None)
            if extra_fields and lookup_name and slot:
                lookup_name = f"{lookup_name}, {slot.strip()}"
                slot = str(extra_fields[0]).strip()

            player = None

            if lookup_id:
                player = by_id.get(lookup_id)
            if player is None and lookup_name:
                player = by_name.get(normalize_name(lookup_name))

            if player is None:
                unresolved.append(raw)
                continue

            rows.append({
                "input": raw,
                "player": player,
                "slot": slot,
            })

    return rows, unresolved


def role_bucket(item):
    player = item["player"]
    slot = item.get("slot", "").lower()
    role = player.get("role")
    label = role_label(player)

    if role == "hitter":
        return "hitters"

    if "starter" in slot:
        return "starters"
    if "relief" in slot or "bullpen" in slot:
        return "relief"

    if label.startswith("S"):
        return "starters"
    return "relief"


def bucket_salary(rows):
    totals = {"hitters": 0.0, "starters": 0.0, "relief": 0.0, "benchFlex": 0.0}
    for item in rows:
        player = item["player"]
        salary = salary_millions(player) or 0.0
        totals[role_bucket(item)] += salary
    return totals


def position_coverage(rows):
    coverage = {position: [] for position in REQUIRED_POSITIONS}
    for item in rows:
        player = item["player"]
        if player.get("role") != "hitter":
            continue
        primary = role_label(player)
        if primary in coverage:
            coverage[primary].append(player_name(player))
    return coverage


def salary_flag(label, value, target_range):
    low, high = target_range
    if value < low:
        return f"[warning] {label} salary below archetype range: ${value:.2f}M vs ${low:.2f}-${high:.2f}M"
    if value > high:
        return f"[warning] {label} salary above archetype range: ${value:.2f}M vs ${low:.2f}-${high:.2f}M"
    return f"[ok] {label} salary within archetype range: ${value:.2f}M"


def improvement_targets(salary_totals, archetype, coverage, rows, ballpark_name, cap_millions):
    targets = []

    total_salary = sum(salary_totals.values())
    cap_gap = cap_millions - total_salary
    if cap_gap > 10:
        targets.append(f"Add approximately ${cap_gap:.2f}M in useful salary before treating this as a full-cap roster.")

    for label in ["hitters", "starters", "relief"]:
        low, high = archetype["salary"][label]
        value = salary_totals[label]
        if value < low:
            targets.append(f"Add ${low - value:.2f}M+ to {label} to reach the archetype floor.")
        elif value > high:
            targets.append(f"Reduce ${value - high:.2f}M+ from {label} to return to the archetype range.")

    missing = [position for position, players in coverage.items() if not players]
    if missing:
        targets.append(f"Resolve missing position coverage: {', '.join(missing)}.")

    pitchers = [item for item in rows if item["player"].get("role") == "pitcher"]
    starters = [item for item in pitchers if role_bucket(item) == "starters"]
    relievers = [item for item in pitchers if role_bucket(item) == "relief"]

    if len(starters) < 4:
        targets.append("Add starter workload before trusting the roster shape.")
    if len(relievers) < 4:
        targets.append("Add relief depth before trusting the bullpen shape.")

    high_salary_negative_movers = []
    for item in rows:
        player = item["player"]
        salary = salary_millions(player) or 0.0
        delta = park_delta(player, ballpark_name)
        if salary >= 7.5 and delta is not None and delta <= -30:
            high_salary_negative_movers.append(player_name(player))

    if high_salary_negative_movers:
        targets.append(
            "Review expensive negative park movers: "
            + ", ".join(high_salary_negative_movers)
            + "."
        )

    if not targets:
        targets.append("No major structural improvement targets detected.")

    return targets


def model_risks(item, ballpark_name):
    player = item["player"]
    risks = []
    salary = salary_millions(player) or 0.0
    card = neutral_score(player)
    defense = defensive_score(player)
    delta = park_delta(player, ballpark_name)

    if salary >= 7.5:
        risks.append("high salary commitment")
    if card is not None and card < 55:
        risks.append("card-strength risk")
    if defense is not None and defense < 50:
        risks.append("defensive risk")
    if player.get("role") == "pitcher" and role_label(player).startswith("R"):
        risks.append("relief/workload dependency")
    if delta is not None and delta <= -40:
        risks.append("large negative park movement")
    if delta is not None and delta >= 30 and card is not None and card < 55:
        risks.append("positive movement / thin card caution")

    return risks


def archetype_score(rows, unresolved, salary_totals, archetype, coverage, ballpark_name, cap_millions):
    score = 100
    flags = []

    if unresolved:
        score -= min(20, len(unresolved) * 5)
        flags.append(f"[error] Unresolved roster rows: {len(unresolved)}")

    total_salary = sum(salary_totals.values())
    if total_salary > cap_millions:
        score -= 20
        flags.append(f"[error] Salary exceeds ${cap_millions:.0f}M cap: ${total_salary:.2f}M")
    elif total_salary < (cap_millions - 10):
        score -= 8
        flags.append(
            f"[warning] Salary materially below ${cap_millions:.0f}M cap: ${total_salary:.2f}M"
        )
    else:
        flags.append(f"[ok] Salary total: ${total_salary:.2f}M")

    for label, value in salary_totals.items():
        if label == "benchFlex":
            continue
        flag = salary_flag(label, value, archetype["salary"][label])
        flags.append(flag)
        if flag.startswith("[warning]"):
            score -= 6

    missing = [position for position, players in coverage.items() if not players]
    if missing:
        score -= min(24, len(missing) * 4)
        flags.append(f"[error] Missing required positions: {', '.join(missing)}")
    else:
        flags.append("[ok] Required hitter positions covered")

    pitchers = [item for item in rows if item["player"].get("role") == "pitcher"]
    starters = [item for item in pitchers if role_bucket(item) == "starters"]
    relievers = [item for item in pitchers if role_bucket(item) == "relief"]

    if len(starters) < 4:
        score -= 10
        flags.append(f"[warning] Starter count thin: {len(starters)}")
    else:
        flags.append(f"[ok] Starter count: {len(starters)}")

    if len(relievers) < 4:
        score -= 6
        flags.append(f"[warning] Relief count thin: {len(relievers)}")
    else:
        flags.append(f"[ok] Relief count: {len(relievers)}")

    risk_items = []
    for item in rows:
        risks = model_risks(item, ballpark_name)
        if risks:
            risk_items.append((item, risks))

    if len(risk_items) >= 8:
        score -= 8
        flags.append(f"[warning] High number of model-risk players: {len(risk_items)}")
    else:
        flags.append(f"[ok] Model-risk player count: {len(risk_items)}")

    return max(0, score), flags, risk_items


def print_player_line(item, ballpark_name):
    player = item["player"]
    delta = park_delta(player, ballpark_name)
    delta_text = "n/a" if delta is None else f"{delta:+}"
    card = neutral_score(player)
    card_text = "n/a" if card is None else f"{card:.1f}"
    print(
        f"- {player_name(player)} | {player.get('role')} {role_label(player)} | "
        f"{salary_raw(player)} | DA {player.get('defenseAwareRank')} | "
        f"park {park_rank(player, ballpark_name)} | delta {delta_text} | card {card_text}"
    )


def main():
    args = parse_args()

    ballpark_payload = load_json(args.ballpark_aware)
    defense_payload = load_json(args.defense_aware)
    by_id, by_name = build_player_lookup(ballpark_payload, defense_payload)

    rows, unresolved = load_roster(args.roster_csv, by_id, by_name)
    salary_totals = bucket_salary(rows)
    coverage = position_coverage(rows)

    if args.compare_archetypes:
        print("# BIE Roster Archetype Comparison v0")
        print()
        print(f"Roster input: {args.roster_csv}")
        print(f"Season: {ballpark_payload.get('season')}")
        print(f"Ballpark: {args.ballpark}")
        print(f"Players resolved: {len(rows)}")
        print(f"Rows unresolved: {len(unresolved)}")
        print(f"Salary total: ${sum(salary_totals.values()):.2f}M")
        print()
        print("| Archetype | Score | Errors | Warnings | Notes |")
        print("|---|---:|---:|---:|---|")
        for archetype_key, candidate in ARCHETYPES.items():
            score, flags, risk_items = archetype_score(
                rows, unresolved, salary_totals, candidate, coverage, args.ballpark, args.cap
            )
            errors = sum(1 for flag in flags if flag.startswith("[error]"))
            warnings = sum(1 for flag in flags if flag.startswith("[warning]"))
            note = "; ".join(
                flag.replace("[warning] ", "").replace("[error] ", "")
                for flag in flags
                if flag.startswith("[warning]") or flag.startswith("[error]")
            )
            if not note:
                note = "clean fit"
            print(
                f"| {archetype_key} | {score} | {errors} | {warnings} | {note} |"
            )
        return

    archetype = ARCHETYPES[args.archetype]
    score, flags, risk_items = archetype_score(
        rows, unresolved, salary_totals, archetype, coverage, args.ballpark, args.cap
    )

    print("# BIE Roster Template Evaluation v0")
    print()
    print(f"Roster input: {args.roster_csv}")
    print(f"Season: {ballpark_payload.get('season')}")
    print(f"Ballpark: {args.ballpark}")
    print(f"Archetype: {archetype['name']}")
    print(f"Archetype principle: {archetype['principle']}")
    print(f"Players resolved: {len(rows)}")
    print(f"Rows unresolved: {len(unresolved)}")
    print()
    print(f"## Archetype Match Score: {score}/100")
    print()
    for flag in flags:
        print(f"- {flag}")
    print()

    print("## Salary Allocation")
    print()
    print(f"- Hitters: ${salary_totals['hitters']:.2f}M")
    print(f"- Starters: ${salary_totals['starters']:.2f}M")
    print(f"- Relief: ${salary_totals['relief']:.2f}M")
    print(f"- Total: ${sum(salary_totals.values()):.2f}M")
    print()

    print("## Improvement Targets")
    print()
    for target in improvement_targets(
        salary_totals, archetype, coverage, rows, args.ballpark, args.cap
    ):
        print(f"- {target}")
    print()

    print("## Position Coverage")
    print()
    for position in REQUIRED_POSITIONS:
        players = coverage[position]
        if players:
            print(f"- {position}: {', '.join(players)}")
        else:
            print(f"- {position}: MISSING")
    print()

    print("## Player Signal Snapshot")
    print()
    for item in rows:
        print_player_line(item, args.ballpark)
    print()

    print("## Model-Risk Players")
    print()
    if not risk_items:
        print("- n/a")
    else:
        for item, risks in risk_items:
            print(f"- {player_name(item['player'])}: {', '.join(risks)}")
    print()

    print("## Unresolved Rows")
    print()
    if not unresolved:
        print("- n/a")
    else:
        for raw in unresolved:
            print(f"- {raw}")


if __name__ == "__main__":
    main()
