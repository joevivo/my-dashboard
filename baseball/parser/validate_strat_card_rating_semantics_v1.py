from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseball.semantics.strat_card_rating_semantics_v1 import (  # noqa: E402
    REGISTRY_PATH,
    compare_numeric,
    compare_ordinal,
    is_better,
    load_registry,
)


REQUIRED_NUMERIC = {
    "pitcher_hold",
    "throwing_arm",
    "running",
    "defensive_range",
    "error_rating",
    "catcher_throwing_error",
    "passed_ball",
    "wild_pitch",
    "balk",
}

REQUIRED_ORDINAL = {
    "stealing_class",
    "bunting",
    "hit_and_run",
}


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

    registry = load_registry()

    assert_equal(
        "seasonAgnostic",
        registry.get("seasonAgnostic"),
        True,
        failures,
    )

    numeric_names = set(
        registry.get(
            "numericMetrics",
            {},
        )
    )

    ordinal_names = set(
        registry.get(
            "ordinalMetrics",
            {},
        )
    )

    missing_numeric = sorted(
        REQUIRED_NUMERIC - numeric_names
    )

    missing_ordinal = sorted(
        REQUIRED_ORDINAL - ordinal_names
    )

    if missing_numeric:
        failures.append(
            "Missing numeric metrics: "
            + ", ".join(missing_numeric)
        )

    if missing_ordinal:
        failures.append(
            "Missing ordinal metrics: "
            + ", ".join(missing_ordinal)
        )

    regression_cases = [
        (
            "hold_negative_beats_positive",
            compare_numeric(
                "pitcher_hold",
                "-4",
                "+3",
            ),
            1,
        ),
        (
            "hold_positive_loses_to_negative",
            compare_numeric(
                "pitcher_hold",
                "+3",
                "-4",
            ),
            -1,
        ),
        (
            "arm_negative_beats_positive",
            compare_numeric(
                "throwing_arm",
                "-3",
                "+2",
            ),
            1,
        ),
        (
            "running_high_beats_low",
            compare_numeric(
                "running",
                "1-17",
                "1-9",
            ),
            1,
        ),
        (
            "range_one_beats_four",
            compare_numeric(
                "defensive_range",
                "1",
                "4",
            ),
            1,
        ),
        (
            "error_zero_beats_sixteen",
            compare_numeric(
                "error_rating",
                "e0",
                "e16",
            ),
            1,
        ),
        (
            "throwing_error_one_beats_ten",
            compare_numeric(
                "catcher_throwing_error",
                "T-1",
                "T-10",
            ),
            1,
        ),
        (
            "passed_ball_one_beats_five",
            compare_numeric(
                "passed_ball",
                "pb-1",
                "pb-5",
            ),
            1,
        ),
        (
            "wild_pitch_zero_beats_thirteen",
            compare_numeric(
                "wild_pitch",
                "wp-0",
                "wp-13",
            ),
            1,
        ),
        (
            "balk_zero_beats_five",
            compare_numeric(
                "balk",
                "bk-0",
                "bk-5",
            ),
            1,
        ),
        (
            "stealing_a_beats_e",
            compare_ordinal(
                "stealing_class",
                "A",
                "E",
            ),
            1,
        ),
        (
            "bunting_a_beats_d",
            compare_ordinal(
                "bunting",
                "A",
                "D",
            ),
            1,
        ),
        (
            "hit_and_run_a_beats_d",
            compare_ordinal(
                "hit_and_run",
                "A",
                "D",
            ),
            1,
        ),
        (
            "pattin_hold_is_not_strength",
            is_better(
                "pitcher_hold",
                "+3",
                "0",
            ),
            False,
        ),
        (
            "running_direction_not_reversed",
            is_better(
                "running",
                "1-9",
                "1-17",
            ),
            False,
        ),
    ]

    for label, actual, expected in regression_cases:
        assert_equal(
            label,
            actual,
            expected,
            failures,
        )

    print("# RESULT SUMMARY")

    if failures:
        print(
            "STRAT_RATING_SEMANTICS_GATE: FAIL"
        )
        print(
            f"REGRESSION_CASES: "
            f"{len(regression_cases)}"
        )
        print(
            f"FAILURES: {len(failures)}"
        )

        for failure in failures:
            print(f"FAILURE: {failure}")

        return 1

    print(
        "STRAT_RATING_SEMANTICS_GATE: PASS"
    )
    print(
        f"NUMERIC_METRICS: "
        f"{len(numeric_names)}"
    )
    print(
        f"ORDINAL_METRICS: "
        f"{len(ordinal_names)}"
    )
    print(
        f"REGRESSION_CASES: "
        f"{len(regression_cases)}"
    )
    print("FAILURES: 0")
    print(
        "HOLD_DIRECTION: "
        "negative_better_positive_worse"
    )
    print(
        "RUNNING_DIRECTION: "
        "higher_upper_bound_better"
    )
    print(
        "PB_T_WP_BK_DIRECTION: "
        "lower_better"
    )
    print(
        "RANGE_ERROR_DIRECTION: "
        "lower_better"
    )
    print(
        "ARM_DIRECTION: "
        "negative_better_positive_worse"
    )
    print(
        "REGISTRY: "
        f"{REGISTRY_PATH.relative_to(ROOT).as_posix()}"
    )
    print(
        "NEXT_ACTION: Use the canonical comparator "
        "in player and transaction analysis."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
