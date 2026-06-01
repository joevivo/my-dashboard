import { buildCardAwareLineup } from "./lineupEngine.js";
import { getCardMap, normalizeCardName } from "./cardStore.js";

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

  const missingCards = [];

  const gameLineup = lineup
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
    isPlayable: gameLineup.length >= 9 && missingCards.length === 0,
  };
}
