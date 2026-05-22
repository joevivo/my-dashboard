export const IMPORTED_MUSIC_SCHEMA_VERSION = 1;

export const MUSIC_IMPORT_SOURCES = {
  APPLE_MUSIC_EXPORT: "apple-music-export",
  GENERIC_JSON: "generic-json",
  MANUAL_BACKUP: "manual-backup",
};

export function createEmptyImportedMusicLibrary() {
  return {
    schemaVersion: IMPORTED_MUSIC_SCHEMA_VERSION,
    tracks: {},
    artists: {},
    albums: {},
    playlists: {},
    imports: [],
  };
}

export function createImportRecord({
  source = MUSIC_IMPORT_SOURCES.GENERIC_JSON,
  fileName = "",
  trackCount = 0,
  artistCount = 0,
  albumCount = 0,
  playlistCount = 0,
} = {}) {
  return {
    id: `import-${Date.now()}`,
    source,
    fileName,
    importedAt: new Date().toISOString(),
    trackCount,
    artistCount,
    albumCount,
    playlistCount,
  };
}
