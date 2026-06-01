import { resolveAndApplyPlateAppearance } from "./plateAppearanceGameEngine.js";

function getLineupEntry(lineup = [], lineupIndex = 0) {
  if (!lineup.length) return null;
  return lineup[lineupIndex % lineup.length];
}

export function simulateHalfInning({
  state,
  lineup = [],
  lineupIndex = 0,
  pitcherCard,
  pitcherHand = "R",
  random = Math.random,
  maxPlateAppearances = 100,
} = {}) {
  if (!state) {
    throw new Error("simulateHalfInning requires a game state.");
  }

  if (!lineup.length) {
    throw new Error("simulateHalfInning requires at least one lineup entry.");
  }

  let currentState = state;
  let currentLineupIndex = lineupIndex;
  const startingHalf = state.half;
  const plateAppearances = [];

  while (
    currentState.half === startingHalf &&
    plateAppearances.length < maxPlateAppearances
  ) {
    const batter = getLineupEntry(lineup, currentLineupIndex);

    const result = resolveAndApplyPlateAppearance({
      state: currentState,
      hitterCard: batter.card,
      pitcherCard,
      pitcherHand,
      batterHand: batter.bats || "R",
      batterId: batter.id,
      batterName: batter.name,
      random,
    });

    plateAppearances.push({
      lineupIndex: currentLineupIndex,
      batterId: batter.id,
      batterName: batter.name,
      plateAppearance: result.plateAppearance,
      summary: result.summary,
      stateAfter: result.state,
    });

    currentState = result.state;
    currentLineupIndex += 1;
  }

  const endedByOuts = currentState.half !== startingHalf;
  const hitSafetyCap =
    plateAppearances.length >= maxPlateAppearances && !endedByOuts;

  return {
    state: currentState,
    nextLineupIndex: currentLineupIndex,
    plateAppearances,
    endedByOuts,
    hitSafetyCap,
  };
}
