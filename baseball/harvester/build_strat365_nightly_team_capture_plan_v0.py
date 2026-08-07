#!/usr/bin/env python3
"""Build a Strat365 nightly three-game capture plan from a captured team schedule.

v0 contract:
- run-spec is series-scoped: 2 teams, 3 games, 1 series.
- schedule metadata points to an already captured /team/schedule/{teamId} response.
- target run and template run share the subject team identity.
- the proven template plan supplies the exact plan schema; this constructor
  replaces only run identity, opponent identity, and discovered game identity.
- no network access is performed.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


GAME_HREF_RE = re.compile(r"/game/(?P<league>\d+)/(?P<game>\d+)(?:[/?#]|$)", re.I)
TEAM_HREF_RE = re.compile(r"/team/(?P<team>\d+)(?:[/?#]|$)", re.I)
SCHEDULE_TEAM_RE = re.compile(r"/team/schedule/(?P<team>\d+)(?:[/?#]|$)", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def repository_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


class ScheduleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, Any]] = []
        self._row: dict[str, Any] | None = None
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag.lower() == "tr":
            self._row = {"text": [], "anchors": []}
        elif tag.lower() == "a" and self._row is not None:
            self._anchor_href = attrs_dict.get("href", "")
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._row is not None:
            self._row["text"].append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "a" and self._row is not None and self._anchor_href is not None:
            self._row["anchors"].append(
                {
                    "href": self._anchor_href,
                    "text": " ".join(" ".join(self._anchor_text).split()),
                }
            )
            self._anchor_href = None
            self._anchor_text = []
        elif lower == "tr" and self._row is not None:
            self._row["normalizedText"] = " ".join(
                " ".join(self._row["text"]).split()
            )
            self.rows.append(self._row)
            self._row = None


def date_tokens(iso_date: str) -> set[str]:
    parsed = date.fromisoformat(iso_date)
    return {
        f"{parsed.month}/{parsed.day}",
        f"{parsed.month}/{parsed.day:02d}",
        f"{parsed.month:02d}/{parsed.day}",
        f"{parsed.month:02d}/{parsed.day:02d}",
    }


def discover_three_games(
    *,
    html_text: str,
    league_id: str,
    league_date: str,
    subject_team_id: str,
    opponent_team_id: str,
) -> list[str]:
    parser = ScheduleParser()
    parser.feed(html_text)

    tokens = date_tokens(league_date)
    discovered: list[str] = []

    for row in parser.rows:
        text = str(row.get("normalizedText") or "")
        if not any(token in text for token in tokens):
            continue

        row_game_ids: set[str] = set()
        row_team_ids: set[str] = set()

        for anchor in row.get("anchors") or []:
            href = str(anchor.get("href") or "")

            game_match = GAME_HREF_RE.search(href)
            if game_match and game_match.group("league") == league_id:
                row_game_ids.add(game_match.group("game"))

            team_match = TEAM_HREF_RE.search(href)
            if team_match:
                row_team_ids.add(team_match.group("team"))

        if opponent_team_id not in row_team_ids:
            continue

        if len(row_game_ids) == 1:
            discovered.append(next(iter(row_game_ids)))

    unique = sorted(set(discovered), key=int)

    if len(unique) != 3:
        raise ValueError(
            "Expected exactly 3 completed schedule games for "
            f"{league_date} vs opponent {opponent_team_id}; found {len(unique)}."
        )

    return unique


def collect_template_game_ids(plan: Any, league_id: str) -> list[str]:
    found: set[str] = set()

    def walk(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                walk(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                walk(child, key)
        elif isinstance(value, str):
            if key and key.lower() in {"gameid", "game_id"} and value.isdigit():
                found.add(value)
            for match in GAME_HREF_RE.finditer(value):
                if match.group("league") == league_id:
                    found.add(match.group("game"))
        elif isinstance(value, int):
            if key and key.lower() in {"gameid", "game_id"}:
                found.add(str(value))

    walk(plan)
    return sorted(found, key=int)


def transform_plan(
    *,
    value: Any,
    old_league: str,
    new_league: str,
    old_date: str,
    new_date: str,
    old_run_rel: str,
    new_run_rel: str,
    team_map: dict[str, str],
    game_map: dict[str, str],
    key: str | None = None,
) -> Any:
    if isinstance(value, dict):
        return {
            child_key: transform_plan(
                value=child,
                old_league=old_league,
                new_league=new_league,
                old_date=old_date,
                new_date=new_date,
                old_run_rel=old_run_rel,
                new_run_rel=new_run_rel,
                team_map=team_map,
                game_map=game_map,
                key=str(child_key),
            )
            for child_key, child in value.items()
        }

    if isinstance(value, list):
        return [
            transform_plan(
                value=child,
                old_league=old_league,
                new_league=new_league,
                old_date=old_date,
                new_date=new_date,
                old_run_rel=old_run_rel,
                new_run_rel=new_run_rel,
                team_map=team_map,
                game_map=game_map,
                key=key,
            )
            for child in value
        ]

    if isinstance(value, int):
        text = str(value)
        if key and key.lower() in {"gameid", "game_id"} and text in game_map:
            return int(game_map[text])
        return value

    if not isinstance(value, str):
        return value

    if key and key.lower() in {"gameid", "game_id"} and value in game_map:
        return game_map[value]

    result = value

    if old_run_rel and old_run_rel in result:
        result = result.replace(old_run_rel, new_run_rel)

    if old_date in result:
        result = result.replace(old_date, new_date)

    result = result.replace(
        f"/game/{old_league}/",
        f"/game/{new_league}/",
    )

    if result == old_league:
        result = new_league

    for old_team, new_team in team_map.items():
        if result == old_team:
            result = new_team
        result = result.replace(f"/team/{old_team}", f"/team/{new_team}")
        result = result.replace(f"team-{old_team}", f"team-{new_team}")

    for old_game, new_game in game_map.items():
        if result == old_game:
            result = new_game
        result = result.replace(
            f"/{old_game}/",
            f"/{new_game}/",
        )
        result = re.sub(
            rf"(?<!\d){re.escape(old_game)}(?!\d)",
            new_game,
            result,
        )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--run-directory", required=True)
    parser.add_argument("--schedule-metadata", required=True)
    parser.add_argument("--template-run-directory", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_directory = Path(args.run_directory).resolve()
    schedule_metadata_path = Path(args.schedule_metadata).resolve()
    template_run_directory = Path(args.template_run_directory).resolve()
    output_path = Path(args.output).resolve()

    run_spec = load_json(run_directory / "run-spec.json")
    template_spec = load_json(template_run_directory / "run-spec.json")
    template_plan = load_json(template_run_directory / "game-capture-plan.json")
    schedule_metadata = load_json(schedule_metadata_path)

    expected = run_spec["expectedCounts"]
    if (
        int(expected["teamCount"]) != 2
        or int(expected["gameCount"]) != 3
        or int(expected["seriesCount"]) != 1
    ):
        raise ValueError("Nightly constructor requires 2 teams / 3 games / 1 series.")

    target_teams = [str(value) for value in run_spec["teamIds"]]
    template_teams = [str(value) for value in template_spec["teamIds"]]

    requested_url = str(schedule_metadata.get("requestedUrl") or "")
    effective_url = str(schedule_metadata.get("effectiveUrl") or requested_url)
    schedule_match = SCHEDULE_TEAM_RE.search(effective_url)
    if not schedule_match:
        raise ValueError("Schedule metadata does not identify /team/schedule/{teamId}.")

    subject_team = schedule_match.group("team")
    if subject_team not in target_teams:
        raise ValueError("Captured team schedule is outside target run team scope.")

    opponent_team = next(team for team in target_teams if team != subject_team)

    template_subject_candidates = [
        team for team in template_teams if team == subject_team
    ]
    if len(template_subject_candidates) != 1:
        raise ValueError(
            "Template and target must share exactly one subject team identity."
        )

    template_subject = template_subject_candidates[0]
    template_opponent = next(
        team for team in template_teams if team != template_subject
    )

    raw_response_rel = str(schedule_metadata["rawResponsePath"])
    schedule_body_path = repo_root / raw_response_rel
    if not schedule_body_path.is_file():
        raise ValueError(f"Captured team schedule body is missing: {schedule_body_path}")

    html_text = schedule_body_path.read_text(encoding="utf-8", errors="replace")

    new_game_ids = discover_three_games(
        html_text=html_text,
        league_id=str(run_spec["leagueId"]),
        league_date=str(run_spec["leagueDate"]),
        subject_team_id=subject_team,
        opponent_team_id=opponent_team,
    )

    old_game_ids = collect_template_game_ids(
        template_plan,
        str(template_spec["leagueId"]),
    )

    if len(old_game_ids) != 3:
        raise ValueError(
            f"Template plan must contain exactly 3 game identities; found {len(old_game_ids)}."
        )

    team_map = {
        template_subject: subject_team,
        template_opponent: opponent_team,
    }
    game_map = dict(zip(old_game_ids, new_game_ids, strict=True))

    transformed = transform_plan(
        value=copy.deepcopy(template_plan),
        old_league=str(template_spec["leagueId"]),
        new_league=str(run_spec["leagueId"]),
        old_date=str(template_spec["leagueDate"]),
        new_date=str(run_spec["leagueDate"]),
        old_run_rel=repository_relative(template_run_directory, repo_root),
        new_run_rel=repository_relative(run_directory, repo_root),
        team_map=team_map,
        game_map=game_map,
    )

    if int(transformed["expectedGameCount"]) != 3:
        raise ValueError("Transformed plan expectedGameCount is not 3.")
    if int(transformed["discoveredGameCount"]) != 3:
        raise ValueError("Transformed plan discoveredGameCount is not 3.")
    if int(transformed["expectedSeriesCount"]) != 1:
        raise ValueError("Transformed plan expectedSeriesCount is not 1.")
    if int(transformed["discoveredSeriesCount"]) != 1:
        raise ValueError("Transformed plan discoveredSeriesCount is not 1.")
    if int(transformed["plannedRequestCount"]) != 9:
        raise ValueError("Transformed plan plannedRequestCount is not 9.")

    write_json(output_path, transformed)

    print(
        json.dumps(
            {
                "status": "PASS",
                "mode": "CAPTURED_TEAM_SCHEDULE",
                "leagueId": str(run_spec["leagueId"]),
                "leagueDate": str(run_spec["leagueDate"]),
                "subjectTeamId": subject_team,
                "opponentTeamId": opponent_team,
                "discoveredGameCount": 3,
                "discoveredSeriesCount": 1,
                "plannedRequestCount": 9,
                "networkRequestsExecuted": 0,
                "output": repository_relative(output_path, repo_root)
                if output_path.is_relative_to(repo_root)
                else str(output_path),
            },
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())