from math import log2

ECOSYSTEMS = {
    "R.E.M.": {
        "Document": 433,
        "Out of Time": 306,
        "Green": 289,
        "Fables of the Reconstruction": 254,
        "Automatic For The People": 248,
        "Lifes Rich Pageant": 239,
        "Murmur": 234,
    },
    "Wilco": {
        "Summerteeth": 390,
        "Sky Blue Sky": 273,
        "Yankee Hotel Foxtrot": 271,
        "Being There": 207,
        "A Ghost Is Born": 193,
        "A.M.": 152,
    },
    "Peter Gabriel": {
        "Peter Gabriel 3: Melt": 143,
        "Plays Live": 70,
        "Peter Gabriel 4: Security": 59,
        "Peter Gabriel 1: Car": 45,
        "Peter Gabriel 2: Scratch": 28,
        "Plays Live (Highlights)": 21,
    },
    "Genesis": {
        "The Lamb Lies Down On Broadway": 144,
        "Selling England By The Pound": 59,
        "Duke": 31,
        "Abacab": 17,
        "A Trick Of The Tail": 10,
        "Invisible Touch": 4,
    },
    "Toad the Wet Sprocket": {
        "Dulcinea": 336,
        "Bread and Circus": 132,
        "Fear": 74,
        "Pale": 64,
    },
}


def entropy(values):
    total = sum(values)

    if total <= 0:
        return 0

    score = 0

    for value in values:
        if value <= 0:
            continue

        p = value / total
        score -= p * log2(p)

    return score


def normalized_entropy(values):
    if len(values) <= 1:
        return 0

    return entropy(values) / log2(len(values))


def summarize(name, albums):
    sorted_albums = sorted(
        albums.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    values = [count for _, count in sorted_albums]
    total = sum(values)
    top_album, top_count = sorted_albums[0]
    top_two = sum(values[:2])

    anchor_threshold = top_count * 0.25

    return {
        "artist": name,
        "total": total,
        "album_count": len(values),
        "top_album": top_album,
        "top_count": top_count,
        "top_share": top_count / total if total else 0,
        "top_two_share": top_two / total if total else 0,
        "albums_over_100": sum(1 for value in values if value >= 100),
        "albums_over_25pct_anchor": sum(1 for value in values if value >= anchor_threshold),
        "entropy": normalized_entropy(values),
    }


print("# Album Ecosystem Metrics")
print()

rows = [
    summarize(name, albums)
    for name, albums in ECOSYSTEMS.items()
]

rows.sort(key=lambda row: row["entropy"], reverse=True)

for row in rows:
    print(row["artist"])
    print(f"  total events:              {row['total']}")
    print(f"  album count:               {row['album_count']}")
    print(f"  top album:                 {row['top_album']} ({row['top_count']})")
    print(f"  top album share:           {row['top_share']:.1%}")
    print(f"  top two share:             {row['top_two_share']:.1%}")
    print(f"  albums >= 100 events:      {row['albums_over_100']}")
    print(f"  albums >= 25% of anchor:   {row['albums_over_25pct_anchor']}")
    print(f"  distribution evenness:     {row['entropy']:.2f}")
    print()
