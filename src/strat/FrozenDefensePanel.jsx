function getPlayer(team, position) {
  const target =
    String(position || "").toUpperCase();

  return (
    (team?.players || [])
      .filter((player) => {
        const positions =
          String(
            player?.primaryPosition || "",
          )
            .toUpperCase()
            .split(/[\/,]/)
            .map((value) => value.trim());

        return positions.includes(target);
      })
      .sort((a, b) => {
        const aPrimary =
          Number(
            a?.xDefense
              ?.primaryPosition
              ?.xTotal,
          ) || 0;

        const bPrimary =
          Number(
            b?.xDefense
              ?.primaryPosition
              ?.xTotal,
          ) || 0;

        if (bPrimary !== aPrimary) {
          return bPrimary - aPrimary;
        }

        const aAll =
          Number(
            a?.xDefense
              ?.allPositions
              ?.xTotal,
          ) || 0;

        const bAll =
          Number(
            b?.xDefense
              ?.allPositions
              ?.xTotal,
          ) || 0;

        return bAll - aAll;
      })[0] || null
  );
}

function surname(name) {
  const raw =
    String(name || "").trim();

  return raw
    ? raw.split(",")[0]
    : "—";
}

function signed(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return number > 0
    ? `+${number}`
    : String(number);
}

function TeamDiamond({
  name,
  fieldingTeam,
  tone,
}) {
  const positions = [
    { key: "CF", left: 50, top: 14 },
    { key: "LF", left: 17, top: 29 },
    { key: "RF", left: 83, top: 29 },
    { key: "SS", left: 34, top: 51 },
    { key: "2B", left: 66, top: 51 },
    { key: "3B", left: 21, top: 70 },
    { key: "1B", left: 79, top: 70 },
    { key: "C", left: 50, top: 88 },
  ];

  const players =
    Object.fromEntries(
      positions.map(({ key }) => [
        key,
        getPlayer(
          fieldingTeam,
          key,
        ),
      ]),
    );

  const teamText =
    tone === "team"
      ? "text-cyan-600 dark:text-cyan-300"
      : "text-rose-600 dark:text-rose-300";

  const badge =
    tone === "team"
      ? "border-cyan-300 bg-cyan-50 text-cyan-950 dark:border-cyan-800 dark:bg-cyan-950/70 dark:text-cyan-100"
      : "border-rose-300 bg-rose-50 text-rose-950 dark:border-rose-800 dark:bg-rose-950/70 dark:text-rose-100";

  return (
    <div>
      <p
        className={`truncate text-center text-xs font-black uppercase tracking-[0.11em] ${teamText}`}
      >
        {name}
      </p>

      <div className="relative mx-auto mt-3 h-[330px] max-w-[520px] overflow-hidden rounded-2xl border border-emerald-800/25 bg-gradient-to-b from-emerald-50 to-amber-50 dark:from-emerald-950/45 dark:to-amber-950/20">
        <svg
          viewBox="0 0 350 245"
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
        >
          <path
            d="M175 13 C78 23 28 80 28 160 L175 232 L322 160 C322 80 272 23 175 13 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-emerald-700/30 dark:text-emerald-500/30"
          />

          <path
            d="M175 218 L94 154 L175 83 L256 154 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-amber-600/35"
          />

          <path
            d="M175 218 L175 83"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            strokeDasharray="4 5"
            className="text-slate-400/25"
          />
        </svg>

        {positions.map((position) => {
          const player =
            players[position.key];

          return (
            <div
              key={position.key}
              className="absolute -translate-x-1/2 -translate-y-1/2 text-center"
              style={{
                left: `${position.left}%`,
                top: `${position.top}%`,
              }}
            >
              <div
                className={`min-w-[76px] rounded-xl border px-2 py-1.5 shadow-sm ${badge}`}
              >
                <p className="text-[10px] font-black uppercase tracking-[0.07em]">
                  {position.key}
                </p>

                <p className="mt-0.5 whitespace-nowrap text-[12px] font-black tabular-nums leading-tight">
                  {player?.defense?.raw ||
                    "—"}
                </p>
              </div>

              <p className="mt-1 max-w-[100px] truncate text-[9px] font-bold text-slate-600 dark:text-slate-300">
                {surname(player?.name)}
              </p>
            </div>
          );
        })}
      </div>

      {/* DEFENSE_DUPLICATE_SUMMARY_TILES_REMOVED - diamond already carries the raw ratings. */}
    </div>
  );
}

function XDefense({
  teamName,
  opponentName,
  teamFielding,
  opponentFielding,
}) {
  const sides = [
    {
      name: teamName,
      tone:
        "text-cyan-600 dark:text-cyan-300",
      bar: "bg-cyan-500",
      x:
        teamFielding?.xDefense
          ?.allPositions,
    },
    {
      name: opponentName,
      tone:
        "text-rose-600 dark:text-rose-300",
      bar: "bg-rose-500",
      x:
        opponentFielding?.xDefense
          ?.allPositions,
    },
  ];

  const rates =
    sides.map((side) =>
      Number(side?.x?.xConversion),
    );

  return (
    <div
      data-bie-surface="x-defense-pairwise"
      className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950/40"
    >
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.12em] text-slate-600 dark:text-slate-200">
            X-Chance Defense
          </p>

          <p className="mt-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-300">
            ↑ Higher conversion is better
          </p>
        </div>

        <span className="rounded-full border border-slate-200 px-2 py-1 text-[9px] font-black uppercase tracking-[0.07em] text-slate-400 dark:border-slate-700">
          Pairwise
        </span>
      </div>

      <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-700">
        {sides.map((side, index) => {
          const rate =
            rates[index];

          const otherRate =
            rates[index === 0 ? 1 : 0];

          const edge =
            Number.isFinite(rate) &&
            Number.isFinite(otherRate) &&
            rate > otherRate;

          return (
            <div
              key={side.name}
              className="p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p
                  className={`truncate text-[11px] font-black uppercase tracking-[0.1em] ${side.tone}`}
                >
                  {side.name}
                </p>

                {edge ? (
                  <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-black uppercase tracking-[0.07em] text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                    Edge
                  </span>
                ) : null}
              </div>

              <p className="mt-2 text-3xl font-black tabular-nums text-slate-950 dark:text-white">
                {Number.isFinite(rate)
                  ? `${(
                      rate * 100
                    ).toFixed(1)}%`
                  : "—"}
              </p>

              <p className="mt-1 text-[11px] font-bold text-slate-600 dark:text-slate-300">
                {side.x
                  ? `${side.x.xOut}/${side.x.xTotal} X outs/chances`
                  : "X data unavailable"}
              </p>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className={`h-full rounded-full ${side.bar}`}
                  style={{
                    width:
                      Number.isFinite(rate)
                        ? `${Math.max(
                            0,
                            Math.min(
                              100,
                              rate * 100,
                            ),
                          )}%`
                        : "0%",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <p className="border-t border-slate-200 px-4 py-2.5 text-[10px] font-bold leading-5 text-slate-500 dark:border-slate-700 dark:text-slate-300">
        League-wide X rank is intentionally unavailable in the frozen six-team review dataset.
      </p>
    </div>
  );
}

export default function FrozenDefensePanel({
  teamName,
  opponentName,
  teamFielding,
  opponentFielding,
}) {
  return (
    <div
      data-bie-surface="defense-intelligence"
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:col-span-12"
    >
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500 dark:text-slate-300">
              Defense
            </p>

            <p className="mt-1 text-xs font-medium text-slate-600 dark:text-slate-300">
              Range, arms and actual X-chance conversion.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[9px] font-black uppercase tracking-[0.07em] text-violet-700 dark:bg-violet-950 dark:text-violet-300">
              Range ↓ lower better
            </span>

            <span className="rounded-full bg-amber-50 px-2 py-1 text-[9px] font-black uppercase tracking-[0.07em] text-amber-700 dark:bg-amber-950 dark:text-amber-300">
              Arm ↓ lower = stronger
            </span>

            <span className="rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-[0.07em] text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
              X ↑ higher better
            </span>
          </div>
        </div>
      </div>

      {teamFielding &&
      opponentFielding ? (
        <>
          <div className="grid gap-6 p-5 md:grid-cols-2">
            <TeamDiamond
              name={teamName}
              tone="team"
              fieldingTeam={
                teamFielding
              }
            />

            <TeamDiamond
              name={opponentName}
              tone="opponent"
              fieldingTeam={
                opponentFielding
              }
            />
          </div>

          <div className="px-4 pb-4">
            <XDefense
              teamName={teamName}
              opponentName={
                opponentName
              }
              teamFielding={
                teamFielding
              }
              opponentFielding={
                opponentFielding
              }
            />
          </div>

          <p className="border-t border-slate-200 bg-slate-50 px-4 py-2.5 text-[10px] font-bold leading-5 text-slate-600 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-300">
            Diamond uses the most-used defender at each primary position by observed primary-position X chances. Raw Strat range/arm/error ratings are preserved.
          </p>
        </>
      ) : (
        <p className="p-4 text-xs font-bold text-slate-400">
          Frozen fielding evidence unavailable.
        </p>
      )}
    </div>
  );
}