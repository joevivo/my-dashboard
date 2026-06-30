from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_INPUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-reports/championship-teams")
DEFAULT_OUT = DEFAULT_INPUT_DIR / "1980.championship-roster-cohort-v0.md"
EVALUATOR = Path("baseball/parser/evaluate_roster_template_v0.py")


@dataclass
class ArchetypeResult:
    name: str
    score: int
    errors: int
    warnings: int
    notes: str


@dataclass
class TeamCohortRow:
    team_id: str
    team: str
    record: str
    ballpark: str
    roster_value: str
    players: int
    pitchers: int
    hitters: int
    resolved: int
    unresolved: int
    salary_total: float
    hitter_salary: float
    starter_salary: float
    relief_salary: float
    best_archetype: str
    best_score: int
    best_warnings: int
    model_risk_count: int | None
    structural_tensions: list[str]


def run_command(args: list[str]) -> str:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\\n"
            + " ".join(args)
            + "\\n\\nSTDOUT:\\n"
            + result.stdout
            + "\\nSTDERR:\\n"
            + result.stderr
        )
    return result.stdout


def parse_float(pattern: str, text: str, default: float = 0.0) -> float:
    match = re.search(pattern, text)
    if not match:
        return default
    return float(match.group(1).replace(",", ""))


def parse_int(pattern: str, text: str, default: int = 0) -> int:
    match = re.search(pattern, text)
    if not match:
        return default
    return int(match.group(1))


def parse_archetype_table(text: str) -> list[ArchetypeResult]:
    rows: list[ArchetypeResult] = []
    for line in text.splitlines():
        match = re.match(
            r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*$",
            line,
        )
        if not match:
            continue

        name = match.group(1).strip()
        if name.lower() == "archetype":
            continue

        rows.append(
            ArchetypeResult(
                name=name,
                score=int(match.group(2)),
                errors=int(match.group(3)),
                warnings=int(match.group(4)),
                notes=match.group(5).strip(),
            )
        )
    return rows


def parse_structural_tensions(text: str) -> list[str]:
    lines = text.splitlines()
    tensions: list[str] = []
    in_section = False

    for line in lines:
        if line.strip() == "## Structural Tensions":
            in_section = True
            continue

        if in_section and line.startswith("## "):
            break

        if in_section and line.startswith("- "):
            tensions.append(line[2:].strip())

    return tensions


def parse_salary_allocation(text: str) -> tuple[float, float, float]:
    return (
        parse_float(r"- Hitters:\s*\$([0-9.]+)M", text),
        parse_float(r"- Starters:\s*\$([0-9.]+)M", text),
        parse_float(r"- Relief:\s*\$([0-9.]+)M", text),
    )


def parse_model_risk_count(notes: str) -> int | None:
    match = re.search(r"High number of model-risk players:\s*(\d+)", notes)
    if not match:
        return None
    return int(match.group(1))


def team_id_from_metadata(metadata: dict) -> str:
    source = str(metadata.get("sourceUrl", "")).rstrip("/")
    if source:
        return source.split("/")[-1]
    return "unknown"


def evaluate_team(metadata_path: Path) -> TeamCohortRow:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    team_id = team_id_from_metadata(metadata)
    roster_path = metadata_path.with_name(f"1980.team-{team_id}-roster-template-v0.csv")
    if not roster_path.exists():
        raise FileNotFoundError(f"Missing roster CSV for {team_id}: {roster_path}")

    ballpark = metadata.get("ballpark") or "Unknown Ballpark"

    compare_text = run_command(
        [
            sys.executable,
            str(EVALUATOR),
            str(roster_path),
            "--ballpark",
            ballpark,
            "--compare-archetypes",
            "--cap",
            "80",
        ]
    )

    archetypes = parse_archetype_table(compare_text)
    if not archetypes:
        raise RuntimeError(f"No archetype rows parsed for {team_id}")

    best = sorted(archetypes, key=lambda item: (item.score, -item.errors, -item.warnings), reverse=True)[0]

    detail_text = run_command(
        [
            sys.executable,
            str(EVALUATOR),
            str(roster_path),
            "--ballpark",
            ballpark,
            "--archetype",
            best.name,
            "--cap",
            "80",
        ]
    )

    hitter_salary, starter_salary, relief_salary = parse_salary_allocation(detail_text)

    return TeamCohortRow(
        team_id=team_id,
        team=metadata.get("team") or "unknown",
        record=metadata.get("record") or "unknown",
        ballpark=ballpark,
        roster_value=metadata.get("rosterValue") or "unknown",
        players=int(metadata.get("playerCount") or 0),
        pitchers=int(metadata.get("pitcherCount") or 0),
        hitters=int(metadata.get("hitterCount") or 0),
        resolved=parse_int(r"Players resolved:\s*(\d+)", detail_text),
        unresolved=parse_int(r"Rows unresolved:\s*(\d+)", detail_text),
        salary_total=parse_float(r"Salary total:\s*\$([0-9.]+)M", compare_text),
        hitter_salary=hitter_salary,
        starter_salary=starter_salary,
        relief_salary=relief_salary,
        best_archetype=best.name,
        best_score=best.score,
        best_warnings=best.warnings,
        model_risk_count=parse_model_risk_count(best.notes),
        structural_tensions=parse_structural_tensions(detail_text),
    )


def money(value: float) -> str:
    return f"${value:.2f}M"


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def minmax(values: list[float]) -> str:
    if not values:
        return "n/a"
    return f"{money(min(values))} to {money(max(values))}"


def write_report(rows: list[TeamCohortRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    hitter_values = [row.hitter_salary for row in rows]
    starter_values = [row.starter_salary for row in rows]
    relief_values = [row.relief_salary for row in rows]
    scores = [row.best_score for row in rows]

    parks = sorted({row.ballpark for row in rows})
    archetype_counts: dict[str, int] = {}
    for row in rows:
        archetype_counts[row.best_archetype] = archetype_counts.get(row.best_archetype, 0) + 1

    lines: list[str] = []
    lines.append("# BIE Championship Roster Cohort v0")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "Summarize imported 1980 Strat365 championship-team roster constructions before pivoting BIE toward 1968 evaluation."
    )
    lines.append("")
    lines.append("This report treats championship teams as roster-shape evidence, not as automatic player-level recommendations.")
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    lines.append(f"- Teams: {len(rows)}")
    lines.append(f"- Parks represented: {len(parks)}")
    for park in parks:
        lines.append(f"  - {park}")
    lines.append("")
    lines.append("## Cohort Salary Bands")
    lines.append("")
    lines.append(f"- Hitter spend range: {minmax(hitter_values)}")
    lines.append(f"- Starter spend range: {minmax(starter_values)}")
    lines.append(f"- Relief spend range: {minmax(relief_values)}")
    lines.append(f"- Average hitter spend: {money(avg(hitter_values))}")
    lines.append(f"- Average starter spend: {money(avg(starter_values))}")
    lines.append(f"- Average relief spend: {money(avg(relief_values))}")
    lines.append(f"- Best-fit score range: {min(scores)} to {max(scores)}")
    lines.append("")
    lines.append("## Best-Fit Archetype Counts")
    lines.append("")
    for archetype, count in sorted(archetype_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {archetype}: {count}")
    lines.append("")
    lines.append("## Team Summary")
    lines.append("")
    lines.append(
        "| Team | Record | Park | Players | Hitter $ | Starter $ | Relief $ | Best Fit | Score | Warnings | Model Risk |"
    )
    lines.append("|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|")
    for row in rows:
        model_risk = "n/a" if row.model_risk_count is None else str(row.model_risk_count)
        lines.append(
            f"| {row.team} | {row.record} | {row.ballpark} | {row.players} | "
            f"{money(row.hitter_salary)} | {money(row.starter_salary)} | {money(row.relief_salary)} | "
            f"{row.best_archetype} | {row.best_score} | {row.best_warnings} | {model_risk} |"
        )
    lines.append("")
    lines.append("## Structural Tensions by Team")
    lines.append("")
    for row in rows:
        lines.append(f"### {row.team}")
        lines.append("")
        lines.append(f"- Record: {row.record}")
        lines.append(f"- Ballpark: {row.ballpark}")
        lines.append(f"- Best fit: {row.best_archetype} ({row.best_score}/100)")
        lines.append(f"- Resolved rows: {row.resolved}")
        lines.append(f"- Unresolved rows: {row.unresolved}")
        lines.append("")
        for tension in row.structural_tensions:
            lines.append(f"- {tension}")
        lines.append("")
    lines.append("## Initial BIE Takeaways")
    lines.append("")
    lines.append("- The championship cohort should be used to refine roster-shape expectations, not to declare optimal player choices.")
    lines.append("- Current archetypes should be checked against observed champion salary bands before being used on the 1968 set.")
    lines.append("- Structural tensions that repeatedly appear on champions should be downgraded from likely defects to review prompts.")
    lines.append("- Park context should remain central when translating 1980 lessons to 1968 draft preparation.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report on imported Strat365 championship roster cohort.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    metadata_paths = sorted(args.input_dir.glob("*metadata-v0.json"))
    if not metadata_paths:
        raise SystemExit(f"No metadata files found in {args.input_dir}")

    rows = [evaluate_team(path) for path in metadata_paths]
    write_report(rows, args.out)

    print(f"Wrote {args.out}")
    print(f"Teams evaluated: {len(rows)}")
    for row in rows:
        print(
            f"- {row.team}: {row.best_archetype} {row.best_score}/100 | "
            f"H {money(row.hitter_salary)} / S {money(row.starter_salary)} / R {money(row.relief_salary)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
