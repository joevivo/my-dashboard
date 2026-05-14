import React, { useState } from "react";

const requiredPositions = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"];

const ballparks = [
  { name: "Astrodome 1980", siL: 18, siR: 6, hrL: 1, hrR: 1 },
  { name: "Busch Stadium 1980", siL: 19, siR: 13, hrL: 1, hrR: 4 },
  { name: "County Stadium 1980", siL: 1, siR: 7, hrL: 5, hrR: 5 },
  { name: "Riverfront Stdm 1980", siL: 1, siR: 1, hrL: 19, hrR: 19 },
  { name: "Yankee Stadium 1980", siL: 17, siR: 9, hrL: 18, hrR: 2 },
];

function SectionCard({ title, children }) {
  return (
    <div className="bg-white p-5 rounded border shadow-sm">
      <h2 className="text-lg font-bold mb-3">{title}</h2>
      {children}
    </div>
  );
}

function PlayerLineupCard({ player, index }) {
  return (
    <div className="border rounded bg-slate-50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-slate-500">#{index + 1}</div>
          <div className="font-bold">
            {player.fieldPos} - {player.name}
          </div>
          <div className="text-sm text-slate-600">Bats: {player.bats}</div>
        </div>

        <div className="text-right">
          <div className="text-xs text-slate-500">Score</div>
          <div className="font-bold">{player.score.toFixed(1)}</div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 mt-3 text-sm">
        <div>
          <div className="text-xs text-slate-500">OBP</div>
          <div className="font-semibold">{player.obp.toFixed(3)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">PWR</div>
          <div className="font-semibold">{player.power}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">SPD</div>
          <div className="font-semibold">{player.speed}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">DEF</div>
          <div className="font-semibold">{player.defense}</div>
        </div>
      </div>
    </div>
  );
}

function LineupCards({ lineup }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {lineup.map((player, index) => (
        <PlayerLineupCard
          key={`${player.name}-${player.fieldPos}-${index}`}
          player={player}
          index={index}
        />
      ))}
    </div>
  );
}

function DefenseGrid({ assigned }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {requiredPositions.map((pos) => {
        const player = assigned[pos];

        return (
          <div key={pos} className="border rounded bg-slate-50 p-3">
            <div className="text-xs text-slate-500">{pos}</div>
            <div className="font-bold">{player ? player.name : "OPEN"}</div>
            {player && (
              <div className="text-sm text-slate-600">
                DEF {player.defense} · {player.bats}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function BenchList({ bench, hand, getObp }) {
  if (!bench.length) {
    return <p className="text-sm text-slate-500">No bench players available.</p>;
  }

  return (
    <div className="space-y-2">
      {bench.map((player) => (
        <div
          key={`${player.name}-${hand}`}
          className="border rounded bg-slate-50 p-3"
        >
          <div className="font-bold">{player.name}</div>
          <div className="text-sm text-slate-600">
            {player.positions.join("/")} · Bats {player.bats} · DEF{" "}
            {player.defense} · OBP {getObp(player, hand).toFixed(3)}
          </div>
        </div>
      ))}
    </div>
  );
}


function IdentityCard({ title, identity }) {
  return (
    <div className="border rounded bg-slate-50 p-4">
      <h3 className="font-bold mb-2">{title}</h3>

      <div className="space-y-1 text-sm">
        <div><span className="font-semibold">Style:</span> {identity.offenseStyle}</div>
        <div><span className="font-semibold">Variance:</span> {identity.varianceProfile}</div>
        <div><span className="font-semibold">Dead Zones:</span> {identity.deadZones}</div>
        <div><span className="font-semibold">Playoff Burst Potential:</span> {identity.playoffBurst}</div>
        <div><span className="font-semibold">Avg OBP:</span> {identity.avgObp.toFixed(3)}</div>
        <div><span className="font-semibold">Avg Power:</span> {identity.avgPower.toFixed(1)}</div>
      </div>
    </div>
  );
}

export default function LineupAnalyzer() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");

  const [selectedLeagueId, setSelectedLeagueId] = useState("");
  const [rosterText, setRosterText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [ballpark, setBallpark] = useState("Busch Stadium 1980");

  const loadLeague = (leagueId) => {
    setSelectedLeagueId(leagueId);

    const league = savedLeagues.find((l) => String(l.id) === String(leagueId));

    if (!league) return;

    setRosterText(league.hitterRoster || league.hitters || "");

    if (league.homePark || league.ballpark) {
      setBallpark(league.homePark || league.ballpark);
    }

    setAnalysis(null);
  };

  const parseRoster = () => {
    return rosterText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(/\s+/);

        return {
          positions: parts[0].split("/"),
          bats: parts[1],
          defense: parseInt(parts[2]) || 5,
          name: parts.slice(3, parts.length - 4).join(" "),
          obpVsR: parseFloat(parts[parts.length - 4]) || 0,
          obpVsL: parseFloat(parts[parts.length - 3]) || 0,
          power: parseFloat(parts[parts.length - 2]) || 0,
          speed: parseFloat(parts[parts.length - 1]) || 0,
        };
      });
  };

  const getObp = (p, hand) => (hand === "RHP" ? p.obpVsR : p.obpVsL);

  const getParkValues = (p, park) => {
    if (p.bats === "L") return { si: park.siL, hr: park.hrL };
    if (p.bats === "R") return { si: park.siR, hr: park.hrR };

    return {
      si: (park.siL + park.siR) / 2,
      hr: (park.hrL + park.hrR) / 2,
    };
  };

  const battingValue = (p, hand, park) => {
    const obp = getObp(p, hand);
    const parkValues = getParkValues(p, park);

    let score = obp * 100;

    score += p.power * 8;
    score += p.speed * 1.2;

    const singlesBoost = (parkValues.si - 10) * 0.12;
    const homerBoost = (parkValues.hr - 10) * 0.35;

    score += p.speed * singlesBoost;
    score += p.power * homerBoost;

    if (hand === "LHP") {
      if (p.bats === "R") score += 8;
      if (p.bats === "S") score += 4;
      if (p.bats === "L") score -= 5;
    }

    if (hand === "RHP") {
      if (p.bats === "L") score += 5;
      if (p.bats === "S") score += 3;
    }

    return score;
  };

  const baseBatScore = (p, hand) => {
    const obp = getObp(p, hand);
    return obp * 100 + p.power * 6 + p.speed * 1.2;
  };

  const isPrimaryPosition = (p, pos) => p.positions[0] === pos;

  const positionFitScore = (p, pos, hand, park) => {
    const obp = getObp(p, hand);
    const parkValues = getParkValues(p, park);

    let score = baseBatScore(p, hand);

    if (isPrimaryPosition(p, pos)) score += 35;
    else if (p.positions.includes(pos)) score += 5;

    if (pos === "C") {
      score += (6 - p.defense) * 25;
      score -= p.power * 2;
      if (!isPrimaryPosition(p, "C")) score -= 35;
      if (p.defense >= 4) score -= 30;
    }

    if (pos === "SS") {
      score += (6 - p.defense) * 28;
      if (!isPrimaryPosition(p, "SS")) score -= 20;
    }

    if (pos === "CF") {
      score += (6 - p.defense) * 24;
      score += p.speed * 2;
      if (!isPrimaryPosition(p, "CF")) score -= 25;
      if (p.defense >= 4) score -= 35;
    }

    if (pos === "2B") {
      score += (6 - p.defense) * 18;
    }

    if (pos === "1B" || pos === "LF" || pos === "RF") {
      score += obp * 35 + p.power * 5;
      if (obp < 0.300 && p.power <= 2) score -= 25;
    }

    if (pos === "DH") {
      score += obp * 60 + p.power * 10;
      score -= (6 - p.defense) * 3;
      if (p.power <= 1 && obp < 0.340) score -= 50;
    }

    const singlesBoost = (parkValues.si - 10) * 0.15;
    const homerBoost = (parkValues.hr - 10) * 0.25;

    score += p.speed * singlesBoost;
    score += p.power * homerBoost;

    if (hand === "LHP") {
      if (p.bats === "R") score += 8;
      if (p.bats === "S") score += 4;
      if (p.bats === "L") score -= 6;
    }

    if (hand === "RHP") {
      if (p.bats === "L") score += 5;
      if (p.bats === "S") score += 3;
    }

    return score;
  };

  const assignPositions = (players, hand, park) => {
    const assigned = {};
    const used = new Set();

    const positionOrder = ["SS", "CF", "C", "2B", "3B", "RF", "LF", "1B"];

    const canPlay = (p, pos) => {
      if (used.has(p.name)) return false;
      if (!p.positions.includes(pos)) return false;

      const obp = getObp(p, hand);

      if (pos === "SS" || pos === "2B") {
        if (obp < 0.300 && p.power <= 2) return false;
      }

      if (pos === "C") {
        if (obp < 0.280 && p.power <= 1) return false;
      }

      return true;
    };

    positionOrder.forEach((pos) => {
      const candidates = players
        .filter((p) => canPlay(p, pos))
        .sort(
          (a, b) =>
            positionFitScore(b, pos, hand, park) -
            positionFitScore(a, pos, hand, park)
        );

      if (candidates[0]) {
        assigned[pos] = candidates[0];
        used.add(candidates[0].name);
      }
    });

    const premiumBenchBats = players
      .filter((p) => !used.has(p.name))
      .filter((p) => getObp(p, hand) >= 0.370 || battingValue(p, hand, park) >= 75)
      .sort((a, b) => battingValue(b, hand, park) - battingValue(a, hand, park));

    premiumBenchBats.forEach((bat) => {
      const possibleSwaps = bat.positions
        .filter((pos) => pos !== "DH")
        .filter((pos) => assigned[pos])
        .map((pos) => {
          const current = assigned[pos];

          return {
            pos,
            current,
            gain:
              battingValue(bat, hand, park) -
              battingValue(current, hand, park),
          };
        })
        .filter((swap) => swap.gain >= 8)
        .sort((a, b) => b.gain - a.gain);

      const bestSwap = possibleSwaps[0];

      if (bestSwap) {
        used.delete(bestSwap.current.name);
        assigned[bestSwap.pos] = bat;
        used.add(bat.name);
      }
    });

    const remaining = players.filter((p) => !used.has(p.name));

    const dh = [...remaining].sort(
      (a, b) => battingValue(b, hand, park) - battingValue(a, hand, park)
    )[0];

    if (dh) {
      assigned.DH = dh;
      used.add(dh.name);
    }

    return assigned;
  };

  const buildLineup = (hand) => {
    const park = ballparks.find((p) => p.name === ballpark) || ballparks[0];
    const players = parseRoster();
    const assigned = assignPositions(players, hand, park);

    const starters = Object.entries(assigned).map(([fieldPos, player]) => ({
      ...player,
      fieldPos,
      obp: getObp(player, hand),
      score: battingValue(player, hand, park),
    }));

    const bench = players.filter(
      (p) => !starters.some((s) => s.name === p.name)
    );

    const avgObp =
      starters.reduce((sum, p) => sum + p.obp, 0) /
      Math.max(starters.length, 1);

    const avgPower =
      starters.reduce((sum, p) => sum + p.power, 0) /
      Math.max(starters.length, 1);

    const elitePowerCount = starters.filter((p) => p.power >= 8).length;

    const weakBatCount = starters.filter(
      (p) => p.obp < 0.300 && p.power <= 3
    ).length;

    const speedPressure = starters.filter((p) => p.speed >= 7).length;

    let offenseStyle = "Balanced";
// OFFENSIVE ARCHETYPES
//
// Sustainable Pressure
// - sequencing offense
// - medium OBP
// - low HR dependence
// - low dead zones
//
// Athletic Pressure
// - elite speed
// - advancement pressure
// - doubles/triples pressure
// - defensive stress
//
// Explosive Pressure
// - HR concentration
// - inning spike potential
// - few easy outs
//
// Star-Driven Offense
// - concentrated elite hitters
// - weak bottom third
// - volatile scoring
//
// Prevention Team
// - defense-first
// - bullpen leverage
// - suppresses variance

if (avgPower >= 6.5 && elitePowerCount >= 3) {
  offenseStyle = "Explosive Power";
} else if (speedPressure >= 3 && avgObp >= 0.330) {
  offenseStyle = "Sustainable Pressure";
} else if (avgObp >= 0.340) {
  offenseStyle = "Contact Pressure";
}
    if (avgPower >= 6.5 && elitePowerCount >= 3) {
      offenseStyle = "Explosive Power";
    } else if (speedPressure >= 3 && avgObp >= 0.330) {
      offenseStyle = "Sustainable Pressure";
    } else if (avgObp >= 0.340) {
      offenseStyle = "Contact Pressure";
    }

    let varianceProfile = "Moderate";

    if (elitePowerCount >= 4) {
      varianceProfile = "High Variance";
    } else if (avgObp >= 0.335 && weakBatCount <= 1) {
      varianceProfile = "Low Variance";
    }

    let playoffBurst = "Moderate";

    if (elitePowerCount >= 4) {
      playoffBurst = "Elite";
    } else if (elitePowerCount >= 2) {
      playoffBurst = "Strong";
    }

    let deadZones = "Low";

    if (weakBatCount >= 3) {
      deadZones = "High";
    } else if (weakBatCount === 2) {
      deadZones = "Moderate";
    }

    const remaining = [...starters];
    const order = [];

    const pickBest = (fn) => {
      if (remaining.length === 0) return null;
      const pick = [...remaining].sort((a, b) => fn(b) - fn(a))[0];
      remaining.splice(remaining.indexOf(pick), 1);
      return pick;
    };

    order[0] = pickBest((p) => p.obp * 100 + p.speed * 2);
    order[1] = pickBest((p) => p.obp * 115 + p.power * 2 + p.speed);
    order[2] = pickBest((p) => p.obp * 100 + p.power * 7);

    order[3] = pickBest((p) => {
      let score = p.power * 9 + p.obp * 95;
      if (p.obp < 0.320) score -= 25;
      return score;
    });

    order[4] = pickBest((p) => {
      let score = p.obp * 105 + p.power * 4;
      if (p.obp < 0.320) score -= 15;
      return score;
    });

    order[5] = pickBest((p) => p.obp * 70 + p.power * 3);
    order[6] = pickBest((p) => p.obp * 55 + p.speed);
    order[7] = pickBest((p) => p.obp * 45 + p.power);
    order[8] = pickBest((p) => p.obp * 35 + p.speed);

    return {
      park,
      lineup: order.filter(Boolean),
      assigned,
      bench,
      avgObp,
      avgPower,
      offenseStyle,
      varianceProfile,
      playoffBurst,
      deadZones,
    };
  };

  const analyze = () => {
    const rhp = buildLineup("RHP");
    const lhp = buildLineup("LHP");

    const league = savedLeagues.find(
      (l) => String(l.id) === String(selectedLeagueId)
    );

    setAnalysis({
      leagueName: league?.leagueName || league?.name || "Custom roster",
      park: rhp.park,
      rhp,
      lhp,
    });
  };

  return (
    <div
      className="space-y-5 min-h-screen bg-cover bg-center bg-fixed"
      style={{
        backgroundImage: "url('/hitter-bg.svg')",
      }}
    >
      <div className="bg-white p-5 rounded border shadow-sm">
        <h1 className="text-xl font-bold">Lineup Analyzer</h1>
        <p className="text-sm text-gray-500">
          Format: POS/POS BATS DEF NAME OBPvsR OBPvsL PWR SPD
        </p>
      </div>

      <SectionCard title="Roster Input">
        <div className="flex flex-wrap gap-3 mb-3">
          <select
            value={selectedLeagueId}
            onChange={(e) => loadLeague(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">Load saved league</option>
            {savedLeagues.map((league) => (
              <option key={league.id} value={league.id}>
                {league.leagueName || league.name || "Unnamed League"}
              </option>
            ))}
          </select>

          <select
            value={ballpark}
            onChange={(e) => setBallpark(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            {ballparks.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <textarea
          className="w-full h-56 border rounded p-3 font-mono text-sm"
          value={rosterText}
          onChange={(e) => {
            setRosterText(e.target.value);
            setSelectedLeagueId("");
          }}
        />

        <button
          onClick={analyze}
          className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          Analyze Lineup
        </button>
      </SectionCard>

      {!analysis ? (
        <SectionCard title="Results">
          <p className="text-sm text-slate-500">Results will appear here.</p>
        </SectionCard>
      ) : (
        <>
          <div className="bg-slate-900 text-white p-5 rounded border shadow-sm">
            <h2 className="text-lg font-bold">{analysis.leagueName}</h2>
            <p className="text-sm text-slate-300">
              Ballpark: {analysis.park.name}
            </p>
            <p className="text-sm text-slate-300">
              SI L/R: {analysis.park.siL}/{analysis.park.siR} · HR L/R:{" "}
              {analysis.park.hrL}/{analysis.park.hrR}
            </p>
          </div>

          <SectionCard title="Team Identity">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <IdentityCard title="VS RHP" identity={analysis.rhp} />
              <IdentityCard title="VS LHP" identity={analysis.lhp} />
            </div>
          </SectionCard>

          <SectionCard title="VS RHP Lineup">
            <LineupCards lineup={analysis.rhp.lineup} />
          </SectionCard>

          <SectionCard title="VS RHP Defense">
            <DefenseGrid assigned={analysis.rhp.assigned} />
          </SectionCard>

          <SectionCard title="Bench vs RHP">
            <BenchList bench={analysis.rhp.bench} hand="RHP" getObp={getObp} />
          </SectionCard>

          <SectionCard title="VS LHP Lineup">
            <LineupCards lineup={analysis.lhp.lineup} />
          </SectionCard>

          <SectionCard title="VS LHP Defense">
            <DefenseGrid assigned={analysis.lhp.assigned} />
          </SectionCard>

          <SectionCard title="Bench vs LHP">
            <BenchList bench={analysis.lhp.bench} hand="LHP" getObp={getObp} />
          </SectionCard>
        </>
      )}
    </div>
  );
}