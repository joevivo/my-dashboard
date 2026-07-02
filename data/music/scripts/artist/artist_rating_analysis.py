from pathlib import Path
import csv
from collections import defaultdict, Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
RATINGS = ROOT / "data" / "music" / "artist_ratings_sample.csv"
SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")


def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def parse_artist(description):
    if not description or " - " not in description:
        return None
    return description.split(" - ", 1)[0].strip()


def main():
    ratings = {}

    with RATINGS.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ratings[row["artist"].strip()] = row["rating"].strip()

    artist_stats = defaultdict(lambda: {
        "events": 0,
        "skip_forwards": 0,
        "duration_ms": 0,
        "years": Counter(),
    })

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            artist = parse_artist(row.get("Track Description"))
            if artist not in ratings:
                continue

            played = parse_date(row.get("Date Played"))
            if not played:
                continue

            artist_stats[artist]["events"] += 1

            if row.get("End Reason Type") == "TRACK_SKIPPED_FORWARDS":
                artist_stats[artist]["skip_forwards"] += 1

            try:
                artist_stats[artist]["duration_ms"] += int(float(row.get("Play Duration Milliseconds") or 0))
            except ValueError:
                pass

            artist_stats[artist]["years"][played.year] += 1

    grouped = defaultdict(list)

    for artist, rating in ratings.items():
        stats = artist_stats.get(artist, {
            "events": 0,
            "skip_forwards": 0,
            "duration_ms": 0,
            "years": Counter(),
        })

        events = stats["events"]
        skips = stats["skip_forwards"]
        skip_rate = skips / events if events else 0
        hours = stats["duration_ms"] / 1000 / 60 / 60

        grouped[rating].append({
            "artist": artist,
            "events": events,
            "skips": skips,
            "skip_rate": skip_rate,
            "hours": hours,
            "years": len(stats["years"]),
        })

    order = ["Love", "Like", "Neutral", "Indifferent", "Avoid"]

    print("\n=== Artist Rating Analysis v1 ===\n")

    for rating in order:
        rows = grouped.get(rating, [])
        if not rows:
            continue

        total_events = sum(r["events"] for r in rows)
        total_skips = sum(r["skips"] for r in rows)
        total_hours = sum(r["hours"] for r in rows)
        avg_events = total_events / len(rows)
        avg_years = sum(r["years"] for r in rows) / len(rows)
        skip_rate = total_skips / total_events if total_events else 0

        print(f"{rating}")
        print(f"  Artists: {len(rows)}")
        print(f"  Total Events: {total_events}")
        print(f"  Total Hours: {total_hours:.2f}")
        print(f"  Avg Events / Artist: {avg_events:.1f}")
        print(f"  Avg Active Years / Artist: {avg_years:.1f}")
        print(f"  Skip Forward Rate: {skip_rate:.1%}")
        print("")

    print("=== Artist Detail ===\n")

    for rating in order:
        rows = sorted(grouped.get(rating, []), key=lambda r: r["events"], reverse=True)
        if not rows:
            continue

        print(f"{rating}")
        for r in rows:
            print(
                f'  {r["artist"]} | '
                f'events={r["events"]} '
                f'hours={r["hours"]:.2f} '
                f'skips={r["skips"]} '
                f'skip={r["skip_rate"]:.1%} '
                f'years={r["years"]}'
            )
        print("")


if __name__ == "__main__":
    main()
