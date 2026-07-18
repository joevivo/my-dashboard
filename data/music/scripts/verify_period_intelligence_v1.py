import json
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "http://localhost:4000"
failures = []
passes = []


def request_json(path, params=None):
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE_URL}{path}{query}"

    try:
        with urlopen(url, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body)


def check(name, condition, detail=""):
    if condition:
        passes.append(name)
        return

    failures.append(f"{name}: {detail or 'condition failed'}")


zero_params = {"start": "2099-01-01", "end": "2099-01-01"}
canonical_status, canonical = request_json(
    "/api/music/query/period",
    zero_params,
)

coverage = {
    item.get("sourceType"): item
    for item in canonical.get("coverage", [])
}

check(
    "canonical_schema",
    canonical_status == 200
    and canonical.get("schemaVersion") == "music.period-intelligence.v1",
    f"status={canonical_status}",
)

check(
    "period_identity",
    canonical.get("period", {}).get("entityType") == "period"
    and canonical.get("period", {}).get("inclusiveDayCount") == 1,
)

check(
    "coverage_model",
    len(canonical.get("coverage", [])) == 4
    and coverage.get("library_evidence", {}).get("status")
    == "searched_no_evidence"
    and coverage.get("actual_listening", {}).get("status")
    == "not_searched",
)

check(
    "null_vs_zero_semantics",
    canonical.get("libraryEvidence", {}).get("recordCount") == 0
    and canonical.get("activity", {}).get("actualPlays") is None,
)

check(
    "canonical_has_no_flat_legacy_aliases",
    "tracksMatched" not in canonical
    and canonical.get("legacy", {}).get("tracksMatched") == 0,
)

compat_status, compatibility = request_json(
    "/api/music/time-machine",
    zero_params,
)

check(
    "compatibility_route",
    compat_status == 200
    and compatibility.get("schemaVersion")
    == canonical.get("schemaVersion")
    and compatibility.get("tracksMatched")
    == compatibility.get("legacy", {}).get("tracksMatched"),
    f"status={compat_status}",
)

invalid_status, invalid = request_json(
    "/api/music/query/period",
    {"start": "2026-02-30", "end": "2026-03-01"},
)

check(
    "invalid_calendar_date",
    invalid_status == 400
    and invalid.get("error", {}).get("code") == "INVALID_START_DATE",
    f"status={invalid_status}",
)

reversed_status, reversed_period = request_json(
    "/api/music/query/period",
    {"start": "2026-07-14", "end": "2026-07-01"},
)

check(
    "reversed_period",
    reversed_status == 400
    and reversed_period.get("error", {}).get("code")
    == "INVALID_PERIOD",
    f"status={reversed_status}",
)

missing_status, missing = request_json(
    "/api/music/query/period",
    {"start": "2026-07-01"},
)

check(
    "missing_end_date",
    missing_status == 400
    and missing.get("error", {}).get("code") == "INVALID_END_DATE",
    f"status={missing_status}",
)

for name in passes:
    print(f"TEST: {name}=PASS")

for failure in failures:
    print(f"TEST_FAILURE: {failure}")

print(f"TEST_COUNT: {len(passes) + len(failures)}")
print(f"PASS_COUNT: {len(passes)}")
print(f"FAIL_COUNT: {len(failures)}")

sys.exit(1 if failures else 0)
