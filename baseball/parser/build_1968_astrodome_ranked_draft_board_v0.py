import json
from pathlib import Path

SEASON = "1968"
PARK = "Astrodome 1968"

BASE = Path("data/baseball/parsed/strat365") / SEASON
DRAFT_PREP = BASE / "draft-prep"

FIT_PATH = DRAFT_PREP / "1968.astrodome-fit-and-pivots-v0.json"
REPORT_PATH = DRAFT_PREP / "1968.astrodome-draft-prep-report-v0.json"

OUT_JSON = DRAFT_PREP / "1968.astrodome-ranked-draft-board-v0.json"
OUT_MD = DRAFT_PREP / "1968.astrodome-ranked-draft-board-v0.md"

CORE_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]

PRIORITY_POSITIONS = {
    "C": 1.10,
    "SS": 1.12,
    "CF": 1.10,
    "3B": 1.04,
    "2B": 1.02,
    "RF": 1.00,
    "LF": 0.98,
    "1B": 0.94,
}

PITCHER_ROLE_BONUS = {
    "starter": 8.0,
    "reliever": 4.0,
    "closer_qualified": 5.0,
    "strikeout_plus": 4.0,
    "core_target": 7.0,
    "target": 3.0,
}

HITTER_TAG_BONUS = {
    "core_target": 8.0,
    "target": 4.0,
    "defensive_plus": 4.0,
    "ob_engine": 5.0,
    "cheap_fit": 2.0,
}

TAG_PENALTIES = {
    "fallback_or_avoid": -20.0,
    "premium_position_range_risk": -8.0,
    "infield_range_risk": -7.0,
    "salary_hr_dependency_risk": -4.0,
    "walk_risk": -5.0,
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


def player_key(row):
    return str(row.get("playerId") or row.get("playerName"))


def hitter_draft_role(row):
    pos = row.get("position")
    salary = safe_float(row.get("salary"))
    fit = safe_float(row.get("astrodomeFitScore"))
    tags = tags_list(row.get("tags"))

    if salary >= 7 and fit >= 105:
        return "anchor_target"
    if pos in {"C", "SS", "CF"} and fit >= 100 and "defensive_plus" in tags:
        return "priority_position_target"
    if salary <= 3 and fit >= 90:
        return "value_target"
    if "premium_position_range_risk" in tags or "infield_range_risk" in tags:
        return "risk_discount_target"
    return "role_target"


def hitter_score(row):
    pos = row.get("position")
    fit = safe_float(row.get("astrodomeFitScore"))
    salary = safe_float(row.get("salary"))
    efficiency = safe_float(row.get("salaryEfficiency"))
    tags = tags_list(row.get("tags"))
    role = hitter_draft_role(row)

    score = fit * PRIORITY_POSITIONS.get(pos, 1.0)

    # Salary efficiency matters, but should not turn backup-value profiles
    # into top-overall draft anchors.
    score += min(efficiency, 12.0) * 0.20

    for tag in tags:
        score += HITTER_TAG_BONUS.get(tag, 0.0)
        score += TAG_PENALTIES.get(tag, 0.0)

    if role == "anchor_target":
        score += 6.0
    if role == "priority_position_target":
        score += 3.0
    if role == "value_target":
        score += 1.0
    if role == "risk_discount_target":
        score -= 3.0

    if salary >= 10:
        score -= 2.0

    # Low-cost catchers are useful roster pieces, but should not outrank
    # true premium bats solely because C is scarce.
    if pos == "C" and salary < 3 and "ob_engine" not in tags:
        score -= 7.0

    return round2(score)


def pitcher_score(row):
    fit = safe_float(row.get("astrodomePitcherFitScore"))
    salary = safe_float(row.get("salary"))
    efficiency = safe_float(row.get("salaryEfficiency"))
    tags = tags_list(row.get("astrodomeTags"))

    score = fit
    score += min(efficiency, 20.0) * 0.30

    for tag in tags:
        score += PITCHER_ROLE_BONUS.get(tag, 0.0)
        score += TAG_PENALTIES.get(tag, 0.0)

    if salary >= 9:
        score -= 2.0
    if salary <= 3 and fit >= 90:
        score += 4.0

    return round2(score)


def board_tier(rank, score):
    if rank <= 8:
        return "Tier 1 - Core Draft Targets"
    if rank <= 20:
        return "Tier 2 - Strong Targets / Early Pivots"
    if rank <= 36:
        return "Tier 3 - Role Targets"
    if rank <= 60:
        return "Tier 4 - Depth / Contingency"
    return "Watch / Avoid"


def build_hitter_board(fit_data):
    pivots = fit_data.get("positionPivots", [])
    best_by_player = {}

    for row in pivots:
        if "fallback_or_avoid" in tags_list(row.get("tags")):
            continue

        key = player_key(row)
        score = hitter_score(row)
        candidate = dict(row)
        candidate["draftBoardScore"] = score
        candidate["draftRole"] = hitter_draft_role(row)

        current = best_by_player.get(key)
        if not current or score > current["draftBoardScore"]:
            best_by_player[key] = candidate

    rows = sorted(best_by_player.values(), key=lambda r: r["draftBoardScore"], reverse=True)

    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
        row["tier"] = board_tier(idx, row["draftBoardScore"])

    return rows


def build_pitcher_board(fit_data):
    pitchers = fit_data.get("topPitchers", [])
    rows = []

    for row in pitchers:
        if "fallback_or_avoid" in tags_list(row.get("astrodomeTags")):
            continue

        candidate = dict(row)
        candidate["draftBoardScore"] = pitcher_score(row)
        rows.append(candidate)

    rows = sorted(rows, key=lambda r: r["draftBoardScore"], reverse=True)

    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
        row["tier"] = board_tier(idx, row["draftBoardScore"])

    return rows


def build_position_boards(hitter_board):
    boards = {}
    for pos in CORE_POSITIONS:
        rows = [r for r in hitter_board if r.get("position") == pos]
        boards[pos] = rows[:8]
    return boards


def render_hitter_table(lines, rows, limit=None):
    lines.append("| Rank | Player | Pos | Role | Salary | Fit | Board | Defense | Tags |")
    lines.append("|---:|---|---|---|---:|---:|---:|---|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('rank')} | {r.get('playerName')} | {r.get('position')} "
            f"| {r.get('draftRole')} | {safe_float(r.get('salary'))} | {round2(r.get('astrodomeFitScore'))} "
            f"| {round2(r.get('draftBoardScore'))} | {r.get('rawDefense')} | {tags_text(r.get('tags'))} |"
        )


def render_pitcher_table(lines, rows, limit=None):
    lines.append("| Rank | Player | Salary | Endurance | Fit | Board | Tags |")
    lines.append("|---:|---|---:|---|---:|---:|---|")
    for r in rows[:limit] if limit else rows:
        lines.append(
            f"| {r.get('rank')} | {r.get('playerName')} | {safe_float(r.get('salary'))} "
            f"| {r.get('browserEndurance')} | {round2(r.get('astrodomePitcherFitScore'))} "
            f"| {round2(r.get('draftBoardScore'))} | {tags_text(r.get('astrodomeTags'))} |"
        )


def render_md(board):
    lines = []
    lines.append("# 1968 Astrodome Ranked Draft Board v0")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append("- Ranked manual draft board for the 1968 Astrodome scenario.")
    lines.append("- This is draft intelligence, not an autonomous drafter.")
    lines.append("- Scores combine Astrodome fit, positional scarcity, tags, salary efficiency, and role value.")
    lines.append("- Generated rankings are for manual review and should be adjusted during the actual draft.")
    lines.append("")

    lines.append("## Top Hitter Targets")
    lines.append("")
    render_hitter_table(lines, board["hitters"], limit=30)
    lines.append("")

    lines.append("## Top Pitcher Targets")
    lines.append("")
    render_pitcher_table(lines, board["pitchers"], limit=30)
    lines.append("")

    lines.append("## Position Boards")
    lines.append("")
    for pos in CORE_POSITIONS:
        lines.append(f"### {pos}")
        lines.append("")
        rows = board["positions"].get(pos, [])
        if not rows:
            lines.append("_No clean targets._")
            lines.append("")
            continue
        render_hitter_table(lines, rows)
        lines.append("")

    lines.append("## Draft Interpretation")
    lines.append("")
    lines.append("- Treat Premium Pitching as the first scenario to pressure-test.")
    lines.append("- Treat Balanced Astrodome as the fallback framework.")
    lines.append("- Do not blindly draft punt bench or filler pitchers from legal scenario output.")
    lines.append("- Preserve C / SS / CF / SP clarity early; solve bench late.")
    lines.append("- Use this board as a ranked target and pivot list, not as a fixed roster.")
    lines.append("")

    return "\n".join(lines)


def main():
    fit_data = load_json(FIT_PATH)
    report_data = load_json(REPORT_PATH)

    hitter_board = build_hitter_board(fit_data)
    pitcher_board = build_pitcher_board(fit_data)
    position_boards = build_position_boards(hitter_board)

    board = {
        "schemaVersion": "v0",
        "season": SEASON,
        "park": PARK,
        "sources": {
            "fit": str(FIT_PATH),
            "report": str(REPORT_PATH),
        },
        "modelNotes": [
            "Ranked manual draft board.",
            "Draft intelligence, not autonomous drafting.",
            "Generated outputs are ignored; commit this builder only.",
        ],
        "manualReviewOrder": report_data.get("manualReviewOrder", []),
        "hitters": hitter_board,
        "pitchers": pitcher_board,
        "positions": position_boards,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(board, f, indent=2)

    OUT_MD.write_text(render_md(board), encoding="utf-8")

    print("# RESULT SUMMARY")
    print("DRAFT_BOARD_BUILT: yes")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"MD_OUT: {OUT_MD}")
    print(f"HITTERS_RANKED: {len(hitter_board)}")
    print(f"PITCHERS_RANKED: {len(pitcher_board)}")
    print("TOP_10_HITTERS:")
    for r in hitter_board[:10]:
        print(
            f"  {r['rank']}. {r.get('playerName')} | {r.get('position')} | "
            f"salary={safe_float(r.get('salary'))} | board={r.get('draftBoardScore')} | tags={tags_text(r.get('tags'))}"
        )
    print("TOP_10_PITCHERS:")
    for r in pitcher_board[:10]:
        print(
            f"  {r['rank']}. {r.get('playerName')} | salary={safe_float(r.get('salary'))} | "
            f"endurance={r.get('browserEndurance')} | board={r.get('draftBoardScore')} | tags={tags_text(r.get('astrodomeTags'))}"
        )


if __name__ == "__main__":
    main()

