export default function AlbumCard({ album }) {
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

        <div className="flex-1 min-w-0">
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
            {album.releaseDate || "Unknown"} • {album.trackCount || "-"} tracks
          </p>
        </div>
      </div>
    </div>
  );
}
