export function selectImportedMusicStats(library) {
  if (!library) {
    return {
      tracks: 0,
      artists: 0,
      albums: 0,
      playlists: 0,
      playlistTrackLinks: 0,
      imports: 0,
    };
  }

  const playlists = Object.values(library.playlists || {});

  return {
    tracks: Object.keys(library.tracks || {}).length,
    artists: Object.keys(library.artists || {}).length,
    albums: Object.keys(library.albums || {}).length,
    playlists: playlists.length,
    playlistTrackLinks: playlists.reduce(
      (sum, playlist) => sum + (playlist.trackIds?.length || 0),
      0
    ),
    imports: library.imports?.length || 0,
  };
}

export function selectTopImportedArtists(library, limit = 10) {
  if (!library) return [];

  const counts = {};

  Object.values(library.tracks || {}).forEach((track) => {
    counts[track.artistId] = (counts[track.artistId] || 0) + 1;
  });

  return Object.entries(counts)
    .map(([artistId, count]) => ({
      artistId,
      name: library.artists?.[artistId]?.name || "Unknown Artist",
      count,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}
