export function normalizeCardName(name = "") {
  return String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

export function getAllCards() {
  const saved = localStorage.getItem("stratPlayerCards1980");

  try {
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

export function getCardMap(cards = getAllCards()) {
  return cards.reduce((map, card) => {
    if (card?.name) {
      map[normalizeCardName(card.name)] = card;
    }

    return map;
  }, {});
}

export function getCardByName(name, cards = getAllCards()) {
  const cardMap = getCardMap(cards);
  return cardMap[normalizeCardName(name)] || null;
}

export function getHitterCard(name, cards = getAllCards()) {
  const card = getCardByName(name, cards);
  return card && card.cardType !== "pitcher" ? card : null;
}

export function getPitcherCard(name, cards = getAllCards()) {
  const card = getCardByName(name, cards);
  return card && card.cardType === "pitcher" ? card : null;
}

export function getCardsByType(cardType, cards = getAllCards()) {
  return cards.filter((card) => card.cardType === cardType);
}

export function saveAllCards(cards = []) {
  localStorage.setItem("stratPlayerCards1980", JSON.stringify(cards));
  return cards;
}

export function replaceCard(card, cards = getAllCards()) {
  if (!card?.name) return cards;

  const nextCards = [
    card,
    ...cards.filter((existingCard) => existingCard.name !== card.name),
  ];

  saveAllCards(nextCards);
  return nextCards;
}

export function deleteCard(cardToDelete, cards = getAllCards()) {
  const nextCards = cards.filter((card) => {
    if (cardToDelete?.id && card?.id) {
      return card.id !== cardToDelete.id;
    }

    return card.name !== cardToDelete?.name;
  });

  saveAllCards(nextCards);
  return nextCards;
}
