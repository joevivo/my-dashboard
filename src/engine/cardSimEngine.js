const STRAT_ROLL_WEIGHTS = {
  2: 1,
  3: 2,
  4: 3,
  5: 4,
  6: 5,
  7: 6,
  8: 5,
  9: 4,
  10: 3,
  11: 2,
  12: 1,
};

function normalizeHand(hand) {
  const value = String(hand || "").toUpperCase();

  if (value === "L" || value === "LEFT" || value === "LHP") return "L";
  return "R";
}

function getHitterSideForPitcherHand(pitcherHand) {
  return normalizeHand(pitcherHand) === "L" ? "vsLHP" : "vsRHP";
}

function getPitcherSideForBatterHand(batterHand) {
  return normalizeHand(batterHand) === "L" ? "vsLHP" : "vsRHP";
}

function getWeightedRandomRoll(random = Math.random) {
  const totalWeight = Object.values(STRAT_ROLL_WEIGHTS).reduce(
    (sum, weight) => sum + weight,
    0
  );

  let threshold = random() * totalWeight;

  for (const [roll, weight] of Object.entries(STRAT_ROLL_WEIGHTS)) {
    threshold -= weight;

    if (threshold <= 0) {
      return String(roll);
    }
  }

  return "7";
}

function pickCardSide(random = Math.random) {
  return random() < 0.5 ? "hitter" : "pitcher";
}

function getEventsForSide(card, side, roll) {
  return (card?.cardEvents || []).filter(
    (event) => event.side === side && String(event.roll) === String(roll)
  );
}

function resolveSplitOutcome(event, random = Math.random) {
  if (!event?.splitOutcomes?.length) {
    return {
      result: event?.result || "UNKNOWN",
      outcomeType: event?.outcomeType || "UNKNOWN",
      rawLine: event?.rawLine || "",
    };
  }

  const d20 = Math.floor(random() * 20) + 1;

  const split = event.splitOutcomes.find(
    (outcome) => d20 >= outcome.rangeStart && d20 <= outcome.rangeEnd
  );

  return {
    result: split?.result || event.result || "UNKNOWN",
    outcomeType: split?.outcomeType || event.outcomeType || "UNKNOWN",
    rawLine: event.rawLine || "",
    d20,
  };
}

export function resolvePlateAppearance({
  hitterCard,
  pitcherCard,
  pitcherHand = "R",
  batterHand = "R",
  random = Math.random,
} = {}) {
  const cardSide = pickCardSide(random);
  const roll = getWeightedRandomRoll(random);

  const hitterSide = getHitterSideForPitcherHand(pitcherHand);
  const pitcherSide = getPitcherSideForBatterHand(batterHand);

  const selectedCard = cardSide === "hitter" ? hitterCard : pitcherCard;
  const selectedSide = cardSide === "hitter" ? hitterSide : pitcherSide;

  const matchingEvents = getEventsForSide(selectedCard, selectedSide, roll);
  const event = matchingEvents[0];

  if (!event) {
    return {
      cardSide,
      roll,
      side: selectedSide,
      result: "OUT",
      outcomeType: "OUT",
      eventClass: "OUT",
      rawLine: "",
      defenseMeta: null,
      isXChance: false,
      isInjury: false,
      isBallparkSingle: false,
      isBallparkHomeRun: false,
      note: "No matching parsed card event found; treated as an out.",
    };
  }

  const resolved = resolveSplitOutcome(event, random);

  return {
    cardSide,
    roll,
    side: selectedSide,

    result: resolved.result,
    outcomeType: resolved.outcomeType,
    rawLine: resolved.rawLine,
    d20: resolved.d20 ?? null,

    eventClass: event.eventClass,
    defenseMeta: event.defenseMeta,
    isXChance: event.isXChance,
    isInjury: event.isInjury,
    isBallparkSingle: event.isBallparkSingle,
    isBallparkHomeRun: event.isBallparkHomeRun,
  };
}
