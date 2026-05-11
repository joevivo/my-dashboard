import React, { useEffect, useState } from "react";

export default function LeagueManager() {
  const [leagues, setLeagues] = useState(() => {
    const saved = localStorage.getItem("stratLeagues");
    return saved ? JSON.parse(saved) : [];
  });

  const [editingId, setEditingId] = useState(null);
  const [leagueName, setLeagueName] = useState("");
  const [ballpark, setBallpark] = useState("");
  const [hitters, setHitters] = useState("");
  const [pitchers, setPitchers] = useState("");
  const [matchupPitchers, setMatchupPitchers] = useState("");
  const [defense, setDefense] = useState("");

  useEffect(() => {
    localStorage.setItem("stratLeagues", JSON.stringify(leagues));
  }, [leagues]);

  const clearForm = () => {
    setEditingId(null);
    setLeagueName("");
    setBallpark("");
    setHitters("");
    setPitchers("");
    setMatchupPitchers("");
    setDefense("");
  };

  const saveLeague = () => {
    if (!leagueName.trim()) return;

    const leagueData = {
      id: editingId || Date.now(),
      name: leagueName.trim(),
      ballpark: ballpark.trim(),
      hitters,
      pitchers,
      matchupPitchers,
      defense,
      updatedAt: new Date().toISOString(),
    };

    if (editingId) {
      setLeagues(
        leagues.map((league) =>
          league.id === editingId
            ? {
                ...league,
                ...leagueData,
              }
            : league
        )
      );
    } else {
      setLeagues([
        ...leagues,
        {
          ...leagueData,
          createdAt: new Date().toISOString(),
        },
      ]);
    }

    clearForm();
  };

  const editLeague = (league) => {
    setEditingId(league.id);
    setLeagueName(league.name || league.leagueName || "");
    setBallpark(league.ballpark || league.homePark || "");
    setHitters(league.hitters || league.hitterRoster || "");
    setPitchers(league.pitchers || league.pitcherRoster || "");
    setMatchupPitchers(league.matchupPitchers || "");
    setDefense(league.defense || league.teamDefense || "");
  };

  const deleteLeague = (id) => {
    setLeagues(leagues.filter((league) => league.id !== id));

    if (editingId === id) {
      clearForm();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border rounded p-4">
        <h1 className="text-2xl font-bold mb-2">League Manager</h1>
        <p className="text-sm text-slate-500">
          Save and edit leagues, rosters, matchup pitchers, defense, and ballpark.
        </p>
      </div>

      <div className="bg-white border rounded p-4 space-y-4">
        <h2 className="text-xl font-bold">
          {editingId ? "Edit League" : "New League"}
        </h2>

        <input
          value={leagueName}
          onChange={(e) => setLeagueName(e.target.value)}
          placeholder="League Name"
          className="w-full border rounded p-2"
        />

        <input
          value={ballpark}
          onChange={(e) => setBallpark(e.target.value)}
          placeholder="Home Ballpark"
          className="w-full border rounded p-2"
        />

        <TextBox
          label="Hitters"
          value={hitters}
          onChange={setHitters}
          placeholder="Paste hitter roster text"
        />

        <TextBox
          label="Pitchers"
          value={pitchers}
          onChange={setPitchers}
          placeholder="Paste pitcher roster text"
        />

        <TextBox
          label="Matchup Pitchers"
          value={matchupPitchers}
          onChange={setMatchupPitchers}
          placeholder={`SP Mario Soto R FB 2 9\nSP Bob Shirley L GB -4 6`}
        />

        <TextBox
          label="Team Defense"
          value={defense}
          onChange={setDefense}
          placeholder={`C 2\n1B 3\n2B 4\n3B 3\nSS 2\nLF 2\nCF 3\nRF 2`}
        />

        <div className="flex flex-wrap gap-2">
          <button
            onClick={saveLeague}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            {editingId ? "Update League" : "Save League"}
          </button>

          {editingId && (
            <button
              onClick={clearForm}
              className="bg-slate-200 text-slate-800 px-4 py-2 rounded"
            >
              Cancel Edit
            </button>
          )}
        </div>
      </div>

      <div className="bg-white border rounded p-4">
        <h2 className="text-xl font-bold mb-4">Saved Leagues</h2>

        {leagues.length === 0 ? (
          <p className="text-sm text-slate-500">No leagues saved yet.</p>
        ) : (
          <div className="space-y-3">
            {leagues.map((league) => {
              const displayName = league.name || league.leagueName || "Unnamed League";
              const displayPark = league.ballpark || league.homePark || "";

              return (
                <div key={league.id} className="border rounded p-3">
                  <div className="flex justify-between gap-3">
                    <div>
                      <div className="font-bold">{displayName}</div>

                      {displayPark && (
                        <div className="text-sm text-slate-500">{displayPark}</div>
                      )}

                      <div className="text-xs text-slate-400 mt-1">
                        {(league.hitters || league.hitterRoster) && "hitters saved"}
                        {(league.pitchers || league.pitcherRoster) && " · pitchers saved"}
                        {league.matchupPitchers && " · matchup pitchers saved"}
                        {(league.defense || league.teamDefense) && " · defense saved"}
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => editLeague(league)}
                        className="text-blue-600 text-sm hover:underline"
                      >
                        Edit
                      </button>

                      <button
                        onClick={() => deleteLeague(league.id)}
                        className="text-red-600 text-sm hover:underline"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function TextBox({ label, value, onChange, placeholder }) {
  return (
    <div>
      <div className="font-semibold mb-1 text-sm">{label}</div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={8}
        className="w-full border rounded p-2 text-sm font-mono"
        placeholder={placeholder}
      />
    </div>
  );
}
