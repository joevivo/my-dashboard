import { useMemo, useState } from "react";
import { estimateLineupRunEnvironment } from "./engine/gameSimEngine";
import { parks1980 } from "./parks1980";

const sampleRoster = `CF R 2 Rickey Henderson 0.430 0.390 5 10
RF S 3 Reggie Smith 0.380 0.400 8 6
DH R 5 Jose Morales 0.320 0.380 8 1
1B L 4 Richie Hebner 0.390 0.340 6 3
C R 2 Brian Downing 0.430 0.390 5 3
3B R 3 Bill Madlock 0.360 0.410 6 4
LF S 1 Dave Collins 0.360 0.300 4 9
SS R 2 Dave Concepcion 0.310 0.350 3 7
2B R 3 Steve Papi 0.220 0.260 2 4
C L 4 Ron Hodges 0.300 0.360 2 2
C R 4 Dan Whitmer 0.240 0.230 2 2
2B R 4 Alan Bannister 0.300 0.340 3 6
3B S 4 Lenny Randle 0.390 0.420 3 8
RF L 2 Dave Parker 0.300 0.340 7 5
RF R 2 Juan Beniquez 0.240 0.220 3 6`;

function formatPercent(value) {
  return `${((Number(value) || 0) * 100).toFixed(1)}%`;
}

function formatRuns(value) {
  return Number(value || 0).toFixed(2);
}

function inferPitcherHand(pitchersText) {
  const firstLine = String(pitchersText || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)[0];

  if (!firstLine) return null;

  const tokens = firstLine.split(/\s+/);
  const hand = tokens[tokens.length - 1]?.toUpperCase();

  return hand === "L" ? "L" : "R";
}

export default function GameSimulator() {
  const defaultPark = parks1980.find((park) => park.name?.includes("Tiger"))?.name || parks1980[0]?.name || "";
  const [hittersText, setHittersText] = useState("");
    const [pitcherHand, setPitcherHand] = useState("R");
  const [pitcherHandSource, setPitcherHandSource] = useState("Manual default");
  const [lineupMode, setLineupMode] = useState("optimized");
  const [parkName, setParkName] = useState(defaultPark);
  const [sims, setSims] = useState(1000);
  const [opponentRuns, setOpponentRuns] = useState(4.5);
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState(null);

  const [savedTeams] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("stratLeagues") || "[]");
    } catch {
      return [];
    }
  });

  const [savedOpponents] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("stratOpponents") || "[]");
    } catch {
      return [];
    }
  });

  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [selectedOpponentId, setSelectedOpponentId] = useState("");

  const loadSavedTeam = (teamId) => {
    setSelectedTeamId(teamId);

    const team = savedTeams.find((item) => String(item.id) === String(teamId));
    if (!team) return;

    setHittersText(team.hittersText || "");
    if (team.ballpark) setParkName(team.ballpark);
    setResult(null);
    setComparison(null);
  };

    const loadSavedOpponent = (opponentId) => {
    setSelectedOpponentId(opponentId);

    const opponent = savedOpponents.find(
      (item) => String(item.id) === String(opponentId)
    );
    if (!opponent) return;

    if (opponent.ballpark) setParkName(opponent.ballpark);

    const inferredHand = inferPitcherHand(opponent.pitchersText);
    if (inferredHand) {
      setPitcherHand(inferredHand);
      setPitcherHandSource(`Auto-detected from ${opponent.name}`);
    }

    setResult(null);
    setComparison(null);
  };

  const hasRoster = hittersText.trim().length > 0;

  const distributionRows = useMemo(() => {
    return result?.runDistribution || [];
  }, [result]);

  const runSimulation = () => {
    const nextResult = estimateLineupRunEnvironment({
      hittersText,
      pitcherHand,
      parkName,
      sims,
      opponentRuns,
      lineupMode,
    });

    setResult(nextResult);
  };

  const compareLineups = () => {
    const optimized = estimateLineupRunEnvironment({
      hittersText,
      pitcherHand,
      parkName,
      sims,
      opponentRuns,
      lineupMode: "optimized",
    });

    const manual = estimateLineupRunEnvironment({
      hittersText,
      pitcherHand,
      parkName,
      sims,
      opponentRuns,
      lineupMode: "manual",
    });

    setComparison({
      optimized,
      manual,
      runDelta: optimized.avgRuns - manual.avgRuns,
      simRunDelta: optimized.simulatedAvgRuns - manual.simulatedAvgRuns,
      winDelta: optimized.winProbability - manual.winProbability,
    });

    setResult(optimized);
  };

  return (
    <div className="space-y-6">
      <div className="dashboard-panel p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Stratomatic Sim Lab
            </div>

            <h1 className="mt-2 text-2xl font-bold">Game Simulator</h1>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              Estimate a lineup run environment using the current card-aware lineup engine,
              1980 ballpark data, pitcher hand, and a lightweight run-distribution model.
              This is an MVP simulation layer, not a full dice/card rules engine yet. Use optimized mode to let the engine choose an order, or manual mode to simulate the first nine pasted rows exactly.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setHittersText(sampleRoster)}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            Load Sample Roster
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="dashboard-panel p-6 space-y-4">
          <div>
            <h2 className="text-xl font-bold">Simulation Inputs</h2>
            <p className="mt-1 text-sm text-slate-500">
              Paste hitter roster text, choose the opposing starter hand, and select the game park.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Saved team
              </label>

              <select
                value={selectedTeamId}
                onChange={(event) => loadSavedTeam(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">Manual / pasted roster</option>
                {savedTeams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name || "Unnamed Team"}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Saved opponent
              </label>

              <select
                value={selectedOpponentId}
                onChange={(event) => loadSavedOpponent(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">No saved opponent selected</option>
                {savedOpponents.map((opponent) => (
                  <option key={opponent.id} value={opponent.id}>
                    {opponent.name || "Unnamed Opponent"}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Hitter roster text
            </label>

            <textarea
              value={hittersText}
              onChange={(event) => setHittersText(event.target.value)}
              rows={14}
              placeholder="Format: POS BATS DEF NAME OBPvsR OBPvsL PWR SPD"
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-3 font-mono text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Lineup mode
              </label>

              <select
                value={lineupMode}
                onChange={(event) => setLineupMode(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="optimized">Optimize lineup from roster</option>
                <option value="manual">Use pasted order exactly</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Opposing pitcher hand
              </label>

              <select
                value={pitcherHand}
                onChange={(event) => {
                  setPitcherHand(event.target.value);
                  setPitcherHandSource("Manual override");
                }}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="R">Right-handed pitcher</option>
                <option value="L">Left-handed pitcher</option>
              </select>

              <p className="mt-1 text-xs text-slate-400">
                {pitcherHandSource}
              </p>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Ballpark
              </label>

              <select
                value={parkName}
                onChange={(event) => setParkName(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                {parks1980.map((park) => (
                  <option key={park.name} value={park.name}>
                    {park.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Simulated games
              </label>

              <input
                type="number"
                min="100"
                max="5000"
                step="100"
                value={sims}
                onChange={(event) => setSims(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
                Opponent runs allowed
              </label>

              <input
                type="number"
                min="1"
                max="10"
                step="0.1"
                value={opponentRuns}
                onChange={(event) => setOpponentRuns(event.target.value)}
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </div>
          </div>

                    <div className="grid gap-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={runSimulation}
              disabled={!hasRoster}
              className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Run Simulation
            </button>

            <button
              type="button"
              onClick={compareLineups}
              disabled={!hasRoster}
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Compare Optimized vs Manual
            </button>
          </div>
        </div>

        <div className="space-y-6">
          {comparison && <ComparisonPanel comparison={comparison} />}

          {!result ? (
            <div className="dashboard-panel p-6">
              <h2 className="text-xl font-bold">Simulation Results</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Add a roster and run the simulation to see projected runs, win estimate,
                lineup order, run distribution, and park notes.
              </p>
            </div>
          ) : (
            <>
              <div className="dashboard-panel p-6">
                <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h2 className="text-xl font-bold">Simulation Results</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {result.park.name} - {result.park.environment}
                    </p>
                  </div>

                  <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-900">
                    {result.inputs.sims.toLocaleString()} games
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-5">
                  <ResultStat label="Expected Runs" value={formatRuns(result.avgRuns)} />
                  <ResultStat label="Sim Avg Runs" value={formatRuns(result.simulatedAvgRuns)} />
                  <ResultStat label="Win Estimate" value={formatPercent(result.winProbability)} />
                  <ResultStat label="Low Run Rate" value={formatPercent(result.lowRunRate)} />
                  <ResultStat label="High Run Rate" value={formatPercent(result.highRunRate)} />
                </div>
              </div>

              <div className="dashboard-panel p-6">
                <h2 className="text-lg font-bold">Projected Lineup</h2>

                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs uppercase tracking-wide text-slate-400">
                      <tr>
                        <th className="py-2 pr-3">Slot</th>
                        <th className="py-2 pr-3">Player</th>
                        <th className="py-2 pr-3">Pos</th>
                        <th className="py-2 pr-3">Bats</th>
                        <th className="py-2 pr-3">OBP</th>
                        <th className="py-2 pr-3">Pwr</th>
                        <th className="py-2 pr-3">Spd</th>
                        <th className="py-2 pr-3">Score</th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {result.lineup.map((player) => (
                        <tr key={`${player.slot}-${player.name}`}>
                          <td className="py-2 pr-3 font-semibold">{player.slot}</td>
                          <td className="py-2 pr-3">{player.name}</td>
                          <td className="py-2 pr-3">{player.fieldPos}</td>
                          <td className="py-2 pr-3">{player.bats}</td>
                          <td className="py-2 pr-3">{player.obp ?? "-"}</td>
                          <td className="py-2 pr-3">{player.power ?? "-"}</td>
                          <td className="py-2 pr-3">{player.speed ?? "-"}</td>
                          <td className="py-2 pr-3">{player.score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="dashboard-panel p-6">
                  <h2 className="text-lg font-bold">Run Distribution</h2>

                  <div className="mt-4 space-y-2">
                    {distributionRows.map((row) => (
                      <div key={row.runs} className="grid grid-cols-[3rem_1fr_4rem] items-center gap-3 text-sm">
                        <div className="font-semibold">{row.runs}</div>
                        <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                          <div
                            className="h-full rounded-full bg-slate-900 dark:bg-slate-100"
                            style={{ width: `${Math.min(100, row.rate * 100)}%` }}
                          />
                        </div>
                        <div className="text-right text-slate-500">{formatPercent(row.rate)}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="dashboard-panel p-6">
                  <h2 className="text-lg font-bold">Notes</h2>

                  <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-500">
                    {result.notes.map((note, index) => (
                      <li key={`${note}-${index}`}>- {note}</li>
                    ))}
                  </ul>

                  <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800/70">
                    Park numbers: SI L/R {result.park.singlesLeft ?? "-"} / {result.park.singlesRight ?? "-"}
                    {" - "}
                    HR L/R {result.park.homeRunsLeft ?? "-"} / {result.park.homeRunsRight ?? "-"}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultStat({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/70">
      <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold">{value}</div>
    </div>
  );
}
function formatSignedRuns(value) {
  const number = Number(value || 0);
  const sign = number > 0 ? "+" : "";

  return `${sign}${formatRuns(number)}`;
}

function formatSignedPercent(value) {
  const number = Number(value || 0);
  const sign = number > 0 ? "+" : "";

  return `${sign}${formatPercent(number)}`;
}

function ComparisonMetric({ label, optimized, manual, delta, type = "runs" }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/70">
      <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
        {label}
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <div>
          <div className="text-xs text-slate-400">Optimized</div>
          <div className="font-bold">
            {type === "percent" ? formatPercent(optimized) : formatRuns(optimized)}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-400">Manual</div>
          <div className="font-bold">
            {type === "percent" ? formatPercent(manual) : formatRuns(manual)}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-400">Delta</div>
          <div className={`font-bold ${delta >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
            {type === "percent" ? formatSignedPercent(delta) : formatSignedRuns(delta)}
          </div>
        </div>
      </div>
    </div>
  );
}

function formatAbsoluteRuns(value) {
  return Math.abs(Number(value || 0)).toFixed(2);
}

function getComparisonVerdict(runDelta) {
  const delta = Number(runDelta || 0);
  const absoluteDelta = Math.abs(delta);
  const leader = delta >= 0 ? "Optimized lineup" : "Manual lineup";

  if (absoluteDelta < 0.1) {
    return {
      label: "Essentially even",
      tone: "text-slate-500",
      message:
        "These lineups are within normal simulation noise. Use matchup preference, fatigue, defense, or managerial rules as the tiebreaker.",
    };
  }

  if (absoluteDelta < 0.25) {
    return {
      label: "Slight edge",
      tone: delta >= 0 ? "text-emerald-600" : "text-sky-600",
      message: `${leader} has a slight edge of ${formatAbsoluteRuns(delta)} expected runs. Worth considering, but not decisive.`,
    };
  }

  if (absoluteDelta < 0.5) {
    return {
      label: "Meaningful edge",
      tone: delta >= 0 ? "text-emerald-700" : "text-sky-700",
      message: `${leader} projects ${formatAbsoluteRuns(delta)} expected runs better. This is large enough to test seriously.`,
    };
  }

  return {
    label: "Strong edge",
    tone: delta >= 0 ? "text-emerald-800" : "text-sky-800",
    message: `${leader} projects ${formatAbsoluteRuns(delta)} expected runs better. This is a strong signal in the current model.`,
  };
}
function ComparisonPanel({ comparison }) {
  const { optimized, manual, runDelta, simRunDelta, winDelta } = comparison;
  const verdict = getComparisonVerdict(runDelta);

  const maxRows = Math.max(
    optimized.lineup?.length || 0,
    manual.lineup?.length || 0
  );

  return (
    <div className="dashboard-panel p-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-xl font-bold">Optimized vs Manual</h2>
                    <div className="mt-1 space-y-1">
            <div className={`text-sm font-semibold ${verdict.tone}`}>
              {verdict.label}
            </div>
            <p className="text-sm text-slate-500">
              {verdict.message} Manual mode uses the first nine pasted rows exactly.
            </p>
          </div>
        </div>

        <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-900">
          {optimized.inputs.sims.toLocaleString()} games each
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        <ComparisonMetric
          label="Expected Runs"
          optimized={optimized.avgRuns}
          manual={manual.avgRuns}
          delta={runDelta}
        />

        <ComparisonMetric
          label="Sim Avg Runs"
          optimized={optimized.simulatedAvgRuns}
          manual={manual.simulatedAvgRuns}
          delta={simRunDelta}
        />

        <ComparisonMetric
          label="Win Estimate"
          optimized={optimized.winProbability}
          manual={manual.winProbability}
          delta={winDelta}
          type="percent"
        />
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="py-2 pr-3">Slot</th>
              <th className="py-2 pr-3">Optimized</th>
              <th className="py-2 pr-3">Manual</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {Array.from({ length: maxRows }).map((_, index) => {
              const optimizedPlayer = optimized.lineup?.[index];
              const manualPlayer = manual.lineup?.[index];

              return (
                <tr key={`comparison-${index}`}>
                  <td className="py-2 pr-3 font-semibold">{index + 1}</td>
                  <td className="py-2 pr-3">
                    {optimizedPlayer
                      ? `${optimizedPlayer.name} (${optimizedPlayer.fieldPos})`
                      : "-"}
                  </td>
                  <td className="py-2 pr-3">
                    {manualPlayer
                      ? `${manualPlayer.name} (${manualPlayer.fieldPos})`
                      : "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}