function Metric({ label, value, detail }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-100">
        {value ?? "Unavailable"}
      </p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}

function formatEvidenceCount(value) {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  return `${value.toLocaleString()} ${
    value === 1 ? "evidence record" : "evidence records"
  }`;
}

function EvidenceList({ title, items = [], itemField }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <h4 className="font-semibold text-slate-100">{title}</h4>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">
          No matching Library Evidence was returned.
        </p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-slate-300">
          {items.map((item, index) => {
            const label =
              typeof item === "string"
                ? item
                : item?.[itemField] ?? item?.label ?? "Unknown";

            const count =
              typeof item === "string" ? null : item?.count ?? null;

            return (
              <li
                key={`${label}-${index}`}
                className="flex items-center justify-between gap-3"
              >
                <span>{label}</span>

                {count !== null && (
                  <span className="text-xs font-semibold text-sky-300">
                    {formatEvidenceCount(count)}
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default function ArtistDossierModal({
  artist,
  journey,
  onClose,
}) {
  if (!artist) {
    return null;
  }

  const timeline = Array.isArray(journey?.timeline)
    ? journey.timeline
    : [];

  const topAlbums = Array.isArray(journey?.topAlbums)
    ? journey.topAlbums
    : [];

  const topTracks = Array.isArray(journey?.topTracks)
    ? journey.topTracks
    : [];

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
              {journey?.status ?? "Unavailable"}
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

        <section className="mt-5 rounded-2xl border border-sky-500/30 bg-sky-950/20 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-sky-300">
            Library Evidence in Selected Range
          </h3>

          <div className="mt-3">
            <Metric
              label="Evidence Records"
              value={formatEvidenceCount(artist.count)}
              detail="Reconstructed Library Evidence, not confirmed Actual Plays"
            />
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <EvidenceList
              title="Top Albums in Selected Range"
              items={topAlbums}
              itemField="album"
            />

            <EvidenceList
              title="Top Tracks in Selected Range"
              items={topTracks}
              itemField="track"
            />
          </div>
        </section>

        <section className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Library Evidence Journey
          </h3>

          <p className="mt-2 text-sm leading-relaxed text-slate-400">
            These fields come directly from the Period Intelligence backend.
            The interface does not recreate or reinterpret the journey
            classification.
          </p>

          <div className="mt-3 grid gap-3 md:grid-cols-3">
            <Metric
              label="Backend Journey Status"
              value={journey?.status ?? "Unavailable"}
            />

            <Metric
              label="First Seen"
              value={journey?.firstSeen ?? "Unavailable"}
            />

            <Metric
              label="Most Active Period"
              value={journey?.mostActivePeriod ?? "Unavailable"}
            />
          </div>

          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <h4 className="font-semibold text-slate-100">
              Yearly Library Evidence
            </h4>

            {timeline.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">
                No yearly Library Evidence timeline was returned.
              </p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm text-slate-300">
                {timeline.map((item, index) => (
                  <li
                    key={`${item.year}-${index}`}
                    className="flex items-center justify-between gap-3"
                  >
                    <span>{item.year}</span>
                    <span className="text-xs font-semibold text-sky-300">
                      {formatEvidenceCount(item.count)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}