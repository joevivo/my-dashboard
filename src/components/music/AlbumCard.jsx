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
    <div className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-xl dark:border-slate-800 dark:bg-slate-950/50 dark:hover:border-blue-800">
      <div className="relative bg-slate-100 dark:bg-slate-900">
        {album.artworkUrl ? (
          <img
            src={album.artworkUrl}
            alt=""
            className="aspect-square w-full object-cover"
          />
        ) : (
          <div className="aspect-square w-full bg-slate-200 dark:bg-slate-800" />
        )}

        <div className="absolute left-3 top-3 rounded-full bg-slate-950/80 px-3 py-1 text-xs font-black text-white shadow">
          Current #{album.displayRank || album.rank}
        </div>

        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/85 to-transparent p-4">
          <p className="truncate text-sm font-black text-white">
            {album.artistName}
          </p>
          <p className="mt-1 text-xs font-semibold text-slate-200">
            {album.evidenceCount > 1 ? `${album.evidenceCount} live evidence objects` : sourceLabel(album)}
          </p>
        </div>
      </div>

      <div className="space-y-4 p-4">
        <div>
          <h3 className="line-clamp-2 text-lg font-black leading-tight tracking-tight text-slate-950 dark:text-slate-50">
            {album.name}
          </h3>

          <p className="mt-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            {album.releaseDate || "Unknown"} / {album.trackCount || "-"} tracks
          </p>
        </div>

        <div className="grid gap-2 text-xs">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900/60">
            <p className="font-black uppercase tracking-[0.12em] text-slate-500">
              Type
            </p>
            <p className="mt-1 font-bold text-slate-800 dark:text-slate-200">
              {albumTypeLabel(album)}
            </p>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900/60">
            <p className="font-black uppercase tracking-[0.12em] text-slate-500">
              Genre
            </p>
            <p className="mt-1 font-bold text-slate-800 dark:text-slate-200">
              {genreSignal(album)}
            </p>
          </div>

          <div className="rounded-xl border border-blue-100 bg-blue-50 p-3 dark:border-blue-900/60 dark:bg-blue-950/30">
            <p className="font-black uppercase tracking-[0.12em] text-blue-700 dark:text-blue-300">
              Queue status
            </p>
            <p className="mt-1 font-bold text-slate-800 dark:text-slate-200">
              {signal?.status || "Not currently prioritized"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
