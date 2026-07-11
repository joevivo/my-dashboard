import csv
import json
import re
from pathlib import Path

SEASON = "1968"
BASE = Path("data/baseball/parsed/strat365") / SEASON
CARDS_DIR = BASE / "cards"
OUT_DIR = BASE / "defense"

OUT_JSON = OUT_DIR / "1968.hitter-defense-assignments-v0.json"
OUT_CSV = OUT_DIR / "1968.hitter-defense-assignments-v0.csv"
OUT_MD = OUT_DIR / "1968.hitter-defense-assignments-v0.md"

POSITION_RE = re.compile(
    r"\b(?P<pos>1b|2b|3b|ss|lf|cf|rf|c|p)-"
    r"(?P<range>\d)"
    r"(?:\((?P<arm>[+-]?\d+)\))?"
    r"e(?P<error>\d+)"
    r"(?:,T-(?P<t>\d+)\(pb-(?P<pb>\d+)\))?",
    re.IGNORECASE,
)

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def parse_assignments(defense_text: str):
    assignments = []
    for m in POSITION_RE.finditer(defense_text or ""):
        pos = m.group("pos").upper()
        assignments.append({
            "position": pos,
            "range": int(m.group("range")),
            "arm": int(m.group("arm")) if m.group("arm") is not None else None,
            "error": int(m.group("error")),
            "catcherThrowing": int(m.group("t")) if m.group("t") is not None else None,
            "passedBall": int(m.group("pb")) if m.group("pb") is not None else None,
            "rawAssignment": m.group(0),
        })
    return assignments

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    warnings = []

    for path in sorted(CARDS_DIR.glob("*.parsed-card-evidence.json")):
        data = load_json(path)

        if data.get("role") != "hitter":
            continue

        player = data.get("player", {})
        traits = data.get("hitterTraits", {}) or {}
        defense_text = traits.get("defenseText") or ""

        assignments = parse_assignments(defense_text)

        if defense_text and not assignments:
            warnings.append({
                "playerId": player.get("playerId"),
                "playerName": player.get("playerName"),
                "defenseText": defense_text,
                "reason": "defense_text_present_but_no_assignments_parsed",
            })

        rows.append({
            "playerId": player.get("playerId"),
            "playerName": player.get("playerName"),
            "team": player.get("team"),
            "bats": player.get("bats"),
            "role": data.get("role"),
            "defenseText": defense_text,
            "runningText": traits.get("runningText"),
            "stealingText": traits.get("stealingText"),
            "buntingText": traits.get("buntingText"),
            "hitAndRunText": traits.get("hitAndRunText"),
            "assignmentCount": len(assignments),
            "assignments": assignments,
            "sourceFile": str(path).replace("\\", "/"),
        })

    position_counts = {}
    for row in rows:
        for a in row["assignments"]:
            position_counts[a["position"]] = position_counts.get(a["position"], 0) + 1

    output = {
        "schemaVersion": "v0",
        "season": SEASON,
        "sourceDir": str(CARDS_DIR).replace("\\", "/"),
        "counts": {
            "hitters": len(rows),
            "assignments": sum(r["assignmentCount"] for r in rows),
            "warnings": len(warnings),
            "positions": dict(sorted(position_counts.items())),
        },
        "players": rows,
        "warnings": warnings,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "playerId", "playerName", "team", "position", "range", "arm",
            "error", "catcherThrowing", "passedBall", "rawAssignment",
            "defenseText", "runningText", "sourceFile"
        ])
        writer.writeheader()
        for row in rows:
            for a in row["assignments"]:
                writer.writerow({
                    "playerId": row["playerId"],
                    "playerName": row["playerName"],
                    "team": row["team"],
                    "position": a["position"],
                    "range": a["range"],
                    "arm": a["arm"],
                    "error": a["error"],
                    "catcherThrowing": a["catcherThrowing"],
                    "passedBall": a["passedBall"],
                    "rawAssignment": a["rawAssignment"],
                    "defenseText": row["defenseText"],
                    "runningText": row["runningText"],
                    "sourceFile": row["sourceFile"],
                })

    lines = []
    lines.append("# 1968 Hitter Defense Assignments v0")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Hitters parsed: {len(rows)}")
    lines.append(f"- Defensive assignments parsed: {sum(r['assignmentCount'] for r in rows)}")
    lines.append(f"- Warnings: {len(warnings)}")
    lines.append("")
    lines.append("## Position Counts")
    lines.append("")
    for pos, count in sorted(position_counts.items()):
        lines.append(f"- {pos}: {count}")
    lines.append("")
    lines.append("## Sample Multi-Position Players")
    lines.append("")
    multi = [r for r in rows if r["assignmentCount"] >= 3][:20]
    for r in multi:
        assigns = ", ".join(a["rawAssignment"] for a in r["assignments"])
        lines.append(f"- {r['playerName']} | {r['team']} | {assigns}")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        for w in warnings[:50]:
            lines.append(f"- {w['playerName']} | {w['reason']} | {w['defenseText']}")
    else:
        lines.append("- None")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"HITTERS_PARSED: {len(rows)}")
    print(f"ASSIGNMENTS_PARSED: {sum(r['assignmentCount'] for r in rows)}")
    print(f"WARNINGS: {len(warnings)}")
    print("POSITION_COUNTS:")
    for pos, count in sorted(position_counts.items()):
        print(f"  {pos}: {count}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")

if __name__ == "__main__":
    main()
