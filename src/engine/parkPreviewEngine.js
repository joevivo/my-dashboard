export function describeParkPressure(singleValue, homeRunValue, batterHand) {
  const si = Number(singleValue);
  const hr = Number(homeRunValue);

  if (!Number.isFinite(si) || !Number.isFinite(hr)) {
    return "Park pressure unavailable; base matchup score is unchanged.";
  }

  const handLabel =
    batterHand === "L" ? "LH hitter" : batterHand === "R" ? "RH hitter" : "Batter";

  const singleRead =
    si >= 15
      ? "strongly boosts singles"
      : si >= 11
        ? "leans singles-friendly"
        : si <= 4
          ? "heavily suppresses singles"
          : si <= 7
            ? "leans against singles"
            : "is near neutral for singles";

  const homeRunRead =
    hr >= 15
      ? "strongly boosts HR chances"
      : hr >= 11
        ? "leans HR-friendly"
        : hr <= 4
          ? "heavily suppresses HR chances"
          : hr <= 7
            ? "leans against HRs"
            : "is near neutral for HRs";

  return `${handLabel} park pressure: SI ${si} ${singleRead}; HR ${hr} ${homeRunRead}. Base matchup score is unchanged.`;
}

export function describeParkFitRead(matchupData, singleValue, homeRunValue) {
  const si = Number(singleValue);
  const hr = Number(homeRunValue);
  const combinedHr = Number(matchupData?.homeRuns || 0) * 100;
  const combinedXbh = Number(matchupData?.extraBase || 0) * 100;
  const combinedOb = Number(matchupData?.onBase || 0) * 100;

  if (!Number.isFinite(si) || !Number.isFinite(hr)) {
    return "Park fit unavailable; base matchup score is unchanged.";
  }

  const hrShape =
    combinedHr >= 5
      ? "strong HR shape"
      : combinedHr >= 3
        ? "meaningful HR shape"
        : combinedHr >= 1.5
          ? "some HR shape"
          : "limited HR shape";

  const xbhShape =
    combinedXbh >= 10
      ? "strong extra-base shape"
      : combinedXbh >= 6
        ? "playable extra-base shape"
        : "limited extra-base shape";

  const obShape =
    combinedOb >= 28
      ? "strong on-base shape"
      : combinedOb >= 20
        ? "playable on-base shape"
        : "limited on-base shape";

  const singleFit =
    si >= 15
      ? "strongly supports singles/on-base pressure"
      : si >= 11
        ? "supports singles/on-base pressure"
        : si <= 4
          ? "works sharply against singles/on-base pressure"
          : si <= 7
            ? "leans against singles/on-base pressure"
            : "is near neutral for singles/on-base pressure";

  const hrFit =
    hr >= 15
      ? "amplifies HR risk/opportunity"
      : hr >= 11
        ? "leans toward HR support"
        : hr <= 4
          ? "works sharply against HR outcomes"
          : hr <= 7
            ? "leans against HR outcomes"
            : "is near neutral for HR outcomes";

  return `Park fit: ${obShape}, ${xbhShape}, and ${hrShape} against this pitcher card. The applicable park SI ${si} ${singleFit}; applicable park HR ${hr} ${hrFit}. Base matchup score is unchanged.`;
}

export function describeParkAdjustedPreview(matchupData, baseScore, singleValue, homeRunValue) {
  const si = Number(singleValue);
  const hr = Number(homeRunValue);
  const base = Number(baseScore);

  if (!Number.isFinite(si) || !Number.isFinite(hr) || !Number.isFinite(base)) {
    return "Park-adjusted preview unavailable. Base matchup score is unchanged.";
  }

  const combinedOb = Number(matchupData?.onBase || 0) * 100;
  const combinedHr = Number(matchupData?.homeRuns || 0) * 100;

  const singleAdjustment = ((si - 10) / 9) * Math.min(combinedOb, 35) * 0.08;
  const homeRunAdjustment = ((hr - 10) / 9) * Math.min(combinedHr, 8) * 0.9;

  const adjustedScore = Math.max(0, Math.min(50, base + singleAdjustment + homeRunAdjustment));
  const effectiveDelta = adjustedScore - base;
  const deltaText = effectiveDelta >= 0 ? `+${effectiveDelta.toFixed(1)}` : effectiveDelta.toFixed(1);

  const direction =
    Math.abs(effectiveDelta) < 0.5
      ? "Park effect is essentially neutral for this matchup shape."
      : effectiveDelta > 0
        ? "Park effect leans toward the hitter profile."
        : "Park effect leans against the hitter profile.";

  return `Experimental park preview: ${adjustedScore.toFixed(1)} (${deltaText} from base ${base.toFixed(1)}). ${direction} SI component ${singleAdjustment.toFixed(1)}, HR component ${homeRunAdjustment.toFixed(1)}. Base Matchup Score is unchanged.`;
}

export function getParkPreviewSummary({
  matchup,
  baseScore,
  applicableParkSingle,
  applicableParkHomeRun,
  batterHand,
}) {
  if (!matchup || baseScore === null || baseScore === undefined) {
    return {
      parkPressure: "",
      parkFitRead: "",
      parkAdjustedPreview: "",
    };
  }

  return {
    parkPressure: describeParkPressure(
      applicableParkSingle,
      applicableParkHomeRun,
      batterHand
    ),
    parkFitRead: describeParkFitRead(
      matchup,
      applicableParkSingle,
      applicableParkHomeRun
    ),
    parkAdjustedPreview: describeParkAdjustedPreview(
      matchup,
      baseScore,
      applicableParkSingle,
      applicableParkHomeRun
    ),
  };
}
