import { buildSavedLineupForGame } from "./savedLineupGameAdapter.js";

function assertEqual(actual, expected, label) {
  return {
    label,
    passed: actual === expected,
    expected,
    actual,
  };
}

function card(name) {
  return {
    name,
    cardType: "hitter",
    cardEvents: [
      {
        side: "vsRHP",
        roll: "7",
        result: "OUT",
        outcomeType: "OUT",
        eventClass: "RESOLVED",
        defenseMeta: null,
        rawLine: "7 OUT",
        splitOutcomes: [],
        isXChance: false,
        isInjury: false,
        isBallparkSingle: false,
        isBallparkHomeRun: false,
      },
    ],
  };
}

export function runSavedLineupGameAdapterTests() {
  const hittersText = [
    "C R 2 Player One 0.350 0.340 4 3",
    "1B L 3 Player Two 0.360 0.330 7 2",
    "2B R 2 Player Three 0.345 0.355 3 5",
    "3B R 3 Player Four 0.340 0.360 6 3",
    "SS S 2 Player Five 0.330 0.335 3 6",
    "LF L 3 Player Six 0.370 0.320 5 7",
    "CF R 2 Player Seven 0.360 0.350 4 8",
    "RF L 3 Player Eight 0.355 0.315 6 5",
    "DH R 5 Player Nine 0.390 0.370 8 1",
  ].join("\n");

  const fullCards = [
    card("Player One"),
    card("Player Two"),
    card("Player Three"),
    card("Player Four"),
    card("Player Five"),
    card("Player Six"),
    card("Player Seven"),
    card("Player Eight"),
    card("Player Nine"),
  ];

  const playableResult = buildSavedLineupForGame({
    hittersText,
    pitcherHand: "R",
    cards: fullCards,
  });

  const missingCardResult = buildSavedLineupForGame({
    hittersText,
    pitcherHand: "R",
    cards: fullCards.filter((item) => item.name !== "Player Nine"),
  });

  const assertions = [
    assertEqual(playableResult.lineup.length, 9, "adapter builds nine-card lineup"),
    assertEqual(playableResult.missingCards.length, 0, "adapter reports no missing cards"),
    assertEqual(playableResult.isPlayable, true, "adapter marks full-card lineup playable"),
    assertEqual(playableResult.lineup[0].lineupSlot, 1, "adapter assigns first lineup slot"),
    assertEqual(Boolean(playableResult.lineup[0].card), true, "adapter attaches card to lineup entry"),
    assertEqual(Boolean(playableResult.lineup[0].sourcePlayer), true, "adapter preserves source player"),
    assertEqual(missingCardResult.isPlayable, false, "adapter blocks lineup with missing card"),
    assertEqual(missingCardResult.missingCards.includes("Player Nine"), true, "adapter reports missing card name"),
  ];

  const failed = assertions.filter((assertion) => !assertion.passed);

  return {
    passed: assertions.length - failed.length,
    failed: failed.length,
    total: assertions.length,
    assertions,
  };
}
