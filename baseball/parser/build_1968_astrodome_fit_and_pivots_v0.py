import csv
import json
from pathlib import Path

SEASON = "1968"
BASE = Path("data/baseball/parsed/strat365") / SEASON

HITTER_MECH = BASE / "card-mechanics" / "1968.hitter-card-mechanics-v0.json"
PITCHER_MECH = BASE / "card-mechanics" / "1968.pitcher-card-mechanics-v0.json"
DEFENSE = BASE / "defense" / "1968.hitter-defense-assignments-v0.json"

OUT_DIR = BASE / "draft-prep"
OUT_JSON = OUT_DIR / "1968.astrodome-fit-and-pivots-v0.json"
OUT_HITTER_MD = OUT_DIR / "1968.astrodome-hitter-fit-v0.md"
OUT_PITCHER_MD = OUT_DIR / "1968.astrodome-pitcher-fit-v0.md"
OUT_PIVOT_MD = OUT_DIR / "1968.astrodome-position-pivot-board-v0.md"
OUT_CSV = OUT_DIR / "1968.astrodome-position-pivot-board-v0.csv"

PIVOT_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]

POSITION_DEFENSE_WEIGHT = {
    "C": 1.25,
    "SS": 1.25,
    "CF": 1.15,
    "2B": 1.05,
    "3B": 1.00,
    "RF": 0.85,
    "LF": 0.80,
    "1B": 0.70,
}

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

def safe_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def round2(value):
    return round(float(value or 0.0), 2)

def round4(value):
    return round(float(value or 0.0), 4)

def salary_value(score, salary):
    s = safe_float(salary)
    if s <= 0:
        return 0.0
    return score / s

def assignment_key(player_id, position):
    return f"{player_id}|{position}"

def defense_points(position, assignment):
    if not assignment:
        return 0.0

    rng = safe_int(assignment.get("range"))
    err = safe_int(assignment.get("error"))
    arm = safe_int(assignment.get("arm"), 0)
    catcher_t = safe_int(assignment.get("catcherThrowing"))
    pb = safe_int(assignment.get("passedBall"))

    if rng is None or err is None:
        return 0.0

    # Range should dominate. A range-4 player with a low error rating
    # should not look like a premium defender at SS/CF/3B.
    range_score_map = {
        1: 85,
        2: 65,
        3: 38,
        4: 12,
        5: 0,
    }
    range_score = range_score_map.get(rng, 0)

    # Error is meaningful, but capped so it cannot rescue poor range.
    error_score = max(0, min(18, (35 - err) * 0.65))

    arm_score = 0
    if position in ["LF", "CF", "RF"]:
        # Negative OF arms are good; positive arms are bad.
        arm_score = max(-10, min(10, -arm * 2.5))
    elif position == "C":
        # Negative catcher arm is good. T/PB matter but should not swamp range.
        arm_score = max(-12, min(12, -arm * 3))
        if catcher_t is not None:
            arm_score += max(0, min(8, (20 - catcher_t) * 0.25))
        if pb is not None:
            arm_score += max(0, min(6, (20 - pb) * 0.18))

    weight = POSITION_DEFENSE_WEIGHT.get(position, 1.0)
    return round2((range_score + error_score + arm_score) * weight)

def hitter_fit_score(h, assignment=None, position=None):
    ob = safe_float(h.get("weightedOB"))
    hit = safe_float(h.get("weightedHit"))
    bb = safe_float(h.get("weightedBB"))
    non_hr_hit = safe_float(h.get("nonHRHit"))
    xbh = safe_float(h.get("weightedXBH"))
    hr = safe_float(h.get("weightedHR"))
    bp_hr = safe_float(h.get("ballparkHRCheck"))
    bp_si = safe_float(h.get("ballparkSingleCheck"))
    gb = safe_float(h.get("weightedGB"))
    k = safe_float(h.get("weightedK"))
    salary = safe_float(h.get("salary"))

    defense = defense_points(position, assignment) if assignment and position else 0.0

    # Astrodome hitter model v0:
    # Reward OB, walks, non-HR hits, useful XBH, low K, defense.
    # Penalize HR dependence, heavy BP-HR dependence, weak premium defense, salary drag.
    score = 0.0
    score += ob * 180
    score += bb * 75
    score += non_hr_hit * 90
    score += xbh * 40
    score += bp_si * 20
    score += defense * 0.32
    score -= hr * 35
    score -= bp_hr * 65
    score -= k * 35
    score -= salary * 3.0

    if gb > 0.42:
        score -= (gb - 0.42) * 35

    return round2(score)

def pitcher_fit_score(p):
    oba = safe_float(p.get("weightedOnBaseAllowed"))
    hit = safe_float(p.get("weightedHitAllowed"))
    hr = safe_float(p.get("weightedHRAllowed"))
    bb = safe_float(p.get("weightedWalkAllowed"))
    k = safe_float(p.get("weightedStrikeout"))
    bp_hr = safe_float(p.get("ballparkHRCheckAllowed"))
    bp_si = safe_float(p.get("ballparkSingleCheckAllowed"))
    xbh = safe_float(p.get("weightedXBHAllowed"))
    defense_delegation = safe_float(p.get("defenseDelegation"))
    pitcher_field = safe_int(p.get("pitcherFieldingRating"), 3)
    pitcher_error = safe_int(p.get("pitcherError"), 20)
    salary = safe_float(p.get("salary"))

    starter = safe_int(p.get("starterEndurance"), 0) or 0
    relief = safe_int(p.get("reliefEndurance"), 0) or 0
    closer = safe_int(p.get("closerEndurance"), 0) or 0

    score = 100
    score -= oba * 220
    score -= hit * 100
    score -= bb * 85
    score -= hr * 45       # Astrodome softens HR risk.
    score -= xbh * 55
    score += k * 90
    score += bp_hr * 35    # HR park can protect BP-HR checks.
    score -= bp_si * 25
    score += defense_delegation * 25
    score += max(0, 6 - pitcher_field) * 3
    score += max(0, 35 - pitcher_error) * 0.12
    score += starter * 1.75
    score += relief * 1.2
    score += closer * 1.0
    score -= salary * 2.0

    return round2(score)

def classify_hitter(h, score, assignment=None, position=None):
    salary = safe_float(h.get("salary"))
    ob = safe_float(h.get("weightedOB"))
    bp_hr = safe_float(h.get("ballparkHRCheck"))
    hr = safe_float(h.get("weightedHR"))
    defense = defense_points(position, assignment) if assignment and position else 0
    rng = safe_int(assignment.get("range")) if assignment else None

    flags = []

    if score >= 115:
        flags.append("core_target")
    elif score >= 95:
        flags.append("target")
    elif score >= 80:
        flags.append("usable")
    else:
        flags.append("fallback_or_avoid")

    if salary >= 8 and bp_hr >= 0.05:
        flags.append("salary_hr_dependency_risk")
    if defense >= 65:
        flags.append("defensive_plus")
    if position in ["C", "SS", "CF"] and rng is not None and rng >= 4:
        flags.append("premium_position_range_risk")
    if position in ["2B", "3B"] and rng is not None and rng >= 4:
        flags.append("infield_range_risk")
    if ob >= 0.40:
        flags.append("ob_engine")
    if hr >= 0.075 and bp_hr >= 0.05:
        flags.append("power_muted_by_park")
    if salary <= 2 and score >= 80:
        flags.append("cheap_fit")

    return ", ".join(flags)

def classify_pitcher(p, score):
    flags = []

    if score >= 95:
        flags.append("core_target")
    elif score >= 75:
        flags.append("target")
    elif score >= 60:
        flags.append("usable")
    else:
        flags.append("fallback_or_avoid")

    if safe_int(p.get("starterEndurance"), 0):
        flags.append("starter")
    if safe_int(p.get("reliefEndurance"), 0):
        flags.append("reliever")
    if safe_int(p.get("closerEndurance"), 0):
        flags.append("closer_qualified")
    if safe_float(p.get("ballparkHRCheckAllowed")) > 0.015:
        flags.append("park_protected_hr_risk")
    if safe_float(p.get("weightedWalkAllowed")) > 0.08:
        flags.append("walk_risk")
    if safe_float(p.get("weightedStrikeout")) > 0.28:
        flags.append("strikeout_plus")

    return ", ".join(flags)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    hitter_data = load_json(HITTER_MECH)
    pitcher_data = load_json(PITCHER_MECH)
    defense_data = load_json(DEFENSE)

    defense_by_player = {}
    defense_by_player_position = {}

    for row in defense_data.get("players", []):
        pid = str(row.get("playerId"))
        defense_by_player[pid] = row
        for a in row.get("assignments", []):
            pos = a.get("position")
            if pos:
                defense_by_player_position[assignment_key(pid, pos)] = a

    hitter_rows = []
    for h in hitter_data.get("hitters", []):
        pid = str(h.get("playerId"))
        primary = h.get("primaryPosition")
        primary_assignment = defense_by_player_position.get(assignment_key(pid, primary))

        best_position = primary
        best_assignment = primary_assignment
        best_def = defense_points(primary, primary_assignment) if primary_assignment else 0

        for pos in PIVOT_POSITIONS:
            a = defense_by_player_position.get(assignment_key(pid, pos))
            d = defense_points(pos, a) if a else 0
            if d > best_def:
                best_def = d
                best_position = pos
                best_assignment = a

        score = hitter_fit_score(h, primary_assignment, primary)
        best_position_score = hitter_fit_score(h, best_assignment, best_position) if best_assignment else score

        row = dict(h)
        row["primaryAstrodomeFitScore"] = score
        row["bestDefensivePosition"] = best_position
        row["bestDefensePoints"] = round2(best_def)
        row["bestPositionAstrodomeFitScore"] = best_position_score
        row["salaryEfficiency"] = round2(salary_value(best_position_score, h.get("salary")))
        row["astrodomeTags"] = classify_hitter(h, best_position_score, best_assignment, best_position)
        hitter_rows.append(row)

    hitter_rows.sort(key=lambda r: (-safe_float(r.get("bestPositionAstrodomeFitScore")), safe_float(r.get("salary"))))

    pitcher_rows = []
    for p in pitcher_data.get("pitchers", []):
        score = pitcher_fit_score(p)
        row = dict(p)
        row["astrodomePitcherFitScore"] = score
        row["salaryEfficiency"] = round2(salary_value(score, p.get("salary")))
        row["astrodomeTags"] = classify_pitcher(p, score)
        pitcher_rows.append(row)

    pitcher_rows.sort(key=lambda r: (-safe_float(r.get("astrodomePitcherFitScore")), safe_float(r.get("salary"))))

    pivot_rows = []
    for pos in PIVOT_POSITIONS:
        for h in hitter_data.get("hitters", []):
            pid = str(h.get("playerId"))
            assignment = defense_by_player_position.get(assignment_key(pid, pos))
            if not assignment:
                continue

            score = hitter_fit_score(h, assignment, pos)
            def_pts = defense_points(pos, assignment)
            row = {
                "position": pos,
                "playerId": h.get("playerId"),
                "playerName": h.get("playerName"),
                "team": h.get("team"),
                "salary": h.get("salary"),
                "bats": h.get("bats"),
                "balance": h.get("balance"),
                "rawDefense": assignment.get("rawAssignment"),
                "defensePoints": def_pts,
                "weightedOB": h.get("weightedOB"),
                "weightedHit": h.get("weightedHit"),
                "weightedBB": h.get("weightedBB"),
                "weightedHR": h.get("weightedHR"),
                "weightedK": h.get("weightedK"),
                "ballparkHRCheck": h.get("ballparkHRCheck"),
                "nonHRHit": h.get("nonHRHit"),
                "astrodomeFitScore": score,
                "salaryEfficiency": round2(salary_value(score, h.get("salary"))),
                "tags": classify_hitter(h, score, assignment, pos),
            }
            pivot_rows.append(row)

    pivot_rows.sort(key=lambda r: (r["position"], -safe_float(r["astrodomeFitScore"]), safe_float(r["salary"])))

    output = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": "Astrodome 1968",
        "modelNotes": [
            "Astrodome fit v0 is an explainable heuristic, not a simulation.",
            "Rewards OB, walks, non-HR hits, defense, strikeout pitching, and park-protected HR risk for pitchers.",
            "Penalizes hitter HR dependency, weak premium defense, high salary drag, pitcher walks, and XBH allowed.",
        ],
        "counts": {
            "hitters": len(hitter_rows),
            "pitchers": len(pitcher_rows),
            "pivotRows": len(pivot_rows),
        },
        "topHitters": hitter_rows[:60],
        "topPitchers": pitcher_rows[:60],
        "positionPivots": pivot_rows,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "position", "playerName", "team", "salary", "rawDefense",
            "defensePoints", "weightedOB", "weightedHit", "weightedBB",
            "weightedHR", "weightedK", "ballparkHRCheck", "nonHRHit",
            "astrodomeFitScore", "salaryEfficiency", "tags",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in pivot_rows:
            writer.writerow({field: r.get(field) for field in fields})

    hitter_lines = []
    hitter_lines.append("# 1968 Astrodome Hitter Fit v0")
    hitter_lines.append("")
    hitter_lines.append("## Model Notes")
    hitter_lines.append("")
    hitter_lines.append("- Explainable heuristic, not a simulation.")
    hitter_lines.append("- Rewards OB, walks, non-HR hits, low strikeouts, and defense.")
    hitter_lines.append("- Penalizes high salary and HR/ballpark-HR dependency.")
    hitter_lines.append("")
    hitter_lines.append("## Top Hitter Fits")
    hitter_lines.append("")
    hitter_lines.append("| Rank | Player | Pos | Best Def Pos | Salary | Fit | Eff | OB | BB | HR | BP HR | Defense | Tags |")
    hitter_lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for i, r in enumerate(hitter_rows[:40], 1):
        hitter_lines.append(
            f"| {i} | {r.get('playerName')} | {r.get('primaryPosition')} | {r.get('bestDefensivePosition')} "
            f"| {r.get('salary')} | {r.get('bestPositionAstrodomeFitScore')} | {r.get('salaryEfficiency')} "
            f"| {r.get('weightedOB')} | {r.get('weightedBB')} | {r.get('weightedHR')} "
            f"| {r.get('ballparkHRCheck')} | {r.get('bestDefensePoints')} | {r.get('astrodomeTags')} |"
        )
    OUT_HITTER_MD.write_text("\n".join(hitter_lines) + "\n", encoding="utf-8")

    pitcher_lines = []
    pitcher_lines.append("# 1968 Astrodome Pitcher Fit v0")
    pitcher_lines.append("")
    pitcher_lines.append("## Model Notes")
    pitcher_lines.append("")
    pitcher_lines.append("- Explainable heuristic, not a simulation.")
    pitcher_lines.append("- Rewards low on-base allowed, strikeouts, endurance, pitcher fielding, and HR risk protected by Astrodome.")
    pitcher_lines.append("- Penalizes walks, XBH allowed, and salary drag.")
    pitcher_lines.append("")
    pitcher_lines.append("## Top Pitcher Fits")
    pitcher_lines.append("")
    pitcher_lines.append("| Rank | Player | Salary | Endurance | Fit | Eff | OBA | Hit | BB | HR | K | BP HR | P Field | Tags |")
    pitcher_lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for i, r in enumerate(pitcher_rows[:40], 1):
        pitcher_lines.append(
            f"| {i} | {r.get('playerName')} | {r.get('salary')} | {r.get('browserEndurance')} "
            f"| {r.get('astrodomePitcherFitScore')} | {r.get('salaryEfficiency')} "
            f"| {r.get('weightedOnBaseAllowed')} | {r.get('weightedHitAllowed')} "
            f"| {r.get('weightedWalkAllowed')} | {r.get('weightedHRAllowed')} "
            f"| {r.get('weightedStrikeout')} | {r.get('ballparkHRCheckAllowed')} "
            f"| {r.get('pitcherFieldingText')}/{r.get('pitcherErrorText')} | {r.get('astrodomeTags')} |"
        )
    OUT_PITCHER_MD.write_text("\n".join(pitcher_lines) + "\n", encoding="utf-8")

    pivot_lines = []
    pivot_lines.append("# 1968 Astrodome Position Pivot Board v0")
    pivot_lines.append("")
    pivot_lines.append("## Model Notes")
    pivot_lines.append("")
    pivot_lines.append("- Position-specific board from card-backed hitters only.")
    pivot_lines.append("- Fit score combines card outcomes, salary, and normalized defense at that position.")
    pivot_lines.append("")
    for pos in PIVOT_POSITIONS:
        pivot_lines.append(f"## {pos}")
        pivot_lines.append("")
        pivot_lines.append("| Rank | Player | Salary | Defense | Def Pts | Fit | Eff | OB | BB | HR | BP HR | Tags |")
        pivot_lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|")
        pos_rows = [r for r in pivot_rows if r["position"] == pos][:15]
        for i, r in enumerate(pos_rows, 1):
            pivot_lines.append(
                f"| {i} | {r.get('playerName')} | {r.get('salary')} | {r.get('rawDefense')} "
                f"| {r.get('defensePoints')} | {r.get('astrodomeFitScore')} | {r.get('salaryEfficiency')} "
                f"| {r.get('weightedOB')} | {r.get('weightedBB')} | {r.get('weightedHR')} "
                f"| {r.get('ballparkHRCheck')} | {r.get('tags')} |"
            )
        pivot_lines.append("")
    OUT_PIVOT_MD.write_text("\n".join(pivot_lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"HITTERS_SCORED: {len(hitter_rows)}")
    print(f"PITCHERS_SCORED: {len(pitcher_rows)}")
    print(f"PIVOT_ROWS: {len(pivot_rows)}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"HITTER_MD_OUT: {OUT_HITTER_MD}")
    print(f"PITCHER_MD_OUT: {OUT_PITCHER_MD}")
    print(f"PIVOT_MD_OUT: {OUT_PIVOT_MD}")
    print(f"PIVOT_CSV_OUT: {OUT_CSV}")
    print("TOP_10_HITTER_FITS:")
    for i, r in enumerate(hitter_rows[:10], 1):
        print(f"  {i}. {r.get('playerName')} | fit={r.get('bestPositionAstrodomeFitScore')} | salary={r.get('salary')} | tags={r.get('astrodomeTags')}")
    print("TOP_10_PITCHER_FITS:")
    for i, r in enumerate(pitcher_rows[:10], 1):
        print(f"  {i}. {r.get('playerName')} | fit={r.get('astrodomePitcherFitScore')} | salary={r.get('salary')} | tags={r.get('astrodomeTags')}")

if __name__ == "__main__":
    main()


