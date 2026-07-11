import csv
import json
import re
from pathlib import Path

SEASON = "1968"
BASE = Path("data/baseball/parsed/strat365") / SEASON

SIGNALS_PATH = BASE / "draft-signals" / "1968.browser-baseline-draft-signals.json"
PROB_DIR = BASE / "card-probability-summaries"
CARD_DIR = BASE / "cards"
OUT_DIR = BASE / "card-mechanics"

OUT_JSON = OUT_DIR / "1968.pitcher-card-mechanics-v0.json"
OUT_CSV = OUT_DIR / "1968.pitcher-card-mechanics-v0.csv"
OUT_MD = OUT_DIR / "1968.pitcher-card-mechanics-v0.md"

LEFT_BATTER_WEIGHT = 0.30
RIGHT_BATTER_WEIGHT = 0.70

BASE_OUTCOME_FIELDS = {
    "SINGLE": "weightedSingleAllowed",
    "DOUBLE": "weightedDoubleAllowed",
    "TRIPLE": "weightedTripleAllowed",
    "HOME_RUN": "weightedHRAllowed",
    "WALK": "weightedWalkAllowed",
    "HBP": "weightedHBPAllowed",
    "GROUNDBALL": "weightedGroundball",
    "GROUNDBALL_X": "weightedGroundballX",
    "FLYBALL": "weightedFlyball",
    "FLYBALL_X": "weightedFlyballX",
    "LINEOUT": "weightedLineout",
    "POPOUT": "weightedPopout",
    "FOULOUT": "weightedFoulout",
    "STRIKEOUT": "weightedStrikeout",
    "CATCHER_X": "weightedCatcherX",
}

DEPENDENCY_FIELDS = {
    "ballpark_home_run_check": "ballparkHRCheckAllowed",
    "ballpark_single_check": "ballparkSingleCheckAllowed",
    "split_roll_d20": "splitRollD20",
    "split_roll_closed_range": "splitRollClosedRange",
    "defensive_x_chart": "defensiveXChartDependency",
    "catcher_defensive_chart": "catcherDefensiveChartDependency",
    "base_out_state": "baseOutStateDependency",
    "runner_advancement_state": "runnerAdvancementDependency",
    "legacy_baserunning_marker": "legacyBaserunningMarker",
    "pitcher_fatigue_marker_ignored_in_365": "pitcherFatigueMarkerIgnoredIn365",
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
    left = side_by_name(prob, "vs_left_batter")
    right = side_by_name(prob, "vs_right_batter")

    if not left or not right:
        return 0.0

    return (
        LEFT_BATTER_WEIGHT * fraction_decimal(left.get(metric_name))
        + RIGHT_BATTER_WEIGHT * fraction_decimal(right.get(metric_name))
    )


def weighted_outcome(prob, outcome_name):
    left = side_by_name(prob, "vs_left_batter")
    right = side_by_name(prob, "vs_right_batter")

    if not left or not right:
        return 0.0

    left_outcomes = left.get("baseOutcomeWeights") or {}
    right_outcomes = right.get("baseOutcomeWeights") or {}

    return (
        LEFT_BATTER_WEIGHT * fraction_decimal(left_outcomes.get(outcome_name))
        + RIGHT_BATTER_WEIGHT * fraction_decimal(right_outcomes.get(outcome_name))
    )


def weighted_dependency(prob, dependency_name):
    left = side_by_name(prob, "vs_left_batter")
    right = side_by_name(prob, "vs_right_batter")

    if not left or not right:
        return 0.0

    left_deps = left.get("dependencyWeights") or {}
    right_deps = right.get("dependencyWeights") or {}

    return (
        LEFT_BATTER_WEIGHT * fraction_decimal(left_deps.get(dependency_name))
        + RIGHT_BATTER_WEIGHT * fraction_decimal(right_deps.get(dependency_name))
    )


def round4(value):
    return round(float(value or 0.0), 4)


def parse_int_from_text(text, pattern):
    if not text:
        return None
    m = re.search(pattern, str(text))
    if not m:
        return None
    try:
        return int(m.group(1))
    except (TypeError, ValueError):
        return None


def parse_signed_int(value):
    if value is None:
        return None
    try:
        return int(str(value).replace("+", "").strip())
    except ValueError:
        return None


def parse_pitcher_rating(pitcher_text):
    return parse_int_from_text(pitcher_text, r"pitcher-(\d+)")


def parse_error(error_text):
    return parse_int_from_text(error_text, r"e(\d+)")


def parse_balk(balk_text):
    return parse_int_from_text(balk_text, r"bk-\s*(\d+)")


def parse_wild_pitch(wild_pitch_text):
    return parse_int_from_text(wild_pitch_text, r"wp-\s*(\d+)")


def parse_starter_endurance(starter_text):
    return parse_int_from_text(starter_text, r"starter\((\d+)\)")


def parse_relief_parts(relief_text):
    if not relief_text:
        return None, None
    m = re.search(r"relief\((\d+)\)(?:/([0-9N]+))?", str(relief_text))
    if not m:
        return None, None
    relief = int(m.group(1))
    closer_raw = m.group(2)
    closer = None
    if closer_raw and closer_raw != "N":
        closer = int(closer_raw)
    return relief, closer


def astrodome_fit(signals_row):
    for fit in signals_row.get("ballparkFits", []):
        if fit.get("ballparkName") == "Astrodome 1968":
            return fit
    return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    signals = load_json(SIGNALS_PATH)
    pitchers = signals.get("pitchers", [])

    rows = []
    warnings = []

    for p in pitchers:
        player = p.get("player") or {}
        pitcher = p.get("pitcher") or {}
        salary = p.get("salary") or {}

        player_id = player.get("playerId")
        if not player_id:
            continue

        prob_path = PROB_DIR / f"{player_id}.card-probability-summary.json"
        card_path = CARD_DIR / f"{player_id}.parsed-card-evidence.json"

        if not prob_path.exists():
            continue

        prob = load_json(prob_path)

        if prob.get("role") != "pitcher":
            continue

        card = load_json(card_path) if card_path.exists() else {}
        traits = card.get("pitcherTraits") or {}

        relief_endurance, closer_endurance = parse_relief_parts(traits.get("reliefText"))

        row = {
            "playerId": player_id,
            "playerName": player.get("playerName"),
            "team": player.get("team"),
            "role": "pitcher",
            "salary": salary.get("millions"),
            "salaryRaw": salary.get("raw"),
            "throws": pitcher.get("throws") or traits.get("throws"),
            "balance": pitcher.get("balance"),
            "browserEndurance": pitcher.get("endurance"),
            "starterText": traits.get("starterText"),
            "reliefText": traits.get("reliefText"),
            "starterEndurance": parse_starter_endurance(traits.get("starterText")),
            "reliefEndurance": relief_endurance,
            "closerEndurance": closer_endurance,
            "hold": parse_signed_int(traits.get("hold")),
            "buntingText": traits.get("buntingText"),
            "balkText": traits.get("balkText"),
            "balk": parse_balk(traits.get("balkText")),
            "wildPitchText": traits.get("wildPitchText"),
            "wildPitch": parse_wild_pitch(traits.get("wildPitchText")),
            "pitcherFieldingText": traits.get("pitcherText"),
            "pitcherFieldingRating": parse_pitcher_rating(traits.get("pitcherText")),
            "pitcherErrorText": traits.get("errorText"),
            "pitcherError": parse_error(traits.get("errorText")),
            "weightedOnBaseAllowed": round4(weighted_side_metric(prob, "onBaseCandidateWeight")),
            "weightedHitAllowed": round4(weighted_side_metric(prob, "hitCandidateWeight")),
            "weightedOut": round4(weighted_side_metric(prob, "outCandidateWeight")),
            "cardBacked": bool(card_path.exists()),
            "probabilitySummaryFile": str(prob_path).replace("\\", "/"),
            "cardEvidenceFile": str(card_path).replace("\\", "/") if card_path.exists() else None,
        }

        for source, target in BASE_OUTCOME_FIELDS.items():
            row[target] = round4(weighted_outcome(prob, source))

        for source, target in DEPENDENCY_FIELDS.items():
            row[target] = round4(weighted_dependency(prob, source))

        row["weightedXBHAllowed"] = round4(
            row["weightedDoubleAllowed"] + row["weightedTripleAllowed"] + row["weightedHRAllowed"]
        )
        row["weightedNonHRHitAllowed"] = round4(
            row["weightedSingleAllowed"] + row["weightedDoubleAllowed"] + row["weightedTripleAllowed"]
        )
        row["hrAllowedDependencyRatio"] = round4(
            row["ballparkHRCheckAllowed"] / row["weightedHRAllowed"] if row["weightedHRAllowed"] else 0.0
        )
        row["defenseDelegation"] = round4(
            row["weightedGroundballX"] + row["weightedFlyballX"] + row["weightedCatcherX"]
        )

        astro = astrodome_fit(p)
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
        r.get("weightedOnBaseAllowed") or 9,
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
                "vsLeftBatter": LEFT_BATTER_WEIGHT,
                "vsRightBatter": RIGHT_BATTER_WEIGHT,
                "note": "Rough comparison weighting only; not league-opponent calibrated.",
            },
            "probabilityBasis": "within_card_side; does not include pitcher-card vs batter-card selection, park resolution, or defensive X-chart resolution",
        },
        "counts": {
            "pitchers": len(rows),
            "warnings": len(warnings),
            "cardBacked": sum(1 for r in rows if r.get("cardBacked")),
        },
        "pitchers": rows,
        "warnings": warnings,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    csv_fields = [
        "playerId", "playerName", "team", "salary", "throws", "balance",
        "browserEndurance", "starterEndurance", "reliefEndurance", "closerEndurance",
        "hold", "balk", "wildPitch", "pitcherFieldingRating", "pitcherError",
        "weightedOnBaseAllowed", "weightedHitAllowed", "weightedOut",
        "weightedSingleAllowed", "weightedDoubleAllowed", "weightedTripleAllowed",
        "weightedHRAllowed", "weightedXBHAllowed", "weightedNonHRHitAllowed",
        "weightedWalkAllowed", "weightedHBPAllowed", "weightedStrikeout",
        "weightedGroundball", "weightedGroundballX", "weightedFlyball",
        "weightedFlyballX", "weightedLineout", "weightedPopout", "weightedCatcherX",
        "ballparkHRCheckAllowed", "ballparkSingleCheckAllowed",
        "splitRollD20", "splitRollClosedRange", "defensiveXChartDependency",
        "catcherDefensiveChartDependency", "defenseDelegation",
        "hrAllowedDependencyRatio", "astrodomeParkAdjustedBrowserRank",
        "astrodomeParkAdjustedBrowserScore", "cardBacked",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in csv_fields})

    lines = []
    lines.append("# 1968 Pitcher Card Mechanics v0")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Pitchers with probability summaries: {len(rows)}")
    lines.append(f"- Card-backed pitchers: {sum(1 for r in rows if r.get('cardBacked'))}")
    lines.append(f"- Warnings: {len(warnings)}")
    lines.append("")
    lines.append("## Model Notes")
    lines.append("")
    lines.append(f"- Side weighting: {LEFT_BATTER_WEIGHT:.2f} vs LHB / {RIGHT_BATTER_WEIGHT:.2f} vs RHB")
    lines.append("- Metrics are within-card-side only.")
    lines.append("- Metrics do not include pitcher-card vs batter-card selection, park resolution, or defensive X-chart resolution.")
    lines.append("")
    lines.append("## Top Astrodome Browser-Ranked Card-Backed Pitchers")
    lines.append("")
    lines.append("| Rank | Player | Salary | Endurance | OBA | Hit | HR | BB | K | GBX | FBX | BP HR | P Field | Hold |")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for r in rows[:30]:
        lines.append(
            f"| {r.get('astrodomeParkAdjustedBrowserRank')} "
            f"| {r.get('playerName')} "
            f"| {r.get('salary')} "
            f"| {r.get('browserEndurance')} "
            f"| {r.get('weightedOnBaseAllowed')} "
            f"| {r.get('weightedHitAllowed')} "
            f"| {r.get('weightedHRAllowed')} "
            f"| {r.get('weightedWalkAllowed')} "
            f"| {r.get('weightedStrikeout')} "
            f"| {r.get('weightedGroundballX')} "
            f"| {r.get('weightedFlyballX')} "
            f"| {r.get('ballparkHRCheckAllowed')} "
            f"| {r.get('pitcherFieldingText')}/{r.get('pitcherErrorText')} "
            f"| {r.get('hold')} |"
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
    print(f"PITCHERS_WITH_PROBABILITY_SUMMARIES: {len(rows)}")
    print(f"CARD_BACKED_PITCHERS: {sum(1 for r in rows if r.get('cardBacked'))}")
    print(f"WARNINGS: {len(warnings)}")
    print(f"JSON_OUT: {OUT_JSON}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("TOP_10_ASTRODOME_BROWSER_RANKED:")
    for r in rows[:10]:
        print(
            f"  {r.get('astrodomeParkAdjustedBrowserRank')} | "
            f"{r.get('playerName')} | ${r.get('salary')} | "
            f"{r.get('browserEndurance')} | OBA={r.get('weightedOnBaseAllowed')} | "
            f"HIT={r.get('weightedHitAllowed')} | HR={r.get('weightedHRAllowed')} | "
            f"BB={r.get('weightedWalkAllowed')} | K={r.get('weightedStrikeout')} | "
            f"BP_HR={r.get('ballparkHRCheckAllowed')} | "
            f"P={r.get('pitcherFieldingText')}/{r.get('pitcherErrorText')}"
        )


if __name__ == "__main__":
    main()
