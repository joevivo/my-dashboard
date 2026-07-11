import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"

BASE = Path("data/baseball/parsed/strat365") / SEASON
DRAFT_PREP = BASE / "draft-prep"

BOARD_PATH = DRAFT_PREP / "1968.astrodome-ranked-draft-board-v0.json"

OUT_JSON = DRAFT_PREP / "1968.astrodome-manual-draft-interpretation-v0.json"
OUT_MD = DRAFT_PREP / "1968.astrodome-manual-draft-interpretation-v0.md"

HARD_WATCH_TAGS = {
    "premium_position_range_risk",
    "infield_range_risk",
    "walk_risk",
    "salary_hr_dependency_risk",
}

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


def tags_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def tags_text(value):
    return ", ".join(tags_list(value))


def risk_tags(row, tag_field):
    tags = set(tags_list(row.get(tag_field)))
    return sorted(tags.intersection(HARD_WATCH_TAGS))


def hitter_bucket(row):
    rank = int(row.get("rank") or 999)
    role = row.get("draftRole")
    pos = row.get("position")
    score = safe_float(row.get("draftBoardScore"))
    risks = risk_tags(row, "tags")

    if rank <= 10 and role == "anchor_target" and not risks:
        return "A-list"
    if rank <= 12 and role in {"anchor_target", "priority_position_target"}:
        return "A-list with review"
    if pos in {"C", "SS", "CF"} and rank <= 20:
        return "B-list"
    if rank <= 30 and role in {"value_target", "role_target", "priority_position_target"}:
        return "C-list"
    if risks or score < 95:
        return "Watch/Avoid"
    return "C-list"


def pitcher_bucket(row):
    rank = int(row.get("rank") or 999)
    score = safe_float(row.get("draftBoardScore"))
    tags = set(tags_list(row.get("astrodomeTags")))
    risks = risk_tags(row, "astrodomeTags")

    if rank <= 7 and "core_target" in tags and not risks:
        return "A-list"
    if rank <= 10 and "core_target" in tags:
        return "A-list with review"
    if rank <= 18 and ("starter" in tags or "closer_qualified" in tags):
        return "B-list"
    if rank <= 30:
        return "C-list"
    if risks or score < 85:
        return "Watch/Avoid"
    return "C-list"


def add_hitter_read(row):
    risks = risk_tags(row, "tags")
    notes = []

    if row.get("draftRole") == "anchor_target":
        notes.append("premium target")
    if row.get("position") in {"C", "SS", "CF"}:
        notes.append("priority position")
    if "ob_engine" in tags_list(row.get("tags")):
        notes.append("OB engine")
    if "defensive_plus" in tags_list(row.get("tags")):
        notes.append("defensive fit")
    if "cheap_fit" in tags_list(row.get("tags")):
        notes.append("value fit")
    if risks:
        notes.append("review risk: " + ", ".join(risks))

    enriched = dict(row)
    enriched["manualBucket"] = hitter_bucket(row)
    enriched["manualRead"] = "; ".join(notes) if notes else "role fit"
    enriched["riskTags"] = risks
    return enriched


def add_pitcher_read(row):
    tags = tags_list(row.get("astrodomeTags"))
    risks = risk_tags(row, "astrodomeTags")
    notes = []

    if "starter" in tags:
        notes.append("starter target")
    if "reliever" in tags:
        notes.append("relief-capable")
    if "closer_qualified" in tags:
        notes.append("closer-qualified")
    if "strikeout_plus" in tags:
        notes.append("strikeout plus")
    if "park_protected_hr_risk" in tags:
        notes.append("Astrodome may protect HR risk")
    if risks:
        notes.append("review risk: " + ", ".join(risks))

    enriched = dict(row)
    enriched["manualBucket"] = pitcher_bucket(row)
    enriched["manualRead"] = "; ".join(notes) if notes else "role fit"
    enriched["riskTags"] = risks
    return enriched


def group_by_bucket(rows):
    buckets = {
        "A-list": [],
        "A-list with review": [],
        "B-list": [],
        "C-list": [],
        "Watch/Avoid": [],
    }

    for row in rows:
        buckets.setdefault(row["manualBucket"], []).append(row)

    return buckets


def render_hitter_table(lines, rows, limit=None):
    lines.append("| Rank | Player | Pos | Role | Salary | Board | Defense | Read |")
    lines.append("|---:|---|---|---|---:|---:|---|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('rank')} | {r.get('playerName')} | {r.get('position')} | {r.get('draftRole')} "
            f"| {safe_float(r.get('salary'))} | {round2(r.get('draftBoardScore'))} "
            f"| {r.get('rawDefense')} | {r.get('manualRead')} |"
        )


def render_pitcher_table(lines, rows, limit=None):
    lines.append("| Rank | Player | Salary | Endurance | Board | Read |")
    lines.append("|---:|---|---:|---|---:|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('rank')} | {r.get('playerName')} | {safe_float(r.get('salary'))} "
            f"| {r.get('browserEndurance')} | {round2(r.get('draftBoardScore'))} | {r.get('manualRead')} |"
        )


def render_md(report):
    lines = []
    lines.append("# 1968 Astrodome Manual Draft Interpretation v0")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append("- Manual interpretation layer over the ranked draft board.")
    lines.append("- This is draft intelligence, not an autonomous drafter.")
    lines.append("- Buckets separate true draft priority from value, contingency, and risk.")
    lines.append("- Use this as a draft-room guide, not as a fixed roster.")
    lines.append("")

    lines.append("## Strategic Read")
    lines.append("")
    lines.append("- Build from premium pitching plus up-the-middle defense.")
    lines.append("- Do not let cheap legal roster filler drive the draft.")
    lines.append("- Treat C, SS, CF, SP, and high-leverage RP as early clarity positions.")
    lines.append("- Astrodome suppresses HR, so OB, defense, contact pressure, and pitching depth matter more than pure HR salary.")
    lines.append("")

    lines.append("## Hitter Buckets")
    lines.append("")
    for bucket in ["A-list", "A-list with review", "B-list", "C-list", "Watch/Avoid"]:
        lines.append(f"### {bucket}")
        lines.append("")
        rows = report["hitterBuckets"].get(bucket, [])
        if not rows:
            lines.append("_No players._")
            lines.append("")
            continue
        render_hitter_table(lines, rows, limit=20)
        lines.append("")

    lines.append("## Pitcher Buckets")
    lines.append("")
    for bucket in ["A-list", "A-list with review", "B-list", "C-list", "Watch/Avoid"]:
        lines.append(f"### {bucket}")
        lines.append("")
        rows = report["pitcherBuckets"].get(bucket, [])
        if not rows:
            lines.append("_No players._")
            lines.append("")
            continue
        render_pitcher_table(lines, rows, limit=20)
        lines.append("")

    lines.append("## Draft-Room Rules")
    lines.append("")
    lines.append("1. Do not draft a CF-4 as the clean CF solution without manual review.")
    lines.append("2. Do not let backup-catcher value replace premium catcher evaluation.")
    lines.append("3. Preserve at least one real SS plan before chasing corner bats.")
    lines.append("4. Prefer pitchers with starter/reliever or closer-qualified flexibility when prices are close.")
    lines.append("5. Treat low-cost filler as late-draft contingency, not strategy.")
    lines.append("")

    return "\n".join(lines)


def main():
    board = load_json(BOARD_PATH)

    hitters = [add_hitter_read(r) for r in board.get("hitters", [])]
    pitchers = [add_pitcher_read(r) for r in board.get("pitchers", [])]

    report = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "sources": {
            "rankedBoard": str(BOARD_PATH),
        },
        "modelNotes": [
            "Manual interpretation layer.",
            "Draft intelligence, not autonomous drafting.",
            "Generated outputs are ignored; commit this builder only.",
        ],
        "hitterBuckets": group_by_bucket(hitters),
        "pitcherBuckets": group_by_bucket(pitchers),
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    OUT_MD.write_text(render_md(report), encoding="utf-8")

    print("# RESULT SUMMARY")
    print("MANUAL_INTERPRETATION_BUILT: yes")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print("HITTER_BUCKET_COUNTS:")
    for bucket, rows in report["hitterBuckets"].items():
        print(f"  {bucket}: {len(rows)}")
    print("PITCHER_BUCKET_COUNTS:")
    for bucket, rows in report["pitcherBuckets"].items():
        print(f"  {bucket}: {len(rows)}")


if __name__ == "__main__":
    main()
