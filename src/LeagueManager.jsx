import React, { useEffect, useState } from "react";

function normalizeLeague(league) {
  return {
    id: league.id || Date.now(),
    name: league.name || league.leagueName || "Unnamed League",
    type: league.type || "team",
    ballpark: league.ballpark || league.homePark || "",
    hittersText: league.hittersText || league.hitters || league.hitterRoster || "",
    pitchersText: league.pitchersText || league.pitchers || league.pitcherRoster || "",
    matchupPitchersText:
      league.matchupPitchersText || league.matchupPitchers || "",
    defenseText: league.defenseText || league.defense || league.teamDefense || "",
    notes: league.notes || "",
    createdAt: league.createdAt || new Date().toISOString(),
    updatedAt: league.updatedAt || new Date().toISOString(),
  };
}

export default function LeagueManager() {
  const [leagues, setLeagues] = useState(() => {
    const saved = localStorage.getItem("stratLeagues");
    return saved ? JSON.parse(saved).map(normalizeLeague) : [];
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

    const existingLeague = leagues.find(
      (league) => String(league.id) === String(editingId)
    );

    const leagueData = {
      id: editingId || Date.now(),
      name: leagueName.trim(),
      type: "team",
      ballpark: ballpark.trim(),
      hittersText: hitters,
      pitchersText: pitchers,
      matchupPitchersText: matchupPitchers,
      defenseText: defense,
      notes: existingLeague?.notes || "",
      createdAt: existingLeague?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    if (editingId) {
      setLeagues(
        leagues.map((league) =>
          String(league.id) === String(editingId)
            ? normalizeLeague({
                ...league,
                ...leagueData,
              })
            : league
        )
      );
    } else {
      setLeagues([...leagues, normalizeLeague(leagueData)]);
    }

    clearForm();
  };

  const editLeague = (league) => {
    const normalized = normalizeLeague(league);

    setEditingId(normalized.id);
    setLeagueName(normalized.name);
    setBallpark(normalized.ballpark);
    setHitters(normalized.hittersText);
    setPitchers(normalized.pitchersText);
    setMatchupPitchers(normalized.matchupPitchersText);
    setDefense(normalized.defenseText);
  };

  const deleteLeague = (id) => {
    setLeagues(leagues.filter((league) => String(league.id) !== String(id)));

    if (String(editingId) === String(id)) {
      clearForm();
    }
  };

  return (
    <div className="space-y-6">
      <div className="dashboard-panel p-6">
        <h1 className="text-2xl font-bold mb-2">League Manager</h1>
        <p className="text-sm text-slate-500">
          Save and edit canonical team records for rosters, matchup pitchers,
          defense, and ballpark.
        </p>
      </div>

      <div className="dashboard-panel p-6 space-y-4">
        <h2 className="text-xl font-bold">
          {editingId ? "Edit League" : "New League"}
        </h2>

        <input
          value={leagueName}
          onChange={(e) => setLeagueName(e.target.value)}
          placeholder="League Name"
          className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-slate-300"
        />

        <input
          value={ballpark}
          onChange={(e) => setBallpark(e.target.value)}
          placeholder="Home Ballpark"
          className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-slate-300"
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
            className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg"
          >
            {editingId ? "Update League" : "Save League"}
          </button>

          {editingId && (
            <button
              onClick={clearForm}
              className="bg-slate-200 hover:bg-slate-300 transition text-slate-800 px-4 py-2 rounded-lg"
            >
              Cancel Edit
            </button>
          )}
        </div>
      </div>

      <div className="dashboard-panel p-6">
        <h2 className="text-xl font-bold mb-4">Saved Leagues</h2>

        {leagues.length === 0 ? (
          <p className="text-sm text-slate-500">No leagues saved yet.</p>
        ) : (
          <div className="space-y-3">
            {leagues.map((league) => {
              const normalized = normalizeLeague(league);

              return (
                <div
                  key={normalized.id}
                  className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/80 hover:bg-white hover:border-slate-300 transition"
                >
                  <div className="flex justify-between gap-3">
                    <div>
                      <div className="font-bold text-slate-950">
                        {normalized.name}
                      </div>

                      {normalized.ballpark && (
                        <div className="text-sm text-slate-500">
                          {normalized.ballpark}
                        </div>
                      )}

                      <div className="text-xs text-slate-400 mt-1">
                        {normalized.hittersText && "hitters saved"}
                        {normalized.pitchersText && " · pitchers saved"}
                        {normalized.matchupPitchersText &&
                          " · matchup pitchers saved"}
                        {normalized.defenseText && " · defense saved"}
                      </div>

                      <div className="text-xs text-slate-400 mt-1">
                        Canonical fields: name · ballpark · hittersText ·
                        pitchersText · matchupPitchersText · defenseText
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => editLeague(normalized)}
                        className="text-blue-700 text-sm hover:underline"
                      >
                        Edit
                      </button>

                      <button
                        onClick={() => deleteLeague(normalized.id)}
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
        className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-300"
        placeholder={placeholder}
      />
    </div>
  );
}
