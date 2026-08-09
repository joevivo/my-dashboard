from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA = "bie.strat365.series-engine.v0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")

    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sum_counts(value: Any) -> int:
    mapping = as_dict(value)
    return sum(int(as_number(item)) for item in mapping.values())


def derive_previous_series_opponents(payload: dict[str, Any]) -> list[str]:
    team_name = str(payload.get("teamName") or "").strip()
    opponents: set[str] = set()

    for game in as_list(payload.get("games")):
        if not isinstance(game, dict):
            continue

        home = str(game.get("homeTeam") or "").strip()
        away = str(game.get("awayTeam") or "").strip()

        if team_name and home == team_name and away:
            opponents.add(away)
        elif team_name and away == team_name and home:
            opponents.add(home)

    return sorted(opponents)


def state_rows(
    signals: dict[str, Any],
    key: str,
    rate_key: str,
    minimum_opportunities: int = 3,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in as_list(signals.get(key)):
        if not isinstance(item, dict):
            continue

        opportunities = int(as_number(item.get("opportunities")))

        if opportunities < minimum_opportunities:
            continue

        rows.append(
            {
                "state": item.get("state"),
                "opportunities": opportunities,
                rate_key: as_number(item.get(rate_key)),
                "runsToInningEnd": int(
                    as_number(item.get("runs_to_inning_end"))
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            as_number(row.get(rate_key)),
            -int(as_number(row.get("opportunities"))),
            str(row.get("state") or ""),
        )
    )

    return rows[:5]



def extract_upcoming_series(
    team_payload: dict[str, Any],
    schedule_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if schedule_payload is None:
        return {
            "status": "NOT_PROVIDED",
            "scheduledDate": None,
            "opponentDisplayName": None,
            "opponentTeamId": None,
            "homeAway": None,
            "gameCount": 0,
            "scheduleGameNumbers": [],
        }

    team_league_id = str(team_payload.get("leagueId") or "").strip()
    schedule_league_id = str(
        schedule_payload.get("leagueId") or ""
    ).strip()

    if (
        team_league_id
        and schedule_league_id
        and team_league_id != schedule_league_id
    ):
        raise ValueError(
            "Team readiness and schedule league IDs do not match: "
            f"{team_league_id!r} != {schedule_league_id!r}"
        )

    team_name = str(team_payload.get("teamName") or "").strip()
    schedule_team_name = str(
        schedule_payload.get("teamName") or ""
    ).strip()

    if (
        team_name
        and schedule_team_name
        and team_name != schedule_team_name
    ):
        raise ValueError(
            "Team readiness and schedule team names do not match: "
            f"{team_name!r} != {schedule_team_name!r}"
        )

    next_series = as_dict(schedule_payload.get("nextSeries"))
    status = str(next_series.get("status") or "").strip()

    if status != "FOUND":
        return {
            "status": status or "NOT_FOUND",
            "scheduledDate": None,
            "opponentDisplayName": None,
            "opponentTeamId": None,
            "homeAway": None,
            "gameCount": 0,
            "scheduleGameNumbers": [],
        }

    opponent_display_name = str(
        next_series.get("opponentDisplayName") or ""
    ).strip()

    if not opponent_display_name:
        raise ValueError(
            "Schedule nextSeries is FOUND but opponentDisplayName "
            "is missing"
        )

    game_count = int(as_number(next_series.get("gameCount")))

    if game_count <= 0:
        raise ValueError(
            "Schedule nextSeries is FOUND but gameCount is not positive"
        )

    return {
        "status": "FOUND",
        "scheduledDate": next_series.get("scheduledDate"),
        "opponentDisplayName": opponent_display_name,
        "opponentTeamId": next_series.get("opponentTeamId"),
        "homeAway": next_series.get("homeAway"),
        "gameCount": game_count,
        "scheduleGameNumbers": as_list(
            next_series.get("scheduleGameNumbers")
        ),
    }


def summarize_recent_signals(payload: dict[str, Any]) -> dict[str, Any]:
    signals = as_dict(payload.get("seriesReadinessSignals"))

    two_out = as_dict(signals.get("twoOutConversion"))
    errors = as_dict(signals.get("defenseErrorEvents"))
    catastrophic = as_dict(signals.get("catastrophicOutcomes"))
    mechanisms = as_dict(signals.get("runMechanisms"))
    tactics = as_dict(signals.get("tacticalEvents"))

    return {
        "gameCount": int(as_number(payload.get("gameCount"))),
        "gameIds": as_list(payload.get("gameIds")),
        "twoOutConversion": {
            "opportunities": int(as_number(two_out.get("opportunities"))),
            "converted": int(as_number(two_out.get("converted"))),
            "conversionRate": as_number(two_out.get("conversionRate")),
            "runsToInningEnd": int(
                as_number(two_out.get("runs_to_inning_end"))
            ),
        },
        "defenseErrors": {
            "eventCount": sum_counts(errors),
            "byType": errors,
        },
        "catastrophicOutcomes": {
            "eventCount": sum_counts(catastrophic),
            "byType": catastrophic,
        },
        "runMechanisms": mechanisms,
        "tacticalEvents": tactics,
        "winMechanismDiversityCount": int(
            as_number(signals.get("winMechanismDiversityCount"))
        ),
        "lowestRecentOffenseStates": state_rows(
            signals,
            "offenseBaseOutStates",
            "conversionRate",
        ),
        "lowestRecentDefensePreventionStates": state_rows(
            signals,
            "defenseBaseOutStates",
            "preventionRate",
        ),
    }


def build_watchlist(recent: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    two_out = as_dict(recent.get("twoOutConversion"))
    opportunities = int(as_number(two_out.get("opportunities")))
    conversion_rate = as_number(two_out.get("conversionRate"))

    if opportunities >= 10 and conversion_rate < 0.20:
        items.append(
            {
                "category": "two_out_offense",
                "signal": "LOW_RECENT_CONVERSION",
                "evidence": {
                    "opportunities": opportunities,
                    "conversionRate": conversion_rate,
                },
                "interpretation": (
                    "Recent two-out conversion was below 20 percent. "
                    "Treat this as a watch signal, not a stable team rate."
                ),
            }
        )

    errors = as_dict(recent.get("defenseErrors"))
    error_count = int(as_number(errors.get("eventCount")))

    if error_count >= 3:
        items.append(
            {
                "category": "defensive_execution",
                "signal": "MULTIPLE_RECENT_ERROR_EVENTS",
                "evidence": {
                    "eventCount": error_count,
                    "byType": as_dict(errors.get("byType")),
                },
                "interpretation": (
                    "Multiple defensive error events occurred in the "
                    "three-game sample. Monitor whether this repeats."
                ),
            }
        )

    catastrophic = as_dict(recent.get("catastrophicOutcomes"))
    catastrophic_types = as_dict(catastrophic.get("byType"))

    double_plays = sum(
        int(as_number(count))
        for name, count in catastrophic_types.items()
        if "Double Play" in str(name)
    )

    if double_plays > 0:
        items.append(
            {
                "category": "offensive_outcomes",
                "signal": "RECENT_DOUBLE_PLAY_COST",
                "evidence": {
                    "doublePlayEvents": double_plays,
                },
                "interpretation": (
                    "The recent sample includes rally-costing double-play "
                    "outcomes. Preserve as contextual evidence only."
                ),
            }
        )

    return items


def compare_recent_signals(
    team_recent: dict[str, Any],
    opponent_recent: dict[str, Any],
) -> dict[str, Any]:
    team_two = as_dict(team_recent.get("twoOutConversion"))
    opp_two = as_dict(opponent_recent.get("twoOutConversion"))

    team_rate = as_number(team_two.get("conversionRate"))
    opp_rate = as_number(opp_two.get("conversionRate"))

    team_errors = int(
        as_number(as_dict(team_recent.get("defenseErrors")).get("eventCount"))
    )
    opp_errors = int(
        as_number(
            as_dict(opponent_recent.get("defenseErrors")).get("eventCount")
        )
    )

    team_mechanisms = set(
        as_dict(team_recent.get("runMechanisms")).keys()
    )
    opp_mechanisms = set(
        as_dict(opponent_recent.get("runMechanisms")).keys()
    )

    return {
        "twoOutConversionRateDelta": round(team_rate - opp_rate, 4),
        "recentDefenseErrorEventDelta": team_errors - opp_errors,
        "sharedRunMechanisms": sorted(
            team_mechanisms.intersection(opp_mechanisms)
        ),
        "teamOnlyRunMechanisms": sorted(
            team_mechanisms.difference(opp_mechanisms)
        ),
        "opponentOnlyRunMechanisms": sorted(
            opp_mechanisms.difference(team_mechanisms)
        ),
    }


def build_engine(
    team_payload: dict[str, Any],
    team_source: Path,
    team_schedule_payload: dict[str, Any] | None,
    team_schedule_source: Path | None,
    opponent_payload: dict[str, Any] | None,
    opponent_source: Path | None,
    explicit_opponent_name: str | None,
) -> dict[str, Any]:
    team_name = str(team_payload.get("teamName") or "").strip()

    if not team_name:
        raise ValueError("Team readiness payload is missing teamName")

    previous_opponents = derive_previous_series_opponents(team_payload)
    team_recent = summarize_recent_signals(team_payload)

    upcoming_series = extract_upcoming_series(
        team_payload,
        team_schedule_payload,
    )

    schedule_opponent_name = (
        upcoming_series["opponentDisplayName"]
        if upcoming_series["status"] == "FOUND"
        else None
    )

    explicit_name = (
        explicit_opponent_name.strip()
        if explicit_opponent_name
        else None
    )

    if (
        schedule_opponent_name
        and explicit_name
        and schedule_opponent_name != explicit_name
    ):
        raise ValueError(
            "Explicit opponent name does not match schedule: "
            f"{explicit_name!r} != {schedule_opponent_name!r}"
        )

    opponent_name = schedule_opponent_name or explicit_name

    opponent_recent: dict[str, Any] | None = None
    matchup: dict[str, Any]

    if opponent_payload is not None:
        payload_opponent_name = str(
            opponent_payload.get("teamName") or ""
        ).strip()

        if not payload_opponent_name:
            raise ValueError(
                "Opponent readiness payload is missing teamName"
            )

        if opponent_name and opponent_name != payload_opponent_name:
            raise ValueError(
                "Explicit opponent name does not match opponent "
                f"readiness payload: {opponent_name!r} != "
                f"{payload_opponent_name!r}"
            )

        opponent_name = payload_opponent_name

        if opponent_name == team_name:
            raise ValueError(
                "Opponent readiness cannot describe the same team"
            )

        opponent_recent = summarize_recent_signals(opponent_payload)

        matchup = {
            "status": "RECENT_SIGNAL_COMPARISON_AVAILABLE",
            "opponentName": opponent_name,
            "comparison": compare_recent_signals(
                team_recent,
                opponent_recent,
            ),
            "opponentPreviousSeriesOpponents":
                derive_previous_series_opponents(opponent_payload),
        }

    else:
        matchup = {
            "status": (
                "UPCOMING_SERIES_IDENTIFIED"
                if upcoming_series["status"] == "FOUND"
                else "OPPONENT_EVIDENCE_REQUIRED"
            ),
            "opponentName": opponent_name,
            "opponentTeamId":
                upcoming_series.get("opponentTeamId"),
            "comparison": None,
        }

    missing_evidence: list[str] = []

    if upcoming_series["status"] != "FOUND":
        missing_evidence.append(
            "upcoming opponent schedule identity"
        )

    if opponent_payload is None:
        missing_evidence.append(
            "upcoming opponent recent-series readiness"
        )

    missing_evidence.extend(
        [
            "upcoming probable starting pitchers",
            "opponent roster and card/split evidence",
            "team roster and card/split evidence",
            "bullpen availability and recent usage",
        ]
    )

    return {
        "schema": SCHEMA,
        "team": {
            "leagueId": team_payload.get("leagueId"),
            "teamName": team_name,
            "season": team_payload.get("season"),
            "leagueDate": team_payload.get("leagueDate"),
        },
        "sourceEvidence": {
            "teamReadiness": str(team_source),
            "teamSchedule": (
                str(team_schedule_source)
                if team_schedule_source is not None
                else None
            ),
            "opponentReadiness": (
                str(opponent_source)
                if opponent_source is not None
                else None
            ),
        },
        "previousSeries": {
            "gameIds": as_list(team_payload.get("gameIds")),
            "opponents": previous_opponents,
        },
        "upcomingSeries": upcoming_series,
        "recentTeamSignals": team_recent,
        "recentOpponentSignals": opponent_recent,
        "matchupAssessment": matchup,
        "managerialWatchlist": build_watchlist(team_recent),
        "managerRecommendations": {
            "status": "EVIDENCE_GATED",
            "items": [],
            "missingEvidence": missing_evidence,
            "note": (
                "Series Engine v0 does not convert a three-game sample "
                "into lineup, pitching, bullpen, or tactical prescriptions "
                "without explicit opponent and roster/card evidence."
            ),
        },
        "sampleGovernance": {
            "recentSeriesGameCount": int(
                as_number(team_payload.get("gameCount"))
            ),
            "classification": "SHORT_SAMPLE_CONTEXT",
            "policy": (
                "Recent-series signals may identify watch items and "
                "questions. They are not stable rates or standalone "
                "managerial recommendations."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compose Strat365 Series Readiness evidence into a "
            "governed BIE Series Engine packet."
        )
    )

    parser.add_argument(
        "--team-readiness",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--team-schedule",
        type=Path,
    )
    parser.add_argument(
        "--opponent-readiness",
        type=Path,
    )
    parser.add_argument(
        "--opponent-name",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    team_payload = load_json(args.team_readiness)

    team_schedule_payload = (
        load_json(args.team_schedule)
        if args.team_schedule
        else None
    )

    opponent_payload = (
        load_json(args.opponent_readiness)
        if args.opponent_readiness
        else None
    )

    output = build_engine(
        team_payload=team_payload,
        team_source=args.team_readiness,
        team_schedule_payload=team_schedule_payload,
        team_schedule_source=args.team_schedule,
        opponent_payload=opponent_payload,
        opponent_source=args.opponent_readiness,
        explicit_opponent_name=args.opponent_name,
    )

    write_json(args.output, output)

    print(
        json.dumps(
            {
                "status": "PASS",
                "schema": output["schema"],
                "leagueId": output["team"]["leagueId"],
                "teamName": output["team"]["teamName"],
                "matchupStatus":
                    output["matchupAssessment"]["status"],
                "upcomingSeriesStatus":
                    output["upcomingSeries"]["status"],
                "upcomingOpponent":
                    output["upcomingSeries"][
                        "opponentDisplayName"
                    ],
                "upcomingOpponentTeamId":
                    output["upcomingSeries"]["opponentTeamId"],
                "watchItemCount":
                    len(output["managerialWatchlist"]),
                "recommendationStatus":
                    output["managerRecommendations"]["status"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())