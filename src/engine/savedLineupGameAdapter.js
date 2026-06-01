import { buildCardAwareLineup } from "./lineupEngine.js";
import { getCardMap, normalizeCardName } from "./cardStore.js";

function normalizeShorthandBats(value = "") {
  const upper = String(value || "").toUpperCase();

  if (["R", "L", "S"].includes(upper)) return upper;

  // Legacy opponent shorthand has used "D" in the batting-hand slot.
  // Treat it as left-handed for now so the pitcher-card side is at least deterministic.
  if (upper === "D") return "L";

  return "R";
}

function parseShorthandLineup(hittersText = "") {
  return String(hittersText || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/\s+/);

      if (parts.length < 3) return null;

      const fieldPos = String(parts[parts.length - 1] || "").toUpperCase();
      const batsToken = String(parts[parts.length - 2] || "").toUpperCase();
      const bats = normalizeShorthandBats(batsToken);
      const name = parts.slice(0, -2).join(" ");

      const validPositions = new Set([
        "C",
        "1B",
        "2B",
        "3B",
        "SS",
        "LF",
        "CF",
        "RF",
        "OF",
        "DH",
      ]);

      if (!name || !validPositions.has(fieldPos)) return null;
      if (!["R", "L", "S", "D"].includes(batsToken)) return null;

      return {
        name,
        bats,
        fieldPos,
        sourceLine: line,
      };
    })
    .filter(Boolean);
}

function attachCardsToLineup(lineup = [], cardMap = {}) {
  const missingCards = [];

  const gameLineup = lineup
    .slice(0, 9)
    .map((player, index) => {
      const card = cardMap[normalizeCardName(player.name)];

      if (!card) {
        missingCards.push(player.name);
        return null;
      }

      return {
        id: player.name,
        name: player.name,
        bats: player.bats || "R",
        fieldPos: player.fieldPos,
        lineupSlot: index + 1,
        card,
        sourcePlayer: player,
      };
    })
    .filter(Boolean);

  return {
    lineup: gameLineup,
    missingCards,
  };
}

export function buildSavedLineupForGame({
  hittersText = "",
  pitcherHand = "R",
  park,
  strategyProfile = "balanced",
  cards = [],
} = {}) {
  const cardMap = getCardMap(cards);

  const lineup = buildCardAwareLineup({
    hittersText,
    pitcherHand,
    park,
    strategyProfile,
  });

  const cardAwareResult = attachCardsToLineup(lineup, cardMap);

  const cardAwarePlayable =
    cardAwareResult.lineup.length >= 9 &&
    cardAwareResult.missingCards.length === 0;

  if (cardAwarePlayable) {
    return {
      ...cardAwareResult,
      sourceFormat: "cardAwareRoster",
      isPlayable: true,
    };
  }

  const shorthandLineup = parseShorthandLineup(hittersText);
  const shorthandResult = attachCardsToLineup(shorthandLineup, cardMap);

  const shorthandPlayable =
    shorthandResult.lineup.length >= 9 &&
    shorthandResult.missingCards.length === 0;

  if (shorthandLineup.length > 0) {
    return {
      ...shorthandResult,
      sourceFormat: "shorthandLineup",
      isPlayable: shorthandPlayable,
    };
  }

  return {
    ...cardAwareResult,
    sourceFormat: "cardAwareRoster",
    isPlayable: false,
  };
}
