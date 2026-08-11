function round(value, digits = 3) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function rankedCounts(values) {
  const counts = new Map();

  for (const value of values) {
    counts.set(
      value,
      (counts.get(value) || 0) + 1
    );
  }

  return [...counts.entries()].sort(
    (a, b) =>
      b[1] - a[1] ||
      a[0].localeCompare(b[0])
  );
}

export function buildHandLineupProfile(samples) {
  if (!Array.isArray(samples)) {
    throw new Error("samples must be an array");
  }

  const valid = samples.filter(
    (sample) =>
      Array.isArray(sample.positionOrder) &&
      sample.positionOrder.length === 8
  );

  const sampleCount = valid.length;

  if (!sampleCount) {
    return {
      sampleCount: 0,
      status: "INSUFFICIENT",
      predictability: "INSUFFICIENT",
      predictabilityScore: null,
      distinctLineups: 0,
      topLineup: null,
      topLineupCount: 0,
      topLineupRate: null,
      averageSlotStability: null,
      slots: [],
    };
  }

  const signatures = valid.map(
    (sample) =>
      sample.positionOrder.join(">")
  );

  const rankedLineups =
    rankedCounts(signatures);

  const [
    topSignature,
    topLineupCount,
  ] = rankedLineups[0];

  const slots = [];

  for (let slot = 0; slot < 8; slot += 1) {
    const ranked = rankedCounts(
      valid.map(
        (sample) =>
          sample.positionOrder[slot]
      )
    );

    const [player, count] =
      ranked[0];

    slots.push({
      slot: slot + 1,
      player,
      count,
      rate: round(
        count / sampleCount
      ),
    });
  }

  const topLineupRate =
    topLineupCount / sampleCount;

  const averageSlotStability =
    slots.reduce(
      (sum, slot) =>
        sum + slot.rate,
      0
    ) / slots.length;

  /*
   * Slot stability carries more weight than
   * exact full-lineup repetition.
   */
  const predictabilityScore =
    0.65 * averageSlotStability +
    0.35 * topLineupRate;

  let predictability = "VARIABLE";

  if (sampleCount < 3) {
    predictability = "INSUFFICIENT";
  } else if (
    sampleCount >= 5 &&
    predictabilityScore >= 0.82
  ) {
    predictability = "STRICT";
  } else if (
    sampleCount >= 4 &&
    predictabilityScore >= 0.68
  ) {
    predictability = "STRUCTURED";
  }

  return {
    sampleCount,
    status:
      sampleCount >= 3
        ? "READY"
        : "INSUFFICIENT",
    predictability,
    predictabilityScore:
      round(predictabilityScore),
    distinctLineups:
      rankedLineups.length,
    topLineup:
      topSignature.split(">"),
    topLineupCount,
    topLineupRate:
      round(topLineupRate),
    averageSlotStability:
      round(averageSlotStability),
    slots,
  };
}

function usageRates(samples) {
  const rates = new Map();

  if (!samples.length) {
    return rates;
  }

  const players = new Set();

  for (const sample of samples) {
    for (
      const player
      of sample.positionOrder || []
    ) {
      players.add(player);
    }
  }

  for (const player of players) {
    const count =
      samples.filter(
        (sample) =>
          sample.positionOrder.includes(
            player
          )
      ).length;

    rates.set(
      player,
      count / samples.length
    );
  }

  return rates;
}

export function buildHandSensitivity(
  leftSamples,
  rightSamples
) {
  if (
    leftSamples.length < 3 ||
    rightSamples.length < 3
  ) {
    return {
      status: "INSUFFICIENT",
      sensitivity: "INSUFFICIENT",
      personnelDeltas: [],
      majorPersonnelSwaps: [],
      modalSlotDifferences: null,
    };
  }

  const leftRates =
    usageRates(leftSamples);

  const rightRates =
    usageRates(rightSamples);

  const players = new Set([
    ...leftRates.keys(),
    ...rightRates.keys(),
  ]);

  const personnelDeltas = [];

  for (const player of players) {
    const leftRate =
      leftRates.get(player) || 0;

    const rightRate =
      rightRates.get(player) || 0;

    const delta =
      leftRate - rightRate;

    if (Math.abs(delta) >= 0.25) {
      personnelDeltas.push({
        player,
        leftRate: round(leftRate),
        rightRate: round(rightRate),
        delta: round(delta),
      });
    }
  }

  personnelDeltas.sort(
    (a, b) =>
      Math.abs(b.delta) -
        Math.abs(a.delta) ||
      a.player.localeCompare(b.player)
  );

  const left =
    buildHandLineupProfile(leftSamples);

  const right =
    buildHandLineupProfile(rightSamples);

  let modalSlotDifferences = 0;

  for (let slot = 0; slot < 8; slot += 1) {
    if (
      left.slots[slot]?.player !==
      right.slots[slot]?.player
    ) {
      modalSlotDifferences += 1;
    }
  }

  const majorPersonnelSwaps =
    personnelDeltas.filter(
      (item) =>
        Math.abs(item.delta) >= 0.5
    );

  let sensitivity = "LOW";

  if (
    majorPersonnelSwaps.length >= 1 ||
    modalSlotDifferences >= 4
  ) {
    sensitivity = "HIGH";
  } else if (
    personnelDeltas.length >= 1 ||
    modalSlotDifferences >= 2
  ) {
    sensitivity = "MEDIUM";
  }

  return {
    status: "READY",
    sensitivity,
    personnelDeltas,
    majorPersonnelSwaps,
    modalSlotDifferences,
  };
}

export function classifyPredictiveLeverage(
  predictability,
  projectedStarterConfidence
) {
  const predictabilityRank = {
    INSUFFICIENT: 0,
    VARIABLE: 1,
    STRUCTURED: 2,
    STRICT: 3,
  };

  const confidenceRank = {
    NONE: 0,
    LOW: 1,
    MEDIUM: 2,
    HIGH: 3,
  };

  const profileRank =
    predictabilityRank[
      predictability
    ] || 0;

  const starterRank =
    confidenceRank[
      projectedStarterConfidence
    ] || 0;

  const limitingRank =
    Math.min(
      profileRank,
      starterRank
    );

  if (limitingRank >= 3) {
    return "HIGH";
  }

  if (limitingRank >= 2) {
    return "MEDIUM";
  }

  if (limitingRank >= 1) {
    return "LOW";
  }

  return "NONE";
}

export function buildManagerLineupFingerprint(
  samples
) {
  if (!Array.isArray(samples)) {
    throw new Error("samples must be an array");
  }

  const left = samples.filter(
    (sample) =>
      sample.opposingHand === "L"
  );

  const right = samples.filter(
    (sample) =>
      sample.opposingHand === "R"
  );

  return {
    schema:
      "bie.strat365.manager-lineup-fingerprint.v0",
    vsLHP:
      buildHandLineupProfile(left),
    vsRHP:
      buildHandLineupProfile(right),
    handSensitivity:
      buildHandSensitivity(
        left,
        right
      ),
  };
}