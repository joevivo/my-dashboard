export function createEmptyBases() {
  return {
    first: null,
    second: null,
    third: null,
  };
}

export function createInitialGameState(overrides = {}) {
  return {
    inning: 1,
    half: "top",
    outs: 0,
    score: {
      away: 0,
      home: 0,
    },
    runners: createEmptyBases(),
    isComplete: false,
    ...overrides,
    score: {
      away: overrides.score?.away ?? 0,
      home: overrides.score?.home ?? 0,
    },
    runners: {
      ...createEmptyBases(),
      ...(overrides.runners || {}),
    },
  };
}

function cloneRunner(runner) {
  return runner ? { ...runner } : null;
}

function cloneState(state) {
  return {
    ...state,
    score: { ...state.score },
    runners: {
      first: cloneRunner(state.runners?.first),
      second: cloneRunner(state.runners?.second),
      third: cloneRunner(state.runners?.third),
    },
  };
}

function getBattingTeamKey(state) {
  return state.half === "bottom" ? "home" : "away";
}

function createBatterRunner(plateAppearance = {}, options = {}) {
  return {
    id:
      options.batterId ||
      plateAppearance.batterId ||
      plateAppearance.batterName ||
      "BATTER",
    name:
      options.batterName ||
      plateAppearance.batterName ||
      plateAppearance.batterId ||
      "Batter",
  };
}

function scoreRunner(nextState, teamKey, runner, summary) {
  nextState.score[teamKey] += 1;
  summary.runsScored += 1;

  summary.advancements.push({
    runner,
    from: "third",
    to: "home",
    scored: true,
  });
}

function advanceHalfInningIfNeeded(nextState) {
  if (nextState.outs < 3) return nextState;

  const advanced = {
    ...nextState,
    outs: 0,
    runners: createEmptyBases(),
  };

  if (nextState.half === "top") {
    advanced.half = "bottom";
    return advanced;
  }

  advanced.half = "top";
  advanced.inning += 1;
  return advanced;
}

function applyOut(nextState, summary, outsRecorded = 1) {
  nextState.outs += outsRecorded;
  summary.outsRecorded += outsRecorded;
  return advanceHalfInningIfNeeded(nextState);
}

function applyWalk(nextState, batterRunner, summary) {
  const { first, second, third } = nextState.runners;
  const teamKey = getBattingTeamKey(nextState);

  if (first && second && third) {
    scoreRunner(nextState, teamKey, third, summary);
    nextState.runners.third = second;
    nextState.runners.second = first;
    nextState.runners.first = batterRunner;
    return nextState;
  }

  if (first && second) {
    nextState.runners.third = second;
    nextState.runners.second = first;
    nextState.runners.first = batterRunner;
    return nextState;
  }

  if (first) {
    nextState.runners.second = first;
    nextState.runners.first = batterRunner;
    return nextState;
  }

  nextState.runners.first = batterRunner;
  return nextState;
}

function applySingle(nextState, batterRunner, summary) {
  const { first, second, third } = nextState.runners;
  const teamKey = getBattingTeamKey(nextState);

  if (third) scoreRunner(nextState, teamKey, third, summary);

  nextState.runners.third = second;
  nextState.runners.second = first;
  nextState.runners.first = batterRunner;

  return nextState;
}

function applyDouble(nextState, batterRunner, summary) {
  const { first, second, third } = nextState.runners;
  const teamKey = getBattingTeamKey(nextState);

  if (third) scoreRunner(nextState, teamKey, third, summary);
  if (second) scoreRunner(nextState, teamKey, second, summary);

  nextState.runners.third = first;
  nextState.runners.second = batterRunner;
  nextState.runners.first = null;

  return nextState;
}

function applyTriple(nextState, batterRunner, summary) {
  const { first, second, third } = nextState.runners;
  const teamKey = getBattingTeamKey(nextState);

  if (third) scoreRunner(nextState, teamKey, third, summary);
  if (second) scoreRunner(nextState, teamKey, second, summary);
  if (first) scoreRunner(nextState, teamKey, first, summary);

  nextState.runners.third = batterRunner;
  nextState.runners.second = null;
  nextState.runners.first = null;

  return nextState;
}

function applyHomeRun(nextState, batterRunner, summary) {
  const { first, second, third } = nextState.runners;
  const teamKey = getBattingTeamKey(nextState);

  if (third) scoreRunner(nextState, teamKey, third, summary);
  if (second) scoreRunner(nextState, teamKey, second, summary);
  if (first) scoreRunner(nextState, teamKey, first, summary);

  nextState.score[teamKey] += 1;
  summary.runsScored += 1;
  summary.advancements.push({
    runner: batterRunner,
    from: "batter",
    to: "home",
    scored: true,
  });

  nextState.runners = createEmptyBases();
  return nextState;
}

export function applyPlateAppearanceToGameState(
  state,
  plateAppearance = {},
  options = {}
) {
  const nextState = cloneState(state);
  const outcomeType = plateAppearance.outcomeType || plateAppearance.result || "UNKNOWN";
  const batterRunner = createBatterRunner(plateAppearance, options);

  const summary = {
    outcomeType,
    runsScored: 0,
    outsRecorded: 0,
    advancements: [],
    notes: [],
  };

  if (["OUT", "STRIKEOUT", "LINEOUT", "POPOUT", "FOULOUT", "GROUNDBALL", "FLYBALL", "GBX", "FBX", "X_CHANCE"].includes(outcomeType)) {
    return {
      state: applyOut(nextState, summary, 1),
      summary,
    };
  }

  if (["WALK", "HBP"].includes(outcomeType)) {
    return {
      state: applyWalk(nextState, batterRunner, summary),
      summary,
    };
  }

  if (outcomeType === "SINGLE") {
    return {
      state: applySingle(nextState, batterRunner, summary),
      summary,
    };
  }

  if (outcomeType === "DOUBLE") {
    return {
      state: applyDouble(nextState, batterRunner, summary),
      summary,
    };
  }

  if (outcomeType === "TRIPLE") {
    return {
      state: applyTriple(nextState, batterRunner, summary),
      summary,
    };
  }

  if (outcomeType === "HOME_RUN") {
    return {
      state: applyHomeRun(nextState, batterRunner, summary),
      summary,
    };
  }

  summary.notes.push(`Unhandled outcome type: ${outcomeType}`);

  return {
    state: nextState,
    summary,
  };
}
