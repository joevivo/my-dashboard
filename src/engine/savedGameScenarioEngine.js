import { simulateFullGame } from "./fullGameSimEngine.js";
import { buildSavedLineupForGame } from "./savedLineupGameAdapter.js";
import { getPitcherCard } from "./cardStore.js";

function getPitcherNameFromStarter(starter = {}) {
  const rawName =
    typeof starter === "string"
      ? starter
      : starter.name || starter.pitcherName || starter.playerName || starter.raw || "";

  const tokens = String(rawName || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (!tokens.length) return "";

  const cleanedTokens = tokens.filter((token, index) => {
    const upper = token.toUpperCase();

    if (index === 0 && ["SP", "RP", "P"].includes(upper)) return false;
    if (["L", "R"].includes(upper)) return false;
    if (/^G\d+$/i.test(token)) return false;
    if (/^S\d+$/i.test(token)) return false;
    if (/^R\d+$/i.test(token)) return false;
    if (/^E$/i.test(token)) return false;
    if (/^-?\d+$/i.test(token)) return false;
    if (/^\d+[LR]$/i.test(token)) return false;
    if (/^\d+(\.\d+)?$/.test(token)) return false;

    return true;
  });

  return cleanedTokens.join(" ");
}

export function simulateSavedGameScenario({
  team = {},
  opponent = {},
  cards = [],
  awayStarter,
  homeStarter,
  awayPitcherHand = "R",
  homePitcherHand = "R",
  innings = 9,
  random = Math.random,
  strategyProfile = "balanced",
  maxPlateAppearancesPerHalf = 100,
} = {}) {
  const awayHittersText = team.hittersText || team.hitters || team.hitterRoster || "";
  const homeHittersText =
    opponent.lineupText ||
    opponent.hittersText ||
    opponent.hitters ||
    opponent.hitterRoster ||
    "";

  const awayStarterName = getPitcherNameFromStarter(awayStarter);
  const homeStarterName = getPitcherNameFromStarter(homeStarter);

  const awayPitcherCard = getPitcherCard(awayStarterName, cards);
  const homePitcherCard = getPitcherCard(homeStarterName, cards);

  const awayLineupResult = buildSavedLineupForGame({
    hittersText: awayHittersText,
    pitcherHand: homePitcherHand,
    strategyProfile,
    cards,
  });

  const homeLineupResult = buildSavedLineupForGame({
    hittersText: homeHittersText,
    pitcherHand: awayPitcherHand,
    strategyProfile,
    cards,
  });

  const missing = {
    awayHitters: awayLineupResult.missingCards,
    homeHitters: homeLineupResult.missingCards,
    awayStarter: awayPitcherCard ? [] : [awayStarterName || "Away starter"],
    homeStarter: homePitcherCard ? [] : [homeStarterName || "Home starter"],
  };

  const isPlayable =
    awayLineupResult.isPlayable &&
    homeLineupResult.isPlayable &&
    Boolean(awayPitcherCard) &&
    Boolean(homePitcherCard);

  if (!isPlayable) {
    return {
      isPlayable: false,
      missing,
      awayLineup: awayLineupResult.lineup,
      homeLineup: homeLineupResult.lineup,
      game: null,
    };
  }

  const game = simulateFullGame({
    awayLineup: awayLineupResult.lineup,
    homeLineup: homeLineupResult.lineup,
    awayPitcherCard,
    homePitcherCard,
    awayPitcherHand,
    homePitcherHand,
    innings,
    random,
    maxPlateAppearancesPerHalf,
  });

  return {
    isPlayable: true,
    missing,
    awayLineup: awayLineupResult.lineup,
    homeLineup: homeLineupResult.lineup,
    game,
  };
}
