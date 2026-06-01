import { parseCardEvents } from "./cardEventParser";
import { resolvePlateAppearance } from "./cardSimEngine";

function buildTestCard(rawText = "") {
  const firstLine =
    rawText
      .split("\n")
      .map((line) => line.trim())
      .find(Boolean) || "Unknown Card";

  return {
    name: firstLine,
    rawText,
    cardEvents: parseCardEvents(rawText),
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

function assertEqual(actual, expected, label) {
  const passed = actual === expected;

  return {
    label,
    passed,
    expected,
    actual,
  };
}

export function runDeterministicCardSimulationTests() {
  const hitterCard = {
    name: "Deterministic Hitter",
    cardEvents: [
      {
        side: "vsRHP",
        roll: "7",
        result: "gb(ss)-x",
        outcomeType: "GBX",
        eventClass: "DEFENSE",
        defenseMeta: {
          type: "GB",
          position: "SS",
          modifier: "X",
        },
        rawLine: "7 gb(ss)-x",
        splitOutcomes: [],
        isXChance: true,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };

  const pitcherCard = {
    name: "Deterministic Pitcher",
    cardEvents: [
      {
        side: "vsRHP",
        roll: "7",
        result: "SINGLE",
        outcomeType: "SINGLE",
        eventClass: "ON_BASE",
        defenseMeta: null,
        rawLine: "7 SINGLE 1-10 / OUT 11-20",
        splitOutcomes: [
          {
            rangeStart: 1,
            rangeEnd: 10,
            result: "SINGLE",
            outcomeType: "SINGLE",
          },
          {
            rangeStart: 11,
            rangeEnd: 20,
            result: "OUT",
            outcomeType: "OUT",
          },
        ],
        isXChance: false,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };

  const defenseOutcome = resolvePlateAppearance({
    hitterCard,
    pitcherCard,
    pitcherHand: "R",
    random: createFixedRandom([
      0.1, // hitter card
      0.5, // weighted roll 7
    ]),
  });

  const splitOutcome = resolvePlateAppearance({
    hitterCard,
    pitcherCard,
    pitcherHand: "R",
    random: createFixedRandom([
      0.9, // pitcher card
      0.5, // weighted roll 7
      0.2, // d20 = 5
    ]),
  });

  const assertions = [
    assertEqual(defenseOutcome.cardSide, "hitter", "selects hitter card"),
    assertEqual(defenseOutcome.roll, "7", "uses deterministic weighted roll"),
    assertEqual(defenseOutcome.outcomeType, "GBX", "preserves defense outcome type"),
    assertEqual(defenseOutcome.eventClass, "DEFENSE", "preserves event class"),
    assertEqual(defenseOutcome.isXChance, true, "preserves X-chance flag"),
    assertEqual(defenseOutcome.defenseMeta?.position, "SS", "preserves defense position"),

    assertEqual(splitOutcome.cardSide, "pitcher", "selects pitcher card"),
    assertEqual(splitOutcome.roll, "7", "uses deterministic weighted roll for split"),
    assertEqual(splitOutcome.d20, 5, "uses deterministic d20 split roll"),
    assertEqual(splitOutcome.result, "SINGLE", "resolves split result"),
    assertEqual(splitOutcome.outcomeType, "SINGLE", "resolves split outcome type"),
    assertEqual(splitOutcome.eventClass, "ON_BASE", "preserves split event class"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}

export function runCardSimulationTest({
  hitterText,
  pitcherText,
  pitcherHand = "L",
  plateAppearances = 10000,
}) {
  const hitterCard = buildTestCard(hitterText);
  const pitcherCard = buildTestCard(pitcherText);

  const results = {};

  for (let index = 0; index < plateAppearances; index += 1) {
    const outcome = resolvePlateAppearance({
      hitterCard,
      pitcherCard,
      pitcherHand,
    });

    const key = outcome.result || outcome.outcomeType || "UNKNOWN";

    results[key] = (results[key] || 0) + 1;
  }

  return {
    hitter: hitterCard.name,
    pitcher: pitcherCard.name,
    plateAppearances,
    results,
  };
}