# Artist-Aware Song Context Probe

This report combines the sanitized artist/song daily summary with DuckDB listening context.

Important limitation: DuckDB does not contain a reliable artist column, so context rows are inferred by matching song title on dates where the sanitized artist/song source confirms the artist-song pair.

## Summary

| Target | Artist/Song Events | Artist/Song Dates | DuckDB Context Rows | Playlist | Playlist % | Album | Album % | Radio | Radio % | Unknown + Blank | Unknown % | First Seen | Latest Seen | Context Read | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pearl Jam — Black | 62 | 55 | 93 | 36 | 38.7% | 22 | 23.7% | 8 | 8.6% | 27 | 29.0% | 2016-01-30 | 2026-03-25 | Mixed-context | High |
| R.E.M. — Untitled | 25 | 25 | 31 | 8 | 25.8% | 10 | 32.3% | 7 | 22.6% | 6 | 19.4% | 2016-04-30 | 2026-05-18 | Album-rooted with radio reinforcement | Medium |
| Matt Pond PA — KC | 28 | 27 | 56 | 8 | 14.3% | 24 | 42.9% | 5 | 8.9% | 19 | 33.9% | 2016-05-04 | 2026-02-13 | Mixed-context | Medium |
| David Essex — Rock On | 36 | 35 | 34 | 19 | 55.9% | 0 | 0.0% | 9 | 26.5% | 6 | 17.6% | 2018-09-25 | 2026-05-10 | Playlist-carried with radio reinforcement | Medium |
| The Beatles — Let It Be | 8 | 8 | 12 | 0 | 0.0% | 5 | 41.7% | 0 | 0.0% | 7 | 58.3% | 2021-06-26 | 2026-02-02 | Context-lost / unknown-heavy | Low |

## Pearl Jam — Black

- Artist/song events from sanitized source: 62
- Artist/song dates from sanitized source: 55
- DuckDB context rows inferred: 93
- Context read: Mixed-context
- Confidence: High

### Matched Titles

- Black: 43
- Spin the Black Circle: 5
- Black (Live): 3
- Black, Red, Yellow: 2
- Black (2004 Remix): 2
- Black, Red, Yellow (Live): 2
- Black (Brendan O'Brien Mix): 2
- Black (Live MTV Unplugged): 2
- Black (Kaufman Astoria Studios - MTV Unplugged - New York, NY 3/16/1992): 1

## R.E.M. — Untitled

- Artist/song events from sanitized source: 25
- Artist/song dates from sanitized source: 25
- DuckDB context rows inferred: 31
- Context read: Album-rooted with radio reinforcement
- Confidence: Medium

### Matched Titles

- Untitled (Remastered 2013): 14
- Untitled (Remastered): 8
- Untitled Demo 2: 2
- Untitled: 1

## Matt Pond PA — KC

- Artist/song events from sanitized source: 28
- Artist/song dates from sanitized source: 27
- DuckDB context rows inferred: 56
- Context read: Mixed-context
- Confidence: Medium

### Matched Titles

- Kc: 18
- KC: 7
- Close (KC Two): 3

## David Essex — Rock On

- Artist/song events from sanitized source: 36
- Artist/song dates from sanitized source: 35
- DuckDB context rows inferred: 34
- Context read: Playlist-carried with radio reinforcement
- Confidence: Medium

### Matched Titles

- Rock On: 36

## The Beatles — Let It Be

- Artist/song events from sanitized source: 8
- Artist/song dates from sanitized source: 8
- DuckDB context rows inferred: 12
- Context read: Context-lost / unknown-heavy
- Confidence: Low

### Matched Titles

- Let It Be: 6
- Let It Be (2021 Mix): 1
- Let It Be (Single Version / 2021 Mix): 1

