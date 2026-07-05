from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEASON = "1968"

COMPARISON_BUILDER = ROOT / "baseball" / "parser" / "build_1968_roster_template_comparison_v0.py"
DISTINCTNESS_BUILDER = ROOT / "baseball" / "parser" / "report_1968_roster_template_distinctness_audit_v0.py"

COMPARISON_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "draft-boards" / "1968.roster-template-comparison-v0.json"
DISTINCTNESS_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "reports" / "1968.roster-template-distinctness-audit-v0.json"

OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "reports"
JSON_OUT = OUTPUT_DIR / "1968.roster-template-sanity-review-v0.json"
MD_OUT = OUTPUT_DIR / "1968.roster-template-sanity-review-v0.md"

STRATEGY_ORDER = [
    "balanced",
    "premium_hitter_heavy",
    "ace_pitcher_heavy",
    "value_heavy",
]


def run_script(path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"# FAILED SCRIPT: {path.relative_to(ROOT)}")
        if result.stdout:
            print("# STDOUT")
            print(result.stdout)
        if result.stderr:
            print("# STDERR")
            print(result.stderr)
        raise RuntimeError(f"Script failed: {path}")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def role_text(player: dict[str, Any]) -> str:
    parts = [
        player.get("primaryPosition"),
        player.get("starterEndurance"),
        player.get("reliefEndurance"),
        player.get("closerEndurance"),
    ]
    return "/".join(str(part) for part in parts if part)


def player_label(player: dict[str, Any]) -> str:
    return (
        f"{player.get('playerName')} | {player.get('team')} | {role_text(player)} | "
        f"salary={float(player.get('salaryMillions') or 0):.2f}"
    )


def severity_rank(value: str) -> int:
    return {
        "acceptable": 0,
        "suspicious": 1,
        "model_debt": 2,
        "draft_blocker": 3,
    }[value]


def max_severity(values: list[str]) -> str:
    if not values:
        return "acceptable"
    return sorted(values, key=severity_rank)[-1]


def max_pairwise_overlap(strategy_id: str, pairwise: list[dict[str, Any]]) -> tuple[float, list[str]]:
    max_value = 0.0
    partners: list[str] = []

    for row in pairwise:
        left = row["left"]
        right = row["right"]
        if strategy_id not in {left, right}:
            continue

        overlap = float(row["overlapPct"])
        partner = right if left == strategy_id else left

        if overlap > max_value:
            max_value = overlap
            partners = [partner]
        elif overlap == max_value:
            partners.append(partner)

    return max_value, partners


def pairwise_map(pairwise: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    mapped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in pairwise:
        mapped[(row["left"], row["right"])] = row
        mapped[(row["right"], row["left"])] = row
    return mapped


def review_anchor(player: dict[str, Any]) -> dict[str, Any]:
    salary = float(player.get("salaryMillions") or 0.0)

    if salary >= 8.0:
        category = "premium_anchor_review"
        note = "High-cost universal anchor. Needs baseball/Strat365 validation, not just model agreement."
    elif salary <= 0.75:
        category = "cheap_role_anchor_review"
        note = "Low-cost universal anchor. Could be useful roster glue or a salary/value artifact."
    else:
        category = "common_anchor"
        note = "Appears in every template and is plausibly functioning as a shared roster-construction anchor."

    return {
        "playerId": player.get("playerId"),
        "playerName": player.get("playerName"),
        "team": player.get("team"),
        "role": player.get("role"),
        "roleText": role_text(player),
        "salaryMillions": salary,
        "category": category,
        "note": note,
    }


def assess_strategy(
    strategy_id: str,
    template: dict[str, Any],
    distinct_summary: dict[str, Any],
    pairwise: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = template["counts"]
    salary = float(template["salaryUsedMillions"])
    hitter_salary = float(template["hitterSalaryMillions"])
    pitcher_salary = float(template["pitcherSalaryMillions"])
    card_backed = int(counts["cardBackedPlayers"])
    exclusive_players = int(distinct_summary["exclusivePlayers"])
    highest_overlap, overlap_partners = max_pairwise_overlap(strategy_id, pairwise)

    findings: list[dict[str, str]] = []
    statuses: list[str] = []

    all_legal = all(item["status"] == "PASS" for item in template["legality"])
    if all_legal:
        findings.append({
            "status": "acceptable",
            "finding": "Template passes current legality and salary-band checks.",
        })
    else:
        findings.append({
            "status": "draft_blocker",
            "finding": "Template fails one or more legality checks.",
        })
        statuses.append("draft_blocker")

    if salary > 80.0:
        findings.append({
            "status": "draft_blocker",
            "finding": "Template exceeds the 80M salary cap.",
        })
        statuses.append("draft_blocker")

    if highest_overlap >= 0.75:
        findings.append({
            "status": "model_debt",
            "finding": f"Template has high overlap ({highest_overlap:.3f}) with {', '.join(overlap_partners)}.",
        })
        statuses.append("model_debt")

    if exclusive_players == 0:
        findings.append({
            "status": "model_debt",
            "finding": "Template has zero exclusive players, so it does not yet express a distinct roster identity.",
        })
        statuses.append("model_debt")

    if card_backed < 14:
        findings.append({
            "status": "suspicious",
            "finding": f"Template has only {card_backed} card-backed players, raising browser-baseline dependency risk.",
        })
        statuses.append("suspicious")

    if pitcher_salary < 25.0:
        findings.append({
            "status": "suspicious",
            "finding": f"Pitcher spend is thin at {pitcher_salary:.2f}M.",
        })
        statuses.append("suspicious")

    if hitter_salary < 30.0:
        findings.append({
            "status": "suspicious",
            "finding": f"Hitter spend is thin at {hitter_salary:.2f}M. This may be acceptable only as an extreme pitching build.",
        })
        statuses.append("suspicious")

    if strategy_id == "ace_pitcher_heavy" and exclusive_players >= 8:
        findings.append({
            "status": "acceptable",
            "finding": "Ace-pitcher-heavy is meaningfully distinct by exclusive-player count and pitcher spend.",
        })

    if strategy_id == "value_heavy":
        findings.append({
            "status": "model_debt",
            "finding": "Value-heavy is value-scored but not budget-distinct from premium-hitter-heavy in v0.",
        })
        statuses.append("model_debt")

    if strategy_id == "premium_hitter_heavy":
        findings.append({
            "status": "acceptable",
            "finding": "Premium-hitter-heavy no longer has the earlier unusable 6M pitching problem.",
        })

    if strategy_id == "balanced":
        findings.append({
            "status": "acceptable",
            "finding": "Balanced remains useful as a baseline even though it lacks a distinct identity.",
        })

    classification = max_severity(statuses)

    return {
        "strategyId": strategy_id,
        "classification": classification,
        "salaryUsedMillions": salary,
        "hitterSalaryMillions": hitter_salary,
        "pitcherSalaryMillions": pitcher_salary,
        "cardBackedPlayers": card_backed,
        "exclusivePlayers": exclusive_players,
        "highestOverlapPct": highest_overlap,
        "highestOverlapPartners": overlap_partners,
        "findings": findings,
    }


def build_payload() -> dict[str, Any]:
    run_script(COMPARISON_BUILDER)
    run_script(DISTINCTNESS_BUILDER)

    comparison = load_json(COMPARISON_JSON)
    distinctness = load_json(DISTINCTNESS_JSON)

    templates = {template["strategyId"]: template for template in comparison["templates"]}
    distinct_summaries = {
        summary["strategyId"]: summary
        for summary in distinctness["templateSummaries"]
    }
    pairwise = distinctness["pairwiseOverlap"]

    strategy_reviews = [
        assess_strategy(strategy_id, templates[strategy_id], distinct_summaries[strategy_id], pairwise)
        for strategy_id in STRATEGY_ORDER
    ]

    anchor_reviews = [
        review_anchor(player)
        for player in distinctness.get("universalSharedPlayers", [])
    ]

    draft_blockers = [
        review
        for review in strategy_reviews
        if review["classification"] == "draft_blocker"
    ]

    model_debt = []
    for review in strategy_reviews:
        for finding in review["findings"]:
            if finding["status"] == "model_debt":
                model_debt.append({
                    "strategyId": review["strategyId"],
                    "finding": finding["finding"],
                })

    return {
        "schemaVersion": "bie.roster-template-sanity-review.v0",
        "season": 1968,
        "sourceArtifacts": {
            "comparison": str(COMPARISON_JSON.relative_to(ROOT)),
            "distinctness": str(DISTINCTNESS_JSON.relative_to(ROOT)),
        },
        "reviewQuestion": "Do the generated legal roster templates make baseball/Strat365 sense as draft-prep concepts?",
        "strategyReviews": strategy_reviews,
        "anchorReviews": anchor_reviews,
        "draftBlockers": draft_blockers,
        "modelDebt": model_debt,
        "decision": {
            "status": "continue_with_caution",
            "summary": (
                "The outputs are useful for draft preparation, but only ace_pitcher_heavy is clearly distinct. "
                "Balanced remains a baseline. Premium-hitter-heavy is plausible. Value-heavy needs future differentiation."
            ),
            "recommendedNextArtifact": "1968 draft pivot board v0",
        },
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 1968 Roster Template Sanity Review v0",
        "",
        f"Review question: {payload['reviewQuestion']}",
        "",
        "## Strategy Review",
        "",
        "| Strategy | Classification | Total | Hitting | Pitching | Card-backed | Exclusive | Highest Overlap |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for review in payload["strategyReviews"]:
        lines.append(
            f"| {review['strategyId']} | {review['classification']} | "
            f"{review['salaryUsedMillions']:.2f} | {review['hitterSalaryMillions']:.2f} | "
            f"{review['pitcherSalaryMillions']:.2f} | {review['cardBackedPlayers']} | "
            f"{review['exclusivePlayers']} | {review['highestOverlapPct']:.3f} |"
        )

    for review in payload["strategyReviews"]:
        lines.extend([
            "",
            f"## {review['strategyId']}",
            "",
            f"Classification: `{review['classification']}`",
            "",
        ])

        for finding in review["findings"]:
            lines.append(f"- `{finding['status']}`: {finding['finding']}")

    lines.extend([
        "",
        "## Universal Anchor Review",
        "",
        "| Player | Team | Role | Salary | Category | Note |",
        "|---|---|---|---:|---|---|",
    ])

    for anchor in payload["anchorReviews"]:
        lines.append(
            f"| {anchor['playerName']} | {anchor['team']} | {anchor['roleText']} | "
            f"{anchor['salaryMillions']:.2f} | {anchor['category']} | {anchor['note']} |"
        )

    lines.extend([
        "",
        "## Model Debt",
        "",
    ])

    if payload["modelDebt"]:
        for item in payload["modelDebt"]:
            lines.append(f"- `{item['strategyId']}`: {item['finding']}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Draft Blockers",
        "",
    ])

    if payload["draftBlockers"]:
        for item in payload["draftBlockers"]:
            lines.append(f"- `{item['strategyId']}`: classified as draft blocker")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        payload["decision"]["summary"],
        "",
        f"Recommended next artifact: `{payload['decision']['recommendedNextArtifact']}`",
        "",
    ])

    return "\n".join(lines)


def print_summary(payload: dict[str, Any]) -> None:
    print("# SANITY REVIEW SUMMARY")
    for review in payload["strategyReviews"]:
        print(
            f"{review['strategyId']}: classification={review['classification']} | "
            f"hitting={review['hitterSalaryMillions']:.2f} | "
            f"pitching={review['pitcherSalaryMillions']:.2f} | "
            f"exclusive={review['exclusivePlayers']} | "
            f"highestOverlap={review['highestOverlapPct']:.3f}"
        )

    print("\n# STRATEGY FINDINGS")
    for review in payload["strategyReviews"]:
        print(f"\n{review['strategyId']} [{review['classification']}]")
        for finding in review["findings"]:
            print(f"- {finding['status']}: {finding['finding']}")

    print("\n# ANCHOR REVIEW")
    for anchor in payload["anchorReviews"]:
        print(
            f"- {anchor['playerName']} | {anchor['team']} | {anchor['roleText']} | "
            f"salary={anchor['salaryMillions']:.2f} | {anchor['category']}"
        )

    print("\n# MODEL DEBT")
    if payload["modelDebt"]:
        for item in payload["modelDebt"]:
            print(f"- {item['strategyId']}: {item['finding']}")
    else:
        print("None")

    print("\n# DRAFT BLOCKERS")
    if payload["draftBlockers"]:
        for item in payload["draftBlockers"]:
            print(f"- {item['strategyId']}")
    else:
        print("None")

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 roster template sanity review v0.")
    print("Paste back:")
    print("1. # SANITY REVIEW SUMMARY")
    print("2. # STRATEGY FINDINGS")
    print("3. # ANCHOR REVIEW")
    print("4. # MODEL DEBT")
    print("5. # DRAFT BLOCKERS")
    print("6. # OUTPUT FILES")
    print("7. # BASEBALL GIT STATUS")
    print("8. # RESULT SUMMARY")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = build_payload()
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
