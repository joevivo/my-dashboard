import { simulateFullGame } from "./fullGameSimEngine.js";
import { buildSavedLineupForGame } from "./savedLineupGameAdapter.js";
import { getPitcherCard } from "./cardStore.js";

function getPitcherNameFromStarter(starter = {}) {
  if (!starter) return "";

  if (typeof starter === "string") return starter;

  return starter.name || starter.pitcherName || starter.playerName || "";
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
