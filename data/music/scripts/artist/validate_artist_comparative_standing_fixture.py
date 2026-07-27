from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from artist_comparative_standing import (
    ComparativeStandingValidationError,
    build_additive_family_population,
    build_historical_unique_object_sets,
    build_historical_unique_object_values,
    build_library_evidence_values,
    build_recent_apple_observation_values,
    build_years_represented_sets,
    build_years_represented_values,
    rank_positive_population,
    unavailable_metric_result,
)


fixture_path = Path(sys.argv[1])
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

assertion_count = 0


def check(condition: bool, message: str) -> None:
    global assertion_count
    assertion_count += 1

    if not condition:
        raise AssertionError(message)


fixture_aliases = fixture["identityFixture"]["aliases"]


def normalize(value: Any) -> str:
    return " ".join(
        str(value or "").strip().casefold().split()
    )


def canonicalize_fixture_artist(value: Any) -> str:
    key = normalize(value)
    return fixture_aliases.get(key, key)


check(
    fixture["schemaVersion"]
    == "music.artist-comparative-standing.fixture.v0",
    "Unexpected fixture schema version.",
)

check(
    fixture["sourceSemantics"]["historicalYearsRepresented"][
        "canonicalDateField"
    ]
    == "Last Played Date",
    "Years Represented source field changed.",
)

check(
    fixture["sourceSemantics"]["historicalUniqueObjectCount"][
        "logicalObjectKey"
    ]
    == ["entity_type", "entity_id"],
    "Logical-object key changed.",
)

for case in fixture["rankingCases"][:2]:
    actual = rank_positive_population(case["entries"])

    check(
        actual == case["expected"],
        f"Ranking case failed: {case['caseId']}",
    )

exclusion_case = fixture["rankingCases"][2]
exclusion_actual = rank_positive_population(
    exclusion_case["entries"]
)

check(
    sorted(exclusion_actual)
    == sorted(exclusion_case["expectedEligibleEntityIds"]),
    "Excluded values entered the population.",
)

check(
    all(
        result["populationSize"]
        == exclusion_case["expectedPopulationSize"]
        for result in exclusion_actual.values()
    ),
    "Excluded-value population size is incorrect.",
)

library_case = fixture["aggregationCases"][0]
library_values = build_library_evidence_values(
    library_case["records"],
    canonicalize_fixture_artist,
)

check(
    library_values
    == library_case["expectedCanonicalValues"],
    "Library Evidence aggregation failed.",
)

years_case = fixture["aggregationCases"][1]
year_sets = build_years_represented_sets(
    years_case["records"],
    canonicalize_fixture_artist,
)
year_values = build_years_represented_values(
    years_case["records"],
    canonicalize_fixture_artist,
)

check(
    year_sets == years_case["expectedCanonicalYearSets"],
    "Years Represented set aggregation failed.",
)

check(
    year_values == years_case["expectedCanonicalValues"],
    "Years Represented value aggregation failed.",
)

check(
    all(
        artist not in year_values
        for artist in years_case[
            "expectedExcludedCanonicalArtists"
        ]
    ),
    "Artist without governed year evidence entered the population.",
)

observation_case = fixture["aggregationCases"][2]
observation_values = build_recent_apple_observation_values(
    observation_case["rows"],
    canonicalize_fixture_artist,
)

check(
    observation_values
    == observation_case["expectedCanonicalValues"],
    "Recent Apple Observation aggregation failed.",
)

object_case = fixture["aggregationCases"][3]
object_sets = build_historical_unique_object_sets(
    object_case["rows"],
    canonicalize_fixture_artist,
)
object_values = build_historical_unique_object_values(
    object_case["rows"],
    canonicalize_fixture_artist,
)

check(
    object_sets
    == object_case["expectedCanonicalObjectKeys"],
    "Historical Unique Object set aggregation failed.",
)

check(
    object_values
    == object_case["expectedCanonicalValues"],
    "Historical Unique Object value aggregation failed.",
)

blank_id_case = fixture["validationCases"][0]
blank_id_error = None

try:
    build_historical_unique_object_values(
        blank_id_case["rows"],
        canonicalize_fixture_artist,
    )
except ComparativeStandingValidationError as error:
    blank_id_error = error.code

check(
    blank_id_error == blank_id_case["expectedErrorCode"],
    "Blank entity ID validation failed.",
)

conflict_case = fixture["validationCases"][1]
conflict_error = None

try:
    build_historical_unique_object_values(
        conflict_case["rows"],
        canonicalize_fixture_artist,
    )
except ComparativeStandingValidationError as error:
    conflict_error = error.code

check(
    conflict_error == conflict_case["expectedErrorCode"],
    "Typed-key artist conflict validation failed.",
)

response_case = fixture["responseCases"][0]

for expected in response_case["metrics"]:
    actual = unavailable_metric_result(
        expected["metricKey"],
        expected["unit"],
        entity_type=expected["entityType"],
        source=expected["source"],
        source_limitation=expected["sourceLimitation"],
    )

    check(
        actual == expected,
        (
            "Unavailable metric response failed: "
            f"{expected['metricKey']}"
        ),
    )

separation_case = fixture["populationSeparationCases"][0]
artist_population = dict(
    separation_case["standaloneArtistValues"]
)

family_population = build_additive_family_population(
    artist_population,
    separation_case["reviewedFamilies"],
    canonicalize_fixture_artist,
)

check(
    artist_population
    == separation_case["expectedArtistPopulation"],
    "Family aggregation altered the artist population.",
)

check(
    family_population
    == separation_case["expectedFamilyPopulation"],
    "Reviewed-family aggregation failed.",
)

family_rank_entries = [
    {
        "entityId": family_id,
        "status": "ranked",
        "value": value,
    }
    for family_id, value in family_population.items()
]

family_ranks = {
    family_id: result["rank"]
    for family_id, result in rank_positive_population(
        family_rank_entries
    ).items()
}

check(
    family_ranks == separation_case["expectedFamilyRanks"],
    "Reviewed-family ranking failed.",
)

check(
    all(
        family_id not in artist_population
        for family_id in family_population
    ),
    "Family identifier entered the artist population.",
)

check(
    separation_case[
        "familyIdentifiersAllowedInArtistPopulation"
    ]
    is False,
    "Fixture must prohibit family IDs in artist population.",
)

check(
    fixture["sourceSemantics"]["unavailableMetrics"][
        "legacyDailyAggregateFallbackAllowed"
    ]
    is False,
    "Legacy aggregate fallback must remain prohibited.",
)

print("PRODUCTION_FIXTURE_VALIDATION: PASS")
print(f"VALIDATION_ASSERTION_COUNT: {assertion_count}")
print(
    "RANKING_CASE_COUNT: "
    f"{len(fixture['rankingCases'])}"
)
print(
    "AGGREGATION_CASE_COUNT: "
    f"{len(fixture['aggregationCases'])}"
)
print(
    "VALIDATION_CASE_COUNT: "
    f"{len(fixture['validationCases'])}"
)
print(
    "UNAVAILABLE_RESPONSE_METRIC_COUNT: "
    f"{len(response_case['metrics'])}"
)
print(
    "POPULATION_SEPARATION_CASE_COUNT: "
    f"{len(fixture['populationSeparationCases'])}"
)
print("COMPETITION_RANKING: PASS")
print("MIDPOINT_TIE_PERCENTILE: PASS")
print("MISSING_VERSUS_ZERO: PASS")
print("LAST_PLAYED_DATE_ONLY: PASS")
print("TYPED_LOGICAL_OBJECT_KEY: PASS")
print("ARTIST_FAMILY_POPULATION_SEPARATION: PASS")
print("LEGACY_AGGREGATE_FALLBACK_PROHIBITED: PASS")