# Artist-Aware Song Context Probe

This report combines the sanitized artist/song daily summary with DuckDB listening context.

Important limitation: DuckDB does not contain a reliable artist column, so context rows are inferred by matching song title on dates where the sanitized artist/song source confirms the artist-song pair.

## Summary

| Target | Artist/Song Events | Artist/Song Dates | DuckDB Context Rows | Playlist | Playlist % | Album | Album % | Radio | Radio % | Unknown + Blank | Unknown % | First Seen | Latest Seen | Context Read | Song Companion Type | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| The Beatles — Love Me Do | 28 | 28 | 33 | 13 | 39.4% | 3 | 9.1% | 11 | 33.3% | 6 | 18.2% | 2016-08-18 | 2026-02-03 | Playlist-carried with radio reinforcement | Playlist/radio cultural marker | Medium |
| Daryl Hall & John Oates — Rich Girl | 23 | 23 | 23 | 4 | 17.4% | 3 | 13.0% | 6 | 26.1% | 10 | 43.5% | 2018-01-23 | 2026-02-22 | Mixed-context | Mixed-context song companion | Medium |
| Phil Collins — I Don't Care Anymore | 13 | 13 | 27 | 6 | 22.2% | 2 | 7.4% | 4 | 14.8% | 15 | 55.6% | 2024-01-20 | 2026-01-30 | Context-lost / unknown-heavy | Context-lost low-volume marker | Medium |
| Son Volt — Tear Stained Eye | 17 | 17 | 31 | 2 | 6.5% | 10 | 32.3% | 15 | 48.4% | 4 | 12.9% | 2016-07-24 | 2026-05-17 | Album-rooted with radio reinforcement | Album/radio identity marker | Medium |
| Uncle Tupelo — Still Be Around | 14 | 14 | 22 | 8 | 36.4% | 4 | 18.2% | 10 | 45.5% | 0 | 0.0% | 2016-11-12 | 2026-05-16 | Playlist-carried with radio reinforcement | Playlist/radio cultural marker | Medium |
| Pearl Jam — Just Breathe | 35 | 35 | 35 | 10 | 28.6% | 2 | 5.7% | 14 | 40.0% | 9 | 25.7% | 2016-05-28 | 2026-05-16 | Playlist-carried with radio reinforcement | Playlist/radio cultural marker | Medium |
| Peter Gabriel — Here Comes the Flood | 97 | 96 | 116 | 68 | 58.6% | 7 | 6.0% | 2 | 1.7% | 39 | 33.6% | 2016-05-29 | 2025-12-27 | Playlist-carried | Playlist-carried song companion | High |
| The Jam — That's Entertainment | 21 | 19 | 47 | 6 | 12.8% | 0 | 0.0% | 0 | 0.0% | 41 | 87.2% | 2016-06-27 | 2026-01-28 | Context-lost / unknown-heavy | Context-lost deep cut | Medium |
| The Police — Hungry for You | 21 | 21 | 26 | 22 | 84.6% | 0 | 0.0% | 4 | 15.4% | 0 | 0.0% | 2016-06-20 | 2026-05-16 | Playlist-carried | Playlist ritual song | Medium |
| The Psychedelic Furs — Heaven | 35 | 34 | 56 | 30 | 53.6% | 10 | 17.9% | 7 | 12.5% | 9 | 16.1% | 2016-04-09 | 2026-02-02 | Mixed-context | Mixed-context song companion | Medium |
| The Greg Kihn Band — The Breakup Song | 0 | 0 | 0 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% | [not found] | [not found] | No DuckDB context rows | Not found / source-limited | Not found |
| Greg Kihn Band — The Breakup Song | 12 | 12 | 10 | 7 | 70.0% | 2 | 20.0% | 0 | 0.0% | 1 | 10.0% | 2017-11-11 | 2026-05-16 | Playlist-carried with album reinforcement | Playlist-carried album gateway | Low |
| Greg Kihn — The Breakup Song | 1 | 1 | 0 | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% | 0 | 0.0% | [not found] | [not found] | No DuckDB context rows | Artist/song found; no context rows | Not found |
| Limbeck — Honk + Wave | 35 | 35 | 38 | 22 | 57.9% | 9 | 23.7% | 0 | 0.0% | 7 | 18.4% | 2018-02-03 | 2025-03-16 | Playlist-carried with album reinforcement | Playlist-carried album gateway | Medium |
| Limbeck — In Ohio on Some Steps | 13 | 13 | 34 | 2 | 5.9% | 7 | 20.6% | 6 | 17.6% | 19 | 55.9% | 2018-02-03 | 2026-01-30 | Context-lost / unknown-heavy | Context-lost low-volume marker | Medium |
| The Box Tops — The Letter | 29 | 29 | 24 | 23 | 95.8% | 1 | 4.2% | 0 | 0.0% | 0 | 0.0% | 2017-10-12 | 2026-05-16 | Playlist-carried | Playlist ritual song | Medium |
| Jefferson Airplane — White Rabbit | 10 | 10 | 16 | 4 | 25.0% | 6 | 37.5% | 6 | 37.5% | 0 | 0.0% | 2017-07-10 | 2026-04-28 | Album-rooted with radio reinforcement | Album/radio identity marker | Low |
| Jefferson Airplane — Somebody to Love | 28 | 28 | 25 | 18 | 72.0% | 2 | 8.0% | 3 | 12.0% | 2 | 8.0% | 2017-10-21 | 2026-01-24 | Playlist-carried | Playlist-carried song companion | Medium |
| The Cure — In Between Days | 31 | 27 | 38 | 2 | 5.3% | 24 | 63.2% | 10 | 26.3% | 2 | 5.3% | 2017-10-14 | 2026-03-26 | Album-rooted with radio reinforcement | Album/radio identity marker | Medium |
| R.E.M. — Radio Free Europe | 11 | 11 | 18 | 5 | 27.8% | 13 | 72.2% | 0 | 0.0% | 0 | 0.0% | 2016-02-18 | 2026-04-26 | Album-rooted with playlist reinforcement | Album/playlist identity marker | Low |
| Pink Floyd — Wish You Were Here | 12 | 12 | 6 | 5 | 83.3% | 0 | 0.0% | 0 | 0.0% | 1 | 16.7% | 2016-04-07 | 2023-03-17 | Playlist-carried | Playlist ritual song | Low |
| Talking Heads — Life During Wartime | 11 | 11 | 8 | 5 | 62.5% | 2 | 25.0% | 0 | 0.0% | 1 | 12.5% | 2016-06-24 | 2023-07-25 | Playlist-carried with album reinforcement | Playlist-carried album gateway | Low |
| Matt Pond PA — Amazing Life | 14 | 14 | 24 | 3 | 12.5% | 7 | 29.2% | 8 | 33.3% | 6 | 25.0% | 2018-11-16 | 2026-05-18 | Album-rooted with radio reinforcement | Album/radio identity marker | Medium |
| Guster — Satellite | 26 | 26 | 101 | 7 | 6.9% | 0 | 0.0% | 4 | 4.0% | 90 | 89.1% | 2017-12-16 | 2026-05-10 | Context-lost / unknown-heavy | Context-lost deep cut | High |
| Sam Cooke — Bring It On Home to Me | 42 | 40 | 49 | 22 | 44.9% | 3 | 6.1% | 7 | 14.3% | 17 | 34.7% | 2016-03-13 | 2026-05-16 | Mixed-context | Mixed-context song companion | Medium |
| The Lemonheads — Into Your Arms | 42 | 42 | 49 | 13 | 26.5% | 10 | 20.4% | 18 | 36.7% | 8 | 16.3% | 2017-03-12 | 2026-05-10 | Playlist-carried with radio reinforcement | Playlist/radio cultural marker | Medium |

## The Beatles — Love Me Do

- Artist/song events from sanitized source: 28
- Artist/song dates from sanitized source: 28
- DuckDB context rows inferred: 33
- Context read: Playlist-carried with radio reinforcement
- Song companion type: Playlist/radio cultural marker
- Confidence: Medium

### Matched Titles

- Love Me Do: 27
- Love Me Do (Mono Version): 1

## Daryl Hall & John Oates — Rich Girl

- Artist/song events from sanitized source: 23
- Artist/song dates from sanitized source: 23
- DuckDB context rows inferred: 23
- Context read: Mixed-context
- Song companion type: Mixed-context song companion
- Confidence: Medium

### Matched Titles

- Rich Girl: 22
- Rich Girl (Remastered 2003): 1

## Phil Collins — I Don't Care Anymore

- Artist/song events from sanitized source: 13
- Artist/song dates from sanitized source: 13
- DuckDB context rows inferred: 27
- Context read: Context-lost / unknown-heavy
- Song companion type: Context-lost low-volume marker
- Confidence: Medium

### Matched Titles

- I Don't Care Anymore: 12
- I Don't Care Anymore (Live): 1

## Son Volt — Tear Stained Eye

- Artist/song events from sanitized source: 17
- Artist/song dates from sanitized source: 17
- DuckDB context rows inferred: 31
- Context read: Album-rooted with radio reinforcement
- Song companion type: Album/radio identity marker
- Confidence: Medium

### Matched Titles

- Tear Stained Eye (2015 Remastered): 13
- Tear Stained Eye: 3
- Tear Stained Eye (Live 1999): 1

## Uncle Tupelo — Still Be Around

- Artist/song events from sanitized source: 14
- Artist/song dates from sanitized source: 14
- DuckDB context rows inferred: 22
- Context read: Playlist-carried with radio reinforcement
- Song companion type: Playlist/radio cultural marker
- Confidence: Medium

### Matched Titles

- Still Be Around: 14

## Pearl Jam — Just Breathe

- Artist/song events from sanitized source: 35
- Artist/song dates from sanitized source: 35
- DuckDB context rows inferred: 35
- Context read: Playlist-carried with radio reinforcement
- Song companion type: Playlist/radio cultural marker
- Confidence: Medium

### Matched Titles

- Just Breathe: 22
- Just Breathe (Live): 11
- Breath: 2

## Peter Gabriel — Here Comes the Flood

- Artist/song events from sanitized source: 97
- Artist/song dates from sanitized source: 96
- DuckDB context rows inferred: 116
- Context read: Playlist-carried
- Song companion type: Playlist-carried song companion
- Confidence: High

### Matched Titles

- Here Comes the Flood: 95
- Here Comes the Flood (Live): 2

## The Jam — That's Entertainment

- Artist/song events from sanitized source: 21
- Artist/song dates from sanitized source: 19
- DuckDB context rows inferred: 47
- Context read: Context-lost / unknown-heavy
- Song companion type: Context-lost deep cut
- Confidence: Medium

### Matched Titles

- That's Entertainment (Demo Version): 13
- That's Entertainment: 3
- That's Entertainment (Remastered): 3
- That's Entertainment (Snap! Demo Version): 1
- That's Entertainment ("The Sound Of The Jam" Version): 1

## The Police — Hungry for You

- Artist/song events from sanitized source: 21
- Artist/song dates from sanitized source: 21
- DuckDB context rows inferred: 26
- Context read: Playlist-carried
- Song companion type: Playlist ritual song
- Confidence: Medium

### Matched Titles

- Hungry for You (Remastered 2003): 17
- Hungry for You (J'Aurais Toujours Faim de Toi): 2
- Hungry for You (J'Aurais Toujours Faim De Toi): 2

## The Psychedelic Furs — Heaven

- Artist/song events from sanitized source: 35
- Artist/song dates from sanitized source: 34
- DuckDB context rows inferred: 56
- Context read: Mixed-context
- Song companion type: Mixed-context song companion
- Confidence: Medium

### Matched Titles

- Heaven: 34
- Heaven (Live at the House of Blues, L.A. 2001): 1

## The Greg Kihn Band — The Breakup Song

- Artist/song events from sanitized source: 0
- Artist/song dates from sanitized source: 0
- DuckDB context rows inferred: 0
- Context read: No DuckDB context rows
- Song companion type: Not found / source-limited
- Confidence: Not found

### Matched Titles

_No matched titles._

## Greg Kihn Band — The Breakup Song

- Artist/song events from sanitized source: 12
- Artist/song dates from sanitized source: 12
- DuckDB context rows inferred: 10
- Context read: Playlist-carried with album reinforcement
- Song companion type: Playlist-carried album gateway
- Confidence: Low

### Matched Titles

- The Breakup Song (They Don't Write 'Em): 12

## Greg Kihn — The Breakup Song

- Artist/song events from sanitized source: 1
- Artist/song dates from sanitized source: 1
- DuckDB context rows inferred: 0
- Context read: No DuckDB context rows
- Song companion type: Artist/song found; no context rows
- Confidence: Not found

### Matched Titles

- The Break Up Song (Studio): 1

## Limbeck — Honk + Wave

- Artist/song events from sanitized source: 35
- Artist/song dates from sanitized source: 35
- DuckDB context rows inferred: 38
- Context read: Playlist-carried with album reinforcement
- Song companion type: Playlist-carried album gateway
- Confidence: Medium

### Matched Titles

- Honk + Wave: 35

## Limbeck — In Ohio on Some Steps

- Artist/song events from sanitized source: 13
- Artist/song dates from sanitized source: 13
- DuckDB context rows inferred: 34
- Context read: Context-lost / unknown-heavy
- Song companion type: Context-lost low-volume marker
- Confidence: Medium

### Matched Titles

- In Ohio on Some Steps: 9
- In Ohio On Some Steps: 4

## The Box Tops — The Letter

- Artist/song events from sanitized source: 29
- Artist/song dates from sanitized source: 29
- DuckDB context rows inferred: 24
- Context read: Playlist-carried
- Song companion type: Playlist ritual song
- Confidence: Medium

### Matched Titles

- The Letter: 29

## Jefferson Airplane — White Rabbit

- Artist/song events from sanitized source: 10
- Artist/song dates from sanitized source: 10
- DuckDB context rows inferred: 16
- Context read: Album-rooted with radio reinforcement
- Song companion type: Album/radio identity marker
- Confidence: Low

### Matched Titles

- White Rabbit: 9
- White Rabbit (Mixed): 1

## Jefferson Airplane — Somebody to Love

- Artist/song events from sanitized source: 28
- Artist/song dates from sanitized source: 28
- DuckDB context rows inferred: 25
- Context read: Playlist-carried
- Song companion type: Playlist-carried song companion
- Confidence: Medium

### Matched Titles

- Somebody to Love: 27
- Somebody to Love (Mono Single Version): 1

## The Cure — In Between Days

- Artist/song events from sanitized source: 31
- Artist/song dates from sanitized source: 27
- DuckDB context rows inferred: 38
- Context read: Album-rooted with radio reinforcement
- Song companion type: Album/radio identity marker
- Confidence: Medium

### Matched Titles

- In Between Days: 23
- In Between Days (Instrumental) [RS Home Demo 12/84]: 4
- End: 2
- In Between Days (Shiver Mix): 1
- In Between Days (Acoustic Version): 1

## R.E.M. — Radio Free Europe

- Artist/song events from sanitized source: 11
- Artist/song dates from sanitized source: 11
- DuckDB context rows inferred: 18
- Context read: Album-rooted with playlist reinforcement
- Song companion type: Album/playlist identity marker
- Confidence: Low

### Matched Titles

- Radio Free Europe: 7
- Radio Free Europe (Live From Rock City, Nottingham / 1984): 2
- Radio Free Europe (Live): 1
- Radio Free Europe (Jacknife Lee Remix / 2025): 1

## Pink Floyd — Wish You Were Here

- Artist/song events from sanitized source: 12
- Artist/song dates from sanitized source: 12
- DuckDB context rows inferred: 6
- Context read: Playlist-carried
- Song companion type: Playlist ritual song
- Confidence: Low

### Matched Titles

- Wish You Were Here: 12

## Talking Heads — Life During Wartime

- Artist/song events from sanitized source: 11
- Artist/song dates from sanitized source: 11
- DuckDB context rows inferred: 8
- Context read: Playlist-carried with album reinforcement
- Song companion type: Playlist-carried album gateway
- Confidence: Low

### Matched Titles

- Life During Wartime: 9
- Life During Wartime (Alternate Version): 2

## Matt Pond PA — Amazing Life

- Artist/song events from sanitized source: 14
- Artist/song dates from sanitized source: 14
- DuckDB context rows inferred: 24
- Context read: Album-rooted with radio reinforcement
- Song companion type: Album/radio identity marker
- Confidence: Medium

### Matched Titles

- Amazing Life: 14

## Guster — Satellite

- Artist/song events from sanitized source: 26
- Artist/song dates from sanitized source: 26
- DuckDB context rows inferred: 101
- Context read: Context-lost / unknown-heavy
- Song companion type: Context-lost deep cut
- Confidence: High

### Matched Titles

- Satellite: 26

## Sam Cooke — Bring It On Home to Me

- Artist/song events from sanitized source: 42
- Artist/song dates from sanitized source: 40
- DuckDB context rows inferred: 49
- Context read: Mixed-context
- Song companion type: Mixed-context song companion
- Confidence: Medium

### Matched Titles

- Bring It On Home to Me: 38
- Bring It on Home to Me: 2
- Bring It On Home to Me (Live at the Harlem Square Club, Miami, FL, 01/1963): 2

## The Lemonheads — Into Your Arms

- Artist/song events from sanitized source: 42
- Artist/song dates from sanitized source: 42
- DuckDB context rows inferred: 49
- Context read: Playlist-carried with radio reinforcement
- Song companion type: Playlist/radio cultural marker
- Confidence: Medium

### Matched Titles

- Into Your Arms: 42

