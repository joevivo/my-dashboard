from __future__ import annotations

import re
import unicodedata

from artist_query_core import (
    ARTIST_ALIASES,
    _canonical_key_text,
    _norm_text,
    canonical_key,
    match_rank,
    norm,
    strip_leading_article,
)


def legacy_norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch) != "Mn"
    )
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def legacy_canonical_key(value: object) -> str:
    normalized = legacy_norm(value)
    aliased = ARTIST_ALIASES.get(
        normalized,
        normalized,
    )
    stripped = strip_leading_article(aliased)
    return ARTIST_ALIASES.get(
        stripped,
        stripped,
    )


def legacy_match_rank(
    query: object,
    artist: object,
) -> int | None:
    q = legacy_canonical_key(query)
    a = legacy_canonical_key(artist)

    if not q or not a:
        return None

    if q == a:
        return 1

    if len(q) < 3:
        return None

    if a.startswith(q):
        return 2

    artist_words = set(a.split())
    query_words = set(q.split())

    if query_words and query_words.issubset(artist_words):
        return 3

    if len(q) >= 4 and q in a:
        return 4

    return None


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    values = (
        None,
        "",
        "R.E.M.",
        "The Beatles",
        "Beatles",
        "Hüsker Dü",
        "Sinéad O'Connor",
        "Björk",
        "Tom Petty & The Heartbreakers",
        "Elvis Costello & The Attractions",
        "Bob Marley & The Wailers",
        "  THE   BEATLES  ",
    )

    for value in values:
        check(
            norm(value) == legacy_norm(value),
            f"Normalization changed for {value!r}.",
        )

        check(
            canonical_key(value)
            == legacy_canonical_key(value),
            f"Canonical key changed for {value!r}.",
        )

    pairs = (
        ("R.E.M.", "R.E.M."),
        ("Beatles", "The Beatles"),
        ("Bob Marley", "Bob Marley & The Wailers"),
        (
            "Elvis Costello",
            "Elvis Costello & The Attractions",
        ),
        (
            "Elvis Costello",
            "Elvis Costello & The Imposters",
        ),
        ("Neil Young", "Neil Young & Crazy Horse"),
        ("U2", "U2"),
        ("AB", "ABBA"),
        ("Unrelated", "The Beatles"),
    )

    for query, artist in pairs:
        check(
            match_rank(query, artist)
            == legacy_match_rank(query, artist),
            (
                "Match rank changed for "
                f"{query!r} / {artist!r}."
            ),
        )

    _norm_text.cache_clear()
    _canonical_key_text.cache_clear()

    for _ in range(10000):
        canonical_key("R.E.M.")
        canonical_key("The Beatles")
        canonical_key("U2")

    norm_info = _norm_text.cache_info()
    canonical_info = _canonical_key_text.cache_info()

    check(
        canonical_info.hits >= 29997,
        "Canonical cache did not record expected hits.",
    )

    check(
        canonical_info.currsize == 3,
        "Canonical cache size changed.",
    )

    check(
        norm_info.currsize == 3,
        "Normalization cache size changed.",
    )

    print("ARTIST_QUERY_NORMALIZATION_CACHE_VALIDATION: PASS")
    print(f"NORMALIZATION_PARITY_CASES: {len(values)}")
    print(f"CANONICAL_PARITY_CASES: {len(values)}")
    print(f"MATCH_RANK_PARITY_CASES: {len(pairs)}")
    print(f"NORM_CACHE_HITS: {norm_info.hits}")
    print(f"NORM_CACHE_MISSES: {norm_info.misses}")
    print(f"CANONICAL_CACHE_HITS: {canonical_info.hits}")
    print(f"CANONICAL_CACHE_MISSES: {canonical_info.misses}")
    print("NORMALIZATION_SEMANTICS: UNCHANGED")
    print("CANONICAL_KEY_SEMANTICS: UNCHANGED")
    print("FUZZY_MATCH_SEMANTICS: UNCHANGED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())