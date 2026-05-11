import React, { useState } from "react";

export default function SeriesPlanner() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");
  const savedOpponents = JSON.parse(localStorage.getItem("stratOpponents") || "[]");

  const [myLeagueId, setMyLeagueId] = useState("");
  const [opponentId, setOpponentId] = useState("");
  const [gameStarters, setGameStarters] = useState("");
  const [injuryNotes, setInjuryNotes] = useState("");
  const [analysis, setAnalysis] = useState("");

  const analyzeSeries = () => {
    const myLeague = savedLeagues.find((l) => String(l.id) === String(myLeagueId));
    const opponent = savedOpponents.find((o) => String(o.id) === String(opponentId));

    setAnalysis(`
Series Plan

My Team:
${myLeague?.name || myLeague?.leagueName || "No team selected"}

Opponent:
${opponent?.name || "No opponent selected"}

Ballpark:
${opponent?.ballpark || myLeague?.ballpark || myLeague?.homePark || "Unknown"}

Opponent Starters:
${gameStarters || "No starters entered"}

Injuries / Notes:
${injuryNotes || "None"}

Early Recommendation:
Use Matchup Analyzer game-by-game for now. This planner is ready to become the 3-game series engine.
`);
  };

  return (
    <div className="space-y-5">
      <div className="bg-white p-6 rounded border">
        <h1 className="text-2xl font-bold mb-2">Series Planner</h1>
        <p className="text-sm text-slate-500">
          Plan regular-season 3-game Strat series using saved teams, opponents, starters, injuries, and ballpark context.
        </p>
      </div>

      <div className="bg-white p-6 rounded border space-y-4">
        <div>
          <div className="font-semibold mb-1">My Saved League</div>
          <select
            value={myLeagueId}
            onChange={(e) => setMyLeagueId(e.target.value)}
            className="border rounded p-2 w-full"
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
            onChange={(e) => setOpponentId(e.target.value)}
            className="border rounded p-2 w-full"
          >
            <option value="">Select opponent</option>
            {savedOpponents.map((opponent) => (
              <option key={opponent.id} value={opponent.id}>
                {opponent.name}
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
            className="w-full border rounded p-2 font-mono text-sm"
            placeholder={`G1 Bob Knepper L GB -1 6
G2 Nolan Ryan R POWER 0 9
G3 Rick Reuschel R GB 0 8`}
          />
        </div>

        <div>
          <div className="font-semibold mb-1">Injuries / Availability Notes</div>
          <textarea
            value={injuryNotes}
            onChange={(e) => setInjuryNotes(e.target.value)}
            rows={4}
            className="w-full border rounded p-2 text-sm"
            placeholder="Example: Robin Yount out Game 3. Opponent catcher fatigued. My Goose unavailable Game 1."
          />
        </div>

        <button
          onClick={analyzeSeries}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Analyze Series
        </button>
      </div>

      {analysis && (
        <pre className="bg-white border rounded p-4 whitespace-pre-wrap text-sm">
          {analysis}
        </pre>
      )}
    </div>
  );
}