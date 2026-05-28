export const parserRegressionCases = [
  {
    id: "gb-ss-a-plus",
    description: "Ground ball to shortstop with A+ result class",
    rawResult: "gb(ss)A+",
    expected: {
      eventClass: "DEFENSE_CHECK",
      defenseType: "GB",
      position: "SS",
      resultClass: "A",
      modifiers: "+",
      resolutionType: "GROUND_BALL_BASE",
      handled: true,
      doublePlayEligible: true,
    },
  },
  {
    id: "fb-cf-b",
    description: "Fly ball to center field with B result class",
    rawResult: "fb(cf)B",
    expected: {
      eventClass: "DEFENSE_CHECK",
      defenseType: "FB",
      position: "CF",
      resultClass: "B",
      modifiers: "",
      resolutionType: "FLY_BALL_BASE",
      handled: true,
      sacrificeFlyEligible: true,
    },
  },
  {
    id: "single-resolved",
    description: "Resolved single should not be treated as defense event",
    rawResult: "1B",
    expected: {
      eventClass: "RESOLVED",
      resolutionType: "NOT_DEFENSE_EVENT",
      handled: false,
    },
  },
];