import React, { useState } from "react";

const requiredPositions = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"];

const ballparks = [
  { name: "Astrodome 1980", siL: 18, siR: 6, hrL: 1, hrR: 1 },
  { name: "Busch Stadium 1980", siL: 19, siR: 13, hrL: 1, hrR: 4 },
  { name: "County Stadium 1980", siL: 1, siR: 7, hrL: 5, hrR: 5 },
  { name: "Riverfront Stdm 1980", siL: 1, siR: 1, hrL: 19, hrR: 19 },
  { name: "Yankee Stadium 1980", siL: 17, siR: 9, hrL: 18, hrR: 2 },
];

export default function LineupAnalyzer() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");

  const [selectedLeagueId, setSelectedLeagueId] = useState("");
  const [rosterText, setRosterText] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [ballpark, setBallpark] = useState("Busch Stadium 1980");

  const loadLeague = (leagueId) => {
    setSelectedLeagueId(leagueId);

    const league = savedLeagues.find(
      (l) => String(l.id) === String(leagueId)
    );

    if (!league) return;

    setRosterText(league.hitterRoster || "");

    if (league.homePark) {
      setBallpark(league.homePark);
    }

    setAnalysis("");
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

    const positionOrder = ["SS", "CF", "2B", "1B", "C", "3B", "RF", "LF"];

    positionOrder.forEach((pos) => {
      const candidates = players
        .filter((p) => !used.has(p.name) && p.positions.includes(pos))
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

    const remaining = players.filter((p) => !used.has(p.name));

    const dh = [...remaining].sort(
      (a, b) =>
        positionFitScore(b, "DH", hand, park) -
        positionFitScore(a, "DH", hand, park)
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
      score: positionFitScore(player, fieldPos, hand, park),
    }));

    const bench = players.filter(
      (p) => !starters.some((s) => s.name === p.name)
    );

    const remaining = [...starters];
    const order = [];

    const pickBest = (fn) => {
      if (remaining.length === 0) return null;
      const pick = [...remaining].sort((a, b) => fn(b) - fn(a))[0];
      remaining.splice(remaining.indexOf(pick), 1);
      return pick;
    };

    order[0] = pickBest((p) => p.obp * 100 + p.speed * 3);
    order[1] = pickBest((p) => p.obp * 90 + p.speed * 2);
    order[2] = pickBest((p) => p.obp * 100 + p.power * 5);
    order[3] = pickBest((p) => p.power * 10 + p.obp * 70);
    order[4] = pickBest((p) => p.power * 8 + p.obp * 60);
    order[5] = pickBest((p) => p.obp * 70 + p.power * 3);
    order[6] = pickBest((p) => p.obp * 50 + p.speed);
    order[7] = pickBest((p) => p.obp * 40 + p.power);
    order[8] = pickBest((p) => p.obp * 30 + p.speed);

    return {
      park,
      lineup: order.filter(Boolean),
      assigned,
      bench,
    };
  };

  const analyze = () => {
    const rhp = buildLineup("RHP");
    const lhp = buildLineup("LHP");

    const formatLineup = (lineup) =>
      lineup
        .map(
          (p, i) =>
            `${i + 1}. ${p.fieldPos} ${p.name} (${p.bats}) DEF:${p.defense} SCORE:${p.score.toFixed(
              1
            )} — OBP:${p.obp.toFixed(3)} PWR:${p.power} SPD:${p.speed}`
        )
        .join("\n");

    const formatDefense = (assigned) =>
      requiredPositions
        .map((pos) => {
          const p = assigned[pos];
          return `${pos}: ${p ? `${p.name} DEF:${p.defense}` : "OPEN"}`;
        })
        .join("\n");

    const formatBench = (bench, hand) =>
      bench.length
        ? bench
            .map(
              (p) =>
                `- ${p.name} (${p.positions.join("/")}, ${p.bats}) DEF:${
                  p.defense
                } OBP:${getObp(p, hand).toFixed(3)}`
            )
            .join("\n")
        : "No bench";

    const league = savedLeagues.find(
      (l) => String(l.id) === String(selectedLeagueId)
    );

    setAnalysis(`Roster: ${league?.leagueName || "Custom roster"}
Ballpark: ${rhp.park.name}
SI L/R: ${rhp.park.siL}/${rhp.park.siR} | HR L/R: ${rhp.park.hrL}/${rhp.park.hrR}

VS RHP Lineup:
${formatLineup(rhp.lineup)}

VS RHP Defense:
${formatDefense(rhp.assigned)}

Bench vs RHP:
${formatBench(rhp.bench, "RHP")}

VS LHP Lineup:
${formatLineup(lhp.lineup)}

VS LHP Defense:
${formatDefense(lhp.assigned)}

Bench vs LHP:
${formatBench(lhp.bench, "LHP")}
`);
  };

  return (
   <div
  className="space-y-5 min-h-screen bg-cover bg-center bg-fixed"
  style={{
    backgroundImage: "url('/hitter-bg.svg')",
  }}
>
      <div className="bg-white p-5 rounded border">
        <h1 className="text-xl font-bold">Lineup Analyzer</h1>
        <p className="text-sm text-gray-500">
          Format: POS/POS BATS DEF NAME OBPvsR OBPvsL PWR SPD
        </p>
      </div>

      <div className="bg-white p-5 rounded border space-y-3">
        <div className="flex flex-wrap gap-3">
          <select
            value={selectedLeagueId}
            onChange={(e) => loadLeague(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">Load saved league</option>
            {savedLeagues.map((league) => (
              <option key={league.id} value={league.id}>
                {league.leagueName}
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
          className="w-full h-56 border p-2 font-mono text-sm"
          value={rosterText}
          onChange={(e) => {
            setRosterText(e.target.value);
            setSelectedLeagueId("");
          }}
        />

        <button
          onClick={analyze}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Analyze
        </button>
      </div>

      <div className="bg-white p-5 rounded border">
        <pre className="bg-black text-green-400 p-3 whitespace-pre-wrap max-h-[700px] overflow-y-auto">
          {analysis || "Results will appear here"}
        </pre>
      </div>
    </div>
  );
}