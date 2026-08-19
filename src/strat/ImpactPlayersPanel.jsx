function numberValue(value) {
  const numeric = Number(value);

  return Number.isFinite(numeric)
    ? numeric
    : null;
}

const CATEGORY_LABELS = new Map([
  ["OPS", "OPS"],
  ["ON-BASE PLUS SLUGGING", "OPS"],
  ["ON BASE PLUS SLUGGING", "OPS"],
  ["ON-BASE PLUS SLUGGING PERCENTAGE", "OPS"],
  ["OBP", "OBP"],
  ["ON-BASE PERCENTAGE", "OBP"],
  ["ON BASE PERCENTAGE", "OBP"],
  ["SLG", "SLG"],
  ["SLUGGING PERCENTAGE", "SLG"],
  ["BA", "BA"],
  ["BATTING AVERAGE", "BA"],
  ["HR", "HR"],
  ["HOME RUNS", "HR"],
  ["RBI", "RBI"],
  ["RUNS BATTED IN", "RBI"],
  ["R", "R"],
  ["RUNS", "R"],
  ["RUNS SCORED", "R"],
  ["ERA", "ERA"],
  ["EARNED RUN AVERAGE", "ERA"],
  ["WHIP", "WHIP"],
  ["SO", "SO"],
  ["STRIKEOUTS", "SO"],
  ["W", "W"],
  ["WINS", "W"],
  ["SV", "SV"],
  ["SAVES", "SV"],
]);

const LONG_CATEGORY_LABELS = {
  OPS: "OPS",
  OBP: "on-base percentage",
  SLG: "slugging percentage",
  BA: "batting average",
  HR: "home runs",
  RBI: "RBI",
  R: "runs scored",
  ERA: "ERA",
  WHIP: "WHIP",
  SO: "strikeouts",
  W: "wins",
  SV: "saves",
  TB: "total bases",
  H: "hits",
  "2B": "doubles",
  "3B": "triples",
  IP: "innings pitched",
  "K/BB": "K/BB",
  "H/9": "H/9",
  "BB/9": "BB/9",
};

function categoryLabel(row) {
  const values = [
    row?.categoryName,
    row?.categoryKey,
  ]
    .map((value) =>
      String(value || "")
        .trim()
        .toUpperCase()
        .replace(/\s+/g, " ")
    )
    .filter(Boolean);

  for (const value of values) {
    if (CATEGORY_LABELS.has(value)) {
      return CATEGORY_LABELS.get(value);
    }
  }

  return null;
}

function categoryPriority(row) {
  const label = categoryLabel(row);

  const hitterPriority = {
    OPS: 0,
    OBP: 1,
    SLG: 2,
    BA: 3,
    HR: 4,
    RBI: 5,
    R: 6,
  };

  const pitcherPriority = {
    ERA: 0,
    WHIP: 1,
    SO: 2,
    W: 3,
    SV: 4,
  };

  return row?.section === "pitchers"
    ? pitcherPriority[label] ?? 50
    : hitterPriority[label] ?? 50;
}

function formatLeaderValue(row) {
  const label = categoryLabel(row);

  const rateLabels = new Set([
    "OPS",
    "OBP",
    "SLG",
    "BA",
  ]);

  if (
    row?.valueRaw !== null &&
    row?.valueRaw !== undefined &&
    String(row.valueRaw).trim() !== ""
  ) {
    const raw = String(row.valueRaw).trim();

    return rateLabels.has(label)
      ? raw.replace(/^0(?=\.)/, "")
      : raw;
  }

  const value = numberValue(row?.valueNumeric);

  if (value === null) {
    return "—";
  }

  if (rateLabels.has(label)) {
    return value
      .toFixed(3)
      .replace(/^0(?=\.)/, "");
  }

  if (
    label === "ERA" ||
    label === "WHIP"
  ) {
    return value.toFixed(2);
  }

  return String(value);
}

function splitPlayerName(value) {
  const text = String(value || "").trim();

  if (!text) {
    return {
      first: "",
      last: "",
    };
  }

  if (text.includes(",")) {
    const pieces = text.split(",");
    const last = pieces.shift()?.trim() || "";
    const first = pieces.join(",").trim();

    return {
      first,
      last,
    };
  }

  const compactInitial = text.match(
    /^([A-Za-z])\.?\s*([A-Za-z][A-Za-z'.-]+)$/
  );

  if (compactInitial) {
    return {
      first: compactInitial[1],
      last: compactInitial[2],
    };
  }

  const pieces = text
    .split(/\s+/)
    .filter(Boolean);

  if (pieces.length === 1) {
    return {
      first: "",
      last: pieces[0],
    };
  }

  return {
    first: pieces
      .slice(0, -1)
      .join(" "),
    last: pieces[pieces.length - 1],
  };
}

function normalizedNamePart(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function naturalPlayerName(value) {
  const {
    first,
    last,
  } = splitPlayerName(value);

  if (!last) {
    return String(value || "").trim();
  }

  if (!first) {
    return last;
  }

  const firstText =
    first.length === 1
      ? `${first}.`
      : first;

  return `${firstText} ${last}`;
}

function rosterNames(players) {
  return [
    ...(Array.isArray(players?.hitters)
      ? players.hitters
      : []),
    ...(Array.isArray(players?.pitchers)
      ? players.pitchers
      : []),
  ]
    .map(
      (row) =>
        row?.playerName ||
        row?.name ||
        ""
    )
    .map((value) =>
      String(value || "").trim()
    )
    .filter(Boolean);
}

function resolvePlayerName(
  sourceName,
  players,
) {
  const source =
    splitPlayerName(sourceName);

  const sourceLast =
    normalizedNamePart(source.last);

  const sourceFirst =
    normalizedNamePart(source.first);

  if (!sourceLast) {
    return naturalPlayerName(sourceName);
  }

  const candidates =
    rosterNames(players)
      .filter((candidate) => {
        const parsed =
          splitPlayerName(candidate);

        const candidateLast =
          normalizedNamePart(parsed.last);

        const candidateFirst =
          normalizedNamePart(parsed.first);

        if (
          candidateLast !== sourceLast
        ) {
          return false;
        }

        if (!sourceFirst) {
          return true;
        }

        if (!candidateFirst) {
          return false;
        }

        if (sourceFirst.length === 1) {
          return (
            candidateFirst[0] ===
            sourceFirst[0]
          );
        }

        return (
          candidateFirst === sourceFirst
        );
      });

  if (candidates.length === 1) {
    return naturalPlayerName(
      candidates[0],
    );
  }

  return naturalPlayerName(
    sourceName,
  );
}

function playerIdentityKey(
  sourceName,
  players,
) {
  return resolvePlayerName(
    sourceName,
    players,
  )
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function secondaryLabel(row) {
  const canonical =
    categoryLabel(row);

  if (canonical) {
    return canonical;
  }

  const raw =
    String(
      row?.categoryName ||
      row?.categoryKey ||
      ""
    )
      .trim()
      .toUpperCase()
      .replace(/\s+/g, " ");

  const safeSecondary =
    new Map([
      ["TOTAL BASES", "TB"],
      ["HITS", "H"],
      ["DOUBLES", "2B"],
      ["TRIPLES", "3B"],
      ["INNINGS PITCHED", "IP"],
      ["STRIKEOUTS/WALKS", "K/BB"],
      ["STRIKEOUTS / WALKS", "K/BB"],
      ["HITS / 9 INNINGS", "H/9"],
      ["BB / 9 INNINGS", "BB/9"],
    ]);

  return (
    safeSecondary.get(raw) ||
    null
  );
}

function leaderImpactPlayers(players) {
  const appearances =
    Array.isArray(
      players?.leagueLeaderAppearances
    )
      ? players.leagueLeaderAppearances
      : [];

  const primaryRows =
    appearances
      .filter((row) => {
        const rank =
          numberValue(row?.rank);

        const category =
          categoryLabel(row);

        return (
          rank !== null &&
          rank >= 1 &&
          rank <= 3 &&
          (
            row?.section === "hitters" ||
            row?.section === "pitchers"
          ) &&
          Boolean(category) &&
          (
            row?.section === "hitters"
              ? [
                  "OPS",
                  "OBP",
                  "SLG",
                  "BA",
                  "HR",
                  "RBI",
                  "R",
                ].includes(category)
              : [
                  "ERA",
                  "WHIP",
                  "SO",
                  "W",
                  "SV",
                ].includes(category)
          )
        );
      })
      .sort((a, b) => {
        const rankDifference =
          Number(a.rank) -
          Number(b.rank);

        if (rankDifference !== 0) {
          return rankDifference;
        }

        const categoryDifference =
          categoryPriority(a) -
          categoryPriority(b);

        if (categoryDifference !== 0) {
          return categoryDifference;
        }

        return String(
          a?.playerName || ""
        ).localeCompare(
          String(
            b?.playerName || ""
          )
        );
      });

  return primaryRows.map((row) => {
    const secondary = [];
    const secondarySeen =
      new Set();

    const samePlayerRows =
      appearances
        .filter((other) => {
          const rank =
            numberValue(other?.rank);

          return (
            playerIdentityKey(
              other?.playerName,
              players,
            ) ===
              playerIdentityKey(
                row?.playerName,
                players,
              ) &&
            rank !== null &&
            rank >= 1 &&
            rank <= 3
          );
        })
        .sort(
          (a, b) =>
            Number(a.rank) -
            Number(b.rank)
        );

    for (const other of samePlayerRows) {
      const label =
        secondaryLabel(other);

      if (
        !label ||
        label === categoryLabel(row) ||
        secondarySeen.has(label)
      ) {
        continue;
      }

      secondarySeen.add(label);

      secondary.push({
        category: label,
        rank: Number(other.rank),
      });

      if (secondary.length >= 2) {
        break;
      }
    }

    return {
      playerName:
        row?.playerName || "",
      displayName:
        resolvePlayerName(
          row?.playerName,
          players,
        ),
      section: row?.section,
      category:
        categoryLabel(row),
      value:
        formatLeaderValue(row),
      rank:
        Number(row.rank),
      source: "LEAGUE_RANK",
      secondary,
    };
  });
}

function bestHitterFallback(
  players,
  usedKeys,
) {
  const hitters =
    Array.isArray(players?.hitters)
      ? [...players.hitters]
      : [];

  const available =
    hitters.filter(
      (row) =>
        !usedKeys.has(
          playerIdentityKey(
            row?.playerName,
            players,
          )
        )
    );

  const baseballRate = (value) =>
    Number(value)
      .toFixed(3)
      .replace(/^0(?=\.)/, "");

  const metrics = [
    {
      key: "OPS",
      label: "OPS",
      format: baseballRate,
    },
    {
      key: "HR",
      label: "HR",
      format: (value) =>
        String(value),
    },
    {
      key: "OBP",
      label: "OBP",
      format: baseballRate,
    },
  ];

  for (const metric of metrics) {
    const ranked =
      available
        .filter(
          (row) =>
            numberValue(
              row?.[metric.key]
            ) !== null
        )
        .sort(
          (a, b) =>
            Number(
              b[metric.key]
            ) -
            Number(
              a[metric.key]
            )
        );

    if (ranked.length) {
      const row = ranked[0];

      return {
        playerName:
          row.playerName,
        displayName:
          resolvePlayerName(
            row.playerName,
            players,
          ),
        section: "hitters",
        category:
          metric.label,
        value:
          metric.format(
            row[metric.key]
          ),
        rank: null,
        source:
          "SEASON_PERFORMANCE",
        secondary: [],
      };
    }
  }

  return null;
}

function bestPitcherFallback(
  players,
  usedKeys,
) {
  const pitchers =
    Array.isArray(players?.pitchers)
      ? [...players.pitchers]
      : [];

  const available =
    pitchers.filter(
      (row) =>
        !usedKeys.has(
          playerIdentityKey(
            row?.playerName,
            players,
          )
        )
    );

  const ranked =
    available
      .filter(
        (row) =>
          numberValue(row?.ERA) !==
          null
      )
      .sort(
        (a, b) =>
          Number(a.ERA) -
          Number(b.ERA)
      );

  if (!ranked.length) {
    return null;
  }

  const row = ranked[0];

  return {
    playerName:
      row.playerName,
    displayName:
      resolvePlayerName(
        row.playerName,
        players,
      ),
    section: "pitchers",
    category: "ERA",
    value:
      Number(row.ERA).toFixed(2),
    rank: null,
    source:
      "SEASON_PERFORMANCE",
    secondary: [],
  };
}

function buildImpactPlayers(players) {
  const leaders =
    leaderImpactPlayers(players);

  const impacts = [];
  const usedKeys =
    new Set();

  const add = (impact) => {
    if (!impact) {
      return false;
    }

    const key =
      playerIdentityKey(
        impact.playerName,
        players,
      );

    if (
      !key ||
      usedKeys.has(key)
    ) {
      return false;
    }

    impacts.push({
      ...impact,
      displayName:
        impact.displayName ||
        resolvePlayerName(
          impact.playerName,
          players,
        ),
    });

    usedKeys.add(key);

    return true;
  };

  const hitterLeader =
    leaders.find(
      (row) =>
        row.section === "hitters"
    );

  const pitcherLeader =
    leaders.find(
      (row) =>
        row.section === "pitchers"
    );

  add(
    hitterLeader ||
    bestHitterFallback(
      players,
      usedKeys,
    )
  );

  add(
    pitcherLeader ||
    bestPitcherFallback(
      players,
      usedKeys,
    )
  );

  if (impacts.length < 2) {
    for (const candidate of leaders) {
      if (add(candidate)) {
        if (impacts.length >= 2) {
          break;
        }
      }
    }
  }

  if (impacts.length < 2) {
    add(
      bestHitterFallback(
        players,
        usedKeys,
      )
    );
  }

  if (impacts.length < 2) {
    add(
      bestPitcherFallback(
        players,
        usedKeys,
      )
    );
  }

  return impacts.slice(0, 2);
}

function metricLongLabel(value) {
  return (
    LONG_CATEGORY_LABELS[value] ||
    value ||
    "stat"
  );
}

function whyHere(impact) {
  const metric =
    metricLongLabel(
      impact?.category,
    );

  if (impact?.rank) {
    const secondaryRanks =
      Array.isArray(
        impact?.secondary,
      )
        ? impact.secondary
            .slice(0, 2)
            .map(
              (row) =>
                `#${row.rank} ${metricLongLabel(
                  row.category,
                )}`,
            )
        : [];

    return secondaryRanks.length
      ? `League #${impact.rank} in ${metric}; also ${secondaryRanks.join(
          ", ",
        )}.`
      : `League #${impact.rank} in ${metric}.`;
  }

  const playerGroup =
    impact?.section === "pitchers"
      ? "pitching"
      : "hitting";

  return `Strongest available club ${playerGroup} signal in ${metric} from the pregame season evidence.`;
}
function ImpactCard({
  impact,
  tone,
}) {
  const isTeam =
    tone === "team";

  const accent =
    isTeam
      ? "text-cyan-600 dark:text-cyan-300"
      : "text-rose-600 dark:text-rose-300";

  const border =
    isTeam
      ? "border-cyan-200 dark:border-cyan-900"
      : "border-rose-200 dark:border-rose-900";

  const sectionLabel =
    impact?.section === "pitchers"
      ? "Pitcher"
      : "Hitter";

  return (
    <article
      className={`rounded-2xl border bg-slate-50 p-4 dark:bg-slate-950/40 ${border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p
            className={`text-[9px] font-black uppercase tracking-[0.14em] ${accent}`}
          >
            {sectionLabel}
          </p>

          <h4 className="mt-1 text-base font-black leading-tight text-slate-950 dark:text-white">
            {impact?.displayName ||
              naturalPlayerName(
                impact?.playerName,
              ) ||
              "Unknown player"}
          </h4>
        </div>

        <span className="shrink-0 rounded-full border border-slate-200 px-2 py-1 text-[8px] font-black uppercase tracking-[0.08em] text-slate-500 dark:border-slate-700 dark:text-slate-400">
          {impact?.rank
            ? `#${impact.rank} league`
            : "Team season"}
        </span>
      </div>

      <div className="mt-3 flex items-end justify-between gap-4">
        <div>
          <p className="text-2xl font-black tabular-nums tracking-tight text-slate-950 dark:text-white">
            {impact?.value || "—"}
          </p>

          <p className="mt-0.5 text-[10px] font-black uppercase tracking-[0.11em] text-slate-500 dark:text-slate-400">
            {impact?.category ||
              "Stat"}
          </p>
        </div>

        {impact?.secondary?.length ? (
          <div className="space-y-0.5 text-right">
            {impact.secondary.map(
              (secondary) => (
                <p
                  key={`${secondary.category}-${secondary.rank}`}
                  className="text-[9px] font-bold text-slate-500 dark:text-slate-400"
                >
                  #{secondary.rank}{" "}
                  {metricLongLabel(
                    secondary.category,
                  )}
                </p>
              ),
            )}
          </div>
        ) : null}
      </div>

      <div className="mt-3 border-t border-slate-200 pt-2.5 dark:border-slate-800">
        <p className="text-[9px] font-black uppercase tracking-[0.11em] text-slate-400">
          Why he matters
        </p>

        <p className="mt-1 text-[11px] font-semibold leading-4 text-slate-600 dark:text-slate-300">
          {whyHere(impact)}
        </p>
      </div>
    </article>
  );
}

function TeamImpactColumn({
  role,
  name,
  players,
  tone,
}) {
  const impacts =
    buildImpactPlayers(players);

  const roleTone =
    tone === "team"
      ? "text-cyan-600 dark:text-cyan-300"
      : "text-rose-600 dark:text-rose-300";

  return (
    <div className="p-4 sm:p-5">
      <div className="mb-3">
        <p
          className={`text-[9px] font-black uppercase tracking-[0.15em] ${roleTone}`}
        >
          {role}
        </p>

        <h3 className="mt-1 text-base font-black leading-tight text-slate-950 dark:text-white">
          {name}
        </h3>
      </div>

      {impacts.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {impacts.map(
            (impact, index) => (
              <ImpactCard
                key={`${playerIdentityKey(
                  impact.playerName,
                  players,
                )}-${impact.category}-${index}`}
                impact={impact}
                tone={tone}
              />
            ),
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-200 p-4 text-xs font-semibold text-slate-400 dark:border-slate-700">
          No player-impact information is available for this preview.
        </div>
      )}
    </div>
  );
}

export default function ImpactPlayersPanel({
  teamName,
  opponentName,
  teamPlayers,
  opponentPlayers,
}) {
  return (
    <section
      data-bie-surface="impact-players"
      data-bie-polish="impact-players-v2"
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800 sm:px-5">
        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
          Impact Players
        </p>

        <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
          Two high-signal players per club; league leaders take priority.
        </p>
      </div>

      <div className="grid xl:grid-cols-2 xl:divide-x xl:divide-slate-200 dark:xl:divide-slate-800">
        <TeamImpactColumn
          role="Aquarium"
          name={teamName}
          players={teamPlayers}
          tone="team"
        />

        <TeamImpactColumn
          role="Opponent"
          name={opponentName}
          players={opponentPlayers}
          tone="opponent"
        />
      </div>
    </section>
  );
}