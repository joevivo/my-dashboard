from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REGISTRY_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "canonical"
    / "rules"
    / "strat_card_rating_semantics_v1.json"
)


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    return json.loads(
        REGISTRY_PATH.read_text(encoding="utf-8-sig")
    )


def _parse_signed_integer(value: Any) -> int:
    text = str(value).strip()

    if not re.fullmatch(r"[+-]?\d+", text):
        raise ValueError(
            f"Expected signed integer, received {value!r}"
        )

    return int(text)


def _parse_integer(value: Any) -> int:
    text = str(value).strip()

    if not re.fullmatch(r"\d+", text):
        raise ValueError(
            f"Expected integer, received {value!r}"
        )

    return int(text)


def _parse_one_to_upper_bound(value: Any) -> int:
    match = re.fullmatch(
        r"1-(\d+)",
        str(value).strip(),
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            f"Expected running rating such as 1-17, "
            f"received {value!r}"
        )

    return int(match.group(1))


def _parse_prefixed_integer(
    value: Any,
    prefix: str,
) -> int:
    text = str(value).strip()

    match = re.fullmatch(
        rf"{re.escape(prefix)}(\d+)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            f"Expected {prefix}<integer>, "
            f"received {value!r}"
        )

    return int(match.group(1))


def _numeric_value(
    metric_name: str,
    value: Any,
) -> int:
    registry = load_registry()

    metric = registry["numericMetrics"].get(
        metric_name
    )

    if metric is None:
        raise KeyError(
            f"Unknown numeric metric: {metric_name}"
        )

    value_format = metric["valueFormat"]

    if value_format == "signed_integer":
        return _parse_signed_integer(value)

    if value_format == "integer":
        return _parse_integer(value)

    if value_format == "one_to_upper_bound":
        return _parse_one_to_upper_bound(value)

    if value_format == "prefixed_integer":
        return _parse_prefixed_integer(
            value,
            metric["prefix"],
        )

    raise ValueError(
        f"Unsupported value format "
        f"{value_format!r} for {metric_name}"
    )


def compare_numeric(
    metric_name: str,
    left: Any,
    right: Any,
) -> int:
    """
    Return:
      1 when left is better,
      0 when equal,
     -1 when left is worse.
    """
    registry = load_registry()
    metric = registry["numericMetrics"][
        metric_name
    ]

    left_value = _numeric_value(
        metric_name,
        left,
    )

    right_value = _numeric_value(
        metric_name,
        right,
    )

    comparison = metric["comparison"]

    if left_value == right_value:
        return 0

    if comparison == "lower_is_better":
        return 1 if left_value < right_value else -1

    if comparison == "higher_is_better":
        return 1 if left_value > right_value else -1

    raise ValueError(
        f"Unsupported comparison rule "
        f"{comparison!r} for {metric_name}"
    )


def compare_ordinal(
    metric_name: str,
    left: Any,
    right: Any,
) -> int:
    """
    Return:
      1 when left is better,
      0 when equal,
     -1 when left is worse.
    """
    registry = load_registry()

    metric = registry["ordinalMetrics"].get(
        metric_name
    )

    if metric is None:
        raise KeyError(
            f"Unknown ordinal metric: {metric_name}"
        )

    order = [
        str(value).upper()
        for value in metric["bestToWorst"]
    ]

    left_text = str(left).strip().upper()
    right_text = str(right).strip().upper()

    if left_text not in order:
        raise ValueError(
            f"Unknown {metric_name} value: {left!r}"
        )

    if right_text not in order:
        raise ValueError(
            f"Unknown {metric_name} value: {right!r}"
        )

    left_index = order.index(left_text)
    right_index = order.index(right_text)

    if left_index == right_index:
        return 0

    return 1 if left_index < right_index else -1


def is_better(
    metric_name: str,
    candidate: Any,
    incumbent: Any,
) -> bool:
    registry = load_registry()

    if metric_name in registry["numericMetrics"]:
        return (
            compare_numeric(
                metric_name,
                candidate,
                incumbent,
            )
            > 0
        )

    if metric_name in registry["ordinalMetrics"]:
        return (
            compare_ordinal(
                metric_name,
                candidate,
                incumbent,
            )
            > 0
        )

    raise KeyError(
        f"Unknown Strat rating metric: {metric_name}"
    )
