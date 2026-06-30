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
        description="Explain BIE draft candidates by role using current 1980 draft signals."
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
    value = score.get("score")
    if value is None:
        value = (score.get("scoreFraction") or {}).get("decimal")
    return value


def fmt(value, digits=1):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def salary_raw(row):
    return (row.get("salary") or {}).get("raw", "n/a")


def salary_millions(row):
    return ((row.get("salary") or {}).get("millions") or {}).get("decimal")


def find_fit(row, ballpark_name):
    for fit in row.get("ballparkFits") or []:
        if fit.get("ballparkName") == ballpark_name:
            return fit
    return None


def build_defense_lookup(payload):
    lookup = {}
    for group in ["hitters", "pitchers"]:
        for row in payload.get(group, []):
            lookup[player_id(row)] = row
    return lookup


def joined_rows(ballpark_payload, defense_payload, role):
    defense_lookup = build_defense_lookup(defense_payload)
    group = "hitters" if role == "hitter" else "pitchers"
    rows = []
    for row in ballpark_payload.get(group, []):
        defense_row = defense_lookup.get(player_id(row), {})
        item = dict(row)
        item["_defenseAware"] = defense_row
        rows.append(item)
    return rows


def rank_at_ballpark(row, ballpark_name):
    fit = find_fit(row, ballpark_name)
    if not fit:
        return row.get("ballparkAwareRank")
    return (fit.get("ballparkImpact") or {}).get("parkAdjustedRank")


def park_score(row, ballpark_name):
    fit = find_fit(row, ballpark_name)
    if not fit:
        return None
    return score_value((fit.get("ballparkImpact") or {}).get("fitScore"))


def park_score_label(score):
    if score is None:
        return "unknown park fit"
    if score >= 57:
        return "strong park fit"
    if score >= 52:
        return "positive park fit"
    if score <= 45:
        return "negative park fit"
    if score <= 48:
        return "soft park fit"
    return "neutral park fit"


def park_rank_delta(row, ballpark_name):
    defense_rank = row.get("defenseAwareRank")
    park_rank = rank_at_ballpark(row, ballpark_name)
    if defense_rank is None or park_rank is None:
        return None
    return defense_rank - park_rank


def position_or_role(row):
    if row.get("role") == "hitter":
        hitter = row.get("hitter") or {}
        return hitter.get("primaryPosition", "unknown")
    pitcher = row.get("pitcher") or {}
    return pitcher.get("pitchingRole", "unknown")


def card_strength_phrase(defense_row):
    neutral = score_value(defense_row.get("neutralDraftScore"))
    if neutral is None:
        return "card strength unavailable"
    if neutral >= 70:
        return f"strong raw card profile ({fmt(neutral, 1)})"
    if neutral >= 62:
        return f"solid raw card profile ({fmt(neutral, 1)})"
    if neutral >= 55:
        return f"usable raw card profile ({fmt(neutral, 1)})"
    return f"thin raw card profile ({fmt(neutral, 1)})"


def salary_phrase(row, defense_row):
    salary = salary_millions(row)
    salary_rank = defense_row.get("salaryAdjustedRank")
    salary_score = score_value(defense_row.get("salaryAdjustedScore"))
    if salary is None:
        return "salary value unavailable"
    if salary <= 1.25 and salary_rank and salary_rank <= 75:
        return f"strong low-cost value at {salary_raw(row)}"
    if salary_rank and salary_rank <= 75:
        return f"strong salary-adjusted value at {salary_raw(row)}"
    if salary_rank and salary_rank <= 150:
        return f"reasonable salary-adjusted value at {salary_raw(row)}"
    if salary >= 7.5:
        return f"expensive profile at {salary_raw(row)}"
    if salary_score is not None:
        return f"middling salary-adjusted value at {salary_raw(row)}"
    return f"salary {salary_raw(row)}"


def defense_phrase(row, defense_row):
    if row.get("role") == "hitter":
        best = defense_row.get("bestDefensivePosition") or {}
        defensive_score = score_value(defense_row.get("defensiveScore"))
        raw = best.get("raw")
        if defense_row.get("defenseNeutralized"):
            return "defense neutralized"
        if defensive_score is None:
            return "defense unavailable"
        if defensive_score >= 80:
            return f"plus defense at {best.get('position', 'unknown')} ({raw})"
        if defensive_score >= 65:
            return f"useful defense at {best.get('position', 'unknown')} ({raw})"
        if defensive_score >= 50:
            return f"playable defense at {best.get('position', 'unknown')} ({raw})"
        return f"defensive liability at {best.get('position', 'unknown')} ({raw})"

    defensive_score = score_value(defense_row.get("defensiveScore"))
    raw = defense_row.get("pitcherDefenseRaw") or {}
    parts = []
    if raw.get("hold") is not None:
        parts.append(f"hold {raw.get('hold')}")
    if raw.get("wildPitch") is not None:
        parts.append(f"wp {raw.get('wildPitch')}")
    if raw.get("pitcherDefense") is not None:
        parts.append(f"p-{raw.get('pitcherDefense')}")
    detail = ", ".join(parts) if parts else "pitcher defense details unavailable"
    if defensive_score is None:
        return detail
    if defensive_score >= 70:
        return f"plus pitcher-control/defense ({detail})"
    if defensive_score >= 55:
        return f"acceptable pitcher-control/defense ({detail})"
    return f"pitcher-control risk ({detail})"


def rank_word(count):
    return "rank" if abs(count) == 1 else "ranks"


def park_phrase(row, ballpark_name):
    score = park_score(row, ballpark_name)
    delta = park_rank_delta(row, ballpark_name)
    fit = find_fit(row, ballpark_name)
    bucket = fit.get("bucket") if fit else "unknown"
    if delta is None:
        movement = "rank movement unavailable"
    elif delta > 0:
        movement = f"moves up {delta} {rank_word(delta)}"
    elif delta < 0:
        movement = f"moves down {abs(delta)} {rank_word(delta)}"
    else:
        movement = "no rank movement"
    return f"{park_score_label(score)} for {ballpark_name} ({bucket}, {movement})"


def risk_flags(row, defense_row, ballpark_name):
    risks = []
    salary = salary_millions(row)
    neutral = score_value(defense_row.get("neutralDraftScore"))
    defensive_score = score_value(defense_row.get("defensiveScore"))
    park_delta = park_rank_delta(row, ballpark_name)
    fit_score = park_score(row, ballpark_name)

    if salary is not None and salary >= 7.5:
        risks.append("high salary commitment")
    if neutral is not None and neutral < 58:
        risks.append("card-strength risk")
    if defensive_score is not None and defensive_score < 50:
        risks.append("defensive risk")
    if row.get("role") == "pitcher" and defensive_score is not None and defensive_score < 55:
        risks.append("pitcher-control risk")
    # Park context is already explained separately. Only large rank movement
    # should become a risk flag in v0; otherwise this gets too noisy in
    # run-suppressing parks like Comiskey.
    if park_delta is not None and park_delta < -20:
        risks.append("large negative park movement")
    if row.get("role") == "pitcher":
        pitching_role = (row.get("pitcher") or {}).get("pitchingRole", "")
        if pitching_role.startswith("R"):
            risks.append("role/workload dependency")
    if not risks:
        risks.append("no major v0 risk flag")
    return risks


def explain_candidate(row, ballpark_name):
    defense_row = row.get("_defenseAware") or {}
    defense_rank = row.get("defenseAwareRank")
    park_rank = rank_at_ballpark(row, ballpark_name)
    role_label = position_or_role(row)

    lines = [
        f"### {player_name(row)}",
        "",
        f"- Role: {row.get('role')} / {role_label}",
        f"- Salary: {salary_raw(row)}",
        f"- Defense-aware rank: {defense_rank}",
        f"- {ballpark_name} rank: {park_rank}",
        f"- Card strength: {card_strength_phrase(defense_row)}",
        f"- Salary value: {salary_phrase(row, defense_row)}",
        f"- Defense: {defense_phrase(row, defense_row)}",
        f"- Park fit: {park_phrase(row, ballpark_name)}",
        f"- Risk: {', '.join(risk_flags(row, defense_row, ballpark_name))}",
        "",
    ]
    return lines


def top_overall(rows, top, ballpark_name):
    return sorted(
        rows,
        key=lambda row: rank_at_ballpark(row, ballpark_name) or 9999,
    )[:top]


def role_representatives(rows, role, ballpark_name):
    if role == "hitter":
        role_order = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
        key_fn = lambda row: (row.get("hitter") or {}).get("primaryPosition", "unknown")
    else:
        role_order = ["S9", "S8", "S7", "S6", "S5", "R5", "R4", "R3", "R2", "R1"]
        key_fn = lambda row: (row.get("pitcher") or {}).get("pitchingRole", "unknown")

    selected = []
    for role_key in role_order:
        candidates = [row for row in rows if key_fn(row) == role_key]
        candidates = sorted(
            candidates,
            key=lambda row: rank_at_ballpark(row, ballpark_name) or 9999,
        )
        if candidates:
            selected.append(candidates[0])

    return selected


def premium_card_anchors(rows, top, ballpark_name):
    return sorted(
        rows,
        key=lambda row: (
            -(score_value((row.get("_defenseAware") or {}).get("neutralDraftScore")) or -1),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:top]


def low_cost_value_candidates(rows, top, ballpark_name, max_salary=1.5):
    candidates = [
        row for row in rows
        if (salary_millions(row) is not None and salary_millions(row) <= max_salary)
    ]
    return sorted(
        candidates,
        key=lambda row: rank_at_ballpark(row, ballpark_name) or 9999,
    )[:top]


def defensive_anchor_candidates(rows, top, ballpark_name):
    return sorted(
        rows,
        key=lambda row: (
            -(score_value((row.get("_defenseAware") or {}).get("defensiveScore")) or -1),
            rank_at_ballpark(row, ballpark_name) or 9999,
        ),
    )[:top]


def park_movers(rows, top, ballpark_name, direction):
    candidates = [
        row for row in rows
        if park_rank_delta(row, ballpark_name) is not None
    ]
    if direction == "positive":
        candidates = [row for row in candidates if park_rank_delta(row, ballpark_name) > 0]
        return sorted(candidates, key=lambda row: -park_rank_delta(row, ballpark_name))[:top]
    candidates = [row for row in candidates if park_rank_delta(row, ballpark_name) < 0]
    return sorted(candidates, key=lambda row: park_rank_delta(row, ballpark_name))[:top]


def pitcher_role_candidates(rows, top, ballpark_name, prefix):
    candidates = [
        row for row in rows
        if ((row.get("pitcher") or {}).get("pitchingRole") or "").startswith(prefix)
    ]
    return sorted(
        candidates,
        key=lambda row: rank_at_ballpark(row, ballpark_name) or 9999,
    )[:top]


def print_section(title, rows, ballpark_name):
    print(f"## {title}")
    print()
    if not rows:
        print("- n/a")
        print()
        return
    for row in rows:
        print("\n".join(explain_candidate(row, ballpark_name)))



def main():
    args = parse_args()
    ballpark_payload = load_json(args.ballpark_aware)
    defense_payload = load_json(args.defense_aware)

    hitters = joined_rows(ballpark_payload, defense_payload, "hitter")
    pitchers = joined_rows(ballpark_payload, defense_payload, "pitcher")

    top_hitter_value = top_overall(hitters, args.top, args.ballpark)
    hitter_card_anchors = premium_card_anchors(hitters, args.top, args.ballpark)
    hitter_low_cost = low_cost_value_candidates(hitters, args.top, args.ballpark)
    hitter_defensive_anchors = defensive_anchor_candidates(hitters, args.top, args.ballpark)
    hitter_positive_movers = park_movers(hitters, args.top, args.ballpark, "positive")
    hitter_negative_movers = park_movers(hitters, args.top, args.ballpark, "negative")
    hitter_role_representatives = role_representatives(hitters, "hitter", args.ballpark)

    top_pitcher_value = top_overall(pitchers, args.top, args.ballpark)
    pitcher_card_anchors = premium_card_anchors(pitchers, args.top, args.ballpark)
    starting_pitcher_targets = pitcher_role_candidates(pitchers, args.top, args.ballpark, "S")
    relief_pitcher_targets = pitcher_role_candidates(pitchers, args.top, args.ballpark, "R")
    pitcher_positive_movers = park_movers(pitchers, args.top, args.ballpark, "positive")
    pitcher_negative_movers = park_movers(pitchers, args.top, args.ballpark, "negative")
    pitcher_role_representatives = role_representatives(pitchers, "pitcher", args.ballpark)

    print("# BIE Draft Candidate Explanations v0")
    print()
    print(f"Season: {ballpark_payload.get('season')}")
    print(f"Ballpark context: {args.ballpark}")
    print(f"Hitters considered: {len(hitters)}")
    print(f"Pitchers considered: {len(pitchers)}")
    print()
    print("## Method")
    print()
    print(
        "Candidates are selected from the ballpark-aware draft signal and explained "
        "using joined defense-aware signal fields. This report is analytical only; "
        "it does not enforce roster construction, usage, league draft order, injuries, "
        "or platoon deployment."
    )
    print()
    print_section("Top Hitter Value Candidates", top_hitter_value, args.ballpark)
    print_section("Premium Hitter Card Anchors", hitter_card_anchors, args.ballpark)
    print_section("Low-Cost Hitter Role Players", hitter_low_cost, args.ballpark)
    print_section("Hitter Defensive Anchors", hitter_defensive_anchors, args.ballpark)
    print_section("Positive Comiskey Hitter Movers", hitter_positive_movers, args.ballpark)
    print_section("Negative Comiskey Hitter Movers", hitter_negative_movers, args.ballpark)
    print_section("Hitter Role Representatives", hitter_role_representatives, args.ballpark)

    print_section("Top Pitcher Value Candidates", top_pitcher_value, args.ballpark)
    print_section("Premium Pitcher Card Anchors", pitcher_card_anchors, args.ballpark)
    print_section("Starting Pitcher Targets", starting_pitcher_targets, args.ballpark)
    print_section("Relief Pitcher Targets", relief_pitcher_targets, args.ballpark)
    print_section("Positive Comiskey Pitcher Movers", pitcher_positive_movers, args.ballpark)
    print_section("Negative Comiskey Pitcher Movers", pitcher_negative_movers, args.ballpark)
    print_section("Pitcher Role Representatives", pitcher_role_representatives, args.ballpark)


if __name__ == "__main__":
    main()
