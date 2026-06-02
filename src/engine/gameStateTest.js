import {
  applyPlateAppearanceToGameState,
  createInitialGameState,
} from "./gameStateEngine.js";

function assertEqual(actual, expected, label) {
  return {
    label,
    passed: actual === expected,
    expected,
    actual,
  };
}

function runner(id) {
  return {
    id,
    name: id,
  };
}

export function runDeterministicGameStateTests() {
  const initial = createInitialGameState();

  const outResult = applyPlateAppearanceToGameState(initial, {
    outcomeType: "OUT",
  });

  const inningAdvanceResult = applyPlateAppearanceToGameState(
    createInitialGameState({ outs: 2 }),
    {
      outcomeType: "STRIKEOUT",
    }
  );

  const walkResult = applyPlateAppearanceToGameState(initial, {
    outcomeType: "WALK",
    batterId: "B1",
  });

  const loadedWalkResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      runners: {
        first: runner("R1"),
        second: runner("R2"),
        third: runner("R3"),
      },
    }),
    {
      outcomeType: "WALK",
      batterId: "B2",
    }
  );

  const singleResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      runners: {
        third: runner("R3"),
      },
    }),
    {
      outcomeType: "SINGLE",
      batterId: "B3",
    }
  );

  const doubleResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      runners: {
        first: runner("R1"),
        second: runner("R2"),
        third: runner("R3"),
      },
    }),
    {
      outcomeType: "DOUBLE",
      batterId: "B4",
    }
  );

  const homeRunResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      runners: {
        first: runner("R1"),
        second: runner("R2"),
        third: runner("R3"),
      },
    }),
    {
      outcomeType: "HOME_RUN",
      batterId: "B5",
    }
  );

  const gbxResult = applyPlateAppearanceToGameState(initial, {
    outcomeType: "GBX",
  });

  const fbxResult = applyPlateAppearanceToGameState(initial, {
    outcomeType: "FBX",
  });

  const xChanceResult = applyPlateAppearanceToGameState(initial, {
    outcomeType: "X_CHANCE",
  });

  const groundballAResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      runners: {
        first: runner("R1"),
      },
    }),
    {
      outcomeType: "GROUNDBALL",
      defenseMeta: {
        defenseType: "GB",
        position: "SS",
        resultClass: "A",
      },
      batterId: "B6",
    }
  );

  const groundballATwoOutResult = applyPlateAppearanceToGameState(
    createInitialGameState({
      outs: 2,
      runners: {
        first: runner("R1"),
      },
    }),
    {
      outcomeType: "GROUNDBALL",
      defenseMeta: {
        defenseType: "GB",
        position: "SS",
        resultClass: "A",
      },
      batterId: "B7",
    }
  );

  const assertions = [
    assertEqual(initial.inning, 1, "initial inning is 1"),
    assertEqual(initial.half, "top", "initial half is top"),
    assertEqual(initial.outs, 0, "initial outs are 0"),
    assertEqual(initial.score.away, 0, "initial away score is 0"),
    assertEqual(initial.score.home, 0, "initial home score is 0"),

    assertEqual(outResult.state.outs, 1, "out records one out"),
    assertEqual(outResult.summary.outsRecorded, 1, "out summary records one out"),

    assertEqual(gbxResult.state.outs, 1, "GBX records one out before defensive resolution exists"),
    assertEqual(gbxResult.summary.outsRecorded, 1, "GBX summary records one out"),
    assertEqual(fbxResult.state.outs, 1, "FBX records one out before defensive resolution exists"),
    assertEqual(fbxResult.summary.outsRecorded, 1, "FBX summary records one out"),
    assertEqual(xChanceResult.state.outs, 1, "X_CHANCE records one out before defensive resolution exists"),
    assertEqual(xChanceResult.summary.outsRecorded, 1, "X_CHANCE summary records one out"),

    assertEqual(groundballAResult.state.outs, 2, "GB(A) with runner on first records two outs"),
    assertEqual(groundballAResult.summary.outsRecorded, 2, "GB(A) summary records two outs"),
    assertEqual(groundballAResult.state.runners.first, null, "GB(A) clears runner from first"),
    assertEqual(groundballAResult.state.score.away, 0, "GB(A) scores no run in first-base-only case"),
    assertEqual(groundballATwoOutResult.state.outs, 0, "GB(A) with two outs ends half inning"),
    assertEqual(groundballATwoOutResult.summary.outsRecorded, 1, "GB(A) with two outs records only the third out"),

    assertEqual(inningAdvanceResult.state.outs, 0, "third out resets outs"),
    assertEqual(inningAdvanceResult.state.half, "bottom", "third out advances to bottom half"),
    assertEqual(inningAdvanceResult.state.inning, 1, "top-half third out keeps inning number"),

    assertEqual(walkResult.state.runners.first?.id, "B1", "walk places batter on first"),
    assertEqual(walkResult.summary.runsScored, 0, "empty-base walk scores no runs"),

    assertEqual(loadedWalkResult.state.score.away, 1, "loaded walk scores one run"),
    assertEqual(loadedWalkResult.state.runners.first?.id, "B2", "loaded walk puts batter on first"),
    assertEqual(loadedWalkResult.state.runners.second?.id, "R1", "loaded walk forces runner to second"),
    assertEqual(loadedWalkResult.state.runners.third?.id, "R2", "loaded walk forces runner to third"),

    assertEqual(singleResult.state.score.away, 1, "single scores runner from third"),
    assertEqual(singleResult.state.runners.first?.id, "B3", "single puts batter on first"),

    assertEqual(doubleResult.state.score.away, 2, "double scores runners from second and third"),
    assertEqual(doubleResult.state.runners.second?.id, "B4", "double puts batter on second"),
    assertEqual(doubleResult.state.runners.third?.id, "R1", "double moves runner from first to third"),

    assertEqual(homeRunResult.state.score.away, 4, "grand slam scores four runs"),
    assertEqual(homeRunResult.state.runners.first, null, "home run clears first"),
    assertEqual(homeRunResult.state.runners.second, null, "home run clears second"),
    assertEqual(homeRunResult.state.runners.third, null, "home run clears third"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
