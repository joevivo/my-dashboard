from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseball.semantics.strat_card_rating_semantics_v1 import (  # noqa: E402
    compare_numeric,
    compare_ordinal,
    load_registry,
)


SCHEMA_VERSION = "bie.strat-transaction-rating-analysis.v1"


FIELD_ALIASES = {
    "pitcherhold": "pitcher_hold",
    "hold": "pitcher_hold",
    "throwingarm": "throwing_arm",
    "arm": "throwing_arm",
    "catcherarm": "throwing_arm",
    "outfieldarm": "throwing_arm",
    "running": "running",
    "runrating": "running",
    "speed": "running",
    "defensiverange": "defensive_range",
    "range": "defensive_range",
    "errorrating": "error_rating",
    "error": "error_rating",
    "catcherthrowingerror": "catcher_throwing_error",
    "throwingerror": "catcher_throwing_error",
    "t": "catcher_throwing_error",
    "passedball": "passed_ball",
    "pb": "passed_ball",
    "wildpitch": "wild_pitch",
    "wp": "wild_pitch",
    "balk": "balk",
    "bk": "balk",
    "stealingclass": "stealing_class",
    "stealing": "stealing_class",
    "steal": "stealing_class",
    "bunting": "bunting",
    "bunt": "bunting",
    "hitandrun": "hit_and_run",
    "hitrun": "hit_and_run",
}


def normalize_field_name(value: Any) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(value).strip().lower(),
    )


def canonical_metric_for_field(
    field_name: Any,
) -> str | None:
    normalized = normalize_field_name(field_name)

    registry = load_registry()

    for metric_name in (
        list(registry["numericMetrics"])
        + list(registry["ordinalMetrics"])
    ):
        if normalized == normalize_field_name(metric_name):
            return metric_name

    return FIELD_ALIASES.get(normalized)


def canonicalize_rating_profile(
    profile: Mapping[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    list[str],
]:
    canonical: dict[str, dict[str, Any]] = {}
    ignored: list[str] = []

    for field_name, value in profile.items():
        metric_name = canonical_metric_for_field(
            field_name
        )

        if metric_name is None:
            ignored.append(str(field_name))
            continue

        if metric_name in canonical:
            existing = canonical[metric_name]["field"]

            raise ValueError(
                "Duplicate fields resolve to metric "
                f"{metric_name!r}: "
                f"{existing!r} and {field_name!r}"
            )

        canonical[metric_name] = {
            "field": str(field_name),
            "value": value,
        }

    return canonical, sorted(ignored)


def metric_direction_rule(
    metric_name: str,
) -> dict[str, Any]:
    registry = load_registry()

    numeric = registry["numericMetrics"]

    if metric_name in numeric:
        metric = numeric[metric_name]

        return {
            "kind": "numeric",
            "comparison": metric["comparison"],
            "bestDirection": metric.get(
                "bestDirection"
            ),
        }

    ordinal = registry["ordinalMetrics"]

    if metric_name in ordinal:
        return {
            "kind": "ordinal",
            "bestToWorst": ordinal[
                metric_name
            ]["bestToWorst"],
        }

    raise KeyError(
        f"Unknown Strat metric: {metric_name}"
    )


def compare_metric_values(
    metric_name: str,
    candidate_value: Any,
    incumbent_value: Any,
) -> int:
    registry = load_registry()

    if metric_name in registry["numericMetrics"]:
        return compare_numeric(
            metric_name,
            candidate_value,
            incumbent_value,
        )

    if metric_name in registry["ordinalMetrics"]:
        return compare_ordinal(
            metric_name,
            candidate_value,
            incumbent_value,
        )

    raise KeyError(
        f"Unknown Strat metric: {metric_name}"
    )


def compare_rating_profiles(
    candidate_profile: Mapping[str, Any],
    incumbent_profile: Mapping[str, Any],
) -> dict[str, Any]:
    candidate, candidate_ignored = (
        canonicalize_rating_profile(
            candidate_profile
        )
    )

    incumbent, incumbent_ignored = (
        canonicalize_rating_profile(
            incumbent_profile
        )
    )

    candidate_metrics = set(candidate)
    incumbent_metrics = set(incumbent)

    shared_metrics = sorted(
        candidate_metrics & incumbent_metrics
    )

    candidate_only = sorted(
        candidate_metrics - incumbent_metrics
    )

    incumbent_only = sorted(
        incumbent_metrics - candidate_metrics
    )

    comparisons: list[dict[str, Any]] = []

    for metric_name in shared_metrics:
        candidate_item = candidate[metric_name]
        incumbent_item = incumbent[metric_name]

        result_value = compare_metric_values(
            metric_name,
            candidate_item["value"],
            incumbent_item["value"],
        )

        if result_value > 0:
            result = "candidate_better"
        elif result_value < 0:
            result = "incumbent_better"
        else:
            result = "equal"

        comparisons.append(
            {
                "metricName": metric_name,
                "candidateField": candidate_item[
                    "field"
                ],
                "candidateValue": candidate_item[
                    "value"
                ],
                "incumbentField": incumbent_item[
                    "field"
                ],
                "incumbentValue": incumbent_item[
                    "value"
                ],
                "result": result,
                "directionRule": (
                    metric_direction_rule(
                        metric_name
                    )
                ),
            }
        )

    candidate_better = [
        row
        for row in comparisons
        if row["result"] == "candidate_better"
    ]

    incumbent_better = [
        row
        for row in comparisons
        if row["result"] == "incumbent_better"
    ]

    equal = [
        row
        for row in comparisons
        if row["result"] == "equal"
    ]

    if candidate_better and not incumbent_better:
        comparison_summary = "candidate_advantage"
    elif incumbent_better and not candidate_better:
        comparison_summary = "incumbent_advantage"
    elif not candidate_better and not incumbent_better:
        comparison_summary = "equal"
    else:
        comparison_summary = "mixed"

    return {
        "comparisons": comparisons,
        "counts": {
            "compared": len(comparisons),
            "candidateBetter": len(
                candidate_better
            ),
            "incumbentBetter": len(
                incumbent_better
            ),
            "equal": len(equal),
            "candidateOnly": len(
                candidate_only
            ),
            "incumbentOnly": len(
                incumbent_only
            ),
        },
        "summary": comparison_summary,
        "strengths": candidate_better,
        "liabilities": incumbent_better,
        "equalRatings": equal,
        "candidateOnlyMetrics": candidate_only,
        "incumbentOnlyMetrics": incumbent_only,
        "ignoredFields": {
            "candidate": candidate_ignored,
            "incumbent": incumbent_ignored,
        },
    }


def integer_dollars(
    value: Any,
    field_name: str,
) -> int:
    try:
        dollars = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be an integer "
            f"dollar amount; received {value!r}"
        ) from exc

    if dollars < 0:
        raise ValueError(
            f"{field_name} cannot be negative"
        )

    return dollars


def analyze_transaction(
    candidate: Mapping[str, Any],
    incumbent: Mapping[str, Any],
    cash_available_dollars: int = 0,
) -> dict[str, Any]:
    candidate_name = str(
        candidate.get("name", "Candidate")
    )

    incumbent_name = str(
        incumbent.get("name", "Incumbent")
    )

    candidate_salary = integer_dollars(
        candidate.get("salaryDollars"),
        "candidate.salaryDollars",
    )

    incumbent_salary = integer_dollars(
        incumbent.get("salaryDollars"),
        "incumbent.salaryDollars",
    )

    cash_available = integer_dollars(
        cash_available_dollars,
        "cashAvailableDollars",
    )

    candidate_ratings = candidate.get(
        "ratings",
        {},
    )

    incumbent_ratings = incumbent.get(
        "ratings",
        {},
    )

    if not isinstance(candidate_ratings, Mapping):
        raise ValueError(
            "candidate.ratings must be an object"
        )

    if not isinstance(incumbent_ratings, Mapping):
        raise ValueError(
            "incumbent.ratings must be an object"
        )

    salary_delta = (
        candidate_salary - incumbent_salary
    )

    cash_after = cash_available - salary_delta

    shortfall = max(0, -cash_after)

    rating_analysis = compare_rating_profiles(
        candidate_ratings,
        incumbent_ratings,
    )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "decisionSupportOnly": True,
        "candidate": {
            "name": candidate_name,
            "salaryDollars": candidate_salary,
        },
        "incumbent": {
            "name": incumbent_name,
            "salaryDollars": incumbent_salary,
        },
        "salary": {
            "cashAvailableDollars": (
                cash_available
            ),
            "salaryDeltaDollars": salary_delta,
            "cashAfterTransactionDollars": (
                cash_after
            ),
            "shortfallDollars": shortfall,
            "affordable": shortfall == 0,
        },
        "ratingAnalysis": rating_analysis,
    }


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8-sig")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"{path} must contain a JSON object"
        )

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a Strat transaction candidate "
            "against an incumbent using canonical "
            "rating directionality."
        )
    )

    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--incumbent",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--cash",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--output",
        type=Path,
    )

    args = parser.parse_args()

    report = analyze_transaction(
        load_json_object(args.candidate),
        load_json_object(args.incumbent),
        args.cash,
    )

    rendered = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    )

    if args.output:
        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output.write_text(
            rendered + "\n",
            encoding="utf-8",
        )
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
