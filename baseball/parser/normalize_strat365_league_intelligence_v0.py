from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "bie.strat365.league-intelligence.v0"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.depth = 0
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()

        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []

        elif tag == "tr" and self.depth == 1:
            self.row = []

        elif (
            tag in ("th", "td")
            and self.depth == 1
            and self.row is not None
        ):
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if (
            tag in ("th", "td")
            and self.cell is not None
            and self.row is not None
        ):
            value = " ".join(
                " ".join(self.cell).split()
            )
            self.row.append(value)
            self.cell = None

        elif (
            tag == "tr"
            and self.depth == 1
            and self.row is not None
        ):
            if any(self.row):
                assert self.table is not None
                self.table.append(self.row)

            self.row = None

        elif tag == "table":
            if (
                self.depth == 1
                and self.table is not None
            ):
                self.tables.append(self.table)
                self.table = None

            self.depth -= 1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest().upper()


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


def team_key(value: str) -> str:
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"[^a-z0-9]+",
        "",
        value.casefold(),
    )


def integer(value: str | None) -> int | None:
    if value is None:
        return None

    text = value.strip().replace(",", "")

    if not text or text in {"-", "--"}:
        return None

    try:
        return int(text)
    except ValueError:
        return None


def number(value: str | None) -> float | None:
    if value is None:
        return None

    text = value.strip().replace(",", "")

    if not text or text in {"-", "--"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def ratio(
    numerator: int | float | None,
    denominator: int | float | None,
) -> float | None:
    if (
        numerator is None
        or denominator is None
        or denominator == 0
    ):
        return None

    return round(
        float(numerator) / float(denominator),
        4,
    )


def parse_tables(path: Path) -> list[list[list[str]]]:
    parser = TableParser()

    parser.feed(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    return [
        table
        for table in parser.tables
        if table
    ]


def find_table(
    tables: list[list[list[str]]],
    required_headers: set[str],
) -> list[list[str]]:
    for table in tables:
        header = set(table[0])

        if required_headers.issubset(header):
            return table

    raise ValueError(
        "Required table not found: "
        + ",".join(sorted(required_headers))
    )


def row_map(
    header: list[str],
    row: list[str],
) -> dict[str, str]:
    return {
        header[index]: row[index]
        for index in range(
            min(len(header), len(row))
        )
    }


def is_total_team(value: str) -> bool:
    text = value.casefold()

    return (
        "total" in text
        or text in {"team", "teams"}
    )


def parse_team_table(
    table: list[list[str]],
) -> dict[str, dict[str, Any]]:
    header = table[0]
    result: dict[str, dict[str, Any]] = {}

    for row in table[1:]:
        if len(row) != len(header):
            continue

        raw = row_map(header, row)

        name = raw.get("Team", row[0]).strip()

        if (
            not name
            or is_total_team(name)
        ):
            continue

        result[team_key(name)] = {
            "teamName": name,
            "raw": raw,
        }

    return result


def parse_standings(
    table: list[list[str]],
) -> dict[str, dict[str, Any]]:
    header = table[0]
    result: dict[str, dict[str, Any]] = {}

    w_index = header.index("W")
    l_index = header.index("L")

    for row in table[1:]:
        if len(row) != len(header):
            continue

        wins = integer(row[w_index])
        losses = integer(row[l_index])

        if wins is None or losses is None:
            continue

        raw = row_map(header, row)
        name = row[0].strip()

        result[team_key(name)] = {
            "teamName": name,
            "owner": raw.get("Owner"),
            "raw": raw,
            "metrics": {
                "wins": wins,
                "losses": losses,
                "pct": number(raw.get("PCT")),
                "gamesBehind": (
                    0.0
                    if raw.get("GB") in {"-", "--"}
                    else number(raw.get("GB"))
                ),
                "runsScored": integer(
                    raw.get("RS")
                ),
                "runsAllowed": integer(
                    raw.get("RA")
                ),
                "runDifferential": integer(
                    raw.get("Diff")
                ),
            },
            "last10": raw.get("L10"),
            "streak": raw.get("Strk"),
            "home": raw.get("HM"),
            "vsLeft": raw.get("vs.L"),
            "vsRight": raw.get("vs.R"),
        }

    return result


def metrics_from(
    raw: dict[str, str],
    integer_fields: set[str],
    number_fields: set[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key in integer_fields:
        result[key] = integer(
            raw.get(key)
        )

    for key in number_fields:
        result[key] = number(
            raw.get(key)
        )

    return result


def parse_manager(
    table: list[list[str]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for row in table[1:]:
        if len(row) < 11:
            continue

        name = row[0].strip()

        if (
            not name
            or is_total_team(name)
        ):
            continue

        result[team_key(name)] = {
            "teamName": name,
            "raw": row,
            "metrics": {
                "stolenBases": integer(row[1]),
                "caughtStealing": integer(row[2]),
                "stolenBasePct": number(row[3]),
                "sacrifices": integer(row[4]),
                "sacrificeAttempts": integer(row[5]),
                "squeezes": integer(row[6]),
                "squeezeAttempts": integer(row[7]),
                "hitAndRuns": integer(row[8]),
                "hitAndRunAttempts": integer(row[9]),
                "advance": integer(row[10]),
                "intentionalWalks": (
                    integer(row[11])
                    if len(row) > 11
                    else None
                ),
            },
        }

    return result


def rank_values(
    teams: list[dict[str, Any]],
    accessor,
    field_name: str,
    descending: bool,
) -> None:
    values = [
        accessor(team)
        for team in teams
        if accessor(team) is not None
    ]

    unique = sorted(
        set(values),
        reverse=descending,
    )

    rank_map = {
        value: index + 1
        for index, value in enumerate(unique)
    }

    for team in teams:
        value = accessor(team)

        team["derived"]["ranks"][
            field_name
        ] = (
            rank_map[value]
            if value is not None
            else None
        )


def dataset_players(
    dataset: dict[str, Any],
    *,
    pitcher: bool,
) -> list[dict[str, Any]]:
    columns = dataset["columns"]
    players: list[dict[str, Any]] = []

    integer_fields = {
        "AB", "R", "H", "2B", "3B", "HR",
        "RBI", "BB", "SO", "SB", "CS", "E",
        "G", "GS", "W", "L", "S", "BS",
    }

    number_fields = {
        "BA", "OBP", "SLG", "OPS",
        "ERA", "WHIP",
    }

    for row in dataset["rows"]:
        raw = row_map(columns, row)

        player = {
            "name": raw.get("Name"),
            "team": raw.get("Tm"),
            "raw": raw,
            "metrics": metrics_from(
                raw,
                integer_fields,
                number_fields,
            ),
        }

        if pitcher:
            runs = integer(
                raw.get("R")
            )
            earned = integer(
                raw.get("ER")
            )

            player["unearnedRunsAllowed"] = (
                runs - earned
                if (
                    runs is not None
                    and earned is not None
                )
                else None
            )

            player["unearnedRunInterpretation"] = (
                "SCORING_ATTRIBUTION_NOT_"
                "PITCHING_PERFORMANCE_BLAME"
            )

        players.append(player)

    return players


def build(
    capture_root: Path,
) -> dict[str, Any]:
    manifest_path = (
        capture_root
        / "league-intelligence-capture-manifest.json"
    )

    manifest = load_json(
        manifest_path
    )

    if manifest.get("captureStatus") != "PASS":
        raise ValueError(
            "Raw capture manifest is not PASS."
        )

    responses = (
        capture_root
        / "responses"
        / "league-intelligence"
    )

    standings_tables = parse_tables(
        responses
        / "league-standings"
        / "page-00000.html"
    )

    team_stats_tables = parse_tables(
        responses
        / "league-team-stats"
        / "page-00000.html"
    )

    fielding_tables = parse_tables(
        responses
        / "league-team-fielding"
        / "page-00000.html"
    )

    manager_tables = parse_tables(
        responses
        / "league-managers"
        / "page-00000.html"
    )

    leaders_tables = parse_tables(
        responses
        / "league-leaders"
        / "page-00000.html"
    )

    awards_tables = parse_tables(
        responses
        / "league-awards"
        / "page-00000.html"
    )

    transaction_tables = parse_tables(
        responses
        / "league-transactions"
        / "page-00000.html"
    )

    standings_table = find_table(
        standings_tables,
        {"Owner", "W", "L", "PCT", "GB", "RS", "RA", "Diff"},
    )

    offense_table = find_table(
        team_stats_tables,
        {"Team", "R", "BA", "OBP", "SLG", "OPS"},
    )

    pitching_table = find_table(
        team_stats_tables,
        {"Team", "W", "L", "R", "ER", "ERA", "WHIP"},
    )

    fielding_table = find_table(
        fielding_tables,
        {"Team", "E", "DP", "PB", "AVG"},
    )

    manager_table = find_table(
        manager_tables,
        {"Team", "SB", "CS", "SAC", "IBB"},
    )

    standings = parse_standings(
        standings_table
    )

    offense = parse_team_table(
        offense_table
    )

    pitching = parse_team_table(
        pitching_table
    )

    fielding = parse_team_table(
        fielding_table
    )

    managers = parse_manager(
        manager_table
    )

    collections = {
        "standings": standings,
        "offense": offense,
        "pitching": pitching,
        "fielding": fielding,
        "managers": managers,
    }

    for name, collection in collections.items():
        if len(collection) != 12:
            raise ValueError(
                f"{name} expected 12 teams; "
                f"found {len(collection)}."
            )

    common_keys = set(standings)

    for collection in (
        offense,
        pitching,
        fielding,
        managers,
    ):
        common_keys &= set(collection)

    if len(common_keys) != 12:
        raise ValueError(
            "Team identity join did not resolve "
            f"12 common teams; found {len(common_keys)}."
        )

    teams: list[dict[str, Any]] = []

    for key in sorted(common_keys):
        standing = standings[key]

        offense_raw = offense[key]["raw"]
        pitching_raw = pitching[key]["raw"]
        fielding_raw = fielding[key]["raw"]

        offense_metrics = metrics_from(
            offense_raw,
            {
                "AB", "R", "H", "2B", "3B",
                "HR", "RBI", "BB", "SO",
                "SB", "CS",
            },
            {"BA", "OBP", "SLG", "OPS"},
        )

        pitching_metrics = metrics_from(
            pitching_raw,
            {
                "W", "L", "S", "BS",
                "H", "R", "ER", "BB", "SO",
                "CG", "SHO",
            },
            {"ERA", "WHIP"},
        )

        fielding_metrics = metrics_from(
            fielding_raw,
            {
                "PO", "Ast", "OFast", "E",
                "TC", "DP", "GDP", "PB",
                "OSB", "OCS",
            },
            {"OSB%", "AVG"},
        )

        runs = pitching_metrics["R"]
        earned = pitching_metrics["ER"]

        uer = (
            runs - earned
            if (
                runs is not None
                and earned is not None
            )
            else None
        )

        games = (
            standing["metrics"]["wins"]
            + standing["metrics"]["losses"]
        )

        teams.append(
            {
                "teamName": standing["teamName"],
                "teamKey": key,
                "owner": standing["owner"],
                "standings": standing,
                "offense": {
                    "raw": offense_raw,
                    "metrics": offense_metrics,
                },
                "pitching": {
                    "raw": pitching_raw,
                    "metrics": pitching_metrics,
                },
                "fielding": {
                    "raw": fielding_raw,
                    "metrics": fielding_metrics,
                },
                "manager": managers[key],
                "derived": {
                    "games": games,
                    "unearnedRunsAllowed": uer,
                    "unearnedRunsPerGame": ratio(
                        uer,
                        games,
                    ),
                    "unearnedRunShareOfRunsAllowed": ratio(
                        uer,
                        runs,
                    ),
                    "unearnedRunInterpretation": (
                        "DEFENSE_ASSOCIATED_RUN_DAMAGE_"
                        "NOT_PITCHING_FAILURE"
                    ),
                    "ranks": {},
                },
            }
        )

    rank_values(
        teams,
        lambda team: team["standings"]["metrics"]["runDifferential"],
        "runDifferentialRank",
        True,
    )

    rank_values(
        teams,
        lambda team: team["offense"]["metrics"]["R"],
        "runsScoredRank",
        True,
    )

    rank_values(
        teams,
        lambda team: team["offense"]["metrics"]["OPS"],
        "opsRank",
        True,
    )

    rank_values(
        teams,
        lambda team: team["pitching"]["metrics"]["ERA"],
        "eraRank",
        False,
    )

    rank_values(
        teams,
        lambda team: team["pitching"]["metrics"]["WHIP"],
        "whipRank",
        False,
    )

    rank_values(
        teams,
        lambda team: team["pitching"]["metrics"]["R"],
        "runsAllowedRank",
        False,
    )

    rank_values(
        teams,
        lambda team: team["fielding"]["metrics"]["E"],
        "fewestErrorsRank",
        False,
    )

    rank_values(
        teams,
        lambda team: team["fielding"]["metrics"]["AVG"],
        "fieldingAverageRank",
        True,
    )

    rank_values(
        teams,
        lambda team: team["derived"]["unearnedRunsAllowed"],
        "fewestUnearnedRunsAllowedRank",
        False,
    )

    rank_values(
        teams,
        lambda team: team["derived"]["unearnedRunsPerGame"],
        "lowestUnearnedRunsPerGameRank",
        False,
    )

    batting_dataset = load_json(
        responses
        / "league-batting"
        / "dataset.json"
    )

    pitching_dataset = load_json(
        responses
        / "league-pitching"
        / "dataset.json"
    )

    batters = dataset_players(
        batting_dataset,
        pitcher=False,
    )

    pitchers = dataset_players(
        pitching_dataset,
        pitcher=True,
    )

    pitcher_uer = sorted(
        [
            {
                "name": player["name"],
                "team": player["team"],
                "unearnedRunsAllowed": player[
                    "unearnedRunsAllowed"
                ],
                "interpretation": player[
                    "unearnedRunInterpretation"
                ],
            }
            for player in pitchers
            if (
                player["unearnedRunsAllowed"]
                is not None
                and player["unearnedRunsAllowed"] > 0
            )
        ],
        key=lambda item: (
            -item["unearnedRunsAllowed"],
            str(item["name"]),
        ),
    )

    transaction_navigation_only = (
        len(transaction_tables) == 1
        and bool(transaction_tables[0])
        and transaction_tables[0][0]
        and transaction_tables[0][0][0].startswith(
            "Pages:"
        )
    )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "leagueId": str(
            manifest["leagueId"]
        ),
        "leagueDate": str(
            manifest["leagueDate"]
        ),
        "sourceCaptureRoot": str(
            capture_root
        ),
        "sourceManifestSha256": sha256_file(
            manifest_path
        ),
        "teamCount": len(teams),
        "batterCount": len(batters),
        "pitcherCount": len(pitchers),
        "sourceCoverage": {
            "leagueStandings": "NORMALIZED",
            "leagueBatting": "NORMALIZED_COMPLETE_DATASET",
            "leaguePitching": "NORMALIZED_COMPLETE_DATASET",
            "leagueTeamStats": "NORMALIZED",
            "leagueTeamFielding": "NORMALIZED",
            "leagueManagers": "NORMALIZED",
            "leagueLeaders": (
                "CAPTURED_PARSER_PENDING_NO_HTML_TABLE"
                if len(leaders_tables) == 0
                else "CAPTURED_REQUIRES_REVIEW"
            ),
            "leagueAwards": (
                "CAPTURED_PARSER_PENDING_NO_HTML_TABLE"
                if len(awards_tables) == 0
                else "CAPTURED_REQUIRES_REVIEW"
            ),
            "leagueTransactions": (
                "CAPTURED_PARSER_PENDING_PAGINATION_ONLY"
                if transaction_navigation_only
                else "CAPTURED_REQUIRES_REVIEW"
            ),
        },
        "governance": {
            "canonicalDataModified": False,
            "gameCaptureContractChanged": False,
            "bieOwnsSortingAndAnalysis": True,
            "unearnedRunsFormula": "R_MINUS_ER",
            "unearnedRunsInterpretation": (
                "DEFENSE_ASSOCIATED_RUN_DAMAGE_"
                "NOT_PITCHING_FAILURE"
            ),
        },
        "teams": teams,
        "players": {
            "batting": batters,
            "pitching": pitchers,
        },
        "pitcherUnearnedRunAttribution": pitcher_uer,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--capture-root",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    result = build(
        Path(args.capture_root).resolve()
    )

    write_json(
        Path(args.output).resolve(),
        result,
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "leagueId": result["leagueId"],
                "teamCount": result["teamCount"],
                "batterCount": result["batterCount"],
                "pitcherCount": result["pitcherCount"],
            },
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())