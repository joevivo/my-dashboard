import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


def repo_root():
    return Path(__file__).resolve().parents[3]


DEFAULT_SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")
DEFAULT_ALIASES = repo_root() / "data" / "music" / "artist_aliases.json"
DEFAULT_MD_OUT = repo_root() / "docs" / "music" / "music-query-workbench-report.md"


def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def parse_track_description(value):
    if not value:
        return None, None

    value = str(value).strip()

    if " - " not in value:
        return None, value

    artist, track = value.split(" - ", 1)
    return artist.strip(), track.strip()



def format_share(value):
    if value is None:
        return "[not found]"
    return f"{value:.1%}"


def normalize_track_family(track):
    if not track:
        return "", ""

    display = str(track).strip()

    # Remove common version/remaster/live metadata from track titles.
    display = re.sub(r"\s*[\(\[].*?[\)\]]", "", display).strip()
    display = re.sub(r"\s+", " ", display).strip()

    if not display:
        display = str(track).strip()

    key = display.lower()
    key = re.sub(r"[^a-z0-9]+", " ", key).strip()

    for article in ("the ", "a ", "an "):
        if key.startswith(article):
            key = key[len(article):]

    return key, display


def classify_companion_type(total_events, distinct_track_families, top_family_share, top_two_family_share):
    if total_events == 0:
        return "Not found / source-limited"

    if total_events < 10:
        if top_family_share >= 0.70:
            return "Low-volume single-song marker"
        return "Low-signal / inconclusive"

    if top_family_share >= 0.85:
        return "Single-song companion"

    if top_family_share >= 0.70:
        return "Song-family companion"

    if top_two_family_share >= 0.75:
        return "Narrow-catalog companion"

    if distinct_track_families >= 8 and top_family_share < 0.40:
        return "Catalog companion"

    if distinct_track_families >= 4:
        return "Narrow-catalog companion"

    return "Low-signal / inconclusive"

def load_aliases(path):
    path = Path(path)

    if not path.exists():
        return {}, {}

    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    alias_to_canonical = {}

    for canonical, info in data.items():
        alias_to_canonical[canonical.lower()] = canonical

        for alias in info.get("aliases", []):
            alias_to_canonical[alias.lower()] = canonical

    return data, alias_to_canonical


def resolve_artist(query, alias_data, alias_to_canonical):
    query_key = query.strip().lower()
    canonical = alias_to_canonical.get(query_key, query.strip())

    info = alias_data.get(canonical, {})
    aliases = list(info.get("aliases", []))

    if canonical not in aliases:
        aliases.insert(0, canonical)

    if query.strip() not in aliases:
        aliases.append(query.strip())

    # Preserve order while removing duplicates.
    seen = set()
    deduped_aliases = []

    for alias in aliases:
        key = alias.lower()
        if key not in seen:
            deduped_aliases.append(alias)
            seen.add(key)

    return {
        "query": query,
        "canonical": canonical,
        "aliases": deduped_aliases,
        "source_note": info.get("source_note", ""),
        "used_alias_file": canonical in alias_data,
    }


def classify_shape(year_counts):
    if not year_counts:
        return "Not found / source-limited"

    total = sum(year_counts.values())
    active_years = len(year_counts)
    max_share = max(year_counts.values()) / total if total else 0
    years = sorted(year_counts)
    latest_year = years[-1]

    if active_years >= 7 and max_share < 0.35:
        return "Steady companion"

    if active_years >= 5 and max_share >= 0.35:
        return "Peak plus steady return"

    if max_share >= 0.60:
        return "Spike-heavy companion"

    if latest_year >= datetime.now().year - 1 and active_years <= 3:
        return "Recent resurgence companion"

    return "Intermittent companion"


def lookup_artist(source, resolved, contains=False, limit=20):
    alias_lowers = {alias.lower() for alias in resolved["aliases"]}

    total_rows = 0
    skipped_rows = 0
    matched_rows = 0

    year_counts = Counter()
    track_counts = Counter()
    track_family_counts = Counter()
    track_family_display = {}
    date_counts = Counter()
    raw_counts = Counter()
    matched_artist_names = Counter()

    first_seen = None
    latest_seen = None

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1

            played = parse_date(row.get("Date Played"))
            description = row.get("Track Description")
            artist, track = parse_track_description(description)

            if not played or not description:
                skipped_rows += 1
                continue

            if contains:
                matched = any(alias in description.lower() for alias in alias_lowers)
            else:
                matched = bool(artist) and artist.lower() in alias_lowers

            if not matched:
                continue

            matched_rows += 1
            year_counts[played.year] += 1
            date_counts[played.isoformat()] += 1
            raw_counts[description] += 1

            if artist:
                matched_artist_names[artist] += 1

            if track:
                track_counts[track] += 1

                family_key, family_display = normalize_track_family(track)
                if family_key:
                    track_family_counts[family_key] += 1
                    track_family_display.setdefault(family_key, family_display)

            if first_seen is None or played < first_seen:
                first_seen = played

            if latest_seen is None or played > latest_seen:
                latest_seen = played

    top_track, top_track_count = (track_counts.most_common(1)[0] if track_counts else (None, 0))
    top_track_share = (top_track_count / matched_rows) if matched_rows else 0

    top_family_key, top_family_count = (
        track_family_counts.most_common(1)[0] if track_family_counts else (None, 0)
    )
    top_track_family = track_family_display.get(top_family_key) if top_family_key else None
    top_family_share = (top_family_count / matched_rows) if matched_rows else 0

    top_two_family_count = sum(count for _, count in track_family_counts.most_common(2))
    top_two_family_share = (top_two_family_count / matched_rows) if matched_rows else 0

    distinct_tracks = len(track_counts)
    distinct_track_families = len(track_family_counts)

    companion_type = classify_companion_type(
        total_events=matched_rows,
        distinct_track_families=distinct_track_families,
        top_family_share=top_family_share,
        top_two_family_share=top_two_family_share,
    )

    return {
        "query": resolved["query"],
        "canonical": resolved["canonical"],
        "aliases": resolved["aliases"],
        "source_note": resolved["source_note"],
        "used_alias_file": resolved["used_alias_file"],
        "match_mode": "contains" if contains else "exact parsed artist / aliases",
        "rows_scanned": total_rows,
        "rows_skipped": skipped_rows,
        "matching_events": matched_rows,
        "first_seen": first_seen,
        "latest_seen": latest_seen,
        "years_active": len(year_counts),
        "shape": classify_shape(year_counts),
        "year_counts": year_counts,
        "track_counts": track_counts,
        "track_family_counts": track_family_counts,
        "track_family_display": track_family_display,
        "top_track": top_track,
        "top_track_count": top_track_count,
        "top_track_share": top_track_share,
        "top_track_family": top_track_family,
        "top_track_family_count": top_family_count,
        "top_track_family_share": top_family_share,
        "top_two_track_family_share": top_two_family_share,
        "distinct_tracks": distinct_tracks,
        "distinct_track_families": distinct_track_families,
        "companion_type": companion_type,
        "date_counts": date_counts,
        "raw_counts": raw_counts,
        "matched_artist_names": matched_artist_names,
        "limit": limit,
    }


def md_table(headers, rows):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return lines


def render_artist(result):
    limit = result["limit"]
    lines = []

    lines.append(f"# Music Artist Lookup: {result['canonical']}")
    lines.append("")
    lines.append(f"- Artist query: {result['query']}")
    lines.append(f"- Normalized artist: {result['canonical']}")
    lines.append(f"- Aliases searched: {', '.join(result['aliases'])}")
    lines.append(f"- Match mode: {result['match_mode']}")
    lines.append(f"- Rows scanned: {result['rows_scanned']}")
    lines.append(f"- Rows skipped: {result['rows_skipped']}")

    if result["source_note"]:
        lines.append(f"- Source note: {result['source_note']}")

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Matching events: {result['matching_events']}")
    lines.append(f"- First seen: {result['first_seen'] or '[not found]'}")
    lines.append(f"- Latest seen: {result['latest_seen'] or '[not found]'}")
    lines.append(f"- Years active: {result['years_active']}")
    lines.append(f"- Provisional shape: {result['shape']}")
    lines.append(f"- Companion type: {result['companion_type']}")
    lines.append(f"- Top track: {result['top_track'] or '[not found]'} ({result['top_track_count']} / {result['matching_events']}, {format_share(result['top_track_share'])})")
    lines.append(f"- Top track family: {result['top_track_family'] or '[not found]'} ({result['top_track_family_count']} / {result['matching_events']}, {format_share(result['top_track_family_share'])})")
    lines.append(f"- Top two track-family share: {format_share(result['top_two_track_family_share'])}")
    lines.append(f"- Distinct tracks: {result['distinct_tracks']}")
    lines.append(f"- Distinct track families: {result['distinct_track_families']}")

    lines.append("")
    lines.append("## Matched Artist Names")
    lines.append("")

    if result["matched_artist_names"]:
        for artist, count in result["matched_artist_names"].most_common(limit):
            lines.append(f"- {artist}: {count}")
    else:
        lines.append("_No matched artist names._")

    lines.append("")
    lines.append("## Events by Year")
    lines.append("")

    if result["year_counts"]:
        for year in sorted(result["year_counts"]):
            lines.append(f"- {year}: {result['year_counts'][year]}")
    else:
        lines.append("_No matching years._")

    lines.append("")
    lines.append("## Top Tracks")
    lines.append("")

    if result["track_counts"]:
        for track, count in result["track_counts"].most_common(limit):
            lines.append(f"- {track}: {count}")
    else:
        lines.append("_No matching tracks._")

    lines.append("")
    lines.append("## Top Listening Dates")
    lines.append("")

    if result["date_counts"]:
        for day, count in result["date_counts"].most_common(limit):
            lines.append(f"- {day}: {count}")
    else:
        lines.append("_No matching dates._")

    lines.append("")
    return lines


def render_comparison(results):
    lines = []
    lines.append("# Music Query Workbench Comparison")
    lines.append("")
    lines.extend(md_table(
        [
            "Artist",
            "Events",
            "Years Active",
            "First Seen",
            "Latest Seen",
            "Shape",
            "Companion Type",
            "Top Track Family",
            "Top Share",
            "Distinct Families",
        ],
        [
            [
                result["canonical"],
                result["matching_events"],
                result["years_active"],
                result["first_seen"] or "[not found]",
                result["latest_seen"] or "[not found]",
                result["shape"],
                result["companion_type"],
                result["top_track_family"] or "[not found]",
                format_share(result["top_track_family_share"]),
                result["distinct_track_families"],
            ]
            for result in results
        ],
    ))
    lines.append("")
    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Artist lookup against Apple Music sanitized daily track summary."
    )
    parser.add_argument("--artist", action="append", help="Artist name. May be repeated.")
    parser.add_argument("--compare", nargs="+", help="Run several artist lookups in one report.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--aliases", default=str(DEFAULT_ALIASES))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--contains", action="store_true")
    parser.add_argument(
        "--md",
        nargs="?",
        const=str(DEFAULT_MD_OUT),
        help="Optional Markdown output path. If no path is supplied, writes to docs/music/music-query-workbench-report.md.",
    )

    args = parser.parse_args()

    source = Path(args.source)

    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    alias_data, alias_to_canonical = load_aliases(args.aliases)

    queries = []

    if args.artist:
        queries.extend(args.artist)

    if args.compare:
        queries.extend(args.compare)

    if not queries:
        raise SystemExit("Provide --artist or --compare.")

    # Preserve order while removing duplicate query strings.
    seen_queries = set()
    deduped_queries = []

    for query in queries:
        key = query.lower()
        if key not in seen_queries:
            deduped_queries.append(query)
            seen_queries.add(key)

    results = []

    for query in deduped_queries:
        resolved = resolve_artist(query, alias_data, alias_to_canonical)
        results.append(
            lookup_artist(
                source=source,
                resolved=resolved,
                contains=args.contains,
                limit=args.limit,
            )
        )

    output_lines = []

    if len(results) > 1:
        output_lines.extend(render_comparison(results))
        output_lines.append("---")
        output_lines.append("")

    for index, result in enumerate(results):
        if index:
            output_lines.append("---")
            output_lines.append("")
        output_lines.extend(render_artist(result))

    print("\n".join(output_lines))

    if args.md:
        out_path = Path(args.md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        print(f"\nWrote Markdown report: {out_path}")


if __name__ == "__main__":
    main()
