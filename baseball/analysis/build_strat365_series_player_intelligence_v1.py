#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def upper(value: Any) -> str:
    return str(value or "").strip().upper()


def number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ip_value(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None

    if "." not in text:
        return number(text)

    whole, fraction = text.split(".", 1)

    try:
        innings = int(whole)
        outs = int(fraction)
    except ValueError:
        return None

    if outs not in (0, 1, 2):
        return None

    return innings + (outs / 3.0)


def team_abbreviation(team: dict[str, Any]) -> str:
    manager = team.get("manager") or {}
    label = manager.get("sourceTeamLabel")
    return upper(label)


def normalize_hitter(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("raw") or {}
    metrics = row.get("metrics") or {}

    return {
        "playerName": row.get("name"),
        "teamAbbreviation": upper(row.get("team")),
        "bats": raw.get("B"),
        "position": raw.get("P"),
        "defense": raw.get("Def."),
        "balance": raw.get("BAL"),
        "salary": raw.get("Salary"),
        "AB": metrics.get("AB"),
        "R": metrics.get("R"),
        "H": metrics.get("H"),
        "doubles": metrics.get("2B"),
        "triples": metrics.get("3B"),
        "HR": metrics.get("HR"),
        "RBI": metrics.get("RBI"),
        "BB": metrics.get("BB"),
        "SO": metrics.get("SO"),
        "SB": metrics.get("SB"),
        "CS": metrics.get("CS"),
        "BA": metrics.get("BA"),
        "OBP": metrics.get("OBP"),
        "SLG": metrics.get("SLG"),
        "OPS": metrics.get("OPS"),
    }


def normalize_pitcher(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("raw") or {}
    metrics = row.get("metrics") or {}

    return {
        "playerName": row.get("name"),
        "teamAbbreviation": upper(row.get("team")),
        "throws": raw.get("T"),
        "endurance": raw.get("End."),
        "salary": raw.get("Salary"),
        "G": metrics.get("G"),
        "GS": metrics.get("GS"),
        "W": metrics.get("W"),
        "L": metrics.get("L"),
        "S": metrics.get("S"),
        "BS": metrics.get("BS"),
        "IP": raw.get("IP"),
        "inningsValue": ip_value(raw.get("IP")),
        "H": metrics.get("H"),
        "R": metrics.get("R"),
        "ER": raw.get("ER"),
        "BB": metrics.get("BB"),
        "SO": metrics.get("SO"),
        "HR": metrics.get("HR"),
        "ERA": metrics.get("ERA"),
        "WHIP": metrics.get("WHIP"),
        "unearnedRunsAllowed": row.get("unearnedRunsAllowed"),
    }


def top_hitters(
    rows: list[dict[str, Any]],
    games: int,
) -> tuple[int, list[dict[str, Any]]]:
    minimum_ab = max(20, games)

    eligible = [
        row
        for row in rows
        if number(row.get("AB")) is not None
        and number(row.get("AB")) >= minimum_ab
        and number(row.get("OPS")) is not None
    ]

    eligible.sort(
        key=lambda row: (
            -float(row["OPS"]),
            -float(row.get("AB") or 0),
            str(row.get("playerName") or ""),
        )
    )

    return minimum_ab, eligible[:5]


def top_pitchers(
    rows: list[dict[str, Any]],
    games: int,
) -> tuple[float, list[dict[str, Any]]]:
    minimum_ip = max(10.0, games * 0.5)

    eligible = [
        row
        for row in rows
        if number(row.get("inningsValue")) is not None
        and float(row["inningsValue"]) >= minimum_ip
        and number(row.get("ERA")) is not None
    ]

    eligible.sort(
        key=lambda row: (
            float(row["ERA"]),
            float(row.get("WHIP") or 99),
            -float(row.get("inningsValue") or 0),
            str(row.get("playerName") or ""),
        )
    )

    return minimum_ip, eligible[:5]


def build_side(
    team: dict[str, Any],
    batting: list[dict[str, Any]],
    pitching: list[dict[str, Any]],
    streaks: list[dict[str, Any]],
) -> dict[str, Any]:
    abbreviation = team_abbreviation(team)
    games = int((team.get("derived") or {}).get("games") or 0)

    hitters = [
        normalize_hitter(row)
        for row in batting
        if upper(row.get("team")) == abbreviation
    ]

    pitchers = [
        normalize_pitcher(row)
        for row in pitching
        if upper(row.get("team")) == abbreviation
    ]

    current_streaks = [
        {
            "playerName": row.get("playerName"),
            "teamAbbreviation": upper(row.get("teamAbbreviation")),
            "streakGames": row.get("streakGames"),
            "isCurrent": bool(row.get("isCurrent")),
            "rawCurrentMarker": row.get("rawCurrentMarker"),
        }
        for row in streaks
        if bool(row.get("isCurrent"))
        and upper(row.get("teamAbbreviation")) == abbreviation
    ]

    min_ab, leaders = top_hitters(hitters, games)
    min_ip, pitcher_leaders = top_pitchers(pitchers, games)

    return {
        "teamId": str(team.get("teamId")),
        "teamName": team.get("teamName"),
        "teamAbbreviation": abbreviation,
        "games": games,
        "evidenceStatus": (
            "AVAILABLE"
            if hitters and pitchers
            else "PARTIAL"
        ),
        "counts": {
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "currentHittingStreaks": len(current_streaks),
        },
        "rankingRules": {
            "topHitters": {
                "metric": "OPS",
                "minimumAtBats": min_ab,
            },
            "topPitchers": {
                "metric": "ERA",
                "minimumInnings": round(min_ip, 1),
                "secondaryMetric": "WHIP",
            },
        },
        "topHittersByOPS": leaders,
        "topPitchersByERA": pitcher_leaders,
        "currentHittingStreaks": current_streaks,
        "hitters": hitters,
        "pitchers": pitchers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-intelligence", required=True)
    parser.add_argument("--hitting-streaks", required=True)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--opponent-team-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    intelligence_path = Path(args.league_intelligence)
    streak_path = Path(args.hitting_streaks)
    output_path = Path(args.output)

    intelligence = json.loads(
        intelligence_path.read_text(encoding="utf-8")
    )
    streak_evidence = json.loads(
        streak_path.read_text(encoding="utf-8")
    )

    teams = intelligence.get("teams") or []
    players = intelligence.get("players") or {}
    batting = players.get("batting") or []
    pitching = players.get("pitching") or []

    team = next(
        (
            row
            for row in teams
            if str(row.get("teamId")) == str(args.team_id)
        ),
        None,
    )

    opponent = next(
        (
            row
            for row in teams
            if str(row.get("teamId"))
            == str(args.opponent_team_id)
        ),
        None,
    )

    if team is None:
        raise ValueError(f"teamId not found: {args.team_id}")

    if opponent is None:
        raise ValueError(
            f"opponentTeamId not found: {args.opponent_team_id}"
        )

    streaks = streak_evidence.get("hittingStreaks") or []

    result = {
        "schemaVersion":
            "strat365-series-player-intelligence-v1",
        "artifactType":
            "series-preview-player-intelligence",
        "generatedAtUtc":
            datetime.now(timezone.utc).isoformat(),
        "leagueId": str(intelligence.get("leagueId")),
        "leagueDate": intelligence.get("leagueDate"),
        "team": build_side(
            team,
            batting,
            pitching,
            streaks,
        ),
        "opponent": build_side(
            opponent,
            batting,
            pitching,
            streaks,
        ),
        "sourceEvidence": {
            "leagueIntelligence":
                str(intelligence_path).replace("\\", "/"),
            "hittingStreaks":
                str(streak_path).replace("\\", "/"),
            "hittingStreakSourceFamily":
                "leagueLeaders",
        },
        "evidenceGates": {
            "seasonPlayerPerformance": "AVAILABLE",
            "activeHittingStreaks": "AVAILABLE",
            "recentPlayerForm": "NOT_YET_NORMALIZED",
            "injuryAvailability": "NOT_YET_NORMALIZED",
            "probableStarters": "NOT_YET_NORMALIZED",
            "bullpenAvailability": "NOT_YET_NORMALIZED",
        },
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
