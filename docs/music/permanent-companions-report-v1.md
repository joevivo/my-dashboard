# Permanent Companions Report v1

Generated: 2026-06-10 11:38

## Sprint Goal

Identify artists and albums that persisted across the greatest number of years.

This report is about persistence, not peak intensity, favorite status, or total play count.

---

## Data Status

This is a research-grade v1 report.

Artist persistence is parsed from:

- `C:\Users\joevi\apple-music-sanitized\apple-music-daily-track-summary.csv`

Album persistence is queried from:

- `C:\Users\joevi\my-dashboard\data\music\music.db`
- DuckDB table: `apple_music_play_activity`

Important caveat:

- Artist coverage and album coverage come from different sources.
- Artist coverage years: `2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026`
- Album coverage years: `2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026`
- Therefore, artist `Years Active` and album `Years Active` should not be compared one-for-one.

Artist rows scanned: `100791`
Artist rows skipped because artist/year could not be parsed: `108`

---

## Feature Taxonomy

| Section | Purpose |
| --- | --- |
| Never Leaves | Appears across every available year |
| Deep Companions | High years active plus high event count |
| Quiet Constants | Many years active, modest event count |
| Memory Validated | Data confirms expected companion |
| Memory Challenged | Expected companion is weak, missing, or source-dependent |
| Needs Identity Resolution | Ambiguous album or artist metadata issue |

---

## Never Leaves

Rule: artist appears in all `11` available artist years.

| Artist | Years Active | First Year | Latest Year | Listening Events |
| --- | --- | --- | --- | --- |
| Brian Eno | 11 | 2016 | 2026 | 2810 |
| R.E.M. | 11 | 2016 | 2026 | 2452 |
| Pearl Jam | 11 | 2016 | 2026 | 1532 |
| The Beatles | 11 | 2016 | 2026 | 1378 |
| Wilco | 11 | 2016 | 2026 | 1328 |
| Grateful Dead | 11 | 2016 | 2026 | 1230 |
| Death Cab for Cutie | 11 | 2016 | 2026 | 1219 |
| Toad the Wet Sprocket | 11 | 2016 | 2026 | 891 |
| Matt Pond PA | 11 | 2016 | 2026 | 709 |
| Tom Petty & The Heartbreakers | 11 | 2016 | 2026 | 663 |
| The Cure | 11 | 2016 | 2026 | 640 |
| Camper Van Beethoven | 11 | 2016 | 2026 | 620 |
| Pixies | 11 | 2016 | 2026 | 612 |
| Peter Gabriel | 11 | 2016 | 2026 | 608 |
| Chet Baker | 11 | 2016 | 2026 | 607 |
| The Smiths | 11 | 2016 | 2026 | 559 |
| Elvis Costello & The Attractions | 11 | 2016 | 2026 | 556 |
| Hippo Campus | 11 | 2016 | 2026 | 534 |
| U2 | 11 | 2016 | 2026 | 510 |
| Foo Fighters | 11 | 2016 | 2026 | 507 |
| Rush | 11 | 2016 | 2026 | 487 |
| Incubus | 11 | 2016 | 2026 | 466 |
| The Replacements | 11 | 2016 | 2026 | 452 |
| Genesis | 11 | 2016 | 2026 | 449 |
| Sam Cooke | 11 | 2016 | 2026 | 447 |
| The Psychedelic Furs | 11 | 2016 | 2026 | 438 |
| Neil Young | 11 | 2016 | 2026 | 421 |
| Hüsker Dü | 11 | 2016 | 2026 | 417 |
| Cracker | 11 | 2016 | 2026 | 416 |
| Imagine Dragons | 11 | 2016 | 2026 | 405 |
| Pink Floyd | 11 | 2016 | 2026 | 400 |
| Talking Heads | 11 | 2016 | 2026 | 389 |
| Fleetwood Mac | 11 | 2016 | 2026 | 380 |
| Radiohead | 11 | 2016 | 2026 | 376 |
| Led Zeppelin | 11 | 2016 | 2026 | 375 |
| The Rolling Stones | 11 | 2016 | 2026 | 363 |
| The Police | 11 | 2016 | 2026 | 327 |
| David Bowie | 11 | 2016 | 2026 | 322 |
| Beach Slang | 11 | 2016 | 2026 | 303 |
| Courtney Barnett | 11 | 2016 | 2026 | 299 |
| Alice In Chains | 11 | 2016 | 2026 | 295 |
| Cage the Elephant | 11 | 2016 | 2026 | 294 |
| Cowboy Junkies | 11 | 2016 | 2026 | 293 |
| Kiss | 11 | 2016 | 2026 | 293 |
| Whiskeytown | 11 | 2016 | 2026 | 290 |
| Bob Mould | 11 | 2016 | 2026 | 278 |
| Steely Dan | 11 | 2016 | 2026 | 272 |
| Sinéad O'Connor | 11 | 2016 | 2026 | 265 |
| Robyn Hitchcock & The Egyptians | 11 | 2016 | 2026 | 264 |
| Uncle Tupelo | 11 | 2016 | 2026 | 261 |

---

## Deep Companions

Rule: artist appears in all `11` available artist years and has at least `500` listening events.

| Artist | Years Active | Listening Events | Read |
| --- | --- | --- | --- |
| Brian Eno | 11 | 2810 | High-longevity / high-presence companion |
| R.E.M. | 11 | 2452 | High-longevity / high-presence companion |
| Pearl Jam | 11 | 1532 | High-longevity / high-presence companion |
| The Beatles | 11 | 1378 | High-longevity / high-presence companion |
| Wilco | 11 | 1328 | High-longevity / high-presence companion |
| Grateful Dead | 11 | 1230 | High-longevity / high-presence companion |
| Death Cab for Cutie | 11 | 1219 | High-longevity / high-presence companion |
| Toad the Wet Sprocket | 11 | 891 | High-longevity / high-presence companion |
| Matt Pond PA | 11 | 709 | High-longevity / high-presence companion |
| Tom Petty & The Heartbreakers | 11 | 663 | High-longevity / high-presence companion |
| The Cure | 11 | 640 | High-longevity / high-presence companion |
| Camper Van Beethoven | 11 | 620 | High-longevity / high-presence companion |
| Pixies | 11 | 612 | High-longevity / high-presence companion |
| Peter Gabriel | 11 | 608 | High-longevity / high-presence companion |
| Chet Baker | 11 | 607 | High-longevity / high-presence companion |
| The Smiths | 11 | 559 | High-longevity / high-presence companion |
| Elvis Costello & The Attractions | 11 | 556 | High-longevity / high-presence companion |
| Hippo Campus | 11 | 534 | High-longevity / high-presence companion |
| U2 | 11 | 510 | High-longevity / high-presence companion |
| Foo Fighters | 11 | 507 | High-longevity / high-presence companion |

---

## Quiet Constants

Rule: artist appears in all `11` available artist years but has fewer than `500` listening events.

| Artist | Years Active | Listening Events | Read |
| --- | --- | --- | --- |
| Rush | 11 | 487 | Persistent but less dominant |
| Incubus | 11 | 466 | Persistent but less dominant |
| The Replacements | 11 | 452 | Persistent but less dominant |
| Genesis | 11 | 449 | Persistent but less dominant |
| Sam Cooke | 11 | 447 | Persistent but less dominant |
| The Psychedelic Furs | 11 | 438 | Persistent but less dominant |
| Neil Young | 11 | 421 | Persistent but less dominant |
| Hüsker Dü | 11 | 417 | Persistent but less dominant |
| Cracker | 11 | 416 | Persistent but less dominant |
| Imagine Dragons | 11 | 405 | Persistent but less dominant |
| Pink Floyd | 11 | 400 | Persistent but less dominant |
| Talking Heads | 11 | 389 | Persistent but less dominant |
| Fleetwood Mac | 11 | 380 | Persistent but less dominant |
| Radiohead | 11 | 376 | Persistent but less dominant |
| Led Zeppelin | 11 | 375 | Persistent but less dominant |
| The Rolling Stones | 11 | 363 | Persistent but less dominant |
| The Police | 11 | 327 | Persistent but less dominant |
| David Bowie | 11 | 322 | Persistent but less dominant |
| Beach Slang | 11 | 303 | Persistent but less dominant |
| Courtney Barnett | 11 | 299 | Persistent but less dominant |
| Alice In Chains | 11 | 295 | Persistent but less dominant |
| Cage the Elephant | 11 | 294 | Persistent but less dominant |
| Cowboy Junkies | 11 | 293 | Persistent but less dominant |
| Kiss | 11 | 293 | Persistent but less dominant |
| Whiskeytown | 11 | 290 | Persistent but less dominant |
| Bob Mould | 11 | 278 | Persistent but less dominant |
| Steely Dan | 11 | 272 | Persistent but less dominant |
| Sinéad O'Connor | 11 | 265 | Persistent but less dominant |
| Robyn Hitchcock & The Egyptians | 11 | 264 | Persistent but less dominant |
| Uncle Tupelo | 11 | 261 | Persistent but less dominant |
| Tom Waits | 11 | 254 | Persistent but less dominant |
| Microwave | 11 | 251 | Persistent but less dominant |
| Band of Horses | 11 | 249 | Persistent but less dominant |
| Bob Marley & The Wailers | 11 | 236 | Persistent but less dominant |
| Billy Joel | 11 | 234 | Persistent but less dominant |

---

## Memory Validated

| Expected Artist | Found As | Years Active | First Year | Latest Year | Listening Events | Read |
| --- | --- | --- | --- | --- | --- | --- |
| The Beatles | The Beatles | 11 | 2016 | 2026 | 1378 | Strongly validated |
| Wilco | Wilco | 11 | 2016 | 2026 | 1328 | Strongly validated |
| Grateful Dead | Grateful Dead | 11 | 2016 | 2026 | 1230 | Strongly validated |
| Brian Eno | Brian Eno | 11 | 2016 | 2026 | 2810 | Strongly validated |
| Bob Dylan | Bob Dylan | 11 | 2016 | 2026 | 174 | Strongly validated |
| Matt Pond PA | Matt Pond PA | 11 | 2016 | 2026 | 709 | Strongly validated |
| R.E.M. | R.E.M. | 11 | 2016 | 2026 | 2452 | Strongly validated |
| Camper Van Beethoven | Camper Van Beethoven | 11 | 2016 | 2026 | 620 | Strongly validated |
| Pearl Jam | Pearl Jam | 11 | 2016 | 2026 | 1532 | Strongly validated |
| Pixies | Pixies | 11 | 2016 | 2026 | 612 | Strongly validated |
| Foo Fighters | Foo Fighters | 11 | 2016 | 2026 | 507 | Strongly validated |

---

## Memory Challenged

| Expected Artist | Found As | Years Active | First Year | Latest Year | Listening Events | Read |
| --- | --- | --- | --- | --- | --- | --- |
| Michelle Shocked | Michelle Shocked | 1 | 2024 | 2024 | 1 | Challenged by source coverage or low recurrence |

Interpretation note:

Memory challenged does not mean memory is wrong. It means this Apple Music source does not strongly support the remembered relationship.

---

## Surprise Candidates

Rule: artist appears in every available artist year but was not included in the initial expected-companion list.

| Artist | Years Active | First Year | Latest Year | Listening Events |
| --- | --- | --- | --- | --- |
| Death Cab for Cutie | 11 | 2016 | 2026 | 1219 |
| Toad the Wet Sprocket | 11 | 2016 | 2026 | 891 |
| Tom Petty & The Heartbreakers | 11 | 2016 | 2026 | 663 |
| The Cure | 11 | 2016 | 2026 | 640 |
| Peter Gabriel | 11 | 2016 | 2026 | 608 |
| Chet Baker | 11 | 2016 | 2026 | 607 |
| The Smiths | 11 | 2016 | 2026 | 559 |
| Elvis Costello & The Attractions | 11 | 2016 | 2026 | 556 |
| Hippo Campus | 11 | 2016 | 2026 | 534 |
| U2 | 11 | 2016 | 2026 | 510 |
| Rush | 11 | 2016 | 2026 | 487 |
| Incubus | 11 | 2016 | 2026 | 466 |
| The Replacements | 11 | 2016 | 2026 | 452 |
| Genesis | 11 | 2016 | 2026 | 449 |
| Sam Cooke | 11 | 2016 | 2026 | 447 |
| The Psychedelic Furs | 11 | 2016 | 2026 | 438 |
| Neil Young | 11 | 2016 | 2026 | 421 |
| Hüsker Dü | 11 | 2016 | 2026 | 417 |
| Cracker | 11 | 2016 | 2026 | 416 |
| Imagine Dragons | 11 | 2016 | 2026 | 405 |
| Pink Floyd | 11 | 2016 | 2026 | 400 |
| Talking Heads | 11 | 2016 | 2026 | 389 |
| Fleetwood Mac | 11 | 2016 | 2026 | 380 |
| Radiohead | 11 | 2016 | 2026 | 376 |
| Led Zeppelin | 11 | 2016 | 2026 | 375 |

---

## Album Companions — High Confidence

Rule: album appears in all `12` available album years and title is distinctive enough for research-grade confidence.

| Album | Years Active | First Year | Latest Year | Listening Events | Container Split |
| --- | --- | --- | --- | --- | --- |
| Ambient 1: Music for Airports | 12 | 2015 | 2026 | 889 | PLAYLIST: 423, UNKNOWN: 390, ALBUM: 64, (blank): 12 |
| Summerteeth | 12 | 2015 | 2026 | 275 | UNKNOWN: 169, ALBUM: 64, PLAYLIST: 37, (blank): 5 |
| Mean Everything To Nothing | 12 | 2015 | 2026 | 270 | ALBUM: 106, (blank): 66, RADIO: 38, PLAYLIST: 31, UNKNOWN: 29 |
| Yankee Hotel Foxtrot | 12 | 2015 | 2026 | 255 | ALBUM: 91, UNKNOWN: 56, PLAYLIST: 53, RADIO: 51, (blank): 4 |
| Hotel California | 12 | 2015 | 2026 | 250 | UNKNOWN: 212, PLAYLIST: 19, ALBUM: 16, (blank): 2, ARTIST: 1 |
| Surfer Rosa (2007 Remaster) | 12 | 2015 | 2026 | 243 | PLAYLIST: 116, UNKNOWN: 55, ALBUM: 46, RADIO: 20, (blank): 6 |
| Key Lime Pie | 12 | 2015 | 2026 | 230 | RADIO: 61, PLAYLIST: 61, ALBUM: 59, UNKNOWN: 48, ARTIST: 1 |
| Yield | 12 | 2015 | 2026 | 230 | ALBUM: 100, RADIO: 53, PLAYLIST: 50, UNKNOWN: 24, (blank): 3 |
| Talk Talk Talk | 12 | 2015 | 2026 | 229 | PLAYLIST: 71, RADIO: 64, ALBUM: 51, UNKNOWN: 18, (blank): 15, ARTIST: 10 |
| Emblems | 12 | 2015 | 2026 | 221 | ALBUM: 88, UNKNOWN: 53, RADIO: 35, PLAYLIST: 34, (blank): 11 |
| Vitalogy | 12 | 2015 | 2026 | 218 | PLAYLIST: 101, ALBUM: 51, UNKNOWN: 40, RADIO: 25, (blank): 1 |
| Cease to Begin | 12 | 2015 | 2026 | 217 | PLAYLIST: 75, UNKNOWN: 62, ALBUM: 52, RADIO: 26, (blank): 1, ARTIST: 1 |
| Plans (Deluxe) | 12 | 2015 | 2026 | 211 | PLAYLIST: 111, RADIO: 42, ALBUM: 41, UNKNOWN: 17 |
| Doolittle | 12 | 2015 | 2026 | 202 | PLAYLIST: 91, RADIO: 45, ALBUM: 34, UNKNOWN: 25, (blank): 7 |
| Workbook | 12 | 2015 | 2026 | 181 | ALBUM: 52, RADIO: 47, UNKNOWN: 45, PLAYLIST: 30, (blank): 7 |
| Hard Promises | 12 | 2015 | 2026 | 180 | PLAYLIST: 125, ALBUM: 29, RADIO: 22, UNKNOWN: 4 |
| Echoes, Silence, Patience & Grace | 12 | 2015 | 2026 | 168 | UNKNOWN: 59, ALBUM: 59, PLAYLIST: 28, RADIO: 22 |
| Out of Time | 12 | 2015 | 2026 | 167 | PLAYLIST: 81, ALBUM: 43, UNKNOWN: 43 |
| Who Would Ever Want Anything So Broken? - EP | 12 | 2015 | 2026 | 158 | PLAYLIST: 84, ALBUM: 40, RADIO: 17, UNKNOWN: 12, (blank): 4, ARTIST: 1 |
| The Psychedelic Furs | 12 | 2015 | 2026 | 140 | PLAYLIST: 64, ALBUM: 46, UNKNOWN: 16, RADIO: 10, (blank): 4 |
| Murmur | 12 | 2015 | 2026 | 135 | PLAYLIST: 95, UNKNOWN: 20, ALBUM: 19, (blank): 1 |
| The Colour And The Shape | 12 | 2015 | 2026 | 130 | ALBUM: 51, RADIO: 32, PLAYLIST: 28, UNKNOWN: 19 |
| Earth Sun Moon | 12 | 2015 | 2026 | 128 | PLAYLIST: 46, UNKNOWN: 39, RADIO: 38, ALBUM: 5 |
| Fables of the Reconstruction | 12 | 2015 | 2026 | 112 | PLAYLIST: 70, UNKNOWN: 24, ALBUM: 18 |
| Nothing's Shocking | 12 | 2015 | 2026 | 108 | ALBUM: 30, RADIO: 24, UNKNOWN: 22, PLAYLIST: 20, (blank): 12 |
| Hunky Dory (2015 Remaster) | 12 | 2015 | 2026 | 107 | UNKNOWN: 43, ALBUM: 27, PLAYLIST: 22, RADIO: 14, (blank): 1 |
| Dreamboat Annie | 12 | 2015 | 2026 | 101 | PLAYLIST: 43, RADIO: 35, ALBUM: 14, UNKNOWN: 8, (blank): 1 |
| Kiss Me, Kiss Me, Kiss Me | 12 | 2015 | 2026 | 100 | PLAYLIST: 37, ALBUM: 30, UNKNOWN: 17, RADIO: 16 |
| Everything All the Time | 12 | 2015 | 2026 | 93 | PLAYLIST: 43, RADIO: 26, UNKNOWN: 16, ALBUM: 8 |
| August and Everything After | 12 | 2015 | 2026 | 92 | ALBUM: 34, UNKNOWN: 30, PLAYLIST: 27, (blank): 1 |
| Flip Your Wig | 12 | 2015 | 2026 | 91 | PLAYLIST: 45, ALBUM: 30, UNKNOWN: 12, RADIO: 4 |
| Taking Up Your Precious Time | 12 | 2015 | 2026 | 86 | PLAYLIST: 70, UNKNOWN: 8, RADIO: 4, (blank): 4 |
| Accelerate | 12 | 2015 | 2026 | 75 | PLAYLIST: 46, ALBUM: 17, RADIO: 10, ARTIST: 1, UNKNOWN: 1 |
| Mirror Moves | 12 | 2015 | 2026 | 66 | PLAYLIST: 42, UNKNOWN: 17, RADIO: 4, ALBUM: 2, (blank): 1 |
| Mr. Tambourine Man | 12 | 2015 | 2026 | 41 | PLAYLIST: 25, RADIO: 13, UNKNOWN: 3 |

---

## Needs Identity Resolution

Rule: album has high persistence but title is ambiguous, generic, compilation-like, or otherwise unsafe without artist metadata.

| Album | Years Active | First Year | Latest Year | Listening Events | Why It Needs Resolution |
| --- | --- | --- | --- | --- | --- |
| Greatest Hits | 12 | 2015 | 2026 | 691 | Album title alone is not a reliable identity key |
| Hit | 12 | 2015 | 2026 | 233 | Album title alone is not a reliable identity key |
| What's Your 20? Essential Tracks 1994-2014 | 12 | 2015 | 2026 | 175 | Album title alone is not a reliable identity key |
| Eye | 12 | 2015 | 2026 | 106 | Album title alone is not a reliable identity key |
| Blind Faith | 12 | 2015 | 2026 | 89 | Album title alone is not a reliable identity key |
| The Wall | 12 | 2015 | 2026 | 75 | Album title alone is not a reliable identity key |
| The Open Door - EP | 12 | 2015 | 2026 | 74 | Album title alone is not a reliable identity key |
| Head Games | 12 | 2015 | 2026 | 56 | Album title alone is not a reliable identity key |
| Madonna | 12 | 2015 | 2026 | 53 | Album title alone is not a reliable identity key |
| Complete | 11 | 2016 | 2026 | 306 | Album title alone is not a reliable identity key |
| Document | 11 | 2015 | 2026 | 292 | Album title alone is not a reliable identity key |
| The Best of Sam Cooke | 11 | 2016 | 2026 | 154 | Album title alone is not a reliable identity key |
| Complete Rarities - I.R.S. 1982-1987 | 11 | 2015 | 2026 | 134 | Album title alone is not a reliable identity key |
| The Hits | 11 | 2016 | 2026 | 132 | Album title alone is not a reliable identity key |
| Greatest Hits 1974-78 | 11 | 2015 | 2026 | 81 | Album title alone is not a reliable identity key |
| The Collection | 11 | 2015 | 2026 | 80 | Album title alone is not a reliable identity key |
| The Very Best of Daryl Hall & John Oates | 11 | 2015 | 2026 | 75 | Album title alone is not a reliable identity key |
| In Time: The Best of R.E.M. 1988-2003 | 11 | 2015 | 2026 | 66 | Album title alone is not a reliable identity key |
| The Best of Faces: Good Boys... When They're Asleep | 11 | 2015 | 2026 | 36 | Album title alone is not a reliable identity key |

---

## Sprint Discoveries

### Surprising discoveries

1. Brian Eno is not just present; he is structurally dominant in the artist data.
2. R.E.M. is a top-tier permanent companion, not merely a remembered favorite.
3. Death Cab for Cutie and Toad the Wet Sprocket are high-ranking permanent companions and deserve review.
4. Album persistence immediately exposed the identity-resolution problem: titles like `Greatest Hits`, `Hit`, and `Complete` cannot be trusted without artist metadata.

### Memory validations

1. The Beatles are validated as a permanent companion.
2. Wilco is validated as a permanent companion, with album support from `Summerteeth` and `Yankee Hotel Foxtrot`.
3. Grateful Dead is validated as a permanent companion.
4. Brian Eno is strongly validated, especially through `Ambient 1: Music for Airports`.
5. Matt Pond PA, R.E.M., Camper Van Beethoven, Pearl Jam, Pixies, and Foo Fighters all validate strongly in artist persistence.

### Memory contradictions / challenges

1. Michelle Shocked is weak in this source despite being meaningful in memory. This suggests source limitation, historical gap, or non-Apple-Music listening.
2. Some albums that feel important may be seasonal, intense, or context-specific rather than permanent companions.
3. Some permanent companions may be ambient, playlist, or background presences rather than explicit favorites.

---

## UI Recommendation

Decision: yes, this deserves a dedicated Music UI feature.

Recommended feature name:

```text
Permanent Companions
```

Recommended subheading:

```text
Who kept showing up across versions of me?
```

Recommended sections:

- Never Leaves
- Deep Companions
- Quiet Constants
- Memory Validated
- Memory Challenged
- Needs Identity Resolution

Implementation should wait until artist and album identity resolution is improved, but the research category is strong enough to preserve.

---

## Next Technical Step

Find or create a durable metadata source with:

```text
artist_name
album_name
song_name
```

Then rebuild Permanent Companions using:

```text
artist_name + album_name
```

as the durable identity key.
