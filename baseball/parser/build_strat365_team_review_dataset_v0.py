from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


LEXICAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("hit_and_run", re.compile(r"\bhit[- ]and[- ]run\b", re.IGNORECASE)),
    ("stolen_base", re.compile(r"\bstole\b|\bstolen base\b", re.IGNORECASE)),
    ("caught_stealing", re.compile(r"\bcaught stealing\b", re.IGNORECASE)),
    ("pickoff", re.compile(r"\bpicked off\b|\bpickoff\b", re.IGNORECASE)),
    ("pinch_hitter", re.compile(r"\bpinch[- ]hit(?:ter|ting)?\b", re.IGNORECASE)),
    ("pinch_runner", re.compile(r"\bpinch[- ]run(?:ner|ning)?\b", re.IGNORECASE)),
    (
        "defensive_substitution",
        re.compile(
            r"\bdefensive replacement\b|\bdefensive substitution\b",
            re.IGNORECASE,
        ),
    ),
    ("injury", re.compile(r"\binjur(?:y|ed|ies)\b", re.IGNORECASE)),
    ("error", re.compile(r"\berror\b", re.IGNORECASE)),
    ("sacrifice", re.compile(r"\bsacrifice\b|\bsac bunt\b", re.IGNORECASE)),
    (
        "intentional_walk",
        re.compile(r"\bintentional(?:ly)? walk(?:ed)?\b", re.IGNORECASE),
    ),
    ("double_play", re.compile(r"\bdouble play\b", re.IGNORECASE)),
    ("triple_play", re.compile(r"\btriple play\b", re.IGNORECASE)),
    ("home_run", re.compile(r"\bhome run\b|\bhomered\b", re.IGNORECASE)),
    ("wild_pitch", re.compile(r"\bwild pitch\b", re.IGNORECASE)),
    ("passed_ball", re.compile(r"\bpassed ball\b", re.IGNORECASE)),
    ("balk", re.compile(r"\bbalk\b", re.IGNORECASE)),
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return (
        "\n".join(
            json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            for row in rows
        )
        + "\n"
    ).encode("utf-8")


def write_if_changed(path: Path, payload: bytes) -> int:
    if path.exists() and path.read_bytes() == payload:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(path)
    return 1


def relative_to_repo(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def safe_int(value: Any) -> int:
    if value is None or value == "":
        return 0

    if isinstance(value, bool):
        return int(value)

    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return 0


def normalized_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def lexical_tags(record: dict[str, Any]) -> list[str]:
    searchable = " ".join(
        normalized_text(record.get(field))
        for field in (
            "text",
            "rawText",
            "result",
            "miscellaneous",
            "batter",
            "baserunners",
        )
    )

    return [
        name
        for name, pattern in LEXICAL_PATTERNS
        if pattern.search(searchable)
    ]


def tree_hash(files: list[Path], root: Path) -> str:
    pairs = [
        f"{path.resolve().relative_to(root.resolve()).as_posix()}|"
        f"{sha256_file(path)}"
        for path in sorted(files)
    ]

    return sha256_bytes("\n".join(pairs).encode("utf-8"))


def normalize_hitter(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "displayName": str(row.get("displayName") or ""),
        "rawIdentity": str(row.get("rawIdentity") or ""),
        "position": str(row.get("position") or ""),
        "substitutionPrefix": str(row.get("substitutionPrefix") or ""),
        "atBats": safe_int(row.get("atBats")),
        "runs": safe_int(row.get("runs")),
        "hits": safe_int(row.get("hits")),
        "runsBattedIn": safe_int(row.get("runsBattedIn")),
        "displayedBattingAverage": str(
            row.get("displayedBattingAverage") or ""
        ),
        "sourceRowIndex": safe_int(row.get("sourceRowIndex")),
    }


def normalize_pitcher(
    row: dict[str, Any],
    row_index: int,
) -> dict[str, Any]:
    return {
        "displayName": str(row.get("displayName") or ""),
        "rawIdentity": str(row.get("rawIdentity") or ""),
        "usageRowRole": "starter_row" if row_index == 0 else "relief_row",
        "substitutionPrefix": str(row.get("substitutionPrefix") or ""),
        "decision": str(row.get("decision") or ""),
        "inningsPitched": str(row.get("inningsPitched") or ""),
        "inningsPitchedOuts": safe_int(row.get("inningsPitchedOuts")),
        "hitsAllowed": safe_int(row.get("hitsAllowed")),
        "runsAllowed": safe_int(row.get("runsAllowed")),
        "earnedRuns": safe_int(row.get("earnedRuns")),
        "homeRunsAllowed": safe_int(row.get("homeRunsAllowed")),
        "walks": safe_int(row.get("walks")),
        "strikeouts": safe_int(row.get("strikeouts")),
        "pitchCount": safe_int(row.get("pitchCount")),
        "displayedEarnedRunAverage": str(
            row.get("displayedEarnedRunAverage") or ""
        ),
        "sourceRowIndex": safe_int(row.get("sourceRowIndex")),
    }


def new_team_summary(name: str) -> dict[str, Any]:
    return {
        "teamName": name,
        "games": 0,
        "wins": 0,
        "losses": 0,
        "runsScored": 0,
        "runsAllowed": 0,
        "hits": 0,
        "hitsAllowed": 0,
        "errors": 0,
        "opponentErrors": 0,
        "oneRunGames": 0,
        "extraInningGames": 0,
    }


def update_league_team(
    summary: dict[str, Any],
    *,
    runs_for: int,
    runs_against: int,
    hits_for: int,
    hits_against: int,
    errors_for: int,
    errors_against: int,
    extra_innings: bool,
) -> None:
    summary["games"] += 1
    summary["runsScored"] += runs_for
    summary["runsAllowed"] += runs_against
    summary["hits"] += hits_for
    summary["hitsAllowed"] += hits_against
    summary["errors"] += errors_for
    summary["opponentErrors"] += errors_against

    if runs_for > runs_against:
        summary["wins"] += 1
    else:
        summary["losses"] += 1

    if abs(runs_for - runs_against) == 1:
        summary["oneRunGames"] += 1

    if extra_innings:
        summary["extraInningGames"] += 1


def aggregate_hitter(
    totals: dict[str, dict[str, Any]],
    row: dict[str, Any],
) -> None:
    name = str(row.get("displayName") or "").strip()

    if not name:
        return

    target = totals.setdefault(
        name,
        {
            "displayName": name,
            "gamesWithRow": 0,
            "starterRowCount": 0,
            "substitutionRowCount": 0,
            "positions": set(),
            "atBats": 0,
            "runs": 0,
            "hits": 0,
            "runsBattedIn": 0,
        },
    )

    target["gamesWithRow"] += 1

    if str(row.get("substitutionPrefix") or "").strip():
        target["substitutionRowCount"] += 1
    else:
        target["starterRowCount"] += 1

    position = str(row.get("position") or "").strip()

    if position:
        target["positions"].add(position)

    for field in ("atBats", "runs", "hits", "runsBattedIn"):
        target[field] += safe_int(row.get(field))


def aggregate_pitcher(
    totals: dict[str, dict[str, Any]],
    row: dict[str, Any],
    row_index: int,
) -> None:
    name = str(row.get("displayName") or "").strip()

    if not name:
        return

    target = totals.setdefault(
        name,
        {
            "displayName": name,
            "appearances": 0,
            "starterRowAppearances": 0,
            "reliefRowAppearances": 0,
            "inningsPitchedOuts": 0,
            "hitsAllowed": 0,
            "runsAllowed": 0,
            "earnedRuns": 0,
            "homeRunsAllowed": 0,
            "walks": 0,
            "strikeouts": 0,
            "pitchCount": 0,
            "decisions": Counter(),
        },
    )

    target["appearances"] += 1

    if row_index == 0:
        target["starterRowAppearances"] += 1
    else:
        target["reliefRowAppearances"] += 1

    for field in (
        "inningsPitchedOuts",
        "hitsAllowed",
        "runsAllowed",
        "earnedRuns",
        "homeRunsAllowed",
        "walks",
        "strikeouts",
        "pitchCount",
    ):
        target[field] += safe_int(row.get(field))

    decision = str(row.get("decision") or "").strip()

    if decision:
        target["decisions"][decision] += 1


def discover_reusable_assets(
    repo_root: Path,
    season: str,
) -> list[dict[str, Any]]:
    roots = (
        repo_root / "baseball" / "parser",
        repo_root / "docs" / "baseball",
        (
            repo_root
            / "data"
            / "baseball"
            / "parsed"
            / "strat365"
            / season
            / "post-draft"
        ),
    )

    pattern = re.compile(
        r"aquarium|comiskey|postdraft|post-draft|"
        r"lineup|bullpen|waiver|injury|defen|"
        r"substitution|roster|draft",
        re.IGNORECASE,
    )

    rows: list[dict[str, Any]] = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix.lower() not in {".py", ".json", ".md"}
                or not pattern.search(path.name)
            ):
                continue

            rows.append(
                {
                    "path": relative_to_repo(repo_root, path),
                    "sha256": sha256_file(path),
                    "byteCount": path.stat().st_size,
                }
            )

    return sorted(rows, key=lambda row: row["path"])


def build(arguments: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(arguments.repo_root).resolve()
    season = str(arguments.season)
    league_id = str(arguments.league_id)
    through_date = str(arguments.through_date)
    team_name = str(arguments.team_name)

    canonical_root = (
        repo_root
        / "data"
        / "baseball"
        / "canonical"
        / "strat365"
        / season
        / "season-ingestion"
        / f"league-{league_id}"
    )

    output_root = (
        repo_root
        / "data"
        / "baseball"
        / "parsed"
        / "strat365"
        / season
        / "season-review"
        / f"league-{league_id}"
        / through_date
    )

    dataset_path = output_root / "team-review-dataset-v0.json"
    event_ledger_path = output_root / "league-event-ledger-v0.jsonl"
    source_manifest_path = output_root / "source-manifest-v0.json"

    if not canonical_root.exists():
        raise ValueError(f"Canonical root is missing: {canonical_root}")

    date_directories = sorted(
        path
        for path in canonical_root.iterdir()
        if (
            path.is_dir()
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.name)
            and path.name <= through_date
        )
    )

    if len(date_directories) != arguments.expected_date_count:
        raise ValueError(
            "Canonical date count differs: "
            f"expected={arguments.expected_date_count}; "
            f"actual={len(date_directories)}"
        )

    source_files: list[Path] = []
    source_date_rows: list[dict[str, Any]] = []
    all_game_index: list[dict[str, Any]] = []
    team_games: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []

    team_hitter_totals: dict[str, dict[str, Any]] = {}
    team_pitcher_totals: dict[str, dict[str, Any]] = {}
    league_team_totals: dict[str, dict[str, Any]] = {}

    league_lexical_counts: Counter[str] = Counter()
    team_batting_lexical_counts: Counter[str] = Counter()
    team_fielding_lexical_counts: Counter[str] = Counter()

    team_game_ids: set[str] = set()
    all_game_ids: set[str] = set()

    team_wins = 0
    team_losses = 0
    team_runs_for = 0
    team_runs_against = 0
    team_hits_for = 0
    team_hits_against = 0
    team_errors = 0
    opponent_errors = 0
    team_one_run_games = 0
    team_extra_inning_games = 0
    team_event_count = 0
    team_control_row_count = 0

    for date_directory in date_directories:
        package_files = sorted(
            path
            for path in date_directory.rglob("*")
            if path.is_file()
        )

        source_files.extend(package_files)

        games_root = date_directory / "games"
        promotion_manifest_path = (
            date_directory / "promotion-manifest-v0.json"
        )

        if not games_root.exists():
            raise ValueError(
                f"Canonical games directory is missing: {games_root}"
            )

        if not promotion_manifest_path.exists():
            raise ValueError(
                "Promotion manifest is missing: "
                f"{promotion_manifest_path}"
            )

        game_files = sorted(games_root.glob("*.json"))

        if (
            len(package_files)
            != arguments.expected_package_files_per_date
        ):
            raise ValueError(
                f"{date_directory.name} package file count differs: "
                f"expected={arguments.expected_package_files_per_date}; "
                f"actual={len(package_files)}"
            )

        if len(game_files) != arguments.expected_games_per_date:
            raise ValueError(
                f"{date_directory.name} game count differs: "
                f"expected={arguments.expected_games_per_date}; "
                f"actual={len(game_files)}"
            )

        source_date_rows.append(
            {
                "leagueDate": date_directory.name,
                "canonicalPackagePath": relative_to_repo(
                    repo_root,
                    date_directory,
                ),
                "packageFileCount": len(package_files),
                "gameFileCount": len(game_files),
                "packageTreeSha256": tree_hash(
                    package_files,
                    date_directory,
                ),
                "promotionManifestSha256": sha256_file(
                    promotion_manifest_path
                ),
            }
        )

        for game_file in game_files:
            game = json.loads(game_file.read_text(encoding="utf-8"))

            game_id = str(game.get("gameId") or "").strip()
            league_date = str(game.get("leagueDate") or "").strip()

            if not game_id:
                raise ValueError(
                    f"Canonical game lacks gameId: {game_file}"
                )

            if not league_date:
                raise ValueError(
                    f"Canonical game lacks leagueDate: {game_file}"
                )

            if game_id in all_game_ids:
                raise ValueError(
                    f"Duplicate canonical gameId: {game_id}"
                )

            all_game_ids.add(game_id)

            away_team = dict(game.get("awayTeam") or {})
            home_team = dict(game.get("homeTeam") or {})

            away_name = str(away_team.get("name") or "").strip()
            home_name = str(home_team.get("name") or "").strip()

            if not away_name or not home_name:
                raise ValueError(
                    f"Canonical game lacks team identity: {game_file}"
                )

            away_runs = safe_int(away_team.get("runs"))
            home_runs = safe_int(home_team.get("runs"))
            away_hits = safe_int(away_team.get("hits"))
            home_hits = safe_int(home_team.get("hits"))
            away_errors = safe_int(away_team.get("errors"))
            home_errors = safe_int(home_team.get("errors"))
            extra_innings = bool(game.get("extraInnings"))

            away_summary = league_team_totals.setdefault(
                away_name,
                new_team_summary(away_name),
            )

            home_summary = league_team_totals.setdefault(
                home_name,
                new_team_summary(home_name),
            )

            update_league_team(
                away_summary,
                runs_for=away_runs,
                runs_against=home_runs,
                hits_for=away_hits,
                hits_against=home_hits,
                errors_for=away_errors,
                errors_against=home_errors,
                extra_innings=extra_innings,
            )

            update_league_team(
                home_summary,
                runs_for=home_runs,
                runs_against=away_runs,
                hits_for=home_hits,
                hits_against=away_hits,
                errors_for=home_errors,
                errors_against=away_errors,
                extra_innings=extra_innings,
            )

            source_game_path = relative_to_repo(repo_root, game_file)

            all_game_index.append(
                {
                    "leagueDate": league_date,
                    "gameId": game_id,
                    "sourceGamePath": source_game_path,
                    "sourceGameSha256": sha256_file(game_file),
                    "awayTeam": away_name,
                    "homeTeam": home_name,
                    "awayRuns": away_runs,
                    "homeRuns": home_runs,
                    "winnerTeam": str(game.get("winnerTeam") or ""),
                    "loserTeam": str(game.get("loserTeam") or ""),
                    "innings": safe_int(game.get("innings")),
                    "extraInnings": extra_innings,
                    "playByPlayEventCount": safe_int(
                        (game.get("playByPlay") or {}).get("eventCount")
                    ),
                    "playByPlayControlCount": safe_int(
                        (game.get("playByPlay") or {}).get("controlCount")
                    ),
                }
            )

            team_side: str | None = None

            if away_name == team_name:
                team_side = "away"
            elif home_name == team_name:
                team_side = "home"

            play_by_play = dict(game.get("playByPlay") or {})
            ordered_records = list(
                play_by_play.get("orderedRecords") or []
            )

            team_game_lexical_counts: Counter[str] = Counter()

            for fallback_sequence, record_value in enumerate(
                ordered_records,
                start=1,
            ):
                record = dict(record_value or {})
                sequence = safe_int(record.get("sequence"))

                if sequence == 0:
                    sequence = fallback_sequence

                half = str(record.get("half") or "").strip()
                normalized_half = half.lower()

                if normalized_half.startswith("top"):
                    batting_team = away_name
                    fielding_team = home_name
                elif normalized_half.startswith("bottom"):
                    batting_team = home_name
                    fielding_team = away_name
                else:
                    batting_team = ""
                    fielding_team = ""

                if batting_team == team_name:
                    team_perspective = "team_batting"
                elif fielding_team == team_name:
                    team_perspective = "team_fielding"
                else:
                    team_perspective = "none"

                tags = lexical_tags(record)

                for tag in tags:
                    league_lexical_counts[tag] += 1

                    if team_perspective == "team_batting":
                        team_batting_lexical_counts[tag] += 1
                        team_game_lexical_counts[
                            f"batting:{tag}"
                        ] += 1
                    elif team_perspective == "team_fielding":
                        team_fielding_lexical_counts[tag] += 1
                        team_game_lexical_counts[
                            f"fielding:{tag}"
                        ] += 1

                if team_perspective != "none":
                    team_event_count += 1

                    if str(record.get("recordType") or "") == "control":
                        team_control_row_count += 1

                event_rows.append(
                    {
                        "schemaVersion": (
                            "strat365-review-event-ledger-row-v0"
                        ),
                        "eventKey": (
                            f"{league_date}:{game_id}:{sequence}"
                        ),
                        "leagueDate": league_date,
                        "gameId": game_id,
                        "sourceGamePath": source_game_path,
                        "sequence": sequence,
                        "inning": safe_int(record.get("inning")),
                        "half": half,
                        "battingTeam": batting_team,
                        "fieldingTeam": fielding_team,
                        "teamPerspective": team_perspective,
                        "recordType": str(
                            record.get("recordType") or ""
                        ),
                        "controlType": str(
                            record.get("controlType") or ""
                        ),
                        "outsBefore": safe_int(
                            record.get("outsBefore")
                        ),
                        "outsBasesBefore": str(
                            record.get("outsBasesBefore") or ""
                        ),
                        "occupiedBasesBefore": list(
                            record.get("occupiedBasesBefore") or []
                        ),
                        "batter": normalized_text(
                            record.get("batter")
                        ),
                        "baserunners": normalized_text(
                            record.get("baserunners")
                        ),
                        "result": normalized_text(
                            record.get("result")
                        ),
                        "text": normalized_text(record.get("text")),
                        "rawText": normalized_text(
                            record.get("rawText")
                        ),
                        "details": record.get("details"),
                        "miscellaneous": normalized_text(
                            record.get("miscellaneous")
                        ),
                        "lexicalTags": tags,
                    }
                )

            if team_side is None:
                continue

            if game_id in team_game_ids:
                raise ValueError(
                    f"Duplicate team gameId: {game_id}"
                )

            team_game_ids.add(game_id)

            if team_side == "away":
                opponent_name = home_name
                runs_for = away_runs
                runs_against = home_runs
                hits_for = away_hits
                hits_against = home_hits
                errors_for = away_errors
                errors_against = home_errors
                hitter_rows = list(game.get("awayHitters") or [])
                pitcher_rows = list(game.get("awayPitchers") or [])
            else:
                opponent_name = away_name
                runs_for = home_runs
                runs_against = away_runs
                hits_for = home_hits
                hits_against = away_hits
                errors_for = home_errors
                errors_against = away_errors
                hitter_rows = list(game.get("homeHitters") or [])
                pitcher_rows = list(game.get("homePitchers") or [])

            result = "W" if runs_for > runs_against else "L"

            if result == "W":
                team_wins += 1
            else:
                team_losses += 1

            team_runs_for += runs_for
            team_runs_against += runs_against
            team_hits_for += hits_for
            team_hits_against += hits_against
            team_errors += errors_for
            opponent_errors += errors_against

            if abs(runs_for - runs_against) == 1:
                team_one_run_games += 1

            if extra_innings:
                team_extra_inning_games += 1

            normalized_hitters = [
                normalize_hitter(dict(row or {}))
                for row in hitter_rows
            ]

            normalized_pitchers = [
                normalize_pitcher(dict(row or {}), index)
                for index, row in enumerate(pitcher_rows)
            ]

            for row in hitter_rows:
                aggregate_hitter(
                    team_hitter_totals,
                    dict(row or {}),
                )

            for index, row in enumerate(pitcher_rows):
                aggregate_pitcher(
                    team_pitcher_totals,
                    dict(row or {}),
                    index,
                )

            team_games.append(
                {
                    "leagueDate": league_date,
                    "gameId": game_id,
                    "sourceGamePath": source_game_path,
                    "sourceGameSha256": sha256_file(game_file),
                    "homeAway": team_side,
                    "opponent": opponent_name,
                    "result": result,
                    "runsFor": runs_for,
                    "runsAgainst": runs_against,
                    "runDifferential": runs_for - runs_against,
                    "hitsFor": hits_for,
                    "hitsAgainst": hits_against,
                    "errorsFor": errors_for,
                    "errorsAgainst": errors_against,
                    "innings": safe_int(game.get("innings")),
                    "extraInnings": extra_innings,
                    "winnerTeam": str(game.get("winnerTeam") or ""),
                    "loserTeam": str(game.get("loserTeam") or ""),
                    "decisionSummaryText": str(
                        game.get("decisionSummaryText") or ""
                    ),
                    "startingPitcherRow": (
                        normalized_pitchers[0]
                        if normalized_pitchers
                        else None
                    ),
                    "reliefPitcherRows": normalized_pitchers[1:],
                    "hitterRows": normalized_hitters,
                    "pitcherRows": normalized_pitchers,
                    "playByPlayEventCount": len(ordered_records),
                    "playByPlayControlCount": safe_int(
                        play_by_play.get("controlCount")
                    ),
                    "playByPlayUnknownControlCount": safe_int(
                        play_by_play.get("unknownControlCount")
                    ),
                    "lexicalEventCounts": dict(
                        sorted(team_game_lexical_counts.items())
                    ),
                }
            )

    expected_league_games = arguments.expected_league_game_count
    expected_team_games = arguments.expected_team_game_count

    if len(all_game_index) != expected_league_games:
        raise ValueError(
            "League game count differs: "
            f"expected={expected_league_games}; "
            f"actual={len(all_game_index)}"
        )

    if len(team_games) != expected_team_games:
        raise ValueError(
            "Team game count differs: "
            f"expected={expected_team_games}; "
            f"actual={len(team_games)}"
        )

    if len(team_game_ids) != expected_team_games:
        raise ValueError(
            "Unique team game count differs: "
            f"expected={expected_team_games}; "
            f"actual={len(team_game_ids)}"
        )

    all_game_index.sort(
        key=lambda row: (
            row["leagueDate"],
            safe_int(row["gameId"]),
        )
    )

    team_games.sort(
        key=lambda row: (
            row["leagueDate"],
            safe_int(row["gameId"]),
        )
    )

    event_rows.sort(
        key=lambda row: (
            row["leagueDate"],
            safe_int(row["gameId"]),
            row["sequence"],
        )
    )

    hitter_rows_out: list[dict[str, Any]] = []

    for row in team_hitter_totals.values():
        output_row = dict(row)
        output_row["positions"] = sorted(output_row["positions"])
        hitter_rows_out.append(output_row)

    hitter_rows_out.sort(
        key=lambda row: (
            -row["atBats"],
            -row["hits"],
            row["displayName"],
        )
    )

    pitcher_rows_out: list[dict[str, Any]] = []

    for row in team_pitcher_totals.values():
        output_row = dict(row)
        output_row["decisions"] = dict(
            sorted(output_row["decisions"].items())
        )
        pitcher_rows_out.append(output_row)

    pitcher_rows_out.sort(
        key=lambda row: (
            -row["inningsPitchedOuts"],
            -row["appearances"],
            row["displayName"],
        )
    )

    league_team_rows: list[dict[str, Any]] = []

    for row in league_team_totals.values():
        output_row = dict(row)
        output_row["runDifferential"] = (
            output_row["runsScored"]
            - output_row["runsAllowed"]
        )
        league_team_rows.append(output_row)

    league_team_rows.sort(
        key=lambda row: (
            -row["wins"],
            -row["runDifferential"],
            row["teamName"],
        )
    )

    reusable_assets = discover_reusable_assets(
        repo_root,
        season,
    )

    source_tree_sha256 = tree_hash(
        source_files,
        canonical_root,
    )

    builder_path = Path(__file__).resolve()
    builder_hash = sha256_file(builder_path)

    event_payload = jsonl_bytes(event_rows)
    event_hash = sha256_bytes(event_payload)

    dataset = {
        "schemaVersion": "strat365-team-review-dataset-v0",
        "scope": {
            "season": int(season),
            "leagueId": int(league_id),
            "throughDate": through_date,
            "teamName": team_name,
            "canonicalDateCount": len(date_directories),
            "expectedLeagueGameCount": expected_league_games,
            "expectedTeamGameCount": expected_team_games,
        },
        "sourceAuthority": {
            "canonicalLeagueRoot": relative_to_repo(
                repo_root,
                canonical_root,
            ),
            "canonicalSourceTreeSha256": source_tree_sha256,
            "builderScript": relative_to_repo(
                repo_root,
                builder_path,
            ),
            "builderScriptSha256": builder_hash,
            "eventLedger": relative_to_repo(
                repo_root,
                event_ledger_path,
            ),
            "eventLedgerSha256": event_hash,
            "semanticPolicy": (
                "Scoreboard, player rows and ordered play-by-play "
                "records are canonical. Lexical tags identify explicit "
                "phrases only and are not final tactical judgments."
            ),
        },
        "counts": {
            "canonicalDates": len(date_directories),
            "leagueGames": len(all_game_index),
            "teamGames": len(team_games),
            "leagueTeams": len(league_team_rows),
            "eventLedgerRows": len(event_rows),
            "teamPerspectiveEventRows": team_event_count,
            "teamPerspectiveControlRows": team_control_row_count,
            "teamHitterTotalRows": len(hitter_rows_out),
            "teamPitcherTotalRows": len(pitcher_rows_out),
            "reusableBieAssets": len(reusable_assets),
        },
        "teamSummary": {
            "teamName": team_name,
            "games": len(team_games),
            "wins": team_wins,
            "losses": team_losses,
            "record": f"{team_wins}-{team_losses}",
            "runsFor": team_runs_for,
            "runsAgainst": team_runs_against,
            "runDifferential": (
                team_runs_for - team_runs_against
            ),
            "hitsFor": team_hits_for,
            "hitsAgainst": team_hits_against,
            "errors": team_errors,
            "opponentErrors": opponent_errors,
            "oneRunGames": team_one_run_games,
            "extraInningGames": team_extra_inning_games,
        },
        "lexicalEventSummary": {
            "league": dict(sorted(league_lexical_counts.items())),
            "teamBatting": dict(
                sorted(team_batting_lexical_counts.items())
            ),
            "teamFielding": dict(
                sorted(team_fielding_lexical_counts.items())
            ),
        },
        "reviewCoverage": {
            "scoreboard": True,
            "hitterBoxRows": True,
            "pitcherBoxRows": True,
            "pitcherDecisionRows": True,
            "orderedPlayByPlay": True,
            "inningAndHalf": True,
            "outsBefore": True,
            "occupiedBasesBefore": True,
            "batterText": True,
            "baserunnerText": True,
            "substitutionPrefixes": True,
            "rawEventText": True,
            "lexicalTacticalFlags": True,
            "finalTacticalClassification": False,
            "draftProjectionComparisonJoined": False,
            "rosterAndWaiverEvidenceJoined": False,
        },
        "sourceDates": source_date_rows,
        "leagueTeamSummaries": league_team_rows,
        "allGameIndex": all_game_index,
        "teamGames": team_games,
        "teamHitterTotals": hitter_rows_out,
        "teamPitcherTotals": pitcher_rows_out,
        "reusableBieAssets": reusable_assets,
        "knownInterpretationLimits": [
            (
                "The first pitcher row is labeled starter_row only "
                "because it is first in the canonical pitching table."
            ),
            (
                "Lexical event tags are evidence-locator signals, "
                "not success, failure, cost or managerial-quality "
                "classifications."
            ),
            (
                "Baserunning and extra-base decisions require a "
                "subsequent state-transition classifier using outs "
                "and occupied-bases evidence."
            ),
            (
                "Roster, card, defense, injury, draft and waiver "
                "artifacts are inventoried but not yet joined."
            ),
        ],
    }

    dataset_payload = json_bytes(dataset)
    dataset_hash = sha256_bytes(dataset_payload)

    source_manifest = {
        "schemaVersion": (
            "strat365-team-review-source-manifest-v0"
        ),
        "scope": dataset["scope"],
        "canonicalSourceTreeSha256": source_tree_sha256,
        "builder": {
            "path": relative_to_repo(repo_root, builder_path),
            "sha256": builder_hash,
        },
        "sourceDates": source_date_rows,
        "sourceFileCount": len(source_files),
        "outputs": {
            "dataset": {
                "path": relative_to_repo(
                    repo_root,
                    dataset_path,
                ),
                "sha256": dataset_hash,
                "byteCount": len(dataset_payload),
            },
            "eventLedger": {
                "path": relative_to_repo(
                    repo_root,
                    event_ledger_path,
                ),
                "sha256": event_hash,
                "byteCount": len(event_payload),
                "rowCount": len(event_rows),
            },
        },
        "reusableBieAssets": reusable_assets,
    }

    source_manifest_payload = json_bytes(source_manifest)
    source_manifest_hash = sha256_bytes(
        source_manifest_payload
    )

    files_modified = 0
    files_modified += write_if_changed(
        event_ledger_path,
        event_payload,
    )
    files_modified += write_if_changed(
        dataset_path,
        dataset_payload,
    )
    files_modified += write_if_changed(
        source_manifest_path,
        source_manifest_payload,
    )

    return {
        "canonicalDateCount": len(date_directories),
        "leagueGameCount": len(all_game_index),
        "teamGameCount": len(team_games),
        "leagueTeamCount": len(league_team_rows),
        "teamRecord": f"{team_wins}-{team_losses}",
        "teamRunsFor": team_runs_for,
        "teamRunsAgainst": team_runs_against,
        "teamRunDifferential": (
            team_runs_for - team_runs_against
        ),
        "eventLedgerRowCount": len(event_rows),
        "teamEventRowCount": team_event_count,
        "teamHitterTotalRowCount": len(hitter_rows_out),
        "teamPitcherTotalRowCount": len(pitcher_rows_out),
        "reusableBieAssetCount": len(reusable_assets),
        "sourceTreeSha256": source_tree_sha256,
        "datasetPath": relative_to_repo(
            repo_root,
            dataset_path,
        ),
        "datasetSha256": dataset_hash,
        "eventLedgerPath": relative_to_repo(
            repo_root,
            event_ledger_path,
        ),
        "eventLedgerSha256": event_hash,
        "sourceManifestPath": relative_to_repo(
            repo_root,
            source_manifest_path,
        ),
        "sourceManifestSha256": source_manifest_hash,
        "filesModified": files_modified,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--season", required=True)
    parser.add_argument("--league-id", required=True)
    parser.add_argument("--through-date", required=True)
    parser.add_argument("--team-name", required=True)
    parser.add_argument(
        "--expected-date-count",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--expected-games-per-date",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--expected-package-files-per-date",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--expected-league-game-count",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--expected-team-game-count",
        required=True,
        type=int,
    )
    return parser.parse_args()


def main() -> int:
    try:
        result = build(parse_arguments())
    except Exception as exc:
        print("# RESULT SUMMARY")
        print("TEAM_REVIEW_DATASET_BUILD: FAIL")
        print("FAILURE_COUNT: 1")
        print(f"FAILURE_DETAIL: {exc}")
        print("FILES_MODIFIED_BY_BUILDER: 0")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 1

    print("# RESULT SUMMARY")
    print("TEAM_REVIEW_DATASET_BUILD: PASS")
    print(
        "CANONICAL_DATE_COUNT: "
        f"{result['canonicalDateCount']}"
    )
    print(
        "LEAGUE_GAME_COUNT: "
        f"{result['leagueGameCount']}"
    )
    print(
        "TEAM_GAME_COUNT: "
        f"{result['teamGameCount']}"
    )
    print(
        "LEAGUE_TEAM_COUNT: "
        f"{result['leagueTeamCount']}"
    )
    print(f"TEAM_RECORD: {result['teamRecord']}")
    print(f"TEAM_RUNS_FOR: {result['teamRunsFor']}")
    print(
        "TEAM_RUNS_AGAINST: "
        f"{result['teamRunsAgainst']}"
    )
    print(
        "TEAM_RUN_DIFFERENTIAL: "
        f"{result['teamRunDifferential']}"
    )
    print(
        "LEAGUE_EVENT_LEDGER_ROW_COUNT: "
        f"{result['eventLedgerRowCount']}"
    )
    print(
        "TEAM_EVENT_ROW_COUNT: "
        f"{result['teamEventRowCount']}"
    )
    print(
        "TEAM_HITTER_TOTAL_ROW_COUNT: "
        f"{result['teamHitterTotalRowCount']}"
    )
    print(
        "TEAM_PITCHER_TOTAL_ROW_COUNT: "
        f"{result['teamPitcherTotalRowCount']}"
    )
    print(
        "REUSABLE_BIE_ASSET_COUNT: "
        f"{result['reusableBieAssetCount']}"
    )
    print(
        "CANONICAL_SOURCE_TREE_SHA256: "
        f"{result['sourceTreeSha256']}"
    )
    print(f"DATASET_PATH: {result['datasetPath']}")
    print(f"DATASET_SHA256: {result['datasetSha256']}")
    print(
        "EVENT_LEDGER_PATH: "
        f"{result['eventLedgerPath']}"
    )
    print(
        "EVENT_LEDGER_SHA256: "
        f"{result['eventLedgerSha256']}"
    )
    print(
        "SOURCE_MANIFEST_PATH: "
        f"{result['sourceManifestPath']}"
    )
    print(
        "SOURCE_MANIFEST_SHA256: "
        f"{result['sourceManifestSha256']}"
    )
    print(
        "FILES_MODIFIED_BY_BUILDER: "
        f"{result['filesModified']}"
    )
    print("FAILURE_COUNT: 0")
    print("FAILURE_DETAIL: none")
    print("LIVE_REQUESTS_EXECUTED: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
