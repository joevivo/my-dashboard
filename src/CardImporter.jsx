import React, { useEffect, useState } from "react";
import {
  parseCardOutcomeProfile,
  describeOutcomeProfile,
} from "./engine/cardOutcomeParser";

function getSavedLeagues() {
  const saved = localStorage.getItem("stratLeagues");
  return saved ? JSON.parse(saved) : [];
}

function parseRosterNames(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/\s+/);

      if (parts.length < 7) return "";

      return parts.slice(3, parts.length - 4).join(" ").trim();
    })
    .filter(Boolean);
}

function parsePitcherNames(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/\s+/);

      if (parts.length < 5) return "";

      return parts.slice(1, parts.length - 4).join(" ").trim();
    })
    .filter(Boolean);
}

function parseCard(rawText, existingCard = {}) {
  const lines = rawText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const name = lines[0] || existingCard.name || "Unknown Player";

  const position =
    rawText.match(/Position:\s*(.+)/i)?.[1]?.trim() ||
    existingCard.position ||
    "";

  const isPitcher = position.toUpperCase() === "P";

  const salary =
    rawText.match(/Salary:\s*\$?([0-9,]+(?:\.\d+)?[MK]?)/i)?.[1]?.trim() ||
    existingCard.salary ||
    "";

  const balance =
    rawText.match(/Balance:\s*([0-9]+[LR]|E)/i)?.[1]?.trim() ||
    existingCard.balance ||
    "";

  const defense =
    rawText
      .match(/Defense:\s*([^\n\r]+)/i)?.[1]
      ?.replace(/running\s+[0-9]+-[0-9]+/i, "")
      ?.trim() ||
    existingCard.defense ||
    "";

  const running =
    rawText.match(/running\s+([0-9]+-[0-9]+)/i)?.[1]?.trim() ||
    existingCard.running ||
    "";

  const stealing =
    rawText.match(/stealing-\(([^)]+)\)/i)?.[1]?.trim() ||
    existingCard.stealing ||
    "";

  const bunting =
    rawText.match(/bunting-([A-E])/i)?.[1]?.trim() ||
    existingCard.bunting ||
    "";

  const hitAndRun =
    rawText.match(/hit\s*&\s*run-([A-E])/i)?.[1]?.trim() ||
    existingCard.hitAndRun ||
    "";

  const throws =
    rawText.match(/throws\s+(RIGHT|LEFT)/i)?.[1]?.toUpperCase() ||
    existingCard.throws ||
    "";

  const hold =
    rawText.match(/hold\s+([+-]?\d+)/i)?.[1] ||
    existingCard.hold ||
    "";

  const starterEndurance =
    rawText.match(/starter\((\d+)\)/i)?.[1] ||
    existingCard.starterEndurance ||
    "";

  const reliefEndurance =
    rawText.match(/relief\((\d+)\)/i)?.[1] ||
    existingCard.reliefEndurance ||
    "";

  const reliefAvailability =
    rawText.match(/relief\(\d+\)\/([YN])/i)?.[1] ||
    existingCard.reliefAvailability ||
    "";

  const balk =
    rawText.match(/\bbk-\s*(\d+)/i)?.[1] ||
    existingCard.balk ||
    "";

  const wildPitch =
    rawText.match(/\bwp-\s*(\d+)/i)?.[1] ||
    existingCard.wildPitch ||
    "";

  const pitcherDefense =
    rawText.match(/pitcher-([0-9])/i)?.[1] ||
    existingCard.pitcherDefense ||
    "";

  const pitcherError =
    rawText.match(/\be([0-9]+)\b/i)?.[1] ||
    existingCard.pitcherError ||
    "";

  const vsLeft = isPitcher
    ? rawText.match(/([0-9]+)%\s+VS\.LEFTY BATTERS/i)?.[1] ||
      existingCard.vsLeft ||
      ""
    : rawText.match(/([0-9]+)%\s+VS\.LEFTY PITCHERS/i)?.[1] ||
      existingCard.vsLeft ||
      "";

  const vsRight = isPitcher
    ? rawText.match(/([0-9]+)%\s+VS\.RIGHTY BATTERS/i)?.[1] ||
      existingCard.vsRight ||
      ""
    : rawText.match(/([0-9]+)%\s+VS\.RIGHTY PITCHERS/i)?.[1] ||
      existingCard.vsRight ||
      "";

  const powerVsLeft =
    rawText.match(/VS\.LEFTY PITCHERS\s*-\s*Power-([YN])/i)?.[1] ||
    existingCard.powerVsLeft ||
    "";

  const powerVsRight =
    rawText.match(/VS\.RIGHTY PITCHERS\s*-\s*Power-([YN])/i)?.[1] ||
    existingCard.powerVsRight ||
    "";

  const outcomeProfile = parseCardOutcomeProfile(rawText);

  const outcomeDescription = describeOutcomeProfile(
    outcomeProfile,
    isPitcher ? "pitcher" : "hitter"
  );

  return {
    ...existingCard,
    id: existingCard.id || `${name}-${Date.now()}`,
    name,
    year: 1980,
    cardType: isPitcher ? "pitcher" : "hitter",
    position,
    salary,
    balance,

    defense,
    running,
    stealing,
    bunting,
    hitAndRun,
    powerVsLeft,
    powerVsRight,

    throws,
    hold,
    starterEndurance,
    reliefEndurance,
    reliefAvailability,
    balk,
    wildPitch,
    pitcherDefense,
    pitcherError,

    vsLeft,
    vsRight,

    outcomeProfile,
    outcomeDescription,

    rawText,
    createdAt: existingCard.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function normalizeCard(card) {
  if (!card.rawText) {
    return {
      ...card,
      id: card.id || `${card.name || "Unknown Player"}-${Date.now()}`,
      cardType:
        card.cardType ||
        (String(card.position || "").toUpperCase() === "P"
          ? "pitcher"
          : "hitter"),
    };
  }

  return parseCard(card.rawText, card);
}

export default function CardImporter() {
  const [rawText, setRawText] = useState("");

  const [cards, setCards] = useState(() => {
    const saved = localStorage.getItem("stratPlayerCards1980");
    return saved ? JSON.parse(saved).map(normalizeCard) : [];
  });

  const [preview, setPreview] = useState(null);
  const [selectedLeagueId, setSelectedLeagueId] = useState("");

  useEffect(() => {
    localStorage.setItem("stratPlayerCards1980", JSON.stringify(cards));
  }, [cards]);

  const parsePreview = () => {
    if (!rawText.trim()) return;
    setPreview(parseCard(rawText));
  };

  const saveCard = () => {
    if (!rawText.trim()) return;

    const parsed = parseCard(rawText);

    const nextCards = [
      parsed,
      ...cards.filter((card) => card.name !== parsed.name),
    ];

    setCards(nextCards);
    setPreview(parsed);
    setRawText("");
  };

  const rebuildProfiles = () => {
    const rebuilt = cards.map((card) => normalizeCard(card));
    setCards(rebuilt);
  };

  const deleteCard = (cardToDelete) => {
    setCards(
      cards.filter((card) => {
        if (cardToDelete.id && card.id) {
          return card.id !== cardToDelete.id;
        }

        return card.name !== cardToDelete.name;
      })
    );
  };

  return (
    <div className="space-y-6">
      <div className="dashboard-panel p-6">
        <h1 className="text-2xl font-bold mb-2">Card Importer</h1>

        <p className="text-sm text-slate-500">
          Paste Strat 1980 player-card text and save parsed metadata for later
          analysis.
        </p>
      </div>

      <div className="dashboard-panel p-6 space-y-4">
        <h2 className="text-xl font-bold">Import Player Card</h2>

        <textarea
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          rows={14}
          className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 text-sm font-mono"
          placeholder="Paste full card text here..."
        />

        <div className="flex flex-wrap gap-2">
          <button
            onClick={parsePreview}
            className="bg-slate-200 hover:bg-slate-300 transition text-slate-800 px-4 py-2 rounded-lg"
          >
            Preview Parse
          </button>

          <button
            onClick={saveCard}
            className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg"
          >
            Save Card
          </button>

          <button
            onClick={rebuildProfiles}
            className="bg-indigo-100 hover:bg-indigo-200 transition text-indigo-900 px-4 py-2 rounded-lg"
          >
            Rebuild / Re-parse Saved Cards
          </button>
        </div>
      </div>

      <CoverageReport
        cards={cards}
        selectedLeagueId={selectedLeagueId}
        setSelectedLeagueId={setSelectedLeagueId}
      />

      {preview && (
        <div className="dashboard-panel p-6">
          <h2 className="text-xl font-bold mb-4">Parsed Preview</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <Field label="Name" value={preview.name} />
            <Field label="Position" value={preview.position} />
            <Field label="Salary" value={preview.salary} />
            <Field label="Balance" value={preview.balance} />
            <Field label="Defense" value={preview.defense} />
            <Field label="Running" value={preview.running} />
            <Field label="Stealing" value={preview.stealing} />
            <Field label="Bunting" value={preview.bunting} />
            <Field label="Hit & Run" value={preview.hitAndRun} />
            <Field label="VS Lefty %" value={preview.vsLeft} />
            <Field label="VS Righty %" value={preview.vsRight} />

            <Field
              label="Power vs L/R"
              value={`${preview.powerVsLeft || "?"}/${
                preview.powerVsRight || "?"
              }`}
            />

            <Field label="Card Type" value={preview.cardType} />
            <Field label="Throws" value={preview.throws} />
            <Field label="Hold" value={preview.hold} />
            <Field label="Starter Endurance" value={preview.starterEndurance} />

            <Field
              label="Relief"
              value={
                preview.reliefEndurance
                  ? `${preview.reliefEndurance}/${
                      preview.reliefAvailability || "?"
                    }`
                  : ""
              }
            />

            <Field
              label="Balk / WP"
              value={`${preview.balk || "?"}/${preview.wildPitch || "?"}`}
            />

            <Field
              label="Pitcher DEF / E"
              value={`${preview.pitcherDefense || "?"}/e${
                preview.pitcherError || "?"
              }`}
            />

            <Field label="Profile" value={preview.outcomeDescription} />
          </div>
        </div>
      )}

      <div className="dashboard-panel p-6">
        <h2 className="text-xl font-bold mb-4">Saved Cards</h2>

        {cards.length === 0 ? (
          <p className="text-sm text-slate-500">No cards saved yet.</p>
        ) : (
          <div className="space-y-3">
            {cards.map((card) => (
              <div
                key={card.id || card.name}
                className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/80"
              >
                <div className="flex justify-between gap-4">
                  <div>
                    <div className="font-bold text-slate-950">{card.name}</div>

                    <div className="text-sm text-slate-500">
                      {card.position} · {card.salary} · BAL {card.balance}
                    </div>

                    {card.cardType === "pitcher" ? (
                      <div className="text-xs text-slate-400 mt-1">
                        Throws {card.throws || "?"} · HOLD {card.hold || "?"} ·
                        S{card.starterEndurance || "?"} · R
                        {card.reliefEndurance || "?"}/
                        {card.reliefAvailability || "?"} · P-
                        {card.pitcherDefense || "?"}e{card.pitcherError || "?"}
                      </div>
                    ) : (
                      <div className="text-xs text-slate-400 mt-1">
                        DEF {card.defense || "?"} · RUN {card.running || "?"} ·
                        STL {card.stealing || "?"} · H&R{" "}
                        {card.hitAndRun || "?"}
                      </div>
                    )}

                    {card.outcomeDescription && (
                      <div className="text-xs text-slate-500 mt-1">
                        Profile: {card.outcomeDescription}
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => deleteCard(card)}
                    className="text-red-600 text-sm hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
      <div className="text-xs uppercase text-slate-400">{label}</div>

      <div className="font-semibold text-slate-900 mt-1">{value || "—"}</div>
    </div>
  );
}

function CoverageReport({ cards, selectedLeagueId, setSelectedLeagueId }) {
  const leagues = getSavedLeagues();

  const selectedLeague = leagues.find(
    (league) => String(league.id) === String(selectedLeagueId)
  );

  const hittersText =
    selectedLeague?.hittersText ||
    selectedLeague?.hitters ||
    selectedLeague?.hitterRoster ||
    "";

  const pitchersText =
    selectedLeague?.pitchersText ||
    selectedLeague?.pitchers ||
    selectedLeague?.pitcherRoster ||
    "";

  const rosterNames = parseRosterNames(hittersText);
  const pitcherNames = parsePitcherNames(pitchersText);

  const normalizedCardNames = cards
    .filter((card) => card.cardType !== "pitcher")
    .map((card) => card.name.toLowerCase());

  const normalizedPitcherCards = cards
    .filter((card) => card.cardType === "pitcher")
    .map((card) => card.name.toLowerCase());

  const coveredPlayers = rosterNames.filter((name) =>
    normalizedCardNames.includes(name.toLowerCase())
  );

  const missingPlayers = rosterNames.filter(
    (name) => !normalizedCardNames.includes(name.toLowerCase())
  );

  const coveredPitchers = pitcherNames.filter((name) =>
    normalizedPitcherCards.includes(name.toLowerCase())
  );

  const missingPitchers = pitcherNames.filter(
    (name) => !normalizedPitcherCards.includes(name.toLowerCase())
  );

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-4">Card Coverage</h2>

      <select
        value={selectedLeagueId}
        onChange={(e) => setSelectedLeagueId(e.target.value)}
        className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 mb-4"
      >
        <option value="">Select league/team</option>

        {leagues.map((league) => (
          <option key={league.id} value={league.id}>
            {league.name}
          </option>
        ))}
      </select>

      {selectedLeague && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard label="Hitters" value={rosterNames.length} />
            <StatCard label="Hitters Saved" value={coveredPlayers.length} />
            <StatCard label="Hitters Missing" value={missingPlayers.length} />
            <StatCard label="Pitchers" value={pitcherNames.length} />
            <StatCard label="Pitchers Saved" value={coveredPitchers.length} />
          </div>

          <div>
            <div className="font-semibold mb-2">Missing Hitters</div>

            {missingPlayers.length === 0 ? (
              <div className="text-sm text-green-700">
                All hitters have saved cards.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {missingPlayers.map((player) => (
                  <div
                    key={player}
                    className="bg-amber-100 text-amber-900 text-sm px-3 py-1 rounded-full"
                  >
                    {player}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-200">
            <div className="font-semibold mb-2">Missing Pitchers</div>

            {missingPitchers.length === 0 ? (
              <div className="text-sm text-green-700">
                All pitchers have saved cards.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {missingPitchers.map((player) => (
                  <div
                    key={player}
                    className="bg-sky-100 text-sky-900 text-sm px-3 py-1 rounded-full"
                  >
                    {player}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
      <div className="text-xs uppercase text-slate-400">{label}</div>

      <div className="text-2xl font-bold text-slate-900 mt-2">{value}</div>
    </div>
  );
}
