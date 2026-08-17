function numberValue(value) {
  const numeric = Number(value);

  return Number.isFinite(numeric)
    ? numeric
    : null;
}

function categoryLabel(row) {
  const values = [
    row?.categoryName,
    row?.categoryKey,
  ]
    .map((value) =>
      String(value || "")
        .trim()
        .toUpperCase()
        .replace(/\\s+/g, " ")
    )
    .filter(Boolean);

  const canonical = new Map([
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

  for (const value of values) {
    if (canonical.has(value)) {
      return canonical.get(value);
    }
  }

  return null;
}

function categoryPriority(row) {
  const label =
    categoryLabel(row);

  const section =
    String(
      row?.section || "",
    ).toLowerCase();

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

  return section === "pitchers"
    ? pitcherPriority[label] ?? 50
    : hitterPriority[label] ?? 50;
}

function formatLeaderValue(row) {
  const label =
    categoryLabel(row);

  const rateLabels =
    new Set([
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
    const raw =
      String(
        row.valueRaw
      ).trim();

    return rateLabels.has(label)
      ? raw.replace(
          /^0(?=\\.)/,
          ""
        )
      : raw;
  }

  const value =
    numberValue(
      row?.valueNumeric
    );

  if (value === null) {
    return "—";
  }

  if (rateLabels.has(label)) {
    return value
      .toFixed(3)
      .replace(
        /^0(?=\\.)/,
        ""
      );
  }

  if (
    label === "ERA" ||
    label === "WHIP"
  ) {
    return value.toFixed(2);
  }

  return String(value);
}

function seriesRelevance({
  section,
  category,
}) {
  if (section === "pitchers") {
    if (category === "ERA") {
      return "Run-prevention anchor who can change the shape of the series.";
    }

    if (category === "WHIP") {
      return "Limits traffic; fewer free baserunners raises the pressure on every scoring chance.";
    }

    if (category === "SO") {
      return "Strikeout ability can take balls in play—and the defense—out of the equation.";
    }

    if (category === "SV") {
      return "Late-inning leverage arm if the series reaches close-game territory.";
    }

    if (category === "W") {
      return "A leading rotation result signal and a potential series-impact arm.";
    }

    return "Pitching performance makes this arm relevant to the series plan.";
  }

  if (
    ["OPS", "SLG", "HR"].includes(
      category,
    )
  ) {
    return "Extra-base damage makes this bat a primary run-production threat.";
  }

  if (category === "OBP") {
    return "On-base pressure creates traffic and forces the pitching staff to work from the stretch.";
  }

  if (category === "BA") {
    return "Consistent hit production makes this bat difficult to pitch around.";
  }

  if (
    ["RBI", "R"].includes(category)
  ) {
    return "Run-production profile makes this bat central to the lineup's scoring pressure.";
  }

  return "Season production makes this hitter relevant to the series plan.";
}

function leaderImpactPlayers(players) {
  const appearances =
    Array.isArray(
      players?.leagueLeaderAppearances
    )
      ? players.leagueLeaderAppearances
      : [];

  const secondaryLabel = (row) => {
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
        .replace(/\\s+/g, " ");

    if (
      !raw ||
      raw.includes(" VS.") ||
      raw.includes(" VS ") ||
      raw.startsWith("VS ") ||
      raw.includes("VERSUS") ||
      raw.includes("OPPONENT SB")
    ) {
      return null;
    }

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
  };

  const primaryRows =
    appearances
      .filter((row) => {
        const rank =
          numberValue(
            row?.rank
          );

        return (
          rank !== null &&
          rank >= 1 &&
          rank <= 3 &&
          (
            row?.section === "hitters" ||
            row?.section === "pitchers"
          ) &&
          Boolean(
            categoryLabel(row)
          ) &&
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
                ].includes(
                  categoryLabel(row)
                )
              : [
                  "ERA",
                  "WHIP",
                  "SO",
                  "W",
                  "SV",
                ].includes(
                  categoryLabel(row)
                )
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

  //
  // One candidate per player/category.
  // This lets selection choose a different category
  // for the same player when that improves diversity.
  //
  const seen =
    new Set();

  const candidates = [];

  for (const row of primaryRows) {
    const playerName =
      String(
        row?.playerName || ""
      ).trim();

    const category =
      categoryLabel(row);

    if (
      !playerName ||
      !category
    ) {
      continue;
    }

    const identity =
      `${playerName}::${category}`;

    if (seen.has(identity)) {
      continue;
    }

    seen.add(identity);

    const secondary = [];
    const secondarySeen =
      new Set();

    const playerRows =
      appearances
        .filter((other) => {
          const rank =
            numberValue(
              other?.rank
            );

          return (
            other?.playerName ===
              playerName &&
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

    for (const other of playerRows) {
      const label =
        secondaryLabel(other);

      if (
        !label ||
        label === category ||
        secondarySeen.has(label)
      ) {
        continue;
      }

      secondarySeen.add(label);

      secondary.push({
        category: label,
        rank:
          Number(other.rank),
      });

      if (
        secondary.length >= 2
      ) {
        break;
      }
    }

    candidates.push({
      playerName,
      section: row.section,
      category,
      value:
        formatLeaderValue(row),
      rank:
        Number(row.rank),
      source:
        "LEAGUE_RANK",
      secondary,
    });
  }

  return candidates;
}

function bestHitterFallback(
  players,
  usedNames,
) {
  const hitters =
    Array.isArray(players?.hitters)
      ? [...players.hitters]
      : [];

  const available =
    hitters.filter(
      (row) =>
        !usedNames.has(
          row?.playerName
        )
    );

  const baseballRate = (value) =>
    Number(value)
      .toFixed(3)
      .replace(
        /^0(?=\\.)/,
        ""
      );

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
      const row =
        ranked[0];

      return {
        playerName:
          row.playerName,
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
        position:
          row.position || null,
        secondary: [],
      };
    }
  }

  return null;
}

function bestPitcherFallback(
  players,
  usedNames,
) {
  const pitchers =
    Array.isArray(players?.pitchers)
      ? [...players.pitchers]
      : [];

  const available =
    pitchers.filter(
      (row) =>
        !usedNames.has(
          row?.playerName,
        ),
    );

  const eraEligible =
    available
      .filter(
        (row) =>
          numberValue(row?.ERA) !==
          null,
      )
      .sort(
        (a, b) =>
          Number(a.ERA) -
          Number(b.ERA),
      );

  if (eraEligible.length) {
    const row =
      eraEligible[0];

    return {
      playerName:
        row.playerName,
      section: "pitchers",
      category: "ERA",
      value:
        Number(
          row.ERA,
        ).toFixed(2),
      rank: null,
      source:
        "SEASON_PERFORMANCE",
      position:
        row.throws
          ? `${row.throws}HP`
          : "P",
      secondary: [],
    };
  }

  return null;
}

function buildImpactPlayers(players) {
  const leaders =
    leaderImpactPlayers(players);

  const impacts = [];
  const usedNames =
    new Set();

  const usedCategories =
    new Set();

  const add = (impact) => {
    if (
      !impact ||
      usedNames.has(
        impact.playerName
      )
    ) {
      return false;
    }

    impacts.push(impact);

    usedNames.add(
      impact.playerName
    );

    if (impact.category) {
      usedCategories.add(
        impact.category
      );
    }

    return true;
  };

  const bestLeaderFor =
    (section) =>
      leaders.find(
        (row) =>
          row.section === section
      ) || null;

  //
  // Establish hitting/pitching representation
  // from actual league-rank evidence first.
  //
  add(
    bestLeaderFor(
      "hitters"
    )
  );

  add(
    bestLeaderFor(
      "pitchers"
    )
  );

  //
  // If either discipline lacks ranked evidence,
  // fill that discipline with season evidence
  // before consuming all three slots elsewhere.
  //
  if (
    !impacts.some(
      (row) =>
        row.section === "pitchers"
    ) &&
    impacts.length < 3
  ) {
    add(
      bestPitcherFallback(
        players,
        usedNames
      )
    );
  }

  if (
    !impacts.some(
      (row) =>
        row.section === "hitters"
    ) &&
    impacts.length < 3
  ) {
    add(
      bestHitterFallback(
        players,
        usedNames
      )
    );
  }

  //
  // Third ranked signal:
  // first prefer an unused player AND a new category.
  //
  while (
    impacts.length < 3
  ) {
    const remaining =
      leaders.filter(
        (row) =>
          !usedNames.has(
            row.playerName
          )
      );

    if (!remaining.length) {
      break;
    }

    const diverse =
      remaining.find(
        (row) =>
          !usedCategories.has(
            row.category
          )
      );

    if (
      !add(
        diverse ||
        remaining[0]
      )
    ) {
      break;
    }
  }

  //
  // Final season fallbacks if ranked evidence
  // still cannot fill three cards.
  //
  while (
    impacts.length < 3
  ) {
    const hitter =
      bestHitterFallback(
        players,
        usedNames
      );

    if (add(hitter)) {
      continue;
    }

    const pitcher =
      bestPitcherFallback(
        players,
        usedNames
      );

    if (add(pitcher)) {
      continue;
    }

    break;
  }

  return impacts.slice(
    0,
    3
  );
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
    <div
      className={`rounded-2xl border bg-slate-50 p-4 dark:bg-slate-950/40 ${border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p
            className={`text-[8px] font-black uppercase tracking-[0.14em] ${accent}`}
          >
            {sectionLabel}
          </p>

          <h4 className="mt-1 truncate text-sm font-black text-slate-950 dark:text-white">
            {impact?.playerName ||
              "Unknown player"}
          </h4>
        </div>

        {impact?.rank ? (
          <span className="shrink-0 rounded-full bg-slate-900 px-2 py-1 text-[8px] font-black uppercase tracking-[0.08em] text-white dark:bg-white dark:text-slate-950">
            #{impact.rank} League
          </span>
        ) : (
          <span className="shrink-0 rounded-full border border-slate-200 px-2 py-1 text-[8px] font-black uppercase tracking-[0.08em] text-slate-400 dark:border-slate-700">
            Season
          </span>
        )}
      </div>

      <div className="mt-4 flex items-end justify-between gap-4">
        <div>
          <p className="text-3xl font-black tabular-nums tracking-tight text-slate-950 dark:text-white">
            {impact?.value || "—"}
          </p>

          <p className="mt-1 text-[9px] font-black uppercase tracking-[0.13em] text-slate-500 dark:text-slate-400">
            {impact?.category ||
              "Stat"}
          </p>
        </div>

        {impact?.secondary?.length ? (
          <div className="text-right">
            {impact.secondary.map(
              (secondary) => (
                <p
                  key={`${secondary.category}-${secondary.rank}`}
                  className="text-[8px] font-bold uppercase tracking-[0.08em] text-slate-400"
                >
                  #{secondary.rank}{" "}
                  {secondary.category}
                </p>
              ),
            )}
          </div>
        ) : null}
      </div>

      <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
        <p className="text-[8px] font-black uppercase tracking-[0.11em] text-slate-400">
          Series relevance
        </p>

        <p className="mt-1 text-[10px] font-semibold leading-4 text-slate-600 dark:text-slate-300">
          {seriesRelevance({
            section:
              impact?.section,
            category:
              impact?.category,
          })}
        </p>
      </div>
    </div>
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
      <div className="mb-4">
        <p
          className={`text-[9px] font-black uppercase tracking-[0.15em] ${roleTone}`}
        >
          {role}
        </p>

        <h3 className="mt-1 text-base font-black text-slate-950 dark:text-white">
          {name}
        </h3>
      </div>

      {impacts.length ? (
        <div className="grid gap-3 xl:grid-cols-3 lg:grid-cols-1">
          {impacts.map(
            (impact, index) => (
              <ImpactCard
                key={`${impact.playerName}-${impact.category}-${index}`}
                impact={impact}
                tone={tone}
              />
            ),
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-200 p-4 text-xs font-semibold text-slate-400 dark:border-slate-700">
          No player-impact evidence available in the frozen preview.
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
      data-bie-polish="impact-players-v1"
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800 sm:px-5">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
            Impact Players
          </p>

          <p className="mt-0.5 text-[11px] font-medium text-slate-500 dark:text-slate-400">
            League-rank signals first; season production fills evidence gaps.
          </p>
        </div>

        <span className="rounded-full border border-slate-200 px-2 py-1 text-[8px] font-black uppercase tracking-[0.09em] text-slate-400 dark:border-slate-700">
          Actual stat · rank · series relevance
        </span>
      </div>

      <div className="grid lg:grid-cols-2 lg:divide-x lg:divide-slate-200 dark:lg:divide-slate-800">
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

      <p className="border-t border-slate-200 bg-slate-50 px-5 py-2.5 text-[8px] font-bold leading-4 text-slate-400 dark:border-slate-800 dark:bg-slate-950/40">
        League rank is shown only when supplied by frozen league-leader evidence. “Season” identifies a production fallback, not a fabricated league rank.
      </p>
    </section>
  );
}