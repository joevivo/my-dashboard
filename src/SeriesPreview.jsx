import React, { useEffect, useMemo, useState } from "react";
import { getStratTeamMark } from "./strat/teamIdentityRegistry";

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
      ? "h-24 w-24 sm:h-28 sm:w-28 lg:h-32 lg:w-32"
      : "h-20 w-20";

  return (
    <div
      className={`flex ${sizeClass} shrink-0 items-center justify-center overflow-hidden rounded-2xl border shadow-sm ${palette}`}
      aria-label={`${mark?.teamName || "Team"} mark`}
    >
      {mark?.logoPath && !imageFailed ? (
        <img
          src={mark.logoPath}
          alt=""
          className="h-full w-full object-contain p-2"
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

  return (
    <section
      data-bie-surface="key-players"
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
            Key Players
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
            Compare both teams on the same batting and pitching measures, with official top-three league context.
          </p>
        </div>

        <div className="flex flex-wrap gap-4">
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

      <div className="mt-5 grid gap-6 lg:grid-cols-2">
        <div className="space-y-5">
          <h3 className="font-black text-slate-900 dark:text-white">
            {teamName}
          </h3>

          <LeagueLeaderSummary
            players={teamPlayers}
          />

          <PlayerList
            title={`Top Hitters · ${hitterMetric.label}`}
            rows={hitterRowsFor(
              teamPlayers,
            )}
            metricConfig={
              hitterMetric
            }
          />

          <PlayerList
            title={`Top Pitchers · ${pitcherMetric.label}`}
            rows={pitcherRowsFor(
              teamPlayers,
            )}
            metricConfig={
              pitcherMetric
            }
          />
        </div>

        <div className="space-y-5">
          <h3 className="font-black text-slate-900 dark:text-white">
            {opponentName}
          </h3>

          <LeagueLeaderSummary
            players={opponentPlayers}
          />

          <PlayerList
            title={`Top Hitters · ${hitterMetric.label}`}
            rows={hitterRowsFor(
              opponentPlayers,
            )}
            metricConfig={
              hitterMetric
            }
          />

          <PlayerList
            title={`Top Pitchers · ${pitcherMetric.label}`}
            rows={pitcherRowsFor(
              opponentPlayers,
            )}
            metricConfig={
              pitcherMetric
            }
          />
        </div>
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
      !selection?.teamId ||
      !selection?.seriesId
    ) {
      return null;
    }

    return (
      `${apiBase}/api/strat/league/${selection.leagueId}` +
      `/team/${selection.teamId}/series-preview/` +
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
              BIE Series Preview
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

        <div className="relative overflow-hidden px-5 py-8 sm:px-6 lg:px-8">
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
          >
            <div className="absolute -left-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-cyan-500/15 blur-3xl" />
            <div className="absolute -right-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-rose-500/15 blur-3xl" />
          </div>

          <div className="relative grid items-center gap-8 lg:grid-cols-[1fr_minmax(320px,0.9fr)_1fr]">
            <div className="flex items-center gap-5">
              <TeamIdentityMark
                key={teamMark?.teamId || "aquarium"}
                mark={teamMark}
                tone="teal"
              />

              <div className="min-w-0">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                  Home Team
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
                Current Matchup
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
                  Away Team
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

      {outlook ? (
        <section
          data-bie-surface="series-intelligence"
          className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-950 text-white shadow-xl"
        >
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 bg-gradient-to-r from-cyan-950/80 via-slate-950 to-rose-950/40 px-5 py-5 sm:px-6">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                Series Intelligence
              </p>

              <h2 className="mt-1 text-2xl font-black tracking-tight text-white">
                {humanize(outlook.classification)}
              </h2>
            </div>

            <Pill status={outlook.status}>
              {humanize(outlook.confidence || outlook.status)}
            </Pill>
          </div>

          <div className="p-5 sm:p-6">
            <p className="max-w-4xl text-sm leading-6 text-slate-300">
              {displayOutlookSynopsis}
            </p>

            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-cyan-900/70 bg-cyan-950/50 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-cyan-300">
                  Series State
                </p>

                <p className="mt-2 text-sm font-black text-white">
                  {humanize(outlook.classification)}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-700 bg-slate-900 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">
                  Edge
                </p>

                <p className="mt-2 text-sm font-black text-white">
                  {outlook.edge?.text || "Evidence gated"}
                </p>
              </div>

              <div className="rounded-2xl border border-amber-900/70 bg-amber-950/30 p-4">
                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-amber-300">
                  Watch
                </p>

                <p className="mt-2 text-sm font-black text-white">
                  {outlook.watch?.text || "Evidence gated"}
                </p>
              </div>
            </div>
          </div>
        </section>
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
                Season-to-date position relative to the full league. Lower rank numbers are better.
              </p>
            </div>

            <span className="rounded-full border border-slate-200 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-slate-500 dark:border-slate-700 dark:text-slate-300">
              {leagueContext?.leagueTeamCount
                ? `${leagueContext.leagueTeamCount} teams`
                : "League context"}
            </span>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <LeaguePositionTeamCard
              name={aquariumDisplayName}
              profile={teamProfile}
              teamCount={
                leagueContext?.leagueTeamCount
              }
            />

            <LeaguePositionTeamCard
              name={opponentDisplayName}
              profile={opponentProfile}
              teamCount={
                leagueContext?.leagueTeamCount
              }
            />
          </div>

          <p className="mt-3 text-[10px] leading-4 text-slate-400">
            Manager usage is descriptive context, not a quality ranking.
          </p>
        </section>
      ) : null}
      {playerIntelligence?.status === "AVAILABLE" ? (
        <KeyPlayersPanel
          teamName={aquariumDisplayName}
          opponentName={opponentDisplayName}
          teamPlayers={teamPlayers}
          opponentPlayers={opponentPlayers}
        />
      ) : null}
      <section>
        <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
          Matchup Intelligence
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
            </div>          ) : (
            <GatedModule
              title="Pitching Matchup"
              detail="Probable starters, bullpen availability, and workload remain evidence gated until captured."
            />
          )}
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
          ) : (
            <GatedModule
              title="Current Offensive Threats"
              detail="Projected lineups, platoon edges, and card-split matchups remain evidence gated."
            />
          )}
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
          ) : (
            <GatedModule
              title="Readiness & Environment"
              status="NOT_CAPTURED"
              detail="Injuries, roster constraints, and park effects are not yet captured in the canonical series artifact."
            />
          )}
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
          ) : (
            <GatedModule
              title="Manager's Notebook"
              detail="Managerial recommendations will appear only when they are traceable to supporting evidence."
            />
          )}
        </div>
      </section>

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
