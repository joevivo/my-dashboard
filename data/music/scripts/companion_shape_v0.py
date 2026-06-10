from pathlib import Path
import csv
from datetime import datetime

ROOT = Path(".").resolve()
SOURCE_PATH = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")
OUT_PATH = ROOT / "docs" / "music" / "companion-shape-v0.md"

TARGET_ARTISTS = [
    "Brian Eno",
    "R.E.M.",
    "Death Cab for Cutie",
    "Toad the Wet Sprocket",
    "Hippo Campus",
    "Chet Baker",
    "The Psychedelic Furs",
    "Cracker",
    "Michelle Shocked",
]

def parse_artist(track_description):
    if not track_description:
        return None
    value = track_description.strip()
    if " - " not in value:
        return None
    return value.split(" - ", 1)[0].strip()

def parse_year(date_played):
    if not date_played:
        return None
    value = str(date_played).strip()
    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None

def md_table(headers, rows):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)

def classify_shape(year_counts):
    counts = list(year_counts.values())
    total = sum(counts)
    active_years = len([c for c in counts if c > 0])
    max_year = max(counts) if counts else 0

    if total == 0:
        return "Not present"

    max_share = max_year / total

    if active_years <= 2:
        return "Narrow / source-limited"
    if max_share >= 0.50:
        return "Spike-heavy companion"
    if max_share >= 0.30:
        return "Peak plus steady return"
    return "Steady companion"

def main():
    years = list(range(2016, 2027))
    target_lookup = {artist.lower(): artist for artist in TARGET_ARTISTS}
    counts = {artist: {year: 0 for year in years} for artist in TARGET_ARTISTS}

    with SOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = parse_artist(row.get("Track Description"))
            year = parse_year(row.get("Date Played"))

            if not artist or year not in years:
                continue

            canonical = target_lookup.get(artist.lower())
            if not canonical:
                continue

            counts[canonical][year] += 1

    rows = []

    for artist in TARGET_ARTISTS:
        year_counts = counts[artist]
        total = sum(year_counts.values())
        peak_year = max(year_counts, key=lambda y: year_counts[y])
        peak_count = year_counts[peak_year]
        active_years = len([c for c in year_counts.values() if c > 0])
        shape = classify_shape(year_counts)

        rows.append([
            artist,
            active_years,
            total,
            peak_year,
            peak_count,
            shape,
            ", ".join(f"{year}: {year_counts[year]}" for year in years),
        ])

    report = []
    report.append("# Companion Shape v0")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Question")
    report.append("")
    report.append("Were permanent companions steady across years, or did they persist because of one big spike plus scattered returns?")
    report.append("")
    report.append("## Results")
    report.append("")
    report.append(md_table(
        ["Artist", "Active Years", "Total Events", "Peak Year", "Peak Count", "Shape", "Year Counts"],
        rows
    ))
    report.append("")
    report.append("## Notes")
    report.append("")
    report.append("- Steady companion: no single year dominates the total.")
    report.append("- Peak plus steady return: one year is clearly elevated, but the artist keeps recurring.")
    report.append("- Spike-heavy companion: one year contributes at least half the total.")
    report.append("- Narrow / source-limited: appears in only one or two years.")
    report.append("")

    OUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote report: {OUT_PATH}")

if __name__ == "__main__":
    main()
