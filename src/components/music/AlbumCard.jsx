function albumTypeLabel(album) {
  const name = album?.name || "";
  const objectType = album?.objectType || "music object";

  if (/live/i.test(name)) {
    return "Live album";
  }

  if (/deluxe|expanded|bonus|anniversary|remaster|edition|version/i.test(name)) {
    return "Edition or variant";
  }

  if (objectType === "albums" || objectType === "library-albums") {
    return "Album";
  }

  return objectType;
}

function genreSignal(album) {
  const genres = (album?.genreNames || [])
    .filter((genre) => genre && genre.toLowerCase() !== "music")
    .slice(0, 2);

  return genres.length ? genres.join(" / ") : "No genre signal";
}

function sourceLabel(album) {
  if (album?.source === "apple_music_recent_played") {
    return "Apple recent-played evidence";
  }

  return album?.source || "Live source evidence";
}

export default function AlbumCard({ album, signal }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-800 dark:bg-slate-950/40">
      <div className="flex items-center gap-4">
        {album.artworkUrl ? (
          <img
            src={album.artworkUrl}
            alt=""
            className="h-20 w-20 shrink-0 rounded-xl object-cover shadow"
          />
        ) : (
          <div className="h-20 w-20 shrink-0 rounded-xl bg-slate-200 dark:bg-slate-800" />
        )}

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-black leading-tight text-slate-900 dark:text-slate-50">
                {album.name}
              </h3>

              <p className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-300">
                {album.artistName}
              </p>
            </div>

            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              #{album.rank}
            </span>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            {album.releaseDate || "Unknown"} · {album.trackCount || "-"} tracks
          </p>

          <div className="mt-4 rounded-lg bg-slate-50 p-2 text-xs text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
            <p>
              <span className="font-bold">Why visible:</span>{" "}
              {sourceLabel(album)}
            </p>
            <p className="mt-1">
              <span className="font-bold">Type:</span>{" "}
              {albumTypeLabel(album)}
            </p>
            <p className="mt-1">
              <span className="font-bold">Genre:</span>{" "}
              {genreSignal(album)}
            </p>
            <p className="mt-1">
              <span className="font-bold">Queue status:</span>{" "}
              {signal?.status || "Not currently prioritized"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
