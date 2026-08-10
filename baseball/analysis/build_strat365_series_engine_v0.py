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


def summarize_league_profile(
    team: dict[str, Any],
) -> dict[str, Any]:
    standings = as_dict(
        team.get("standings")
    )
    standings_metrics = as_dict(
        standings.get("metrics")
    )

    offense = as_dict(
        team.get("offense")
    )
    offense_metrics = as_dict(
        offense.get("metrics")
    )

    pitching = as_dict(
        team.get("pitching")
    )
    pitching_metrics = as_dict(
        pitching.get("metrics")
    )

    fielding = as_dict(
        team.get("fielding")
    )
    fielding_metrics = as_dict(
        fielding.get("metrics")
    )

    manager = as_dict(
        team.get("manager")
    )
    manager_metrics = as_dict(
        manager.get("metrics")
    )

    derived = as_dict(
        team.get("derived")
    )
    ranks = as_dict(
        derived.get("ranks")
    )

    return {
        "teamId": str(
            team.get("teamId") or ""
        ),
        "teamName": str(
            team.get("teamName") or ""
        ),
        "record": {
            "wins": int(
                as_number(
                    standings_metrics.get("wins")
                )
            ),
            "losses": int(
                as_number(
                    standings_metrics.get("losses")
                )
            ),
        },
        "runDifferential": int(
            as_number(
                standings_metrics.get(
                    "runDifferential"
                )
            )
        ),
        "runDifferentialRank": (
            int(
                as_number(
                    ranks.get(
                        "runDifferentialRank"
                    )
                )
            )
            if ranks.get(
                "runDifferentialRank"
            ) is not None
            else None
        ),
        "offense": {
            "runsScored": int(
                as_number(
                    offense_metrics.get("R")
                )
            ),
            "runsScoredRank": int(
                as_number(
                    ranks.get("runsScoredRank")
                )
            ),
            "ops": as_number(
                offense_metrics.get("OPS")
            ),
            "opsRank": int(
                as_number(
                    ranks.get("opsRank")
                )
            ),
        },
        "pitching": {
            "runsAllowed": int(
                as_number(
                    pitching_metrics.get("R")
                )
            ),
            "runsAllowedRank": int(
                as_number(
                    ranks.get("runsAllowedRank")
                )
            ),
            "era": as_number(
                pitching_metrics.get("ERA")
            ),
            "eraRank": int(
                as_number(
                    ranks.get("eraRank")
                )
            ),
            "whip": as_number(
                pitching_metrics.get("WHIP")
            ),
            "whipRank": int(
                as_number(
                    ranks.get("whipRank")
                )
            ),
        },
        "defense": {
            "errors": int(
                as_number(
                    fielding_metrics.get("E")
                )
            ),
            "fewestErrorsRank": int(
                as_number(
                    ranks.get("fewestErrorsRank")
                )
            ),
            "fieldingAverage": as_number(
                fielding_metrics.get("AVG")
            ),
            "fieldingAverageRank": int(
                as_number(
                    ranks.get(
                        "fieldingAverageRank"
                    )
                )
            ),
            "unearnedRunsAllowed": int(
                as_number(
                    derived.get(
                        "unearnedRunsAllowed"
                    )
                )
            ),
            "unearnedRunsPerGame": as_number(
                derived.get(
                    "unearnedRunsPerGame"
                )
            ),
            "fewestUnearnedRunsAllowedRank": int(
                as_number(
                    ranks.get(
                        "fewestUnearnedRunsAllowedRank"
                    )
                )
            ),
            "lowestUnearnedRunsPerGameRank": int(
                as_number(
                    ranks.get(
                        "lowestUnearnedRunsPerGameRank"
                    )
                )
            ),
        },
        "managerTendencies": {
            "stolenBases": int(
                as_number(
                    manager_metrics.get(
                        "stolenBases"
                    )
                )
            ),
            "caughtStealing": int(
                as_number(
                    manager_metrics.get(
                        "caughtStealing"
                    )
                )
            ),
            "stolenBasePct": as_number(
                manager_metrics.get(
                    "stolenBasePct"
                )
            ),
            "sacrifices": int(
                as_number(
                    manager_metrics.get(
                        "sacrifices"
                    )
                )
            ),
            "hitAndRuns": int(
                as_number(
                    manager_metrics.get(
                        "hitAndRuns"
                    )
                )
            ),
            "intentionalWalks": int(
                as_number(
                    manager_metrics.get(
                        "intentionalWalks"
                    )
                )
            ),
        },
    }


def find_league_team(
    league_payload: dict[str, Any],
    *,
    team_id: str | None,
    team_name: str | None,
) -> dict[str, Any] | None:
    teams = [
        as_dict(item)
        for item in as_list(
            league_payload.get("teams")
        )
    ]

    normalized_team_id = str(
        team_id or ""
    ).strip()

    if normalized_team_id:
        matches = [
            team
            for team in teams
            if str(
                team.get("teamId") or ""
            ).strip() == normalized_team_id
        ]

        if len(matches) != 1:
            raise ValueError(
                "League Intelligence team ID "
                f"{normalized_team_id!r} resolved "
                f"{len(matches)} teams"
            )

        return matches[0]

    normalized_name = str(
        team_name or ""
    ).strip()

    if normalized_name:
        matches = [
            team
            for team in teams
            if str(
                team.get("teamName") or ""
            ).strip() == normalized_name
        ]

        if len(matches) != 1:
            raise ValueError(
                "League Intelligence team name "
                f"{normalized_name!r} resolved "
                f"{len(matches)} teams"
            )

        return matches[0]

    return None


def metric_delta(
    left: Any,
    right: Any,
    digits: int = 4,
) -> float | None:
    if left is None or right is None:
        return None

    return round(
        as_number(left) - as_number(right),
        digits,
    )


def rank_advantage(
    team_rank: Any,
    opponent_rank: Any,
) -> int | None:
    if (
        team_rank is None
        or opponent_rank is None
    ):
        return None

    return int(
        as_number(opponent_rank)
        - as_number(team_rank)
    )


def compare_league_profiles(
    team: dict[str, Any],
    opponent: dict[str, Any],
) -> dict[str, Any]:
    team_offense = as_dict(
        team.get("offense")
    )
    opp_offense = as_dict(
        opponent.get("offense")
    )

    team_pitching = as_dict(
        team.get("pitching")
    )
    opp_pitching = as_dict(
        opponent.get("pitching")
    )

    team_defense = as_dict(
        team.get("defense")
    )
    opp_defense = as_dict(
        opponent.get("defense")
    )

    return {
        "deltaConvention": (
            "TEAM_MINUS_OPPONENT_FOR_METRICS"
        ),
        "rankAdvantageConvention": (
            "POSITIVE_MEANS_TEAM_RANKS_BETTER"
        ),
        "runDifferentialDelta": metric_delta(
            team.get("runDifferential"),
            opponent.get("runDifferential"),
            0,
        ),
        "opsDelta": metric_delta(
            team_offense.get("ops"),
            opp_offense.get("ops"),
        ),
        "eraDelta": metric_delta(
            team_pitching.get("era"),
            opp_pitching.get("era"),
        ),
        "whipDelta": metric_delta(
            team_pitching.get("whip"),
            opp_pitching.get("whip"),
        ),
        "fieldingAverageDelta": metric_delta(
            team_defense.get(
                "fieldingAverage"
            ),
            opp_defense.get(
                "fieldingAverage"
            ),
        ),
        "unearnedRunsPerGameDelta": metric_delta(
            team_defense.get(
                "unearnedRunsPerGame"
            ),
            opp_defense.get(
                "unearnedRunsPerGame"
            ),
        ),
        "rankAdvantages": {
            "ops": rank_advantage(
                team_offense.get("opsRank"),
                opp_offense.get("opsRank"),
            ),
            "era": rank_advantage(
                team_pitching.get("eraRank"),
                opp_pitching.get("eraRank"),
            ),
            "whip": rank_advantage(
                team_pitching.get("whipRank"),
                opp_pitching.get("whipRank"),
            ),
            "fieldingAverage": rank_advantage(
                team_defense.get(
                    "fieldingAverageRank"
                ),
                opp_defense.get(
                    "fieldingAverageRank"
                ),
            ),
            "unearnedRunsAllowed": rank_advantage(
                team_defense.get(
                    "fewestUnearnedRunsAllowedRank"
                ),
                opp_defense.get(
                    "fewestUnearnedRunsAllowedRank"
                ),
            ),
            "unearnedRunsPerGame": rank_advantage(
                team_defense.get(
                    "lowestUnearnedRunsPerGameRank"
                ),
                opp_defense.get(
                    "lowestUnearnedRunsPerGameRank"
                ),
            ),
        },
    }


def build_league_context(
    team_payload: dict[str, Any],
    team_schedule_payload: dict[str, Any] | None,
    upcoming_series: dict[str, Any],
    league_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if league_payload is None:
        return {
            "status": "NOT_PROVIDED",
            "teamProfile": None,
            "opponentProfile": None,
            "comparison": None,
        }

    readiness_league_id = str(
        team_payload.get("leagueId") or ""
    ).strip()

    intelligence_league_id = str(
        league_payload.get("leagueId") or ""
    ).strip()

    if (
        readiness_league_id
        and intelligence_league_id
        and readiness_league_id
        != intelligence_league_id
    ):
        raise ValueError(
            "Team readiness and League Intelligence "
            "league IDs do not match: "
            f"{readiness_league_id!r} != "
            f"{intelligence_league_id!r}"
        )

    schedule_team_id = None

    if team_schedule_payload is not None:
        raw_team_id = (
            team_schedule_payload.get("teamId")
        )

        if raw_team_id is not None:
            schedule_team_id = str(
                raw_team_id
            ).strip() or None

    team = find_league_team(
        league_payload,
        team_id=schedule_team_id,
        team_name=str(
            team_payload.get("teamName") or ""
        ).strip(),
    )

    if team is None:
        raise ValueError(
            "Unable to resolve team in "
            "League Intelligence"
        )

    team_profile = summarize_league_profile(
        team
    )

    opponent_id = str(
        upcoming_series.get(
            "opponentTeamId"
        ) or ""
    ).strip()

    if not opponent_id:
        return {
            "status": "TEAM_PROFILE_ONLY",
            "teamProfile": team_profile,
            "opponentProfile": None,
            "comparison": None,
        }

    opponent = find_league_team(
        league_payload,
        team_id=opponent_id,
        team_name=None,
    )

    if opponent is None:
        return {
            "status": "TEAM_PROFILE_ONLY",
            "teamProfile": team_profile,
            "opponentProfile": None,
            "comparison": None,
        }

    opponent_profile = summarize_league_profile(
        opponent
    )

    if (
        opponent_profile["teamId"]
        == team_profile["teamId"]
    ):
        raise ValueError(
            "League Intelligence opponent "
            "resolved to team itself"
        )

    return {
        "status": "AVAILABLE",
        "classification": (
            "SEASON_TO_DATE_LEAGUE_CONTEXT"
        ),
        "teamProfile": team_profile,
        "opponentProfile": opponent_profile,
        "comparison": compare_league_profiles(
            team_profile,
            opponent_profile,
        ),
    }


def build_engine(
    team_payload: dict[str, Any],
    team_source: Path,
    team_schedule_payload: dict[str, Any] | None,
    team_schedule_source: Path | None,
    opponent_payload: dict[str, Any] | None,
    opponent_source: Path | None,
    league_intelligence_payload: dict[str, Any] | None,
    league_intelligence_source: Path | None,
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

    league_context = build_league_context(
        team_payload,
        team_schedule_payload,
        upcoming_series,
        league_intelligence_payload,
    )

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

    matchup["leagueComparison"] = (
        league_context.get("comparison")
    )

    if league_context["status"] == "AVAILABLE":
        matchup["status"] = (
            "RECENT_AND_LEAGUE_COMPARISON_AVAILABLE"
            if opponent_payload is not None
            else "LEAGUE_COMPARISON_AVAILABLE"
        )

    missing_evidence: list[str] = []

    if upcoming_series["status"] != "FOUND":
        missing_evidence.append(
            "upcoming opponent schedule identity"
        )

    if (
        opponent_payload is None
        and league_context["status"] != "AVAILABLE"
    ):
        missing_evidence.append(
            "upcoming opponent recent-series or "
            "League Intelligence evidence"
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
            "leagueIntelligence": (
                str(league_intelligence_source)
                if league_intelligence_source is not None
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
        "leagueContext": league_context,
        "matchupAssessment": matchup,
        "managerialWatchlist": build_watchlist(team_recent),
        "managerRecommendations": {
            "status": "EVIDENCE_GATED",
            "items": [],
            "missingEvidence": missing_evidence,
            "note": (
                "Series Engine v0 keeps short-sample readiness and "
                "season-to-date League Intelligence distinct. League "
                "context can establish opponent performance evidence, "
                "but lineup, pitching, bullpen, and tactical prescriptions "
                "remain gated by probable-starter, roster/card, and "
                "bullpen-availability evidence."
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
            "leagueIntelligenceClassification": (
                "SEASON_TO_DATE_LEAGUE_CONTEXT"
                if league_intelligence_payload is not None
                else "NOT_PROVIDED"
            ),
            "leagueIntelligencePolicy": (
                "League-relative season evidence may support matchup "
                "assessment but does not substitute for player-card, "
                "probable-starter, or bullpen-availability evidence."
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
        "--league-intelligence",
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

    league_intelligence_payload = (
        load_json(args.league_intelligence)
        if args.league_intelligence
        else None
    )

    output = build_engine(
        team_payload=team_payload,
        team_source=args.team_readiness,
        team_schedule_payload=team_schedule_payload,
        team_schedule_source=args.team_schedule,
        opponent_payload=opponent_payload,
        opponent_source=args.opponent_readiness,
        league_intelligence_payload=league_intelligence_payload,
        league_intelligence_source=args.league_intelligence,
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