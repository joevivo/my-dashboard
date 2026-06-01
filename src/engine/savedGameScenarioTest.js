import { simulateSavedGameScenario } from "./savedGameScenarioEngine.js";

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

function hitterCard(name, outcomeType = "OUT") {
  return {
    name,
    cardType: "hitter",
    cardEvents: [
      {
        side: "vsRHP",
        roll: "7",
        result: outcomeType,
        outcomeType,
        eventClass: "RESOLVED",
        defenseMeta: null,
        rawLine: `7 ${outcomeType}`,
        splitOutcomes: [],
        isXChance: false,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };
}

function pitcherCard(name) {
  return {
    name,
    cardType: "pitcher",
    cardEvents: [
      {
        side: "vsRHP",
        roll: "7",
        result: "OUT",
        outcomeType: "OUT",
        eventClass: "RESOLVED",
        defenseMeta: null,
        rawLine: "7 OUT",
        splitOutcomes: [],
        isXChance: false,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };
}

function rosterText(prefix) {
  return [
    `C R 2 ${prefix} One 0.350 0.340 4 3`,
    `1B L 3 ${prefix} Two 0.360 0.330 7 2`,
    `2B R 2 ${prefix} Three 0.345 0.355 3 5`,
    `3B R 3 ${prefix} Four 0.340 0.360 6 3`,
    `SS S 2 ${prefix} Five 0.330 0.335 3 6`,
    `LF L 3 ${prefix} Six 0.370 0.320 5 7`,
    `CF R 2 ${prefix} Seven 0.360 0.350 4 8`,
    `RF L 3 ${prefix} Eight 0.355 0.315 6 5`,
    `DH R 5 ${prefix} Nine 0.390 0.370 8 1`,
  ].join("\n");
}

function hitterCardsFor(prefix, firstOutcome = "OUT") {
  return [
    hitterCard(`${prefix} One`, firstOutcome),
    hitterCard(`${prefix} Two`),
    hitterCard(`${prefix} Three`),
    hitterCard(`${prefix} Four`),
    hitterCard(`${prefix} Five`),
    hitterCard(`${prefix} Six`),
    hitterCard(`${prefix} Seven`),
    hitterCard(`${prefix} Eight`),
    hitterCard(`${prefix} Nine`),
  ];
}

export function runSavedGameScenarioTests() {
  const team = {
    name: "Away Testers",
    hittersText: rosterText("Away"),
  };

  const opponent = {
    name: "Home Testers",
    lineupText: rosterText("Home"),
  };

  const cards = [
    ...hitterCardsFor("Away", "HOME_RUN"),
    ...hitterCardsFor("Home", "OUT"),
    pitcherCard("Away Starter"),
    pitcherCard("Home Starter"),
  ];

  const playableResult = simulateSavedGameScenario({
    team,
    opponent,
    cards,
    awayStarter: { name: "Away Starter" },
    homeStarter: { name: "Home Starter" },
    innings: 1,
    random: createFixedRandom([
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
      0.1, 0.5,
    ]),
  });

  const missingResult = simulateSavedGameScenario({
    team,
    opponent,
    cards: cards.filter((card) => card.name !== "Home Starter"),
    awayStarter: { name: "Away Starter" },
    homeStarter: { name: "Home Starter" },
    innings: 1,
    random: createFixedRandom([]),
  });

  const assertions = [
    assertEqual(playableResult.isPlayable, true, "scenario is playable with complete cards"),
    assertEqual(playableResult.awayLineup.length, 9, "scenario builds away lineup"),
    assertEqual(playableResult.homeLineup.length, 9, "scenario builds home lineup"),
    assertEqual(Boolean(playableResult.game), true, "scenario returns game result"),
    assertEqual(playableResult.game.finalScore.away, 0, "scenario simulates away score"),
    assertEqual(playableResult.game.finalScore.home, 0, "scenario simulates home score"),
    assertEqual(playableResult.game.halfInnings.length, 2, "scenario simulates one full inning"),
    assertEqual(playableResult.missing.awayHitters.length, 0, "scenario reports no missing away hitters"),
    assertEqual(playableResult.missing.homeHitters.length, 0, "scenario reports no missing home hitters"),
    assertEqual(playableResult.missing.awayStarter.length, 0, "scenario reports no missing away starter"),
    assertEqual(playableResult.missing.homeStarter.length, 0, "scenario reports no missing home starter"),

    assertEqual(missingResult.isPlayable, false, "scenario blocks missing starter"),
    assertEqual(missingResult.game, null, "scenario does not simulate when missing starter"),
    assertEqual(missingResult.missing.homeStarter.includes("Home Starter"), true, "scenario reports missing home starter"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
