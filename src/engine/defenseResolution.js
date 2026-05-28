export function resolveDefenseEvent(event = {}) {
  const meta = event.defenseMeta;

  if (!meta) {
    return {
      resolutionType: "NOT_DEFENSE_EVENT",
      handled: false,
      reason: "No defense metadata present.",
    };
  }

  const defenseType = meta.defenseType;
  const resultClass = meta.resultClass;
  const modifiers = meta.modifiers || "";

  if (defenseType === "GB") {
    return {
      resolutionType: "GROUND_BALL_BASE",
      handled: true,
      position: meta.position,
      resultClass,
      modifiers,
      doublePlayEligible: ["A", "B"].includes(resultClass),
      advancementModel: "PENDING_RUNNER_STATE",
    };
  }

  if (defenseType === "FB") {
    return {
      resolutionType: "FLY_BALL_BASE",
      handled: true,
      position: meta.position,
      resultClass,
      modifiers,
      sacrificeFlyEligible: ["B", "C"].includes(resultClass),
      advancementModel: "PENDING_RUNNER_STATE",
    };
  }

  return {
    resolutionType: "UNKNOWN_DEFENSE_EVENT",
    handled: false,
    position: meta.position || null,
    resultClass: resultClass || null,
    modifiers,
  };
}
