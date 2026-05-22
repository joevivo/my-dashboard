function normalizeSide(line = "") {
  const text = line.toLowerCase();

  if (
    text.includes("vs rhp") ||
    text.includes("vs right") ||
    text.includes("right-handed pitcher") ||
    text.includes("right handed pitcher")
  ) {
    return "vsRHP";
  }

  if (
    text.includes("vs lhp") ||
    text.includes("vs left") ||
    text.includes("left-handed pitcher") ||
    text.includes("left handed pitcher")
  ) {
    return "vsLHP";
  }

  return null;
}

function detectOutcomeType(result = "") {
  const text = result.toLowerCase();

  if (/\bgbx\b/.test(text) || /\bgb\(.*\)x\b/.test(text)) return "GBX";
  if (/\bfbx\b/.test(text) || /\bfb\(.*\)x\b/.test(text)) return "FBX";
  if (/\bx\b/.test(text)) return "X_CHANCE";

  if (/\bhr\b/.test(text) || /\bhomerun\b/.test(text)) return "HOME_RUN";
  if (/\bsi\b/.test(text) || /\bsingle\b/.test(text)) return "SINGLE";
  if (/\bdo\b/.test(text) || /\bdouble\b/.test(text)) return "DOUBLE";
  if (/\btr\b/.test(text) || /\btriple\b/.test(text)) return "TRIPLE";

  if (/\bwalk\b/.test(text)) return "WALK";
  if (/\bhbp\b/.test(text)) return "HBP";
  if (/\bstrikeout\b/.test(text) || /\bk\b/.test(text)) return "STRIKEOUT";

  if (/\bgb\b/.test(text) || /\bgb\(/.test(text)) return "GROUNDBALL";
  if (/\bfb\b/.test(text) || /\bfly\b/.test(text)) return "FLYBALL";
  if (/\blo\b/.test(text) || /\blineout\b/.test(text)) return "LINEOUT";

  return "UNKNOWN";
}

function parseRollPrefix(line = "") {
  const match = line.match(/^\s*(\d+)\s*[-–]\s*(\d+)\s+(.+)$/);

  if (!match) {
    return {
      column: null,
      roll: null,
      result: line.trim(),
    };
  }

  return {
    column: Number(match[1]),
    roll: match[2],
    result: match[3].trim(),
  };
}

export function parseCardEvents(rawText = "") {
  const lines = rawText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  let currentSide = "unknown";

  return lines
    .map((line, index) => {
      const detectedSide = normalizeSide(line);

      if (detectedSide) {
        currentSide = detectedSide;
        return null;
      }

      const parsed = parseRollPrefix(line);
      const outcomeType = detectOutcomeType(parsed.result);

      if (!parsed.result || outcomeType === "UNKNOWN") return null;

      return {
        id: `${currentSide}-${index}`,
        side: currentSide,
        column: parsed.column,
        roll: parsed.roll,
        result: parsed.result,
        outcomeType,
        rawLine: line,
        isXChance: outcomeType === "GBX" || outcomeType === "FBX" || outcomeType === "X_CHANCE",
        isInjury: /\binj\b|\binjury\b|\+\s*injury/i.test(line),
        isBallparkSingle: /\bballpark\b.*\bsi\b|\bsi\b.*\bballpark\b/i.test(line),
        isBallparkHomeRun: /\bballpark\b.*\bhr\b|\bhr\b.*\bballpark\b/i.test(line),
      };
    })
    .filter(Boolean);
}

export function summarizeCardEvents(events = []) {
  return events.reduce(
    (summary, event) => {
      summary.total += 1;
      summary.bySide[event.side] = (summary.bySide[event.side] || 0) + 1;
      summary.byOutcome[event.outcomeType] =
        (summary.byOutcome[event.outcomeType] || 0) + 1;

      if (event.isXChance) summary.xChances += 1;
      if (event.isInjury) summary.injuryEvents += 1;
      if (event.isBallparkSingle) summary.ballparkSingles += 1;
      if (event.isBallparkHomeRun) summary.ballparkHomeRuns += 1;

      return summary;
    },
    {
      total: 0,
      bySide: {},
      byOutcome: {},
      xChances: 0,
      injuryEvents: 0,
      ballparkSingles: 0,
      ballparkHomeRuns: 0,
    }
  );
}
