import frozenFieldingIntelligence from "./strat/frozenFieldingIntelligence.pre10pm.json";
import FrozenDefensePanel from "./strat/FrozenDefensePanel.jsx";
import { getFrozenSeriesPreview, FROZEN_STRAT_REVIEW_ID } from "./strat/frozenSeriesPreviewReview";
import frozenMiscIntelligence from "./strat/frozenMiscIntelligence.pre10pm.json";
import React, { useEffect, useMemo, useState } from "react";
import { getStratTeamMark } from "./strat/teamIdentityRegistry";

import ImpactPlayersPanel from "./strat/ImpactPlayersPanel.jsx";
function humanize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatRotationEvidence(projection = {}) {
  const samples =
    Number(projection.transitionSamples);

  const consistency =
    Number(projection.dominance);

  const sampleText =
    Number.isFinite(samples)
      ? `${samples} rotation observation${samples === 1 ? "" : "s"}`
      : null;

  const consistencyText =
    Number.isFinite(consistency)
      ? `${Math.round(consistency * 100)}% rotation consistency`
      : null;

  const conditionalText =
    projection.conditional
      ? "conditional pattern"
      : null;

  return [
    sampleText,
    consistencyText,
    conditionalText,
  ]
    .filter(Boolean)
    .join(" · ");
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


function TeamIdentityMark({
  mark,
  tone = "teal",
  size = "standard",
}) {
  const [imageFailed, setImageFailed] =
    useState(false);

  const palette =
    tone === "rose"
      ? "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200"
      : "border-cyan-200 bg-cyan-50 text-cyan-800 dark:border-cyan-900/60 dark:bg-cyan-950/40 dark:text-cyan-200";

  const sizeClass =
    size === "large"
      ? "h-32 w-32 sm:h-40 sm:w-40 lg:h-52 lg:w-52"
      : "h-32 w-32 sm:h-40 sm:w-40 lg:h-52 lg:w-52";

  return (
    <div
      className={`flex ${sizeClass} shrink-0 items-center justify-center overflow-hidden rounded-2xl border shadow-sm ${palette}`}
      aria-label={`${mark?.teamName || "Team"} mark`}
    >
      {mark?.logoPath && !imageFailed ? (
        <img
          src={mark.logoPath}
          alt=""
          className="h-full w-full object-contain p-1"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <span className="text-xl font-black tracking-tight">
          {mark?.monogram || "?"}
        </span>
      )}
    </div>
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

function formatLeagueRank(
  rank,
  teamCount,
) {
  const numericRank = Number(rank);
  const numericCount = Number(teamCount);

  if (
    !Number.isFinite(numericRank) ||
    numericRank < 1
  ) {
    return "Rank unavailable";
  }

  if (
    Number.isFinite(numericCount) &&
    numericCount >= numericRank
  ) {
    return `#${numericRank} of ${numericCount}`;
  }

  return `#${numericRank} in league`;
}

function leagueRankTier(
  rank,
  teamCount,
) {
  const numericRank = Number(rank);
  const numericCount = Number(teamCount);

  if (
    !Number.isFinite(numericRank) ||
    !Number.isFinite(numericCount) ||
    numericRank < 1 ||
    numericCount < 1
  ) {
    return null;
  }

  const fraction =
    numericRank / numericCount;

  if (fraction <= 1 / 3) {
    return "Top third";
  }

  if (fraction <= 2 / 3) {
    return "Middle third";
  }

  return "Bottom third";
}

function formatLeagueMetric(
  value,
  digits = 0,
) {
  if (
    value == null ||
    value === ""
  ) {
    return "—";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  return numericValue.toFixed(digits);
}

function LeaguePositionMetric({
  label,
  value,
  rank,
  teamCount,
  digits = 0,
}) {
  const tier =
    leagueRankTier(
      rank,
      teamCount,
    );

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-800 dark:bg-slate-950/50">
      <div className="min-w-0">
        <p className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">
          {label}
        </p>

        <p className="mt-0.5 text-sm font-bold text-slate-900 dark:text-white">
          {formatLeagueMetric(
            value,
            digits,
          )}
        </p>
      </div>

      <div className="shrink-0 text-right">
        <p className="text-xs font-black text-slate-700 dark:text-slate-200">
          {formatLeagueRank(
            rank,
            teamCount,
          )}
        </p>

        {tier ? (
          <p className="mt-0.5 text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400">
            {tier}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ManagerUsageContext({
  tendencies,
}) {
  if (!tendencies) {
    return null;
  }

  const items = [
    [
      "SB",
      tendencies.stolenBases,
    ],
    [
      "Sac",
      tendencies.sacrifices,
    ],
    [
      "Hit & Run",
      tendencies.hitAndRuns,
    ],
    [
      "IBB",
      tendencies.intentionalWalks,
    ],
  ];

  return (
    <div className="rounded-xl border border-dashed border-slate-300 px-3 py-3 dark:border-slate-700">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
          Manager Usage
        </p>

        <span className="text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400">
          Descriptive
        </span>
      </div>

      <div className="mt-2 grid grid-cols-4 gap-2">
        {items.map(
          ([label, value]) => (
            <div
              key={label}
              className="text-center"
            >
              <p className="text-[9px] font-bold uppercase tracking-[0.08em] text-slate-400">
                {label}
              </p>

              <p className="mt-0.5 text-xs font-black text-slate-700 dark:text-slate-200">
                {value ?? "—"}
              </p>
            </div>
          ),
        )}
      </div>
    </div>
  );
}


function shortLeagueRank(rank) {
  const numericRank = Number(rank);

  if (
    !Number.isFinite(numericRank) ||
    numericRank < 1
  ) {
    return "—";
  }

  const mod100 = numericRank % 100;

  if (mod100 >= 11 && mod100 <= 13) {
    return `${numericRank}th`;
  }

  switch (numericRank % 10) {
    case 1:
      return `${numericRank}st`;
    case 2:
      return `${numericRank}nd`;
    case 3:
      return `${numericRank}rd`;
    default:
      return `${numericRank}th`;
  }
}

function frozenMetricValue(
  value,
  digits = 0
) {
  const numeric = Number(value);

  if (!Number.isFinite(numeric)) {
    return "—";
  }

  if (digits === 3) {
    return numeric
      .toFixed(3)
      .replace(/^0(?=\.)/, "");
  }

  return numeric.toFixed(digits);
}

function frozenPercent(value) {
  if (!Number.isFinite(value)) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function frozenRate(numerator, denominator) {
  const top = Number(numerator);
  const bottom = Number(denominator);

  if (
    !Number.isFinite(top) ||
    !Number.isFinite(bottom) ||
    bottom <= 0
  ) {
    return null;
  }

  return top / bottom;
}

function frozenLeaguePercentile(rank, teamCount) {
  const numericRank = Number(rank);
  const numericCount = Number(teamCount);

  if (
    !Number.isFinite(numericRank) ||
    !Number.isFinite(numericCount) ||
    numericCount <= 1 ||
    numericRank < 1
  ) {
    return null;
  }

  return Math.max(
    0,
    Math.min(
      100,
      ((numericCount - numericRank) /
        (numericCount - 1)) *
        100,
    ),
  );
}

function FrozenPercentileTrack({
  teamPercentile,
  opponentPercentile,
}) {
  return (
    <div className="relative mt-3 h-7">
      <div className="absolute left-0 right-0 top-3 h-1 rounded-full bg-slate-200 dark:bg-slate-700" />

      <div className="absolute left-1/2 top-1 h-5 w-px bg-slate-300 dark:bg-slate-600" />

      <span className="absolute left-1/2 top-0 -translate-x-1/2 text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
        League
      </span>

      {Number.isFinite(teamPercentile) ? (
        <span
          className="absolute top-[8px] h-3 w-3 -translate-x-1/2 rounded-full border-2 border-white bg-cyan-500 shadow dark:border-slate-900"
          style={{
            left: `${teamPercentile}%`,
          }}
          title={`Aquarium league percentile ${Math.round(
            teamPercentile,
          )}`}
        />
      ) : null}

      {Number.isFinite(opponentPercentile) ? (
        <span
          className="absolute top-[8px] h-3 w-3 -translate-x-1/2 rounded-full border-2 border-white bg-rose-500 shadow dark:border-slate-900"
          style={{
            left: `${opponentPercentile}%`,
          }}
          title={`Opponent league percentile ${Math.round(
            opponentPercentile,
          )}`}
        />
      ) : null}
    </div>
  );
}

// SERIES_LEAGUE_AVERAGE_SCOREBOARD_V1
function formatLeagueAverageMetric(
  value,
  digits,
) {
  if (
    value == null ||
    value === ""
  ) {
    return null;
  }

  const numericValue =
    Number(value);

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  const formatted =
    numericValue.toFixed(digits);

  return (
    digits === 3 &&
    numericValue >= 0 &&
    numericValue < 1
      ? formatted.replace(/^0/, "")
      : formatted
  );
}
// SERIES_MATCHUP_COMMAND_DECK_V1
const SERIES_COMMAND_METRICS = [
  {
    key: "ops",
    label: "OPS",
    direction: "HIGHER BETTER",
    digits: 3,
    teamValue: (profile) =>
      profile?.offense?.ops,
    opponentValue: (profile) =>
      profile?.offense?.ops,
    teamRank: (profile) =>
      profile?.offense?.opsRank,
    opponentRank: (profile) =>
      profile?.offense?.opsRank,
  },
  {
    key: "runs",
    label: "Runs Scored",
    direction: "HIGHER BETTER",
    digits: 0,
    teamValue: (profile) =>
      profile?.offense?.runsScored,
    opponentValue: (profile) =>
      profile?.offense?.runsScored,
    teamRank: (profile) =>
      profile?.offense?.runsScoredRank,
    opponentRank: (profile) =>
      profile?.offense?.runsScoredRank,
  },
  {
    key: "era",
    label: "ERA",
    direction: "LOWER BETTER",
    digits: 2,
    teamValue: (profile) =>
      profile?.pitching?.era,
    opponentValue: (profile) =>
      profile?.pitching?.era,
    teamRank: (profile) =>
      profile?.pitching?.eraRank,
    opponentRank: (profile) =>
      profile?.pitching?.eraRank,
  },
  {
    key: "whip",
    label: "WHIP",
    direction: "LOWER BETTER",
    digits: 2,
    teamValue: (profile) =>
      profile?.pitching?.whip,
    opponentValue: (profile) =>
      profile?.pitching?.whip,
    teamRank: (profile) =>
      profile?.pitching?.whipRank,
    opponentRank: (profile) =>
      profile?.pitching?.whipRank,
  },
  {
    key: "fielding",
    label: "Fielding %",
    direction: "HIGHER BETTER",
    digits: 3,
    teamValue: (profile) =>
      profile?.defense?.fieldingAverage,
    opponentValue: (profile) =>
      profile?.defense?.fieldingAverage,
    teamRank: (profile) =>
      profile?.defense?.fieldingAverageRank,
    opponentRank: (profile) =>
      profile?.defense?.fieldingAverageRank,
  },
  {
    key: "runDifferential",
    label: "Run Differential",
    direction: "HIGHER BETTER",
    digits: 0,
    teamValue: (profile) =>
      profile?.runDifferential,
    opponentValue: (profile) =>
      profile?.runDifferential,
    teamRank: (profile) =>
      profile?.runDifferentialRank,
    opponentRank: (profile) =>
      profile?.runDifferentialRank,
  },
];

function formatSeriesCommandMetric(
  value,
  digits = 0,
  signed = false,
) {
  if (
    value == null ||
    value === ""
  ) {
    return "—";
  }

  const numericValue =
    Number(value);

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  const formatted =
    numericValue.toFixed(digits);

  if (
    digits === 3 &&
    numericValue >= 0 &&
    numericValue < 1
  ) {
    return formatted.replace(/^0/, "");
  }

  if (
    signed &&
    numericValue > 0
  ) {
    return `+${formatted}`;
  }

  return formatted;
}

function buildSeriesCommandSignals(
  teamProfile,
  opponentProfile,
) {
  const rows =
    SERIES_COMMAND_METRICS.map(
      (metric) => {
        const teamValue =
          metric.teamValue(teamProfile);

        const opponentValue =
          metric.opponentValue(
            opponentProfile,
          );

        const teamRank =
          Number(
            metric.teamRank(teamProfile),
          );

        const opponentRank =
          Number(
            metric.opponentRank(
              opponentProfile,
            ),
          );

        const hasRanks =
          Number.isFinite(teamRank) &&
          Number.isFinite(opponentRank) &&
          teamRank > 0 &&
          opponentRank > 0;

        const teamNumeric =
          Number(teamValue);

        const opponentNumeric =
          Number(opponentValue);

        let favored = null;
        let rankGap = null;

        if (
          hasRanks &&
          teamRank !== opponentRank
        ) {
          favored =
            teamRank < opponentRank
              ? "TEAM"
              : "OPPONENT";

          rankGap =
            Math.abs(
              opponentRank - teamRank,
            );
        } else if (
          Number.isFinite(teamNumeric) &&
          Number.isFinite(
            opponentNumeric,
          ) &&
          teamNumeric !== opponentNumeric
        ) {
          const higherBetter =
            metric.direction ===
            "HIGHER BETTER";

          favored =
            higherBetter
              ? (
                  teamNumeric >
                  opponentNumeric
                    ? "TEAM"
                    : "OPPONENT"
                )
              : (
                  teamNumeric <
                  opponentNumeric
                    ? "TEAM"
                    : "OPPONENT"
                );
        }

        return {
          ...metric,
          teamValue,
          opponentValue,
          teamRank:
            hasRanks
              ? teamRank
              : null,
          opponentRank:
            hasRanks
              ? opponentRank
              : null,
          favored,
          rankGap,
        };
      },
    ).filter(
      (row) => row.favored,
    );

  const strongest = (
    favored,
    excludedKeys = new Set(),
  ) =>
    rows
      .filter(
        (row) =>
          row.favored === favored &&
          !excludedKeys.has(row.key),
      )
      .sort(
        (a, b) =>
          (b.rankGap || 0) -
          (a.rankGap || 0),
      )[0] || null;

  const teamEdge =
    strongest("TEAM");

  const opponentEdge =
    strongest("OPPONENT");

  const usedKeys =
    new Set(
      [
        teamEdge?.key,
        opponentEdge?.key,
      ].filter(Boolean),
    );

  const swing =
    rows
      .filter(
        (row) =>
          !usedKeys.has(row.key),
      )
      .sort(
        (a, b) =>
          (b.rankGap || 0) -
          (a.rankGap || 0),
      )[0] ||
    teamEdge ||
    opponentEdge ||
    null;

  return {
    teamEdge,
    opponentEdge,
    swing,
  };
}

function SeriesCommandSignalCard({
  eyebrow,
  signal,
  tone,
  teamName,
  opponentName,
  showFavored = false,
}) {
  const toneClass =
    tone === "cyan"
      ? "border-cyan-800/80 bg-cyan-950/35"
      : tone === "rose"
        ? "border-rose-900/80 bg-rose-950/30"
        : "border-amber-900/80 bg-amber-950/25";

  const eyebrowClass =
    tone === "cyan"
      ? "text-cyan-300"
      : tone === "rose"
        ? "text-rose-300"
        : "text-amber-300";

  if (!signal) {
    return (
      <div
        className={`rounded-2xl border p-4 ${toneClass}`}
      >
        <p
          className={`text-[11px] font-black uppercase tracking-[0.14em] ${eyebrowClass}`}
        >
          {eyebrow}
        </p>

        <p className="mt-3 text-sm font-bold text-slate-400">
          Evidence gated
        </p>
      </div>
    );
  }

  const favoredName =
    signal.favored === "TEAM"
      ? teamName
      : opponentName;

  return (
    <div
      className={`rounded-2xl border p-4 ${toneClass}`}
    >
      <p
        className={`text-[11px] font-black uppercase tracking-[0.14em] ${eyebrowClass}`}
      >
        {eyebrow}
      </p>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-xl font-black tracking-tight text-white">
          {signal.label}
        </h3>

        {showFavored ? (
          <span className="rounded-full border border-slate-700 bg-slate-950/70 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.1em] text-slate-300">
            Favors {favoredName}
          </span>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <p className="truncate text-[10px] font-bold uppercase tracking-[0.1em] text-cyan-300">
            {teamName}
          </p>

          <p className="mt-1 text-lg font-black tabular-nums text-white">
            {formatSeriesCommandMetric(
              signal.teamValue,
              signal.digits,
              signal.key === "runDifferential",
            )}

            {signal.teamRank ? (
              <span className="ml-2 text-xs font-bold text-slate-400">
                #{signal.teamRank}
              </span>
            ) : null}
          </p>
        </div>

        <div className="text-right">
          <p className="truncate text-[10px] font-bold uppercase tracking-[0.1em] text-rose-300">
            {opponentName}
          </p>

          <p className="mt-1 text-lg font-black tabular-nums text-white">
            {formatSeriesCommandMetric(
              signal.opponentValue,
              signal.digits,
              signal.key === "runDifferential",
            )}

            {signal.opponentRank ? (
              <span className="ml-2 text-xs font-bold text-slate-400">
                #{signal.opponentRank}
              </span>
            ) : null}
          </p>
        </div>
      </div>

      <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.08em] text-slate-400">
        {signal.rankGap
          ? `${signal.rankGap}-rank gap`
          : signal.direction}
      </p>
    </div>
  );
}

function SeriesCommandDeck({
  teamName,
  opponentName,
  teamProfile,
  opponentProfile,
  watchText,
}) {
  const {
    teamEdge,
    opponentEdge,
    swing,
  } = buildSeriesCommandSignals(
    teamProfile,
    opponentProfile,
  );

  const readLabels = {
    ops: "offensive-production",
    runs: "run-production",
    era: "run-prevention",
    whip: "traffic-suppression",
    fielding: "fielding",
    runDifferential: "run-differential",
  };

  const teamReadLabel =
    teamEdge
      ? readLabels[teamEdge.key] ||
        teamEdge.label.toLowerCase()
      : null;

  const opponentReadLabel =
    opponentEdge
      ? readLabels[opponentEdge.key] ||
        opponentEdge.label.toLowerCase()
      : null;

  let commandRead = null;

  if (
    teamEdge &&
    opponentEdge
  ) {
    commandRead =
      `${teamName} needs its ${teamReadLabel} advantage to shape the series; ` +
      `${opponentName} counters with the stronger ${opponentReadLabel} profile.`;
  } else if (teamEdge) {
    commandRead =
      `${teamName}'s clearest path is to lean on its ${teamReadLabel} advantage.`;
  } else if (opponentEdge) {
    commandRead =
      `${opponentName} owns the clearest season-to-date advantage through ${opponentReadLabel}.`;
  }

  return (
    <section
      data-bie-surface="series-command"
      data-bie-refinement="SERIES_MATCHUP_VISUAL_REFINEMENT_V2"
      className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 text-white shadow-xl"
    >
      <div className="border-b border-slate-800 px-5 py-5 sm:px-6">
        <p className="text-[11px] font-black uppercase tracking-[0.18em] text-cyan-300">
          Series Command
        </p>

        <h2 className="mt-1 text-2xl font-black tracking-tight text-white">
          What decides this matchup
        </h2>
      </div>

      <div className="grid gap-3 p-5 sm:p-6 xl:grid-cols-3">
        <SeriesCommandSignalCard
          eyebrow="Aquarium Edge"
          signal={teamEdge}
          tone="cyan"
          teamName={teamName}
          opponentName={opponentName}
        />

        <SeriesCommandSignalCard
          eyebrow={`${opponentName} Edge`}
          signal={opponentEdge}
          tone="rose"
          teamName={teamName}
          opponentName={opponentName}
        />

        <SeriesCommandSignalCard
          eyebrow="Swing Factor"
          signal={swing}
          tone="amber"
          teamName={teamName}
          opponentName={opponentName}
          showFavored
        />
      </div>

      {commandRead ? (
        <div className="border-t border-slate-800 bg-slate-900/60 px-5 py-4 sm:px-6">
          <p className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">
            BIE Read
          </p>

          <p className="mt-1 text-sm font-semibold leading-6 text-slate-200">
            {commandRead}
          </p>

          <p className="mt-1 text-[11px] font-medium text-slate-500">
            Season-to-date league evidence · recent form not yet normalized
          </p>
        </div>
      ) : null}

      {watchText ? (
        <div className="flex flex-col gap-1 border-t border-amber-900/50 bg-amber-950/20 px-5 py-3 sm:flex-row sm:items-center sm:gap-3 sm:px-6">
          <span className="shrink-0 text-[10px] font-black uppercase tracking-[0.14em] text-amber-300">
            Watch
          </span>

          <p className="text-xs font-semibold leading-5 text-slate-300">
            {watchText}
          </p>
        </div>
      ) : null}
    </section>
  );
}

function LeagueEdgeScoreboard({
  teamName,
  opponentName,
  teamProfile,
  opponentProfile,
  teamCount,
  leagueAverages,
}) {
  const rows = [
    {
      label: "OPS",
      context: "Offense",
      direction: "HIGHER BETTER",
      higherBetter: true,
      teamValue:
        teamProfile?.offense?.ops,
      opponentValue:
        opponentProfile?.offense?.ops,
      leagueAverage:
        leagueAverages?.ops,
      teamRank:
        teamProfile?.offense?.opsRank,
      opponentRank:
        opponentProfile?.offense?.opsRank,
      digits: 3,
      scaleFloor: 0.005,
    },
    {
      label: "Runs",
      context: "Run Production",
      direction: "HIGHER BETTER",
      higherBetter: true,
      teamValue:
        teamProfile?.offense?.runsScored,
      opponentValue:
        opponentProfile?.offense?.runsScored,
      leagueAverage:
        leagueAverages?.runsScored,
      teamRank:
        teamProfile?.offense?.runsScoredRank,
      opponentRank:
        opponentProfile?.offense?.runsScoredRank,
      digits: 0,
      averageDigits: 1,
      scaleFloor: 2,
    },
    {
      label: "ERA",
      context: "Run Prevention",
      direction: "LOWER BETTER",
      higherBetter: false,
      teamValue:
        teamProfile?.pitching?.era,
      opponentValue:
        opponentProfile?.pitching?.era,
      leagueAverage:
        leagueAverages?.era,
      teamRank:
        teamProfile?.pitching?.eraRank,
      opponentRank:
        opponentProfile?.pitching?.eraRank,
      digits: 2,
      scaleFloor: 0.05,
    },
    {
      label: "WHIP",
      context: "Traffic",
      direction: "LOWER BETTER",
      higherBetter: false,
      teamValue:
        teamProfile?.pitching?.whip,
      opponentValue:
        opponentProfile?.pitching?.whip,
      leagueAverage:
        leagueAverages?.whip,
      teamRank:
        teamProfile?.pitching?.whipRank,
      opponentRank:
        opponentProfile?.pitching?.whipRank,
      digits: 2,
      scaleFloor: 0.02,
    },
  ];

  return (
    <div
      data-bie-surface="league-edge-scoreboard-v4"
      data-bie-scale="TEAM_LEAGUE_AVG_OPPONENT_NUMERIC"
      className="mt-4 overflow-hidden rounded-2xl border border-slate-700 bg-slate-950/35"
    >
      <div className="grid grid-cols-[minmax(0,1fr)_180px_minmax(0,1fr)] items-center border-b border-slate-700 px-4 py-3">
        <div>
          <p className="text-[9px] font-black uppercase tracking-[0.16em] text-cyan-300">
            Aquarium
          </p>

          <p className="truncate text-xs font-black text-white">
            {teamName}
          </p>
        </div>

        <p className="text-center text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">
          League-average benchmark
        </p>

        <div className="text-right">
          <p className="text-[9px] font-black uppercase tracking-[0.16em] text-rose-300">
            Opponent
          </p>

          <p className="truncate text-xs font-black text-white">
            {opponentName}
          </p>
        </div>
      </div>

      {rows.map((row) => {
        const numericValue = (value) => {
          if (
            value == null ||
            value === ""
          ) {
            return null;
          }

          const parsed =
            Number(value);

          return Number.isFinite(parsed)
            ? parsed
            : null;
        };

        const teamNumeric =
          numericValue(row.teamValue);

        const opponentNumeric =
          numericValue(
            row.opponentValue,
          );

        const leagueNumeric =
          numericValue(
            row.leagueAverage,
          );

        const allValuesAvailable =
          teamNumeric != null &&
          opponentNumeric != null &&
          leagueNumeric != null;

        const teamBetter =
          teamNumeric != null &&
          opponentNumeric != null &&
          (
            row.higherBetter
              ? teamNumeric > opponentNumeric
              : teamNumeric < opponentNumeric
          );

        const opponentBetter =
          teamNumeric != null &&
          opponentNumeric != null &&
          (
            row.higherBetter
              ? opponentNumeric > teamNumeric
              : opponentNumeric < teamNumeric
          );

        const difference =
          teamNumeric != null &&
          opponentNumeric != null
            ? Math.abs(
                teamNumeric -
                opponentNumeric,
              )
            : null;

        const scaleValues =
          [
            teamNumeric,
            opponentNumeric,
            leagueNumeric,
          ].filter(
            (value) =>
              value != null,
          );

        const rawMinimum =
          scaleValues.length > 0
            ? Math.min(...scaleValues)
            : 0;

        const rawMaximum =
          scaleValues.length > 0
            ? Math.max(...scaleValues)
            : 1;

        const rawSpread =
          rawMaximum -
          rawMinimum;

        const scalePadding =
          Math.max(
            rawSpread * 0.12,
            row.scaleFloor,
          );

        const scaleMinimum =
          rawMinimum -
          scalePadding;

        const scaleMaximum =
          rawMaximum +
          scalePadding;

        const positionFor =
          (value) => {
            if (
              value == null ||
              scaleMaximum <= scaleMinimum
            ) {
              return 50;
            }

            const rawPosition =
              (
                (value - scaleMinimum) /
                (
                  scaleMaximum -
                  scaleMinimum
                )
              ) * 100;

            return Math.max(
              4,
              Math.min(
                96,
                rawPosition,
              ),
            );
          };

        const teamPosition =
          positionFor(teamNumeric);

        const opponentPosition =
          positionFor(
            opponentNumeric,
          );

        const leaguePosition =
          positionFor(
            leagueNumeric,
          );

        const teamRank =
          Number(row.teamRank);

        const opponentRank =
          Number(
            row.opponentRank,
          );

        const teamRankText =
          Number.isFinite(teamRank) &&
          teamRank > 0
            ? `#${teamRank}`
            : "—";

        const opponentRankText =
          Number.isFinite(
            opponentRank,
          ) &&
          opponentRank > 0
            ? `#${opponentRank}`
            : "—";

        const teamDisplay =
          formatLeagueAverageMetric(
            row.teamValue,
            row.digits,
          ) || "—";

        const opponentDisplay =
          formatLeagueAverageMetric(
            row.opponentValue,
            row.digits,
          ) || "—";

        const leagueDisplay =
          formatLeagueAverageMetric(
            row.leagueAverage,
            row.averageDigits ??
              row.digits,
          ) || "—";

        const differenceDisplay =
          difference == null
            ? null
            : formatLeagueAverageMetric(
                difference,
                row.digits,
              );

        const favoredName =
          teamBetter
            ? teamName
            : opponentBetter
              ? opponentName
              : null;

        return (
          <div
            key={row.label}
            className="grid grid-cols-[minmax(0,0.8fr)_minmax(420px,1.4fr)_minmax(0,0.8fr)] items-center gap-5 border-b border-slate-800 px-4 py-4 last:border-b-0"
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xl font-black tabular-nums text-cyan-300">
                  {teamDisplay}
                </span>

                <span className="text-[10px] font-black text-slate-400">
                  {teamRankText}
                </span>

                {teamBetter ? (
                  <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.1em] text-cyan-300">
                    Edge
                  </span>
                ) : null}
              </div>
            </div>

            <div className="min-w-0 text-center">
              <div className="flex flex-wrap items-center justify-center gap-2">
                <span className="text-sm font-black text-white">
                  {row.label}
                </span>

                <span
                  className={
                    row.higherBetter
                      ? "text-[9px] font-black uppercase tracking-[0.1em] text-emerald-300"
                      : "text-[9px] font-black uppercase tracking-[0.1em] text-violet-300"
                  }
                >
                  {row.higherBetter
                    ? "↑ Higher better"
                    : "↓ Lower better"}
                </span>
              </div>

              <p className="mt-0.5 text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400">
                {row.context}
              </p>

              <div className="relative mx-auto mt-3 h-10 max-w-xl">
                <div className="absolute left-0 right-0 top-6 h-1 rounded-full bg-slate-700" />

                {allValuesAvailable ? (
                  <>
                    <div
                      className="absolute top-1 -translate-x-1/2 whitespace-nowrap rounded-full border border-slate-600 bg-slate-900 px-2 py-0.5 text-[9px] font-black tabular-nums text-slate-300"
                      style={{
                        left: `${leaguePosition}%`,
                      }}
                    >
                      Lg Avg {leagueDisplay}
                    </div>

                    <div
                      className="absolute top-[19px] h-4 w-px -translate-x-1/2 bg-slate-400"
                      style={{
                        left: `${leaguePosition}%`,
                      }}
                    />

                    <div
                      aria-label={`${teamName} ${teamDisplay}`}
                      className="absolute top-[21px] h-3 w-3 -translate-x-1/2 rounded-full border-2 border-slate-950 bg-cyan-400 shadow"
                      style={{
                        left: `${teamPosition}%`,
                      }}
                    />

                    <div
                      aria-label={`${opponentName} ${opponentDisplay}`}
                      className="absolute top-[21px] h-3 w-3 -translate-x-1/2 rounded-full border-2 border-slate-950 bg-rose-400 shadow"
                      style={{
                        left: `${opponentPosition}%`,
                      }}
                    />
                  </>
                ) : null}
              </div>

              {favoredName &&
              differenceDisplay ? (
                <p className="mt-1 text-[10px] font-semibold text-slate-400">
                  {favoredName} · {differenceDisplay}
                </p>
              ) : null}
            </div>

            <div className="text-right">
              <div className="flex flex-wrap items-center justify-end gap-2">
                {opponentBetter ? (
                  <span className="rounded-full bg-rose-500/15 px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.1em] text-rose-300">
                    Edge
                  </span>
                ) : null}

                <span className="text-[10px] font-black text-slate-400">
                  {opponentRankText}
                </span>

                <span className="text-xl font-black tabular-nums text-rose-300">
                  {opponentDisplay}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FrozenBasepathGraphic({
  teamRate,
  opponentRate,
  label,
}) {
  const team =
    Number.isFinite(teamRate)
      ? Math.max(0, Math.min(1, teamRate))
      : 0;

  const opponent =
    Number.isFinite(opponentRate)
      ? Math.max(
          0,
          Math.min(1, opponentRate),
        )
      : 0;

  return (
    <div className="relative mx-auto h-[92px] w-[150px]">
      <svg
        viewBox="0 0 160 96"
        className="h-full w-full"
        aria-label={label}
      >
        <path
          d="M80 10 L142 48 L80 86 L18 48 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-slate-300 dark:text-slate-700"
        />

        <path
          d="M80 86 L80 10"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          strokeDasharray="3 4"
          className="text-slate-300 dark:text-slate-700"
        />

        <circle
          cx={18 + 62 * team}
          cy={48 - 38 * team}
          r="6"
          className="fill-cyan-500"
        />

        <circle
          cx={142 - 62 * opponent}
          cy={48 - 38 * opponent}
          r="6"
          className="fill-rose-500"
        />

        <circle
          cx="80"
          cy="48"
          r="18"
          className="fill-slate-950 dark:fill-slate-900"
        />

        <text
          x="80"
          y="52"
          textAnchor="middle"
          className="fill-white text-[9px] font-black"
        >
          RUN
        </text>
      </svg>
    </div>
  );
}

function FrozenMetricBar({
  value,
  tone = "team",
}) {
  const numeric =
    Number.isFinite(value)
      ? Math.max(0, Math.min(1, value))
      : 0;

  return (
    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
      <div
        className={
          tone === "team"
            ? "h-full rounded-full bg-cyan-500"
            : "h-full rounded-full bg-rose-500"
        }
        style={{
          width: `${numeric * 100}%`,
        }}
      />
    </div>
  );
}

function FrozenTeamMetric({
  label,
  value,
  rate,
  tone,
  note,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-[8px] font-black uppercase tracking-[0.14em] text-slate-400">
        {label}
      </p>

      <p
        className={`mt-1 text-lg font-black tabular-nums ${
          tone === "team"
            ? "text-cyan-600 dark:text-cyan-300"
            : "text-rose-600 dark:text-rose-300"
        }`}
      >
        {value}
      </p>

      {Number.isFinite(rate) ? (
        <FrozenMetricBar
          value={rate}
          tone={tone}
        />
      ) : null}

      {note ? (
        <p className="mt-1.5 text-[9px] font-medium leading-4 text-slate-500 dark:text-slate-400">
          {note}
        </p>
      ) : null}
    </div>
  );
}

function FrozenStealMetric({
  steals,
  caught,
  tone,
}) {
  const sb = Number(steals) || 0;
  const cs = Number(caught) || 0;
  const attempts = sb + cs;
  const success =
    frozenRate(sb, attempts);

  const sample =
    attempts < 5
      ? "Small sample"
      : attempts < 15
        ? "Developing sample"
        : "Established sample";

  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-[8px] font-black uppercase tracking-[0.14em] text-slate-400">
        Stealing
      </p>

      <p
        className={`mt-1 text-lg font-black tabular-nums ${
          tone === "team"
            ? "text-cyan-600 dark:text-cyan-300"
            : "text-rose-600 dark:text-rose-300"
        }`}
      >
        {sb}-{cs}
      </p>

      <p className="mt-1 text-[9px] font-bold text-slate-600 dark:text-slate-300">
        {frozenPercent(success)} success
      </p>

      <p className="mt-0.5 text-[8px] font-bold uppercase tracking-[0.1em] text-slate-400">
        {attempts} attempts · {sample}
      </p>
    </div>
  );
}

function FrozenDefenseDiamond() {
  return (
    <div className="relative mx-auto h-[205px] max-w-[330px]">
      <svg
        viewBox="0 0 360 220"
        className="h-full w-full"
        aria-label="Defense architecture"
      >
        <path
          d="M180 20 C80 30 35 85 35 155 L180 210 L325 155 C325 85 280 30 180 20 Z"
          className="fill-emerald-950/10 stroke-emerald-700/40 dark:fill-emerald-950/40"
          strokeWidth="2"
        />

        <path
          d="M180 202 L92 130 L180 58 L268 130 Z"
          className="fill-amber-100/50 stroke-amber-500/40 dark:fill-amber-950/25"
          strokeWidth="2"
        />

        {[
          ["CF", 180, 43],
          ["LF", 77, 82],
          ["RF", 283, 82],
          ["SS", 132, 118],
          ["2B", 228, 118],
          ["3B", 95, 157],
          ["1B", 265, 157],
          ["C", 180, 202],
        ].map(([position, x, y]) => (
          <g key={position}>
            <circle
              cx={x}
              cy={y}
              r="18"
              className="fill-slate-950 stroke-slate-500 dark:fill-slate-900"
              strokeWidth="1.5"
            />
            <text
              x={x}
              y={y + 4}
              textAnchor="middle"
              className="fill-white text-[10px] font-black"
            >
              {position}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function FrozenMatchupIntelligence({
  leagueId,
  teamName,
  opponentName,
}) {
  const leagueKey = String(
    leagueId || "",
  );

  const leagueTeams =
    frozenMiscIntelligence?.teams?.filter(
      (entry) =>
        String(entry?.leagueId) ===
        leagueKey,
    ) || [];

  const fieldingLeagueTeams =
    frozenFieldingIntelligence?.teams?.filter(
      (entry) =>
        String(entry?.leagueId) ===
        leagueKey,
    ) || [];

  const team =
    leagueTeams.find(
      (entry) =>
        entry?.role === "aquarium",
    );

  const opponent =
    leagueTeams.find(
      (entry) =>
        entry?.role === "opponent",
    );

  const teamFielding =
    fieldingLeagueTeams.find(
      (entry) =>
        entry?.role === "aquarium",
    ) || null;

  const opponentFielding =
    fieldingLeagueTeams.find(
      (entry) =>
        entry?.role === "opponent",
    ) || null;

  if (!team || !opponent) {
    return null;
  }

  const teamHitting =
    team?.hitting?.totals;

  const opponentHitting =
    opponent?.hitting?.totals;

  const teamPitching =
    team?.pitching?.totals;

  const opponentPitching =
    opponent?.pitching?.totals;

  if (
    !teamHitting ||
    !opponentHitting ||
    !teamPitching ||
    !opponentPitching
  ) {
    return null;
  }

  const running = (hitting) => {
    const opportunities =
      Number(
        hitting?.baserunning
          ?.opportunities,
      ) || 0;

    const advances =
      Number(
        hitting?.baserunning?.advances,
      ) || 0;

    const outs =
      Number(
        hitting?.baserunning?.outs,
      ) || 0;

    const attempts =
      advances + outs;

    const steals =
      Number(
        hitting?.stealing?.sb,
      ) || 0;

    const caught =
      Number(
        hitting?.stealing?.cs,
      ) || 0;

    return {
      opportunities,
      advances,
      outs,
      attempts,
      aggression:
        frozenRate(
          attempts,
          opportunities,
        ),
      execution:
        frozenRate(
          advances,
          attempts,
        ),
      stealSuccess:
        frozenRate(
          steals,
          steals + caught,
        ),
      steals,
      caught,
    };
  };

  const contact = (
    hitting,
    pitching,
  ) => {
    const hGb =
      Number(
        hitting?.contact
          ?.groundBalls,
      ) || 0;

    const hFb =
      Number(
        hitting?.contact?.flyBalls,
      ) || 0;

    const pGb =
      Number(
        pitching?.contact
          ?.groundBalls,
      ) || 0;

    const pFb =
      Number(
        pitching?.contact?.flyBalls,
      ) || 0;

    return {
      hittingGbShare:
        frozenRate(
          hGb,
          hGb + hFb,
        ),
      hittingGb: hGb,
      hittingFb: hFb,
      hittingGidp:
        hitting?.contact?.gidp,
      pitchingGbShare:
        frozenRate(
          pGb,
          pGb + pFb,
        ),
      pitchingGb: pGb,
      pitchingFb: pFb,
      pitchingGidp:
        pitching?.contact
          ?.gidpInduced,
    };
  };

  const teamRunning =
    running(teamHitting);

  const opponentRunning =
    running(opponentHitting);

  const teamContact =
    contact(
      teamHitting,
      teamPitching,
    );

  const opponentContact =
    contact(
      opponentHitting,
      opponentPitching,
    );

  const sampleLabel = (
    opportunities,
  ) => {
    if (opportunities < 20) {
      return "Small sample";
    }

    if (opportunities < 50) {
      return "Developing sample";
    }

    return "Established sample";
  };

  const teamRollTotal =
    Number(
      teamHitting?.rolls
        ?.hitterCard,
    ) +
    Number(
      teamHitting?.rolls
        ?.pitcherCard,
    );

  const opponentRollTotal =
    Number(
      opponentHitting?.rolls
        ?.hitterCard,
    ) +
    Number(
      opponentHitting?.rolls
        ?.pitcherCard,
    );

  const teamPhAb =
    Number(
      teamHitting?.pinchHitting?.ab,
    ) || 0;

  const opponentPhAb =
    Number(
      opponentHitting
        ?.pinchHitting?.ab,
    ) || 0;

  return (
    <section
      data-bie-surface="frozen-matchup-intelligence"
      data-bie-source="pre-10pm-20260816-201815"
      className="mt-5 grid gap-4 xl:grid-cols-12"
    >
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-8">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
                Running Game
              </p>
              <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
                Taking the extra base and stealing.
              </p>
            </div>

            <span className="rounded-full bg-slate-100 px-2 py-1 text-[8px] font-black uppercase tracking-[0.12em] text-slate-500 dark:bg-slate-800 dark:text-slate-300">
              Frozen data
            </span>
          </div>
        </div>

        <div className="grid grid-cols-[1fr_150px_1fr] items-center gap-2 px-4 py-4">
          <div className="space-y-2">
            <FrozenTeamMetric
              label="Aggression"
              value={frozenPercent(
                teamRunning.aggression,
              )}
              rate={
                teamRunning.aggression
              }
              tone="team"
              note={`${teamRunning.attempts}/${teamRunning.opportunities} attempts/opportunities`}
            />

            <FrozenTeamMetric
              label="Execution"
              value={frozenPercent(
                teamRunning.execution,
              )}
              rate={
                teamRunning.execution
              }
              tone="team"
              note={`${teamRunning.advances} safe · ${teamRunning.outs} out`}
            />

            <FrozenStealMetric
              steals={teamRunning.steals}
              caught={teamRunning.caught}
              tone="team"
            />
          </div>

          <div>
            <FrozenBasepathGraphic
              teamRate={
                teamRunning.aggression
              }
              opponentRate={
                opponentRunning.aggression
              }
              label="Baserunning aggression comparison"
            />

            <p className="mt-1 text-center text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
              Extra-base pressure
            </p>
          </div>

          <div className="space-y-2">
            <FrozenTeamMetric
              label="Aggression"
              value={frozenPercent(
                opponentRunning.aggression,
              )}
              rate={
                opponentRunning.aggression
              }
              tone="opponent"
              note={`${opponentRunning.attempts}/${opponentRunning.opportunities} attempts/opportunities`}
            />

            <FrozenTeamMetric
              label="Execution"
              value={frozenPercent(
                opponentRunning.execution,
              )}
              rate={
                opponentRunning.execution
              }
              tone="opponent"
              note={`${opponentRunning.advances} safe · ${opponentRunning.outs} out`}
            />

            <FrozenStealMetric
              steals={opponentRunning.steals}
              caught={opponentRunning.caught}
              tone="opponent"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 border-t border-slate-200 bg-slate-50 px-4 py-3 text-[9px] dark:border-slate-800 dark:bg-slate-950/40">
          <div>
            <p className="font-black text-cyan-600 dark:text-cyan-300">
              {teamName}
            </p>
            <p className="mt-0.5 text-slate-500 dark:text-slate-400">
              {sampleLabel(
                teamRunning.opportunities,
              )}
            </p>
          </div>

          <div className="text-right">
            <p className="font-black text-rose-600 dark:text-rose-300">
              {opponentName}
            </p>
            <p className="mt-0.5 text-slate-500 dark:text-slate-400">
              {sampleLabel(
                opponentRunning.opportunities,
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-4">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Run Control
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Preventing opponent advancement.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4">
          {[
            {
              label: teamName,
              tone: "text-cyan-600 dark:text-cyan-300",
              pitching: teamPitching,
            },
            {
              label: opponentName,
              tone: "text-rose-600 dark:text-rose-300",
              pitching:
                opponentPitching,
            },
          ].map((side) => (
            <div
              key={side.label}
              className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40"
            >
              <p
                className={`truncate text-[9px] font-black uppercase tracking-[0.12em] ${side.tone}`}
              >
                {side.label}
              </p>

              <p className="mt-3 text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
                SB allowed-CS
              </p>

              {(() => {
                const allowed =
                  Number(
                    side.pitching
                      ?.runControl
                      ?.stolenBasesAllowed,
                  ) || 0;

                const caught =
                  Number(
                    side.pitching
                      ?.runControl
                      ?.caughtStealing,
                  ) || 0;

                const attempts =
                  allowed + caught;

                return (
                  <>
                    <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                      {allowed}-{caught}
                    </p>

                    <p className="mt-1 text-[9px] font-bold text-slate-500 dark:text-slate-400">
                      {attempts} attempts faced
                    </p>

                    <p className="mt-0.5 text-[9px] font-bold text-slate-500 dark:text-slate-400">
                      {frozenPercent(
                        frozenRate(
                          caught,
                          attempts,
                        ),
                      )}{" "}
                      caught stealing
                    </p>

                    <p className="mt-1 text-[8px] font-black uppercase tracking-[0.1em] text-slate-400">
                      {attempts < 5
                        ? "Small sample"
                        : attempts < 15
                          ? "Developing sample"
                          : "Established sample"}
                    </p>
                  </>
                );
              })()}
            </div>
          ))}
        </div>

        <div className="mx-4 mb-4 rounded-xl border border-dashed border-slate-300 px-3 py-2.5 dark:border-slate-700">
          <p className="text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
            Next join
          </p>
          <p className="mt-1 text-[10px] font-bold leading-4 text-slate-600 dark:text-slate-300">
            Projected starter Hold will complete the running-game defense view.
          </p>
        </div>
      </div>

      <FrozenDefensePanel
        teamName={teamName}
        opponentName={opponentName}
        teamFielding={teamFielding}
        opponentFielding={opponentFielding}
      />

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-6">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Contact Profile
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Style and tendencies — not a grade.
          </p>
        </div>

        <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-800">
          {[
            {
              name: teamName,
              tone:
                "text-cyan-600 dark:text-cyan-300",
              profile: teamContact,
            },
            {
              name: opponentName,
              tone:
                "text-rose-600 dark:text-rose-300",
              profile:
                opponentContact,
            },
          ].map((side) => (
            <div
              key={side.name}
              className="p-4"
            >
              <p
                className={`truncate text-[9px] font-black uppercase tracking-[0.12em] ${side.tone}`}
              >
                {side.name}
              </p>

              <div className="mt-3 grid grid-cols-2 gap-3">
                <div>
                  <p className="text-[8px] font-black uppercase tracking-[0.1em] text-slate-400">
                    Hitting GB
                  </p>
                  <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                    {frozenPercent(
                      side.profile
                        .hittingGbShare,
                    )}
                  </p>
                  <p className="text-[8px] text-slate-400">
                    {side.profile.hittingGb}-
                    {side.profile.hittingFb}
                  </p>
                </div>

                <div>
                  <p className="text-[8px] font-black uppercase tracking-[0.1em] text-slate-400">
                    GIDP
                  </p>
                  <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                    {side.profile
                      .hittingGidp}
                  </p>
                </div>

                <div>
                  <p className="text-[8px] font-black uppercase tracking-[0.1em] text-slate-400">
                    Staff GB
                  </p>
                  <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                    {frozenPercent(
                      side.profile
                        .pitchingGbShare,
                    )}
                  </p>
                  <p className="text-[8px] text-slate-400">
                    {side.profile.pitchingGb}-
                    {side.profile.pitchingFb}
                  </p>
                </div>

                <div>
                  <p className="text-[8px] font-black uppercase tracking-[0.1em] text-slate-400">
                    GIDP induced
                  </p>
                  <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                    {side.profile
                      .pitchingGidp}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-3">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Bench
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Pinch-hitting production.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4">
          {[
            {
              name: teamName,
              tone:
                "text-cyan-600 dark:text-cyan-300",
              hitting: teamHitting,
            },
            {
              name: opponentName,
              tone:
                "text-rose-600 dark:text-rose-300",
              hitting:
                opponentHitting,
            },
          ].map((side) => {
            const ab =
              Number(
                side.hitting
                  ?.pinchHitting?.ab,
              ) || 0;

            const hits =
              Number(
                side.hitting
                  ?.pinchHitting?.hits,
              ) || 0;

            return (
              <div
                key={side.name}
                className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40"
              >
                <p
                  className={`truncate text-[9px] font-black uppercase tracking-[0.12em] ${side.tone}`}
                >
                  {side.name}
                </p>

                <p className="mt-3 text-2xl font-black tabular-nums text-slate-900 dark:text-white">
                  {hits}/{ab}
                </p>

                <p className="mt-1 text-[9px] font-bold text-slate-500 dark:text-slate-400">
                  {ab
                    ? frozenMetricValue(
                        hits / ab,
                        3,
                      )
                    : "—"}{" "}
                  AVG
                </p>

                <p className="mt-2 text-[9px] text-slate-400">
                  {
                    side.hitting
                      ?.pinchHitting?.hr
                  }{" "}
                  HR
                </p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-3">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Context
          </p>
          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Supporting information, not edge scores.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4">
          {[
            {
              name: teamName,
              tone:
                "text-cyan-600 dark:text-cyan-300",
              hitting: teamHitting,
              pitching: teamPitching,
              rollTotal: teamRollTotal,
            },
            {
              name: opponentName,
              tone:
                "text-rose-600 dark:text-rose-300",
              hitting:
                opponentHitting,
              pitching:
                opponentPitching,
              rollTotal:
                opponentRollTotal,
            },
          ].map((side) => (
            <div
              key={side.name}
              className="space-y-3"
            >
              <p
                className={`truncate text-[9px] font-black uppercase tracking-[0.12em] ${side.tone}`}
              >
                {side.name}
              </p>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40">
                <p className="text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
                  Hitter-card rolls
                </p>
                <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                  {frozenPercent(
                    frozenRate(
                      Number(
                        side.hitting
                          ?.rolls
                          ?.hitterCard,
                      ),
                      side.rollTotal,
                    ),
                  )}
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40">
                <p className="text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
                  GWBI
                </p>
                <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                  {
                    side.hitting
                      ?.contact?.gwbi
                  }
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40">
                <p className="text-[8px] font-black uppercase tracking-[0.12em] text-slate-400">
                  Inherited scored
                </p>
                <p className="mt-1 text-lg font-black tabular-nums text-slate-900 dark:text-white">
                  {
                    side.pitching
                      ?.inherited?.scored
                  }
                  /
                  {
                    side.pitching
                      ?.inherited?.runners
                  }
                </p>
                <p className="mt-1 text-[8px] font-bold uppercase tracking-[0.1em] text-slate-400">
                  Relief context
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LeaguePositionTeamCard({
  name,
  profile,
  teamCount,
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-950/30">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-black text-slate-900 dark:text-white">
            {name}
          </h3>

          <p className="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">
            Record{" "}
            {formatRecord(profile)}
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-right dark:border-slate-800 dark:bg-slate-950">
          <p className="text-[9px] font-black uppercase tracking-[0.12em] text-slate-400">
            Run Differential
          </p>

          <p className="mt-0.5 text-sm font-black text-slate-900 dark:text-white">
            {profile?.runDifferential ??
              "—"}
          </p>

          <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400">
            {formatLeagueRank(
              profile?.runDifferentialRank,
              teamCount,
            )}
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
            Offense
          </p>

          <div className="grid gap-2 sm:grid-cols-2">
            <LeaguePositionMetric
              label="OPS"
              value={
                profile?.offense?.ops
              }
              rank={
                profile?.offense?.opsRank
              }
              teamCount={teamCount}
              digits={3}
            />

            <LeaguePositionMetric
              label="Runs"
              value={
                profile?.offense
                  ?.runsScored
              }
              rank={
                profile?.offense
                  ?.runsScoredRank
              }
              teamCount={teamCount}
            />
          </div>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
            Pitching
          </p>

          <div className="grid gap-2 sm:grid-cols-3">
            <LeaguePositionMetric
              label="ERA"
              value={
                profile?.pitching?.era
              }
              rank={
                profile?.pitching?.eraRank
              }
              teamCount={teamCount}
              digits={2}
            />

            <LeaguePositionMetric
              label="WHIP"
              value={
                profile?.pitching?.whip
              }
              rank={
                profile?.pitching
                  ?.whipRank
              }
              teamCount={teamCount}
              digits={2}
            />

            <LeaguePositionMetric
              label="Runs Allowed"
              value={
                profile?.pitching
                  ?.runsAllowed
              }
              rank={
                profile?.pitching
                  ?.runsAllowedRank
              }
              teamCount={teamCount}
            />
          </div>
        </div>

        <div>
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
            Defense
          </p>

          <div className="grid gap-2 sm:grid-cols-3">
            <LeaguePositionMetric
              label="Fielding %"
              value={
                profile?.defense
                  ?.fieldingAverage
              }
              rank={
                profile?.defense
                  ?.fieldingAverageRank
              }
              teamCount={teamCount}
              digits={3}
            />

            <LeaguePositionMetric
              label="Errors"
              value={
                profile?.defense?.errors
              }
              rank={
                profile?.defense
                  ?.fewestErrorsRank
              }
              teamCount={teamCount}
            />

            <LeaguePositionMetric
              label="Unearned R/G"
              value={
                profile?.defense
                  ?.unearnedRunsPerGame
              }
              rank={
                profile?.defense
                  ?.lowestUnearnedRunsPerGameRank
              }
              teamCount={teamCount}
              digits={2}
            />
          </div>
        </div>

        <ManagerUsageContext
          tendencies={
            profile?.managerTendencies
          }
        />
      </div>
    </article>
  );
}
const HITTER_KEY_PLAYER_METRICS = [
  {
    key: "OPS",
    label: "OPS",
    digits: 3,
    direction: "desc",
  },
  {
    key: "OBP",
    label: "OBP",
    digits: 3,
    direction: "desc",
  },
  {
    key: "SLG",
    label: "SLG",
    digits: 3,
    direction: "desc",
  },
  {
    key: "BA",
    label: "BA",
    digits: 3,
    direction: "desc",
  },
  {
    key: "HR",
    label: "HR",
    digits: 0,
    direction: "desc",
  },
  {
    key: "RBI",
    label: "RBI",
    digits: 0,
    direction: "desc",
  },
];

const PITCHER_KEY_PLAYER_METRICS = [
  {
    key: "ERA",
    label: "ERA",
    digits: 2,
    direction: "asc",
  },
  {
    key: "WHIP",
    label: "WHIP",
    digits: 2,
    direction: "asc",
  },
  {
    key: "SO",
    label: "SO",
    digits: 0,
    direction: "desc",
  },
  {
    key: "W",
    label: "W",
    digits: 0,
    direction: "desc",
  },
  {
    key: "S",
    label: "S",
    digits: 0,
    direction: "desc",
  },
];

function numericPlayerMetric(row, metricKey) {
  const rawValue = row?.[metricKey];

  if (
    rawValue === null ||
    rawValue === undefined ||
    rawValue === ""
  ) {
    return null;
  }

  const numericValue = Number(rawValue);

  return Number.isFinite(numericValue)
    ? numericValue
    : null;
}

function rankPlayerRows(rows, metricConfig) {
  const safeRows =
    Array.isArray(rows) ? rows : [];

  return safeRows
    .map((row) => ({
      row,
      value: numericPlayerMetric(
        row,
        metricConfig.key,
      ),
    }))
    .filter(({ value }) => value !== null)
    .sort((left, right) => {
      const delta =
        metricConfig.direction === "asc"
          ? left.value - right.value
          : right.value - left.value;

      if (delta !== 0) {
        return delta;
      }

      return String(
        left.row?.playerName ||
          left.row?.name ||
          "",
      ).localeCompare(
        String(
          right.row?.playerName ||
            right.row?.name ||
            "",
        ),
      );
    })
    .slice(0, 3)
    .map(({ row }) => row);
}

function formatPlayerMetric(row, metricConfig) {
  const value =
    numericPlayerMetric(
      row,
      metricConfig.key,
    );

  if (value === null) {
    return "—";
  }

  return value.toFixed(
    metricConfig.digits,
  );
}

function KeyPlayerMetricSelector({
  label,
  metrics,
  selectedKey,
  onChange,
}) {
  return (
    <div>
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
        {label}
      </p>

      <div className="flex flex-wrap gap-1.5">
        {metrics.map((metric) => {
          const active =
            metric.key === selectedKey;

          return (
            <button
              key={metric.key}
              type="button"
              aria-pressed={active}
              onClick={() =>
                onChange(metric.key)
              }
              className={
                active
                  ? "rounded-full border border-cyan-500 bg-cyan-500 px-2.5 py-1 text-[11px] font-black text-slate-950 shadow-sm"
                  : "rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-bold text-slate-600 transition hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300 dark:hover:border-slate-600 dark:hover:text-white"
              }
            >
              {metric.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function PlayerList({
  title,
  rows,
  metricConfig,
}) {
  const safeRows =
    rankPlayerRows(
      rows,
      metricConfig,
    );

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
          {title}
        </p>

        <span className="text-[10px] font-black uppercase tracking-[0.12em] text-slate-400">
          {metricConfig.direction === "asc"
            ? "Low"
            : "High"}
        </span>
      </div>

      {safeRows.length ? (
        <div className="mt-2 space-y-2">
          {safeRows.map((row, index) => (
            <div
              key={`${row?.playerName || row?.name || "player"}-${index}`}
              className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-950/50"
            >
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {row?.playerName ||
                  row?.name ||
                  "Unknown player"}
              </span>

              <div className="text-right">
                <span className="text-sm font-bold tabular-nums text-slate-700 dark:text-slate-200">
                  {formatPlayerMetric(
                    row,
                    metricConfig,
                  )}
                </span>

                <span className="ml-1.5 text-[9px] font-black uppercase tracking-[0.1em] text-slate-400">
                  {metricConfig.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-400">
          Evidence gated
        </p>
      )}
    </div>
  );
}

const LEAGUE_LEADER_CATEGORY_PRIORITY = {
  hitters: [
    "BATTING AVERAGE",
    "ON BASE PCT",
    "SLUGGING PCT",
    "HOMERUNS",
    "RUNS BATTED IN",
    "RUNS SCORED",
    "HITS",
    "STOLEN BASES",
  ],
  pitchers: [
    "ERA",
    "WINS",
    "STRIKEOUTS",
    "SAVES",
    "INNINGS PITCHED",
    "STRIKEOUTS/WALKS",
    "HITS / 9 INNINGS",
    "BB / 9 INNINGS",
  ],
};

const LEAGUE_LEADER_CATEGORY_LABELS = {
  "BATTING AVERAGE": "Batting Avg",
  "ON BASE PCT": "On-Base %",
  "SLUGGING PCT": "Slugging %",
  HOMERUNS: "Home Runs",
  "RUNS BATTED IN": "RBI",
  "RUNS SCORED": "Runs",
  HITS: "Hits",
  "STOLEN BASES": "Stolen Bases",
  ERA: "ERA",
  WINS: "Wins",
  STRIKEOUTS: "Strikeouts",
  SAVES: "Saves",
  "INNINGS PITCHED": "Innings",
  "STRIKEOUTS/WALKS": "K/BB",
  "HITS / 9 INNINGS": "H/9",
  "BB / 9 INNINGS": "BB/9",
};

function prominentLeagueLeaders(
  players,
  section,
) {
  const appearances =
    players?.leagueLeaderAppearances;

  if (!Array.isArray(appearances)) {
    return null;
  }

  const priority =
    LEAGUE_LEADER_CATEGORY_PRIORITY[
      section
    ] || [];

  return appearances
    .filter((row) => {
      const rank = Number(row?.rank);

      return (
        row?.section === section &&
        Number.isFinite(rank) &&
        rank >= 1 &&
        rank <= 3 &&
        priority.includes(
          row?.categoryName,
        )
      );
    })
    .sort((left, right) => {
      const rankDifference =
        Number(left?.rank) -
        Number(right?.rank);

      if (rankDifference !== 0) {
        return rankDifference;
      }

      const categoryDifference =
        priority.indexOf(
          left?.categoryName,
        ) -
        priority.indexOf(
          right?.categoryName,
        );

      if (categoryDifference !== 0) {
        return categoryDifference;
      }

      return String(
        left?.playerName || "",
      ).localeCompare(
        String(
          right?.playerName || "",
        ),
      );
    })
    .slice(0, 3);
}

function LeagueLeaderGroup({
  label,
  rows,
}) {
  return (
    <div>
      <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">
        {label}
      </p>

      {rows?.length ? (
        <div className="mt-2 space-y-1.5">
          {rows.map((row, index) => (
            <div
              key={`${row?.section}-${row?.categoryName}-${row?.playerName}-${index}`}
              className="flex items-center gap-2 rounded-lg bg-white px-2.5 py-2 dark:bg-slate-950/60"
            >
              <span className="min-w-8 rounded-md bg-slate-900 px-1.5 py-1 text-center text-[10px] font-black text-white dark:bg-slate-100 dark:text-slate-950">
                #{row?.rank}
              </span>

              <div className="min-w-0">
                <p className="truncate text-xs font-bold text-slate-800 dark:text-slate-100">
                  {row?.playerName ||
                    "Unknown player"}
                </p>

                <p className="truncate text-[10px] font-semibold text-slate-500 dark:text-slate-400">
                  {LEAGUE_LEADER_CATEGORY_LABELS[
                    row?.categoryName
                  ] ||
                    row?.categoryName ||
                    "League category"}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-xs leading-5 text-slate-400">
          No top-three placements in
          highlighted categories.
        </p>
      )}
    </div>
  );
}

function LeagueLeaderSummary({
  players,
}) {
  const appearances =
    players?.leagueLeaderAppearances;

  const hasEvidence =
    Array.isArray(appearances);

  const hitterRows =
    prominentLeagueLeaders(
      players,
      "hitters",
    );

  const pitcherRows =
    prominentLeagueLeaders(
      players,
      "pitchers",
    );

  return (
    <div
      data-bie-surface="league-leaders"
      className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/40"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-600 dark:text-slate-300">
          League Leaders
        </p>

        {hasEvidence &&
        appearances.length > 0 ? (
          <span className="text-[9px] font-black uppercase tracking-[0.12em] text-slate-400">
            Top 3 league ranks
          </span>
        ) : null}
      </div>

      {!hasEvidence ? (
        <p className="mt-2 text-xs leading-5 text-slate-400">
          League leader context unavailable.
        </p>
      ) : appearances.length === 0 ? (
        <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
          No listed league leaders.
        </p>
      ) : (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <LeagueLeaderGroup
            label="Hitters"
            rows={hitterRows}
          />

          <LeagueLeaderGroup
            label="Pitchers"
            rows={pitcherRows}
          />
        </div>
      )}
    </div>
  );
}
function KeyPlayersPanel({
  teamName,
  opponentName,
  teamPlayers,
  opponentPlayers,
}) {
  const [
    hitterMetricKey,
    setHitterMetricKey,
  ] = useState("OPS");

  const [
    pitcherMetricKey,
    setPitcherMetricKey,
  ] = useState("ERA");

  const hitterMetric =
    HITTER_KEY_PLAYER_METRICS.find(
      (metric) =>
        metric.key === hitterMetricKey,
    ) || HITTER_KEY_PLAYER_METRICS[0];

  const pitcherMetric =
    PITCHER_KEY_PLAYER_METRICS.find(
      (metric) =>
        metric.key === pitcherMetricKey,
    ) || PITCHER_KEY_PLAYER_METRICS[0];

  const hitterRowsFor = (players) =>
    hitterMetric.key === "OPS"
      ? players?.topHittersByOPS
      : players?.hitters;

  const pitcherRowsFor = (players) =>
    pitcherMetric.key === "ERA"
      ? players?.topPitchersByERA
      : players?.pitchers;

  const sides = [
    {
      key: "team",
      name: teamName,
      players: teamPlayers,
      role: "Aquarium",
    },
    {
      key: "opponent",
      name: opponentName,
      players: opponentPlayers,
      role: "Opponent",
    },
  ];

  return (
    <section
      data-bie-surface="key-players"
      data-bie-polish="key-players-compact-v2"
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Key Players
          </p>

          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            League leaders and top current performers.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <KeyPlayerMetricSelector
            label="Hitters"
            metrics={
              HITTER_KEY_PLAYER_METRICS
            }
            selectedKey={
              hitterMetricKey
            }
            onChange={
              setHitterMetricKey
            }
          />

          <KeyPlayerMetricSelector
            label="Pitchers"
            metrics={
              PITCHER_KEY_PLAYER_METRICS
            }
            selectedKey={
              pitcherMetricKey
            }
            onChange={
              setPitcherMetricKey
            }
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 lg:divide-x lg:divide-slate-200 dark:lg:divide-slate-800">
        {sides.map(
          (
            {
              key,
              name,
              players,
              role,
            },
            sideIndex,
          ) => (
            <div
              key={key}
              className={
                sideIndex === 0
                  ? "px-4 py-3 lg:pr-4"
                  : "border-t border-slate-200 px-4 py-3 dark:border-slate-800 lg:border-t-0 lg:pl-4"
              }
            >
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p
                    className={
                      sideIndex === 0
                        ? "text-[9px] font-black uppercase tracking-[0.15em] text-cyan-600 dark:text-cyan-300"
                        : "text-[9px] font-black uppercase tracking-[0.15em] text-rose-600 dark:text-rose-300"
                    }
                  >
                    {role}
                  </p>

                  <h3 className="mt-0.5 truncate text-sm font-black text-slate-900 dark:text-white">
                    {name}
                  </h3>
                </div>

                <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-slate-400">
                  League-average benchmark
                </span>
              </div>

              <div className="space-y-3">
                <LeagueLeaderSummary
                  players={players}
                />

                <PlayerList
                  title={`Top Hitters · ${hitterMetric.label}`}
                  rows={hitterRowsFor(
                    players,
                  )}
                  metricConfig={
                    hitterMetric
                  }
                />

                <PlayerList
                  title={`Top Pitchers · ${pitcherMetric.label}`}
                  rows={pitcherRowsFor(
                    players,
                  )}
                  metricConfig={
                    pitcherMetric
                  }
                />
              </div>
            </div>
          ),
        )}
      </div>
    </section>
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
      !selection?.teamId
    ) {
      return null;
    }

    return (
      `${apiBase}/api/strat/league/${selection.leagueId}` +
      `/team/${selection.teamId}/series-preview/current`
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

      const frozenPreview =
        getFrozenSeriesPreview(
          selection?.leagueId,
          selection?.teamId
        );

      if (frozenPreview) {
        if (!cancelled) {
          setSeries(frozenPreview);
          setStatus("ready");
          setError("");
        }

        return;
      }

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

  const sourceOpponentDisplayName =
    identity.opponentDisplayName ||
    selection?.opponentDisplayName ||
    "Opponent";

  const opponentTeamId =
    identity.opponentTeamId ||
    selection?.opponentTeamId ||
    identity?.opponent?.teamId ||
    null;

  const teamMark = getStratTeamMark(
    selection?.teamId,
    "Aquarium Drinkers",
  );

  const opponentMark = getStratTeamMark(
    opponentTeamId,
    sourceOpponentDisplayName,
  );

  const canonicalOpponentDisplayName =
    opponentMark?.teamName ||
    sourceOpponentDisplayName;

  const opponentDisplayName =
    canonicalOpponentDisplayName;

  const normalizePreviewText = (value) => {
    if (value === null || value === undefined) {
      return value;
    }

    let normalized = String(value);

    if (
      sourceOpponentDisplayName &&
      opponentDisplayName &&
      sourceOpponentDisplayName !==
        opponentDisplayName &&
      !normalized.includes(
        opponentDisplayName
      )
    ) {
      normalized = normalized.replaceAll(
        sourceOpponentDisplayName,
        opponentDisplayName,
      );
    }

    normalized = normalized.replace(
      /\bdominance\s+([0-9]+(?:\.[0-9]+)?)/gi,
      (match, rawValue) => {
        const numericValue =
          Number(rawValue);

        if (!Number.isFinite(numericValue)) {
          return match;
        }

        return `${Math.round(
          numericValue * 100
        )}% rotation consistency`;
      },
    );

    return normalized;
  };

  const aquariumDisplayName =
    teamMark?.teamName ||
    "Aquarium Drinkers";

  const aquariumIsHome =
    String(identity.homeAway || "")
      .trim()
      .toUpperCase()
      .startsWith("HOME");

  const homeTeamDisplayName =
    aquariumIsHome
      ? aquariumDisplayName
      : opponentDisplayName;

  const awayTeamDisplayName =
    aquariumIsHome
      ? opponentDisplayName
      : aquariumDisplayName;

  const displayOutlookSynopsis =
    payload?.executiveOutlook?.synopsis
      ? normalizePreviewText(
          payload.executiveOutlook.synopsis
        )
      : null;

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
    <div className="min-h-full space-y-6 bg-slate-100/70 p-4 sm:p-6 dark:bg-slate-950">
      <header
        data-bie-surface="series-hero"
        className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 text-white shadow-xl"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-gradient-to-r from-cyan-950/90 via-slate-950 to-rose-950/80 px-5 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-3">
            {onBack ? (
              <button
                type="button"
                onClick={onBack}
                className="text-xs font-black uppercase tracking-[0.14em] text-cyan-300 transition hover:text-cyan-200"
              >
                ← Active Teams
              </button>
            ) : null}

            <span className="hidden h-4 w-px bg-slate-700 sm:block" />

            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
              BIE Series Matchup
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Pill status={snapshot.snapshotClassification}>
              {humanize(snapshot.snapshotClassification)}
            </Pill>

            <Pill status={lifecycle.stage}>
              {humanize(lifecycle.stage)}
            </Pill>
          </div>
        </div>

        <div className="relative overflow-hidden px-5 py-10 sm:px-8 lg:px-10 lg:py-12">
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
          >
            <div className="absolute -left-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-cyan-500/15 blur-3xl" />
            <div className="absolute -right-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-rose-500/15 blur-3xl" />
          </div>

          <div className="relative grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(220px,0.55fr)_minmax(0,1fr)]">
            <div className="flex items-center gap-5">
              <TeamIdentityMark
                key={teamMark?.teamId || "aquarium"}
                mark={teamMark}
                tone="teal"
              />

              <div className="min-w-0">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                  Aquarium Drinkers
                </p>

                <h2 className="mt-1 text-2xl font-black tracking-tight text-white">
                  {teamMark?.teamName || "Aquarium Drinkers"}
                </h2>

                <p className="mt-1 text-xs font-semibold text-slate-400">
                  BIE-backed team
                </p>
              </div>
            </div>

            <div className="text-center">
              <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">
                Series Matchup
              </p>

              <h1 className="mt-3 text-3xl font-black leading-tight tracking-tight text-white">
                <span className="block whitespace-nowrap">
                  {homeTeamDisplayName}
                </span>

                <span className="mt-1 block whitespace-nowrap">
                  <span className="mr-2 font-semibold text-cyan-300">
                    vs.
                  </span>
                  {awayTeamDisplayName}
                </span>
              </h1>

              <div className="mt-4 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs font-semibold text-slate-400">
                <span>{identity.homeAway || "Venue TBD"}</span>
                <span aria-hidden="true">·</span>
                <span>{identity.scheduledDate || "Date TBD"}</span>
                <span aria-hidden="true">·</span>
                <span>
                  {identity.gameCount || replayGames.length || "—"} games
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-5">
              <div className="min-w-0 text-right">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-rose-300">
                  Opponent
                </p>

                <h2 className="mt-1 text-2xl font-black tracking-tight text-white">
                  {opponentDisplayName}
                </h2>

                <p className="mt-1 text-xs font-semibold text-slate-400">
                  League {selection?.leagueId}
                </p>
              </div>

              <TeamIdentityMark
                key={opponentMark?.teamId || opponentDisplayName}
                mark={opponentMark}
                tone="rose"
                size="large"
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 bg-slate-950/90 px-5 py-3 sm:px-6">
          <p className="truncate text-[10px] font-semibold text-slate-500">
            {identity.seriesId}
          </p>

          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-emerald-400">
            Feedback loop active
          </p>
        </div>
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

      {leagueContext?.status === "AVAILABLE" ? (
        <SeriesCommandDeck
          teamName={aquariumDisplayName}
          opponentName={opponentDisplayName}
          teamProfile={teamProfile}
          opponentProfile={opponentProfile}

          watchText={
            outlook?.watch?.text
              ? normalizePreviewText(
                  outlook.watch.text,
                )
              : null
          }
        />
      ) : null}

      {leagueContext?.status === "AVAILABLE" ? (
        <section
          data-bie-surface="league-position"
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                League Position
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Season-to-date team and opponent position against league rank and the league-average baseline.
              </p>
            </div>

            <span className="rounded-full border border-slate-200 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-slate-500 dark:border-slate-700 dark:text-slate-300">
              {leagueContext?.leagueTeamCount
                ? `${leagueContext.leagueTeamCount} teams`
                : "League context"}
            </span>
          </div>

          <LeagueEdgeScoreboard
            teamName={aquariumDisplayName}
            opponentName={opponentDisplayName}
            teamProfile={teamProfile}
            opponentProfile={opponentProfile}
            teamCount={
              leagueContext?.leagueTeamCount
            }
            leagueAverages={
              leagueContext?.leagueAverages
            }
          />

          <FrozenMatchupIntelligence
            leagueId={selection?.leagueId}
            teamName={aquariumDisplayName}
            opponentName={opponentDisplayName}
          />
        </section>
      ) : null}
      {playerIntelligence?.status === "AVAILABLE" ? (
        <ImpactPlayersPanel
          teamName={aquariumDisplayName}
          opponentName={opponentDisplayName}
          teamPlayers={teamPlayers}
          opponentPlayers={opponentPlayers}
        />
      ) : null}
      {(payload?.pitchingMatchup?.status === "CURRENT_PROJECTED" ||
        payload?.lineupMatchups?.status === "CURRENT_OFFENSIVE_PROFILE") ? (
        <section
          data-bie-cleanup="available-intelligence-only"
        >
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
          What Matters in This Series
        </p>

        <div className="grid gap-3 md:grid-cols-2">
          {payload?.pitchingMatchup?.status === "CURRENT_PROJECTED" ? (
            <div
              data-bie-surface="projected-starters"
              className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 text-white shadow-xl md:col-span-2"
            >
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 px-5 py-5 sm:px-6">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                    Rotation Intelligence
                  </p>

                  <h2 className="mt-1 text-xl font-black text-white">
                    Projected Starters
                  </h2>

                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    BIE projection from observed starter sequencing. These are
                    not published probable starters.
                  </p>
                </div>

                <Pill status="PROJECTED">
                  BIE projected
                </Pill>
              </div>

              <div className="grid gap-4 p-5 sm:p-6 lg:grid-cols-2">
                {[
                  payload.pitchingMatchup.team,
                  payload.pitchingMatchup.opponent,
                ].map((side, sideIndex) => (
                  <article
                    key={side.role}
                    className={
                      sideIndex === 0
                        ? "rounded-2xl border-2 border-cyan-300 bg-cyan-50 p-4 text-slate-950 shadow-md"
                        : "rounded-2xl border-2 border-rose-300 bg-rose-50 p-4 text-slate-950 shadow-md"
                    }
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={
                              sideIndex === 0
                                ? "h-2.5 w-2.5 rounded-full bg-cyan-500"
                                : "h-2.5 w-2.5 rounded-full bg-rose-500"
                            }
                            aria-hidden="true"
                          />

                          <h3
                            className={
                              sideIndex === 0
                                ? "text-lg font-black text-cyan-950"
                                : "text-lg font-black text-rose-950"
                            }
                          >
                            {normalizePreviewText(side.displayName)}
                          </h3>
                        </div>

                        <p className="mt-1 text-[11px] font-medium text-slate-500">
                          Last starter: {side.currentLastStarter || "Unknown"}
                          {" · "}
                          {side.startHistoryCount ?? 0} starts observed
                        </p>
                      </div>

                      <Pill status={side.overallConfidence}>
                        {side.overallConfidence} confidence
                      </Pill>
                    </div>

                    <div className="mt-4 space-y-2.5">
                      {(side.projections || []).map((projection) => {
                        const scheduleGameNumber =
                          identity.scheduleGameNumbers?.[
                            projection.slot - 1
                          ] ?? projection.slot;

                        return (
                          <div
                            key={`${side.role}-${projection.slot}`}
                            className={
                              sideIndex === 0
                                ? "rounded-xl border border-cyan-100 bg-white px-3 py-3 shadow-sm"
                                : "rounded-xl border border-rose-100 bg-white px-3 py-3 shadow-sm"
                            }
                          >
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">
                                  Game {scheduleGameNumber}
                                </p>

                                <p className="mt-1 text-base font-black text-slate-950">
                                  {projection.pitcher}
                                </p>
                              </div>

                              <Pill status={projection.effectiveConfidence}>
                                {projection.effectiveConfidence}
                              </Pill>
                            </div>

                            <p
                              className="mt-2 text-[10px] font-medium leading-4 text-slate-500"
                              title="Rotation evidence used by BIE to estimate the likelihood that the observed starter sequence repeats."
                            >
                              {formatRotationEvidence(projection)}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </article>
                ))}
              </div>

              <div className="border-t border-slate-800 bg-slate-900/70 px-5 py-3 sm:px-6">
                <p className="text-[10px] leading-4 text-slate-500">
                  Rotation consistency describes how consistently the observed
                  starter sequence repeats; it is not a measure of pitcher
                  performance.
                </p>
              </div>
            </div>          ) : null}
          {payload?.lineupMatchups?.status === "CURRENT_OFFENSIVE_PROFILE" ? (
            <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  Current Offensive Threats
                </p>

                <Pill status="CURRENT">
                  Current OPS profile
                </Pill>
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Top current offensive threats by OPS, minimum 100 AB.
                This is not a projected batting order. Batting hand and card
                balance are shown as evidence; platoon edges remain unresolved.
              </p>

              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                {[
                  payload.lineupMatchups.team,
                  payload.lineupMatchups.opponent,
                ].map((side, sideIndex) => (
                  <div
                    key={side.role}
                    className={
                      sideIndex === 0
                        ? "rounded-2xl border border-cyan-200 bg-gradient-to-b from-cyan-50/80 to-white p-4 dark:border-cyan-900/60 dark:from-cyan-950/25 dark:to-slate-900"
                        : "rounded-2xl border border-rose-200 bg-gradient-to-b from-rose-50/80 to-white p-4 dark:border-rose-900/60 dark:from-rose-950/25 dark:to-slate-900"
                    }
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p
                        className={
                          sideIndex === 0
                            ? "font-black text-cyan-900 dark:text-cyan-100"
                            : "font-black text-rose-900 dark:text-rose-100"
                        }
                      >
                        {normalizePreviewText(side.displayName)}
                      </p>

                      <span
                        className={
                          sideIndex === 0
                            ? "rounded-full bg-cyan-100 px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300"
                            : "rounded-full bg-rose-100 px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                        }
                      >
                        {sideIndex === 0
                          ? "Aquarium"
                          : "Opponent"}
                      </span>
                    </div>

                    <div className="mt-3 space-y-2">
                      {(side.threats || []).map((player, index) => (
                        <div
                          key={`${side.role}-${player.name}`}
                          className="rounded-xl border border-slate-200/80 bg-white/90 px-3 py-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-950/60"
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                                Threat {index + 1}
                              </p>

                              <p className="mt-0.5 text-sm font-black text-slate-800 dark:text-slate-100">
                                {player.name}
                              </p>

                              <p className="mt-0.5 text-[11px] text-slate-400">
                                {player.position || "N/A"}
                                {" / "}
                                Bats {player.bats || "N/A"}
                                {" / "}
                                Balance {player.balance || "N/A"}
                                {" / "}
                                {player.ab} AB
                              </p>
                            </div>

                            <div className="text-right">
                              <p className="text-sm font-black text-slate-900 dark:text-white">
                                OPS {Number(player.ops).toFixed(3)}
                              </p>

                              <p className="mt-0.5 text-[11px] text-slate-400">
                                {Number(player.ba).toFixed(3)}
                                {" / "}
                                {Number(player.obp).toFixed(3)}
                                {" / "}
                                {Number(player.slg).toFixed(3)}
                              </p>

                              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400">
                                BA / OBP / SLG
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {payload?.availabilityEnvironment?.status === "CURRENT_PARTIAL" ? (
            <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:col-span-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  Readiness & Environment
                </p>

                <Pill status="CURRENT">
                  Partial current evidence
                </Pill>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <div className="rounded-2xl border border-sky-200 bg-gradient-to-b from-sky-50/80 to-white p-4 dark:border-sky-900/60 dark:from-sky-950/25 dark:to-slate-900">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                    Series Environment
                  </p>

                  <p className="mt-1 text-base font-black text-slate-900 dark:text-white">
                    {payload.availabilityEnvironment.series.ballpark}
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {payload.availabilityEnvironment.series.homeAway} series
                  </p>

                  <p className="mt-2 text-[11px] leading-4 text-slate-400">
                    Park identity is captured. Park-factor effects remain unresolved.
                  </p>
                </div>

                <div className="rounded-2xl border border-cyan-200 bg-gradient-to-b from-cyan-50/80 to-white p-4 dark:border-cyan-900/60 dark:from-cyan-950/25 dark:to-slate-900">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                    Aquarium Roster State
                  </p>

                  <p className="mt-1 text-base font-black text-slate-900 dark:text-white">
                    {payload.availabilityEnvironment.team.record}
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {payload.availabilityEnvironment.team.hitterCount} hitters
                    {" / "}
                    {payload.availabilityEnvironment.team.pitcherCount} pitchers
                  </p>

                  <p className="mt-2 text-[11px] leading-4 text-slate-400">
                    Roster value {payload.availabilityEnvironment.team.rosterValue}
                    {" / "}
                    Cash {payload.availabilityEnvironment.team.cashAvailable}
                  </p>
                </div>

                <div className="rounded-2xl border border-rose-200 bg-gradient-to-b from-rose-50/80 to-white p-4 dark:border-rose-900/60 dark:from-rose-950/25 dark:to-slate-900">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">
                    Opponent Roster State
                  </p>

                  <p className="mt-1 text-base font-black text-slate-900 dark:text-white">
                    {payload.availabilityEnvironment.opponent.record}
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {payload.availabilityEnvironment.opponent.hitterCount} hitters
                    {" / "}
                    {payload.availabilityEnvironment.opponent.pitcherCount} pitchers
                  </p>

                  <p className="mt-2 text-[11px] leading-4 text-slate-400">
                    Roster value {payload.availabilityEnvironment.opponent.rosterValue}
                  </p>
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    Live injury-page check
                  </p>

                  <Pill status={
                    payload.availabilityEnvironment.injuries.relevantRowCount > 0
                      ? "CURRENT"
                      : "CLEAR"
                  }>
                    {payload.availabilityEnvironment.injuries.relevantRowCount > 0
                      ? `${payload.availabilityEnvironment.injuries.relevantRowCount} relevant row(s)`
                      : "No relevant rows found"}
                  </Pill>
                </div>

                <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
                  {payload.availabilityEnvironment.injuries.note}
                </p>
              </div>

              <p className="mt-3 text-[11px] leading-4 text-slate-400">
                Recent transaction implications and quantified park effects remain evidence gated.
              </p>
            </div>
          ) : null}
          {payload?.managerNotebook?.status === "CURRENT_EVIDENCE_BASED" ? (
            <div className="overflow-hidden rounded-3xl bg-slate-950 shadow-xl ring-1 ring-slate-800 md:col-span-2">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 bg-gradient-to-r from-slate-950 via-slate-950 to-cyan-950/60 px-5 py-5 sm:px-6">
                <div>
                  <div className="flex items-center gap-3">
                    <span
                      className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400 text-lg font-black text-slate-950"
                      aria-hidden="true"
                    >
                      B
                    </span>

                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                        Decision Support
                      </p>

                      <h2 className="mt-0.5 text-xl font-black tracking-tight text-white">
                        Manager's Notebook
                      </h2>
                    </div>
                  </div>

                  <p className="mt-3 max-w-4xl text-xs leading-5 text-slate-400">
                    {normalizePreviewText(
                      payload.managerNotebook.note
                    )}
                  </p>
                </div>

                <div className="rounded-full border border-emerald-700/60 bg-emerald-950/70 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.16em] text-emerald-300">
                  Evidence based
                </div>
              </div>

              <div className="grid gap-4 p-5 sm:p-6 lg:grid-cols-2">
                {(payload.managerNotebook.items || []).map(
                  (item) => (
                    <article
                      key={item.priority}
                      className={
                        Number(item.priority) === 1
                          ? "group relative overflow-hidden rounded-2xl border border-rose-200 bg-white p-5 shadow-sm transition dark:border-rose-900/60 dark:bg-slate-900"
                          : Number(item.priority) === 2
                            ? "group relative overflow-hidden rounded-2xl border border-cyan-200 bg-white p-5 shadow-sm transition dark:border-cyan-900/60 dark:bg-slate-900"
                            : Number(item.priority) === 3
                              ? "group relative overflow-hidden rounded-2xl border border-indigo-200 bg-white p-5 shadow-sm transition dark:border-indigo-900/60 dark:bg-slate-900"
                              : "group relative overflow-hidden rounded-2xl border border-amber-200 bg-white p-5 shadow-sm transition dark:border-amber-900/60 dark:bg-slate-900"
                      }
                    >
                      <div
                        className={
                          Number(item.priority) === 1
                            ? "absolute inset-x-0 top-0 h-1 bg-rose-500"
                            : Number(item.priority) === 2
                              ? "absolute inset-x-0 top-0 h-1 bg-cyan-500"
                              : Number(item.priority) === 3
                                ? "absolute inset-x-0 top-0 h-1 bg-indigo-500"
                                : "absolute inset-x-0 top-0 h-1 bg-amber-500"
                        }
                      />

                      <div className="flex items-start gap-4">
                        <div
                          className={
                            Number(item.priority) === 1
                              ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-100 text-xl font-black text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                              : Number(item.priority) === 2
                                ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-cyan-100 text-xl font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300"
                                : Number(item.priority) === 3
                                  ? "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-100 text-xl font-black text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                                  : "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-xl font-black text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                          }
                        >
                          {item.priority}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <div>
                              <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">
                                Decision Priority
                              </p>

                              <h3 className="mt-1 text-base font-black leading-snug text-slate-950 dark:text-white">
                                {normalizePreviewText(
                                  item.title
                                )}
                              </h3>
                            </div>

                            <Pill status={item.confidence}>
                              {item.confidence}
                            </Pill>
                          </div>

                          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                            {normalizePreviewText(
                              item.recommendation
                            )}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
                        <p className="text-[10px] font-medium leading-4 text-slate-400">
                          <span className="mr-1 font-black uppercase tracking-[0.12em]">
                            Evidence
                          </span>
                          {normalizePreviewText(
                            item.evidence
                          )}
                        </p>
                      </div>
                    </article>
                  )
                )}
              </div>
            </div>
          ) : null}
        </div>
      </section>
      ) : null}

      <section className="grid gap-5 lg:grid-cols-[1.45fr_0.55fr]">
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 text-white shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 px-5 py-5 sm:px-6">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                Series Workflow
              </p>

              <h2 className="mt-1 text-xl font-black">
                Preview to Learning
              </h2>

              <p className="mt-2 max-w-2xl text-xs leading-5 text-slate-400">
                The preview stays frozen. Game evidence is revealed deliberately,
                reviewed after the series, then carried forward into the next
                matchup.
              </p>
            </div>

            <Pill status={series?.replay?.status}>
              {humanize(series?.replay?.status)}
            </Pill>
          </div>

          <div className="p-5 sm:p-6">
            <div className="grid gap-3 md:grid-cols-4">
              <div className="relative rounded-2xl border border-cyan-500/70 bg-cyan-950/60 p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-400 text-sm font-black text-slate-950">
                    1
                  </span>

                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-cyan-300">
                    Current
                  </span>
                </div>

                <p className="mt-4 text-sm font-black text-white">
                  Series Preview
                </p>

                <p className="mt-1 text-[11px] leading-4 text-slate-400">
                  Frozen pre-series decision baseline.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-700 bg-slate-900 p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-600 text-sm font-black text-slate-300">
                    2
                  </span>

                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-500">
                    Controlled
                  </span>
                </div>

                <p className="mt-4 text-sm font-black text-white">
                  Spoiler-Free Replay
                </p>

                <p className="mt-1 text-[11px] leading-4 text-slate-400">
                  Game evidence stays hidden until deliberately revealed.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-700 bg-slate-900 p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-600 text-sm font-black text-slate-300">
                    3
                  </span>

                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-slate-500">
                    After Series
                  </span>
                </div>

                <p className="mt-4 text-sm font-black text-white">
                  Series Review
                </p>

                <p className="mt-1 text-[11px] leading-4 text-slate-400">
                  Actual game shape is compared with the frozen preview.
                </p>
              </div>

              <div className="rounded-2xl border border-emerald-900/80 bg-emerald-950/40 p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full border border-emerald-700 text-sm font-black text-emerald-300">
                    4
                  </span>

                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-emerald-400">
                    Feedback
                  </span>
                </div>

                <p className="mt-4 text-sm font-black text-white">
                  Learning
                </p>

                <p className="mt-1 text-[11px] leading-4 text-slate-400">
                  Supported signals carry into the next series preview.
                </p>
              </div>
            </div>

            {replayGames.length ? (
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {replayGames.map((game) => (
                  <div
                    key={`${identity.seriesId}-${game.ordinal}`}
                    className="rounded-2xl border border-slate-700 bg-slate-900/80 p-4"
                  >
                    <p className="text-[9px] font-black uppercase tracking-[0.16em] text-cyan-300">
                      Game {game.ordinal}
                    </p>

                    <p className="mt-1 text-sm font-black text-white">
                      Schedule #{game.scheduleGameNumber}
                    </p>

                    <p className="mt-2 text-[11px] text-slate-400">
                      {humanize(game.evidenceStatus)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 px-4 py-4">
                <p className="text-xs font-semibold text-slate-300">
                  No replay evidence has been deliberately revealed yet.
                </p>

                <p className="mt-1 text-[11px] leading-4 text-slate-500">
                  Scores, winners, updated records, series outcomes, and
                  future-game information remain protected.
                </p>
              </div>
            )}
          </div>
        </div>

        <aside className="overflow-hidden rounded-2xl border border-cyan-900/60 bg-gradient-to-b from-slate-900 to-cyan-950 text-white shadow-sm">
          <div className="border-b border-cyan-900/60 px-5 py-5">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
              Provenance
            </p>

            <h2 className="mt-1 text-lg font-black">
              Evidence Integrity
            </h2>
          </div>

          <div className="space-y-5 p-5">
            <div>
              <p className="mb-2 text-[9px] font-black uppercase tracking-[0.16em] text-slate-500">
                Artifact Evidence
              </p>

              <Pill status={series?.evidence?.status}>
                {humanize(series?.evidence?.status)}
              </Pill>
            </div>

            <div>
              <p className="mb-2 text-[9px] font-black uppercase tracking-[0.16em] text-slate-500">
                Snapshot Integrity
              </p>

              <Pill status={snapshot.status}>
                {humanize(snapshot.status)}
              </Pill>
            </div>

            <div className="border-t border-cyan-900/60 pt-4">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-cyan-300">
                Certification
              </p>

              {missingEvidence.length ? (
                <ul className="mt-3 space-y-2">
                  {missingEvidence.map((item) => (
                    <li
                      key={item}
                      className="flex gap-2 text-xs leading-5 text-slate-300"
                    >
                      <span className="mt-0.5 text-amber-400">
                        •
                      </span>

                      <span>
                        {normalizePreviewText(item)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="mt-3 rounded-xl border border-emerald-800/70 bg-emerald-950/50 p-3">
                  <p className="text-xs font-semibold leading-5 text-emerald-200">
                    Pre-series snapshot integrity is intact.
                  </p>
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-cyan-800/60 bg-cyan-950/60 p-4">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-cyan-300">
                BIE Contract
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-300">
                Unsupported intelligence remains evidence gated rather than
                being presented as known before Game 1.
              </p>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}
