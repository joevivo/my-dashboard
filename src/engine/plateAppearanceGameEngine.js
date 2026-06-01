import { resolvePlateAppearance } from "./cardSimEngine.js";
import { applyPlateAppearanceToGameState } from "./gameStateEngine.js";

export function resolveAndApplyPlateAppearance({
  state,
  hitterCard,
  pitcherCard,
  pitcherHand = "R",
  batterHand = "R",
  batterId,
  batterName,
  random = Math.random,
} = {}) {
  const plateAppearance = resolvePlateAppearance({
    hitterCard,
    pitcherCard,
    pitcherHand,
    batterHand,
    random,
  });

  const enrichedPlateAppearance = {
    ...plateAppearance,
    batterId,
    batterName,
  };

  const mutation = applyPlateAppearanceToGameState(
    state,
    enrichedPlateAppearance,
    {
      batterId,
      batterName,
    }
  );

  return {
    state: mutation.state,
    plateAppearance: enrichedPlateAppearance,
    summary: mutation.summary,
  };
}
