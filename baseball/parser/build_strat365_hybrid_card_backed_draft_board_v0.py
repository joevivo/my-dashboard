from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

SEASON = 1968

DRAFT_SIGNALS_PATH = Path("data/baseball/parsed/strat365/1968/draft-signals/1968.browser-baseline-draft-signals.json")
SUMMARY_DIR = Path("data/baseball/parsed/strat365/1968/card-probability-summaries")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1968/draft-boards")
CSV_PATH = OUTPUT_DIR / "1968.hybrid-card-backed-draft-board.csv"
MD_PATH = OUTPUT_DIR / "1968.hybrid-card-backed-draft-board.md"

HITTER_SIDE_WEIGHTS = {
    "vs_right_pitcher": 0.68,
    "vs_left_pitcher": 0.32,
}

PITCHER_SIDE_WEIGHTS = {
    "vs_right_batter": 0.60,
    "vs_left_batter": 0.40,
}


def decimal_weight(value: Any) -> float:
    if isinstance(value, dict):
        return float(value.get("decimal", 0) or 0)
    return 0.0


def outcome_weight(side: dict[str, Any], label: str) -> float:
    return decimal_weight(side.get("baseOutcomeWeights", {}).get(label))


def weighted_card_metrics(summary: dict[str, Any], role: str) -> dict[str, float]:
    weights = HITTER_SIDE_WEIGHTS if role == "hitter" else PITCHER_SIDE_WEIGHTS

    metrics = {
        "ob": 0.0,
        "hit": 0.0,
        "out": 0.0,
        "single": 0.0,
        "double": 0.0,
        "triple": 0.0,
        "hr": 0.0,
        "walk": 0.0,
        "strikeout": 0.0,
        "totalBasesCandidate": 0.0,
        "unresolvedSides": 0,
    }

    for side in summary.get("sides", []):
        side_name = side.get("side")
        weight = weights.get(side_name, 0.0)
        if not weight:
            continue

        single = outcome_weight(side, "SINGLE")
        double = outcome_weight(side, "DOUBLE")
        triple = outcome_weight(side, "TRIPLE")
        hr = outcome_weight(side, "HOME_RUN")

        metrics["ob"] += weight * decimal_weight(side.get("onBaseCandidateWeight"))
        metrics["hit"] += weight * decimal_weight(side.get("hitCandidateWeight"))
        metrics["out"] += weight * decimal_weight(side.get("outCandidateWeight"))
        metrics["single"] += weight * single
        metrics["double"] += weight * double
        metrics["triple"] += weight * triple
        metrics["hr"] += weight * hr
        metrics["walk"] += weight * outcome_weight(side, "WALK")
        metrics["strikeout"] += weight * outcome_weight(side, "STRIKEOUT")
        metrics["totalBasesCandidate"] += weight * (single + 2 * double + 3 * triple + 4 * hr)

        if side.get("unresolvedOutcomeRows"):
            metrics["unresolvedSides"] += 1

    return metrics


def card_score(role: str, metrics: dict[str, float]) -> float:
    if role == "hitter":
        return 100 * (
            1.15 * metrics["ob"]
            + 0.70 * metrics["hit"]
            + 0.75 * metrics["totalBasesCandidate"]
            + 0.45 * metrics["hr"]
            + 0.15 * metrics["walk"]
            - 0.10 * metrics["strikeout"]
            - 0.04 * metrics["unresolvedSides"]
        )

    return 100 * (
        1.20 * metrics["out"]
        + 0.55 * metrics["strikeout"]
        - 1.10 * metrics["ob"]
        - 0.75 * metrics["hit"]
        - 0.90 * metrics["hr"]
        - 0.35 * metrics["walk"]
        - 0.04 * metrics["unresolvedSides"]
    )


def row_from_signal(item: dict[str, Any], role: str) -> dict[str, Any]:
    player = item.get("player", {})
    player_id = int(player.get("playerId"))
    salary = float(item.get("salary", {}).get("millions", 0) or 0)
    browser_score = float(item.get("browserBaselineDraftScore", {}).get("score", 0) or 0)

    summary_path = SUMMARY_DIR / f"{player_id}.card-probability-summary.json"
    card_backed = summary_path.exists()

    metrics = {
        "ob": 0.0,
        "hit": 0.0,
        "out": 0.0,
        "single": 0.0,
        "double": 0.0,
        "triple": 0.0,
        "hr": 0.0,
        "walk": 0.0,
        "strikeout": 0.0,
        "totalBasesCandidate": 0.0,
        "unresolvedSides": 0,
    }

    raw_card_score = None
    hybrid_score = browser_score

    if card_backed:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        metrics = weighted_card_metrics(summary, role)
        raw_card_score = card_score(role, metrics)
        hybrid_score = 0.65 * raw_card_score + 0.35 * browser_score

    return {
        "playerId": player_id,
        "playerName": player.get("playerName"),
        "team": player.get("team"),
        "role": role,
        "salaryMillions": round(salary, 2),
        "confidenceTier": "card-backed" if card_backed else "browser-baseline",
        "hybridDraftScore": round(hybrid_score, 2),
        "browserBaselineDraftScore": round(browser_score, 2),
        "rawCardScore": "" if raw_card_score is None else round(raw_card_score, 2),
        "hybridValueScore": round(hybrid_score / max(salary, 0.50), 2),
        "obCandidate": round(metrics["ob"], 3),
        "hitCandidate": round(metrics["hit"], 3),
        "outCandidate": round(metrics["out"], 3),
        "hrCandidate": round(metrics["hr"], 3),
        "walkCandidate": round(metrics["walk"], 3),
        "strikeoutCandidate": round(metrics["strikeout"], 3),
        "unresolvedSides": metrics["unresolvedSides"],
    }


def markdown_table(title: str, rows: list[dict[str, Any]], limit: int = 25) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Rank | Player | Tier | Salary | Hybrid | Browser | Card | Value |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]

    for index, row in enumerate(rows[:limit], 1):
        lines.append(
            f"| {index} | {row['playerName']} | {row['confidenceTier']} | "
            f"{row['salaryMillions']:.2f} | {row['hybridDraftScore']:.2f} | "
            f"{row['browserBaselineDraftScore']:.2f} | {row['rawCardScore']} | "
            f"{row['hybridValueScore']:.2f} |"
        )

    lines.append("")
    return lines


def main() -> None:
    signals = json.loads(DRAFT_SIGNALS_PATH.read_text(encoding="utf-8"))

    rows = []
    for item in signals.get("hitters", []):
        rows.append(row_from_signal(item, "hitter"))
    for item in signals.get("pitchers", []):
        rows.append(row_from_signal(item, "pitcher"))

    hitters = sorted(
        [row for row in rows if row["role"] == "hitter"],
        key=lambda row: row["hybridDraftScore"],
        reverse=True,
    )
    pitchers = sorted(
        [row for row in rows if row["role"] == "pitcher"],
        key=lambda row: row["hybridDraftScore"],
        reverse=True,
    )
    cheap_hitters = sorted(
        [row for row in hitters if row["salaryMillions"] <= 3.0],
        key=lambda row: row["hybridValueScore"],
        reverse=True,
    )
    cheap_pitchers = sorted(
        [row for row in pitchers if row["salaryMillions"] <= 2.0],
        key=lambda row: row["hybridValueScore"],
        reverse=True,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["role"], -row["hybridDraftScore"])))

    card_backed_count = sum(1 for row in rows if row["confidenceTier"] == "card-backed")
    unresolved_count = sum(1 for row in rows if row["unresolvedSides"])

    md_lines = [
        "# 1968 Hybrid Card-Backed Draft Board",
        "",
        f"Players: {len(rows)}",
        f"Hitters: {len(hitters)}",
        f"Pitchers: {len(pitchers)}",
        f"Card-backed players: {card_backed_count}",
        f"Browser-baseline players: {len(rows) - card_backed_count}",
        f"Players with unresolved card sides: {unresolved_count}",
        "",
        "Model: card-backed players use 65% raw card score + 35% browser-baseline score. Browser-only players use browser-baseline score.",
        "",
    ]

    md_lines.extend(markdown_table("Top Hitters", hitters))
    md_lines.extend(markdown_table("Top Pitchers", pitchers))
    md_lines.extend(markdown_table("Cheap Hitter Values <= $3M", cheap_hitters))
    md_lines.extend(markdown_table("Cheap Pitcher Values <= $2M", cheap_pitchers))

    MD_PATH.write_text("\n".join(md_lines), encoding="utf-8")

    print("Hybrid board created")
    print(f"Players: {len(rows)}")
    print(f"Card-backed: {card_backed_count}")
    print(f"Browser-baseline: {len(rows) - card_backed_count}")
    print(f"Unresolved card-backed players: {unresolved_count}")
    print(f"CSV: {CSV_PATH}")
    print(f"MD: {MD_PATH}")

    print()
    print("Top 12 hitters:")
    for index, row in enumerate(hitters[:12], 1):
        print(
            f"{index:>2}. {row['playerName']} | {row['confidenceTier']} | "
            f"${row['salaryMillions']:.2f} | score {row['hybridDraftScore']:.2f} | value {row['hybridValueScore']:.2f}"
        )

    print()
    print("Top 12 pitchers:")
    for index, row in enumerate(pitchers[:12], 1):
        print(
            f"{index:>2}. {row['playerName']} | {row['confidenceTier']} | "
            f"${row['salaryMillions']:.2f} | score {row['hybridDraftScore']:.2f} | value {row['hybridValueScore']:.2f}"
        )


if __name__ == "__main__":
    main()
