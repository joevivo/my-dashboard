from math import log2

ARTISTS = {
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
        "Peter Gabriel 3": 143,
        "Plays Live": 70,
        "Security": 59,
        "Peter Gabriel 1": 45,
        "Peter Gabriel 2": 28,
        "Plays Live Highlights": 21,
    },
    "Toad the Wet Sprocket": {
        "Dulcinea": 336,
        "Bread and Circus": 132,
        "Fear": 74,
        "Pale": 64,
    },
    "Genesis": {
        "The Lamb Lies Down On Broadway": 144,
        "Selling England By The Pound": 59,
        "Duke": 31,
        "Abacab": 17,
        "A Trick Of The Tail": 10,
        "Invisible Touch": 4,
    },
    "matt pond PA": {
        "Emblems": 145,
        "Several Arrows Later": 83,
        "The Nature Of Maps": 79,
        "Green Fury": 78,
        "Last Light": 78,
        "Matt Pond's Youtube treasures": 62,
        "Skeletons and Friends": 55,
        "The Dark Leaves": 53,
    },
    "The Replacements": {
        "Stink": 48,
        "Let It Be": 45,
        "Pleased to Meet Me": 44,
        "All for Nothing": 29,
        "Sorry Ma": 28,
        "Hootenanny": 20,
        "Tim": 18,
        "Don't Tell a Soul": 16,
    },
}

def evenness(values):
    total = sum(values)

    if total == 0 or len(values) < 2:
        return 0

    entropy = 0

    for value in values:
        p = value / total
        entropy -= p * log2(p)

    return entropy / log2(len(values))

rows = []

for artist, albums in ARTISTS.items():
    values = sorted(albums.values(), reverse=True)

    total = sum(values)
    anchor = values[0]
    top_two = values[0] + values[1]

    anchor_share = anchor / total
    top_two_share = top_two / total

    width_25 = sum(
        1 for value in values
        if value >= anchor * 0.25
    )

    width_50 = sum(
        1 for value in values
        if value >= anchor * 0.50
    )

    ev = evenness(values)

    concentration = (
        (anchor_share * 40)
        + (top_two_share * 30)
        - (width_25 * 2)
        - (ev * 20)
    )

    rows.append(
        (
            concentration,
            artist,
            anchor_share,
            top_two_share,
            width_50,
            width_25,
            ev,
        )
    )

rows.sort(reverse=True)

print("# Relationship Concentration Report")
print()

for (
    concentration,
    artist,
    anchor_share,
    top_two_share,
    width_50,
    width_25,
    ev,
) in rows:

    print(artist)
    print(f"  concentration: {concentration:.2f}")
    print(f"  anchor share : {anchor_share:.1%}")
    print(f"  top two share: {top_two_share:.1%}")
    print(f"  width >=50%  : {width_50}")
    print(f"  width >=25%  : {width_25}")
    print(f"  evenness     : {ev:.2f}")
    print()
