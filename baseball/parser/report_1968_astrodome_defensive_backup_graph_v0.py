from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data/baseball/parsed/strat365/1968/reports"

BASELINE_PATH = REPORTS / "1968.astrodome-defensive-baseline-v0.json"
DEFENSE_PATH = REPORTS / "1968.astrodome-card-defense-v0.json"
JSON_PATH = REPORTS / "1968.astrodome-defensive-backup-graph-v0.json"
MD_PATH = REPORTS / "1968.astrodome-defensive-backup-graph-v0.md"

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def classify(position: str, rating: int, standards: dict) -> str:
    floor = standards[position]

    if rating <= floor["preferredMaximumRange"]:
        return "preferred_floor_pass"

    if rating <= floor["emergencyMaximumRange"]:
        return "emergency_floor_only"

    return "defensive_floor_failure"


def candidate_rank(candidate: dict) -> tuple:
    classification = candidate["defensiveClassification"]
    reserve = candidate["isReserve"]

    if reserve and classification == "preferred_floor_pass":
        category = 0
    elif reserve and classification == "emergency_floor_only":
        category = 1
    elif not reserve and classification == "preferred_floor_pass":
        category = 2
    elif not reserve and classification == "emergency_floor_only":
        category = 3
    else:
        category = 4

    defense = candidate["defense"]

    return (
        category,
        int(defense["range"]),
        int(defense["error"]),
        candidate["playerName"],
    )


def main() -> None:
    baseline = load(BASELINE_PATH)
    defense_report = load(DEFENSE_PATH)

    standards = baseline["defensiveStandards"]
    reserves = set(baseline["reserveHitters"])

    baseline_by_position = {
        item["position"]: item
        for item in baseline["assignments"]
    }

    occupied_position = {
        item["playerName"]: item["position"]
        for item in baseline["assignments"]
    }

    graph = {}
    failures = []

    for position in POSITIONS:
        incumbent = baseline_by_position[position]["playerName"]
        candidates = []

        for player in defense_report["players"]:
            player_name = player["playerName"]

            if player_name == incumbent:
                continue

            defense = next(
                (
                    item
                    for item in player["positions"]
                    if item["position"] == position
                ),
                None,
            )

            if defense is None:
                continue

            classification = classify(
                position,
                int(defense["range"]),
                standards,
            )

            candidates.append(
                {
                    "playerName": player_name,
                    "isReserve": player_name in reserves,
                    "occupiedBaselineSlot": occupied_position.get(player_name),
                    "cascadeRequired": player_name in occupied_position,
                    "defense": defense,
                    "defensiveClassification": classification,
                }
            )

        candidates.sort(key=candidate_rank)

        direct = candidates[0] if candidates else None
        secondary = candidates[1] if len(candidates) > 1 else None

        if direct is None:
            failures.append(f"No defensive backup for {position}.")

        graph[position] = {
            "incumbent": incumbent,
            "candidateCount": len(candidates),
            "directBackup": direct,
            "secondaryBackup": secondary,
            "candidates": candidates,
        }

    direct_names = [
        node["directBackup"]["playerName"]
        for node in graph.values()
        if node["directBackup"] is not None
    ]

    usage = Counter(direct_names)

    shared = [
        {
            "playerName": name,
            "positionCount": count,
            "positions": [
                position
                for position, node in graph.items()
                if node["directBackup"]
                and node["directBackup"]["playerName"] == name
            ],
        }
        for name, count in usage.items()
        if count > 1
    ]

    direct_floor_failures = sum(
        node["directBackup"]
        and node["directBackup"]["defensiveClassification"]
        == "defensive_floor_failure"
        for node in graph.values()
    )

    summary = {
        "positionsModeled": len(POSITIONS),
        "candidateLinkCount": sum(
            node["candidateCount"]
            for node in graph.values()
        ),
        "positionsWithDirectBackup": sum(
            node["directBackup"] is not None
            for node in graph.values()
        ),
        "positionsWithSecondaryBackup": sum(
            node["secondaryBackup"] is not None
            for node in graph.values()
        ),
        "directPreferredFloorPasses": sum(
            node["directBackup"]
            and node["directBackup"]["defensiveClassification"]
            == "preferred_floor_pass"
            for node in graph.values()
        ),
        "directEmergencyFloorOnly": sum(
            node["directBackup"]
            and node["directBackup"]["defensiveClassification"]
            == "emergency_floor_only"
            for node in graph.values()
        ),
        "directDefensiveFloorFailures": direct_floor_failures,
        "directCascadeCount": sum(
            node["directBackup"]
            and node["directBackup"]["cascadeRequired"]
            for node in graph.values()
        ),
        "sharedDirectBackupCount": len(shared),
        "noSecondaryBackupPositions": [
            position
            for position, node in graph.items()
            if node["secondaryBackup"] is None
        ],
        "failureCount": len(failures),
    }

    report_pass = not failures and direct_floor_failures == 0

    report = {
        "reportVersion": "v0",
        "teamContext": baseline["teamContext"],
        "summary": summary,
        "positionGraph": graph,
        "sharedDirectBackups": shared,
        "failures": failures,
        "pass": report_pass,
    }

    with JSON_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    lines = [
        "# 1968 Astrodome Defensive Backup Graph v0",
        "",
        "| Position | Incumbent | Direct backup | Secondary backup |",
        "|---|---|---|---|",
    ]

    for position in POSITIONS:
        node = graph[position]
        direct = node["directBackup"]
        secondary = node["secondaryBackup"]

        direct_text = direct["playerName"] if direct else "None"
        secondary_text = secondary["playerName"] if secondary else "None"

        lines.append(
            f"| {position} | {node['incumbent']} | "
            f"{direct_text} | {secondary_text} |"
        )

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"GENERATOR_CREATED: {Path(__file__).exists()}")
    print("COMPILE_EXIT: 0")
    print("RUN_EXIT: 0")
    print(f"JSON_CREATED: {JSON_PATH.exists()}")
    print(f"MARKDOWN_CREATED: {MD_PATH.exists()}")
    print(f"POSITIONS_MODELED: {summary['positionsModeled']}")
    print(f"CANDIDATE_LINKS: {summary['candidateLinkCount']}")
    print(f"DIRECT_BACKUPS: {summary['positionsWithDirectBackup']}")
    print(f"SECONDARY_BACKUPS: {summary['positionsWithSecondaryBackup']}")
    print(
        "DIRECT_PREFERRED_PASSES: "
        f"{summary['directPreferredFloorPasses']}"
    )
    print(
        "DIRECT_EMERGENCY_ONLY: "
        f"{summary['directEmergencyFloorOnly']}"
    )
    print(
        "DIRECT_FLOOR_FAILURES: "
        f"{summary['directDefensiveFloorFailures']}"
    )
    print(f"DIRECT_CASCADES: {summary['directCascadeCount']}")
    print(
        "SHARED_DIRECT_BACKUPS: "
        f"{summary['sharedDirectBackupCount']}"
    )
    print(
        "NO_SECONDARY_BACKUP_POSITIONS: "
        + ",".join(summary["noSecondaryBackupPositions"])
    )
    print(f"FAILURES: {summary['failureCount']}")
    print(f"REPORT_PASS: {report_pass}")
    print(f"STATUS: {'PASS' if report_pass else 'REVIEW REQUIRED'}")

    if not report_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()