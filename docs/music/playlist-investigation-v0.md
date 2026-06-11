\# Playlist Investigation v0



Generated: 2026-06-10



\## Purpose



Determine whether Apple Music playlist identity is recoverable for Defending Sisyphus.



The original question was not just:



```text

Was this play playlist-carried?

```



The real question was:



```text

Which playlist carried it?

```



\## Confirmed Sources



Original Apple Media Services export:



```text

C:\\Users\\joevi\\ams\\Apple\_Media\_Services\\Apple Music Activity

```



Important files:



\* `Apple Music Library Playlists.json.zip`

\* `Apple Music Library Tracks.json.zip`

\* `Apple Music Play Activity.csv`

\* `Apple Music - Container Details.csv`

\* `Apple Music - Recently Played Containers.csv`



\## Key Findings



\### Playlist membership is recoverable



Confirmed join:



```text

Apple Music Library Playlists.json

Playlist Item Identifiers

→

Apple Music Library Tracks.json

Track Identifier

```



Observed:



| Metric                                       |  Value |

| -------------------------------------------- | -----: |

| Playlists                                    |    312 |

| Tracks                                       | 34,643 |

| Playlist item references                     | 23,066 |

| Unique playlist item references              | 14,733 |

| Playlist item refs matching Track Identifier | 14,733 |

| Match rate                                   | 100.0% |

| Playlists with zero items                    |     83 |

| Largest playlist item count                  |    945 |



Conclusion:



```text

Playlist-to-track membership is fully recoverable.

```



\### Playlist play-event attribution is partially recoverable



`Apple Music Play Activity.csv` has 66,812 playlist play rows.



Important field:



```text

Container iTunes Playlist ID

```



Observed:



| Field                        | Filled Rows | Fill Rate |

| ---------------------------- | ----------: | --------: |

| Container Name               |           0 |      0.0% |

| Container iTunes Playlist ID |      47,186 |     70.6% |



Confirmed join:



```text

Apple Music Play Activity.csv

Container iTunes Playlist ID

→

Apple Music Library Playlists.json

Container Identifier

```



Observed:



| Field                        | Unique Values | Matching Playlist IDs | Match Rate |

| ---------------------------- | ------------: | --------------------: | ---------: |

| Container iTunes Playlist ID |           202 |                   202 |     100.0% |



Conclusion:



```text

Historical playlist play-event attribution is recoverable for about 70.6% of playlist play rows.

```



\## Capability Matrix



| Question                                        | Answer                                     |

| ----------------------------------------------- | ------------------------------------------ |

| Which playlists exist?                          | Yes                                        |

| Which tracks are in each playlist?              | Yes                                        |

| Which playlists contain a song?                 | Yes                                        |

| Which playlists contain an artist?              | Yes                                        |

| Which playlists contain an album?               | Yes                                        |

| Which playlist carried a historical play event? | Yes, for about 70.6% of playlist play rows |

| Are all playlist play events attributable?      | No                                         |



\## Privacy Boundary



Do not commit raw playlist membership exports by default.



Safe to commit:



\* scripts

\* schema notes

\* aggregate summaries

\* planning docs



Keep generated playlist data local:



```text

C:\\Users\\joevi\\apple-music-sanitized

```



\## Recommended Next Sprint



```text

Music Playlist Investigation v1 — Build Safe Playlist Extractor

```



\## Proposed Script



```text

data/music/scripts/extract\_playlist\_intelligence.py

```



\## Proposed Local Outputs



```text

C:\\Users\\joevi\\apple-music-sanitized\\apple-music-playlist-inventory.csv

C:\\Users\\joevi\\apple-music-sanitized\\apple-music-playlist-tracks.csv

C:\\Users\\joevi\\apple-music-sanitized\\apple-music-playlist-play-attribution.csv

C:\\Users\\joevi\\apple-music-sanitized\\apple-music-playlist-investigation-summary.md

```



\## First Useful Reports



1\. Which playlists contain this song?

2\. Which playlists contain this artist?

3\. Which playlists contain this album?

4\. Which playlists actually carried playlist-context plays?

5\. Which playlists preserve long-term companions that do not appear in top-artist charts?



\## Working Principle



```text

Albums have gravity.

Artists persist.

Songs recur.

Playlists preserve.

```



