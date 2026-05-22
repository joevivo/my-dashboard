export function getSideMetrics(cardEventSummary, side) {
  const weighted = cardEventSummary?.bySideWeighted?.[side] || {};
  const weightedOutcome = cardEventSummary?.bySideWeightedOutcome?.[side] || {};

  const onBase = weighted.onBase || 0;
  const extraBase = weighted.extraBase || 0;
  const homeRuns = weighted.homeRuns || 0;
  const strikeouts = weighted.strikeouts || 0;
  const outs = weighted.outs || 0;

  return {
    side,
    onBase,
    extraBase,
    homeRuns,
    strikeouts,
    outs,
    singles: weightedOutcome.SINGLE || 0,
    doubles: weightedOutcome.DOUBLE || 0,
    triples: weightedOutcome.TRIPLE || 0,
    walks: weightedOutcome.WALK || 0,
    hbp: weightedOutcome.HBP || 0,
  };
}

export function getCardProbabilityProfile(cardEventSummary) {
  return {
    vsLHP: getSideMetrics(cardEventSummary, "vsLHP"),
    vsRHP: getSideMetrics(cardEventSummary, "vsRHP"),
  };
}

export function formatRate(value) {
  return `${((value || 0) * 100).toFixed(1)}%`;
}

export function getMatchupSideForPitcherHand(pitcherHand) {
  const hand = String(pitcherHand || "").toUpperCase();

  if (hand === "L" || hand === "LHP" || hand === "LEFT") {
    return "vsLHP";
  }

  return "vsRHP";
}

export function getCardScore(metrics = {}) {
  const onBase = metrics.onBase || 0;
  const extraBase = metrics.extraBase || 0;
  const homeRuns = metrics.homeRuns || 0;
  const strikeouts = metrics.strikeouts || 0;
  const outs = metrics.outs || 0;

  return (
    onBase * 100 +
    extraBase * 80 +
    homeRuns * 120 -
    strikeouts * 35 -
    outs * 20
  );
}

export function compareCardSides(cardEventSummary) {
  const profile = getCardProbabilityProfile(cardEventSummary);

  return {
    vsLHP: {
      ...profile.vsLHP,
      score: getCardScore(profile.vsLHP),
    },
    vsRHP: {
      ...profile.vsRHP,
      score: getCardScore(profile.vsRHP),
    },
  };
}
