import { createInitialGameState } from "./gameStateEngine.js";
import { simulateHalfInning } from "./inningSimEngine.js";

function assertEqual(actual, expected, label) {
  return {
    label,
    passed: actual === expected,
    expected,
    actual,
  };
}

function createFixedRandom(values = []) {
  let index = 0;

  return function fixedRandom() {
    const value = values[index];
    index += 1;
    return value ?? 0;
  };
}

function cardWithEvent({ name, side = "vsRHP", roll = "7", result, outcomeType }) {
  return {
    name,
    cardEvents: [
      {
        side,
        roll,
        result,
        outcomeType,
        eventClass: "RESOLVED",
        defenseMeta: null,
        rawLine: `${roll} ${result}`,
        splitOutcomes: [],
        isXChance: false,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };
}

function lineupEntry(id, outcomeType) {
  return {
    id,
    name: id,
    bats: "R",
    card: cardWithEvent({
      name: `${id} Card`,
      result: outcomeType,
      outcomeType,
    }),
  };
}

export function runDeterministicInningSimTests() {
  const pitcherCard = cardWithEvent({
    name: "Pitcher Placeholder",
    result: "OUT",
    outcomeType: "OUT",
  });

  const lineup = [
    lineupEntry("B1", "SINGLE"),
    lineupEntry("B2", "HOME_RUN"),
    lineupEntry("B3", "OUT"),
    lineupEntry("B4", "OUT"),
    lineupEntry("B5", "OUT"),
  ];

  const topHalfResult = simulateHalfInning({
    state: createInitialGameState(),
    lineup,
    lineupIndex: 0,
    pitcherCard,
    pitcherHand: "R",
    random: createFixedRandom([
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
    ]),
  });

  const bottomHalfResult = simulateHalfInning({
    state: createInitialGameState({
      inning: 1,
      half: "bottom",
    }),
    lineup: [
      lineupEntry("H1", "OUT"),
      lineupEntry("H2", "OUT"),
      lineupEntry("H3", "OUT"),
    ],
    lineupIndex: 7,
    pitcherCard,
    pitcherHand: "R",
    random: createFixedRandom([
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
    ]),
  });

  const assertions = [
    assertEqual(topHalfResult.endedByOuts, true, "top half ends by outs"),
    assertEqual(topHalfResult.hitSafetyCap, false, "top half does not hit safety cap"),
    assertEqual(topHalfResult.plateAppearances.length, 5, "top half records five plate appearances"),
    assertEqual(topHalfResult.nextLineupIndex, 5, "top half advances lineup index by five"),
    assertEqual(topHalfResult.state.score.away, 2, "single plus home run scores two runs"),
    assertEqual(topHalfResult.state.score.home, 0, "top half leaves home score unchanged"),
    assertEqual(topHalfResult.state.half, "bottom", "top half advances to bottom"),
    assertEqual(topHalfResult.state.inning, 1, "top half keeps inning number"),
    assertEqual(topHalfResult.state.outs, 0, "top half resets outs after third out"),
    assertEqual(topHalfResult.state.runners.first, null, "top half clears first after inning ends"),
    assertEqual(topHalfResult.state.runners.second, null, "top half clears second after inning ends"),
    assertEqual(topHalfResult.state.runners.third, null, "top half clears third after inning ends"),

    assertEqual(bottomHalfResult.endedByOuts, true, "bottom half ends by outs"),
    assertEqual(bottomHalfResult.plateAppearances.length, 3, "bottom half records three plate appearances"),
    assertEqual(bottomHalfResult.nextLineupIndex, 10, "bottom half advances lineup index from supplied index"),
    assertEqual(bottomHalfResult.state.half, "top", "bottom half advances to top"),
    assertEqual(bottomHalfResult.state.inning, 2, "bottom half advances inning number"),
    assertEqual(bottomHalfResult.state.outs, 0, "bottom half resets outs after third out"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
