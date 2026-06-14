import { useState } from "react";

export default function QueryWorkbench({ onOpenArtist }) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  const songs = result?.topSongs || [];
  const albums = result?.topAlbums || [];
  const timeline = result?.timeline || [];

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
        <label className="text-sm font-bold">Artist Lookup</label>
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
      </section>

      {error ? (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-red-200 dark:bg-slate-900/80 dark:border-red-900">
          <h3 className="text-lg font-black">Query failed</h3>
          <p className="mt-2 text-sm text-red-600 dark:text-red-300">{error}</p>
        </section>
      ) : result ? (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-300">
            {result.classification || result.source || "Artist result"}
          </p>
          <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h3 className="text-2xl font-black">{result.artist}</h3>
            {onOpenArtist ? (
              <button
                type="button"
                onClick={() => onOpenArtist(result.artist || query)}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                Open Artist Intelligence
              </button>
            ) : null}
          </div>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{result.notes}</p>

          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Total Plays</p>
              <p className="text-xl font-black">{result.totalPlays}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Years Active</p>
              <p className="text-xl font-black">{result.yearsActive}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">First Seen</p>
              <p className="text-xl font-black">{result.firstSeen}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Latest Seen</p>
              <p className="text-xl font-black">{result.latestSeen}</p>
            </div>
          </div>

          {songs.length ? (
            <div className="mt-6">
              <h4 className="text-sm font-black">Top Songs</h4>
              <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                {songs.map((item) => (
                  <li key={item.song}>
                    {item.song}
                    {item.plays ? ` — ${item.plays}` : ""}
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
                    {item.plays ? ` — ${item.plays}` : ""}
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
        </section>
      ) : (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
          <h3 className="text-lg font-black">Search the archive</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Enter an artist to inspect library-track reconstruction, persistence, albums, songs, and timeline evidence.
          </p>

          <div className="mt-4">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
              Try
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {["Peter Gabriel", "Billie Holiday", "The Feelies", "Sam Cooke", "H?sker D?", "The Replacements"].map((artist) => (
                <button
                  key={artist}
                  type="button"
                  onClick={() => setQuery(artist)}
                  className="rounded-full border border-slate-300 px-3 py-1 text-xs font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  {artist}
                </button>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
