import React, { useState } from "react";
import { parks1980 } from "./parks1980";
import { getParkData, getParkStrategySummary } from "./engine/parkEngine";
import { buildCardAwareLineup } from "./engine/lineupEngine";

function getTeamHittersText(team) {
  return team?.hittersText || team?.hitters || team?.hitterRoster || "";
}

function getOpponentStartersText(opponent) {
  return (
    opponent?.probableStartersText ||
    opponent?.probableStarters ||
    opponent?.matchupPitchersText ||
    opponent?.matchupPitchers ||
    ""
  );
}

function getOpponentScoutingNotes(opponent) {
  const sections = [];

  if (opponent?.bullpenText || opponent?.bullpen) {
    sections.push(`Bullpen:\n${opponent.bullpenText || opponent.bullpen}`);
  }

  if (opponent?.tendenciesText || opponent?.tendencies) {
    sections.push(
      `Tendencies:\n${opponent.tendenciesText || opponent.tendencies}`
    );
  }

  if (opponent?.notes) {
    sections.push(`Notes:\n${opponent.notes}`);
  }

  return sections.join("\n\n") || "No opponent scouting notes saved.";
}

function parseStarterLine(line) {
  const clean = line.trim();
  if (!clean) return null;

  const handedness = clean.match(/\b(L|R)\b/i)?.[1]?.toUpperCase() || "R";
  const name = clean
    .replace(/^G\d+\s*/i, "")
    .replace(/\b(L|R)\b.*/i, "")
    .trim();

  return {
    raw: clean,
    name: name || clean,
    handedness,
  };
}

function getPitcherPlan(pitcher, park) {
  const isLefty = pitcher.handedness === "L";
  const lower = pitcher.raw.toLowerCase();

  const plan = [];

  if (isLefty) {
    plan.push("Lean RH and switch hitters batting RH.");
    plan.push("Prioritize RH OBP and gap power over pure HR hunting.");
  } else {
    plan.push("Use your best overall lineup unless a specific platoon weakness is obvious.");
    plan.push("Prioritize OBP, contact, and speed over low-OBP power.");
  }

  if (lower.includes("reuschel")) {
    plan.push("Expect a low-scoring, groundball-heavy game.");
    plan.push("Avoid dead bats. Defense and baserunning matter more than usual.");
    plan.push("This is the best game to manufacture runs aggressively.");
  }

  if (lower.includes("ruthven")) {
    plan.push("Balanced attack. He is more grindable than overpowering.");
    plan.push("Look for traffic, contact innings, and selective running.");
  }

  if (lower.includes("matlack")) {
    plan.push("This is the clearest platoon-attack game.");
    plan.push("Maximize quality RH bats, especially RH OBP and doubles power.");
  }

  if (park?.environment?.includes("Low")) {
    plan.push(
      "Because this is a low-HR environment, expect fewer cheap HRs and more value from defense."
    );
  }

  return plan;
}

function formatLineup(lineup, pitcherHand) {
  if (!lineup.length) {
    return "No hitter roster found for selected team.";
  }

  return lineup
    .map((player, index) => {
      const obp =
        player.obp ??
        (pitcherHand === "L" ? player.obpVsL : player.obpVsR) ??
        0;

      return `${index + 1}. ${player.fieldPos || "?"} ${player.name} (${player.bats}) — OBP ${Number(
        obp
      ).toFixed(3)}, PWR ${player.power}, SPD ${player.speed}, DEF ${
        player.defense
      }`;
    })
    .join("\n");
}

export default function SeriesPlanner() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");
  const savedOpponents = JSON.parse(
    localStorage.getItem("stratOpponents") || "[]"
  );

  const [myLeagueId, setMyLeagueId] = useState("");
  const [opponentId, setOpponentId] = useState("");
  const [ballpark, setBallpark] = useState("Astrodome 1980");
  const [gameStarters, setGameStarters] = useState(
    "G1 Dick Ruthven R\nG2 Rick Reuschel R\nG3 Jon Matlack L"
  );
  const [injuryNotes, setInjuryNotes] = useState("");
  const [analysis, setAnalysis] = useState("");

  const handleOpponentChange = (opponentIdValue) => {
    setOpponentId(opponentIdValue);

    const opponent = savedOpponents.find(
      (o) => String(o.id) === String(opponentIdValue)
    );

    if (!opponent) return;

    const opponentStarters = getOpponentStartersText(opponent);

    if (opponentStarters) {
      setGameStarters(opponentStarters);
    }

    if (opponent.ballpark) {
      setBallpark(opponent.ballpark);
    }
  };

  const analyzeSeries = () => {
    const myLeague = savedLeagues.find(
      (l) => String(l.id) === String(myLeagueId)
    );

    const opponent = savedOpponents.find(
      (o) => String(o.id) === String(opponentId)
    );

    const starters = gameStarters
      .split("\n")
      .map(parseStarterLine)
      .filter(Boolean);

    const park = getParkData(ballpark);

    const starterReports = starters
      .map((starter, index) => {
        const plan = getPitcherPlan(starter, park);

        const lineup = buildCardAwareLineup({
          hittersText: getTeamHittersText(myLeague),
          pitcherHand: starter.handedness,
          park,
        });

        return `Game ${index + 1}: ${starter.name} (${starter.handedness})

Recommended posture:
${plan.map((item) => `• ${item}`).join("\n")}

Suggested Lineup:
${formatLineup(lineup, starter.handedness)}`;
      })
      .join("\n\n");

    setAnalysis(`
Series Plan

My Team:
${myLeague?.name || myLeague?.leagueName || "No team selected"}

Opponent:
${opponent?.name || "No opponent selected"}

Opponent Scouting:
${getOpponentScoutingNotes(opponent)}

Ballpark:
${park?.name || ballpark}
SI L/R: ${park?.singlesLeft != null ? `${park.singlesLeft}/${park.singlesRight}` : "Unknown"}
HR L/R: ${park?.homeRunsLeft != null ? `${park.homeRunsLeft}/${park.homeRunsRight}` : "Unknown"}

Environment:
${park?.environment || "Unknown"}

Park Notes:
${park?.notes || "No park notes available."}

Park Strategy:
${getParkStrategySummary(ballpark)}

Opponent Starters:
${
  starters.map((s, i) => `G${i + 1}: ${s.name} (${s.handedness})`).join("\n") ||
  "No starters entered"
}

Game-by-Game Plan:

${starterReports || "No starter analysis available."}

Series-Level Recommendation:
• Treat this as a low-scoring tactical series.
• Defense, baserunning, and bullpen leverage matter more than raw slugging.
• Game 3 vs Matlack is likely your best platoon opportunity.
• Game 2 vs Reuschel is the game most likely to require manufacturing runs.
• Avoid dead zones at the bottom of the lineup.

Recommended Series Settings:

Stealing:
• Average overall
• Aggressive vs Matlack
• Selective vs Ruthven (+2 HOLD)

Hit & Run:
• Average
• Increase usage in Game 2 vs Reuschel
• Prioritize high-contact hitters only

Baserunning:
• Aggressive
• Extra bases matter heavily in the Astrodome

Defense:
• Prioritize CF, SS, and catcher defense
• Consider late-inning defensive replacements aggressively

Bullpen:
• Expect multiple close games
• Use leverage relievers early if needed
• Preventing one run may matter more than saving arms

Injuries / Notes:
${injuryNotes || "None"}
`);
  };

  return (
    <div className="space-y-5">
      <div className="dashboard-panel p-6">
        <h1 className="text-2xl font-bold mb-2">Series Planner</h1>
        <p className="text-sm text-slate-500">
          Plan 3-game Strat series using opponent starters, ballpark context,
          saved scouting records, and card-aware lineup recommendations.
        </p>
      </div>

      <div className="dashboard-panel p-6 space-y-4">
        <div>
          <div className="font-semibold mb-1">My Saved League</div>
          <select
            value={myLeagueId}
            onChange={(e) => setMyLeagueId(e.target.value)}
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 w-full"
          >
            <option value="">Select my team</option>
            {savedLeagues.map((league) => (
              <option key={league.id} value={league.id}>
                {league.name || league.leagueName}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="font-semibold mb-1">Saved Opponent</div>
          <select
            value={opponentId}
            onChange={(e) => handleOpponentChange(e.target.value)}
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 w-full"
          >
            <option value="">Select opponent</option>
            {savedOpponents.map((opponent) => (
              <option key={opponent.id} value={opponent.id}>
                {opponent.name || "Unnamed Opponent"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="font-semibold mb-1">Ballpark</div>
          <select
            value={ballpark}
            onChange={(e) => setBallpark(e.target.value)}
            className="border border-slate-200 bg-white/80 rounded-lg p-2.5 w-full"
          >
            {parks1980.map((park) => (
              <option key={park.id} value={park.name}>
                {park.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="font-semibold mb-1">Opponent Starters</div>
          <textarea
            value={gameStarters}
            onChange={(e) => setGameStarters(e.target.value)}
            rows={5}
            className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 font-mono text-sm"
            placeholder={`G1 Dick Ruthven R
G2 Rick Reuschel R
G3 Jon Matlack L`}
          />
        </div>

        <div>
          <div className="font-semibold mb-1">Injuries / Availability Notes</div>
          <textarea
            value={injuryNotes}
            onChange={(e) => setInjuryNotes(e.target.value)}
            rows={4}
            className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 text-sm"
            placeholder="Example: My closer unavailable Game 1. Opponent catcher weak arm. Key bench bat injured."
          />
        </div>

        <button
          onClick={analyzeSeries}
          className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg"
        >
          Analyze Series
        </button>
      </div>

      {analysis && (
        <div className="space-y-4">
          {analysis
            .split("\n\n")
            .filter(Boolean)
            .map((section, index) => (
              <div key={index} className="dashboard-panel p-5">
                <div className="whitespace-pre-wrap text-sm text-slate-800 leading-relaxed">
                  {section}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
