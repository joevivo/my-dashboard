import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"
CAP = 80.00

BASE = Path("data/baseball/parsed/strat365") / SEASON
IN_PATH = BASE / "draft-prep" / "1968.astrodome-roster-scenarios-v0.json"
OUT_DIR = BASE / "draft-prep"

OUT_JSON = OUT_DIR / "1968.astrodome-scenario-review-v0.json"
OUT_MD = OUT_DIR / "1968.astrodome-scenario-review-v0.md"


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


def tags_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [part.strip() for part in str(value).split(",") if part.strip()]


def has_tag(row, tag):
    return tag in tags_list(row.get("tags"))


def count_tag(rows, tag):
    return sum(1 for row in rows if has_tag(row, tag))


def salary_total(rows):
    return round2(sum(safe_float(r.get("salary")) for r in rows))


def scenario_bucket(total_salary):
    if total_salary < 65:
        return "underbuilt"
    if total_salary < 74:
        return "light_spend"
    if total_salary <= 80:
        return "viable_spend"
    return "over_cap"


def summarize_hitter_structure(hitters):
    starters = [h for h in hitters if str(h.get("reason", "")).startswith("scenario_core")]
    bench = [h for h in hitters if not str(h.get("reason", "")).startswith("scenario_core")]

    fallback = count_tag(hitters, "fallback_or_avoid")
    premium_risk = count_tag(hitters, "premium_position_range_risk")
    infield_risk = count_tag(hitters, "infield_range_risk")
    cheap_fit = count_tag(hitters, "cheap_fit")
    defensive_plus = count_tag(hitters, "defensive_plus")

    bench_salary = salary_total(bench)
    core_salary = salary_total(starters)

    bench_positions = {}
    for h in bench:
        pos = h.get("assignedPosition") or "UNK"
        bench_positions[pos] = bench_positions.get(pos, 0) + 1

    weak_core = [
        h for h in starters
        if has_tag(h, "fallback_or_avoid") or safe_float(h.get("fit")) < 75
    ]

    weak_bench = [
        h for h in bench
        if has_tag(h, "fallback_or_avoid") or safe_float(h.get("fit")) < 70
    ]

    return {
        "coreCount": len(starters),
        "benchCount": len(bench),
        "coreSalary": core_salary,
        "benchSalary": bench_salary,
        "fallbackCount": fallback,
        "premiumPositionRangeRiskCount": premium_risk,
        "infieldRangeRiskCount": infield_risk,
        "cheapFitCount": cheap_fit,
        "defensivePlusCount": defensive_plus,
        "benchPositions": bench_positions,
        "weakCorePlayers": [
            {
                "playerName": h.get("playerName"),
                "position": h.get("assignedPosition"),
                "salary": safe_float(h.get("salary")),
                "fit": safe_float(h.get("fit")),
                "tags": h.get("tags"),
            }
            for h in weak_core
        ],
        "weakBenchPlayers": [
            {
                "playerName": h.get("playerName"),
                "position": h.get("assignedPosition"),
                "salary": safe_float(h.get("salary")),
                "fit": safe_float(h.get("fit")),
                "tags": h.get("tags"),
            }
            for h in weak_bench
        ],
    }


def summarize_pitcher_structure(pitchers):
    fallback = count_tag(pitchers, "fallback_or_avoid")
    core_target = count_tag(pitchers, "core_target")
    target = count_tag(pitchers, "target")
    walk_risk = count_tag(pitchers, "walk_risk")
    strikeout_plus = count_tag(pitchers, "strikeout_plus")
    park_protected = count_tag(pitchers, "park_protected_hr_risk")

    cheap_pitchers = [p for p in pitchers if safe_float(p.get("salary")) <= 0.75]
    weak_pitchers = [
        p for p in pitchers
        if has_tag(p, "fallback_or_avoid") or safe_float(p.get("fit")) < 60
    ]

    preferred = [p for p in pitchers if p.get("reason") == "scenario_pitcher"]
    filler = [p for p in pitchers if p.get("reason") != "scenario_pitcher"]

    return {
        "preferredCount": len(preferred),
        "fillerCount": len(filler),
        "fallbackCount": fallback,
        "coreTargetCount": core_target,
        "targetCount": target,
        "walkRiskCount": walk_risk,
        "strikeoutPlusCount": strikeout_plus,
        "parkProtectedHrRiskCount": park_protected,
        "cheapPitcherCount": len(cheap_pitchers),
        "weakPitchers": [
            {
                "playerName": p.get("playerName"),
                "salary": safe_float(p.get("salary")),
                "endurance": p.get("endurance"),
                "fit": safe_float(p.get("fit")),
                "tags": p.get("tags"),
            }
            for p in weak_pitchers
        ],
    }


def identity_notes(scenario):
    label = scenario.get("label", "")
    hitters = scenario.get("hitters", [])
    pitchers = scenario.get("pitchers", [])

    notes = []

    names = {h.get("playerName") for h in hitters} | {p.get("playerName") for p in pitchers}
    salary = scenario.get("legality", {}).get("salary", {})
    total_salary = safe_float(salary.get("total"))
    remaining = safe_float(salary.get("remaining"))

    if label == "Balanced Astrodome":
        if total_salary >= 74 and 26 <= safe_float(salary.get("pitchers")) <= 38:
            notes.append("identity_supported: balanced spend profile")
        if "Tiant, Luis" in names and "Gibson, Bob" in names:
            notes.append("identity_supported: preserves premium starter pair")

    if label == "Premium CF / Defense":
        if "Mays, Willie" in names or "Flood, Curt" in names:
            notes.append("identity_supported: preserves premium CF concept")
        else:
            notes.append("identity_warning: premium CF concept not preserved")

    if label == "Premium Pitching":
        premium_pitchers = {"Tiant, Luis", "Gibson, Bob", "McNally, Dave", "Seaver, Tom", "McDaniel, Lindy"}
        retained = sorted(premium_pitchers.intersection(names))
        notes.append(f"premium_pitching_retained:{len(retained)}:{', '.join(retained)}")

    if label == "Value Defense":
        if total_salary < 65:
            notes.append("identity_warning: legal but economically underbuilt")
        if remaining >= 15:
            notes.append("identity_warning: too much cap left unused for draftable roster")

    if label == "OB / Low HR Dependency":
        ob_players = [h for h in hitters if has_tag(h, "ob_engine")]
        notes.append(f"ob_engine_count:{len(ob_players)}")

    return notes


def classify_scenario(scenario, hitter_summary, pitcher_summary):
    legal = scenario.get("legality", {})
    salary = legal.get("salary", {})
    total_salary = safe_float(salary.get("total"))
    remaining = safe_float(salary.get("remaining"))

    issues = []
    strengths = []

    if not legal.get("pass"):
        issues.append("illegal_roster")
    else:
        strengths.append("legal_roster")

    bucket = scenario_bucket(total_salary)
    if bucket == "underbuilt":
        issues.append("underbuilt_salary")
    elif bucket == "light_spend":
        issues.append("light_salary_usage")
    elif bucket == "viable_spend":
        strengths.append("viable_salary_usage")

    if remaining >= 8:
        issues.append("excess_cap_unused")
    elif remaining <= 3:
        strengths.append("efficient_cap_usage")

    if hitter_summary["fallbackCount"] >= 6:
        issues.append("too_many_fallback_hitters")
    if hitter_summary["premiumPositionRangeRiskCount"] >= 2:
        issues.append("premium_position_range_risk")
    if hitter_summary["benchSalary"] <= 4:
        issues.append("punt_bench")
    if len(hitter_summary["weakCorePlayers"]) > 0:
        issues.append("weak_core_hitter_slots")
    if hitter_summary["defensivePlusCount"] >= 7:
        strengths.append("strong_defensive_coverage")

    if pitcher_summary["fallbackCount"] >= 5:
        issues.append("too_many_fallback_pitchers")
    if pitcher_summary["cheapPitcherCount"] >= 4:
        issues.append("cheap_pitcher_filler_overload")
    if pitcher_summary["coreTargetCount"] >= 3:
        strengths.append("preserves_core_pitching")
    if pitcher_summary["strikeoutPlusCount"] >= 2:
        strengths.append("strikeout_staff_component")

    if not issues:
        recommendation = "review_first"
    elif "underbuilt_salary" in issues or "excess_cap_unused" in issues:
        recommendation = "needs_salary_reinvestment"
    elif "illegal_roster" in issues:
        recommendation = "do_not_use_until_repaired"
    else:
        recommendation = "review_with_cautions"

    return {
        "recommendation": recommendation,
        "strengths": strengths,
        "issues": issues,
    }


def review_scenario(scenario):
    hitters = scenario.get("hitters", [])
    pitchers = scenario.get("pitchers", [])

    hitter_summary = summarize_hitter_structure(hitters)
    pitcher_summary = summarize_pitcher_structure(pitchers)
    identity = identity_notes(scenario)
    classification = classify_scenario(scenario, hitter_summary, pitcher_summary)

    return {
        "key": scenario.get("key"),
        "label": scenario.get("label"),
        "legality": scenario.get("legality"),
        "scenarioScore": scenario.get("scenarioScore"),
        "identityNotes": identity,
        "hitterSummary": hitter_summary,
        "pitcherSummary": pitcher_summary,
        "classification": classification,
    }


def render_player_list(players):
    if not players:
        return "none"
    return "; ".join(
        f"{p.get('playerName')} ({p.get('position') or p.get('endurance')}, ${p.get('salary')}, fit {round2(p.get('fit'))})"
        for p in players[:8]
    )


def render_md(reviews):
    lines = []
    lines.append("# 1968 Astrodome Scenario Review v0")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append("- Sanity review for legal roster scenarios.")
    lines.append("- This report separates legal roster construction from draftable roster quality.")
    lines.append("- It is a draft-prep review, not an autonomous draft recommendation.")
    lines.append("")
    lines.append("## Scenario Review Summary")
    lines.append("")
    lines.append("| Scenario | Legal | Salary | Remaining | Recommendation | Issues | Strengths |")
    lines.append("|---|---:|---:|---:|---|---|---|")

    for r in reviews:
        legal = r["legality"]
        salary = legal["salary"]
        classification = r["classification"]
        issues = ", ".join(classification["issues"]) if classification["issues"] else "none"
        strengths = ", ".join(classification["strengths"]) if classification["strengths"] else "none"
        lines.append(
            f"| {r['label']} | {str(legal['pass']).upper()} | {salary['total']} | {salary['remaining']} "
            f"| {classification['recommendation']} | {issues} | {strengths} |"
        )

    lines.append("")
    lines.append("## Recommended Manual Review Order")
    lines.append("")

    order = sorted(
        reviews,
        key=lambda r: (
            0 if r["classification"]["recommendation"] == "review_first" else
            1 if r["classification"]["recommendation"] == "review_with_cautions" else
            2 if r["classification"]["recommendation"] == "needs_salary_reinvestment" else
            3,
            -safe_float(r.get("scenarioScore")),
        )
    )

    for idx, r in enumerate(order, start=1):
        lines.append(
            f"{idx}. **{r['label']}** - {r['classification']['recommendation']} "
            f"(score {round2(r.get('scenarioScore'))})"
        )

    for r in reviews:
        legal = r["legality"]
        salary = legal["salary"]
        hs = r["hitterSummary"]
        ps = r["pitcherSummary"]
        classification = r["classification"]

        lines.append("")
        lines.append(f"## {r['label']}")
        lines.append("")
        lines.append(f"- Recommendation: {classification['recommendation']}")
        lines.append(f"- Legal: {str(legal['pass']).upper()}")
        lines.append(f"- Salary: {salary['total']} / {CAP}; remaining {salary['remaining']}")
        lines.append(f"- Hitter salary: {salary['hitters']}; pitcher salary: {salary['pitchers']}")
        lines.append(f"- Issues: {', '.join(classification['issues']) if classification['issues'] else 'none'}")
        lines.append(f"- Strengths: {', '.join(classification['strengths']) if classification['strengths'] else 'none'}")
        if r["identityNotes"]:
            lines.append(f"- Identity notes: {'; '.join(r['identityNotes'])}")

        lines.append("")
        lines.append("### Hitter Read")
        lines.append("")
        lines.append(f"- Core hitters: {hs['coreCount']}; bench hitters: {hs['benchCount']}")
        lines.append(f"- Core salary: {hs['coreSalary']}; bench salary: {hs['benchSalary']}")
        lines.append(f"- Fallback hitters: {hs['fallbackCount']}")
        lines.append(f"- Premium-position range risks: {hs['premiumPositionRangeRiskCount']}")
        lines.append(f"- Defensive-plus hitters: {hs['defensivePlusCount']}")
        lines.append(f"- Bench positions: {hs['benchPositions']}")
        lines.append(f"- Weak core players: {render_player_list(hs['weakCorePlayers'])}")
        lines.append(f"- Weak bench players: {render_player_list(hs['weakBenchPlayers'])}")

        lines.append("")
        lines.append("### Pitcher Read")
        lines.append("")
        lines.append(f"- Preferred pitchers: {ps['preferredCount']}; filler pitchers: {ps['fillerCount']}")
        lines.append(f"- Core-target pitchers: {ps['coreTargetCount']}; target pitchers: {ps['targetCount']}")
        lines.append(f"- Fallback pitchers: {ps['fallbackCount']}")
        lines.append(f"- Cheap pitchers <= $0.75M: {ps['cheapPitcherCount']}")
        lines.append(f"- Strikeout-plus pitchers: {ps['strikeoutPlusCount']}")
        lines.append(f"- Walk-risk pitchers: {ps['walkRiskCount']}")
        lines.append(f"- Weak pitchers: {render_player_list(ps['weakPitchers'])}")

    return "\n".join(lines) + "\n"


def main():
    data = load_json(IN_PATH)
    scenarios = data.get("scenarios", [])

    reviews = [review_scenario(s) for s in scenarios]

    output = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "source": str(IN_PATH),
        "modelNotes": [
            "Scenario sanity review for legal roster scenarios.",
            "Separates legality from draftability.",
            "Draft-prep review, not autonomous drafting.",
        ],
        "reviews": reviews,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    OUT_MD.write_text(render_md(reviews), encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"SCENARIOS_REVIEWED: {len(reviews)}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print("RECOMMENDATION_SUMMARY:")
    for r in reviews:
        salary = r["legality"]["salary"]
        cls = r["classification"]
        print(
            f"  {r['key']} | recommendation={cls['recommendation']} | "
            f"salary={salary['total']} | remaining={salary['remaining']} | "
            f"issues={','.join(cls['issues']) if cls['issues'] else 'none'}"
        )


if __name__ == "__main__":
    main()

