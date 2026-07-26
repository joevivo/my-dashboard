import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def write_json(path, value):
    target = Path(path)
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"

    if target.exists() and target.read_text(encoding="utf-8") == text:
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return 1


def sum_field(rows, field):
    return sum(float(row.get(field, 0) or 0) for row in rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--join", required=True)
    parser.add_argument("--plan-summary", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--team-name", required=True)
    args = parser.parse_args()

    data = load(args.dataset)
    join = load(args.join)
    plan = load(args.plan_summary)

    starter_rows = [
        game["startingPitcherRow"]
        for game in data["teamGames"]
        if game.get("startingPitcherRow") is not None
    ]

    relief_rows = [
        row
        for game in data["teamGames"]
        for row in game.get("reliefPitcherRows", [])
    ]

    starter_outs = int(sum_field(starter_rows, "inningsPitchedOuts"))
    starter_er = int(sum_field(starter_rows, "earnedRuns"))
    relief_outs = int(sum_field(relief_rows, "inningsPitchedOuts"))
    relief_er = int(sum_field(relief_rows, "earnedRuns"))

    starter_era = round(starter_er * 27 / starter_outs, 2)
    bullpen_era = round(relief_er * 27 / relief_outs, 2)
    starter_share = round(
        starter_outs / (starter_outs + relief_outs),
        3,
    )

    comparison = plan["projectionComparison"]

    scoring_gap = round(
        comparison["actualRunsScoredPerGame"]
        - comparison["projectedRunsScoredPerGame"],
        3,
    )

    prevention_gap = round(
        comparison["projectedRunsAllowedPerGame"]
        - comparison["actualRunsAllowedPerGame"],
        3,
    )

    winning_gap = round(
        comparison["actualWinningPercentage"]
        - comparison["projectedWinningPercentage"],
        3,
    )

    team_signals = [
        {
            "signal": "RUN_PREVENTION_IS_PRIMARY_RECORD_DRIVER",
            "evidence": (
                f"Actual runs allowed are {prevention_gap} per game "
                f"better than projection; scoring is "
                f"{abs(scoring_gap)} per game below projection."
            ),
            "confidence": "HIGH_FOR_OBSERVED_SAMPLE",
            "interpretationLimit": (
                "Fifteen games do not establish season-long "
                "sustainability."
            ),
        },
        {
            "signal": "STARTING_PITCHING_WORKLOAD_STRENGTH",
            "evidence": (
                f"Starters recorded {starter_outs} outs, a "
                f"{starter_share} share of all pitching outs, "
                f"with a {starter_era} ERA."
            ),
            "confidence": "HIGH_FOR_OBSERVED_SAMPLE",
            "interpretationLimit": (
                "Workload durability and opponent quality require "
                "longer observation."
            ),
        },
        {
            "signal": "BULLPEN_RESULT_STRENGTH",
            "evidence": (
                f"Relievers recorded {relief_outs} outs and allowed "
                f"{relief_er} earned runs, producing a "
                f"{bullpen_era} ERA."
            ),
            "confidence": "HIGH_FOR_OBSERVED_SAMPLE",
            "interpretationLimit": (
                "Relief results are highly volatile over "
                "35 to 36 innings."
            ),
        },
        {
            "signal": "RECORD_REGRESSION_WARNING",
            "evidence": (
                f"Actual winning percentage exceeds projection by "
                f"{winning_gap} while scoring remains below "
                "projection."
            ),
            "confidence": "MODERATE",
            "interpretationLimit": (
                "This is a variance warning, not a prediction of "
                "immediate decline."
            ),
        },
    ]

    player_signals = []

    for row in join["playerRows"]:
        hitting = row.get("actualHitting")

        if hitting is not None:
            signals = []
            at_bats = int(hitting["atBats"])
            average = hitting.get("battingAverage")
            substitutions = int(hitting["substitutionRows"])

            if (
                at_bats >= 20
                and average is not None
                and average < 0.200
            ):
                signals.append("OBSERVED_HITTING_SLUMP")

            if (
                at_bats >= 20
                and average is not None
                and average >= 0.320
            ):
                signals.append("HOT_START_VARIANCE_WARNING")

            if substitutions >= 2 and at_bats < 15:
                signals.append("LOW_USAGE_BENCH_EVIDENCE")

            if signals:
                player_signals.append({
                    "player": row["canonicalName"],
                    "role": "hitter",
                    "signals": signals,
                    "evidence": {
                        "atBats": at_bats,
                        "hits": int(hitting["hits"]),
                        "battingAverage": average,
                        "runs": int(hitting["runs"]),
                        "runsBattedIn": int(
                            hitting["runsBattedIn"]
                        ),
                        "starterRows": int(
                            hitting["starterRows"]
                        ),
                        "substitutionRows": substitutions,
                    },
                    "currentRoster": row["currentRoster"],
                    "formerOrUnresolvedObservedPlayer": row[
                        "formerOrUnresolvedObservedPlayer"
                    ],
                })

        pitching = row.get("actualPitching")

        if pitching is not None:
            signals = []
            starts = int(pitching["starts"])
            relief_appearances = int(
                pitching["reliefAppearances"]
            )
            era = pitching.get("earnedRunAverage")

            if starts >= 3 and era is not None and era < 3.00:
                signals.append("ROTATION_STRENGTH_SIGNAL")

            if starts >= 3 and era is not None and era < 1.50:
                signals.append("ROTATION_VARIANCE_WARNING")

            if (
                relief_appearances >= 3
                and era is not None
                and era < 3.00
            ):
                signals.append("BULLPEN_STRENGTH_SIGNAL")

            if (
                relief_appearances >= 3
                and era is not None
                and era < 1.00
            ):
                signals.append("BULLPEN_VARIANCE_WARNING")

            if signals:
                player_signals.append({
                    "player": row["canonicalName"],
                    "role": "pitcher",
                    "signals": signals,
                    "evidence": {
                        "appearances": int(
                            pitching["appearances"]
                        ),
                        "starts": starts,
                        "reliefAppearances": relief_appearances,
                        "inningsPitchedOuts": int(
                            pitching["inningsPitchedOuts"]
                        ),
                        "earnedRuns": int(
                            pitching["earnedRuns"]
                        ),
                        "earnedRunAverage": era,
                        "walks": int(pitching["walks"]),
                        "strikeouts": int(
                            pitching["strikeouts"]
                        ),
                    },
                    "currentRoster": row["currentRoster"],
                    "formerOrUnresolvedObservedPlayer": row[
                        "formerOrUnresolvedObservedPlayer"
                    ],
                })

    former_count = plan["joinCounts"][
        "formerOrUnresolvedObservedPlayers"
    ]

    decision_candidates = [
        {
            "priority": 1,
            "candidate": (
                "PRESERVE_CURRENT_RUN_PREVENTION_STRUCTURE"
            ),
            "basis": (
                "Rotation workload and bullpen results are both "
                "strong."
            ),
            "actionStatus": (
                "HOLD_PENDING_DEFENSE_AND_WORKLOAD_REVIEW"
            ),
        },
        {
            "priority": 2,
            "candidate": "INVESTIGATE_OFFENSIVE_UNDERPERFORMANCE",
            "basis": (
                f"Scoring is {abs(scoring_gap)} runs per game "
                f"below preseason projection."
            ),
            "actionStatus": (
                "REVIEW_LINEUP_AND_PLAYER_SIGNALS_BEFORE_TRANSACTION"
            ),
        },
        {
            "priority": 3,
            "candidate": "DO_NOT_VALUE_PLAYERS_FROM_RECORD_ALONE",
            "basis": (
                "The 12-3 record substantially exceeds the "
                "preseason winning expectation and is "
                "run-prevention driven."
            ),
            "actionStatus": (
                "APPLY_REGRESSION_AND_SAMPLE_SIZE_GUARDRAILS"
            ),
        },
        {
            "priority": 4,
            "candidate": (
                "RETAIN_FORMER_PLAYERS_IN_UPGRADE_UNIVERSE"
            ),
            "basis": (
                f"{former_count} former or unresolved observed "
                f"players remain in the evidence set."
            ),
            "actionStatus": "ELIGIBLE_FOR_LATER_COMPARISON",
        },
    ]

    output = {
        "schemaVersion": (
            "strat365-performance-interpretation-v0"
        ),
        "team": args.team_name,
        "leagueId": join["leagueId"],
        "season": join["season"],
        "throughLeagueDate": join["asOfLeagueDate"],
        "sampleGames": plan["sampleGames"],
        "evidencePolicy": {
            "observedResultsAreFacts": True,
            "sustainabilityLabelsAreInference": True,
            "transactionRecommendationsDeferred": True,
            "formerAquariumPlayersRemainEligible": True,
        },
        "unitMetrics": {
            "starterOuts": starter_outs,
            "starterEarnedRuns": starter_er,
            "starterEarnedRunAverage": starter_era,
            "starterOutShare": starter_share,
            "reliefOuts": relief_outs,
            "reliefEarnedRuns": relief_er,
            "bullpenEarnedRunAverage": bullpen_era,
            "scoringGapVersusProjectionPerGame": scoring_gap,
            "runPreventionAdvantageVersusProjectionPerGame": (
                prevention_gap
            ),
            "winningPercentageGapVersusProjection": winning_gap,
        },
        "teamSignals": team_signals,
        "playerSignals": player_signals,
        "decisionCandidates": decision_candidates,
        "interpretationLimits": [
            (
                "Fifteen games are insufficient to stabilize "
                "batting, pitching or fielding performance."
            ),
            (
                "Batting evidence lacks walks, on-base percentage "
                "and card-outcome attribution."
            ),
            (
                "Pitcher aggregate rows do not fully separate "
                "performance by starter and relief role for "
                "swingmen."
            ),
            (
                "Defense, injury, lineup quality and waiver "
                "alternatives are evaluated in later layers."
            ),
        ],
    }

    output_root = Path(args.output_root)
    output_path = (
        output_root / "performance-interpretation-v0.json"
    )
    manifest_path = (
        output_root
        / "performance-interpretation-source-manifest-v0.json"
    )

    modified = write_json(output_path, output)

    manifest = {
        "schemaVersion": (
            "strat365-performance-interpretation-manifest-v0"
        ),
        "sources": [
            {"path": path, "sha256": sha256(path)}
            for path in (
                args.dataset,
                args.join,
                args.plan_summary,
            )
        ],
        "output": {
            "path": str(output_path),
            "sha256": sha256(output_path),
        },
    }

    modified += write_json(manifest_path, manifest)

    print(
        f"FILES_MODIFIED_BY_INTERPRETATION_BUILDER: {modified}"
    )
    print(f"STARTER_OUTS: {starter_outs}")
    print(f"STARTER_ERA: {starter_era}")
    print(f"RELIEF_OUTS: {relief_outs}")
    print(f"BULLPEN_ERA: {bullpen_era}")
    print(f"TEAM_SIGNAL_COUNT: {len(team_signals)}")
    print(f"PLAYER_SIGNAL_COUNT: {len(player_signals)}")
    print(
        f"DECISION_CANDIDATE_COUNT: "
        f"{len(decision_candidates)}"
    )


if __name__ == "__main__":
    main()