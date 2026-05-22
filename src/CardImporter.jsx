import React, { useEffect, useState } from "react";
import {
  getAllCards,
  saveAllCards,
  replaceCard,
  deleteCard as deleteStoredCard,
} from "./engine/cardStore";
import {
  parseCardOutcomeProfile,
  describeOutcomeProfile,
} from "./engine/cardOutcomeParser";
import {
  parseCardEvents,
  summarizeCardEvents,
} from "./engine/cardEventParser";
import {
  compareCardSides,
} from "./engine/cardProbabilityEngine";
import {
  combineCardMetrics,
  scoreCombinedMatchup,
} from "./engine/cardMatchupEngine";

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
  const cardEvents = parseCardEvents(rawText);
  const cardEventSummary = summarizeCardEvents(cardEvents);
  const cardProbabilityProfile = compareCardSides(cardEventSummary);

  const outcomeDescription = describeOutcomeProfile(
    outcomeProfile,
    cardEvents,
    cardEventSummary,
    cardProbabilityProfile,
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
    cardEvents,
    cardEventSummary,
    cardProbabilityProfile,
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
    saveAllCards(cards);
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

  const exportStratData = () => {
    const backup = {
      exportedAt: new Date().toISOString(),
      source: "my-dashboard",
      version: 1,
      data: {
        stratPlayerCards1980: JSON.parse(
          localStorage.getItem("stratPlayerCards1980") || "[]"
        ),
        stratLeagues: JSON.parse(localStorage.getItem("stratLeagues") || "[]"),
        stratOpponents: JSON.parse(
          localStorage.getItem("stratOpponents") || "[]"
        ),
      },
    };

    const blob = new Blob([JSON.stringify(backup, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `strat-data-backup-${new Date()
      .toISOString()
      .slice(0, 10)}.json`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
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
            onClick={exportStratData}
            className="bg-emerald-700 hover:bg-emerald-800 transition text-white px-4 py-2 rounded-lg"
          >
            Export Strat Backup
          </button>

          <button
            onClick={rebuildProfiles}
            className="bg-indigo-100 hover:bg-indigo-200 transition text-indigo-900 px-4 py-2 rounded-lg"
          >
            Rebuild / Re-parse Saved Cards
          </button>
        </div>
      </div>

      <CardMatchupTester cards={cards} />

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

            <Field
              label="Parsed Events"
              value={
                preview.cardEventSummary
                  ? `${preview.cardEventSummary.total} total | RHP ${
                      preview.cardEventSummary.bySide?.vsRHP || 0
                    } | LHP ${preview.cardEventSummary.bySide?.vsLHP || 0}`
                  : ""
              }
            />

            <Field
              label="X / Injury"
              value={
                preview.cardEventSummary
                  ? `${preview.cardEventSummary.xChances || 0} X | ${
                      preview.cardEventSummary.injuryEvents || 0
                    } injury`
                  : ""
              }
            />

            <Field
              label="Split Events"
              value={
                preview.cardEventSummary
                  ? `${preview.cardEventSummary.splitEvents || 0} grouped splits`
                  : ""
              }
            />

            <Field
              label="Outcome Breakdown"
              value={
                preview.cardEventSummary
                  ? `HR ${preview.cardEventSummary.byOutcome?.HOME_RUN || 0} | SI ${
                      preview.cardEventSummary.byOutcome?.SINGLE || 0
                    } | DO ${preview.cardEventSummary.byOutcome?.DOUBLE || 0} | BB ${
                      preview.cardEventSummary.byOutcome?.WALK || 0
                    } | K ${preview.cardEventSummary.byOutcome?.STRIKEOUT || 0}`
                  : ""
              }
            />

            <Field
              label="vs LHP Outcomes"
              value={
                preview.cardEventSummary
                  ? `HR ${
                      preview.cardEventSummary.bySideOutcome?.vsLHP?.HOME_RUN || 0
                    } | SI ${
                      preview.cardEventSummary.bySideOutcome?.vsLHP?.SINGLE || 0
                    } | DO ${
                      preview.cardEventSummary.bySideOutcome?.vsLHP?.DOUBLE || 0
                    } | BB ${
                      preview.cardEventSummary.bySideOutcome?.vsLHP?.WALK || 0
                    } | K ${
                      preview.cardEventSummary.bySideOutcome?.vsLHP?.STRIKEOUT || 0
                    }`
                  : ""
              }
            />

            <Field
              label="vs RHP Outcomes"
              value={
                preview.cardEventSummary
                  ? `HR ${
                      preview.cardEventSummary.bySideOutcome?.vsRHP?.HOME_RUN || 0
                    } | SI ${
                      preview.cardEventSummary.bySideOutcome?.vsRHP?.SINGLE || 0
                    } | DO ${
                      preview.cardEventSummary.bySideOutcome?.vsRHP?.DOUBLE || 0
                    } | BB ${
                      preview.cardEventSummary.bySideOutcome?.vsRHP?.WALK || 0
                    } | K ${
                      preview.cardEventSummary.bySideOutcome?.vsRHP?.STRIKEOUT || 0
                    }`
                  : ""
              }
            />

            <Field
              label="vs LHP Shape"
              value={
                preview.cardEventSummary
                  ? "OB " +
                    (preview.cardEventSummary.bySideShape?.vsLHP?.onBase || 0) +
                    " | XBH " +
                    (preview.cardEventSummary.bySideShape?.vsLHP?.extraBase || 0) +
                    " | Outs " +
                    (preview.cardEventSummary.bySideShape?.vsLHP?.outs || 0) +
                    " | K " +
                    (preview.cardEventSummary.bySideShape?.vsLHP?.strikeouts || 0)
                  : ""
              }
            />

            <Field
              label="vs RHP Shape"
              value={
                preview.cardEventSummary
                  ? "OB " +
                    (preview.cardEventSummary.bySideShape?.vsRHP?.onBase || 0) +
                    " | XBH " +
                    (preview.cardEventSummary.bySideShape?.vsRHP?.extraBase || 0) +
                    " | Outs " +
                    (preview.cardEventSummary.bySideShape?.vsRHP?.outs || 0) +
                    " | K " +
                    (preview.cardEventSummary.bySideShape?.vsRHP?.strikeouts || 0)
                  : ""
              }
            />

            <Field
              label="vs LHP Weighted"
              value={
                preview.cardEventSummary
                  ? "OB " +
                    ((preview.cardEventSummary.bySideWeighted?.vsLHP?.onBase || 0) * 100).toFixed(1) +
                    "% | XBH " +
                    ((preview.cardEventSummary.bySideWeighted?.vsLHP?.extraBase || 0) * 100).toFixed(1) +
                    "% | HR " +
                    ((preview.cardEventSummary.bySideWeighted?.vsLHP?.homeRuns || 0) * 100).toFixed(1) +
                    "% | K " +
                    ((preview.cardEventSummary.bySideWeighted?.vsLHP?.strikeouts || 0) * 100).toFixed(1) +
                    "%"
                  : ""
              }
            />

            <Field
              label="vs RHP Weighted"
              value={
                preview.cardEventSummary
                  ? "OB " +
                    ((preview.cardEventSummary.bySideWeighted?.vsRHP?.onBase || 0) * 100).toFixed(1) +
                    "% | XBH " +
                    ((preview.cardEventSummary.bySideWeighted?.vsRHP?.extraBase || 0) * 100).toFixed(1) +
                    "% | HR " +
                    ((preview.cardEventSummary.bySideWeighted?.vsRHP?.homeRuns || 0) * 100).toFixed(1) +
                    "% | K " +
                    ((preview.cardEventSummary.bySideWeighted?.vsRHP?.strikeouts || 0) * 100).toFixed(1) +
                    "%"
                  : ""
              }
            />

            <Field
              label="vs LHP Weighted Outcomes"
              value={
                preview.cardEventSummary
                  ? "HR " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsLHP?.HOME_RUN || 0) * 100).toFixed(1) +
                    "% | SI " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsLHP?.SINGLE || 0) * 100).toFixed(1) +
                    "% | DO " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsLHP?.DOUBLE || 0) * 100).toFixed(1) +
                    "% | BB " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsLHP?.WALK || 0) * 100).toFixed(1) +
                    "% | K " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsLHP?.STRIKEOUT || 0) * 100).toFixed(1) +
                    "%"
                  : ""
              }
            />

            <Field
              label="vs RHP Weighted Outcomes"
              value={
                preview.cardEventSummary
                  ? "HR " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsRHP?.HOME_RUN || 0) * 100).toFixed(1) +
                    "% | SI " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsRHP?.SINGLE || 0) * 100).toFixed(1) +
                    "% | DO " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsRHP?.DOUBLE || 0) * 100).toFixed(1) +
                    "% | BB " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsRHP?.WALK || 0) * 100).toFixed(1) +
                    "% | K " +
                    ((preview.cardEventSummary.bySideWeightedOutcome?.vsRHP?.STRIKEOUT || 0) * 100).toFixed(1) +
                    "%"
                  : ""
              }
            />

            <Field
              label={
                preview.cardType === "pitcher"
                  ? "vs LHB Allowed Score"
                  : "vs LHP Card Score"
              }
              value={
                preview.cardProbabilityProfile
                  ? preview.cardProbabilityProfile.vsLHP.score.toFixed(1)
                  : ""
              }
            />

            <Field
              label={
                preview.cardType === "pitcher"
                  ? "vs RHB Allowed Score"
                  : "vs RHP Card Score"
              }
              value={
                preview.cardProbabilityProfile
                  ? preview.cardProbabilityProfile.vsRHP.score.toFixed(1)
                  : ""
              }
            />

          <Field
            label="Hitter Card Input"
            value={
              "OB " +
              formatPct(matchup.hitterMetrics?.onBase) +
              " | XBH " +
              formatPct(matchup.hitterMetrics?.extraBase) +
              " | HR " +
              formatPct(matchup.hitterMetrics?.homeRuns) +
              " | K " +
              formatPct(matchup.hitterMetrics?.strikeouts)
            }
          />

          <Field
            label="Pitcher Card Allowed"
            value={
              "OB " +
              formatPct(matchup.pitcherMetrics?.onBase) +
              " | XBH " +
              formatPct(matchup.pitcherMetrics?.extraBase) +
              " | HR " +
              formatPct(matchup.pitcherMetrics?.homeRuns) +
              " | K " +
              formatPct(matchup.pitcherMetrics?.strikeouts)
            }
          />

            <Field
              label="Park SI / HR"
              value={
                preview.cardEventSummary
                  ? `${preview.cardEventSummary.ballparkSingles || 0} SI | ${
                      preview.cardEventSummary.ballparkHomeRuns || 0
                    } HR`
                  : ""
              }
            />
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


function CardMatchupTester({ cards }) {
  const hitters = cards.filter((card) => card.cardType !== "pitcher");
  const pitchers = cards.filter((card) => card.cardType === "pitcher");

  const [selectedHitterName, setSelectedHitterName] = useState("");
  const [selectedPitcherName, setSelectedPitcherName] = useState("");

  const selectedHitter = hitters.find((card) => card.name === selectedHitterName);
  const selectedPitcher = pitchers.find((card) => card.name === selectedPitcherName);

  const getBatterHand = (card) => {
    if (card?.bats) return card.bats;

    const rawMatch = String(card?.rawText || "").match(/\b([LSR])\s*\|/);
    return rawMatch?.[1] || "R";
  };

  const matchup =
    selectedHitter && selectedPitcher
      ? combineCardMetrics({
          hitterProfile: selectedHitter.cardProbabilityProfile,
          pitcherProfile: selectedPitcher.cardProbabilityProfile,
          hitterBats: getBatterHand(selectedHitter),
          pitcherThrows: selectedPitcher.throws,
        })
      : null;

  const formatPct = (value) => `${((value || 0) * 100).toFixed(1)}%`;

  const getMatchupRead = (score) => {
    if (score >= 40) return "Strong hitter edge";
    if (score >= 30) return "Hitter edge";
    if (score >= 20) return "Neutral / playable";
    if (score >= 10) return "Pitcher edge";
    return "Strong pitcher edge";
  };

  const matchupScore = matchup ? scoreCombinedMatchup(matchup) : null;

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-4">Card Matchup Tester</h2>

      <p className="text-sm text-slate-500 mb-4">
        Preview-only comparison using saved card probability profiles.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <select
          value={selectedHitterName}
          onChange={(event) => setSelectedHitterName(event.target.value)}
          className="border border-slate-200 bg-white/80 rounded-lg p-2.5"
        >
          <option value="">Select hitter</option>
          {hitters.map((card) => (
            <option key={card.id || card.name} value={card.name}>
              {card.name}
            </option>
          ))}
        </select>

        <select
          value={selectedPitcherName}
          onChange={(event) => setSelectedPitcherName(event.target.value)}
          className="border border-slate-200 bg-white/80 rounded-lg p-2.5"
        >
          <option value="">Select pitcher</option>
          {pitchers.map((card) => (
            <option key={card.id || card.name} value={card.name}>
              {card.name}
            </option>
          ))}
        </select>
      </div>

      {matchup ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <Field
            label="Hitter Card Used"
            value={matchup.hitterSide === "vsLHP" ? "vs LHP" : "vs RHP"}
          />

          <Field
            label="Pitcher Card Used"
            value={matchup.pitcherSide === "vsLHP" ? "vs LHB" : "vs RHB"}
          />

          <Field
            label="Hitter Card Input"
            value={
              "OB " +
              formatPct(matchup.hitterMetrics?.onBase) +
              " | XBH " +
              formatPct(matchup.hitterMetrics?.extraBase) +
              " | HR " +
              formatPct(matchup.hitterMetrics?.homeRuns) +
              " | K " +
              formatPct(matchup.hitterMetrics?.strikeouts)
            }
          />

          <Field
            label="Pitcher Card Allowed"
            value={
              "OB " +
              formatPct(matchup.pitcherMetrics?.onBase) +
              " | XBH " +
              formatPct(matchup.pitcherMetrics?.extraBase) +
              " | HR " +
              formatPct(matchup.pitcherMetrics?.homeRuns) +
              " | K " +
              formatPct(matchup.pitcherMetrics?.strikeouts)
            }
          />

          <Field label="Combined OB" value={formatPct(matchup.onBase)} />
          <Field label="Combined XBH" value={formatPct(matchup.extraBase)} />
          <Field label="Combined HR" value={formatPct(matchup.homeRuns)} />
          <Field label="Combined K" value={formatPct(matchup.strikeouts)} />

          <Field
            label="Matchup Score"
            value={matchupScore.toFixed(1)}
          />

          <Field
            label="Matchup Read"
            value={getMatchupRead(matchupScore)}
          />
        </div>
      ) : (
        <p className="text-sm text-slate-500">
          Select one saved hitter and one saved pitcher to preview a card-based matchup.
        </p>
      )}
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






















