import { parseCardEvents } from "./cardEventParser";
import { resolvePlateAppearance } from "./cardSimEngine";

function buildTestCard(rawText = "") {
  const firstLine =
    rawText
      .split("\n")
      .map((line) => line.trim())
      .find(Boolean) || "Unknown Card";

  return {
    name: firstLine,
    rawText,
    cardEvents: parseCardEvents(rawText),
  };
}

export function runCardSimulationTest({
  hitterText,
  pitcherText,
  pitcherHand = "L",
  plateAppearances = 10000,
}) {
  const hitterCard = buildTestCard(hitterText);
  const pitcherCard = buildTestCard(pitcherText);

  const results = {};

  for (let index = 0; index < plateAppearances; index += 1) {
    const outcome = resolvePlateAppearance({
      hitterCard,
      pitcherCard,
      pitcherHand,
    });

    const key = outcome.result || outcome.outcomeType || "UNKNOWN";

    results[key] = (results[key] || 0) + 1;
  }

  return {
    hitter: hitterCard.name,
    pitcher: pitcherCard.name,
    plateAppearances,
    results,
  };
}
