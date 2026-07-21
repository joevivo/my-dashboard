from __future__ import annotations

import csv
from collections import Counter
from calendar import monthcalendar
from datetime import datetime, timedelta, timezone
from pathlib import Path


MUSIC_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "music"
)

RECENT_APPLE_WAREHOUSE = (
    MUSIC_DIRECTORY
    / "live"
    / "apple_snapshot_warehouse.csv"
)

def nth_sunday(year, month, occurrence):
    sundays = [
        week[6]
        for week in monthcalendar(year, month)
        if week[6] != 0
    ]

    return sundays[occurrence - 1]


def central_utc_offset(snapshot_time):
    year = snapshot_time.year

    dst_start_day = nth_sunday(year, 3, 2)
    dst_end_day = nth_sunday(year, 11, 1)

    dst_start_utc = datetime(
        year,
        3,
        dst_start_day,
        8,
        0,
        tzinfo=timezone.utc,
    )

    dst_end_utc = datetime(
        year,
        11,
        dst_end_day,
        7,
        0,
        tzinfo=timezone.utc,
    )

    if dst_start_utc <= snapshot_time < dst_end_utc:
        return timedelta(hours=-5)

    return timedelta(hours=-6)


def central_local_date(snapshot_time):
    return (
        snapshot_time
        + central_utc_offset(snapshot_time)
    ).date()


def empty_recent_apple_evidence(status):
    numeric_value = 0 if status == "available" else None

    return {
        "status": status,
        "observationCount": numeric_value,
        "entitySnapshotObservationCount": numeric_value,
        "uniqueEntityCount": numeric_value,
        "snapshotCount": numeric_value,
        "observedDayCount": numeric_value,
        "observedDays": [],
        "sourceCounts": {},
        "entityTypeCounts": {},
        "topItems": [],
        "sourceNote": (
            "Recent Apple Objects are snapshot observations, "
            "not confirmed plays or complete listening history."
        ),
    }


def parse_snapshot_time(value):
    text = str(value or "").strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except ValueError:
        pass

    try:
        return datetime.strptime(
            text,
            "%Y-%m-%d_%H%M%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def entity_identity(row):
    catalog_id = str(
        row.get("catalog_or_global_id") or ""
    ).strip()

    if catalog_id:
        return catalog_id

    entity_id = str(row.get("entity_id") or "").strip()

    if entity_id:
        return entity_id

    return "|".join(
        [
            str(row.get("entity_type") or "").strip(),
            str(row.get("artist") or "").strip(),
            str(row.get("name") or "").strip(),
        ]
    )


def recent_apple_unavailable(message):
    return {
        "coverage": {
            "sourceId": "apple_live_snapshot_warehouse",
            "sourceType": "recent_apple_observation",
            "status": "unavailable",
            "recordsExamined": None,
            "recordsMatched": None,
            "coverageStart": None,
            "coverageEnd": None,
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [message],
        },
        "evidence": empty_recent_apple_evidence(
            "unavailable"
        ),
        "warnings": [
            {
                "code": "RECENT_APPLE_UNAVAILABLE",
                "message": message,
                "sourceId": (
                    "apple_live_snapshot_warehouse"
                ),
            }
        ],
        "provenance": None,
    }


def load_recent_apple(requested_start, requested_end):
    requested_start_text = str(requested_start)
    requested_end_text = str(requested_end)

    if not RECENT_APPLE_WAREHOUSE.exists():
        return recent_apple_unavailable(
            "The Recent Apple snapshot warehouse was not found."
        )

    normalized_rows = []
    invalid_timestamp_count = 0

    try:
        with RECENT_APPLE_WAREHOUSE.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            for row in csv.DictReader(handle):
                snapshot_time = parse_snapshot_time(
                    row.get("snapshot_time")
                )

                if snapshot_time is None:
                    invalid_timestamp_count += 1
                    continue

                local_date = central_local_date(
                    snapshot_time
                )

                normalized_rows.append(
                    {
                        **row,
                        "snapshotTime": snapshot_time,
                        "localDate": local_date,
                        "identity": entity_identity(row),
                    }
                )
    except (OSError, csv.Error) as error:
        return recent_apple_unavailable(
            "The Recent Apple snapshot warehouse could "
            f"not be read: {error}"
        )

    if not normalized_rows:
        return recent_apple_unavailable(
            "The Recent Apple snapshot warehouse contains "
            "no usable observations."
        )

    coverage_start = min(
        row["localDate"] for row in normalized_rows
    )
    coverage_end = max(
        row["localDate"] for row in normalized_rows
    )
    captured_at = max(
        row["snapshotTime"] for row in normalized_rows
    ).isoformat().replace("+00:00", "Z")

    no_overlap = (
        requested_end < coverage_start
        or requested_start > coverage_end
    )

    base_limitation = (
        "Recent Apple Objects are snapshot observations, "
        "not confirmed plays or complete listening history."
    )

    if no_overlap:
        message = (
            "Recent Apple Objects cover "
            f"{coverage_start} through {coverage_end} and do "
            "not cover the selected period."
        )

        return {
            "coverage": {
                "sourceId": (
                    "apple_live_snapshot_warehouse"
                ),
                "sourceType": (
                    "recent_apple_observation"
                ),
                "status": "unsupported_for_period",
                "recordsExamined": None,
                "recordsMatched": None,
                "coverageStart": str(coverage_start),
                "coverageEnd": str(coverage_end),
                "capturedAt": captured_at,
                "freshness": "stale",
                "limitations": [
                    message,
                    base_limitation,
                ],
            },
            "evidence": empty_recent_apple_evidence(
                "unsupported_for_period"
            ),
            "warnings": [
                {
                    "code": (
                        "RECENT_APPLE_UNSUPPORTED_FOR_PERIOD"
                    ),
                    "message": message,
                    "sourceId": (
                        "apple_live_snapshot_warehouse"
                    ),
                }
            ],
            "provenance": {
                "evidenceId": (
                    "recent-apple-snapshot-observations"
                ),
                "sourceId": (
                    "apple_live_snapshot_warehouse"
                ),
                "sourceLabel": (
                    "Recent Apple Snapshot Warehouse"
                ),
                "sourceType": (
                    "recent_apple_observation"
                ),
                "recordCount": 0,
                "coverageStart": str(coverage_start),
                "coverageEnd": str(coverage_end),
                "capturedAt": captured_at,
                "notes": [base_limitation],
            },
        }

    query_start = max(requested_start, coverage_start)
    query_end = min(requested_end, coverage_end)

    partial_coverage = (
        query_start != requested_start
        or query_end != requested_end
    )

    period_rows = [
        row
        for row in normalized_rows
        if requested_start
        <= row["localDate"]
        <= requested_end
    ]

    snapshot_folders = {
        str(row.get("snapshot_folder") or "")
        for row in period_rows
    }

    observed_days = sorted(
        {
            str(row["localDate"])
            for row in period_rows
        }
    )

    unique_entities = {
        (
            str(row.get("entity_type") or ""),
            row["identity"],
        )
        for row in period_rows
    }

    entity_snapshot_rows = {}

    for row in period_rows:
        key = (
            str(row.get("snapshot_folder") or ""),
            str(row.get("entity_type") or ""),
            row["identity"],
        )

        entity_snapshot_rows.setdefault(key, row)

    item_observation_counts = Counter()
    item_snapshot_sets = {}

    for row in entity_snapshot_rows.values():
        name = str(row.get("name") or "").strip()

        if not name:
            continue

        key = (
            str(row.get("entity_type") or ""),
            str(row.get("artist") or ""),
            name,
        )

        item_observation_counts[key] += 1
        item_snapshot_sets.setdefault(key, set()).add(
            str(row.get("snapshot_folder") or "")
        )

    sorted_items = sorted(
        item_observation_counts.items(),
        key=lambda item: (
            -item[1],
            item[0][2].casefold(),
            item[0][1].casefold(),
            item[0][0],
        ),
    )

    top_items = [
        {
            "entityType": key[0],
            "artist": key[1] or None,
            "name": key[2],
            "observationCount": count,
            "snapshotCount": len(
                item_snapshot_sets.get(key, set())
            ),
        }
        for key, count in sorted_items[:10]
    ]

    source_counts = Counter(
        str(row.get("source") or "unknown")
        for row in period_rows
    )

    entity_type_counts = Counter(
        str(row.get("entity_type") or "unknown")
        for row in period_rows
    )

    observation_count = len(period_rows)
    snapshot_count = len(snapshot_folders)
    observed_day_count = len(observed_days)
    inclusive_day_count = (
        requested_end - requested_start
    ).days + 1

    limitations = [base_limitation]
    warnings = []

    if partial_coverage:
        message = (
            "Only the overlapping Recent Apple range "
            f"{query_start} through {query_end} was searched; "
            "the selected period extends beyond warehouse "
            "coverage."
        )
        limitations.insert(0, message)
        warnings.append(
            {
                "code": (
                    "RECENT_APPLE_PARTIAL_COVERAGE"
                ),
                "message": message,
                "sourceId": (
                    "apple_live_snapshot_warehouse"
                ),
            }
        )

    if observation_count > 0:
        intermittent_message = (
            "Snapshot coverage is intermittent: "
            f"{snapshot_count} snapshots were captured on "
            f"{observed_day_count} of {inclusive_day_count} "
            "selected calendar days."
        )
        limitations.append(intermittent_message)

        if observed_day_count < inclusive_day_count:
            warnings.append(
                {
                    "code": (
                        "RECENT_APPLE_INTERMITTENT_COVERAGE"
                    ),
                    "message": intermittent_message,
                    "sourceId": (
                        "apple_live_snapshot_warehouse"
                    ),
                }
            )
    else:
        limitations.append(
            "No snapshot containing Recent Apple Objects was "
            "captured on a selected date."
        )

    if invalid_timestamp_count:
        limitations.append(
            f"{invalid_timestamp_count} warehouse rows had "
            "unusable snapshot timestamps and were excluded."
        )

    coverage_status = (
        "searched_with_evidence"
        if observation_count > 0
        else "searched_no_evidence"
    )

    evidence = {
        "status": "available",
        "observationCount": observation_count,
        "entitySnapshotObservationCount": len(
            entity_snapshot_rows
        ),
        "uniqueEntityCount": len(unique_entities),
        "snapshotCount": snapshot_count,
        "observedDayCount": observed_day_count,
        "observedDays": observed_days,
        "sourceCounts": dict(source_counts),
        "entityTypeCounts": dict(entity_type_counts),
        "topItems": top_items,
        "sourceNote": base_limitation,
    }

    return {
        "coverage": {
            "sourceId": "apple_live_snapshot_warehouse",
            "sourceType": "recent_apple_observation",
            "status": coverage_status,
            "recordsExamined": observation_count,
            "recordsMatched": observation_count,
            "coverageStart": str(query_start),
            "coverageEnd": str(query_end),
            "capturedAt": captured_at,
            "freshness": (
                "stale"
                if requested_end > coverage_end
                else "current"
            ),
            "limitations": limitations,
        },
        "evidence": evidence,
        "warnings": warnings,
        "provenance": {
            "evidenceId": (
                "recent-apple-snapshot-observations"
            ),
            "sourceId": "apple_live_snapshot_warehouse",
            "sourceLabel": (
                "Recent Apple Snapshot Warehouse"
            ),
            "sourceType": "recent_apple_observation",
            "recordCount": observation_count,
            "coverageStart": str(query_start),
            "coverageEnd": str(query_end),
            "capturedAt": captured_at,
            "notes": limitations,
        },
    }


def apply_recent_apple_to_result(result, recent_apple):
    replacement_coverage = recent_apple["coverage"]
    coverage = result.setdefault("coverage", [])

    for index, item in enumerate(coverage):
        if (
            item.get("sourceId")
            == "apple_live_snapshot_warehouse"
        ):
            coverage[index] = replacement_coverage
            break
    else:
        coverage.append(replacement_coverage)

    result["recentAppleEvidence"] = recent_apple[
        "evidence"
    ]

    result["warnings"] = [
        warning
        for warning in result.get("warnings", [])
        if warning.get("code")
        != "RECENT_APPLE_NOT_SEARCHED"
    ]

    result["warnings"].extend(
        recent_apple.get("warnings", [])
    )

    provenance = recent_apple.get("provenance")

    if provenance:
        provenance_items = result.setdefault(
            "provenance",
            [],
        )
        insert_index = 1 if provenance_items else 0
        provenance_items.insert(insert_index, provenance)

    evidence = result["recentAppleEvidence"]
    observation_count = int(
        evidence.get("observationCount") or 0
    )
    snapshot_count = int(
        evidence.get("snapshotCount") or 0
    )
    observed_day_count = int(
        evidence.get("observedDayCount") or 0
    )

    result["facts"] = [
        fact
        for fact in result.get("facts", [])
        if fact.get("id")
        != "recent-apple-period-summary"
    ]

    if observation_count > 0:
        result.setdefault("facts", []).append(
            {
                "id": "recent-apple-period-summary",
                "statement": (
                    "Recent Apple snapshot history contained "
                    f"{observation_count} observations across "
                    f"{snapshot_count} snapshots on "
                    f"{observed_day_count} calendar days."
                ),
                "confidence": "medium",
                "evidenceRefs": [
                    "recent-apple-snapshot-observations"
                ],
            }
        )

    activity = result.get("activity", {})
    activity_status = activity.get("status")
    actual_plays = int(
        activity.get("actualPlays") or 0
    )
    library_count = int(
        result.get("libraryEvidence", {}).get(
            "recordCount",
            0,
        )
        or 0
    )
    recent_status = evidence.get("status")

    narrative_parts = []

    if activity_status == "available":
        if actual_plays > 0:
            narrative_parts.append(
                f"Actual Listening returned {actual_plays} "
                "confirmed plays."
            )
        else:
            narrative_parts.append(
                "Actual Listening was searched and returned "
                "no confirmed plays."
            )
    elif activity_status == "unsupported_for_period":
        narrative_parts.append(
            "Actual Listening does not cover the selected "
            "period."
        )
    elif activity_status == "unavailable":
        narrative_parts.append(
            "Actual Listening was unavailable."
        )

    if library_count > 0:
        narrative_parts.append(
            f"Library Evidence returned {library_count} "
            "records."
        )
    else:
        narrative_parts.append(
            "Library Evidence was searched and returned no "
            "matching evidence."
        )

    if recent_status == "available":
        if observation_count > 0:
            narrative_parts.append(
                "Recent Apple Objects returned "
                f"{observation_count} observations across "
                f"{snapshot_count} snapshots on "
                f"{observed_day_count} calendar days."
            )
        else:
            narrative_parts.append(
                "Recent Apple Objects were searched and "
                "returned no observations."
            )
    elif recent_status == "unsupported_for_period":
        narrative_parts.append(
            "Recent Apple Objects do not cover the selected "
            "period."
        )
    elif recent_status == "unavailable":
        narrative_parts.append(
            "Recent Apple Objects were unavailable."
        )

    narrative_parts.append(
        "Playback context was not searched."
    )

    evidence_found = (
        actual_plays > 0
        or library_count > 0
        or observation_count > 0
    )

    summary = result.setdefault("summary", {})
    summary["status"] = (
        "partial_coverage"
        if evidence_found
        else "no_matching_evidence"
    )

    if actual_plays > 0:
        summary["headline"] = (
            "Confirmed Actual Listening was found for this "
            "period."
        )
    elif observation_count > 0:
        summary["headline"] = (
            "Recent Apple Objects were found for this period."
        )
    elif library_count > 0:
        summary["headline"] = (
            "Library Evidence was found for this period."
        )
    else:
        summary["headline"] = (
            "No matching evidence was found in the searched "
            "sources."
        )

    summary["narrative"] = " ".join(narrative_parts)

    confidence = result.setdefault("confidence", {})
    confidence["level"] = (
        "medium"
        if (
            activity_status == "available"
            or library_count > 0
            or observation_count > 0
        )
        else "low"
    )

    confidence["reasons"] = [
        "Actual Listening, Library Evidence, and Recent "
        "Apple source status are reported independently.",
        "Recent Apple Objects remain observations rather "
        "than confirmed plays.",
    ]

    limitations = [
        limitation
        for limitation in confidence.get(
            "limitations",
            [],
        )
        if (
            "Recent Apple Objects" not in limitation
            and "playback context" not in limitation.lower()
        )
    ]

    if observation_count > 0:
        limitations.append(
            "Recent Apple Objects provide intermittent "
            "snapshot coverage, not continuous listening "
            "history."
        )
    elif recent_status == "unsupported_for_period":
        limitations.append(
            "Recent Apple Objects do not cover the selected "
            "period."
        )

    limitations.append(
        "Playback context was not searched."
    )

    confidence["limitations"] = list(
        dict.fromkeys(limitations)
    )