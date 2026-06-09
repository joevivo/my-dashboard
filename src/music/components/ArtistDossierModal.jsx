function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-100">{value ?? "Pending"}</p>
    </div>
  );
}

function normalizeList(items) {
  if (!Array.isArray(items)) return [];

  return items
    .map((item) => {
      if (typeof item === "string") return item;
      return item?.label ?? item?.album ?? item?.playlist ?? item?.name ?? null;
    })
    .filter(Boolean);
}

export default function ArtistDossierModal({ dossier, onClose }) {
  if (!dossier) return null;

  const artist = dossier.artist ?? {};
  const journey = dossier.journey ?? {};
  const timeline = journey.timeline ?? [];

  const years = timeline.map((item) => Number(item.year)).filter(Boolean);
  const firstSeen = journey.firstSeen ?? (years.length ? Math.min(...years) : "Pending");
  const latestActivity = years.length ? Math.max(...years) : "Pending";

  const maxTimelineCount = timeline.length
    ? Math.max(...timeline.map((item) => item.count))
    : 0;

  const peakYears = timeline
    .filter((item) => maxTimelineCount && item.count === maxTimelineCount)
    .map((item) => item.year);

  const peakYear = peakYears.length
    ? peakYears.join(", ")
    : journey.mostActivePeriod ?? "Pending";

  const yearsActive = years.length || "Pending";
  const activityInRange = artist.count ?? 0;
  const totalPlays = journey.totalPlays ?? artist.totalPlays ?? activityInRange;

  const topAlbums = normalizeList(journey.topAlbums ?? artist.topAlbums);
  const playlistAppearances = normalizeList(
    journey.playlistAppearances ?? artist.playlistAppearances ?? artist.playlists
  );

  const journeyType = journey.journeyType ?? artist.journeyType ?? "Pending";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-sky-500/40 bg-slate-950 p-5 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Artist Dossier
            </p>
            <h3 className="mt-1 text-2xl font-bold text-white">
              {artist.label ?? "Unknown Artist"}
            </h3>
            <div className="mt-3 inline-flex rounded-full border border-amber-400/40 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-200">
              {journeyType}
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800"
          >
            Close
          </button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <Metric label="First Seen" value={firstSeen} />
          <Metric label="Peak Year" value={peakYear} />
          <Metric label="Latest Activity" value={latestActivity} />
          <Metric label="Years Active" value={yearsActive} />
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <Metric
            label="Activity in Range"
            value={`${activityInRange} ${activityInRange === 1 ? "play" : "plays"}`}
          />
          <Metric label="Total Plays" value={totalPlays} />
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h4 className="font-semibold text-slate-100">Top Albums</h4>
            {topAlbums.length ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-300">
                {topAlbums.map((album) => (
                  <li key={album}>{album}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Pending</p>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h4 className="font-semibold text-slate-100">
              Playlist Appearances
            </h4>
            {playlistAppearances.length ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-300">
                {playlistAppearances.map((playlist) => (
                  <li key={playlist}>{playlist}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Pending</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
