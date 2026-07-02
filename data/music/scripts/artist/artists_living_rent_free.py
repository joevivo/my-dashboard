from pathlib import Path
import csv
import re
from collections import defaultdict, Counter
from datetime import datetime

SOURCE = Path(
    "C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv"
)


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


def normalize_track(track):
    if not track:
        return ""

    value = re.sub(r"\s*[\(\[].*?[\)\]]", "", str(track)).strip()
    value = re.sub(r"\s+", " ", value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()

    return value


def fmt_pct(value):
    return f"{value:.1%}"


def main():
    artists = defaultdict(
        lambda: {
            "plays": 0,
            "skips": 0,
            "duration_ms": 0,
            "tracks": Counter(),
            "years": Counter(),
            "first_seen": None,
            "last_seen": None,
        }
    )

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            artist, track = parse_track_description(
                row.get("Track Description")
            )

            played = parse_date(row.get("Date Played"))

            if not artist or not played:
                continue

            play_count = int(row.get("Play Count") or 0)
            skip_count = int(row.get("Skip Count") or 0)

            try:
                duration_ms = int(
                    float(row.get("Play Duration Milliseconds") or 0)
                )
            except ValueError:
                duration_ms = 0

            data = artists[artist]

            data["plays"] += play_count
            data["skips"] += skip_count
            data["duration_ms"] += duration_ms

            total_events = play_count + skip_count

            data["years"][played.year] += total_events

            track_key = normalize_track(track)

            if track_key:
                data["tracks"][track_key] += total_events

            if data["first_seen"] is None or played < data["first_seen"]:
                data["first_seen"] = played

            if data["last_seen"] is None or played > data["last_seen"]:
                data["last_seen"] = played

    rows = []

    for artist, data in artists.items():
        total_events = data["plays"] + data["skips"]

        if total_events < 20:
            continue

        distinct_tracks = len(data["tracks"])
        years_active = len(data["years"])

        skip_rate = (
            data["skips"] / total_events if total_events else 0
        )

        listen_hours = (
            data["duration_ms"] / 1000 / 60 / 60
        )

        if data["tracks"]:
            top_track, top_track_events = (
                data["tracks"].most_common(1)[0]
            )
        else:
            top_track, top_track_events = ("", 0)

        top_track_share = (
            top_track_events / total_events
            if total_events
            else 0
        )

        rows.append(
            {
                "artist": artist,
                "events": total_events,
                "plays": data["plays"],
                "skips": data["skips"],
                "skip_rate": skip_rate,
                "listen_hours": listen_hours,
                "tracks": distinct_tracks,
                "years": years_active,
                "first_seen": data["first_seen"],
                "last_seen": data["last_seen"],
                "top_track": top_track,
                "top_track_share": top_track_share,
            }
        )

    print("\n=== Artists Living Rent-Free: High Skip / High Exposure ===")

    high_skip = sorted(
        [
            r
            for r in rows
            if r["events"] >= 30
            and r["skip_rate"] >= 0.40
        ],
        key=lambda r: (r["skip_rate"], r["events"]),
        reverse=True,
    )[:25]

    for r in high_skip:
        print(
            f'{r["artist"]} | '
            f'events={r["events"]} '
            f'plays={r["plays"]} '
            f'skips={r["skips"]} '
            f'skip={fmt_pct(r["skip_rate"])} '
            f'tracks={r["tracks"]} '
            f'years={r["years"]}'
        )

    print("\n=== One-Song Residents ===")

    one_song = sorted(
        [
            r
            for r in rows
            if r["events"] >= 20
            and r["top_track_share"] >= 0.60
        ],
        key=lambda r: (
            r["top_track_share"],
            r["events"],
        ),
        reverse=True,
    )[:25]

    for r in one_song:
        print(
            f'{r["artist"]} | '
            f'events={r["events"]} '
            f'top_song_share={fmt_pct(r["top_track_share"])} '
            f'top_song="{r["top_track"]}" '
            f'tracks={r["tracks"]}'
        )

    print("\n=== Idle Catalogs ===")

    idle = sorted(
        [
            r
            for r in rows
            if r["events"] >= 20
            and r["last_seen"]
            and r["last_seen"].year <= 2022
        ],
        key=lambda r: (
            r["last_seen"],
            r["events"],
        ),
    )[:25]

    for r in idle:
        print(
            f'{r["artist"]} | '
            f'events={r["events"]} '
            f'tracks={r["tracks"]} '
            f'years={r["years"]} '
            f'last={r["last_seen"]}'
        )

    print("\n=== Low Breadth / Meaningful Exposure ===")

    low_breadth = sorted(
        [
            r
            for r in rows
            if r["events"] >= 30
            and r["tracks"] <= 3
        ],
        key=lambda r: (
            r["events"],
            r["top_track_share"],
        ),
        reverse=True,
    )[:25]

    for r in low_breadth:
        print(
            f'{r["artist"]} | '
            f'events={r["events"]} '
            f'tracks={r["tracks"]} '
            f'top_song_share={fmt_pct(r["top_track_share"])} '
            f'years={r["years"]}'
        )

    print("\n=== Rent-Free Prime Candidates ===")

    prime = sorted(
        [
            r
            for r in rows
            if r["events"] >= 40
            and r["skip_rate"] >= 0.50
            and r["tracks"] >= 5
        ],
        key=lambda r: (
            r["skip_rate"],
            r["events"],
        ),
        reverse=True,
    )[:30]

    for r in prime:
        print(
            f'{r["artist"]} | '
            f'events={r["events"]} '
            f'plays={r["plays"]} '
            f'skips={r["skips"]} '
            f'skip={fmt_pct(r["skip_rate"])} '
            f'tracks={r["tracks"]} '
            f'years={r["years"]} '
            f'last={r["last_seen"]}'
        )
if __name__ == "__main__":
    main()
