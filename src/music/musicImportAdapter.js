import {
  MUSIC_IMPORT_SOURCES,
  createEmptyImportedMusicLibrary,
  createImportRecord,
} from "./musicSchema.js";

const cleanText = (value) => String(value || "").trim();

export function makeMusicId(prefix, ...parts) {
  const body = parts
    .map(cleanText)
    .filter(Boolean)
    .join("-")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return `${prefix}-${body || "unknown"}`;
}

function readTrackTitle(rawTrack) {
  return cleanText(
    rawTrack.title ||
      rawTrack.name ||
      rawTrack.trackName ||
      rawTrack["Track Name"]
  );
}

function readArtistName(rawTrack) {
  return cleanText(
    rawTrack.artist ||
      rawTrack.artistName ||
      rawTrack.albumArtist ||
      rawTrack["Artist"] ||
      "Unknown Artist"
  );
}

function readAlbumTitle(rawTrack) {
  return cleanText(
    rawTrack.album ||
      rawTrack.albumName ||
      rawTrack.collectionName ||
      rawTrack["Album"] ||
      "Unknown Album"
  );
}

function readDurationMs(rawTrack) {
  const value =
    rawTrack.durationMs ||
    rawTrack.duration ||
    rawTrack.trackTimeMillis ||
    rawTrack["Total Time"];

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function normalizeGenericMusicImport(
  input,
  {
    source = MUSIC_IMPORT_SOURCES.GENERIC_JSON,
    fileName = "",
  } = {}
) {
  const library = createEmptyImportedMusicLibrary();

  const rawTracks = Array.isArray(input)
    ? input
    : Array.isArray(input?.tracks)
      ? input.tracks
      : Array.isArray(input?.songs)
        ? input.songs
        : [];

  const rawPlaylists = Array.isArray(input?.playlists) ? input.playlists : [];

  const upsertTrack = (rawTrack = {}) => {
    const title = readTrackTitle(rawTrack);
    const artistName = readArtistName(rawTrack);
    const albumTitle = readAlbumTitle(rawTrack);

    if (!title) return null;

    const artistId =
      cleanText(rawTrack.artistId) || makeMusicId("artist", artistName);

    const albumId =
      cleanText(rawTrack.albumId) ||
      makeMusicId("album", artistName, albumTitle);

    const trackId =
      cleanText(rawTrack.id) ||
      cleanText(rawTrack.trackId) ||
      cleanText(rawTrack.persistentId) ||
      cleanText(rawTrack.appleMusicId) ||
      makeMusicId("track", artistName, albumTitle, title);

    library.artists[artistId] = {
      id: artistId,
      name: artistName,
    };

    library.albums[albumId] = {
      id: albumId,
      title: albumTitle,
      artistId,
    };

    library.tracks[trackId] = {
      id: trackId,
      title,
      artistId,
      albumId,
      durationMs: readDurationMs(rawTrack),
      source,
      raw: rawTrack,
    };

    return trackId;
  };

  rawTracks.forEach(upsertTrack);

  rawPlaylists.forEach((rawPlaylist = {}) => {
    const name = cleanText(rawPlaylist.name || rawPlaylist.title);

    if (!name) return;

    const playlistId =
      cleanText(rawPlaylist.id) ||
      cleanText(rawPlaylist.playlistId) ||
      makeMusicId("playlist", name);

    const playlistItems =
      rawPlaylist.trackIds ||
      rawPlaylist.tracks ||
      rawPlaylist.items ||
      [];

    const trackIds = playlistItems
      .map((item) => {
        if (typeof item === "string") return item;
        return upsertTrack(item);
      })
      .filter(Boolean);

    library.playlists[playlistId] = {
      id: playlistId,
      name,
      trackIds,
      source,
      raw: rawPlaylist,
    };
  });

  library.imports.push(
    createImportRecord({
      source,
      fileName,
      trackCount: Object.keys(library.tracks).length,
      artistCount: Object.keys(library.artists).length,
      albumCount: Object.keys(library.albums).length,
      playlistCount: Object.keys(library.playlists).length,
    })
  );

  return library;
}
