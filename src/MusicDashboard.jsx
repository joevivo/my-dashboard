import { useEffect, useMemo, useState } from "react";
import DashboardCard from "./components/music/DashboardCard";
import { Activity, Disc3, ListMusic, Radio, Users } from "lucide-react";
import { musicTheme } from "./components/music/musicTheme";
import MusicBadge from "./components/music/MusicBadge";
import AlbumCard from "./components/music/AlbumCard";

const API_BASE = "http://localhost:4000";

function formatTimestamp(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

function objectLabel(count) {
  return `${count} object${count === 1 ? "" : "s"}`;
}

function artistSummary(item) {
  return `${item.artist} appears in the latest Apple Music snapshot.`;
}
function getStoryArtist(dashboard) {
  const relationships = dashboard?.relationshipActivity || [];
  return relationships[0]?.artist || "Your listening";
}

function getStoryText(dashboard) {
  const topSignal = dashboard?.relationshipActivity?.[0];

  if (!topSignal?.artist) {
    return "Current Apple live evidence is ready for investigation.";
  }

  const objectCount = objectLabel(topSignal.recentObjectCount ?? 0);
  const why = (topSignal.whyItMatters || "Current listening signal.")
    .replace(/\.$/, "")
    .toLowerCase();

  return `${topSignal.artist} leads this snapshot: ${why} across ${objectCount}.`;
}


export default function MusicDashboard({ onOpenArtist }) {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  function loadDashboard({ refresh = false } = {}) {
    const url = refresh
      ? `${API_BASE}/api/music/dashboard/refresh`
      : `${API_BASE}/api/music/dashboard`;

    if (refresh) {
      setIsRefreshing(true);
    }

    return fetch(url, { method: refresh ? "POST" : "GET" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            refresh
              ? "Music Dashboard refresh failed."
              : "Music Dashboard failed to load."
          );
        }
        return response.json();
      })
      .then((data) => {
        setDashboard(refresh ? data.dashboard : data);
        setError("");
      })
      .catch((err) =>
        setError(
          err.message ||
            (refresh
              ? "Music Dashboard refresh failed."
              : "Music Dashboard failed to load.")
        )
      )
      .finally(() => {
        if (refresh) {
          setIsRefreshing(false);
        }
      });
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const listeningEnvironment = useMemo(() => {
    const playlists = dashboard?.playlistsAndStations?.playlists || [];
    const stations = dashboard?.playlistsAndStations?.stations || [];
    return { playlists, stations };
  }, [dashboard]);

  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
        {error}
      </section>
    );
  }

  if (!dashboard) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-300">
        Loading Music Dashboard...
      </section>
    );
  }

  const summary = dashboard.liveSummary || {};
  const relationships = dashboard.relationshipActivity || [];
  const albums = dashboard.recentAlbums || [];
  const artists = dashboard.recentArtists || [];
  const relationshipByArtist = new Map(
    relationships.map((item) => [item.artist, item])
  );
  const enrichedArtists = artists.map((item) => ({
    ...item,
    signal: relationshipByArtist.get(item.artist),
  }));

  return (
    <section className="space-y-6">
      <div className="overflow-hidden rounded-[2rem] border border-slate-800 bg-slate-950 text-white shadow-2xl">
        <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6 md:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.22em] text-blue-300">
                Music Intelligence
              </p>
              <h2 className="mt-3 text-5xl font-black tracking-tight text-white md:text-6xl">
                Music Dashboard
              </h2>
              <p className="mt-3 max-w-4xl text-base leading-7 text-slate-300">
                The dashboard observes the present. The Workbench explains why it matters.
              </p>
            </div>

            <button
              type="button"
              onClick={() => loadDashboard({ refresh: true })}
              disabled={isRefreshing}
              className="rounded-2xl border border-blue-300/50 bg-blue-500 px-5 py-3 text-sm font-black text-white shadow-lg shadow-blue-950/30 transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRefreshing ? "Refreshing..." : "Refresh Live Data"}
            </button>
          </div>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-200">
                Evidence
              </p>
              <p className="mt-2 text-sm font-black text-white">
                Apple live objects
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-300">
                Captured source observations, not complete play-count history.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-200">
                Signal
              </p>
              <p className="mt-2 text-sm font-black text-white">
                Current listening signal
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-300">
                Repeated artist appearances and album context become investigation leads.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-blue-200">
                Investigation
              </p>
              <p className="mt-2 text-sm font-black text-white">
                Workbench comparison
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-300">
                Compare live leads against actual plays, skips, albums, and family identity.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-[2rem] border border-blue-200 bg-gradient-to-br from-blue-50 via-white to-slate-50 p-6 shadow-lg dark:border-blue-900/60 dark:from-blue-950/40 dark:via-slate-950 dark:to-slate-900">
        <div className="flex flex-col gap-5 md:flex-row md:items-start">
          <div className="rounded-2xl bg-blue-600 p-3 text-white shadow-lg shadow-blue-900/20">
            <Activity size={24} />
          </div>
          <div className="min-w-0 flex-1">
            <MusicBadge tone="story">Current Listening Signal</MusicBadge>
            <h3 className="mt-3 max-w-5xl text-3xl font-black tracking-tight text-slate-950 dark:text-slate-50">
              {getStoryText(dashboard)}
            </h3>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
              {summary.recentObjectCount ?? 0} Apple live objects observed · Updated {formatTimestamp(dashboard.capturedAt)}
            </p>
          </div>
        </div>
      </div>

      <DashboardCard title="Source Snapshot">
        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <p className="text-xs text-slate-500">Last Updated</p>
            <p className="mt-1 text-lg font-black text-slate-900 dark:text-slate-50">
              {formatTimestamp(dashboard.capturedAt)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Recent Objects</p>
            <p className="mt-1 text-3xl font-black text-slate-900 dark:text-slate-50">
              {summary.recentObjectCount ?? "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Source Evidence</p>
            <p className="mt-1 text-sm font-black text-slate-900 dark:text-slate-50">
              Apple live APIs
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Opaque Apple classifications are retained as provenance only.
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Snapshot</p>
            <p className="mt-1 text-sm font-black text-slate-900 dark:text-slate-50">
              {dashboard.snapshotId || "-"}
            </p>
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
          {dashboard.sourceNote || "Apple Music live snapshot metadata is available for this dashboard."}
        </p>
      </DashboardCard>

      <div className="grid gap-6 xl:grid-cols-12">
        <DashboardCard title="Investigation Queue" className="xl:col-span-8">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Ranked by current Apple live evidence, repeated artist appearance, and album context. These are leads, not conclusions; open an artist to compare live signal against actual plays, skips, albums, and family identity.
          </p>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {relationships.slice(0, 8).map((item) => (
              <button
                key={item.artist}
                type="button"
                onClick={() => onOpenArtist?.(item.artist)}
                className="group overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg dark:border-slate-800 dark:bg-slate-950/50 dark:hover:border-blue-800"
              >
                <div className="border-b border-slate-100 bg-gradient-to-br from-white to-slate-50 p-4 dark:border-slate-800 dark:from-slate-950 dark:to-slate-900">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-lg font-black tracking-tight text-slate-950 dark:text-slate-50">
                        {item.artist}
                      </p>
                      <p className="mt-1 text-sm font-semibold leading-5 text-slate-700 dark:text-slate-200">
                        {item.whyItMatters || artistSummary(item)}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-col items-end gap-2">
                      <MusicBadge tone="relationship">
                        {item.priority || objectLabel(item.recentObjectCount)}
                      </MusicBadge>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-black text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                        {objectLabel(item.recentObjectCount)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 p-4">
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300">
                    <p>
                      <span className="font-black text-slate-700 dark:text-slate-200">Evidence:</span>{" "}
                      {item.evidence || `${item.recentObjectCount ?? 0} recent Apple live objects.`}
                    </p>
                    {item.context ? (
                      <p className="mt-1">
                        <span className="font-black text-slate-700 dark:text-slate-200">Context:</span>{" "}
                        {item.context.replace("Recent album context: ", "")}
                      </p>
                    ) : null}
                  </div>

                  <div className="flex items-center justify-between text-xs font-black text-blue-700 dark:text-blue-300">
                    <span>{item.nextStep || "Investigate in Workbench"}</span>
                    <span className="transition group-hover:translate-x-1">→</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </DashboardCard>

        <DashboardCard title="Listening Environment" className="xl:col-span-4">
          <div className="space-y-5">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Stations
              </p>
              <div className="mt-3 space-y-2">
                {listeningEnvironment.stations.slice(0, 5).map((item) => (
                  <div key={`${item.appleId}-${item.source}-${item.rank}`} className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="font-black text-slate-900 dark:text-slate-50">{item.name}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.source}</p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Playlists
              </p>
              <div className="mt-3 space-y-2">
                {listeningEnvironment.playlists.slice(0, 6).map((item) => (
                  <div key={`${item.appleId}-${item.source}-${item.rank}`} className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="font-black text-slate-900 dark:text-slate-50">{item.name}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.source}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </DashboardCard>
      </div>

      <DashboardCard title="Recently Active Albums">
        <p className="mb-4 text-sm text-slate-600 dark:text-slate-300">
          Ordered by current artist signal, then Apple live source position. Current rank is this dashboard display order, not all-time plays or a favorite-album ranking.
        </p>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {albums.slice(0, 20).map((album) => (
            <AlbumCard
              key={`${album.appleId}-${album.rank}`}
              album={album}
              signal={relationshipByArtist.get(album.artistName)}
            />
          ))}
        </div>
      </DashboardCard>

      <div className="grid gap-6 xl:grid-cols-12">
        <DashboardCard title="Recently Active Artists" className="xl:col-span-7">
          <div className="grid gap-3 md:grid-cols-2">
            {enrichedArtists.slice(0, 10).map((item) => (
              <button
                key={item.artist}
                type="button"
                onClick={() => onOpenArtist?.(item.artist)}
                className="rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="font-black text-slate-900 dark:text-slate-50">
                    {item.artist}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                    {item.signal?.priority || objectLabel(item.count)}
                  </span>
                </div>

                <p className="mt-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
                  {item.signal?.whyItMatters || "Current Apple live evidence."}
                </p>

                <div className="mt-3 space-y-1 text-xs text-slate-500 dark:text-slate-400">
                  <p>{objectLabel(item.signal?.recentObjectCount ?? item.count)}</p>
                  {item.signal?.context ? (
                    <p>{item.signal.context.replace(/^Recent album context:\s*/i, "Context: ")}</p>
                  ) : null}
                </div>
              </button>
            ))}
          </div>
        </DashboardCard>

        <DashboardCard title="What's Changed" className="xl:col-span-5">
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {dashboard.whatsChanged?.headline || dashboard.whatsChanged?.status || "Snapshot comparison has not been calculated yet."}
          </p>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {dashboard.whatsChanged?.note}
          </p>

          {dashboard.whatsChanged?.previousSnapshotId ? (
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Compared with {dashboard.whatsChanged.previousSnapshotId}
            </p>
          ) : null}

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-900/60">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">New</p>
              <p className="mt-1 text-2xl font-black text-slate-900 dark:text-slate-50">
                {dashboard.whatsChanged?.newArtists?.length ?? 0}
              </p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-900/60">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Changed</p>
              <p className="mt-1 text-2xl font-black text-slate-900 dark:text-slate-50">
                {dashboard.whatsChanged?.changedArtists?.length ?? 0}
              </p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-900/60">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">No Longer Visible</p>
              <p className="mt-1 text-2xl font-black text-slate-900 dark:text-slate-50">
                {dashboard.whatsChanged?.departedArtists?.length ?? 0}
              </p>
            </div>
          </div>

          {dashboard.whatsChanged?.changedArtists?.length ? (
            <div className="mt-4">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                Count Changes
              </p>
              <ul className="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
                {dashboard.whatsChanged.changedArtists.slice(0, 5).map((item) => (
                  <li key={item.artist}>
                    {item.artist}: {item.previousCount} → {item.currentCount}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </DashboardCard>
      </div>
    </section>
  );
}
