import preview479336 from "./frozenSeriesPreview.479336.1851052.json";
import preview479431 from "./frozenSeriesPreview.479431.1853975.json";
import preview479610 from "./frozenSeriesPreview.479610.1854215.json";

export const FROZEN_STRAT_REVIEW_ENABLED = true;

export const FROZEN_STRAT_REVIEW_ID =
  "pre-10pm-20260816-201815";

const previews = new Map([
  ["479336:1851052", preview479336],
  ["479431:1853975", preview479431],
  ["479610:1854215", preview479610],
]);

export function getFrozenSeriesPreview(
  leagueId,
  teamId
) {
  if (!FROZEN_STRAT_REVIEW_ENABLED) {
    return null;
  }

  const key =
    `${String(leagueId || "")}:${String(teamId || "")}`;

  return previews.get(key) || null;
}