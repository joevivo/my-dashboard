from pathlib import Path
import duckdb
from datetime import datetime

ROOT = Path(".").resolve()
DB_PATH = ROOT / "data" / "music" / "music.db"
OUT_PATH = ROOT / "docs" / "music" / "album-shape-v0.md"

MIN_EVENTS_TO_DISPLAY = 50

AMBIGUOUS_ALBUM_TITLES = {
    "greatest hits",
    "hit",
    "complete",
    "document",
    "madonna",
    "eye",
    "head games",
    "the wall",
    "the open door - ep",
    "blind faith",
}

def is_ambiguous_album(album):
    if not album:
        return True

    key = album.strip().lower()

    if key in AMBIGUOUS_ALBUM_TITLES:
        return True

    generic_phrases = [
        "greatest hits",
        "best of",
        "essential",
        "collection",
        "anthology",
        "complete",
        "hits",
    ]

    return any(phrase in key for phrase in generic_phrases)

def classify_shape(year_counts, years):
    counts = [year_counts.get(year, 0) for year in years]
    total = sum(counts)

    if total == 0:
        return "Not present"

    peak_count = max(counts)
    peak_share = peak_count / total

    last_two = sum(year_counts.get(year, 0) for year in years[-2:])
    last_two_share = last_two / total

    if peak_share >= 0.50:
        if last_two_share >= 0.40:
            return "Recent resurgence album"
        return "Spike-heavy album"

    if last_two_share >= 0.40:
        return "Recent resurgence album"

    if peak_share >= 0.30:
        return "Peak plus steady return"

    return "Steady album"

def classify_context(container_counts):
    total = sum(container_counts.values())

    if total == 0:
        return "Unknown context"

    album = container_counts.get("ALBUM", 0)
    playlist = container_counts.get("PLAYLIST", 0)
    unknown = container_counts.get("UNKNOWN", 0)
    radio = container_counts.get("RADIO", 0)
    blank = container_counts.get("(blank)", 0)

    largest_type = max(container_counts, key=lambda k: container_counts[k])
    largest_share = container_counts[largest_type] / total

    if album / total >= 0.40 or largest_type == "ALBUM":
        return "Album-centered"

    if playlist / total >= 0.40 or largest_type == "PLAYLIST":
        return "Playlist-carried"

    if unknown / total >= 0.40 or largest_type == "UNKNOWN":
        return "Unknown/context-heavy"

    if radio / total >= 0.30 or largest_type == "RADIO":
        return "Radio-carried"

    if blank / total >= 0.30 or largest_type == "(blank)":
        return "Blank-context-heavy"

    return "Mixed context"

def md_table(headers, rows):
    if not rows:
        return "_No rows found._"

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        cleaned = []
        for value in row:
            cleaned.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(cleaned) + " |")

    return "\n".join(lines)

def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    year_rows = con.execute("""
        SELECT DISTINCT YEAR(TRY_CAST(event_start_timestamp AS TIMESTAMP)) AS year
        FROM apple_music_play_activity
        WHERE TRY_CAST(event_start_timestamp AS TIMESTAMP) IS NOT NULL
        ORDER BY year
    """).fetchall()

    years = [row[0] for row in year_rows if row[0] is not None]
    max_years = len(years)

    album_year_rows = con.execute("""
        SELECT
            NULLIF(TRIM(album_name), '') AS album,
            YEAR(TRY_CAST(event_start_timestamp AS TIMESTAMP)) AS year,
            COUNT(*) AS events
        FROM apple_music_play_activity
        WHERE album_name IS NOT NULL
          AND TRY_CAST(event_start_timestamp AS TIMESTAMP) IS NOT NULL
        GROUP BY 1, 2
    """).fetchall()

    album_container_rows = con.execute("""
        SELECT
            NULLIF(TRIM(album_name), '') AS album,
            COALESCE(NULLIF(TRIM(container_type), ''), '(blank)') AS container_type,
            COUNT(*) AS events
        FROM apple_music_play_activity
        WHERE album_name IS NOT NULL
        GROUP BY 1, 2
    """).fetchall()

    album_year_counts = {}
    album_container_counts = {}

    for album, year, events in album_year_rows:
        if not album or str(album).upper() in {"UNKNOWN", "NONE", "NULL"}:
            continue

        album_year_counts.setdefault(album, {})
        album_year_counts[album][year] = events

    for album, container_type, events in album_container_rows:
        if not album or str(album).upper() in {"UNKNOWN", "NONE", "NULL"}:
            continue

        album_container_counts.setdefault(album, {})
        album_container_counts[album][container_type] = events

    records = []

    for album, year_counts in album_year_counts.items():
        active_years = len([year for year in years if year_counts.get(year, 0) > 0])
        total = sum(year_counts.get(year, 0) for year in years)

        if active_years != max_years:
            continue

        if total < MIN_EVENTS_TO_DISPLAY:
            continue

        container_counts = album_container_counts.get(album, {})
        peak_year = max(years, key=lambda year: year_counts.get(year, 0))
        peak_count = year_counts.get(peak_year, 0)
        peak_share = peak_count / total if total else 0
        recent_count = sum(year_counts.get(year, 0) for year in years[-2:])
        recent_share = recent_count / total if total else 0

        container_split = ", ".join(
            f"{key}: {value}"
            for key, value in sorted(container_counts.items(), key=lambda item: item[1], reverse=True)
        )

        records.append({
            "album": album,
            "active_years": active_years,
            "total": total,
            "peak_year": peak_year,
            "peak_count": peak_count,
            "peak_share": peak_share,
            "recent_share": recent_share,
            "shape": classify_shape(year_counts, years),
            "context": classify_context(container_counts),
            "ambiguous": is_ambiguous_album(album),
            "year_counts": ", ".join(f"{year}: {year_counts.get(year, 0)}" for year in years),
            "container_split": container_split,
        })

    records.sort(key=lambda x: (-x["total"], x["album"].lower()))

    by_shape = {}
    by_context = {}

    for record in records:
        by_shape.setdefault(record["shape"], []).append(record)
        by_context.setdefault(record["context"], []).append(record)

    shape_order = [
        "Steady album",
        "Peak plus steady return",
        "Spike-heavy album",
        "Recent resurgence album",
    ]

    context_order = [
        "Album-centered",
        "Playlist-carried",
        "Unknown/context-heavy",
        "Radio-carried",
        "Mixed context",
        "Blank-context-heavy",
    ]

    report = []
    report.append("# Album Shape v0")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Question")
    report.append("")
    report.append("Among albums that never leave, are they steady albums, spike albums, recent resurgences, playlist artifacts, or album-centered companions?")
    report.append("")
    report.append("## Coverage")
    report.append("")
    report.append(f"- Years: `{', '.join(str(year) for year in years)}`")
    report.append(f"- Required active years: `{max_years}`")
    report.append(f"- Minimum events displayed: `{MIN_EVENTS_TO_DISPLAY}`")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Shape Definitions")
    report.append("")
    report.append(md_table(
        ["Shape", "Meaning"],
        [
            ["Steady album", "Persistent across years without one dominant spike"],
            ["Peak plus steady return", "One clear peak year, but meaningful recurrence afterward"],
            ["Spike-heavy album", "One year explains at least half the album events"],
            ["Recent resurgence album", "Recent two-year period accounts for a large share of events"],
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Context Definitions")
    report.append("")
    report.append(md_table(
        ["Context", "Meaning"],
        [
            ["Album-centered", "Album container is dominant or at least 40% of events"],
            ["Playlist-carried", "Playlist context is dominant or at least 40% of events"],
            ["Unknown/context-heavy", "UNKNOWN context is dominant or at least 40% of events"],
            ["Radio-carried", "Radio is a major carrier"],
            ["Mixed context", "No single context dominates"],
            ["Blank-context-heavy", "Blank container value is unusually prominent"],
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Summary by Shape")
    report.append("")

    report.append(md_table(
        ["Shape", "Album Count", "Examples"],
        [
            [
                shape,
                len(by_shape.get(shape, [])),
                ", ".join(item["album"] for item in by_shape.get(shape, [])[:10])
            ]
            for shape in shape_order
            if by_shape.get(shape)
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Summary by Context")
    report.append("")

    report.append(md_table(
        ["Context", "Album Count", "Examples"],
        [
            [
                context,
                len(by_context.get(context, [])),
                ", ".join(item["album"] for item in by_context.get(context, [])[:10])
            ]
            for context in context_order
            if by_context.get(context)
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## High-Confidence Album Companions")
    report.append("")
    report.append("Rule: appears every available album year, meets event threshold, and is not flagged as title-ambiguous.")
    report.append("")

    high_confidence = [item for item in records if not item["ambiguous"]]

    report.append(md_table(
        ["Album", "Shape", "Context", "Total Events", "Peak Year", "Peak Share", "Recent Share", "Container Split"],
        [
            [
                item["album"],
                item["shape"],
                item["context"],
                item["total"],
                item["peak_year"],
                f"{item['peak_share']:.1%}",
                f"{item['recent_share']:.1%}",
                item["container_split"],
            ]
            for item in high_confidence[:60]
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Needs Identity Resolution")
    report.append("")
    report.append("Rule: appears every available album year but title is ambiguous, generic, compilation-like, or unsafe without artist metadata.")
    report.append("")

    needs_resolution = [item for item in records if item["ambiguous"]]

    report.append(md_table(
        ["Album", "Shape", "Context", "Total Events", "Peak Year", "Peak Share", "Recent Share", "Container Split"],
        [
            [
                item["album"],
                item["shape"],
                item["context"],
                item["total"],
                item["peak_year"],
                f"{item['peak_share']:.1%}",
                f"{item['recent_share']:.1%}",
                item["container_split"],
            ]
            for item in needs_resolution
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Research Notes")
    report.append("")
    report.append("- Album shape is useful, but album identity is weaker than artist identity until artist metadata is joined.")
    report.append("- Container context is critical: a persistent album may be album-centered, playlist-carried, unknown/context-heavy, or mixed.")
    report.append("- This should inform the future Permanent Companions UI, especially the difference between album listening and playlist-carried album presence.")
    report.append("")

    OUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote report: {OUT_PATH}")

if __name__ == "__main__":
    main()
