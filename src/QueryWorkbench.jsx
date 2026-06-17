import { useState } from "react";

export default function QueryWorkbench({ onOpenArtist }) {
  const [mode, setMode] = useState("artist");
  const [query, setQuery] = useState("");
  const [songArtist, setSongArtist] = useState("");
  const [songTitle, setSongTitle] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const daysSince = (dateString) => {
    if (!dateString) return null;

    const played = new Date(dateString);
    const now = new Date();

    const diffDays = Math.floor(
      (now - played) / (1000 * 60 * 60 * 24)
    );

    if (diffDays < 30) {
      return `${diffDays} days ago`;
    }

    if (diffDays < 365) {
      return `${Math.floor(diffDays / 30)} months ago`;
    }

    return `${Math.floor(diffDays / 365)} years ago`;
  };

  const runArtistSearch = async (artistName) => {
    const trimmed = artistName.trim();

    if (!trimmed) {
      setError("Enter an artist name.");
      setResult(null);
      return;
    }

    setMode("artist");
    setQuery(trimmed);
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:4000/api/music/query/artist?name=${encodeURIComponent(trimmed)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Artist query failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Artist query failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const runSearch = async () => {
    const trimmed = query.trim();

    if (!trimmed) {
      setError("Enter an artist name.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:4000/api/music/query/artist?name=${encodeURIComponent(trimmed)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Artist query failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Artist query failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const runSongSearch = async () => {
    const trimmedArtist = songArtist.trim();
    const trimmedSong = songTitle.trim();

    if (!trimmedArtist || !trimmedSong) {
      setError("Enter both an artist and a song.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:4000/api/music/query/song?artist=${encodeURIComponent(trimmedArtist)}&song=${encodeURIComponent(trimmedSong)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Song query failed.");
      }

      setResult({
        ...data,
        resultType: "song",
      });
    } catch (err) {
      setError(err.message || "Song query failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const runDateSearch = async () => {
    if (!dateStart || !dateEnd) {
      setError("Select both a start date and an end date.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:4000/api/music/time-machine?start=${encodeURIComponent(dateStart)}&end=${encodeURIComponent(dateEnd)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Date range query failed.");
      }

      setResult({
        ...data,
        resultType: "date",
      });
    } catch (err) {
      setError(err.message || "Date range query failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };


  const songs = result?.topSongs || [];
  const albums = result?.topAlbums || [];
  const timeline = result?.timeline || [];
  const family = result?.family || null;
  const familyMembers = family?.members || family?.aliases || [];
  const probeArtists = [
    "Peter Gabriel",
    "Billie Holiday",
    "Neil Young",
    "Neil Young & Crazy Horse",
    "Elvis Costello",
    "Elvis Costello & The Attractions",
    "Tom Petty",
    "Robyn Hitchcock",
    "HÃ¼sker DÃ¼",
    "BjÃ¶rk",
    "SinÃ©ad O'Connor",
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          Intelligence
        </p>
        <h2 className="mt-2 text-3xl font-black tracking-tight">Query Workbench</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          Ask direct questions of the archive. Artist lookup is currently backed by Apple Music Library Tracks reconstruction.
        </p>
      </section>

      <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
        <div className="flex flex-wrap gap-2">
          {["artist", "song", "date"].map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setMode(item);
                setResult(null);
                setError("");
              }}
              className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.14em] ${
                mode === item
                  ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-200"
                  : "border-slate-300 text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
              }`}
            >
              {item === "artist"
                ? "Artist"
                : item === "song"
                ? "Song"
                : "Date"}
            </button>
          ))}
        </div>

        <label className="mt-5 block text-sm font-bold">
          {mode === "artist"
            ? "Artist Lookup"
            : mode === "song"
            ? "Song Lookup"
            : "Date Range"}
        </label>
        {mode === "artist" ? (
          <div className="mt-3 flex gap-3">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && runSearch()}
              className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
              placeholder="Try Billie Holiday, Sam Cooke, The Misfits, Peter Gabriel..."
            />
            <button
              type="button"
              onClick={runSearch}
              disabled={loading}
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        ) : mode === "song" ? (
          <div className="mt-3 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <input
              value={songArtist}
              onChange={(event) => setSongArtist(event.target.value)}
              className="rounded-xl border border-slate-300 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
              placeholder="Artist, e.g. Guster"
            />
            <input
              value={songTitle}
              onChange={(event) => setSongTitle(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && runSongSearch()}
              className="rounded-xl border border-slate-300 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
              placeholder="Song, e.g. Satellite"
            />
            <button
              type="button"
              onClick={runSongSearch}
              disabled={loading}
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        ) : (
          <div className="mt-3 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <input
              type="date"
              value={dateStart}
              onChange={(event) => setDateStart(event.target.value)}
              className="rounded-xl border border-slate-300 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
            />
            <input
              type="date"
              value={dateEnd}
              onChange={(event) => setDateEnd(event.target.value)}
              className="rounded-xl border border-slate-300 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950"
            />
            <button
              type="button"
              onClick={runDateSearch}
              disabled={loading}
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Analyzing..." : "Analyze Range"}
            </button>
          </div>
        )}
      
        <div className="mt-4">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-bold uppercase tracking-[0.16em] text-slate-500">
              Examples
            </span>

            {[
              "Peter Gabriel",
              "Billie Holiday",
              "Neil Young",
              "Tom Petty",
              "HÃ¼sker DÃ¼"
            ].map((artist) => (
              <button
                key={artist}
                type="button"
                onClick={() => setQuery(artist)}
                className="rounded-full border border-slate-300 px-3 py-1 font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                {artist}
              </button>
            ))}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="font-bold uppercase tracking-[0.16em] text-slate-500">
              Research Probes
            </span>

            {[
              "Neil Young & Crazy Horse",
              "Elvis Costello & The Attractions",
              "Robyn Hitchcock",
              "BjÃ¶rk",
              "SinÃ©ad O'Connor"
            ].map((artist) => (
              <button
                key={artist}
                type="button"
                onClick={() => setQuery(artist)}
                className="rounded-full border border-blue-300 px-3 py-1 font-bold hover:bg-blue-50 dark:border-blue-700 dark:hover:bg-slate-800"
              >
                {artist}
              </button>
            ))}
          </div>
        </div>
      </section>

      {error ? (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-red-200 dark:bg-slate-900/80 dark:border-red-900">
          <h3 className="text-lg font-black">Query failed</h3>
          <p className="mt-2 text-sm text-red-600 dark:text-red-300">{error}</p>
        </section>
      ) : result ? (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-300">
            {result.resultType === "song"
              ? result.song_companion_type || "Song result"
              : result.resultType === "date"
              ? "Period Intelligence"
              : result.classification || result.source || "Artist result"}
          </p>
          <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-2xl font-black">
                {result.resultType === "song"
                  ? result.label
                  : result.resultType === "date"
                  ? "Period Intelligence"
                  : result.artist}
              </h3>

              {result.resultType === "date" ? (
                <p className="mt-1 text-sm text-slate-500">
                  {dateStart} â†’ {dateEnd}
                </p>
              ) : null}
            </div>
            {result.resultType === "artist" && onOpenArtist ? (
              <button
                type="button"
                onClick={() => onOpenArtist(result.artist || query)}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                Open Artist Intelligence
              </button>
            ) : null}
          </div>
          {result.resultType === "song" ? (
            <div className="mt-5 space-y-5">
              <div className="grid gap-3 md:grid-cols-4">
                <div>
                  <p className="text-xs text-slate-500">Events</p>
                  <p className="text-xl font-black">{result.artist_song_events}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Context Rows</p>
                  <p className="text-xl font-black">{result.duckdb_context_rows}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">First Seen</p>
                  <p className="text-xl font-black">{result.first_seen}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Latest Seen</p>
                  <p className="text-xl font-black">{result.latest_seen}</p>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                  Song Context
                </p>
                <p className="mt-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                  {result.context_read}
                </p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  Confidence: {result.confidence}
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-4">
                <div>
                  <p className="text-xs text-slate-500">Playlist Share</p>
                  <p className="text-xl font-black">{Math.round((result.playlist_share || 0) * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Album Share</p>
                  <p className="text-xl font-black">{Math.round((result.album_share || 0) * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Radio Share</p>
                  <p className="text-xl font-black">{Math.round((result.radio_share || 0) * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Unknown Share</p>
                  <p className="text-xl font-black">{Math.round((result.unknown_share || 0) * 100)}%</p>
                </div>
              </div>
            </div>
          ) : result.resultType === "date" ? (
            <div className="mt-5 space-y-5">

              <div className="grid gap-3 md:grid-cols-4">
                <div>
                  <p className="text-xs text-slate-500">Tracks Matched</p>
                  <p className="text-xl font-black">{result.tracksMatched}</p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Anchor Artist</p>
                  <p className="text-xl font-black">
                    {result.topArtists?.[0]?.artist || "-"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Anchor Album</p>
                  <p className="text-xl font-black">
                    {result.topAlbums?.[0]?.album || "-"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Source</p>
                  <p className="text-xl font-black">Time Machine</p>
                </div>
              </div>

              {result.memoryRead?.length ? (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                    Memory Read
                  </p>

                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                    {result.memoryRead.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {result.topArtists?.length ? (
                <div>
                  <h4 className="text-sm font-black">Top Artists</h4>
                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                    {result.topArtists.slice(0, 5).map((item) => (
                      <li key={item.artist}>
                        <button
                          type="button"
                          onClick={() => runArtistSearch(item.artist)}
                          className="font-bold text-blue-700 hover:underline dark:text-blue-300"
                        >
                          {item.artist}
                        </button>{" "}
                        ({item.count})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {result.topAlbums?.length ? (
                <div>
                  <h4 className="text-sm font-black">Top Albums</h4>
                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                    {result.topAlbums.slice(0, 5).map((item) => (
                      <li key={item.album}>
                        {item.album} ({item.count})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

            </div>
          ) : (
            <>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{result.notes}</p>

          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
              Normalization Status
            </p>
            {family ? (
              <div className="mt-2 space-y-2">
                <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  Family: {family.name || family.family || "Mapped artist family"}
                </p>
                {familyMembers.length ? (
                  <div className="flex flex-wrap gap-2">
                    {familyMembers.map((member) => (
                      <span
                        key={member}
                        className="rounded-full border border-slate-300 px-3 py-1 text-xs dark:border-slate-700"
                      >
                        {member}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                No family mapping found. This is useful normalization debt if the artist belongs to a known artist family.
              </p>
            )}
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Actual Plays</p>
              <p className="text-xl font-black">{result.actualPlays ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Hours Listened</p>
              <p className="text-xl font-black">{result.hoursListened ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Actual Skips</p>
              <p className="text-xl font-black">{result.actualSkips ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Years Represented</p>
              <p className="text-xl font-black">{result.yearsActive}</p>
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-300">
            <span className="font-bold text-slate-800 dark:text-slate-100">Evidence:</span>{" "}
            Library Evidence {result.libraryEvidenceRecords ?? result.totalPlays ?? "-"} records ·{" "}
            First Seen {result.firstPlayedDate || result.firstSeen || "-"} ·{" "}
            Latest Seen {result.latestPlayedDate || result.latestSeen || "-"}
            {result.latestPlayedDate ? (
              <span> · {daysSince(result.latestPlayedDate)}</span>
            ) : null}
          </div>

          {songs.length ? (
            <div className="mt-6">
              <h4 className="text-sm font-black">Top Songs</h4>
              <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                {songs.map((item) => (
                  <li key={item.song}>
                    {item.song}
                    {item.plays ? ` â€” ${item.plays}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {albums.length ? (
            <div className="mt-6">
              <h4 className="text-sm font-black">Top Albums</h4>
              <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                {albums.map((item) => (
                  <li key={item.album}>
                    {item.album}
                    {item.plays ? ` â€” ${item.plays}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {timeline.length ? (
            <div className="mt-6">
              <h4 className="text-sm font-black">Timeline</h4>
              <div className="mt-2 flex flex-wrap gap-2">
                {timeline.map((item) => (
                  <span
                    key={item.year}
                    className="rounded-full border border-slate-300 px-3 py-1 text-xs dark:border-slate-700"
                  >
                    {item.year}: {item.count}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
            </>
          )}
        </section>
      ) : null}


    </div>
  );
}





