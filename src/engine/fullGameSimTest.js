import { simulateFullGame } from "./fullGameSimEngine.js";

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

export function runDeterministicFullGameSimTests() {
  const pitcherOutCard = cardWithEvent({
    name: "Pitcher OUT Placeholder",
    result: "OUT",
    outcomeType: "OUT",
  });

  const awayLineup = [
    lineupEntry("A1", "HOME_RUN"),
    lineupEntry("A2", "OUT"),
    lineupEntry("A3", "OUT"),
    lineupEntry("A4", "OUT"),
  ];

  const homeLineup = [
    lineupEntry("H1", "OUT"),
    lineupEntry("H2", "OUT"),
    lineupEntry("H3", "OUT"),
  ];

  const oneInningResult = simulateFullGame({
    awayLineup,
    homeLineup,
    awayPitcherCard: pitcherOutCard,
    homePitcherCard: pitcherOutCard,
    awayPitcherHand: "R",
    homePitcherHand: "R",
    innings: 1,
    random: createFixedRandom([
      0.1, 0.5, // A1 HR
      0.1, 0.5, // A2 OUT
      0.1, 0.5, // A3 OUT
      0.1, 0.5, // A4 OUT
      0.1, 0.5, // H1 OUT
      0.1, 0.5, // H2 OUT
      0.1, 0.5, // H3 OUT
    ]),
  });

  const twoInningResult = simulateFullGame({
    awayLineup: [
      lineupEntry("A1", "OUT"),
      lineupEntry("A2", "OUT"),
      lineupEntry("A3", "OUT"),
    ],
    homeLineup: [
      lineupEntry("H1", "OUT"),
      lineupEntry("H2", "OUT"),
      lineupEntry("H3", "OUT"),
    ],
    awayPitcherCard: pitcherOutCard,
    homePitcherCard: pitcherOutCard,
    innings: 2,
    random: createFixedRandom([
      0.1, 0.5, 0.1, 0.5, 0.1, 0.5,
      0.1, 0.5, 0.1, 0.5, 0.1, 0.5,
      0.1, 0.5, 0.1, 0.5, 0.1, 0.5,
      0.1, 0.5, 0.1, 0.5, 0.1, 0.5,
    ]),
  });

  const assertions = [
    assertEqual(oneInningResult.finalScore.away, 1, "one-inning game gives away one run"),
    assertEqual(oneInningResult.finalScore.home, 0, "one-inning game gives home zero runs"),
    assertEqual(oneInningResult.halfInnings.length, 2, "one-inning game has two half-innings"),
    assertEqual(oneInningResult.plateAppearanceCount, 7, "one-inning game records seven plate appearances"),
    assertEqual(oneInningResult.awayLineupIndex, 4, "away lineup advances four batters"),
    assertEqual(oneInningResult.homeLineupIndex, 3, "home lineup advances three batters"),
    assertEqual(oneInningResult.inningsCompleted, 1, "one inning completed"),
    assertEqual(oneInningResult.state.inning, 2, "state advances to inning two after one completed inning"),
    assertEqual(oneInningResult.state.half, "top", "state returns to top after completed inning"),
    assertEqual(oneInningResult.isTieAfterRegulation, false, "one-inning game is not tied"),
    assertEqual(oneInningResult.hitSafetyCap, false, "one-inning game does not hit safety cap"),

    assertEqual(twoInningResult.finalScore.away, 0, "two-inning all-out game away score is zero"),
    assertEqual(twoInningResult.finalScore.home, 0, "two-inning all-out game home score is zero"),
    assertEqual(twoInningResult.halfInnings.length, 4, "two-inning game has four half-innings"),
    assertEqual(twoInningResult.plateAppearanceCount, 12, "two-inning game records twelve plate appearances"),
    assertEqual(twoInningResult.inningsCompleted, 2, "two innings completed"),
    assertEqual(twoInningResult.state.inning, 3, "state advances to inning three after two completed innings"),
    assertEqual(twoInningResult.isTieAfterRegulation, true, "scoreless two-inning game is tied"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
