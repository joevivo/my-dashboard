import React, { useEffect, useState } from "react";

export default function LeagueManager() {
  const [leagues, setLeagues] = useState(() => {
    const saved = localStorage.getItem("stratLeagues");
    return saved ? JSON.parse(saved) : [];
  });

  const [leagueNumber, setLeagueNumber] = useState("");
  const [leagueName, setLeagueName] = useState("");
  const [homePark, setHomePark] = useState("");
  const [playerUrls, setPlayerUrls] = useState("");
const [hitterRoster, setHitterRoster] = useState("");
const [pitcherRoster, setPitcherRoster] = useState("");
  useEffect(() => {
    localStorage.setItem("stratLeagues", JSON.stringify(leagues));
  }, [leagues]);

  const addLeague = () => {
    if (!leagueNumber.trim()) return;

    const newLeague = {
      id: Date.now(),
      leagueNumber: leagueNumber.trim(),
      leagueName: leagueName.trim() || `League ${leagueNumber.trim()}`,
      homePark: homePark.trim(),
      playerUrls: playerUrls
        .split("\n")
        .map((url) => url.trim())
        .filter(Boolean),
        hitterRoster,
pitcherRoster,
      createdAt: new Date().toISOString(),
    };

    setLeagues([...leagues, newLeague]);

    setLeagueNumber("");
    setLeagueName("");
    setHomePark("");
    setPlayerUrls("");
    setHitterRoster("");
setPitcherRoster("");
  };

  const deleteLeague = (id) => {
    setLeagues(leagues.filter((league) => league.id !== id));
  };

  return (
    <div className="space-y-5">
      <div className="bg-white p-5 rounded border">
        <h1 className="text-xl font-bold">League Manager</h1>
        <p className="text-sm text-gray-500">
          Save league numbers, home parks, and player URLs for future scouting.
        </p>
      </div>

      <div className="bg-white p-5 rounded border space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            className="border rounded px-3 py-2 text-sm"
            placeholder="League # e.g. 477817"
            value={leagueNumber}
            onChange={(e) => setLeagueNumber(e.target.value)}
          />

          <input
            className="border rounded px-3 py-2 text-sm"
            placeholder="League name"
            value={leagueName}
            onChange={(e) => setLeagueName(e.target.value)}
          />

          <input
            className="border rounded px-3 py-2 text-sm"
            placeholder="Home park"
            value={homePark}
            onChange={(e) => setHomePark(e.target.value)}
          />
        </div>

        <textarea
          className="w-full h-40 border rounded p-2 font-mono text-sm"
          placeholder="Paste player URLs, one per line"
          value={playerUrls}
          onChange={(e) => setPlayerUrls(e.target.value)}
        />
<textarea
  className="w-full h-40 border rounded p-2 font-mono text-sm"
  placeholder="Paste hitter roster text"
  value={hitterRoster}
  onChange={(e) => setHitterRoster(e.target.value)}
/>

<textarea
  className="w-full h-40 border rounded p-2 font-mono text-sm"
  placeholder="Paste pitcher roster text"
  value={pitcherRoster}
  onChange={(e) => setPitcherRoster(e.target.value)}
/>
        <button
          onClick={addLeague}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Save League
        </button>
      </div>

      <div className="bg-white p-5 rounded border">
        <h2 className="font-bold mb-3">Saved Leagues</h2>

        {leagues.length === 0 ? (
          <div className="text-sm text-gray-500">No leagues saved yet.</div>
        ) : (
          <div className="space-y-3">
            {leagues.map((league) => (
              <div key={league.id} className="border rounded p-3">
                <div className="flex justify-between gap-3">
                  <div>
                    <div className="font-semibold">{league.leagueName}</div>
                    <div className="text-sm text-gray-500">
                      League #{league.leagueNumber}
                      {league.homePark && ` · ${league.homePark}`}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {league.playerUrls.length} player URLs saved
{league.hitterRoster && " · hitters saved"}
{league.pitcherRoster && " · pitchers saved"}
                    </div>
                  </div>

                  <button
                    onClick={() => deleteLeague(league.id)}
                    className="text-red-600 text-sm hover:underline"
                  >
                    Delete
                  </button>
                </div>

                {league.playerUrls.length > 0 && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm text-blue-600">
                      View URLs
                    </summary>
                    <pre className="mt-2 bg-slate-100 p-2 rounded text-xs whitespace-pre-wrap">
                      {league.playerUrls.join("\n")}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}