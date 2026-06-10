from pathlib import Path
import csv
import duckdb
from datetime import datetime

ROOT = Path(".").resolve()
ARTIST_SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")
DB_PATH = ROOT / "data" / "music" / "music.db"
OUT_PATH = ROOT / "docs" / "music" / "permanent-companions-report-v1.md"

EXPECTED_ARTISTS = [
    "The Beatles",
    "Wilco",
    "Grateful Dead",
    "Brian Eno",
    "Bob Dylan",
    "Matt Pond PA",
    "Michelle Shocked",
    "R.E.M.",
    "Camper Van Beethoven",
    "Pearl Jam",
    "Pixies",
    "Foo Fighters",
]

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

def parse_artist(track_description):
    if not track_description:
        return None

    value = track_description.strip()

    if " - " not in value:
        return None

    artist = value.split(" - ", 1)[0].strip()

    if not artist:
        return None

    if artist.upper() in {"UNKNOWN", "N/A", "NONE", "NULL"}:
        return None

    return artist

def parse_year(date_played):
    if not date_played:
        return None

    value = str(date_played).strip()

    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])

    return None

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
        values = []
        for value in row:
            if value is None:
                values.append("")
            else:
                values.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)

def load_artists():
    if not ARTIST_SOURCE.exists():
        raise FileNotFoundError(f"Artist source not found: {ARTIST_SOURCE}")

    artist_years = {}
    artist_events = {}
    total_rows = 0
    skipped = 0

    with ARTIST_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1

            artist = parse_artist(row.get("Track Description"))
            year = parse_year(row.get("Date Played"))

            if not artist or not year:
                skipped += 1
                continue

            artist_years.setdefault(artist, set()).add(year)
            artist_events[artist] = artist_events.get(artist, 0) + 1

    artists = []

    for artist, years in artist_years.items():
        years_sorted = sorted(years)
        artists.append({
            "artist": artist,
            "years_active": len(years_sorted),
            "first_year": years_sorted[0],
            "latest_year": years_sorted[-1],
            "years": ", ".join(str(y) for y in years_sorted),
            "events": artist_events.get(artist, 0),
        })

    artists.sort(key=lambda x: (-x["years_active"], -x["events"], x["artist"].lower()))

    coverage_years = sorted({year for years in artist_years.values() for year in years})

    return artists, coverage_years, total_rows, skipped

def load_albums():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Music database not found: {DB_PATH}")

    con = duckdb.connect(str(DB_PATH), read_only=True)

    rows = con.execute("""
        WITH yearly AS (
            SELECT DISTINCT
                NULLIF(TRIM(album_name), '') AS album,
                YEAR(TRY_CAST(event_start_timestamp AS TIMESTAMP)) AS year
            FROM apple_music_play_activity
            WHERE album_name IS NOT NULL
              AND TRY_CAST(event_start_timestamp AS TIMESTAMP) IS NOT NULL
        ),
        events AS (
            SELECT
                NULLIF(TRIM(album_name), '') AS album,
                COUNT(*) AS listening_events
            FROM apple_music_play_activity
            WHERE album_name IS NOT NULL
            GROUP BY 1
        ),
        container_split AS (
            SELECT
                NULLIF(TRIM(album_name), '') AS album,
                COALESCE(NULLIF(TRIM(container_type), ''), '(blank)') AS container_type,
                COUNT(*) AS listening_events
            FROM apple_music_play_activity
            WHERE album_name IS NOT NULL
            GROUP BY 1, 2
        ),
        container_summary AS (
            SELECT
                album,
                STRING_AGG(container_type || ': ' || CAST(listening_events AS VARCHAR), ', ' ORDER BY listening_events DESC) AS container_split
            FROM container_split
            GROUP BY album
        )
        SELECT
            y.album,
            COUNT(DISTINCT y.year) AS years_active,
            MIN(y.year) AS first_year,
            MAX(y.year) AS latest_year,
            STRING_AGG(CAST(y.year AS VARCHAR), ', ' ORDER BY y.year) AS years,
            e.listening_events,
            c.container_split
        FROM yearly y
        LEFT JOIN events e ON e.album = y.album
        LEFT JOIN container_summary c ON c.album = y.album
        WHERE y.album IS NOT NULL
          AND UPPER(y.album) NOT IN ('UNKNOWN', 'NONE', 'NULL')
        GROUP BY y.album, e.listening_events, c.container_split
        ORDER BY years_active DESC, listening_events DESC, album
    """).fetchall()

    albums = []

    for row in rows:
        albums.append({
            "album": row[0],
            "years_active": row[1],
            "first_year": row[2],
            "latest_year": row[3],
            "years": row[4],
            "events": row[5],
            "container_split": row[6],
            "ambiguous": is_ambiguous_album(row[0]),
        })

    coverage_rows = con.execute("""
        SELECT DISTINCT YEAR(TRY_CAST(event_start_timestamp AS TIMESTAMP)) AS year
        FROM apple_music_play_activity
        WHERE TRY_CAST(event_start_timestamp AS TIMESTAMP) IS NOT NULL
        ORDER BY year
    """).fetchall()

    coverage_years = [row[0] for row in coverage_rows if row[0] is not None]

    return albums, coverage_years

def main():
    artists, artist_years, artist_total_rows, artist_skipped = load_artists()
    albums, album_years = load_albums()

    max_artist_years = max(item["years_active"] for item in artists) if artists else 0
    max_album_years = max(item["years_active"] for item in albums) if albums else 0

    expected_lookup = {name.lower(): name for name in EXPECTED_ARTISTS}
    artist_by_lower = {item["artist"].lower(): item for item in artists}

    never_leaves = [
        item for item in artists
        if item["years_active"] == max_artist_years
    ][:50]

    deep_companions = [
        item for item in artists
        if item["years_active"] == max_artist_years and item["events"] >= 500
    ]

    quiet_constants = [
        item for item in artists
        if item["years_active"] == max_artist_years and item["events"] < 500
    ][:35]

    memory_validated = []
    memory_challenged = []

    for expected in EXPECTED_ARTISTS:
        found = artist_by_lower.get(expected.lower())

        if not found:
            memory_challenged.append({
                "expected": expected,
                "found_as": "",
                "years_active": 0,
                "first_year": "",
                "latest_year": "",
                "events": "",
                "read": "Not found or naming mismatch",
            })
            continue

        row = {
            "expected": expected,
            "found_as": found["artist"],
            "years_active": found["years_active"],
            "first_year": found["first_year"],
            "latest_year": found["latest_year"],
            "events": found["events"],
            "read": "",
        }

        if found["years_active"] == max_artist_years and found["events"] >= 100:
            row["read"] = "Strongly validated"
            memory_validated.append(row)
        elif found["years_active"] == max_artist_years:
            row["read"] = "Validated by years, modest event count"
            memory_validated.append(row)
        else:
            row["read"] = "Challenged by source coverage or low recurrence"
            memory_challenged.append(row)

    surprise_candidates = [
        item for item in artists
        if item["artist"].lower() not in expected_lookup
           and item["years_active"] == max_artist_years
    ][:25]

    album_companions = [
        item for item in albums
        if item["years_active"] == max_album_years and not item["ambiguous"]
    ][:40]

    needs_identity_resolution = [
        item for item in albums
        if item["ambiguous"] and item["years_active"] >= max_album_years - 1
    ][:40]

    report = []

    report.append("# Permanent Companions Report v1")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Sprint Goal")
    report.append("")
    report.append("Identify artists and albums that persisted across the greatest number of years.")
    report.append("")
    report.append("This report is about persistence, not peak intensity, favorite status, or total play count.")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Data Status")
    report.append("")
    report.append("This is a research-grade v1 report.")
    report.append("")
    report.append("Artist persistence is parsed from:")
    report.append("")
    report.append(f"- `{ARTIST_SOURCE}`")
    report.append("")
    report.append("Album persistence is queried from:")
    report.append("")
    report.append(f"- `{DB_PATH}`")
    report.append("- DuckDB table: `apple_music_play_activity`")
    report.append("")
    report.append("Important caveat:")
    report.append("")
    report.append("- Artist coverage and album coverage come from different sources.")
    report.append(f"- Artist coverage years: `{', '.join(str(y) for y in artist_years)}`")
    report.append(f"- Album coverage years: `{', '.join(str(y) for y in album_years)}`")
    report.append("- Therefore, artist `Years Active` and album `Years Active` should not be compared one-for-one.")
    report.append("")
    report.append(f"Artist rows scanned: `{artist_total_rows}`")
    report.append(f"Artist rows skipped because artist/year could not be parsed: `{artist_skipped}`")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Feature Taxonomy")
    report.append("")
    report.append(md_table(
        ["Section", "Purpose"],
        [
            ["Never Leaves", "Appears across every available year"],
            ["Deep Companions", "High years active plus high event count"],
            ["Quiet Constants", "Many years active, modest event count"],
            ["Memory Validated", "Data confirms expected companion"],
            ["Memory Challenged", "Expected companion is weak, missing, or source-dependent"],
            ["Needs Identity Resolution", "Ambiguous album or artist metadata issue"],
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Never Leaves")
    report.append("")
    report.append(f"Rule: artist appears in all `{max_artist_years}` available artist years.")
    report.append("")
    report.append(md_table(
        ["Artist", "Years Active", "First Year", "Latest Year", "Listening Events"],
        [[x["artist"], x["years_active"], x["first_year"], x["latest_year"], x["events"]] for x in never_leaves]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Deep Companions")
    report.append("")
    report.append(f"Rule: artist appears in all `{max_artist_years}` available artist years and has at least `500` listening events.")
    report.append("")
    report.append(md_table(
        ["Artist", "Years Active", "Listening Events", "Read"],
        [[x["artist"], x["years_active"], x["events"], "High-longevity / high-presence companion"] for x in deep_companions]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Quiet Constants")
    report.append("")
    report.append(f"Rule: artist appears in all `{max_artist_years}` available artist years but has fewer than `500` listening events.")
    report.append("")
    report.append(md_table(
        ["Artist", "Years Active", "Listening Events", "Read"],
        [[x["artist"], x["years_active"], x["events"], "Persistent but less dominant"] for x in quiet_constants]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Memory Validated")
    report.append("")
    report.append(md_table(
        ["Expected Artist", "Found As", "Years Active", "First Year", "Latest Year", "Listening Events", "Read"],
        [[x["expected"], x["found_as"], x["years_active"], x["first_year"], x["latest_year"], x["events"], x["read"]] for x in memory_validated]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Memory Challenged")
    report.append("")
    report.append(md_table(
        ["Expected Artist", "Found As", "Years Active", "First Year", "Latest Year", "Listening Events", "Read"],
        [[x["expected"], x["found_as"], x["years_active"], x["first_year"], x["latest_year"], x["events"], x["read"]] for x in memory_challenged]
    ))
    report.append("")
    report.append("Interpretation note:")
    report.append("")
    report.append("Memory challenged does not mean memory is wrong. It means this Apple Music source does not strongly support the remembered relationship.")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Surprise Candidates")
    report.append("")
    report.append("Rule: artist appears in every available artist year but was not included in the initial expected-companion list.")
    report.append("")
    report.append(md_table(
        ["Artist", "Years Active", "First Year", "Latest Year", "Listening Events"],
        [[x["artist"], x["years_active"], x["first_year"], x["latest_year"], x["events"]] for x in surprise_candidates]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Album Companions — High Confidence")
    report.append("")
    report.append(f"Rule: album appears in all `{max_album_years}` available album years and title is distinctive enough for research-grade confidence.")
    report.append("")
    report.append(md_table(
        ["Album", "Years Active", "First Year", "Latest Year", "Listening Events", "Container Split"],
        [[x["album"], x["years_active"], x["first_year"], x["latest_year"], x["events"], x["container_split"]] for x in album_companions]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Needs Identity Resolution")
    report.append("")
    report.append("Rule: album has high persistence but title is ambiguous, generic, compilation-like, or otherwise unsafe without artist metadata.")
    report.append("")
    report.append(md_table(
        ["Album", "Years Active", "First Year", "Latest Year", "Listening Events", "Why It Needs Resolution"],
        [[x["album"], x["years_active"], x["first_year"], x["latest_year"], x["events"], "Album title alone is not a reliable identity key"] for x in needs_identity_resolution]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Sprint Discoveries")
    report.append("")
    report.append("### Surprising discoveries")
    report.append("")
    report.append("1. Brian Eno is not just present; he is structurally dominant in the artist data.")
    report.append("2. R.E.M. is a top-tier permanent companion, not merely a remembered favorite.")
    report.append("3. Death Cab for Cutie and Toad the Wet Sprocket are high-ranking permanent companions and deserve review.")
    report.append("4. Album persistence immediately exposed the identity-resolution problem: titles like `Greatest Hits`, `Hit`, and `Complete` cannot be trusted without artist metadata.")
    report.append("")
    report.append("### Memory validations")
    report.append("")
    report.append("1. The Beatles are validated as a permanent companion.")
    report.append("2. Wilco is validated as a permanent companion, with album support from `Summerteeth` and `Yankee Hotel Foxtrot`.")
    report.append("3. Grateful Dead is validated as a permanent companion.")
    report.append("4. Brian Eno is strongly validated, especially through `Ambient 1: Music for Airports`.")
    report.append("5. Matt Pond PA, R.E.M., Camper Van Beethoven, Pearl Jam, Pixies, and Foo Fighters all validate strongly in artist persistence.")
    report.append("")
    report.append("### Memory contradictions / challenges")
    report.append("")
    report.append("1. Michelle Shocked is weak in this source despite being meaningful in memory. This suggests source limitation, historical gap, or non-Apple-Music listening.")
    report.append("2. Some albums that feel important may be seasonal, intense, or context-specific rather than permanent companions.")
    report.append("3. Some permanent companions may be ambient, playlist, or background presences rather than explicit favorites.")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## UI Recommendation")
    report.append("")
    report.append("Decision: yes, this deserves a dedicated Music UI feature.")
    report.append("")
    report.append("Recommended feature name:")
    report.append("")
    report.append("```text")
    report.append("Permanent Companions")
    report.append("```")
    report.append("")
    report.append("Recommended subheading:")
    report.append("")
    report.append("```text")
    report.append("Who kept showing up across versions of me?")
    report.append("```")
    report.append("")
    report.append("Recommended sections:")
    report.append("")
    report.append("- Never Leaves")
    report.append("- Deep Companions")
    report.append("- Quiet Constants")
    report.append("- Memory Validated")
    report.append("- Memory Challenged")
    report.append("- Needs Identity Resolution")
    report.append("")
    report.append("Implementation should wait until artist and album identity resolution is improved, but the research category is strong enough to preserve.")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Next Technical Step")
    report.append("")
    report.append("Find or create a durable metadata source with:")
    report.append("")
    report.append("```text")
    report.append("artist_name")
    report.append("album_name")
    report.append("song_name")
    report.append("```")
    report.append("")
    report.append("Then rebuild Permanent Companions using:")
    report.append("")
    report.append("```text")
    report.append("artist_name + album_name")
    report.append("```")
    report.append("")
    report.append("as the durable identity key.")
    report.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(report), encoding="utf-8")

    print(f"Wrote report: {OUT_PATH}")

if __name__ == "__main__":
    main()
