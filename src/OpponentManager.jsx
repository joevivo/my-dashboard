import React, { useEffect, useState } from "react";

function normalizeOpponent(opponent) {
  return {
    id: opponent.id || Date.now(),

    name: opponent.name || "Unnamed Opponent",

    type: "opponent",

    ballpark: opponent.ballpark || "",

    hittersText:
      opponent.hittersText ||
      opponent.hitters ||
      opponent.hitterRoster ||
      "",

    pitchersText:
      opponent.pitchersText ||
      opponent.pitchers ||
      opponent.pitcherRoster ||
      "",

    probableStartersText:
      opponent.probableStartersText ||
      opponent.probableStarters ||
      "",

    bullpenText:
      opponent.bullpenText ||
      opponent.bullpen ||
      "",

    tendenciesText:
      opponent.tendenciesText ||
      opponent.tendencies ||
      "",

    notes:
      opponent.notes || "",

    createdAt:
      opponent.createdAt ||
      new Date().toISOString(),

    updatedAt:
      opponent.updatedAt ||
      new Date().toISOString(),
  };
}

export default function OpponentManager() {
  const [opponents, setOpponents] = useState(() => {
    const saved = localStorage.getItem("stratOpponents");

    return saved
      ? JSON.parse(saved).map(normalizeOpponent)
      : [];
  });

  const [editingId, setEditingId] = useState(null);

  const [name, setName] = useState("");
  const [ballpark, setBallpark] = useState("");

  const [hittersText, setHittersText] =
    useState("");

  const [pitchersText, setPitchersText] =
    useState("");

  const [
    probableStartersText,
    setProbableStartersText,
  ] = useState("");

  const [bullpenText, setBullpenText] =
    useState("");

  const [tendenciesText, setTendenciesText] =
    useState("");

  const [notes, setNotes] = useState("");

  useEffect(() => {
    localStorage.setItem(
      "stratOpponents",
      JSON.stringify(opponents)
    );
  }, [opponents]);

  const clearForm = () => {
    setEditingId(null);

    setName("");
    setBallpark("");

    setHittersText("");
    setPitchersText("");

    setProbableStartersText("");
    setBullpenText("");

    setTendenciesText("");

    setNotes("");
  };

  const saveOpponent = () => {
    if (!name.trim()) return;

    const existing = opponents.find(
      (o) =>
        String(o.id) === String(editingId)
    );

    const opponentData = {
      id: editingId || Date.now(),

      name: name.trim(),

      type: "opponent",

      ballpark: ballpark.trim(),

      hittersText,

      pitchersText,

      probableStartersText,

      bullpenText,

      tendenciesText,

      notes,

      createdAt:
        existing?.createdAt ||
        new Date().toISOString(),

      updatedAt:
        new Date().toISOString(),
    };

    if (editingId) {
      setOpponents(
        opponents.map((opponent) =>
          String(opponent.id) ===
          String(editingId)
            ? normalizeOpponent({
                ...opponent,
                ...opponentData,
              })
            : opponent
        )
      );
    } else {
      setOpponents([
        ...opponents,
        normalizeOpponent(opponentData),
      ]);
    }

    clearForm();
  };

  const editOpponent = (opponent) => {
    const normalized =
      normalizeOpponent(opponent);

    setEditingId(normalized.id);

    setName(normalized.name);

    setBallpark(normalized.ballpark);

    setHittersText(
      normalized.hittersText
    );

    setPitchersText(
      normalized.pitchersText
    );

    setProbableStartersText(
      normalized.probableStartersText
    );

    setBullpenText(
      normalized.bullpenText
    );

    setTendenciesText(
      normalized.tendenciesText
    );

    setNotes(normalized.notes);
  };

  const deleteOpponent = (id) => {
    setOpponents(
      opponents.filter(
        (opponent) =>
          String(opponent.id) !==
          String(id)
      )
    );

    if (
      String(editingId) === String(id)
    ) {
      clearForm();
    }
  };

  return (
    <div className="space-y-6">
      <div className="dashboard-panel p-6">
        <h1 className="text-2xl font-bold mb-2">
          Opponent Manager
        </h1>

        <p className="text-sm text-slate-500">
          Save reusable scouting records for
          recurring Strat opponents.
        </p>
      </div>

      <div className="dashboard-panel p-6 space-y-4">
        <h2 className="text-xl font-bold">
          {editingId
            ? "Edit Opponent"
            : "New Opponent"}
        </h2>

        <input
          value={name}
          onChange={(e) =>
            setName(e.target.value)
          }
          placeholder="Opponent Name"
          className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5"
        />

        <input
          value={ballpark}
          onChange={(e) =>
            setBallpark(e.target.value)
          }
          placeholder="Home Ballpark"
          className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5"
        />

        <TextBox
          label="Hitters"
          value={hittersText}
          onChange={setHittersText}
          placeholder="Paste opponent hitter roster"
        />

        <TextBox
          label="Pitchers"
          value={pitchersText}
          onChange={setPitchersText}
          placeholder="Paste opponent pitcher roster"
        />

        <TextBox
          label="Probable Starters"
          value={
            probableStartersText
          }
          onChange={
            setProbableStartersText
          }
          placeholder={`G1 Dick Ruthven R
G2 Rick Reuschel R
G3 Jon Matlack L`}
        />

        <TextBox
          label="Bullpen Notes"
          value={bullpenText}
          onChange={setBullpenText}
          placeholder="Closer, setup roles, lefty specialists, fatigue concerns"
        />

        <TextBox
          label="Team Tendencies"
          value={tendenciesText}
          onChange={
            setTendenciesText
          }
          placeholder="Aggressive stealing, low defense, platoon heavy, etc."
        />

        <TextBox
          label="Scouting Notes"
          value={notes}
          onChange={setNotes}
          placeholder="General notes and observations"
        />

        <div className="flex gap-2">
          <button
            onClick={saveOpponent}
            className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg"
          >
            {editingId
              ? "Update Opponent"
              : "Save Opponent"}
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
        <h2 className="text-xl font-bold mb-4">
          Saved Opponents
        </h2>

        {opponents.length === 0 ? (
          <p className="text-sm text-slate-500">
            No opponents saved yet.
          </p>
        ) : (
          <div className="space-y-3">
            {opponents.map((opponent) => (
              <div
                key={opponent.id}
                className="border border-slate-200 rounded-xl p-4 bg-slate-50/80"
              >
                <div className="flex justify-between gap-4">
                  <div>
                    <div className="font-bold">
                      {opponent.name}
                    </div>

                    {opponent.ballpark && (
                      <div className="text-sm text-slate-500">
                        {
                          opponent.ballpark
                        }
                      </div>
                    )}

                    <div className="text-xs text-slate-400 mt-1">
                      {opponent.hittersText &&
                        "hitters saved"}

                      {opponent.pitchersText &&
                        " · pitchers saved"}

                      {opponent.probableStartersText &&
                        " · probable starters"}

                      {opponent.tendenciesText &&
                        " · tendencies"}

                      {opponent.notes &&
                        " · scouting notes"}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() =>
                        editOpponent(
                          opponent
                        )
                      }
                      className="text-blue-700 text-sm hover:underline"
                    >
                      Edit
                    </button>

                    <button
                      onClick={() =>
                        deleteOpponent(
                          opponent.id
                        )
                      }
                      className="text-red-600 text-sm hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TextBox({
  label,
  value,
  onChange,
  placeholder,
}) {
  return (
    <div>
      <div className="font-semibold mb-1 text-sm">
        {label}
      </div>

      <textarea
        value={value}
        onChange={(e) =>
          onChange(e.target.value)
        }
        rows={6}
        className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 text-sm font-mono"
        placeholder={placeholder}
      />
    </div>
  );
}