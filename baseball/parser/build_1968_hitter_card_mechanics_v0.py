import csv
import json
from pathlib import Path

SEASON = "1968"
BASE = Path("data/baseball/parsed/strat365") / SEASON

SIGNALS_PATH = BASE / "draft-signals" / "1968.browser-baseline-draft-signals.json"
PROB_DIR = BASE / "card-probability-summaries"
CARD_DIR = BASE / "cards"
OUT_DIR = BASE / "card-mechanics"

OUT_JSON = OUT_DIR / "1968.hitter-card-mechanics-v0.json"
OUT_CSV = OUT_DIR / "1968.hitter-card-mechanics-v0.csv"
OUT_MD = OUT_DIR / "1968.hitter-card-mechanics-v0.md"

LEFT_WEIGHT = 0.30
RIGHT_WEIGHT = 0.70

BASE_OUTCOME_FIELDS = {
    "SINGLE": "weightedSingle",
    "DOUBLE": "weightedDouble",
    "TRIPLE": "weightedTriple",
    "HOME_RUN": "weightedHR",
    "WALK": "weightedBB",
    "HBP": "weightedHBP",
    "GROUNDBALL": "weightedGB",
    "FLYBALL": "weightedFB",
    "LINEOUT": "weightedLineout",
    "LINEOUT_MAX": "weightedLineoutMax",
    "POPOUT": "weightedPopout",
    "FOULOUT": "weightedFoulout",
    "STRIKEOUT": "weightedK",
}

DEPENDENCY_FIELDS = {
    "ballpark_home_run_check": "ballparkHRCheck",
    "ballpark_single_check": "ballparkSingleCheck",
    "split_roll_d20": "splitRollD20",
    "split_roll_closed_range": "splitRollClosedRange",
    "base_out_state": "baseOutStateDependency",
    "runner_advancement_state": "runnerAdvancementDependency",
    "clutch_context_reversal": "clutchContextDependency",
    "contextual_plus_marker": "contextualPlusDependency",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fraction_decimal(weight_obj):
    if not isinstance(weight_obj, dict):
        return 0.0
    value = weight_obj.get("decimal")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def side_by_name(prob, side_name):
    for side in prob.get("sides", []):
        if side.get("side") == side_name:
            return side
    return None


def weighted_side_metric(prob, metric_name):
    left = side_by_name(prob, "vs_left_pitcher")
    right = side_by_name(prob, "vs_right_pitcher")

    if not left or not right:
        return 0.0

    if metric_name == "onBaseCandidateWeight":
        return (
            LEFT_WEIGHT * fraction_decimal(left.get("onBaseCandidateWeight"))
            + RIGHT_WEIGHT * fraction_decimal(right.get("onBaseCandidateWeight"))
        )

    if metric_name == "hitCandidateWeight":
        return (
            LEFT_WEIGHT * fraction_decimal(left.get("hitCandidateWeight"))
            + RIGHT_WEIGHT * fraction_decimal(right.get("hitCandidateWeight"))
        )

    if metric_name == "outCandidateWeight":
        return (
            LEFT_WEIGHT * fraction_decimal(left.get("outCandidateWeight"))
            + RIGHT_WEIGHT * fraction_decimal(right.get("outCandidateWeight"))
        )

    return 0.0


def weighted_outcome(prob, outcome_name):
    left = side_by_name(prob, "vs_left_pitcher")
    right = side_by_name(prob, "vs_right_pitcher")

    if not left or not right:
        return 0.0

    left_outcomes = left.get("baseOutcomeWeights") or {}
    right_outcomes = right.get("baseOutcomeWeights") or {}

    return (
        LEFT_WEIGHT * fraction_decimal(left_outcomes.get(outcome_name))
        + RIGHT_WEIGHT * fraction_decimal(right_outcomes.get(outcome_name))
    )


def weighted_dependency(prob, dependency_name):
    left = side_by_name(prob, "vs_left_pitcher")
    right = side_by_name(prob, "vs_right_pitcher")

    if not left or not right:
        return 0.0

    left_deps = left.get("dependencyWeights") or {}
    right_deps = right.get("dependencyWeights") or {}

    return (
        LEFT_WEIGHT * fraction_decimal(left_deps.get(dependency_name))
        + RIGHT_WEIGHT * fraction_decimal(right_deps.get(dependency_name))
    )


def count_injury_flags(prob):
    total = 0
    for side in prob.get("sides", []):
        flags = side.get("nonProbabilityFlagCounts") or {}
        try:
            total += int(flags.get("INJURY_FLAG") or 0)
        except (TypeError, ValueError):
            pass
    return total


def astrodome_fit(signals_row):
    for fit in signals_row.get("ballparkFits", []):
        if fit.get("ballparkName") == "Astrodome 1968":
            return fit
    return None


def round4(value):
    return round(float(value or 0.0), 4)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    signals = load_json(SIGNALS_PATH)
    hitters = signals.get("hitters", [])

    rows = []
    warnings = []

    for h in hitters:
        player = h.get("player") or {}
        hitter = h.get("hitter") or {}
        salary = h.get("salary") or {}

        player_id = player.get("playerId")
        if not player_id:
            continue

        prob_path = PROB_DIR / f"{player_id}.card-probability-summary.json"
        card_path = CARD_DIR / f"{player_id}.parsed-card-evidence.json"

        if not prob_path.exists():
            continue

        prob = load_json(prob_path)

        if prob.get("role") != "hitter":
            continue

        card = load_json(card_path) if card_path.exists() else {}
        traits = card.get("hitterTraits") or {}

        row = {
            "playerId": player_id,
            "playerName": player.get("playerName"),
            "team": player.get("team"),
            "role": "hitter",
            "salary": salary.get("millions"),
            "salaryRaw": salary.get("raw"),
            "bats": hitter.get("bats"),
            "primaryPosition": hitter.get("primaryPosition"),
            "browserDefense": hitter.get("defense"),
            "balance": hitter.get("balance"),
            "defenseText": traits.get("defenseText"),
            "runningText": traits.get("runningText"),
            "stealingText": traits.get("stealingText"),
            "buntingText": traits.get("buntingText"),
            "hitAndRunText": traits.get("hitAndRunText"),
            "weightedOB": round4(weighted_side_metric(prob, "onBaseCandidateWeight")),
            "weightedHit": round4(weighted_side_metric(prob, "hitCandidateWeight")),
            "weightedOut": round4(weighted_side_metric(prob, "outCandidateWeight")),
            "injuryFlags": count_injury_flags(prob),
            "cardBacked": bool(card_path.exists()),
            "probabilitySummaryFile": str(prob_path).replace("\\", "/"),
            "cardEvidenceFile": str(card_path).replace("\\", "/") if card_path.exists() else None,
        }

        for source, target in BASE_OUTCOME_FIELDS.items():
            row[target] = round4(weighted_outcome(prob, source))

        for source, target in DEPENDENCY_FIELDS.items():
            row[target] = round4(weighted_dependency(prob, source))

        row["weightedXBH"] = round4(row["weightedDouble"] + row["weightedTriple"] + row["weightedHR"])
        row["nonHRHit"] = round4(row["weightedSingle"] + row["weightedDouble"] + row["weightedTriple"])
        row["hrDependencyRatio"] = round4(
            row["ballparkHRCheck"] / row["weightedHR"] if row["weightedHR"] else 0.0
        )

        astro = astrodome_fit(h)
        row["astrodomeBrowserParkFitScore"] = (
            round4((astro.get("browserParkFitScore") or {}).get("score")) if astro else None
        )
        row["astrodomeParkAdjustedBrowserScore"] = (
            round4((astro.get("parkAdjustedBrowserScore") or {}).get("score")) if astro else None
        )
        row["astrodomeParkAdjustedBrowserRank"] = (
            astro.get("parkAdjustedBrowserRank") if astro else None
        )

        if not card_path.exists():
            warnings.append({
                "playerId": player_id,
                "playerName": player.get("playerName"),
                "reason": "probability_summary_exists_but_card_evidence_missing",
            })

        rows.append(row)

    rows.sort(key=lambda r: (
        r.get("astrodomeParkAdjustedBrowserRank") if r.get("astrodomeParkAdjustedBrowserRank") is not None else 9999,
        -(r.get("weightedOB") or 0),
    ))

    output = {
        "schemaVersion": "v0",
        "season": SEASON,
        "sourceFiles": {
            "draftSignals": str(SIGNALS_PATH).replace("\\", "/"),
            "probabilitySummaries": str(PROB_DIR).replace("\\", "/"),
            "cardEvidence": str(CARD_DIR).replace("\\", "/"),
        },
        "model": {
            "sideWeighting": {
                "vsLeftPitcher": LEFT_WEIGHT,
                "vsRightPitcher": RIGHT_WEIGHT,
                "note": "Rough comparison weighting only; not league-opponent calibrated.",
            },
            "probabilityBasis": "within_card_side; does not include batter-card vs pitcher-card selection, park resolution, or defensive X-chart resolution",
        },
        "counts": {
            "hitters": len(rows),
            "warnings": len(warnings),
            "cardBacked": sum(1 for r in rows if r.get("cardBacked")),
        },
        "hitters": rows,
        "warnings": warnings,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    csv_fields = [
        "playerId", "playerName", "team", "salary", "bats", "primaryPosition",
        "browserDefense", "balance", "defenseText", "runningText",
        "weightedOB", "weightedHit", "weightedOut",
        "weightedSingle", "weightedDouble", "weightedTriple", "weightedHR",
        "weightedXBH", "nonHRHit", "weightedBB", "weightedHBP",
        "weightedGB", "weightedFB", "weightedLineout", "weightedPopout",
        "weightedFoulout", "weightedK",
        "ballparkHRCheck", "ballparkSingleCheck",
        "splitRollD20", "splitRollClosedRange", "hrDependencyRatio",
        "injuryFlags", "astrodomeParkAdjustedBrowserRank",
        "astrodomeParkAdjustedBrowserScore", "cardBacked",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in csv_fields})

    lines = []
    lines.append("# 1968 Hitter Card Mechanics v0")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Hitters with probability summaries: {len(rows)}")
    lines.append(f"- Card-backed hitters: {sum(1 for r in rows if r.get('cardBacked'))}")
    lines.append(f"- Warnings: {len(warnings)}")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append(f"- Side weighting: {LEFT_WEIGHT:.2f} vs LHP / {RIGHT_WEIGHT:.2f} vs RHP")
    lines.append("- Metrics are within-card-side only.")
    lines.append("- Metrics do not include batter-card vs pitcher-card selection, park resolution, or defensive X-chart resolution.")
    lines.append("")
    lines.append("## Top Astrodome Browser-Ranked Card-Backed Hitters")
    lines.append("")
    lines.append("| Rank | Player | Pos | Salary | OB | Hit | HR | BB | GB | K | BP HR | Defense |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows[:30]:
        lines.append(
            f"| {r.get('astrodomeParkAdjustedBrowserRank')} "
            f"| {r.get('playerName')} "
            f"| {r.get('primaryPosition')} "
            f"| {r.get('salary')} "
            f"| {r.get('weightedOB')} "
            f"| {r.get('weightedHit')} "
            f"| {r.get('weightedHR')} "
            f"| {r.get('weightedBB')} "
            f"| {r.get('weightedGB')} "
            f"| {r.get('weightedK')} "
            f"| {r.get('ballparkHRCheck')} "
            f"| {r.get('defenseText') or r.get('browserDefense')} |"
        )
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        for w in warnings[:50]:
            lines.append(f"- {w.get('playerName')} | {w.get('reason')}")
    else:
        lines.append("- None")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"HITTERS_WITH_PROBABILITY_SUMMARIES: {len(rows)}")
    print(f"CARD_BACKED_HITTERS: {sum(1 for r in rows if r.get('cardBacked'))}")
    print(f"WARNINGS: {len(warnings)}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("TOP_10_ASTRODOME_BROWSER_RANKED:")
    for r in rows[:10]:
        print(
            f"  {r.get('astrodomeParkAdjustedBrowserRank')} | "
            f"{r.get('playerName')} | {r.get('primaryPosition')} | "
            f"${r.get('salary')} | OB={r.get('weightedOB')} | "
            f"HR={r.get('weightedHR')} | BB={r.get('weightedBB')} | "
            f"DEF={r.get('defenseText') or r.get('browserDefense')}"
        )


if __name__ == "__main__":
    main()
