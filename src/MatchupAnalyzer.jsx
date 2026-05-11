import React, { useEffect, useState } from "react";

const ballparks = [
  { name: "Astrodome 1980", hrL: 1, hrR: 1 },
  { name: "Busch Stadium 1980", hrL: 1, hrR: 4 },
  { name: "Riverfront Stadium 1980", hrL: 19, hrR: 19 },
  { name: "Arlington Stadium 1980", hrL: 7, hrR: 7 },
  { name: "Memorial Stadium 1980", hrL: 8, hrR: 17 },
  { name: "Yankee Stadium 1980", hrL: 18, hrR: 2 },
  { name: "Tiger Stadium 1980", hrL: 19, hrR: 16 },
  { name: "Comiskey Park 1980", hrL: 1, hrR: 1 },
];

function getLeagueName(league) {
  return league.leagueName || league.name || "Unnamed League";
}

function getLeaguePark(league) {
  return league.homePark || league.ballpark || "Astrodome 1980";
}

export default function MatchupAnalyzer() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");

  const [savedOpponents, setSavedOpponents] = useState(() => {
    const saved = localStorage.getItem("stratOpponents");
    return saved ? JSON.parse(saved) : [];
  });

  const [selectedLeague, setSelectedLeague] = useState("");
  const [selectedOpponent, setSelectedOpponent] = useState("");
  const [opponentName, setOpponentName] = useState("");
  const [lineupText, setLineupText] = useState("");
  const [pitcherText, setPitcherText] = useState("");
  const [defenseText, setDefenseText] = useState("");
  const [ballpark, setBallpark] = useState("Astrodome 1980");
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    localStorage.setItem("stratOpponents", JSON.stringify(savedOpponents));
  }, [savedOpponents]);

  const loadLeague = (leagueId) => {
    setSelectedLeague(leagueId);

    const league = savedLeagues.find((item) => String(item.id) === String(leagueId));
    if (!league) return;

    setPitcherText(league.matchupPitchers || "");
    setDefenseText(league.teamDefense || league.defense || "");
    setBallpark(getLeaguePark(league));
    setAnalysis(null);
  };

  const newOpponent = () => {
    setSelectedOpponent("");
    setOpponentName("");
    setLineupText("");
    setAnalysis(null);
  };

  const saveOpponent = () => {
    if (!opponentName.trim() || !lineupText.trim()) return;

    if (selectedOpponent) {
      setSavedOpponents(
        savedOpponents.map((opponent) =>
          String(opponent.id) === String(selectedOpponent)
            ? {
                ...opponent,
                name: opponentName.trim(),
                ballpark,
                lineupText,
                updatedAt: new Date().toISOString(),
              }
            : opponent
        )
      );
      return;
    }

    const opponentData = {
      id: Date.now(),
      name: opponentName.trim(),
      ballpark,
      lineupText,
      createdAt: new Date().toISOString(),
    };

    setSavedOpponents([...savedOpponents, opponentData]);
    setSelectedOpponent(String(opponentData.id));
  };

  const loadOpponent = (opponentId) => {
    setSelectedOpponent(opponentId);

    const opponent = savedOpponents.find((item) => String(item.id) === String(opponentId));

    if (!opponent) {
      setOpponentName("");
      setLineupText("");
      return;
    }

    setOpponentName(opponent.name || "");
    setLineupText(opponent.lineupText || "");
    setBallpark(opponent.ballpark || ballpark);
    setAnalysis(null);
  };

  const deleteOpponent = (opponentId) => {
    setSavedOpponents(savedOpponents.filter((item) => String(item.id) !== String(opponentId)));

    if (String(selectedOpponent) === String(opponentId)) {
      newOpponent();
    }
  };

  const analyzeMatchup = () => {
    const park = ballparks.find((item) => item.name === ballpark) || ballparks[0];

    const hitters = lineupText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(/\s+/);

        return {
          spot: parts[0],
          name: parts.slice(1, parts.length - 4).join(" "),
          bats: parts[parts.length - 4],
          obp: parseFloat(parts[parts.length - 3]) || 0,
          power: parseFloat(parts[parts.length - 2]) || 0,
          speed: parseFloat(parts[parts.length - 1]) || 0,
        };
      });

    const pitchers = pitcherText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(/\s+/);

        return {
          role: parts[0],
          name: parts.slice(1, parts.length - 4).join(" "),
          hand: parts[parts.length - 4],
          profile: parts[parts.length - 3],
          hold: parseInt(parts[parts.length - 2], 10) || 0,
          talent: parseInt(parts[parts.length - 1], 10) || 5,
        };
      });

    const defense = {};

    defenseText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .forEach((line) => {
        const parts = line.split(/\s+/);
        defense[parts[0]] = parseInt(parts[1], 10) || 5;
      });

    const infieldDefense =
      (6 - (defense["2B"] || 5)) +
      (6 - (defense["SS"] || 5)) +
      (6 - (defense["3B"] || 5));

    const outfieldDefense =
      (6 - (defense["LF"] || 5)) +
      (6 - (defense["CF"] || 5)) +
      (6 - (defense["RF"] || 5));

    const catcherDefense = 6 - (defense["C"] || 5);

    const lefties = hitters.filter((p) => p.bats === "L").length;
    const righties = hitters.filter((p) => p.bats === "R").length;
    const switchHitters = hitters.filter((p) => p.bats === "S").length;

    const avgObp =
      hitters.reduce((sum, p) => sum + p.obp, 0) / Math.max(hitters.length, 1);

    const avgPower =
      hitters.reduce((sum, p) => sum + p.power, 0) / Math.max(hitters.length, 1);

    const rightyPower = hitters
      .filter((p) => p.bats === "R")
      .reduce((sum, p) => sum + p.power, 0);

    const leftyPower = hitters
      .filter((p) => p.bats === "L")
      .reduce((sum, p) => sum + p.power, 0);

    const hrPressure = (rightyPower * park.hrR + leftyPower * park.hrL) / 100;
    const powerThreats = hitters.filter((p) => p.power >= 6);

    const scoredPitchers = pitchers.map((p) => {
      let score = 50;

      score += p.talent * 3;
      score += p.hold * -4;
      score += catcherDefense;

      if (p.profile === "GB") {
        score += 10;
        score += infieldDefense;
      }

      if (p.profile === "FB") {
        score += outfieldDefense;
        score -= hrPressure * 2;

        if (avgPower >= 5) {
          score -= 15;
        }
      }

      if (p.profile === "POWER") {
        score += 25;
      }

      if (p.profile === "GB" && hrPressure >= 8) {
        score += 10;
      }

      if (righties >= 6 && p.hand === "R") {
        score += 5;
      }

      if (lefties >= 5 && p.hand === "L") {
        score += 5;
      }

      return {
        ...p,
        matchupScore: Number(score.toFixed(1)),
      };
    });

    const starters = scoredPitchers
      .filter((p) => p.role === "SP")
      .sort((a, b) => b.matchupScore - a.matchupScore);

    const relievers = scoredPitchers
      .filter((p) => p.role === "RP")
      .sort((a, b) => b.matchupScore - a.matchupScore);

    const avoid = scoredPitchers
      .filter((p) => p.matchupScore < 55 || (p.profile === "FB" && avgPower >= 5))
      .sort((a, b) => a.matchupScore - b.matchupScore);

    setAnalysis({
      park,
      lefties,
      righties,
      switchHitters,
      avgObp,
      avgPower,
      hrPressure,
      powerThreats,
      starters,
      relievers,
      avoid,
      infieldDefense,
      outfieldDefense,
    });
  };

  return (
    <div className="space-y-5">
      <div className="bg-white p-6 rounded border">
        <h1 className="text-2xl font-bold mb-2">Matchup Analyzer</h1>
        <p className="text-sm text-slate-500">
          Analyze opponent threats, defense context, ballpark fit, and pitching matchups.
        </p>
      </div>

      <div className="bg-white p-6 rounded border">
        <h2 className="font-bold mb-2">Load Saved League</h2>

        <select
          value={selectedLeague}
          onChange={(e) => loadLeague(e.target.value)}
          className="border rounded px-3 py-2 text-sm w-full"
        >
          <option value="">Select saved league</option>

          {savedLeagues.map((league) => (
            <option key={league.id} value={league.id}>
              {getLeagueName(league)}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-white p-6 rounded border space-y-3">
        <h2 className="font-bold">Opponent Library</h2>

        <select
          value={selectedOpponent}
          onChange={(e) => loadOpponent(e.target.value)}
          className="border rounded px-3 py-2 text-sm w-full"
        >
          <option value="">Load saved opponent</option>

          {savedOpponents.map((opponent) => (
            <option key={opponent.id} value={opponent.id}>
              {opponent.name}
            </option>
          ))}
        </select>

        <input
          value={opponentName}
          onChange={(e) => setOpponentName(e.target.value)}
          placeholder="Opponent name"
          className="w-full border rounded px-3 py-2 text-sm"
        />

        <div className="flex flex-wrap gap-2">
          <button
            onClick={newOpponent}
            className="bg-slate-200 text-slate-800 px-4 py-2 rounded"
          >
            New Opponent
          </button>

          <button
            onClick={saveOpponent}
            className="bg-slate-800 text-white px-4 py-2 rounded"
          >
            {selectedOpponent ? "Update Current Opponent" : "Save Current Opponent"}
          </button>

          {selectedOpponent && (
            <button
              onClick={() => deleteOpponent(selectedOpponent)}
              className="bg-red-600 text-white px-4 py-2 rounded"
            >
              Delete Selected Opponent
            </button>
          )}
        </div>
      </div>

      <div className="bg-white p-6 rounded border">
        <h2 className="font-bold mb-2">Ballpark</h2>

        <select
          value={ballpark}
          onChange={(e) => setBallpark(e.target.value)}
          className="border rounded px-3 py-2 text-sm w-full"
        >
          {ballparks.map((park) => (
            <option key={park.name} value={park.name}>
              {park.name}
            </option>
          ))}
        </select>
      </div>

      <InputSection
        title="Opponent Lineup"
        example="1 Mike Schmidt R .372 10 5"
        value={lineupText}
        onChange={setLineupText}
      />

      <InputSection
        title="Your Pitchers"
        example={`SP Mario Soto R FB 2 9\nSP Bob Shirley L GB -4 6\nRP Goose Gossage R POWER 0 10`}
        value={pitcherText}
        onChange={setPitcherText}
      />

      <InputSection
        title="Team Defense"
        example={`C 4\n1B 4\n2B 4\n3B 3\nSS 2\nLF 2\nCF 3\nRF 2`}
        value={defenseText}
        onChange={setDefenseText}
      />

      <button
        onClick={analyzeMatchup}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Analyze Matchup
      </button>

      {analysis && (
        <>
          <div className="bg-white p-6 rounded border">
            <h2 className="text-xl font-bold mb-4">Opponent Overview</h2>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatCard label="Ballpark" value={analysis.park.name} />
              <StatCard label="HR L/R" value={`${analysis.park.hrL}/${analysis.park.hrR}`} />
              <StatCard label="IF Defense" value={analysis.infieldDefense} />
              <StatCard label="OF Defense" value={analysis.outfieldDefense} />
              <StatCard label="Lefties" value={analysis.lefties} />
              <StatCard label="Righties" value={analysis.righties} />
              <StatCard label="Switch Hitters" value={analysis.switchHitters} />
              <StatCard label="Avg OBP" value={analysis.avgObp.toFixed(3)} />
              <StatCard label="Avg Power" value={analysis.avgPower.toFixed(1)} />
              <StatCard label="HR Pressure" value={analysis.hrPressure.toFixed(1)} />
            </div>
          </div>

          <ThreatSection title="Power Threats" players={analysis.powerThreats} />

          <PitcherSection title="Recommended Starters" pitchers={analysis.starters} />

          <PitcherSection title="Bullpen Plan" pitchers={analysis.relievers} />

          <PitcherSection title="Avoid in Leverage" pitchers={analysis.avoid} />
        </>
      )}
    </div>
  );
}

function InputSection({ title, example, value, onChange }) {
  return (
    <div className="bg-white p-6 rounded border">
      <h2 className="font-bold mb-2">{title}</h2>

      <div className="font-mono text-sm bg-slate-100 p-3 rounded mb-3 whitespace-pre-line">
        {example}
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-40 border rounded p-3 font-mono text-sm"
      />
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-slate-100 rounded p-4">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className="text-lg font-bold mt-1">{value}</div>
    </div>
  );
}

function ThreatSection({ title, players }) {
  return (
    <div className="bg-white p-6 rounded border">
      <h2 className="text-xl font-bold mb-3">{title}</h2>

      {players.length === 0 ? (
        <p className="text-sm text-slate-500">No major threats detected.</p>
      ) : (
        <div className="space-y-2">
          {players.map((p) => (
            <div key={`${p.spot}-${p.name}`} className="border rounded p-3 bg-slate-50">
              <div className="font-bold">
                {p.spot}. {p.name}
              </div>

              <div className="text-sm text-slate-600">
                Bats: {p.bats} · OBP {p.obp.toFixed(3)} · PWR {p.power} · SPD {p.speed}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PitcherSection({ title, pitchers }) {
  return (
    <div className="bg-white p-6 rounded border">
      <h2 className="text-xl font-bold mb-3">{title}</h2>

      {pitchers.length === 0 ? (
        <p className="text-sm text-slate-500">No pitchers listed.</p>
      ) : (
        <div className="space-y-3">
          {pitchers.map((p) => (
            <div key={`${p.role}-${p.name}`} className="border rounded p-4 bg-slate-50">
              <div className="font-bold text-lg">
                {p.role} {p.name}
              </div>

              <div className="text-sm text-slate-600">
                {p.hand} · {p.profile} · Hold {p.hold} · Talent {p.talent}
              </div>

              <div className="mt-2 text-blue-700 font-semibold">
                Matchup Score: {p.matchupScore}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
