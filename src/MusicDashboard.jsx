import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://localhost:4000";

const PERIODS = ["1D", "7D", "30D", "90D"];

const DONUT_COLORS = [
  "#8b5cf6",
  "#22c55e",
  "#38bdf8",
  "#f59e0b",
  "#64748b",
];

function formatTimestamp(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatNumber(value) {
  const numeric = Number(value);

  if (!Number.isFinite(numeric)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US").format(numeric);
}

function objectLabel(value) {
  const numeric = Number(value) || 0;
  return `${formatNumber(numeric)} object${numeric === 1 ? "" : "s"}`;
}

function cleanAlbumContext(value) {
  return String(value || "").replace(/^Recent album context:\s*/i, "");
}

function buildHeadline(dashboard) {
  const topSignal = dashboard?.relationshipActivity?.[0];

  if (!topSignal?.artist) {
    return "Current Apple evidence is available for review.";
  }

  const why = topSignal.whyItMatters || "Current listening signal.";

  return `${topSignal.artist} leads the current signal. ${why}`;
}

function buildDonutGradient(items) {
  const usable = items
    .map((item, index) => ({
      ...item,
      count: Math.max(0, Number(item.count) || 0),
      color: DONUT_COLORS[index % DONUT_COLORS.length],
    }))
    .filter((item) => item.count > 0);

  const total = usable.reduce((sum, item) => sum + item.count, 0);

  if (!total) {
    return {
      gradient: "conic-gradient(#334155 0deg 360deg)",
      items: usable,
      total: 0,
    };
  }

  let cursor = 0;

  const segments = usable.map((item) => {
    const start = cursor;
    const degrees = (item.count / total) * 360;
    cursor += degrees;

    return `${item.color} ${start}deg ${cursor}deg`;
  });

  return {
    gradient: `conic-gradient(${segments.join(", ")})`,
    items: usable,
    total,
  };
}

function EvidenceChip({ children, tone = "violet" }) {
  const tones = {
    violet:
      "border-violet-500/30 bg-violet-500/10 text-violet-200",
    green:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
    slate:
      "border-slate-700 bg-slate-900/80 text-slate-300",
  };

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.16em] ${
        tones[tone] || tones.slate
      }`}
    >
      {children}
    </span>
  );
}

function CockpitCard({
  title,
  eyebrow,
  children,
  className = "",
  action = null,
}) {
  return (
    <section
      className={`rounded-2xl border border-slate-800 bg-slate-950/70 shadow-sm ${className}`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-5 py-4">
        <div>
          {eyebrow ? (
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-violet-300">
              {eyebrow}
            </p>
          ) : null}
          <h3 className="mt-1 text-base font-black text-white">
            {title}
          </h3>
        </div>
        {action}
      </div>

      <div className="p-5">{children}</div>
    </section>
  );
}

function MetricCard({ label, value, note, accent = false }) {
  return (
    <div
      className={`rounded-2xl border p-4 ${
        accent
          ? "border-violet-500/40 bg-violet-500/10"
          : "border-slate-800 bg-slate-950/70"
      }`}
    >
      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">
        {label}
      </p>

      <p
        className={`mt-2 text-4xl font-black tracking-tight ${
          accent ? "text-violet-200" : "text-white"
        }`}
      >
        {value}
      </p>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        {note}
      </p>
    </div>
  );
}

export default function MusicDashboard({ onOpenArtist }) {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  function loadDashboard(refresh = false) {
    setError("");

    if (refresh) {
      setIsRefreshing(true);
    }

    const url = refresh
      ? `${API_BASE}/api/music/dashboard/refresh`
      : `${API_BASE}/api/music/dashboard`;

    return fetch(url, {
      method: refresh ? "POST" : "GET",
    })
      .then(async (response) => {
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(
            payload?.error || "Failed to load Music Intelligence."
          );
        }

        return payload?.dashboard ?? payload;
      })
      .then((payload) => {
        setDashboard(payload);
      })
      .catch((loadError) => {
        setError(loadError.message || "Failed to load Music Intelligence.");
      })
      .finally(() => {
        setIsRefreshing(false);
      });
  }

  useEffect(() => {
    loadDashboard(false);
  }, []);

  const derived = useMemo(() => {
    if (!dashboard) {
      return null;
    }

    const summary = dashboard.liveSummary || {};
    const relationships = dashboard.relationshipActivity || [];
    const albums = dashboard.recentAlbums || [];
    const artists = dashboard.recentArtists || [];
    const changes = dashboard.whatsChanged || {};

    const relationshipByArtist = new Map(
      relationships.map((item) => [item.artist, item])
    );

    const enrichedArtists = artists.map((item) => ({
      ...item,
      signal: relationshipByArtist.get(item.artist),
    }));

    const leadSignal = relationships[0] || null;

    const leadAlbum =
      albums.find(
        (album) =>
          leadSignal?.artist &&
          album.artistName === leadSignal.artist
      ) ||
      albums[0] ||
      null;

    const donut = buildDonutGradient(
      artists.slice(0, 5)
    );

    return {
      summary,
      relationships,
      albums,
      artists,
      changes,
      enrichedArtists,
      leadSignal,
      leadAlbum,
      donut,
    };
  }, [dashboard]);

  if (error) {
    return (
      <section className="rounded-2xl border border-red-900 bg-red-950/40 p-5 text-sm text-red-200">
        <p className="font-black">Music Intelligence could not load.</p>
        <p className="mt-2">{error}</p>
        <button
          type="button"
          onClick={() => loadDashboard(false)}
          className="mt-4 rounded-xl border border-red-700 px-4 py-2 font-bold hover:bg-red-900/50"
        >
          Try again
        </button>
      </section>
    );
  }

  if (!dashboard || !derived) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5 text-sm text-slate-300">
        Loading Music Intelligence...
      </section>
    );
  }

  const {
    summary,
    relationships,
    albums,
    artists,
    changes,
    enrichedArtists,
    leadSignal,
    leadAlbum,
    donut,
  } = derived;

  const newArtists = changes.newArtists || [];
  const departedArtists = changes.departedArtists || [];
  const changedArtists = changes.changedArtists || [];
  const movementCount =
    newArtists.length +
    departedArtists.length +
    changedArtists.length;

  return (
    <section className="mx-auto w-full max-w-[1500px] space-y-7 pb-12">
      <header className="overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-950 to-violet-950/30">
        <div className="flex flex-col gap-6 px-7 py-7 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-4xl">
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-violet-300">
              Music Intelligence
            </p>

            <h2 className="mt-3 text-4xl font-black tracking-tight text-white md:text-5xl">
              Current Listening Cockpit
            </h2>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Current Apple evidence, movement, concentration, and the
              strongest signals worth investigating.
            </p>
          </div>

          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex flex-wrap items-center gap-2">
              {PERIODS.map((period) => (
                <button
                  key={period}
                  type="button"
                  disabled
                  title="Rolling-period query wiring is the next implementation slice."
                  className="cursor-not-allowed rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-black text-slate-600"
                >
                  {period}
                </button>
              ))}

              <span className="rounded-lg border border-violet-500/40 bg-violet-500/15 px-3 py-2 text-xs font-black text-violet-200">
                CURRENT
              </span>

              <button
                type="button"
                onClick={() => loadDashboard(true)}
                disabled={isRefreshing}
                className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-black text-slate-200 transition hover:border-violet-500 hover:text-white disabled:cursor-wait disabled:opacity-60"
              >
                {isRefreshing ? "Refreshing…" : "Refresh"}
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Snapshot {dashboard.snapshotId || "—"} ·{" "}
              {formatTimestamp(dashboard.capturedAt)}
            </p>
          </div>
        </div>
      </header>

      <CockpitCard
        eyebrow="Current read"
        title="What matters now"
        className="border-violet-500/20 bg-gradient-to-r from-violet-950/25 via-slate-950 to-slate-950"
        action={<EvidenceChip>Recent Apple</EvidenceChip>}
      >
        <p className="max-w-5xl text-2xl font-black leading-tight tracking-tight text-white md:text-3xl">
          {buildHeadline(dashboard)}
        </p>

        {changes.headline ? (
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {changes.headline}
          </p>
        ) : null}

        <div className="mt-5 flex flex-wrap gap-2">
          <EvidenceChip>Current snapshot</EvidenceChip>
          <EvidenceChip tone="green">Snapshot delta</EvidenceChip>
          <EvidenceChip tone="slate">No inferred plays</EvidenceChip>
        </div>
      </CockpitCard>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Recent objects"
          value={formatNumber(summary.recentObjectCount)}
          note="Apple objects observed in the current evidence."
          accent
        />

        <MetricCard
          label="Heavy rotation"
          value={formatNumber(summary.heavyRotationCount)}
          note="Objects currently surfaced by Heavy Rotation."
        />

        <MetricCard
          label="Artists surfaced"
          value={formatNumber(artists.length)}
          note="Distinct artists in the current dashboard signal."
        />

        <MetricCard
          label="Albums surfaced"
          value={formatNumber(albums.length)}
          note="Recent album evidence currently retained."
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
        <CockpitCard
          title="Top Artist"
          eyebrow="Current signal"
          className={
            movementCount === 0
              ? "xl:col-span-9"
              : "xl:col-span-7"
          }
          action={<EvidenceChip>Recent Apple</EvidenceChip>}
        >
          {leadSignal ? (
            <div className="grid gap-6 md:grid-cols-[260px_1fr]">
              <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
                {leadAlbum?.artworkUrl ? (
                  <img
                    src={leadAlbum.artworkUrl}
                    alt={`${leadAlbum.name} artwork`}
                    className="aspect-square h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex aspect-square items-center justify-center p-6 text-center text-sm font-bold text-slate-500">
                    Artwork unavailable
                  </div>
                )}

                <div className="absolute inset-x-0 bottom-0 bg-slate-950/85 px-3 py-2 backdrop-blur-sm">
                  <p className="text-[9px] font-black uppercase tracking-[0.18em] text-violet-300">
                    Album context
                  </p>
                  <p className="mt-0.5 truncate text-xs font-bold text-white">
                    {leadAlbum?.name || "Current album evidence"}
                  </p>
                </div>
              </div>

              <div className="flex flex-col justify-between">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.2em] text-violet-300">
                    #1 current artist signal
                  </p>

                  <button
                    type="button"
                    onClick={() => onOpenArtist?.(leadSignal.artist)}
                    className="mt-2 text-left text-4xl font-black tracking-tight text-white transition hover:text-violet-300"
                  >
                    {leadSignal.artist}
                  </button>

                  <p className="mt-3 text-sm leading-6 text-slate-300">
                    {leadSignal.whyItMatters}
                  </p>

                  {leadSignal.context ? (
                    <p className="mt-3 text-sm leading-6 text-slate-500">
                      {cleanAlbumContext(leadSignal.context)}
                    </p>
                  ) : null}
                </div>

                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <span className="text-sm font-black text-white">
                    {objectLabel(leadSignal.recentObjectCount)}
                  </span>

                  <EvidenceChip tone="green">
                    {leadSignal.priority || "Current signal"}
                  </EvidenceChip>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              No current artist signal is available.
            </p>
          )}

          <div className="mt-6 divide-y divide-slate-800 border-t border-slate-800">
            {enrichedArtists.slice(1, 5).map((item, index) => (
              <button
                key={item.artist}
                type="button"
                onClick={() => onOpenArtist?.(item.artist)}
                className="grid w-full grid-cols-[32px_1fr_auto] items-center gap-3 py-3 text-left transition hover:text-violet-300"
              >
                <span className="text-xs font-black text-slate-600">
                  {String(index + 2).padStart(2, "0")}
                </span>

                <div>
                  <p className="font-black text-white">
                    {item.artist}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {item.signal?.whyItMatters ||
                      "Current Apple evidence."}
                  </p>
                </div>

                <span className="text-xs font-black text-slate-400">
                  {objectLabel(
                    item.signal?.recentObjectCount ?? item.count
                  )}
                </span>
              </button>
            ))}
          </div>
        </CockpitCard>

        <CockpitCard
          title="What Changed"
          eyebrow="Vs previous snapshot"
          className={
            movementCount === 0
              ? "self-start xl:col-span-3"
              : "xl:col-span-5"
          }
          action={<EvidenceChip tone="green">Observed delta</EvidenceChip>}
        >
          <p className="text-sm leading-6 text-slate-300">
            {changes.headline ||
              "Refresh comparison has not been calculated yet."}
          </p>

          <div className={movementCount === 0 ? "hidden" : "mt-5 grid grid-cols-3 gap-3"}>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
              <p className="text-[10px] font-black uppercase tracking-[0.15em] text-emerald-300">
                New
              </p>
              <p className="mt-2 text-2xl font-black text-white">
                {newArtists.length}
              </p>
            </div>

            <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-3">
              <p className="text-[10px] font-black uppercase tracking-[0.15em] text-violet-300">
                Changed
              </p>
              <p className="mt-2 text-2xl font-black text-white">
                {changedArtists.length}
              </p>
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-3">
              <p className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">
                Departed
              </p>
              <p className="mt-2 text-2xl font-black text-white">
                {departedArtists.length}
              </p>
            </div>
          </div>

          <div className={movementCount === 0 ? "hidden" : "mt-5 space-y-3"}>
            {newArtists.slice(0, 2).map((item) => (
              <div
                key={`new-${item.artist}`}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-3"
              >
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.16em] text-emerald-300">
                    Appeared
                  </p>
                  <p className="mt-1 font-black text-white">
                    {item.artist}
                  </p>
                </div>
                <span className="text-sm font-black text-slate-400">
                  {item.currentCount ?? "—"}
                </span>
              </div>
            ))}

            {changedArtists.slice(0, 2).map((item) => (
              <div
                key={`changed-${item.artist}`}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-3"
              >
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.16em] text-violet-300">
                    Changed
                  </p>
                  <p className="mt-1 font-black text-white">
                    {item.artist}
                  </p>
                </div>
                <span className="text-sm font-black text-slate-300">
                  {item.previousCount} → {item.currentCount}
                </span>
              </div>
            ))}

            {departedArtists.slice(0, 2).map((item) => (
              <div
                key={`departed-${item.artist}`}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/50 px-3 py-3"
              >
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-500">
                    No longer visible
                  </p>
                  <p className="mt-1 font-black text-white">
                    {item.artist}
                  </p>
                </div>
                <span className="text-sm font-black text-slate-500">
                  {item.previousCount ?? "—"}
                </span>
              </div>
            ))}
          </div>

          {changes.note ? (
            <p className="mt-5 text-xs leading-5 text-slate-600">
              {changes.note}
            </p>
          ) : null}
        </CockpitCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
        <CockpitCard
          title="Top Albums"
          eyebrow="Artwork-led current evidence"
          className="xl:col-span-8"
          action={<EvidenceChip>Recent Apple</EvidenceChip>}
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {albums.slice(0, 5).map((album) => (
              <article key={`${album.appleId}-${album.displayRank}`}>
                <div
                  className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900"
                  style={
                    album.artworkBgColor
                      ? {
                          backgroundColor: `#${album.artworkBgColor}`,
                        }
                      : undefined
                  }
                >
                  {album.artworkUrl ? (
                    <img
                      src={album.artworkUrl}
                      alt={`${album.name} artwork`}
                      className="aspect-square w-full object-cover"
                    />
                  ) : (
                    <div className="flex aspect-square items-center justify-center p-4 text-center text-xs text-slate-500">
                      Artwork unavailable
                    </div>
                  )}
                </div>

                <p className="mt-3 line-clamp-2 text-sm font-black leading-5 text-white">
                  {album.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {album.artistName}
                </p>
              </article>
            ))}
          </div>
        </CockpitCard>

        <CockpitCard
          title="Listening Shape"
          eyebrow="Current evidence concentration"
          className="xl:col-span-4"
          action={<EvidenceChip tone="slate">Composition</EvidenceChip>}
        >
          <div className="grid gap-5 sm:grid-cols-[150px_1fr] xl:grid-cols-1 2xl:grid-cols-[150px_1fr]">
            <div className="relative mx-auto h-36 w-36">
              <div
                className="absolute inset-0 rounded-full"
                style={{ background: donut.gradient }}
              />

              <div className="absolute inset-6 flex items-center justify-center rounded-full border border-slate-800 bg-slate-950">
                <div className="text-center">
                  <p className="text-2xl font-black text-white">
                    {formatNumber(donut.total)}
                  </p>
                  <p className="text-[9px] font-black uppercase tracking-[0.14em] text-slate-500">
                    Evidence
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {donut.items.map((item) => {
                const share = donut.total
                  ? Math.round((item.count / donut.total) * 100)
                  : 0;

                return (
                  <div
                    key={item.artist}
                    className="flex items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="truncate font-bold text-slate-300">
                        {item.artist}
                      </span>
                    </div>

                    <span className="font-black text-white">
                      {share}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="mt-5 text-xs leading-5 text-slate-500">
            Share of current Apple evidence across the leading surfaced
            artists. This is composition evidence, not play share.
          </p>
        </CockpitCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
        <CockpitCard
          title="Worth Investigating"
          eyebrow="Next questions"
          className="xl:col-span-8"
        >
          <div className="grid gap-3 md:grid-cols-2">
            {relationships.slice(0, 4).map((item) => (
              <button
                key={item.artist}
                type="button"
                onClick={() => onOpenArtist?.(item.artist)}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-left transition hover:border-violet-500/50 hover:bg-violet-500/5"
              >
                <p className="text-xs font-black uppercase tracking-[0.14em] text-violet-300">
                  {item.artist}
                </p>

                <p className="mt-2 text-sm font-bold leading-6 text-white">
                  {item.investigationHint ||
                    item.whyItMatters ||
                    "Compare current signal with historical evidence."}
                </p>

                <p className="mt-3 text-xs text-slate-500">
                  {item.nextStep || "Open Artist Intelligence"}
                </p>
              </button>
            ))}
          </div>
        </CockpitCard>

        <CockpitCard
          title="Evidence"
          eyebrow="Coverage"
          className="xl:col-span-4"
        >
          <div className="space-y-3">
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
              <p className="text-xs font-black text-emerald-200">
                Recent Apple
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Current Apple objects and artist/album signals.
              </p>
            </div>

            <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-3">
              <p className="text-xs font-black text-violet-200">
                Heavy Rotation
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Current rotation evidence retained separately from plays.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
              <p className="text-xs font-black text-slate-300">
                Snapshot movement
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Appearance, departure, and count changes between usable
                captures.
              </p>
            </div>
          </div>

          <p className="mt-4 text-xs leading-5 text-slate-600">
            {dashboard.sourceNote ||
              "Current evidence remains source-specific and is not conflated with confirmed play history."}
          </p>
        </CockpitCard>
      </div>
    </section>
  );
}