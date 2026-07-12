import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"

BASE = Path("data/baseball/parsed/strat365") / SEASON
DRAFT_PREP = BASE / "draft-prep"

INTERPRETATION_PATH = DRAFT_PREP / "1968.astrodome-manual-draft-interpretation-v0.json"

OUT_JSON = DRAFT_PREP / "1968.astrodome-draft-room-cheat-sheet-v0.json"
OUT_MD = DRAFT_PREP / "1968.astrodome-draft-room-cheat-sheet-v0.md"


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


def rows(report, group, bucket):
    return report.get(group, {}).get(bucket, [])


def take_names(items, limit=None):
    selected = items[:limit] if limit else items
    return [r.get("playerName") for r in selected]


def player_line(row, kind):
    if kind == "hitter":
        return (
            f"- **{row.get('playerName')}** ({row.get('position')}, ${safe_float(row.get('salary'))}M): "
            f"{row.get('manualRead')}"
        )

    return (
        f"- **{row.get('playerName')}** ({row.get('browserEndurance')}, ${safe_float(row.get('salary'))}M): "
        f"{row.get('manualRead')}"
    )


def by_position(items, position):
    return [r for r in items if r.get("position") == position]


def render_section(lines, title, items, kind, limit=None):
    lines.append(f"## {title}")
    lines.append("")
    selected = items[:limit] if limit else items
    if not selected:
        lines.append("_No players._")
        lines.append("")
        return

    for row in selected:
        lines.append(player_line(row, kind))
    lines.append("")


def render_md(sheet):
    lines = []
    lines.append("# 1968 Astrodome Draft-Room Cheat Sheet v0")
    lines.append("")
    lines.append("## Identity")
    lines.append("")
    lines.append("- Draft intelligence, not an autonomous drafter.")
    lines.append("- Astrodome identity: run prevention, OB pressure, up-the-middle defense, pitching depth, and selective premium bats.")
    lines.append("- Do not build around HR-only salary.")
    lines.append("- Do not let cheap legal roster filler drive draft strategy.")
    lines.append("")

    lines.append("## First Principles")
    lines.append("")
    lines.append("1. Solve CF intentionally. Do not treat a CF-4 bat as a clean CF solution.")
    lines.append("2. Solve SS intentionally. Maxvill/Aparicio/Fregosi/Alley are the main planned paths.")
    lines.append("3. Build around real starter depth, not just legal starter count.")
    lines.append("4. Draft high-leverage relief deliberately. Do not back into cheap bullpen filler.")
    lines.append("5. Treat value pieces as late structure support, not as the foundation.")
    lines.append("")

    render_section(lines, "Hitter A-List", sheet["hitterAList"], "hitter")
    render_section(lines, "Hitter A-List With Review", sheet["hitterReviewList"], "hitter")
    render_section(lines, "Pitcher A-List", sheet["pitcherAList"], "pitcher")
    render_section(lines, "Pitcher A-List With Review", sheet["pitcherReviewList"], "pitcher")

    lines.append("## Clean CF Paths")
    lines.append("")
    for row in sheet["cleanCfPaths"]:
        lines.append(player_line(row, "hitter"))
    lines.append("")

    lines.append("## SS Plans")
    lines.append("")
    for row in sheet["ssPlans"]:
        lines.append(player_line(row, "hitter"))
    lines.append("")

    lines.append("## Catcher Plans")
    lines.append("")
    for row in sheet["catcherPlans"]:
        lines.append(player_line(row, "hitter"))
    lines.append("")

    lines.append("## Late Value / Contingency")
    lines.append("")
    lines.append("### Hitters")
    lines.append("")
    for row in sheet["hitterValue"][:12]:
        lines.append(player_line(row, "hitter"))
    lines.append("")
    lines.append("### Pitchers")
    lines.append("")
    for row in sheet["pitcherValue"][:12]:
        lines.append(player_line(row, "pitcher"))
    lines.append("")

    lines.append("## Watch / Avoid")
    lines.append("")
    lines.append("### Hitters")
    lines.append("")
    for row in sheet["hitterWatch"][:14]:
        lines.append(player_line(row, "hitter"))
    lines.append("")
    lines.append("### Pitchers")
    lines.append("")
    for row in sheet["pitcherWatch"][:10]:
        lines.append(player_line(row, "pitcher"))
    lines.append("")

    lines.append("## Draft Posture")
    lines.append("")
    lines.append("- Early: prioritize Tiant/Gibson, clean CF, Freehan, Kaline/Rose/Alou/Flood, or high-leverage RP.")
    lines.append("- Middle: lock SS, C2, bullpen leverage, and fifth usable starter.")
    lines.append("- Late: use value targets only after the roster structure is solved.")
    lines.append("- If the board collapses, preserve defense and pitcher flexibility before chasing corner bats.")
    lines.append("")

    return "\n".join(lines)


def main():
    interpretation = load_json(INTERPRETATION_PATH)

    hitter_a = rows(interpretation, "hitterBuckets", "A-list")
    hitter_review = rows(interpretation, "hitterBuckets", "A-list with review")
    hitter_b = rows(interpretation, "hitterBuckets", "B-list")
    hitter_c = rows(interpretation, "hitterBuckets", "C-list")
    hitter_watch = rows(interpretation, "hitterBuckets", "Watch/Avoid")

    pitcher_a = rows(interpretation, "pitcherBuckets", "A-list")
    pitcher_review = rows(interpretation, "pitcherBuckets", "A-list with review")
    pitcher_b = rows(interpretation, "pitcherBuckets", "B-list")
    pitcher_c = rows(interpretation, "pitcherBuckets", "C-list")
    pitcher_watch = rows(interpretation, "pitcherBuckets", "Watch/Avoid")

    clean_cf = [
        r for r in hitter_a + hitter_review + hitter_b + hitter_c
        if r.get("position") == "CF" and "CF-4" not in str(r.get("rawDefense")).upper()
    ]

    ss_plans = [
        r for r in hitter_review + hitter_b + hitter_c
        if r.get("position") == "SS"
    ]

    catcher_plans = [
        r for r in hitter_a + hitter_review + hitter_b + hitter_c
        if r.get("position") == "C"
    ]

    hitter_value = [
        r for r in hitter_c
        if r.get("draftRole") == "value_target" or safe_float(r.get("salary")) <= 2.5
    ]

    pitcher_value = [
        r for r in pitcher_b + pitcher_c
        if safe_float(r.get("salary")) <= 2.0 or "closer-qualified" in str(r.get("manualRead"))
    ]

    sheet = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "sources": {
            "manualInterpretation": str(INTERPRETATION_PATH),
        },
        "hitterAList": hitter_a,
        "hitterReviewList": hitter_review,
        "pitcherAList": pitcher_a,
        "pitcherReviewList": pitcher_review,
        "cleanCfPaths": clean_cf,
        "ssPlans": ss_plans,
        "catcherPlans": catcher_plans,
        "hitterValue": hitter_value,
        "pitcherValue": pitcher_value,
        "hitterWatch": hitter_watch,
        "pitcherWatch": pitcher_watch,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2)

    OUT_MD.write_text(render_md(sheet), encoding="utf-8")

    print("# RESULT SUMMARY")
    print("CHEAT_SHEET_BUILT: yes")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print(f"HITTER_A_LIST: {len(hitter_a)}")
    print(f"HITTER_REVIEW_LIST: {len(hitter_review)}")
    print(f"PITCHER_A_LIST: {len(pitcher_a)}")
    print(f"PITCHER_REVIEW_LIST: {len(pitcher_review)}")
    print(f"CLEAN_CF_PATHS: {len(clean_cf)}")
    print(f"SS_PLANS: {len(ss_plans)}")
    print(f"CATCHER_PLANS: {len(catcher_plans)}")


if __name__ == "__main__":
    main()
