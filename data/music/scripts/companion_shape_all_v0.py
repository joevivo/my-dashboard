from pathlib import Path
import csv
from datetime import datetime

ROOT = Path(".").resolve()
SOURCE_PATH = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")
OUT_PATH = ROOT / "docs" / "music" / "companion-shape-all-v0.md"

MIN_EVENTS_TO_DISPLAY = 100

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

def classify_shape(year_counts, years):
    counts = [year_counts.get(year, 0) for year in years]
    total = sum(counts)

    if total == 0:
        return "Not present"

    peak_count = max(counts)
    peak_share = peak_count / total

    first_two = sum(year_counts.get(year, 0) for year in years[:2])
    last_two = sum(year_counts.get(year, 0) for year in years[-2:])

    first_two_share = first_two / total
    last_two_share = last_two / total

    if peak_share >= 0.50:
        if last_two_share >= 0.40:
            return "Recent resurgence companion"
        return "Spike-heavy companion"

    if last_two_share >= 0.40:
        return "Recent resurgence companion"

    if peak_share >= 0.30:
        return "Peak plus steady return"

    if first_two_share >= 0.45:
        return "Early anchor, recurring companion"

    return "Steady companion"

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
    artist_year_counts = {}
    all_years = set()

    with SOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            artist = parse_artist(row.get("Track Description"))
            year = parse_year(row.get("Date Played"))

            if not artist or not year:
                continue

            all_years.add(year)
            artist_year_counts.setdefault(artist, {})
            artist_year_counts[artist][year] = artist_year_counts[artist].get(year, 0) + 1

    years = sorted(all_years)
    max_years = len(years)

    records = []

    for artist, year_counts in artist_year_counts.items():
        active_years = len([year for year in years if year_counts.get(year, 0) > 0])

        if active_years != max_years:
            continue

        total = sum(year_counts.get(year, 0) for year in years)

        if total < MIN_EVENTS_TO_DISPLAY:
            continue

        peak_year = max(years, key=lambda year: year_counts.get(year, 0))
        peak_count = year_counts.get(peak_year, 0)
        peak_share = peak_count / total if total else 0
        last_two = sum(year_counts.get(year, 0) for year in years[-2:])
        last_two_share = last_two / total if total else 0
        shape = classify_shape(year_counts, years)

        records.append({
            "artist": artist,
            "active_years": active_years,
            "total": total,
            "peak_year": peak_year,
            "peak_count": peak_count,
            "peak_share": peak_share,
            "recent_share": last_two_share,
            "shape": shape,
            "year_counts": ", ".join(f"{year}: {year_counts.get(year, 0)}" for year in years),
        })

    records.sort(key=lambda x: (-x["total"], x["artist"].lower()))

    grouped = {}

    for record in records:
        grouped.setdefault(record["shape"], []).append(record)

    shape_order = [
        "Steady companion",
        "Peak plus steady return",
        "Spike-heavy companion",
        "Recent resurgence companion",
        "Early anchor, recurring companion",
        "Not present",
    ]

    report = []
    report.append("# Companion Shape All v0")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Question")
    report.append("")
    report.append("Among artists who never leave, what kind of companion are they?")
    report.append("")
    report.append("This report classifies all artists who appear in every available artist year.")
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
            ["Steady companion", "Persistent across years without one dominant spike"],
            ["Peak plus steady return", "One clear peak year, but meaningful recurrence afterward"],
            ["Spike-heavy companion", "One year explains at least half the artist's events"],
            ["Recent resurgence companion", "Recent two-year period accounts for a large share of events"],
            ["Early anchor, recurring companion", "Early period dominates, but the artist keeps returning"],
        ]
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Summary by Shape")
    report.append("")

    summary_rows = []

    for shape in shape_order:
        items = grouped.get(shape, [])
        if not items:
            continue

        summary_rows.append([
            shape,
            len(items),
            ", ".join(item["artist"] for item in items[:10]),
        ])

    report.append(md_table(
        ["Shape", "Artist Count", "Examples"],
        summary_rows
    ))
    report.append("")
    report.append("---")
    report.append("")
    report.append("## All Never-Leaves Artists by Shape")
    report.append("")

    for shape in shape_order:
        items = grouped.get(shape, [])

        if not items:
            continue

        report.append(f"### {shape}")
        report.append("")
        report.append(md_table(
            [
                "Artist",
                "Active Years",
                "Total Events",
                "Peak Year",
                "Peak Count",
                "Peak Share",
                "Recent Share",
                "Year Counts",
            ],
            [
                [
                    item["artist"],
                    item["active_years"],
                    item["total"],
                    item["peak_year"],
                    item["peak_count"],
                    f"{item['peak_share']:.1%}",
                    f"{item['recent_share']:.1%}",
                    item["year_counts"],
                ]
                for item in items
            ]
        ))
        report.append("")

    report.append("---")
    report.append("")
    report.append("## Research Notes")
    report.append("")
    report.append("- This is still research-grade because artist parsing comes from `Track Description`.")
    report.append("- Companion shape should become part of the Permanent Companions UI model.")
    report.append("- The next question is whether albums have similar shapes: steady album, spike album, seasonal album, or playlist artifact.")
    report.append("")

    OUT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote report: {OUT_PATH}")

if __name__ == "__main__":
    main()
