import { parserRegressionCases } from "../tests/parserRegressionCases";
import { parseCardEvents } from "../cardEventParser";
import { resolveDefenseEvent } from "../defenseResolution";

function compareExpected(actual, expected) {
  const mismatches = [];

  for (const [key, expectedValue] of Object.entries(expected)) {
    const actualValue = actual?.[key];

    if (actualValue !== expectedValue) {
      mismatches.push({
        field: key,
        expected: expectedValue,
        actual: actualValue,
      });
    }
  }

  return mismatches;
}

export function runParserRegressionSuite() {
  const results = parserRegressionCases.map((testCase) => {
    const parsed = parseCardEvents(`2 - ${testCase.rawResult}`)[0];

    const defenseResolution = resolveDefenseEvent(parsed);

    const combined = {
      ...parsed,
      ...defenseResolution,
    };

    const mismatches = compareExpected(
      combined,
      testCase.expected
    );

    return {
      id: testCase.id,
      description: testCase.description,
      passed: mismatches.length === 0,
      mismatches,
      parsed,
      defenseResolution,
    };
  });

  return {
    total: results.length,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    results,
  };
}