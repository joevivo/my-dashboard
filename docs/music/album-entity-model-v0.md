# Album Entity Model v0

Define Album Entity
before any Album Intelligence work proceeds.

Sections:

Identity Problem
Canonical Album Identity
Album Entity Definition
Album Variant Membership
Relationship to Session Reconstruction
Relationship to Playlist Intelligence
Future Apple Music Live Data Integration
## Why Album Entity Exists

Album normalization began as an attempt to merge remasters, deluxe editions, anniversary editions, and expanded releases.

Research quickly showed that normalization was not a cleanup problem but an identity problem.

The album universe audit found:

* 17,392 raw album titles
* 595 canonical groups with variants
* 26,203 listening events affected by normalization

Canonical normalization materially changes album rankings.

Examples:

| Album       | Raw Events | Canonical Events |
| ----------- | ---------: | ---------------: |
| Abbey Road  |        110 |              322 |
| Green       |        126 |              289 |
| Document    |        292 |              433 |
| Out of Time |        167 |              306 |

Several albums enter the Top 100 only after canonical normalization:

* Abbey Road
* Green
* Fables of the Reconstruction
* Lifes Rich Pageant
* Murmur
* Narrow Stairs
* Being There
* New Adventures In Hi-Fi
* Let It Be
* A Ghost Is Born
* Every Where Is Some Where
* Several Arrows Later
* The Joshua Tree

Therefore Album Intelligence cannot safely operate on raw Apple album titles.

The foundational analytical entity becomes:

Artist Identity + Canonical Album Title

All future Album Intelligence, Album Relationship Modeling, Session Reconstruction, Playlist Intelligence, and Live Apple Music integration should operate on Album Entities rather than raw album titles.
Finding B-04

Edition metadata accounts for approximately 83% of
album normalization impact events.

Album Entity v1 should prioritize edition normalization.

Album Family can be deferred to a later phase focused on
live albums, acoustic recordings, remix albums,
soundtracks, and other alternative album forms.

## Data Source Finding

### Play Activity Dataset Limitation

The DuckDB `apple_music_play_activity` table does not currently contain artist identity.

Available fields include:

- album_name
- song_name
- event_timestamp
- container_name
- source_type
- play_duration_ms

Artist information is not present.

Consequence:

Play Activity is suitable for:

- Session Reconstruction
- Album Traversals
- Listening behavior analysis
- Event chronology

Play Activity is not sufficient for:

- Album Entity construction
- Artist + Album relationship analysis

Album Entity modeling currently requires enrichment from Library Tracks data, which contains:

- Artist
- Album
- Last Played Date
- Play Count
- Skip Count

Architectural principle:

Identity first, behavior second.

Album Entity = Artist Identity + Canonical Album Title

Behavioral evidence from Play Activity should be attached to Album Entities rather than used to define them.
