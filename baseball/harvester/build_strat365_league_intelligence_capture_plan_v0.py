from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "strat365-league-intelligence-capture-plan-v0"

PHASE_COLLECTIONS = {
    "pregame": "pregameSources",
    "postgame": "postgameLeagueSources",
}

EXPECTED_FAMILIES = [
    "leagueStandings",
    "leagueBatting",
    "leaguePitching",
    "leagueLeaders",
    "leagueTeamStats",
    "leagueTeamFielding",
    "leagueManagers",
    "leagueAwards",
    "leagueInjuries",
    "leagueTransactions",
]

PAGINATED_FAMILIES = {
    "leagueTransactions": {
        "pageSize": 100,
        "acquisitionSort": "native",
    },
    "leagueBatting": {
        "pageSize": 50,
        "acquisitionSort": "ops",
    },
    "leaguePitching": {
        "pageSize": 50,
        "acquisitionSort": "era",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def slugify(value: str) -> str:
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1-\2",
        value,
    )

    value = re.sub(
        r"[^A-Za-z0-9]+",
        "-",
        value,
    )

    return value.strip("-").lower()


def find_team(
    registry: dict[str, Any],
    *,
    league_id: str,
    team_id: str,
) -> dict[str, Any]:
    teams = registry.get("teams")

    if not isinstance(teams, list):
        raise ValueError(
            "Registry teams collection is missing."
        )

    matches = [
        team
        for team in teams
        if (
            str(team.get("leagueId")) == league_id
            and str(team.get("teamId")) == team_id
        )
    ]

    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one active team for "
            f"league={league_id}, team={team_id}; "
            f"found {len(matches)}."
        )

    return matches[0]


def build_request(
    *,
    source: dict[str, Any],
    league_id: str,
    team_id: str,
    league_date: str,
    phase: str,
) -> dict[str, Any]:
    family = str(
        source.get("sourceFamily") or ""
    )

    if not family:
        raise ValueError(
            "Registry source lacks sourceFamily."
        )

    url_template = str(
        source.get("urlTemplate") or ""
    )

    if not url_template:
        raise ValueError(
            f"{family} lacks urlTemplate."
        )

    slug = slugify(family)

    request: dict[str, Any] = {
        "requestId": (
            f"league-intelligence-{slug}"
        ),
        "sourceFamily": family,
        "leagueId": league_id,
        "teamId": team_id,
        "leagueDate": league_date,
        "phase": phase,
        "requestedUrl": url_template.format(
            leagueId=league_id,
            teamId=team_id,
        ),
        "required": bool(
            source.get("required") is True
        ),
        "planStatus": "planned",
        "attemptCount": 0,
        "artifactRelativeRoot": (
            "responses/league-intelligence/"
            f"{slug}"
        ),
        "metadataRelativeRoot": (
            "metadata/league-intelligence/"
            f"{slug}"
        ),
    }

    if family in PAGINATED_FAMILIES:
        policy = PAGINATED_FAMILIES[family]

        request["captureMode"] = (
            "completePaginatedTable"
        )

        request["paginationPolicy"] = {
            "strategy": "strat365OffsetLinks",
            "pageSize": int(
                policy["pageSize"]
            ),
            "initialOffset": 0,
            "discoverNextOffsetsFromResponse": True,
            "captureUntilNoNextOffset": True,
            "sameSourceFamilyOnly": True,
            "acquisitionSort": str(
                policy["acquisitionSort"]
            ),
            "semanticMeaningOfSort": "NONE",
        }

    else:
        request["captureMode"] = "singlePage"

    return request


def validate_plan(
    plan: dict[str, Any],
) -> None:
    requests = plan.get("requests")

    if not isinstance(requests, list):
        raise ValueError(
            "Plan requests collection is missing."
        )

    if len(requests) != 10:
        raise ValueError(
            "Expected 10 logical league sources; "
            f"found {len(requests)}."
        )

    families = [
        str(request.get("sourceFamily"))
        for request in requests
    ]

    if families != EXPECTED_FAMILIES:
        raise ValueError(
            "Unexpected source-family contract: "
            f"{families}"
        )

    request_ids = [
        str(request.get("requestId"))
        for request in requests
    ]

    if len(request_ids) != len(
        set(request_ids)
    ):
        raise ValueError(
            "Duplicate requestId detected."
        )

    required_count = sum(
        request.get("required") is True
        for request in requests
    )

    if required_count != 8:
        raise ValueError(
            "Expected 8 required sources; "
            f"found {required_count}."
        )

    paginated = [
        request["sourceFamily"]
        for request in requests
        if (
            request.get("captureMode")
            == "completePaginatedTable"
        )
    ]

    if paginated != [
        "leagueBatting",
        "leaguePitching",
        "leagueTransactions",
    ]:
        raise ValueError(
            "Unexpected paginated datasets: "
            f"{paginated}"
        )

    for family in paginated:
        request = next(
            item
            for item in requests
            if item["sourceFamily"] == family
        )

        policy = request[
            "paginationPolicy"
        ]

        if (
            policy.get(
                "captureUntilNoNextOffset"
            )
            is not True
        ):
            raise ValueError(
                f"{family} pagination "
                "is not exhaustive."
            )

        if (
            policy.get(
                "semanticMeaningOfSort"
            )
            != "NONE"
        ):
            raise ValueError(
                f"{family} acquisition sort "
                "became semantic."
            )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--registry",
        required=True,
    )

    parser.add_argument(
        "--league-id",
        required=True,
    )

    parser.add_argument(
        "--team-id",
        required=True,
    )

    parser.add_argument(
        "--league-date",
        required=True,
    )

    parser.add_argument(
        "--phase",
        choices=(
            "pregame",
            "postgame",
        ),
        default="pregame",
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    registry_path = Path(
        args.registry
    ).resolve()

    output_path = Path(
        args.output
    ).resolve()

    registry = load_json(
        registry_path
    )

    league_id = str(
        args.league_id
    )

    team_id = str(
        args.team_id
    )

    phase = str(
        args.phase
    )

    team = find_team(
        registry,
        league_id=league_id,
        team_id=team_id,
    )

    collection_name = (
        PHASE_COLLECTIONS[phase]
    )

    sources = team.get(
        collection_name
    )

    if not isinstance(
        sources,
        list,
    ):
        raise ValueError(
            "Missing registry collection: "
            f"{collection_name}"
        )

    if len(sources) != 9:
        raise ValueError(
            f"{collection_name} must contain "
            "9 normalized sources; found "
            f"{len(sources)}."
        )

    requests = [
        build_request(
            source=source,
            league_id=league_id,
            team_id=team_id,
            league_date=str(
                args.league_date
            ),
            phase=phase,
        )
        for source in sources
    ]

    plan = {
        "schemaVersion": SCHEMA_VERSION,
        "planState": "frozen",
        "leagueDate": str(
            args.league_date
        ),
        "leagueId": league_id,
        "teamId": team_id,
        "teamName": str(
            team.get("teamName") or ""
        ),
        "season": team.get("season"),
        "phase": phase,
        "sourceCollection": collection_name,
        "plannedSourceCount": len(
            requests
        ),
        "requiredSourceCount": sum(
            request["required"]
            for request in requests
        ),
        "completePaginatedDatasetCount": sum(
            request["captureMode"]
            == "completePaginatedTable"
            for request in requests
        ),
        "singlePageSourceCount": sum(
            request["captureMode"]
            == "singlePage"
            for request in requests
        ),
        "governance": {
            "gameCaptureContractChanged": False,
            "canonicalDataModified": False,
            "bieOwnsSortingAndAnalysis": True,
            "acquisitionSortIsNonSemantic": True,
            "completeDatasetRequiredForBatting": True,
            "completeDatasetRequiredForPitching": True,
        },
        "requests": requests,
    }

    validate_plan(plan)

    write_json(
        output_path,
        plan,
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "schemaVersion": (
                    SCHEMA_VERSION
                ),
                "leagueId": league_id,
                "teamId": team_id,
                "phase": phase,
                "plannedSourceCount": (
                    plan[
                        "plannedSourceCount"
                    ]
                ),
                "requiredSourceCount": (
                    plan[
                        "requiredSourceCount"
                    ]
                ),
                "paginatedDatasetCount": (
                    plan[
                        "completePaginatedDatasetCount"
                    ]
                ),
                "singlePageSourceCount": (
                    plan[
                        "singlePageSourceCount"
                    ]
                ),
            },
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())