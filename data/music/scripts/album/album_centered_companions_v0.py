from pathlib import Path
import duckdb
from datetime import datetime

ROOT = Path(".").resolve()
DB_PATH = ROOT / "data" / "music" / "music.db"
OUT_PATH = ROOT / "docs" / "music" / "album-centered-companions-v0.md"

MIN_TOTAL_EVENTS = 50
MIN_ALBUM_EVENTS = 25

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

def classify_album_relationship(album_events, total_events):
    if total_events == 0:
        return "No data"

    share = album_events / total_events

    if share >= 0.50:
        return "Strong album-centered companion"

    if share >= 0.35:
        return "Album-centered companion"

    if share >= 0.25:
        return "Mixed but album-significant"

    return "Low album-container share"

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

    rows = con.execute("""
        WITH yearly AS (
            SELECT
                NULLIF(TRIM(album_name), '') AS album,
                YEAR(TRY_CAST(event_start_timestamp AS TIMESTAMP)) AS year,
                COUNT(*) AS events
            FROM apple_music_play_activity
            WHERE album_name IS NOT NULL
              AND TRY_CAST(event_start_timestamp AS TIMESTAMP) IS NOT NULL
            GROUP BY 1, 2
        ),
        year_summary AS (
            SELECT
                album,
                COUNT(DISTINCT year) AS years_active,
                MIN(year) AS first_year,
                MAX(year) AS latest_year,
                STRING_AGG(CAST(year AS VARCHAR), ', ' ORDER BY year) AS years,
                SUM(events) AS total_events
            FROM yearly
            GROUP BY album
        ),
        container_summary AS (
            SELECT
                NULLIF(TRIM(album_name), '') AS album,
                COALESCE(NULLIF(TRIM(container_type), ''), '(blank)') AS container_type,
                COUNT(*) AS events
            FROM apple_music_play_activity
            WHERE album_name IS NOT NULL
            GROUP BY 1, 2
        ),
        pivoted AS (
            SELECT
                album,
                SUM(CASE WHEN container_type = 'ALBUM' THEN events ELSE 0 END) AS album_events,
                SUM(CASE WHEN container_type = 'PLAYLIST' THEN events ELSE 0 END) AS playlist_events,
                SUM(CASE WHEN container_type = 'RADIO' THEN events ELSE 0 END) AS radio_events,
                SUM(CASE WHEN container_type = 'UNKNOWN' THEN events ELSE 0 END) AS unknown_events,
                SUM(CASE WHEN container_type = '(blank)' THEN events ELSE 0 END) AS blank_events,
                SUM(events) AS all_container_events
            FROM container_summary
            GROUP BY album
        )
        SELECT
            y.album,
            y.years_active,
            y.first_year,
            y.latest_year,
            y.years,
            y.total_events,
            p.album_events,
            p.playlist_events,
            p.radio_events,
            p.unknown_events,
            p.blank_events,
            p.all_container_events
        FROM year_summary y
        LEFT JOIN pivoted p ON p.album = y.album
        WHERE y.album IS NOT NULL
          AND UPPER(y.album) NOT IN ('UNKNOWN', 'NONE', 'NULL')
          AND y.years_active = ?
          AND y.total_events >= ?
          AND p.album_events >= ?
        ORDER BY p.album_events DESC, y.total_events DESC, y.album
    """, [max_years, MIN_TOTAL_EVENTS, MIN_ALBUM_EVENTS]).fetchall()

    records = []

    for row in rows:
        album = row[0]
        years_active = row[1]
        first_year = row[2]
        latest_year = row[3]
        years_text = row[4]
        total_events = row[5] or 0
        album_events = row[6] or 0
        playlist_events = row[7] or 0
        radio_events = row[8] or 0
        unknown_events = row[9] or 0
        blank_events = row[10] or 0

        album_share = album_events / total_events if total_events else 0

        records.append({
            "album": album,
            "years_active": years_active,
            "first_year": first_year,
            "latest_year": latest_year,
            "years": years_text,
            "total_events": total_events,
            "album_events": album_events,
            "album_share": album_share,
            "playlist_events": playlist_events,
            "radio_events": radio_events,
            "unknown_events": unknown_events,
            "blank_events": blank_events,
            "relationship": classify_album_relationship(album_events, total_events),
            "ambiguous": is_ambiguous_album(album),
        })

    high_confidence = [item for item in records if not item["ambiguous"]]
    needs_resolution = [item for item in records if item["ambiguous"]]

    report = []
    report.append("# Album-Centered Companions v0")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Question")
    report.append("")
    report.append("Which permanent album companions show the strongest evidence of intentional album-centered listening?")
    report.append("")
    report.append("## Coverage")
    report.append("")
    report.append(f"- Years: `{', '.join(str(year) for year in years)}`")
    report.append(f"- Required active years: `{max_years}`")
    report.append(f"- Minimum total events: `{MIN_TOTAL_EVENTS}`")
    report.append(f"- Minimum ALBUM-container events: `{MIN_ALBUM_EVENTS}`")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Relationship Definitions")
    report.append("")
    report.append(md_table(
        ["Relationship", "Rule"],
        [
            ["Strong album-centered companion", "ALBUM container is at least 50% of total events"],
            ["Album-centered companion", "ALBUM container is 35%–49.9% of total events"],
            ["Mixed but album-significant", "ALBUM container is 25%–34.9% of total events"],
            ["Low album-container share", "ALBUM container is below 25%, but still has at least 25 album events"],
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## High-Confidence Album-Centered Companions")
    report.append("")
    report.append("Rule: appears every available album year, has meaningful ALBUM-container activity, and is not flagged as title-ambiguous.")
    report.append("")
    report.append(md_table(
        [
            "Album",
            "Relationship",
            "Years Active",
            "Total Events",
            "Album Events",
            "Album Share",
            "Playlist",
            "Radio",
            "Unknown",
            "Blank",
        ],
        [
            [
                item["album"],
                item["relationship"],
                item["years_active"],
                item["total_events"],
                item["album_events"],
                f"{item['album_share']:.1%}",
                item["playlist_events"],
                item["radio_events"],
                item["unknown_events"],
                item["blank_events"],
            ]
            for item in high_confidence
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Needs Identity Resolution")
    report.append("")
    report.append("These also have meaningful ALBUM-container activity but need artist metadata before they can be trusted as specific works.")
    report.append("")
    report.append(md_table(
        [
            "Album",
            "Relationship",
            "Years Active",
            "Total Events",
            "Album Events",
            "Album Share",
            "Playlist",
            "Radio",
            "Unknown",
            "Blank",
        ],
        [
            [
                item["album"],
                item["relationship"],
                item["years_active"],
                item["total_events"],
                item["album_events"],
                f"{item['album_share']:.1%}",
                item["playlist_events"],
                item["radio_events"],
                item["unknown_events"],
                item["blank_events"],
            ]
            for item in needs_resolution
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Research Notes")
    report.append("")
    report.append("- This report is closer to `Albums I Actually Lived With` than the broader album-shape report.")
    report.append("- It intentionally separates album-centered behavior from playlist-carried persistence.")
    report.append("- It still needs artist metadata before ambiguous titles can be fully trusted.")
    report.append("- Strong candidates here should feed the future Desert Island 25 / Albums I Lived With research.")
    report.append("")

    OUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote report: {OUT_PATH}")

if __name__ == "__main__":
    main()
