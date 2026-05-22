function getSideForHand(hand) {
  const normalized = String(hand || "").toUpperCase();

  if (
    normalized === "L" ||
    normalized === "LHP" ||
    normalized === "LEFT" ||
    normalized === "LEFTY"
  ) {
    return "vsLHP";
  }

  return "vsRHP";
}

function averageRate(a = 0, b = 0) {
  return ((a || 0) + (b || 0)) / 2;
}

export function getHitterSideForPitcherHand(pitcherHand) {
  return getSideForHand(pitcherHand);
}

export function getPitcherSideForBatterHand(batterHand) {
  return getSideForHand(batterHand);
}

export function combineCardMetrics({
  hitterProfile,
  pitcherProfile,
  hitterBats,
  pitcherThrows,
}) {
  const hitterSide = getHitterSideForPitcherHand(pitcherThrows);
  const pitcherSide = getPitcherSideForBatterHand(hitterBats);

  const hitterMetrics = hitterProfile?.[hitterSide] || {};
  const pitcherMetrics = pitcherProfile?.[pitcherSide] || {};

  return {
    hitterSide,
    pitcherSide,

    onBase: averageRate(hitterMetrics.onBase, pitcherMetrics.onBase),
    extraBase: averageRate(hitterMetrics.extraBase, pitcherMetrics.extraBase),
    homeRuns: averageRate(hitterMetrics.homeRuns, pitcherMetrics.homeRuns),
    strikeouts: averageRate(
      hitterMetrics.strikeouts,
      pitcherMetrics.strikeouts
    ),
    outs: averageRate(hitterMetrics.outs, pitcherMetrics.outs),

    hitterMetrics,
    pitcherMetrics,
  };
}

export function scoreCombinedMatchup(metrics = {}) {
  return (
    (metrics.onBase || 0) * 100 +
    (metrics.extraBase || 0) * 80 +
    (metrics.homeRuns || 0) * 120 -
    (metrics.strikeouts || 0) * 35 -
    (metrics.outs || 0) * 20
  );
}
