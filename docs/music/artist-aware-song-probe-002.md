# Artist-Aware Song Context Probe

This report combines the sanitized artist/song daily summary with DuckDB listening context.

Important limitation: DuckDB does not contain a reliable artist column, so context rows are inferred by matching song title on dates where the sanitized artist/song source confirms the artist-song pair.

## Summary

| Target | Artist/Song Events | Artist/Song Dates | DuckDB Context Rows | Playlist | Playlist % | Album | Album % | Radio | Radio % | Unknown + Blank | Unknown % | First Seen | Latest Seen | Context Read | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Matt Pond PA — New Hampshire | 12 | 11 | 20 | 3 | 15.0% | 10 | 50.0% | 0 | 0.0% | 7 | 35.0% | 2016-05-04 | 2025-03-22 | Album-carried | Medium |
| Matt Pond PA — Measure 3 | 41 | 41 | 32 | 11 | 34.4% | 4 | 12.5% | 4 | 12.5% | 13 | 40.6% | 2016-05-04 | 2026-05-16 | Mixed-context | Medium |
| The Lemonheads — Confetti | 48 | 46 | 49 | 13 | 26.5% | 9 | 18.4% | 16 | 32.7% | 11 | 22.4% | 2016-09-05 | 2026-05-19 | Playlist-carried with radio reinforcement | Medium |
| The Lemonheads — Bit Part | 24 | 24 | 20 | 5 | 25.0% | 5 | 25.0% | 0 | 0.0% | 10 | 50.0% | 2016-05-21 | 2025-06-15 | Context-lost / unknown-heavy | Medium |
| A Flock of Seagulls — Space Age Love Song | 31 | 31 | 16 | 11 | 68.8% | 0 | 0.0% | 0 | 0.0% | 5 | 31.2% | 2016-12-25 | 2024-12-29 | Playlist-carried | Low |
| Wang Chung — To Live and Die in L.A. | 17 | 17 | 17 | 17 | 100.0% | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% | 2020-06-04 | 2026-02-07 | Playlist-carried | Low |
| Peter Gabriel — Mercy Street | 20 | 20 | 22 | 15 | 68.2% | 4 | 18.2% | 0 | 0.0% | 3 | 13.6% | 2016-07-01 | 2023-06-02 | Playlist-carried | Medium |
| Radiohead — Fake Plastic Trees | 44 | 44 | 54 | 37 | 68.5% | 3 | 5.6% | 10 | 18.5% | 4 | 7.4% | 2016-06-07 | 2026-05-11 | Playlist-carried | Medium |
| Against Me! — White People for Peace | 36 | 35 | 105 | 31 | 29.5% | 23 | 21.9% | 4 | 3.8% | 47 | 44.8% | 2016-02-19 | 2026-05-07 | Mixed-context | High |
| Toad the Wet Sprocket — Fall Down | 102 | 96 | 151 | 46 | 30.5% | 64 | 42.4% | 2 | 1.3% | 39 | 25.8% | 2016-06-25 | 2026-05-19 | Album-rooted with playlist reinforcement | High |

## Matt Pond PA — New Hampshire

- Artist/song events from sanitized source: 12
- Artist/song dates from sanitized source: 11
- DuckDB context rows inferred: 20
- Context read: Album-carried
- Confidence: Medium

### Matched Titles

- New Hampshire: 12

## Matt Pond PA — Measure 3

- Artist/song events from sanitized source: 41
- Artist/song dates from sanitized source: 41
- DuckDB context rows inferred: 32
- Context read: Mixed-context
- Confidence: Medium

### Matched Titles

- Measure 3: 38
- #3: 3

## The Lemonheads — Confetti

- Artist/song events from sanitized source: 48
- Artist/song dates from sanitized source: 46
- DuckDB context rows inferred: 49
- Context read: Playlist-carried with radio reinforcement
- Confidence: Medium

### Matched Titles

- Confetti: 37
- Confetti (Remastered): 7
- Confetti (Demo Version): 3
- Confetti (Acoustic): 1

## The Lemonheads — Bit Part

- Artist/song events from sanitized source: 24
- Artist/song dates from sanitized source: 24
- DuckDB context rows inferred: 20
- Context read: Context-lost / unknown-heavy
- Confidence: Medium

### Matched Titles

- Bit Part: 10
- Bit Part (Remastered): 6
- Bit Part (Demo Version): 6
- Bit Part (2022 Remastered Edition): 2

## A Flock of Seagulls — Space Age Love Song

- Artist/song events from sanitized source: 31
- Artist/song dates from sanitized source: 31
- DuckDB context rows inferred: 16
- Context read: Playlist-carried
- Confidence: Low

### Matched Titles

- Space Age Love Song (Re-Recorded / Remastered): 17
- Space Age Love Song: 13
- Space Age Love Song (Extended Remix): 1

## Wang Chung — To Live and Die in L.A.

- Artist/song events from sanitized source: 17
- Artist/song dates from sanitized source: 17
- DuckDB context rows inferred: 17
- Context read: Playlist-carried
- Confidence: Low

### Matched Titles

- To Live and Die in L.A.: 11
- To Live And Die In L.A. (From "To Live And Die In L.A." Soundtrack): 5
- Wait (From "To Live And Die In L.A." Soundtrack): 1

## Peter Gabriel — Mercy Street

- Artist/song events from sanitized source: 20
- Artist/song dates from sanitized source: 20
- DuckDB context rows inferred: 22
- Context read: Playlist-carried
- Confidence: Medium

### Matched Titles

- Mercy Street: 17
- Mercy Street (New Blood Version): 1
- Mercy Street (Live): 1
- Mercy Street (William Orbit Mix): 1

## Radiohead — Fake Plastic Trees

- Artist/song events from sanitized source: 44
- Artist/song dates from sanitized source: 44
- DuckDB context rows inferred: 54
- Context read: Playlist-carried
- Confidence: Medium

### Matched Titles

- Fake Plastic Trees: 43
- Fake Plastic Trees (Acoustic Version) [Live]: 1

## Against Me! — White People for Peace

- Artist/song events from sanitized source: 36
- Artist/song dates from sanitized source: 35
- DuckDB context rows inferred: 105
- Context read: Mixed-context
- Confidence: High

### Matched Titles

- White People for Peace: 36

## Toad the Wet Sprocket — Fall Down

- Artist/song events from sanitized source: 102
- Artist/song dates from sanitized source: 96
- DuckDB context rows inferred: 151
- Context read: Album-rooted with playlist reinforcement
- Confidence: High

### Matched Titles

- Fall Down: 70
- Fall Down (Live at Catspaw Studios, Atlanta, GA, 06/1994): 13
- Fall Down (Live at Sony Studios, NY, May 1995): 8
- Fall Down (Acoustic): 5
- Fall Down (2011 Re-Recording): 3
- Fall Down (Live): 2
- Fall Down (Re-Recorded): 1

