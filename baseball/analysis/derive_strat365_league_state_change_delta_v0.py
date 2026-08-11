from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = (
    "bie.strat365.league-state-change-delta.v0"
)

TRANSACTION_COVERAGE = (
    "NORMALIZED_COMPLETE_PAGINATION"
)

INJURY_COVERAGE = (
    "NORMALIZED_CURRENT_STATE_SNAPSHOT"
)

INVALIDATION_TARGET_ORDER = [
    "ROSTER",
    "LINEUP",
    "ROTATION",
    "MANAGER_FINGERPRINT",
    "SERIES_READ",
]

TRANSACTION_INVALIDATIONS = [
    "ROSTER",
    "LINEUP",
    "ROTATION",
    "MANAGER_FINGERPRINT",
    "SERIES_READ",
]

INJURY_INVALIDATIONS = [
    "LINEUP",
    "ROTATION",
    "MANAGER_FINGERPRINT",
    "SERIES_READ",
]


def load_json(
    path: Path,
) -> dict[str, Any]:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return value


def write_json(
    path: Path,
    value: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def stable_hash(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def state_container(
    payload: dict[str, Any],
) -> dict[str, Any]:
    state = payload.get(
        "leagueStateChanges"
    )

    if not isinstance(
        state,
        dict,
    ):
        raise ValueError(
            "leagueStateChanges is missing."
        )

    return state


def source_coverage(
    payload: dict[str, Any],
    family: str,
) -> str | None:
    coverage = payload.get(
        "sourceCoverage"
    )

    if not isinstance(
        coverage,
        dict,
    ):
        return None

    value = coverage.get(
        family
    )

    if value is None:
        return None

    return str(value)


def transaction_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    value = state_container(
        payload
    ).get(
        "transactions"
    )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            "Normalized transaction payload is missing."
        )

    return value


def injury_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    value = state_container(
        payload
    ).get(
        "activeInjuries"
    )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            "Normalized injury payload is missing."
        )

    return value


def transaction_events(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    events = transaction_payload(
        payload
    ).get(
        "events",
        [],
    )

    if not isinstance(
        events,
        list,
    ):
        raise ValueError(
            "Transaction events must be a list."
        )

    output = []

    seen = set()

    for item in events:
        if not isinstance(
            item,
            dict,
        ):
            raise ValueError(
                "Transaction event must be an object."
            )

        event_key = str(
            item.get(
                "eventKey",
                "",
            )
        )

        if not event_key:
            raise ValueError(
                "Transaction eventKey is missing."
            )

        if event_key in seen:
            raise ValueError(
                f"Duplicate transaction eventKey: {event_key}"
            )

        seen.add(
            event_key
        )

        output.append(
            item
        )

    return output


def injury_records(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    injuries = injury_payload(
        payload
    ).get(
        "injuries",
        [],
    )

    if not isinstance(
        injuries,
        list,
    ):
        raise ValueError(
            "Injury records must be a list."
        )

    output = []

    seen = set()

    for item in injuries:
        if not isinstance(
            item,
            dict,
        ):
            raise ValueError(
                "Injury record must be an object."
            )

        identity = str(
            item.get(
                "identityKey",
                "",
            )
        )

        if not identity:
            raise ValueError(
                "Injury identityKey is missing."
            )

        if identity in seen:
            raise ValueError(
                f"Duplicate injury identity: {identity}"
            )

        seen.add(
            identity
        )

        output.append(
            item
        )

    return output


def transaction_source_valid(
    payload: dict[str, Any],
) -> bool:
    if (
        source_coverage(
            payload,
            "leagueTransactions",
        )
        != TRANSACTION_COVERAGE
    ):
        return False

    transaction_payload(
        payload
    )

    return True


def injury_source_valid(
    payload: dict[str, Any],
) -> bool:
    if (
        source_coverage(
            payload,
            "leagueInjuries",
        )
        != INJURY_COVERAGE
    ):
        return False

    injuries = injury_payload(
        payload
    )

    return (
        injuries.get(
            "snapshotValid"
        )
        is True
    )


def transaction_change(
    *,
    league_id: str,
    event: dict[str, Any],
) -> dict[str, Any]:
    source_event_key = str(
        event["eventKey"]
    )

    change_key = stable_hash(
        {
            "leagueId": league_id,
            "changeType": (
                "TRANSACTION_EVENT"
            ),
            "sourceEventKey": (
                source_event_key
            ),
        }
    )

    return {
        "changeKey": change_key,
        "changeType": (
            "TRANSACTION_EVENT"
        ),
        "domain": event.get(
            "domain"
        ),
        "actionCode": event.get(
            "actionCode"
        ),
        "rawAction": event.get(
            "rawAction"
        ),
        "sourceEventKey": (
            source_event_key
        ),
        "sourceDateText": event.get(
            "sourceDateText"
        ),
        "teamId": event.get(
            "teamId"
        ),
        "teamName": event.get(
            "teamName"
        ),
        "playerId": event.get(
            "playerId"
        ),
        "playerName": event.get(
            "playerName"
        ),
        "tradeId": event.get(
            "tradeId"
        ),
        "counterpartyTeamId": (
            event.get(
                "counterpartyTeamId"
            )
        ),
        "counterpartyTeamName": (
            event.get(
                "counterpartyTeamName"
            )
        ),
        "invalidates": list(
            TRANSACTION_INVALIDATIONS
        ),
    }


def injury_change(
    *,
    league_id: str,
    change_type: str,
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    source = (
        current
        if current is not None
        else previous
    )

    assert source is not None

    identity = str(
        source[
            "identityKey"
        ]
    )

    previous_game = (
        previous.get(
            "injuredThroughGame"
        )
        if previous is not None
        else None
    )

    current_game = (
        current.get(
            "injuredThroughGame"
        )
        if current is not None
        else None
    )

    change_key = stable_hash(
        {
            "leagueId": league_id,
            "changeType": change_type,
            "identityKey": identity,
            "previousInjuredThroughGame": (
                previous_game
            ),
            "currentInjuredThroughGame": (
                current_game
            ),
        }
    )

    return {
        "changeKey": change_key,
        "changeType": change_type,
        "domain": "INJURY",
        "identityKey": identity,
        "teamId": source.get(
            "teamId"
        ),
        "teamName": source.get(
            "teamName"
        ),
        "playerId": source.get(
            "playerId"
        ),
        "playerName": source.get(
            "playerName"
        ),
        "previousInjuredThroughGame": (
            previous_game
        ),
        "currentInjuredThroughGame": (
            current_game
        ),
        "invalidates": list(
            INJURY_INVALIDATIONS
        ),
    }


def aggregate_invalidations(
    changes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_target: dict[
        str,
        list[str],
    ] = {
        target: []
        for target
        in INVALIDATION_TARGET_ORDER
    }

    for change in changes:
        change_key = str(
            change["changeKey"]
        )

        invalidates = change.get(
            "invalidates",
            [],
        )

        if not isinstance(
            invalidates,
            list,
        ):
            raise ValueError(
                "Change invalidates must be a list."
            )

        for target in invalidates:
            target = str(target)

            if target not in by_target:
                raise ValueError(
                    f"Unknown invalidation target: {target}"
                )

            if (
                change_key
                not in by_target[
                    target
                ]
            ):
                by_target[
                    target
                ].append(
                    change_key
                )

    output = []

    for target in (
        INVALIDATION_TARGET_ORDER
    ):
        keys = by_target[
            target
        ]

        if not keys:
            continue

        output.append(
            {
                "target": target,
                "eventCount": len(
                    keys
                ),
                "changeKeys": keys,
            }
        )

    return output


def build_delta(
    *,
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> dict[str, Any]:
    league_id = str(
        current.get(
            "leagueId",
            "",
        )
    )

    if not league_id:
        raise ValueError(
            "Current leagueId is missing."
        )

    if previous is not None:
        previous_league_id = str(
            previous.get(
                "leagueId",
                "",
            )
        )

        if (
            previous_league_id
            != league_id
        ):
            raise ValueError(
                "Previous/current leagueId mismatch."
            )

    previous_date = (
        previous.get(
            "leagueDate"
        )
        if previous is not None
        else None
    )

    current_date = current.get(
        "leagueDate"
    )

    changes = []

    transaction_status = None
    injury_status = None
    history_regression_count = 0

    if previous is None:
        transaction_status = (
            "BASELINE_ESTABLISHED"
            if transaction_source_valid(
                current
            )
            else (
                "BASELINE_SOURCE_INVALID_OR_UNAVAILABLE"
            )
        )

        injury_status = (
            "BASELINE_ESTABLISHED"
            if injury_source_valid(
                current
            )
            else (
                "BASELINE_SOURCE_INVALID_OR_UNAVAILABLE"
            )
        )

    else:
        if (
            transaction_source_valid(
                previous
            )
            and transaction_source_valid(
                current
            )
        ):
            prior_events = (
                transaction_events(
                    previous
                )
            )

            current_events = (
                transaction_events(
                    current
                )
            )

            prior_keys = {
                str(
                    item[
                        "eventKey"
                    ]
                )
                for item
                in prior_events
            }

            current_keys = {
                str(
                    item[
                        "eventKey"
                    ]
                )
                for item
                in current_events
            }

            missing_keys = (
                prior_keys
                - current_keys
            )

            history_regression_count = (
                len(
                    missing_keys
                )
            )

            if missing_keys:
                transaction_status = (
                    "INVALID_HISTORY_REGRESSION"
                )

            else:
                transaction_status = (
                    "DERIVED"
                )

                for event in current_events:
                    event_key = str(
                        event[
                            "eventKey"
                        ]
                    )

                    if (
                        event_key
                        in prior_keys
                    ):
                        continue

                    changes.append(
                        transaction_change(
                            league_id=league_id,
                            event=event,
                        )
                    )

        else:
            transaction_status = (
                "GATED_SOURCE_INVALID_OR_UNAVAILABLE"
            )

        if (
            injury_source_valid(
                previous
            )
            and injury_source_valid(
                current
            )
        ):
            prior_injuries = {
                str(
                    item[
                        "identityKey"
                    ]
                ): item
                for item
                in injury_records(
                    previous
                )
            }

            current_injuries = {
                str(
                    item[
                        "identityKey"
                    ]
                ): item
                for item
                in injury_records(
                    current
                )
            }

            prior_ids = set(
                prior_injuries
            )

            current_ids = set(
                current_injuries
            )

            for identity in sorted(
                current_ids
                - prior_ids
            ):
                changes.append(
                    injury_change(
                        league_id=league_id,
                        change_type=(
                            "INJURY_ACTIVE"
                        ),
                        previous=None,
                        current=(
                            current_injuries[
                                identity
                            ]
                        ),
                    )
                )

            for identity in sorted(
                prior_ids
                & current_ids
            ):
                previous_record = (
                    prior_injuries[
                        identity
                    ]
                )

                current_record = (
                    current_injuries[
                        identity
                    ]
                )

                if (
                    previous_record.get(
                        "injuredThroughGame"
                    )
                    != current_record.get(
                        "injuredThroughGame"
                    )
                ):
                    changes.append(
                        injury_change(
                            league_id=league_id,
                            change_type=(
                                "INJURY_UPDATED"
                            ),
                            previous=(
                                previous_record
                            ),
                            current=(
                                current_record
                            ),
                        )
                    )

            for identity in sorted(
                prior_ids
                - current_ids
            ):
                changes.append(
                    injury_change(
                        league_id=league_id,
                        change_type=(
                            "INJURY_CLEARED"
                        ),
                        previous=(
                            prior_injuries[
                                identity
                            ]
                        ),
                        current=None,
                    )
                )

            injury_status = (
                "DERIVED"
            )

        else:
            injury_status = (
                "GATED_SOURCE_OR_SNAPSHOT_INVALID"
            )

    transaction_changes = [
        item
        for item in changes
        if item[
            "changeType"
        ] == "TRANSACTION_EVENT"
    ]

    injury_changes = [
        item
        for item in changes
        if item[
            "domain"
        ] == "INJURY"
    ]

    invalidations = (
        aggregate_invalidations(
            changes
        )
    )

    return {
        "schemaVersion": (
            SCHEMA_VERSION
        ),
        "leagueId": league_id,
        "previousLeagueDate": (
            previous_date
        ),
        "currentLeagueDate": (
            current_date
        ),
        "baseline": (
            previous is None
        ),
        "domainStatus": {
            "transactions": (
                transaction_status
            ),
            "injuries": (
                injury_status
            ),
        },
        "transactionHistoryRegressionCount": (
            history_regression_count
        ),
        "changeCount": len(
            changes
        ),
        "transactionChangeCount": len(
            transaction_changes
        ),
        "injuryChangeCount": len(
            injury_changes
        ),
        "changes": changes,
        "invalidationSignalCount": len(
            invalidations
        ),
        "invalidationSignals": (
            invalidations
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--previous",
        required=False,
    )

    parser.add_argument(
        "--current",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    previous = (
        load_json(
            Path(
                args.previous
            ).resolve()
        )
        if args.previous
        else None
    )

    current = load_json(
        Path(
            args.current
        ).resolve()
    )

    result = build_delta(
        previous=previous,
        current=current,
    )

    write_json(
        Path(
            args.output
        ).resolve(),
        result,
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "leagueId": (
                    result[
                        "leagueId"
                    ]
                ),
                "baseline": (
                    result[
                        "baseline"
                    ]
                ),
                "changeCount": (
                    result[
                        "changeCount"
                    ]
                ),
                "invalidationSignalCount": (
                    result[
                        "invalidationSignalCount"
                    ]
                ),
            },
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
