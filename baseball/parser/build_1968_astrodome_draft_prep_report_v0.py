import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"
CAP = 80.00

BASE = Path("data/baseball/parsed/strat365") / SEASON
DRAFT_PREP = BASE / "draft-prep"

FIT_PATH = DRAFT_PREP / "1968.astrodome-fit-and-pivots-v0.json"
SCENARIOS_PATH = DRAFT_PREP / "1968.astrodome-roster-scenarios-v0.json"
REVIEW_PATH = DRAFT_PREP / "1968.astrodome-scenario-review-v0.json"

OUT_JSON = DRAFT_PREP / "1968.astrodome-draft-prep-report-v0.json"
OUT_MD = DRAFT_PREP / "1968.astrodome-draft-prep-report-v0.md"

CORE_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]


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


def round2(value):
    return round(float(value or 0.0), 2)


def tags_text(value):
    if not value:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def top_items(rows, score_field, limit=12):
    return sorted(rows, key=lambda r: safe_float(r.get(score_field)), reverse=True)[:limit]


def position_pivots(rows, limit_per_position=8):
    out = {}
    for pos in CORE_POSITIONS:
        candidates = [r for r in rows if r.get("position") == pos]
        out[pos] = sorted(
            candidates,
            key=lambda r: (
                safe_float(r.get("astrodomeFitScore")),
                safe_float(r.get("salaryEfficiency")),
                -safe_float(r.get("salary")),
            ),
            reverse=True,
        )[:limit_per_position]
    return out


def scenario_review_by_key(review_data):
    return {r.get("key"): r for r in review_data.get("reviews", [])}


def manual_review_order(reviews):
    order_rank = {
        "review_first": 0,
        "review_with_cautions": 1,
        "needs_salary_reinvestment": 2,
        "do_not_use_until_repaired": 3,
    }

    return sorted(
        reviews,
        key=lambda r: (
            order_rank.get(r.get("classification", {}).get("recommendation"), 99),
            -safe_float(r.get("scenarioScore")),
        ),
    )


def collect_cautions(reviews):
    cautions = []
    for r in reviews:
        label = r.get("label")
        issues = r.get("classification", {}).get("issues", [])
        salary = r.get("legality", {}).get("salary", {})
        if issues:
            cautions.append({
                "scenario": label,
                "recommendation": r.get("classification", {}).get("recommendation"),
                "salary": salary.get("total"),
                "remaining": salary.get("remaining"),
                "issues": issues,
            })
    return cautions


def enrich_hitter_target(row, pivots):
    name = row.get("playerName")
    player_pivots = [p for p in pivots if p.get("playerName") == name]

    if not player_pivots:
        return row

    best_pivot = sorted(
        player_pivots,
        key=lambda p: safe_float(p.get("astrodomeFitScore")),
        reverse=True,
    )[0]

    enriched = dict(row)
    enriched["bestPosition"] = enriched.get("bestPosition") or best_pivot.get("position")
    enriched["bestDefense"] = enriched.get("bestDefense") or best_pivot.get("rawDefense")
    enriched["tags"] = enriched.get("tags") or best_pivot.get("tags")
    enriched["bestPositionAstrodomeFitScore"] = (
        enriched.get("bestPositionAstrodomeFitScore")
        or best_pivot.get("astrodomeFitScore")
    )
    return enriched


def first_pass_targets(fit_data):
    hitters = fit_data.get("topHitters", [])
    pitchers = fit_data.get("topPitchers", [])
    pivots = fit_data.get("positionPivots", [])

    enriched_hitters = [enrich_hitter_target(h, pivots) for h in hitters]

    hitter_targets = [
        h for h in top_items(enriched_hitters, "bestPositionAstrodomeFitScore", 30)
        if "fallback_or_avoid" not in tags_text(h.get("tags"))
    ][:12]

    pitcher_targets = [
        p for p in top_items(pitchers, "astrodomePitcherFitScore", 30)
        if "fallback_or_avoid" not in tags_text(p.get("astrodomeTags"))
    ][:12]

    pivot_targets = {}
    for pos, rows in position_pivots(pivots, 8).items():
        pivot_targets[pos] = [
            r for r in rows
            if "fallback_or_avoid" not in tags_text(r.get("tags"))
        ][:5]

    return {
        "hitters": hitter_targets,
        "pitchers": pitcher_targets,
        "positionPivots": pivot_targets,
    }


def render_hitter_table(lines, rows, score_field, limit=None):
    lines.append("| Player | Pos | Salary | Fit | Defense | Tags |")
    lines.append("|---|---|---:|---:|---|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('playerName')} | {r.get('bestPosition') or r.get('position')} "
            f"| {safe_float(r.get('salary'))} | {round2(r.get(score_field))} "
            f"| {r.get('bestDefense') or r.get('rawDefense')} | {tags_text(r.get('tags'))} |"
        )


def render_pitcher_table(lines, rows, limit=None):
    lines.append("| Player | Salary | Endurance | Fit | Tags |")
    lines.append("|---|---:|---|---:|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('playerName')} | {safe_float(r.get('salary'))} | {r.get('browserEndurance')} "
            f"| {round2(r.get('astrodomePitcherFitScore'))} | {tags_text(r.get('astrodomeTags'))} |"
        )


def render_scenario_summary(lines, scenarios, reviews_by_key):
    lines.append("| Scenario | Legal | Salary | Remaining | Recommendation | Key Issues |")
    lines.append("|---|---:|---:|---:|---|---|")

    for s in scenarios:
        review = reviews_by_key.get(s.get("key"), {})
        legal = s.get("legality", {})
        salary = legal.get("salary", {})
        classification = review.get("classification", {})
        issues = classification.get("issues", [])
        lines.append(
            f"| {s.get('label')} | {str(legal.get('pass')).upper()} | {salary.get('total')} "
            f"| {salary.get('remaining')} | {classification.get('recommendation')} "
            f"| {', '.join(issues) if issues else 'none'} |"
        )


def render_md(report):
    lines = []
    lines.append("# 1968 Astrodome Draft Prep Report v0")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append("- Consolidated draft-prep report for the 1968 Strat-O-Matic 365 Astrodome scenario.")
    lines.append("- This is draft intelligence, not an autonomous drafter.")
    lines.append("- Generated rosters and targets are starting points for manual review.")
    lines.append("- Legal roster construction is necessary but not sufficient for draftability.")
    lines.append("")

    lines.append("## Executive Read")
    lines.append("")
    lines.append("- **Best starting scenario:** Premium Pitching.")
    lines.append("- **Best balanced follow-up:** Balanced Astrodome.")
    lines.append("- **Needs reinvestment:** Value Defense and OB / Low HR Dependency.")
    lines.append("- **Main model debt:** punt bench, fallback filler, and cheap pitcher overload.")
    lines.append("")

    lines.append("## Manual Review Order")
    lines.append("")
    for idx, r in enumerate(report["manualReviewOrder"], start=1):
        cls = r.get("classification", {})
        lines.append(
            f"{idx}. **{r.get('label')}** - {cls.get('recommendation')} "
            f"(score {round2(r.get('scenarioScore'))})"
        )
    lines.append("")

    lines.append("## Scenario Summary")
    lines.append("")
    render_scenario_summary(lines, report["scenarios"], report["reviewsByKey"])
    lines.append("")

    lines.append("## First-Pass Hitter Targets")
    lines.append("")
    render_hitter_table(lines, report["targets"]["hitters"], "bestPositionAstrodomeFitScore", limit=12)
    lines.append("")

    lines.append("## First-Pass Pitcher Targets")
    lines.append("")
    render_pitcher_table(lines, report["targets"]["pitchers"], limit=12)
    lines.append("")

    lines.append("## Position Pivot Board")
    lines.append("")
    for pos in CORE_POSITIONS:
        lines.append(f"### {pos}")
        lines.append("")
        rows = report["targets"]["positionPivots"].get(pos, [])
        if not rows:
            lines.append("_No clean pivot targets found._")
            lines.append("")
            continue
        render_hitter_table(lines, rows, "astrodomeFitScore")
        lines.append("")

    lines.append("## Cautions")
    lines.append("")
    for c in report["cautions"]:
        lines.append(
            f"- **{c['scenario']}**: {c['recommendation']}; salary {c['salary']}; "
            f"remaining {c['remaining']}; issues: {', '.join(c['issues'])}"
        )
    lines.append("")

    lines.append("## Next Manual Review Questions")
    lines.append("")
    lines.append("1. Is Premium Pitching actually draftable after replacing punt bench pieces?")
    lines.append("2. Can Balanced Astrodome preserve Tiant/Gibson while upgrading bench and RF?")
    lines.append("3. Does Premium CF / Defense justify Mays/Flood-style spend in Astrodome?")
    lines.append("4. Which cheap pitchers are real role players versus filler artifacts?")
    lines.append("5. Which fallback hitters should become hard avoids in the next model pass?")
    lines.append("")

    return "\n".join(lines)


def main():
    fit_data = load_json(FIT_PATH)
    scenario_data = load_json(SCENARIOS_PATH)
    review_data = load_json(REVIEW_PATH)

    reviews = review_data.get("reviews", [])
    reviews_by_key = scenario_review_by_key(review_data)
    targets = first_pass_targets(fit_data)

    report = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "cap": CAP,
        "sources": {
            "fit": str(FIT_PATH),
            "scenarios": str(SCENARIOS_PATH),
            "review": str(REVIEW_PATH),
        },
        "modelNotes": [
            "Consolidated draft-prep report.",
            "Draft intelligence, not autonomous drafting.",
            "Generated outputs are ignored; commit this builder only.",
        ],
        "manualReviewOrder": manual_review_order(reviews),
        "scenarios": scenario_data.get("scenarios", []),
        "reviewsByKey": reviews_by_key,
        "targets": targets,
        "cautions": collect_cautions(reviews),
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    OUT_MD.write_text(render_md(report), encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"REPORT_BUILT: yes")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print("MANUAL_REVIEW_ORDER:")
    for idx, r in enumerate(report["manualReviewOrder"], start=1):
        cls = r.get("classification", {})
        print(f"  {idx}. {r.get('label')} | {cls.get('recommendation')} | score={round2(r.get('scenarioScore'))}")
    print(f"HITTER_TARGETS: {len(report['targets']['hitters'])}")
    print(f"PITCHER_TARGETS: {len(report['targets']['pitchers'])}")


if __name__ == "__main__":
    main()

