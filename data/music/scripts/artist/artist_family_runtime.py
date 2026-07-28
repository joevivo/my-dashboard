from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping
import unicodedata


FAMILIES_PATH = (
    Path(__file__).resolve().parents[2]
    / "curated"
    / "artistFamilies.json"
)

ARTIST_ALIASES = {
    "h sker d": "husker du",
    "h?sker d?": "husker du",
    "husker du": "husker du",
    "love rockets": "love and rockets",
    "love and rockets": "love and rockets",
    "the scorpions": "scorpions",
    "scorpions": "scorpions",
    "the eagles": "eagles",
    "eagles": "eagles",
}


def normalize_artist_key(value: Any) -> str:
    text = unicodedata.normalize(
        "NFD",
        str(value or "").strip().casefold(),
    )
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def canonical_artist_key(value: Any) -> str:
    normalized = normalize_artist_key(value)
    aliased = ARTIST_ALIASES.get(normalized, normalized)

    if aliased.startswith("the "):
        aliased = aliased[4:]

    return ARTIST_ALIASES.get(aliased, aliased)


def load_artist_families() -> list[dict[str, Any]]:
    try:
        payload = json.loads(
            FAMILIES_PATH.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    return [
        deepcopy(row)
        for row in payload
        if isinstance(row, Mapping)
    ]


def resolve_artist_family(
    artist_name: Any,
) -> dict[str, Any] | None:
    target_key = canonical_artist_key(artist_name)

    for family in load_artist_families():
        members = family.get("members")

        if not isinstance(members, list):
            continue

        matched = any(
            canonical_artist_key(member) == target_key
            for member in members
        )

        if not matched:
            continue

        result = deepcopy(family)
        family_name = result.get("familyName")
        primary_artist = result.get("primaryArtist")

        result.setdefault(
            "familyId",
            canonical_artist_key(family_name),
        )
        result.setdefault(
            "primaryArtistKey",
            canonical_artist_key(primary_artist),
        )

        return result

    return None


def _number(value: Any) -> float | int:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0

    return int(number) if number.is_integer() else number


def build_family_metrics(
    family: Mapping[str, Any] | None,
    run_artist_query: Callable[
        [str],
        Mapping[str, Any] | None,
    ],
) -> dict[str, Any] | None:
    if not isinstance(family, Mapping):
        return None

    members = family.get("members")

    if not isinstance(members, list):
        return None

    metrics: dict[str, Any] = {
        "familyName": family.get("familyName"),
        "primaryArtist": family.get("primaryArtist"),
        "actualPlays": 0,
        "actualSkips": 0,
        "hoursListened": 0,
        "listeningDurationMs": 0,
        "libraryEvidenceRecords": 0,
        "yearsActive": 0,
        "firstPlayedDate": None,
        "latestPlayedDate": None,
        "membersMatched": [],
    }

    seen: set[str] = set()

    for member in members:
        result = run_artist_query(str(member))

        if not isinstance(result, Mapping) or result.get("error"):
            continue

        canonical_key = canonical_artist_key(
            result.get("artist") or member
        )

        if canonical_key in seen:
            continue

        seen.add(canonical_key)

        for key in (
            "actualPlays",
            "actualSkips",
            "hoursListened",
            "listeningDurationMs",
            "libraryEvidenceRecords",
        ):
            metrics[key] += _number(result.get(key))

        first_date = result.get("firstPlayedDate")
        latest_date = result.get("latestPlayedDate")

        if first_date and (
            metrics["firstPlayedDate"] is None
            or first_date < metrics["firstPlayedDate"]
        ):
            metrics["firstPlayedDate"] = first_date

        if latest_date and (
            metrics["latestPlayedDate"] is None
            or latest_date > metrics["latestPlayedDate"]
        ):
            metrics["latestPlayedDate"] = latest_date

        timeline = result.get("timeline")

        metrics["membersMatched"].append({
            "artist": result.get("artist") or member,
            "query": member,
            "actualPlays": _number(result.get("actualPlays")),
            "actualSkips": _number(result.get("actualSkips")),
            "hoursListened": _number(result.get("hoursListened")),
            "libraryEvidenceRecords": _number(
                result.get("libraryEvidenceRecords")
            ),
            "yearsActive": _number(result.get("yearsActive")),
            "firstPlayedDate": first_date or None,
            "latestPlayedDate": latest_date or None,
            "timeline": (
                deepcopy(timeline)
                if isinstance(timeline, list)
                else []
            ),
        })

    active_years = {
        str(row["year"])
        for member in metrics["membersMatched"]
        for row in member["timeline"]
        if isinstance(row, Mapping) and row.get("year")
    }

    metrics["yearsActive"] = len(active_years)
    metrics["hoursListened"] = round(
        float(metrics["hoursListened"]),
        1,
    )

    first_member_plays = (
        metrics["membersMatched"][0]["actualPlays"]
        if metrics["membersMatched"]
        else 0
    )

    metrics["familyAmplificationFactor"] = (
        round(
            metrics["actualPlays"] / first_member_plays,
            2,
        )
        if first_member_plays
        else None
    )

    return metrics
