import { createInitialGameState } from "./gameStateEngine.js";
import { simulateHalfInning } from "./inningSimEngine.js";

export function simulateFullGame({
  awayLineup = [],
  homeLineup = [],
  awayPitcherCard,
  homePitcherCard,
  awayPitcherHand = "R",
  homePitcherHand = "R",
  innings = 9,
  random = Math.random,
  maxPlateAppearancesPerHalf = 100,
} = {}) {
  if (!awayLineup.length) {
    throw new Error("simulateFullGame requires an away lineup.");
  }

  if (!homeLineup.length) {
    throw new Error("simulateFullGame requires a home lineup.");
  }

  if (!awayPitcherCard) {
    throw new Error("simulateFullGame requires an away pitcher card.");
  }

  if (!homePitcherCard) {
    throw new Error("simulateFullGame requires a home pitcher card.");
  }

  let state = createInitialGameState();
  let awayLineupIndex = 0;
  let homeLineupIndex = 0;

  const halfInnings = [];

  while (state.inning <= innings) {
    const topHalf = simulateHalfInning({
      state,
      lineup: awayLineup,
      lineupIndex: awayLineupIndex,
      pitcherCard: homePitcherCard,
      pitcherHand: homePitcherHand,
      random,
      maxPlateAppearances: maxPlateAppearancesPerHalf,
    });

    halfInnings.push({
      inning: state.inning,
      half: "top",
      battingTeam: "away",
      result: topHalf,
    });

    state = topHalf.state;
    awayLineupIndex = topHalf.nextLineupIndex;

    if (topHalf.hitSafetyCap) {
      break;
    }

    const bottomHalf = simulateHalfInning({
      state,
      lineup: homeLineup,
      lineupIndex: homeLineupIndex,
      pitcherCard: awayPitcherCard,
      pitcherHand: awayPitcherHand,
      random,
      maxPlateAppearances: maxPlateAppearancesPerHalf,
    });

    halfInnings.push({
      inning: state.inning,
      half: "bottom",
      battingTeam: "home",
      result: bottomHalf,
    });

    state = bottomHalf.state;
    homeLineupIndex = bottomHalf.nextLineupIndex;

    if (bottomHalf.hitSafetyCap) {
      break;
    }
  }

  const plateAppearanceCount = halfInnings.reduce(
    (total, halfInning) => total + halfInning.result.plateAppearances.length,
    0
  );

  return {
    state,
    finalScore: {
      away: state.score.away,
      home: state.score.home,
    },
    awayLineupIndex,
    homeLineupIndex,
    halfInnings,
    plateAppearanceCount,
    inningsScheduled: innings,
    inningsCompleted: Math.min(innings, state.inning - 1),
    isTieAfterRegulation: state.score.away === state.score.home,
    hitSafetyCap: halfInnings.some((halfInning) => halfInning.result.hitSafetyCap),
  };
}
