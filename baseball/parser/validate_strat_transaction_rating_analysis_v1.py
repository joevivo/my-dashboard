from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseball.semantics.strat_transaction_rating_analysis_v1 import (  # noqa: E402
    SCHEMA_VERSION,
    analyze_transaction,
    canonical_metric_for_field,
    compare_rating_profiles,
)


def assert_equal(
    label: str,
    actual: Any,
    expected: Any,
    failures: list[str],
) -> None:
    if actual != expected:
        failures.append(
            f"{label}: expected {expected!r}, "
            f"received {actual!r}"
        )


def main() -> int:
    failures: list[str] = []

    alias_cases = {
        "hold": "pitcher_hold",
        "Pitcher Hold": "pitcher_hold",
        "arm": "throwing_arm",
        "runRating": "running",
        "range": "defensive_range",
        "error": "error_rating",
        "T": "catcher_throwing_error",
        "pb": "passed_ball",
        "wp": "wild_pitch",
        "bk": "balk",
        "steal": "stealing_class",
        "bunt": "bunting",
        "hitRun": "hit_and_run",
    }

    for field_name, expected in alias_cases.items():
        assert_equal(
            f"alias_{field_name}",
            canonical_metric_for_field(
                field_name
            ),
            expected,
            failures,
        )

    pattin = {
        "name": "Marty Pattin",
        "salaryDollars": 1_310_000,
        "ratings": {
            "hold": "+3",
            "wp": "wp-13",
            "range": "4",
            "error": "e0",
            "bk": "bk-0",
        },
    }

    boozer = {
        "name": "John Boozer",
        "salaryDollars": 500_000,
        "ratings": {
            "pitcherHold": "0",
            "wildPitch": "wp-0",
            "defensiveRange": "3",
            "errorRating": "e5",
            "balk": "bk-2",
        },
    }

    report = analyze_transaction(
        pattin,
        boozer,
        cash_available_dollars=270_000,
    )

    assert_equal(
        "schema",
        report["schemaVersion"],
        SCHEMA_VERSION,
        failures,
    )

    assert_equal(
        "decision_support_only",
        report["decisionSupportOnly"],
        True,
        failures,
    )

    salary = report["salary"]

    assert_equal(
        "salary_delta",
        salary["salaryDeltaDollars"],
        810_000,
        failures,
    )

    assert_equal(
        "cash_after",
        salary[
            "cashAfterTransactionDollars"
        ],
        -540_000,
        failures,
    )

    assert_equal(
        "shortfall",
        salary["shortfallDollars"],
        540_000,
        failures,
    )

    assert_equal(
        "affordable",
        salary["affordable"],
        False,
        failures,
    )

    ratings = report["ratingAnalysis"]

    assert_equal(
        "comparison_count",
        ratings["counts"]["compared"],
        5,
        failures,
    )

    assert_equal(
        "pattin_strength_count",
        ratings["counts"]["candidateBetter"],
        2,
        failures,
    )

    assert_equal(
        "pattin_liability_count",
        ratings["counts"]["incumbentBetter"],
        3,
        failures,
    )

    assert_equal(
        "pattin_summary",
        ratings["summary"],
        "mixed",
        failures,
    )

    strength_metrics = sorted(
        row["metricName"]
        for row in ratings["strengths"]
    )

    liability_metrics = sorted(
        row["metricName"]
        for row in ratings["liabilities"]
    )

    assert_equal(
        "pattin_strengths",
        strength_metrics,
        [
            "balk",
            "error_rating",
        ],
        failures,
    )

    assert_equal(
        "pattin_liabilities",
        liability_metrics,
        [
            "defensive_range",
            "pitcher_hold",
            "wild_pitch",
        ],
        failures,
    )

    broad_profile = compare_rating_profiles(
        {
            "running": "1-17",
            "arm": "-3",
            "pb": "pb-1",
            "steal": "A",
            "bunt": "A",
            "hitRun": "B",
        },
        {
            "runRating": "1-9",
            "throwingArm": "+2",
            "passedBall": "pb-5",
            "stealingClass": "E",
            "bunting": "D",
            "hitAndRun": "D",
        },
    )

    assert_equal(
        "broad_candidate_better",
        broad_profile["counts"][
            "candidateBetter"
        ],
        6,
        failures,
    )

    assert_equal(
        "broad_incumbent_better",
        broad_profile["counts"][
            "incumbentBetter"
        ],
        0,
        failures,
    )

    cheaper_report = analyze_transaction(
        {
            "name": "Candidate",
            "salaryDollars": 500_000,
            "ratings": {
                "hold": "-2",
            },
        },
        {
            "name": "Incumbent",
            "salaryDollars": 880_000,
            "ratings": {
                "hold": "+1",
            },
        },
        cash_available_dollars=100_000,
    )

    assert_equal(
        "cheaper_salary_delta",
        cheaper_report["salary"][
            "salaryDeltaDollars"
        ],
        -380_000,
        failures,
    )

    assert_equal(
        "cheaper_cash_after",
        cheaper_report["salary"][
            "cashAfterTransactionDollars"
        ],
        480_000,
        failures,
    )

    assert_equal(
        "cheaper_affordable",
        cheaper_report["salary"][
            "affordable"
        ],
        True,
        failures,
    )

    regression_cases = (
        len(alias_cases)
        + 15
    )

    print("# RESULT SUMMARY")

    if failures:
        print(
            "TRANSACTION_RATING_ANALYSIS_GATE: FAIL"
        )
        print(
            f"REGRESSION_CASES: "
            f"{regression_cases}"
        )
        print(
            f"FAILURES: {len(failures)}"
        )

        for failure in failures:
            print(f"FAILURE: {failure}")

        return 1

    print(
        "TRANSACTION_RATING_ANALYSIS_GATE: PASS"
    )
    print(
        f"FIELD_ALIASES_CHECKED: "
        f"{len(alias_cases)}"
    )
    print(
        f"REGRESSION_CASES: "
        f"{regression_cases}"
    )
    print("FAILURES: 0")
    print(
        "PATTIN_STRENGTHS: "
        "balk,error_rating"
    )
    print(
        "PATTIN_LIABILITIES: "
        "defensive_range,pitcher_hold,wild_pitch"
    )
    print(
        "PATTIN_VS_BOOZER_SHORTFALL: 540000"
    )
    print(
        "DECISION_SUPPORT_ONLY: true"
    )
    print(
        "NEXT_ACTION: Commit the completed "
        "Strat semantics and transaction-analysis layer."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
