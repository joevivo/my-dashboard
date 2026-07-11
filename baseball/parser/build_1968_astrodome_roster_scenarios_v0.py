import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"
CAP = 80.00

BASE = Path("data/baseball/parsed/strat365") / SEASON
FIT_PATH = BASE / "draft-prep" / "1968.astrodome-fit-and-pivots-v0.json"
OUT_DIR = BASE / "draft-prep"

OUT_JSON = OUT_DIR / "1968.astrodome-roster-scenarios-v0.json"
OUT_MD = OUT_DIR / "1968.astrodome-roster-scenarios-v0.md"

ROSTER_SIZE = 25
HITTER_COUNT = 14
PITCHER_COUNT = 11

MIN_CATCHERS = 2
MIN_STARTERS = 5
MIN_RELIEVERS = 4
MIN_CLOSERS = 1

CORE_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]

SCENARIOS = [
    {
        "key": "balanced_astrodome",
        "label": "Balanced Astrodome",
        "hitter_budget": 44.0,
        "core": {
            "C": ["Freehan, Bill", "Corrales, Pat"],
            "1B": ["Parker, Wes", "McCovey, Willie", "Mantle, Mickey"],
            "2B": ["McAuliffe, Dick", "Alley, Gene"],
            "3B": ["Santo, Ron", "Boyer, Clete", "Foy, Joe"],
            "SS": ["Maxvill, Dal", "Aparicio, Luis", "Alley, Gene"],
            "LF": ["Kaline, Al", "Mota, Manny", "Gonzalez, Tony"],
            "CF": ["Flood, Curt", "Mota, Manny", "Unser, Del"],
            "RF": ["Rettenmund, Merv", "Kaline, Al", "Morton, Bubba"],
        },
        "pitchers": ["Tiant, Luis", "Gibson, Bob", "McDaniel, Lindy", "Hoerner, Joe"],
    },
    {
        "key": "premium_cf_defense",
        "label": "Premium CF / Defense",
        "hitter_budget": 48.0,
        "core": {
            "C": ["Freehan, Bill", "Corrales, Pat"],
            "1B": ["Parker, Wes", "Mantle, Mickey"],
            "2B": ["Alley, Gene", "McAuliffe, Dick"],
            "3B": ["Santo, Ron", "Boyer, Clete"],
            "SS": ["Maxvill, Dal", "Aparicio, Luis", "Belanger, Mark"],
            "LF": ["Kaline, Al", "Mota, Manny"],
            "CF": ["Mays, Willie", "Flood, Curt", "Stanley, Mickey"],
            "RF": ["Rose, Pete", "Kaline, Al", "Morton, Bubba"],
        },
        "pitchers": ["Tiant, Luis", "Gibson, Bob", "McDaniel, Lindy"],
    },
    {
        "key": "premium_pitching",
        "label": "Premium Pitching",
        "hitter_budget": 38.0,
        "core": {
            "C": ["Corrales, Pat", "Freehan, Bill"],
            "1B": ["Parker, Wes", "Stahl, Larry", "Mantle, Mickey"],
            "2B": ["Alley, Gene", "McAuliffe, Dick"],
            "3B": ["Boyer, Clete", "Foy, Joe", "Santo, Ron"],
            "SS": ["Maxvill, Dal", "Belanger, Mark", "Kessinger, Don"],
            "LF": ["Mota, Manny", "Gonzalez, Tony"],
            "CF": ["Flood, Curt", "Mota, Manny", "Unser, Del"],
            "RF": ["Kaline, Al", "Morton, Bubba", "Alou, Jesus"],
        },
        "pitchers": ["Tiant, Luis", "Gibson, Bob", "McNally, Dave", "Seaver, Tom", "McDaniel, Lindy"],
    },
    {
        "key": "value_defense",
        "label": "Value Defense",
        "hitter_budget": 36.0,
        "core": {
            "C": ["Corrales, Pat", "Etchebarren, Andy"],
            "1B": ["Parker, Wes", "Stahl, Larry"],
            "2B": ["Alley, Gene", "Woodward, Woody"],
            "3B": ["Boyer, Clete", "Woodward, Woody"],
            "SS": ["Maxvill, Dal", "Belanger, Mark", "Kessinger, Don"],
            "LF": ["Mota, Manny", "Gonzalez, Tony"],
            "CF": ["Mota, Manny", "Unser, Del", "Blair, Paul"],
            "RF": ["Alou, Jesus", "Morton, Bubba", "Kaline, Al"],
        },
        "pitchers": ["McDaniel, Lindy", "Hoerner, Joe", "Wilhelm, Hoyt", "Hamilton, Steve", "Tiant, Luis"],
    },
    {
        "key": "ob_low_hr_dependency",
        "label": "OB / Low HR Dependency",
        "hitter_budget": 45.0,
        "core": {
            "C": ["Corrales, Pat", "Freehan, Bill"],
            "1B": ["Mantle, Mickey", "Parker, Wes"],
            "2B": ["McAuliffe, Dick", "Alley, Gene"],
            "3B": ["Foy, Joe", "Santo, Ron", "Boyer, Clete"],
            "SS": ["Maxvill, Dal", "Fregosi, Jim", "Campaneris, Bert"],
            "LF": ["Rettenmund, Merv", "Kaline, Al", "Mota, Manny"],
            "CF": ["Flood, Curt", "Monday, Rick", "Mota, Manny"],
            "RF": ["Rettenmund, Merv", "Kaline, Al", "Robinson, Frank"],
        },
        "pitchers": ["McDaniel, Lindy", "Hoerner, Joe", "Hamilton, Steve", "Tiant, Luis"],
    },
]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def round2(value):
    return round(float(value or 0.0), 2)


def player_key(row):
    return str(row.get("playerId") or row.get("playerName"))


def make_indexes(pivots, pitchers):
    by_pos_name = {}
    by_pos = {}
    for row in pivots:
        pos = row.get("position")
        name = row.get("playerName")
        by_pos_name[(pos, name)] = row
        by_pos.setdefault(pos, []).append(row)

    pitcher_by_name = {p.get("playerName"): p for p in pitchers}
    return by_pos_name, by_pos, pitcher_by_name


def roster_init(scenario):
    return {
        "key": scenario["key"],
        "label": scenario["label"],
        "salary": 0.0,
        "hitterSalary": 0.0,
        "pitcherSalary": 0.0,
        "hitters": [],
        "pitchers": [],
        "selectedIds": set(),
        "notes": [],
    }


def can_add(roster, row):
    return round2(roster["salary"] + safe_float(row.get("salary"))) <= CAP


def add_hitter(roster, row, pos, reason):
    key = player_key(row)
    if key in roster["selectedIds"]:
        return False
    if not can_add(roster, row):
        return False

    salary = safe_float(row.get("salary"))
    roster["hitters"].append({
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "assignedPosition": pos,
        "salary": salary,
        "fit": safe_float(row.get("astrodomeFitScore")),
        "efficiency": safe_float(row.get("salaryEfficiency")),
        "rawDefense": row.get("rawDefense"),
        "tags": row.get("tags"),
        "reason": reason,
    })
    roster["selectedIds"].add(key)
    roster["salary"] += salary
    roster["hitterSalary"] += salary
    return True


def add_pitcher(roster, row, reason):
    key = player_key(row)
    if key in roster["selectedIds"]:
        return False
    if not can_add(roster, row):
        return False

    salary = safe_float(row.get("salary"))
    roster["pitchers"].append({
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "salary": salary,
        "endurance": row.get("browserEndurance"),
        "starterEndurance": row.get("starterEndurance"),
        "reliefEndurance": row.get("reliefEndurance"),
        "closerEndurance": row.get("closerEndurance"),
        "fit": safe_float(row.get("astrodomePitcherFitScore")),
        "efficiency": safe_float(row.get("salaryEfficiency")),
        "tags": row.get("astrodomeTags"),
        "reason": reason,
    })
    roster["selectedIds"].add(key)
    roster["salary"] += salary
    roster["pitcherSalary"] += salary
    return True


def hitter_rank(row):
    return (
        safe_float(row.get("astrodomeFitScore")),
        safe_float(row.get("salaryEfficiency")),
        -safe_float(row.get("salary")),
    )


def pitcher_rank(row):
    return (
        safe_float(row.get("astrodomePitcherFitScore")),
        safe_float(row.get("salaryEfficiency")),
        -safe_float(row.get("salary")),
    )


def cheap_hitter_rank(row):
    return (
        safe_float(row.get("salary")),
        -safe_float(row.get("astrodomeFitScore")),
    )


def cheap_pitcher_rank(row):
    return (
        safe_float(row.get("salary")),
        -safe_float(row.get("astrodomePitcherFitScore")),
    )


def count_pos(roster, pos):
    return sum(1 for h in roster["hitters"] if h["assignedPosition"] == pos)


def starter_count(roster):
    return sum(1 for p in roster["pitchers"] if safe_int(p.get("starterEndurance")) > 0)


def reliever_count(roster):
    return sum(1 for p in roster["pitchers"] if safe_int(p.get("reliefEndurance")) > 0)


def closer_count(roster):
    return sum(1 for p in roster["pitchers"] if safe_int(p.get("closerEndurance")) > 0)


def pick_core_hitters(roster, scenario, by_pos_name, by_pos):
    for pos in CORE_POSITIONS:
        added = False

        for name in scenario["core"].get(pos, []):
            row = by_pos_name.get((pos, name))
            if row and roster["hitterSalary"] + safe_float(row.get("salary")) <= scenario["hitter_budget"]:
                if add_hitter(roster, row, pos, f"scenario_core_{pos}"):
                    added = True
                    break

        if added:
            continue

        candidates = sorted(by_pos.get(pos, []), key=cheap_hitter_rank)
        for row in candidates:
            if add_hitter(roster, row, pos, f"cheap_required_{pos}"):
                added = True
                break

        if not added:
            roster["notes"].append(f"missing_core_position:{pos}")


def fill_second_catcher(roster, by_pos):
    if count_pos(roster, "C") >= MIN_CATCHERS:
        return

    candidates = sorted(by_pos.get("C", []), key=cheap_hitter_rank)
    for row in candidates:
        if add_hitter(roster, row, "C", "second_catcher_requirement"):
            return


def fill_hitter_bench(roster, pivots):
    # Bench should be cheap, but not a pile of one position.
    # First pass: try to add useful coverage across C/IF/OF.
    desired_bench_positions = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]

    for pos in desired_bench_positions:
        if len(roster["hitters"]) >= HITTER_COUNT:
            return

        # Skip positions already carrying multiple bodies, except catcher.
        current = count_pos(roster, pos)
        if pos != "C" and current >= 2:
            continue
        if pos == "C" and current >= 3:
            continue

        candidates = sorted(
            [r for r in pivots if r.get("position") == pos],
            key=lambda r: (
                safe_float(r.get("salary")),
                -safe_float(r.get("salaryEfficiency")),
                -safe_float(r.get("astrodomeFitScore")),
            )
        )

        for row in candidates:
            if add_hitter(roster, row, pos, "bench_position_coverage"):
                break

    # Second pass: fill remaining slots by cheap value, but cap position pileups.
    candidates = sorted(
        pivots,
        key=lambda r: (
            safe_float(r.get("salary")),
            -safe_float(r.get("salaryEfficiency")),
            -safe_float(r.get("astrodomeFitScore")),
        )
    )

    for row in candidates:
        if len(roster["hitters"]) >= HITTER_COUNT:
            return

        pos = row.get("position")
        if pos and count_pos(roster, pos) >= 3:
            continue

        add_hitter(roster, row, pos, "bench_min_cost")


def fill_preferred_pitchers(roster, scenario, pitcher_by_name):
    for name in scenario.get("pitchers", []):
        if len(roster["pitchers"]) >= PITCHER_COUNT:
            return
        row = pitcher_by_name.get(name)
        if row:
            add_pitcher(roster, row, "scenario_pitcher")


def fill_pitcher_requirement(roster, pitchers, predicate, reason):
    candidates = sorted([p for p in pitchers if predicate(p)], key=cheap_pitcher_rank)

    for row in candidates:
        if len(roster["pitchers"]) >= PITCHER_COUNT:
            return
        if add_pitcher(roster, row, reason):
            if reason == "starter_requirement" and starter_count(roster) >= MIN_STARTERS:
                return
            if reason == "reliever_requirement" and reliever_count(roster) >= MIN_RELIEVERS:
                return
            if reason == "closer_requirement" and closer_count(roster) >= MIN_CLOSERS:
                return


def fill_pitcher_depth(roster, pitchers):
    candidates = sorted(
        pitchers,
        key=lambda p: (
            safe_float(p.get("salary")),
            -safe_float(p.get("salaryEfficiency")),
            -safe_float(p.get("astrodomePitcherFitScore")),
        )
    )

    for row in candidates:
        if len(roster["pitchers"]) >= PITCHER_COUNT:
            return
        add_pitcher(roster, row, "pitcher_min_cost_depth")


def legality(roster):
    assigned = {h["assignedPosition"] for h in roster["hitters"]}
    missing_positions = [p for p in CORE_POSITIONS if p not in assigned]

    checks = {
        "rosterSize": len(roster["hitters"]) + len(roster["pitchers"]) == ROSTER_SIZE,
        "hitterCount": len(roster["hitters"]) == HITTER_COUNT,
        "pitcherCount": len(roster["pitchers"]) == PITCHER_COUNT,
        "salaryCap": round2(roster["salary"]) <= CAP,
        "catchers": count_pos(roster, "C") >= MIN_CATCHERS,
        "starters": starter_count(roster) >= MIN_STARTERS,
        "relievers": reliever_count(roster) >= MIN_RELIEVERS,
        "closers": closer_count(roster) >= MIN_CLOSERS,
        "corePositionsCovered": len(missing_positions) == 0,
    }

    return {
        "pass": all(checks.values()),
        "checks": checks,
        "missingPositions": missing_positions,
        "counts": {
            "rosterSize": len(roster["hitters"]) + len(roster["pitchers"]),
            "hitters": len(roster["hitters"]),
            "pitchers": len(roster["pitchers"]),
            "catchers": count_pos(roster, "C"),
            "starters": starter_count(roster),
            "relievers": reliever_count(roster),
            "closers": closer_count(roster),
        },
        "salary": {
            "total": round2(roster["salary"]),
            "hitters": round2(roster["hitterSalary"]),
            "pitchers": round2(roster["pitcherSalary"]),
            "remaining": round2(CAP - roster["salary"]),
        },
    }


def scenario_score(roster):
    return round2(
        sum(safe_float(h.get("fit")) for h in roster["hitters"])
        + sum(safe_float(p.get("fit")) for p in roster["pitchers"])
    )


def build_scenario(scenario, pivots, pitchers):
    by_pos_name, by_pos, pitcher_by_name = make_indexes(pivots, pitchers)
    roster = roster_init(scenario)

    pick_core_hitters(roster, scenario, by_pos_name, by_pos)
    fill_second_catcher(roster, by_pos)
    fill_hitter_bench(roster, pivots)

    fill_preferred_pitchers(roster, scenario, pitcher_by_name)
    fill_pitcher_requirement(roster, pitchers, lambda p: safe_int(p.get("starterEndurance")) > 0, "starter_requirement")
    fill_pitcher_requirement(roster, pitchers, lambda p: safe_int(p.get("reliefEndurance")) > 0, "reliever_requirement")
    fill_pitcher_requirement(roster, pitchers, lambda p: safe_int(p.get("closerEndurance")) > 0, "closer_requirement")
    fill_pitcher_depth(roster, pitchers)

    roster["selectedIds"] = sorted(roster["selectedIds"])
    roster["legality"] = legality(roster)
    roster["scenarioScore"] = scenario_score(roster)

    return roster


def render_md(scenarios):
    lines = []
    lines.append("# 1968 Astrodome Roster Scenarios v0")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append("- Draft-prep scenario generator, not an autonomous drafter.")
    lines.append("- Legal-first v0: hitters are filled before pitchers to preserve roster structure.")
    lines.append("- Generated rosters are starting points for review, not final recommendations.")
    lines.append("")
    lines.append("## Scenario Summary")
    lines.append("")
    lines.append("| Scenario | Legal | Salary | Hitters | Pitchers | C | SP | RP | CL | Score | Notes |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")

    for s in scenarios:
        legal = s["legality"]
        counts = legal["counts"]
        salary = legal["salary"]
        failed = [k for k, v in legal["checks"].items() if not v]
        notes = "PASS" if legal["pass"] else "FAIL: " + ", ".join(failed)
        lines.append(
            f"| {s['label']} | {str(legal['pass']).upper()} | {salary['total']} "
            f"| {counts['hitters']} | {counts['pitchers']} | {counts['catchers']} "
            f"| {counts['starters']} | {counts['relievers']} | {counts['closers']} "
            f"| {s['scenarioScore']} | {notes} |"
        )

    for s in scenarios:
        legal = s["legality"]
        lines.append("")
        lines.append(f"## {s['label']}")
        lines.append("")
        lines.append(f"- Legal: {str(legal['pass']).upper()}")
        lines.append(f"- Salary: {legal['salary']['total']} / {CAP}")
        lines.append(f"- Hitter salary: {legal['salary']['hitters']}")
        lines.append(f"- Pitcher salary: {legal['salary']['pitchers']}")
        lines.append(f"- Remaining: {legal['salary']['remaining']}")
        lines.append(f"- Scenario score: {s['scenarioScore']}")
        if legal["missingPositions"]:
            lines.append(f"- Missing positions: {', '.join(legal['missingPositions'])}")
        if s.get("notes"):
            lines.append(f"- Notes: {'; '.join(s['notes'])}")

        lines.append("")
        lines.append("### Hitters")
        lines.append("")
        lines.append("| Pos | Player | Salary | Fit | Defense | Tags | Reason |")
        lines.append("|---|---|---:|---:|---|---|---|")
        for h in sorted(s["hitters"], key=lambda r: CORE_POSITIONS.index(r["assignedPosition"]) if r["assignedPosition"] in CORE_POSITIONS else 99):
            lines.append(
                f"| {h['assignedPosition']} | {h['playerName']} | {h['salary']} | {round2(h['fit'])} "
                f"| {h.get('rawDefense')} | {h.get('tags')} | {h.get('reason')} |"
            )

        lines.append("")
        lines.append("### Pitchers")
        lines.append("")
        lines.append("| Player | Salary | Endurance | Fit | Tags | Reason |")
        lines.append("|---|---:|---|---:|---|---|")
        for p in s["pitchers"]:
            lines.append(
                f"| {p['playerName']} | {p['salary']} | {p.get('endurance')} | {round2(p['fit'])} "
                f"| {p.get('tags')} | {p.get('reason')} |"
            )

    return "\n".join(lines) + "\n"


def main():
    data = load_json(FIT_PATH)
    pivots = data.get("positionPivots", [])
    pitchers = data.get("topPitchers", [])

    scenarios = [build_scenario(s, pivots, pitchers) for s in SCENARIOS]

    output = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "cap": CAP,
        "modelNotes": [
            "Draft-prep scenario generator, not an autonomous drafter.",
            "Legal-first v0 fills hitters before pitchers.",
            "Generated outputs are ignored; commit this builder only.",
        ],
        "scenarios": scenarios,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    OUT_MD.write_text(render_md(scenarios), encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"SCENARIOS_BUILT: {len(scenarios)}")
    print(f"LEGAL_SCENARIOS: {sum(1 for s in scenarios if s['legality']['pass'])}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print("SCENARIO_SUMMARY:")
    for s in scenarios:
        legal = s["legality"]
        counts = legal["counts"]
        salary = legal["salary"]
        print(
            f"  {s['key']} | legal={legal['pass']} | "
            f"salary={salary['total']} | hitters={counts['hitters']} | pitchers={counts['pitchers']} | "
            f"C={counts['catchers']} | SP={counts['starters']} | RP={counts['relievers']} | CL={counts['closers']} | "
            f"score={s['scenarioScore']}"
        )


if __name__ == "__main__":
    main()

