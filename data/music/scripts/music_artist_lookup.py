import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", required=True)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--contains", action="store_true")
    args = parser.parse_args()

    source = Path(args.source)

    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    query = args.artist.strip().lower()

    total_rows = 0
    skipped_rows = 0
    matched_rows = 0

    year_counts = Counter()
    track_counts = Counter()
    date_counts = Counter()
    raw_counts = Counter()

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

            if args.contains:
                matched = query in description.lower()
            else:
                matched = bool(artist) and artist.lower() == query

            if not matched:
                continue

            matched_rows += 1
            year_counts[played.year] += 1
            date_counts[played.isoformat()] += 1

            if track:
                track_counts[track] += 1

            raw_counts[description] += 1

            if first_seen is None or played < first_seen:
                first_seen = played

            if latest_seen is None or played > latest_seen:
                latest_seen = played

    print("# Music Artist Lookup")
    print(f"- Artist query: {args.artist}")
    print(f"- Source: {source}")
    print(f"- Match mode: {'contains' if args.contains else 'exact parsed artist'}")
    print(f"- Rows scanned: {total_rows}")
    print(f"- Rows skipped: {skipped_rows}")

    print("\n## Summary")
    print(f"- Matching events: {matched_rows}")
    print(f"- First seen: {first_seen or '[not found]'}")
    print(f"- Latest seen: {latest_seen or '[not found]'}")
    print(f"- Years active: {len(year_counts)}")
    print(f"- Provisional shape: {classify_shape(year_counts)}")

    print("\n## Events by Year")
    if year_counts:
        for year in sorted(year_counts):
            print(f"- {year}: {year_counts[year]}")
    else:
        print("_No matching years._")

    print("\n## Top Tracks")
    if track_counts:
        for track, count in track_counts.most_common(args.limit):
            print(f"- {track}: {count}")
    else:
        print("_No matching tracks._")

    print("\n## Top Listening Dates")
    if date_counts:
        for day, count in date_counts.most_common(args.limit):
            print(f"- {day}: {count}")
    else:
        print("_No matching dates._")

    print("\n## Raw Descriptions")
    if raw_counts:
        for description, count in raw_counts.most_common(args.limit):
            print(f"- {description}: {count}")
    else:
        print("_No matching descriptions._")


if __name__ == "__main__":
    main()
