import React, { useMemo, useState } from "react";

export default function PitchingAnalyzer() {
  const savedLeagues = JSON.parse(localStorage.getItem("stratLeagues") || "[]");

  const [selectedLeagueId, setSelectedLeagueId] = useState("");
  const [pitcherText, setPitcherText] = useState("");
  const [sortField, setSortField] = useState("score");
  const [analysisView, setAnalysisView] = useState("SP");

  const loadLeague = (leagueId) => {
    setSelectedLeagueId(leagueId);

    const league = savedLeagues.find(
      (l) => String(l.id) === String(leagueId)
    );

    if (!league) return;

    setPitcherText(league.pitcherRoster || "");
  };

  const clearPitchers = () => {
    setSelectedLeagueId("");
    setPitcherText("");
  };

  const parsePitchers = () => {
    return pitcherText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(/\s+/);

        return {
          role: parts[0],
          hand: parts[1],
          name: parts.slice(2, parts.length - 5).join(" "),
          endurance: parts[parts.length - 5],
          hold: parseInt(parts[parts.length - 4]) || 0,
          balance: parts[parts.length - 3],
          salary: parseFloat(parts[parts.length - 2]) || 0,
          profile: parts[parts.length - 1],
        };
      });
  };

  const getEnduranceValue = (p) => {
    if (p.endurance.includes("S")) {
      return parseInt(p.endurance.replace("S", "")) || 0;
    }

    return parseInt(p.endurance.replace("R", "")) || 0;
  };

  const getBalanceValue = (balance) => {
    if (balance === "E") return 8;
    if (balance.includes("R")) {
      return 5 - parseInt(balance.replace("R", ""));
    }

    if (balance.includes("L")) {
      return 5 - parseInt(balance.replace("L", ""));
    }

    return 0;
  };

  const getProfileValue = (profile, role) => {
    if (profile === "GB") {
      return role === "SP" ? 8 : 5;
    }

    if (profile === "POWER") {
      return role === "RP" ? 9 : 4;
    }

    if (profile === "FB") {
      return -4;
    }

    return 0;
  };

  const scoreStarter = (p) => {
    const endurance = getEnduranceValue(p);

    let score = 0;

    score += endurance * 7;

    score += p.hold * -1.5;

    score += getBalanceValue(p.balance);

    score += getProfileValue(p.profile, "SP");

    if (endurance >= 8) score += 10;
    if (endurance <= 5) score -= 12;

    if (p.profile === "FB" && p.hold >= 1) {
      score -= 10;
    }

    score += 18 / Math.max(p.salary, 1);

    return Number(score.toFixed(1));
  };

  const scoreReliever = (p) => {
    const endurance = getEnduranceValue(p);

    let score = 0;

    score += p.hold * -5;

    score += endurance * 3;

    score += getBalanceValue(p.balance);

    score += getProfileValue(p.profile, "RP");

    if (p.hold <= -2) score += 12;
    if (p.hold >= 2) score -= 10;

    if (p.profile === "POWER") score += 8;

    if (p.endurance === "R1") score -= 8;

    score += 14 / Math.max(p.salary, 1);

    return Number(score.toFixed(1));
  };

  const scorePitcher = (p) => {
    return p.role === "SP"
      ? scoreStarter(p)
      : scoreReliever(p);
  };

  const buildRiskFlags = (p) => {
    const flags = [];

    if (p.hold >= 2) flags.push("Poor hold");

    if (p.hold <= -2) flags.push("Elite hold");

    if (p.profile === "FB") flags.push("HR risk");

    if (p.salary >= 7) flags.push("Expensive");

    if (p.endurance === "R1") flags.push("Fragile usage");

    if (p.role === "RP" && p.profile === "POWER" && p.hold <= -2) {
      flags.push("Bullpen weapon");
    }

    if (
      p.role === "SP" &&
      getEnduranceValue(p) <= 5
    ) {
      flags.push("Short starter");
    }

    if (
      p.role === "SP" &&
      p.profile === "GB"
    ) {
      flags.push("Groundball fit");
    }

    return flags;
  };

  const pitchers = useMemo(() => {
    return parsePitchers().map((p) => ({
      ...p,
      score: scorePitcher(p),
      flags: buildRiskFlags(p),
    }));
  }, [pitcherText]);

  const filteredPitchers = pitchers
    .filter((p) => p.role === analysisView)
    .sort((a, b) => {
      if (sortField === "salary") {
        return a.salary - b.salary;
      }

      if (sortField === "hold") {
        return a.hold - b.hold;
      }

      return b.score - a.score;
    });

  const league = savedLeagues.find(
    (l) => String(l.id) === String(selectedLeagueId)
  );

  return (
    <div
      className="space-y-5 min-h-screen bg-cover bg-center bg-fixed"
      style={{
        backgroundImage: "url('/pitcher-bg.svg')",
      }}
    >
      <div className="bg-white p-5 rounded border">
        <h1 className="text-xl font-bold">Pitching Analyzer</h1>

        <p className="text-sm text-gray-500 mt-1">
          Analyze rotations, bullpen structure, holds, endurance and profile fit.
        </p>
      </div>

      <div className="bg-white p-5 rounded border space-y-4">
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

          <button
            onClick={clearPitchers}
            className="bg-slate-200 text-slate-800 px-4 py-2 rounded"
          >
            Clear Pitchers
          </button>
        </div>

        <textarea
          className="w-full h-52 border p-2 font-mono text-sm"
          value={pitcherText}
          onChange={(e) => {
            setPitcherText(e.target.value);
            setSelectedLeagueId("");
          }}
          placeholder={`SP R Mario Soto S8 -2 3R 7.94 FB\nRP R Rich Gossage R2 0 E 4.14 POWER`}
        />
      </div>

      <div className="bg-white p-5 rounded border space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-2">
            <button
              onClick={() => setAnalysisView("SP")}
              className={`px-4 py-2 rounded ${
                analysisView === "SP"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-200"
              }`}
            >
              Starters
            </button>

            <button
              onClick={() => setAnalysisView("RP")}
              className={`px-4 py-2 rounded ${
                analysisView === "RP"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-200"
              }`}
            >
              Relievers
            </button>
          </div>

          <select
            value={sortField}
            onChange={(e) => setSortField(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="score">Sort by Score</option>
            <option value="salary">Sort by Salary</option>
            <option value="hold">Sort by Hold</option>
          </select>
        </div>

        {league && (
          <div className="text-sm text-slate-500">
            Viewing: <span className="font-semibold">{league.leagueName}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-slate-100 text-left">
                <th className="border p-2">Pitcher</th>
                <th className="border p-2">Hand</th>
                <th className="border p-2">END</th>
                <th className="border p-2">Hold</th>
                <th className="border p-2">BAL</th>
                <th className="border p-2">Salary</th>
                <th className="border p-2">Profile</th>
                <th className="border p-2">Score</th>
                <th className="border p-2">Flags</th>
              </tr>
            </thead>

            <tbody>
              {filteredPitchers.map((p, index) => (
                <tr key={`${p.name}-${index}`} className="hover:bg-slate-50">
                  <td className="border p-2 font-medium">{p.name}</td>

                  <td className="border p-2">{p.hand}</td>

                  <td className="border p-2">{p.endurance}</td>

                  <td className="border p-2">{p.hold}</td>

                  <td className="border p-2">{p.balance}</td>

                  <td className="border p-2">
                    ${p.salary.toFixed(2)}M
                  </td>

                  <td className="border p-2">{p.profile}</td>

                  <td className="border p-2 font-bold">
                    {p.score}
                  </td>

                  <td className="border p-2">
                    <div className="flex flex-wrap gap-1">
                      {p.flags.length === 0 ? (
                        <span className="text-green-700">Clean</span>
                      ) : (
                        p.flags.map((flag) => (
                          <span
                            key={flag}
                            className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs"
                          >
                            {flag}
                          </span>
                        ))
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {filteredPitchers.length === 0 && (
                <tr>
                  <td className="border p-3 text-slate-500" colSpan={9}>
                    No {analysisView === "SP" ? "starters" : "relievers"} loaded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}