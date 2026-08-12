import React, { useEffect, useMemo, useState } from "react";

function humanize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClasses(status) {
  const normalized = String(status || "").toUpperCase();

  if (
    normalized === "AVAILABLE" ||
    normalized === "IMMUTABLE_PRE_SERIES"
  ) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300";
  }

  if (
    normalized === "PARTIAL" ||
    normalized.includes("HISTORICAL") ||
    normalized.includes("RECONSTRUCTION")
  ) {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300";
  }

  return "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400";
}

function Pill({ children, status }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${statusClasses(
        status
      )}`}
    >
      {children}
    </span>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
        {value ?? "—"}
      </p>
    </div>
  );
}

function formatRecord(profile) {
  const wins = profile?.record?.wins;
  const losses = profile?.record?.losses;

  if (wins == null || losses == null) return "—";

  return `${wins}-${losses}`;
}

function PlayerList({ title, rows, metric, digits = 3 }) {
  const safeRows = Array.isArray(rows) ? rows.slice(0, 3) : [];

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
        {title}
      </p>

      {safeRows.length ? (
        <div className="mt-2 space-y-2">
          {safeRows.map((row, index) => {
            const value = Number(row?.[metric]);

            return (
              <div
                key={`${row?.playerName || row?.name || "player"}-${index}`}
                className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-950/50"
              >
                <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {row?.playerName || row?.name || "Unknown player"}
                </span>
                <span className="text-sm font-bold tabular-nums text-slate-600 dark:text-slate-300">
                  {Number.isFinite(value) ? value.toFixed(digits) : "—"}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-400">Evidence gated</p>
      )}
    </div>
  );
}

function GatedModule({ title, status = "EVIDENCE_GATED", detail }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/30">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-bold text-slate-700 dark:text-slate-300">
          {title}
        </p>
        <Pill status={status}>{humanize(status)}</Pill>
      </div>
      {detail ? (
        <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
          {detail}
        </p>
      ) : null}
    </div>
  );
}

export default function SeriesPreview({
  selection,
  onBack,
  apiBase = "http://localhost:4000",
}) {
  const [series, setSeries] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const requestUrl = useMemo(() => {
    if (
      !selection?.leagueId ||
      !selection?.teamId ||
      !selection?.seriesId
    ) {
      return null;
    }

    return (
      `${apiBase}/api/strat/league/${selection.leagueId}` +
      `/team/${selection.teamId}/series/` +
      encodeURIComponent(selection.seriesId)
    );
  }, [apiBase, selection]);

  useEffect(() => {
    if (!requestUrl) {
      setSeries(null);
      setStatus("idle");
      return;
    }

    let cancelled = false;

    const load = async () => {
      setStatus("loading");
      setError("");

      try {
        const response = await fetch(requestUrl);

        if (!response.ok) {
          throw new Error(
            `Series Preview request failed (${response.status})`
          );
        }

        const payload = await response.json();

        if (!cancelled) {
          setSeries(payload);
          setStatus("ready");
        }
      } catch (requestError) {
        if (!cancelled) {
          setSeries(null);
          setStatus("error");
          setError(requestError?.message || String(requestError));
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [requestUrl]);

  if (!selection) {
    return (
      <div className="p-6">
        <GatedModule
          title="Series Preview"
          status="EVIDENCE_GATED"
          detail="No canonical BIE series has been selected."
        />
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="p-6 text-sm font-semibold text-slate-500">
        Loading Series Preview…
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="p-6">
        <GatedModule
          title="Series Preview unavailable"
          status="EVIDENCE_GATED"
          detail={error}
        />
      </div>
    );
  }

  if (!series) return null;

  const identity = series.seriesIdentity || {};
  const lifecycle = series.lifecycle || {};
  const snapshot = series.preSeriesSnapshot || {};
  const payload = snapshot.payload || null;

  const canonicalOpponentDisplayName =
    identity.opponentDisplayName || "Opponent";

  const opponentDisplayName =
    selection?.opponentDisplayName ||
    canonicalOpponentDisplayName;

  const displayOutlookSynopsis =
    payload?.executiveOutlook?.synopsis &&
    canonicalOpponentDisplayName !== opponentDisplayName
      ? payload.executiveOutlook.synopsis.replace(
          canonicalOpponentDisplayName,
          opponentDisplayName
        )
      : payload?.executiveOutlook?.synopsis;

  const outlook = payload?.executiveOutlook || null;
  const leagueContext = payload?.leagueContext || null;
  const playerIntelligence = payload?.playerIntelligence || null;

  const teamProfile = leagueContext?.teamProfile || null;
  const opponentProfile = leagueContext?.opponentProfile || null;

  const teamPlayers = playerIntelligence?.team || {};
  const opponentPlayers = playerIntelligence?.opponent || {};

  const missingEvidence = Array.isArray(snapshot.missingEvidence)
    ? snapshot.missingEvidence
    : [];

  const replayGames = Array.isArray(series?.replay?.games)
    ? series.replay.games
    : [];

  const historicalOnly =
    snapshot.snapshotClassification ===
    "HISTORICAL_RECONSTRUCTION_NOT_CERTIFIED";

  return (
    <div className="space-y-6 p-4 sm:p-6">
      <header className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            {onBack ? (
              <button
                type="button"
                onClick={onBack}
                className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-blue-600 hover:text-blue-500"
              >
                ← Active Teams
              </button>
            ) : null}

            <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
              BIE Series Preview
            </p>

            <h1 className="mt-1 text-2xl font-black text-slate-950 dark:text-white">
              Aquarium Drinkers vs.{" "}
              {opponentDisplayName}
            </h1>

            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {identity.homeAway || "Venue TBD"} ·{" "}
              {identity.scheduledDate || "Date TBD"} ·{" "}
              {identity.gameCount || replayGames.length || "—"} games
            </p>
          </div>

          <div className="flex flex-wrap gap-4">
            <div>
              <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                Snapshot
              </p>
              <Pill status={snapshot.snapshotClassification}>
                {humanize(snapshot.snapshotClassification)}
              </Pill>
            </div>

            <div>
              <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                Lifecycle
              </p>
              <Pill status={lifecycle.stage}>
                {humanize(lifecycle.stage)}
              </Pill>
            </div>
          </div>
        </div>

        <p className="mt-4 break-all text-[10px] text-slate-400">
          {identity.seriesId}
        </p>
      </header>

      {historicalOnly ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-900/50 dark:bg-amber-950/30">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-amber-700 dark:text-amber-300">
            Historical reconstruction
          </p>
          <p className="mt-2 text-sm leading-6 text-amber-900 dark:text-amber-100">
            {snapshot.warning ||
              "This series does not have a certified immutable pre-series snapshot. BIE will not present reconstructed evidence as though it were known before Game 1."}
          </p>
        </section>
      ) : null}

      {outlook ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                Series Outlook
              </p>
              <h2 className="mt-1 text-xl font-black text-slate-950 dark:text-white">
                {humanize(outlook.classification)}
              </h2>
            </div>

            <Pill status={outlook.status}>
              {humanize(outlook.confidence || outlook.status)}
            </Pill>
          </div>

          <p className="mt-4 max-w-4xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            {displayOutlookSynopsis}
          </p>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {outlook.hot?.text ? (
              <Metric label="Hot" value={outlook.hot.text} />
            ) : null}
            <Metric label="Edge" value={outlook.edge?.text || "Evidence gated"} />
            <Metric label="Watch" value={outlook.watch?.text || "Evidence gated"} />
          </div>
        </section>
      ) : null}

      {leagueContext?.status === "AVAILABLE" ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
            Team vs. Opponent
          </p>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {[
              ["Aquarium Drinkers", teamProfile],
              [opponentDisplayName, opponentProfile],
            ].map(([name, profile]) => (
              <div
                key={name}
                className="rounded-xl border border-slate-200 p-4 dark:border-slate-800"
              >
                <h3 className="font-black text-slate-900 dark:text-white">
                  {name}
                </h3>

                <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <Metric label="Record" value={formatRecord(profile)} />
                  <Metric
                    label="Run Diff"
                    value={profile?.runDifferential ?? "—"}
                  />
                  <Metric
                    label="OPS"
                    value={
                      profile?.offense?.ops != null
                        ? Number(profile.offense.ops).toFixed(3)
                        : "—"
                    }
                  />
                  <Metric
                    label="ERA"
                    value={
                      profile?.pitching?.era != null
                        ? Number(profile.pitching.era).toFixed(2)
                        : "—"
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {playerIntelligence?.status === "AVAILABLE" ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
            Key Players
          </p>

          <div className="mt-4 grid gap-6 lg:grid-cols-2">
            <div className="space-y-5">
              <h3 className="font-black text-slate-900 dark:text-white">
                Aquarium Drinkers
              </h3>
              <PlayerList
                title="Top Hitters · OPS"
                rows={teamPlayers.topHittersByOPS}
                metric="OPS"
              />
              <PlayerList
                title="Top Pitchers · ERA"
                rows={teamPlayers.topPitchersByERA}
                metric="ERA"
                digits={2}
              />
            </div>

            <div className="space-y-5">
              <h3 className="font-black text-slate-900 dark:text-white">
                {opponentDisplayName}
              </h3>
              <PlayerList
                title="Top Hitters · OPS"
                rows={opponentPlayers.topHittersByOPS}
                metric="OPS"
              />
              <PlayerList
                title="Top Pitchers · ERA"
                rows={opponentPlayers.topPitchersByERA}
                metric="ERA"
                digits={2}
              />
            </div>
          </div>
        </section>
      ) : null}

      <section>
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
          Matchup Detail
        </p>

        <div className="grid gap-3 md:grid-cols-2">
          <GatedModule
            title="Pitching Matchup"
            detail="Probable starters, bullpen availability, and workload remain evidence gated until captured."
          />
          <GatedModule
            title="Lineup Matchups"
            detail="Projected lineups, platoon edges, and card-split matchups remain evidence gated."
          />
          <GatedModule
            title="Availability & Environment"
            status="NOT_CAPTURED"
            detail="Injuries, roster constraints, and park effects are not yet captured in the canonical series artifact."
          />
          <GatedModule
            title="Manager's Notebook"
            detail="Managerial recommendations will appear only when they are traceable to supporting evidence."
          />
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
              Spoiler-Free Replay
            </p>
            <h2 className="mt-1 text-lg font-black text-slate-950 dark:text-white">
              Series progression
            </h2>
          </div>

          <Pill status={series?.replay?.status}>
            {humanize(series?.replay?.status)}
          </Pill>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {replayGames.map((game) => (
            <div
              key={`${identity.seriesId}-${game.ordinal}`}
              className="rounded-xl border border-slate-200 p-4 dark:border-slate-800"
            >
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
                Game {game.ordinal}
              </p>
              <p className="mt-1 text-sm font-bold text-slate-800 dark:text-slate-200">
                Schedule #{game.scheduleGameNumber}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                {humanize(game.evidenceStatus)}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-4 text-xs leading-5 text-slate-400">
          Scores, winners, updated records, series outcomes, and future-game
          information remain hidden until deliberately revealed.
        </p>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
          Evidence & Snapshot Integrity
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          <Pill status={series?.evidence?.status}>
            Artifact Evidence {humanize(series?.evidence?.status)}
          </Pill>
          <Pill status={snapshot.status}>
            Snapshot Integrity {humanize(snapshot.status)}
          </Pill>
        </div>

        {missingEvidence.length ? (
          <div className="mt-4">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
              Snapshot certification gaps
            </p>
            <ul className="mt-2 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              {missingEvidence.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Pre-series snapshot integrity is intact. Baseball intelligence
            remains evidence gated wherever supporting data has not yet been
            captured.
          </p>
        )}
      </section>

      <footer className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center text-xs font-semibold text-slate-500 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-400">
        Preview → Spoiler-Free Replay → Series Review → Learning
      </footer>
    </div>
  );
}
