import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:4000";

export default function PlaylistIntelligence() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [selectedPlaylistName, setSelectedPlaylistName] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/music/playlist-intelligence/summary`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
      })
      .then((payload) => {
        setData(payload);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, []);

  if (status === "loading") {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        Loading Playlist Intelligence...
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 shadow-sm dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
        Playlist Intelligence failed to load: {error}
      </div>
    );
  }

  const playlists = Array.isArray(data.playlists) ? data.playlists : [];
  const selectedPlaylist =
    playlists.find((playlist) => playlist.name === selectedPlaylistName) ||
    playlists[0];

  if (!selectedPlaylist) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        Playlist Intelligence loaded, but no playlists were found.
      </div>
    );
  }

  const bridgeSongs = data.bridgeSongs || [];
  const sharedCoreArtists = data.sharedCoreArtists || [];
  const signaturesByPlaylist = (data.playlistSignatures || []).reduce((acc, item) => {
    acc[item.playlist] = acc[item.playlist] || [];
    acc[item.playlist].push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          Music Intelligence
        </p>
        <h2 className="mt-2 text-3xl font-black tracking-tight">
          Playlist Intelligence
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          Playlist worlds, signature songs, bridge songs, and shared artists across the curated cohort.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {playlists.map((playlist) => (
          <button
            key={playlist.name}
            type="button"
            onClick={() => setSelectedPlaylistName(playlist.name)}
            className="rounded-2xl border border-slate-200 bg-white/90 p-5 text-left shadow-sm transition hover:border-blue-400 dark:border-slate-800 dark:bg-slate-900/80"
          >
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-300">
              Playlist World
            </p>
            <h3 className="mt-2 text-xl font-black">{playlist.name}</h3>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-xs text-slate-500">Songs</div>
                <div className="font-black">{playlist.songCount}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Artists</div>
                <div className="font-black">{playlist.artistCount}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Plays</div>
                <div className="font-black">{playlist.totalPlays}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Median</div>
                <div className="font-black">{playlist.medianPlays}</div>
              </div>
            </div>

            <div className="mt-5">
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Signature Songs
              </div>
              <ul className="mt-2 space-y-2">
                {(signaturesByPlaylist[playlist.name] || []).map((song) => (
                  <li key={`${song.artist}-${song.song}`} className="text-sm">
                    <span className="font-bold">{song.song}</span>
                    <span className="block text-xs text-slate-500">
                      {song.artist}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </button>
        ))}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
          Playlist Dossier
        </p>
        <h3 className="mt-2 text-2xl font-black">{selectedPlaylist.name}</h3>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {selectedPlaylist.playlistWorldSummary}
        </p>

        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <div className="text-xs text-slate-500">Exclusive</div>
            <div className="text-xl font-black">{selectedPlaylist.exclusivityScore}%</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <div className="text-xs text-slate-500">Unique Songs</div>
            <div className="text-xl font-black">{selectedPlaylist.exclusiveSongCount}</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <div className="text-xs text-slate-500">Shared Songs</div>
            <div className="text-xl font-black">{selectedPlaylist.sharedSongCount}</div>
          </div>
          <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <div className="text-xs text-slate-500">Total Songs</div>
            <div className="text-xl font-black">{selectedPlaylist.songCount}</div>
          </div>
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <div>
            <h4 className="text-sm font-black uppercase tracking-[0.14em] text-slate-500">
              Signature Songs
            </h4>
            <div className="mt-3 space-y-2">
              {(selectedPlaylist.signatureSongs || []).map((song) => (
                <div
                  key={`${song.artist}-${song.song}`}
                  className="rounded-xl border border-slate-200 p-3 dark:border-slate-800"
                >
                  <div className="text-sm font-black">{song.song}</div>
                  <div className="text-xs text-slate-500">
                    {song.artist} - {song.plays} plays
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-black uppercase tracking-[0.14em] text-slate-500">
              Bridge Songs
            </h4>
            <div className="mt-3 space-y-2">
              {(selectedPlaylist.bridgeSongs || []).map((song) => (
                <div
                  key={`${song.artist}-${song.song}`}
                  className="rounded-xl border border-slate-200 p-3 dark:border-slate-800"
                >
                  <div className="text-sm font-black">{song.song}</div>
                  <div className="text-xs text-slate-500">
                    {song.artist} - {song.playlistCount} playlists
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
          <h3 className="text-lg font-black">Bridge Songs</h3>
          <p className="mt-1 text-sm text-slate-500">
            Songs that appear across multiple playlist worlds.
          </p>
          <div className="mt-4 space-y-3">
            {bridgeSongs.map((song) => (
              <div
                key={`${song.artist}-${song.song}`}
                className="rounded-xl border border-slate-200 p-3 dark:border-slate-800"
              >
                <div className="text-sm font-black">{song.song}</div>
                <div className="text-xs text-slate-500">{song.artist}</div>
                <div className="mt-2 text-xs text-slate-500">
                  {song.playlistCount} playlists · {song.playlists.join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
          <h3 className="text-lg font-black">Shared Artists</h3>
          <p className="mt-1 text-sm text-slate-500">
            Artists appearing across several playlist worlds.
          </p>
          <div className="mt-4 space-y-3">
            {sharedCoreArtists.map((artist) => (
              <div
                key={artist.artist}
                className="rounded-xl border border-slate-200 p-3 dark:border-slate-800"
              >
                <div className="text-sm font-black">{artist.artist}</div>
                <div className="mt-1 text-xs text-slate-500">
                  {artist.playlistCount} playlists · {artist.playlists.join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
