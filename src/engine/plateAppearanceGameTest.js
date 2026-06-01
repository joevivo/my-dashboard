import { createInitialGameState } from "./gameStateEngine.js";
import { resolveAndApplyPlateAppearance } from "./plateAppearanceGameEngine.js";

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

function runner(id) {
  return {
    id,
    name: id,
  };
}

function cardWithEvent({ name, side, roll = "7", result, outcomeType }) {
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

export function runDeterministicPlateAppearanceGameTests() {
  const hitterHomeRunCard = cardWithEvent({
    name: "Hitter HR Card",
    side: "vsRHP",
    result: "HOME_RUN",
    outcomeType: "HOME_RUN",
  });

  const hitterOutCard = cardWithEvent({
    name: "Hitter OUT Card",
    side: "vsRHP",
    result: "OUT",
    outcomeType: "OUT",
  });

  const pitcherSingleVsLeftCard = cardWithEvent({
    name: "Pitcher Single vs LHB Card",
    side: "vsLHP",
    result: "SINGLE",
    outcomeType: "SINGLE",
  });

  const pitcherOutVsRightCard = cardWithEvent({
    name: "Pitcher OUT vs RHB Card",
    side: "vsRHP",
    result: "OUT",
    outcomeType: "OUT",
  });

  const grandSlamResult = resolveAndApplyPlateAppearance({
    state: createInitialGameState({
      runners: {
        first: runner("R1"),
        second: runner("R2"),
        third: runner("R3"),
      },
    }),
    hitterCard: hitterHomeRunCard,
    pitcherCard: pitcherOutVsRightCard,
    pitcherHand: "R",
    batterHand: "R",
    batterId: "B-HR",
    random: createFixedRandom([
      0.1, // hitter card
      0.5, // weighted roll 7
    ]),
  });

  const pitcherSingleResult = resolveAndApplyPlateAppearance({
    state: createInitialGameState({
      runners: {
        third: runner("R3"),
      },
    }),
    hitterCard: hitterOutCard,
    pitcherCard: pitcherSingleVsLeftCard,
    pitcherHand: "R",
    batterHand: "L",
    batterId: "B-SI",
    random: createFixedRandom([
      0.9, // pitcher card
      0.5, // weighted roll 7
    ]),
  });

  const inningAdvanceResult = resolveAndApplyPlateAppearance({
    state: createInitialGameState({
      outs: 2,
    }),
    hitterCard: hitterOutCard,
    pitcherCard: pitcherOutVsRightCard,
    pitcherHand: "R",
    batterHand: "R",
    batterId: "B-OUT",
    random: createFixedRandom([
      0.1, // hitter card
      0.5, // weighted roll 7
    ]),
  });

  const assertions = [
    assertEqual(grandSlamResult.plateAppearance.cardSide, "hitter", "bridge uses hitter card when roll selects hitter"),
    assertEqual(grandSlamResult.plateAppearance.outcomeType, "HOME_RUN", "bridge resolves hitter home run"),
    assertEqual(grandSlamResult.state.score.away, 4, "bridge applies grand slam to game state"),
    assertEqual(grandSlamResult.state.runners.first, null, "bridge clears first after home run"),
    assertEqual(grandSlamResult.state.runners.second, null, "bridge clears second after home run"),
    assertEqual(grandSlamResult.state.runners.third, null, "bridge clears third after home run"),
    assertEqual(grandSlamResult.summary.runsScored, 4, "bridge summary records four runs"),

    assertEqual(pitcherSingleResult.plateAppearance.cardSide, "pitcher", "bridge uses pitcher card when roll selects pitcher"),
    assertEqual(pitcherSingleResult.plateAppearance.side, "vsLHP", "bridge uses batter hand for pitcher card side"),
    assertEqual(pitcherSingleResult.plateAppearance.outcomeType, "SINGLE", "bridge resolves pitcher-card single"),
    assertEqual(pitcherSingleResult.state.score.away, 1, "bridge applies single scoring runner from third"),
    assertEqual(pitcherSingleResult.state.runners.first?.id, "B-SI", "bridge places batter on first after single"),

    assertEqual(inningAdvanceResult.plateAppearance.outcomeType, "OUT", "bridge resolves out"),
    assertEqual(inningAdvanceResult.state.outs, 0, "bridge advances half inning after third out"),
    assertEqual(inningAdvanceResult.state.half, "bottom", "bridge moves from top to bottom after third out"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
