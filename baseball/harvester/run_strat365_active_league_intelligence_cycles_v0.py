from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_strat365_league_intelligence_cycle_v0 import execute_cycle


SCHEMA_VERSION = "bie.strat365.active-league-intelligence-fanout.v0"
RESULT_FILENAME = "fanout-result.json"


class RegistryContractError(ValueError):
    pass


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise RegistryContractError(
            "Registry root must be a JSON object."
        )

    return payload


def write_json_atomic(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f".{path.name}.tmp"
    )

    encoded = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    with temporary_path.open("wb") as handle:
        handle.write(encoded)
        handle.flush()

    temporary_path.replace(path)


def numeric_identity_key(
    value: str,
) -> tuple[int, str]:
    try:
        return (
            int(value),
            value,
        )
    except ValueError:
        return (
            2**63 - 1,
            value,
        )


def resolve_active_leagues(
    registry_payload: dict[str, Any],
) -> list[tuple[str, str]]:
    teams = registry_payload.get("teams")

    if not isinstance(teams, list):
        raise RegistryContractError(
            "Registry teams must be a list."
        )

    teams_by_league: dict[str, set[str]] = {}

    for entry in teams:
        if not isinstance(entry, dict):
            raise RegistryContractError(
                "Every registry team entry must be an object."
            )

        if entry.get("active") is not True:
            continue

        league_id = str(
            entry.get(
                "leagueId",
                "",
            )
        ).strip()

        team_id = str(
            entry.get(
                "teamId",
                "",
            )
        ).strip()

        if not league_id or not team_id:
            raise RegistryContractError(
                "Every active registry entry must have "
                "leagueId and teamId."
            )

        teams_by_league.setdefault(
            league_id,
            set(),
        ).add(team_id)

    ambiguous = {
        league_id: sorted(
            team_ids,
            key=numeric_identity_key,
        )
        for league_id, team_ids in teams_by_league.items()
        if len(team_ids) > 1
    }

    if ambiguous:
        details = "; ".join(
            (
                f"{league_id}="
                f"{','.join(team_ids)}"
            )
            for league_id, team_ids in sorted(
                ambiguous.items(),
                key=lambda item: numeric_identity_key(
                    item[0]
                ),
            )
        )

        raise RegistryContractError(
            "More than one canonical active team "
            f"resolved for league(s): {details}"
        )

    resolved = [
        (
            league_id,
            next(iter(team_ids)),
        )
        for league_id, team_ids in teams_by_league.items()
    ]

    return sorted(
        resolved,
        key=lambda item: numeric_identity_key(
            item[0]
        ),
    )


def ensure_empty_run_root(
    run_root: Path,
) -> None:
    if run_root.exists():
        if not run_root.is_dir():
            raise FileExistsError(
                f"Fan-out run root is not a directory: {run_root}"
            )

        if any(run_root.iterdir()):
            raise FileExistsError(
                f"Fan-out run root is not empty: {run_root}"
            )
    else:
        run_root.mkdir(
            parents=True,
            exist_ok=False,
        )


def execute_fanout(
    *,
    repo_root: Path,
    registry: Path,
    league_date: str,
    phase: str,
    run_root: Path,
    state_root: Path,
    cycle_executor: Callable[..., dict[str, Any]] = execute_cycle,
) -> dict[str, Any]:
    ensure_empty_run_root(
        run_root
    )

    result_path = (
        run_root
        / RESULT_FILENAME
    )

    try:
        registry_payload = load_json(
            registry
        )

        active_leagues = resolve_active_leagues(
            registry_payload
        )

    except Exception as exc:
        result = {
            "schemaVersion": SCHEMA_VERSION,
            "status": "FAIL",
            "leagueDate": str(
                league_date
            ),
            "phase": str(
                phase
            ),
            "activeLeagueCount": 0,
            "passCount": 0,
            "failureCount": 0,
            "registryStatus": "INVALID",
            "failureReason": str(
                exc
            ),
            "failureType": type(
                exc
            ).__name__,
            "cycles": [],
            "completedAtUtc": utc_now(),
        }

        write_json_atomic(
            result_path,
            result,
        )

        return result

    cycle_results: list[dict[str, Any]] = []

    for league_id, team_id in active_leagues:
        league_run_root = (
            run_root
            / f"league-{league_id}"
        )

        try:
            cycle_result = cycle_executor(
                repo_root=repo_root,
                registry=registry,
                league_id=league_id,
                team_id=team_id,
                league_date=league_date,
                phase=phase,
                run_root=league_run_root,
                state_root=state_root,
            )

            status = str(
                cycle_result.get(
                    "status",
                    "FAIL",
                )
            )

            cycle_results.append(
                {
                    "leagueId": league_id,
                    "teamId": team_id,
                    "status": status,
                    "promotionStatus": (
                        cycle_result.get(
                            "promotionStatus"
                        )
                    ),
                    "stateAdvanced": bool(
                        cycle_result.get(
                            "stateAdvanced",
                            False,
                        )
                    ),
                    "runRoot": str(
                        league_run_root
                    ),
                    "cycleResult": cycle_result,
                }
            )

        except Exception as exc:
            cycle_results.append(
                {
                    "leagueId": league_id,
                    "teamId": team_id,
                    "status": "FAIL",
                    "promotionStatus": (
                        "NOT_ATTEMPTED_EXCEPTION"
                    ),
                    "stateAdvanced": False,
                    "runRoot": str(
                        league_run_root
                    ),
                    "failureType": type(
                        exc
                    ).__name__,
                    "failureReason": str(
                        exc
                    ),
                }
            )

    pass_count = sum(
        1
        for result in cycle_results
        if result["status"] == "PASS"
    )

    failure_count = (
        len(cycle_results)
        - pass_count
    )

    if failure_count == 0:
        overall_status = "PASS"
    elif pass_count > 0:
        overall_status = "PARTIAL"
    else:
        overall_status = "FAIL"

    result = {
        "schemaVersion": SCHEMA_VERSION,
        "status": overall_status,
        "leagueDate": str(
            league_date
        ),
        "phase": str(
            phase
        ),
        "activeLeagueCount": len(
            active_leagues
        ),
        "passCount": pass_count,
        "failureCount": failure_count,
        "registryStatus": "VALID",
        "cycles": cycle_results,
        "completedAtUtc": utc_now(),
    }

    write_json_atomic(
        result_path,
        result,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-root",
        required=True,
    )

    parser.add_argument(
        "--registry",
        required=True,
    )

    parser.add_argument(
        "--league-date",
        required=True,
    )

    parser.add_argument(
        "--phase",
        choices=[
            "pregame",
            "postgame",
        ],
        required=True,
    )

    parser.add_argument(
        "--run-root",
        required=True,
    )

    parser.add_argument(
        "--state-root",
        required=True,
    )

    args = parser.parse_args()

    result = execute_fanout(
        repo_root=Path(
            args.repo_root
        ).resolve(),
        registry=Path(
            args.registry
        ).resolve(),
        league_date=str(
            args.league_date
        ),
        phase=str(
            args.phase
        ),
        run_root=Path(
            args.run_root
        ).resolve(),
        state_root=Path(
            args.state_root
        ).resolve(),
    )

    print(
        json.dumps(
            {
                "status": result[
                    "status"
                ],
                "activeLeagueCount": (
                    result[
                        "activeLeagueCount"
                    ]
                ),
                "passCount": result[
                    "passCount"
                ],
                "failureCount": result[
                    "failureCount"
                ],
            },
            separators=(",", ":"),
        )
    )

    return (
        0
        if result["status"] == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )