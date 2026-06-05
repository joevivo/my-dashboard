import { normalizeCardName } from "./cardStore";

export function getNameParts(name = "") {
  const cleaned = String(name)
    .replace(/\s+/g, " ")
    .replace(/\./g, "")
    .trim();

  const commaMatch = cleaned.match(/^(.+),\s*(.+)$/);

  if (commaMatch) {
    return {
      first: commaMatch[2].trim(),
      last: commaMatch[1].trim(),
      normalized: normalizeCardName(`${commaMatch[2]} ${commaMatch[1]}`),
    };
  }

  const parts = cleaned.split(" ").filter(Boolean);

  return {
    first: parts[0] || "",
    last: parts[parts.length - 1] || "",
    normalized: normalizeCardName(cleaned),
  };
}

export function buildCardIndex(cards = []) {
  return cards.reduce(
    (index, card) => {
      if (!card?.name) return index;

      const parts = getNameParts(card.name);
      const exactKey = parts.normalized;
      const initialLastKey = normalizeCardName(
        `${parts.first.charAt(0)} ${parts.last}`
      );

      index.byExactName[exactKey] = card;

      if (!index.byInitialLast[initialLastKey]) {
        index.byInitialLast[initialLastKey] = [];
      }

      index.byInitialLast[initialLastKey].push(card);

      return index;
    },
    {
      byExactName: {},
      byInitialLast: {},
    }
  );
}

export function findMatchingCard(player = {}, cardsOrIndex = []) {
  const index = Array.isArray(cardsOrIndex)
    ? buildCardIndex(cardsOrIndex)
    : cardsOrIndex;

  const parts = getNameParts(player.name);
  const exactMatch = index.byExactName[parts.normalized];

  if (exactMatch) {
    return {
      cardFound: true,
      confidence: 1,
      matchType: "exact",
      card: exactMatch,
    };
  }

  const initialLastKey = normalizeCardName(
    `${parts.first.charAt(0)} ${parts.last}`
  );

  const candidates = index.byInitialLast[initialLastKey] || [];

  if (candidates.length === 1) {
    return {
      cardFound: true,
      confidence: 0.85,
      matchType: "first-initial-last",
      card: candidates[0],
    };
  }

  return {
    cardFound: false,
    confidence: 0,
    matchType: candidates.length > 1 ? "ambiguous" : "none",
    candidates,
    card: null,
  };
}

export function linkRosterToCards(roster = [], cards = []) {
  const index = buildCardIndex(cards);

  return roster.map((player) => {
    const match = findMatchingCard(player, index);

    return {
      ...player,
      cardFound: match.cardFound,
      cardMatchConfidence: match.confidence,
      cardMatchType: match.matchType,
      cardId: match.card?.id || null,
      cardName: match.card?.name || null,
      cardType: match.card?.cardType || null,
      cardPosition: match.card?.position || null,
      cardBalance: match.card?.balance || null,
      cardDefense: match.card?.defense || null,
      cardRunning: match.card?.running || null,
      cardStealing: match.card?.stealing || null,
      cardPowerVsLeft: match.card?.powerVsLeft || null,
      cardPowerVsRight: match.card?.powerVsRight || null,
      cardProbabilityProfile: match.card?.cardProbabilityProfile || null,
      cardEventSummary: match.card?.cardEventSummary || null,
    };
  });
}
