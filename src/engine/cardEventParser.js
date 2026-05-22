function detectHandednessHeader(line = "") {
  const text = line.toLowerCase();

  const hasLeft =
    /vs\W*lefty/.test(text) ||
    /vs\W*left/.test(text) ||
    text.includes("vs lhp") ||
    text.includes("left-handed pitcher") ||
    text.includes("left handed pitcher");

  const hasRight =
    /vs\W*righty/.test(text) ||
    /vs\W*right/.test(text) ||
    text.includes("vs rhp") ||
    text.includes("right-handed pitcher") ||
    text.includes("right handed pitcher");

  if (hasLeft && hasRight) return "dual";
  if (hasLeft) return "vsLHP";
  if (hasRight) return "vsRHP";

  return null;
}

function detectOutcomeType(result = "") {
  const text = result.toLowerCase();

  if (/\bgbx\b/.test(text) || /\bgb\(.*\)x\b/.test(text)) return "GBX";
  if (/\bfbx\b/.test(text) || /\bfb\(.*\)x\b/.test(text)) return "FBX";
  if (/\bx\b/.test(text)) return "X_CHANCE";

  if (/\binj\b/.test(text) || /\binjury\b/.test(text)) return "INJURY";

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
  if (/\bpopout\b/.test(text)) return "POPOUT";
  if (/\bfoulout\b/.test(text)) return "FOULOUT";

  return "UNKNOWN";
}

function parseRollPrefix(line = "") {
  const match = line.match(/^\s*[#$>]*\s*(\d{1,2})\s*[-ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ]\s*(.*)$/);

  if (!match) {
    return {
      roll: null,
      result: line.trim(),
      isPrimaryRoll: false,
    };
  }

  const rollNumber = Number(match[1]);
  const result = match[2].trim();

  return {
    roll: String(rollNumber),
    result,
    isPrimaryRoll: rollNumber >= 2 && rollNumber <= 12,
  };
}

function parseSplitResult(result = "") {
  const match = result.match(/^(.*?)\s+(\d{1,2})\s*[-ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ]\s*(\d{1,2})$/);

  if (!match) {
    return null;
  }

  const outcome = match[1].trim();

  return {
    result: outcome,
    outcomeType: detectOutcomeType(outcome),
    rangeStart: Number(match[2]),
    rangeEnd: Number(match[3]),
  };
}

function isColumnHeader(line = "") {
  return /^\s*1\s+2\s+3\s+1\s+2\s+3\s*$/.test(line);
}

function getSideFromBlockIndex(blockIndex) {
  if (blockIndex >= 0 && blockIndex <= 2) return "vsLHP";
  if (blockIndex >= 3 && blockIndex <= 5) return "vsRHP";
  return "unknown";
}

function getColumnFromBlockIndex(blockIndex) {
  if (blockIndex < 0) return null;
  return (blockIndex % 3) + 1;
}

function buildEvent({
  currentSide,
  currentColumn,
  parsed,
  line,
  index,
}) {
  const splitResult = parseSplitResult(parsed.result);
  const baseResult = splitResult ? splitResult.result : parsed.result;
  const outcomeType = detectOutcomeType(baseResult);

  if (!baseResult || outcomeType === "UNKNOWN") return null;

  return {
    id: `${currentSide}-${index}`,
    side: currentSide,
    column: currentColumn,
    roll: parsed.roll,
    result: baseResult,
    outcomeType,
    rawLine: line,
    splitOutcomes: splitResult ? [splitResult] : [],
    isXChance:
      outcomeType === "GBX" ||
      outcomeType === "FBX" ||
      outcomeType === "X_CHANCE",
    isInjury: /\binj\b|\binjury\b|\+\s*injury/i.test(line),
    isBallparkSingle:
      /\bballpark\b.*\bsi\b|\bsi\b.*\bballpark\b/i.test(line),
    isBallparkHomeRun:
      /\bballpark\b.*\bhr\b|\bhr\b.*\bballpark\b/i.test(line),
  };
}

export function parseCardEvents(rawText = "") {
  const lines = rawText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  let currentSide = "unknown";
  let copiedTableMode = false;
  let blockIndex = -1;
  let currentColumn = null;
  let lastPrimaryEvent = null;

  const events = [];

  lines.forEach((line, index) => {
    const handednessHeader = detectHandednessHeader(line);

    if (handednessHeader === "dual") {
      copiedTableMode = true;
      currentSide = "vsLHP";
      return;
    }

    if (handednessHeader) {
      currentSide = handednessHeader;
      return;
    }

    if (isColumnHeader(line)) return;

    const parsed = parseRollPrefix(line);

    if (copiedTableMode && parsed.isPrimaryRoll && parsed.roll === "2") {
      blockIndex += 1;
      currentSide = getSideFromBlockIndex(blockIndex);
      currentColumn = getColumnFromBlockIndex(blockIndex);
    }

    if (!parsed.isPrimaryRoll) {
      const splitResult = parseSplitResult(parsed.result);
      const continuationType = detectOutcomeType(parsed.result);

      if (splitResult && lastPrimaryEvent) {
        lastPrimaryEvent.splitOutcomes.push(splitResult);
        return;
      }

      if (continuationType === "INJURY") {
        const injuryEvent = buildEvent({
          currentSide,
          currentColumn,
          parsed,
          line,
          index,
        });

        if (injuryEvent) events.push(injuryEvent);
        return;
      }

      return;
    }

    const event = buildEvent({
      currentSide,
      currentColumn,
      parsed,
      line,
      index,
    });

    if (!event) return;

    events.push(event);
    lastPrimaryEvent = event;
  });

  return events;
}

export function summarizeCardEvents(events = []) {
  return events.reduce(
    (summary, event) => {
      summary.total += 1;

      summary.bySide[event.side] = (summary.bySide[event.side] || 0) + 1;

      if (!summary.bySideOutcome[event.side]) {
        summary.bySideOutcome[event.side] = {};
      }

      if (!summary.bySideShape[event.side]) {
        summary.bySideShape[event.side] = {
          onBase: 0,
          extraBase: 0,
          outs: 0,
          strikeouts: 0,
        };
      }

      const addOutcome = (outcomeType) => {
        if (!outcomeType) return;

        summary.byOutcome[outcomeType] =
          (summary.byOutcome[outcomeType] || 0) + 1;

        summary.bySideOutcome[event.side][outcomeType] =
          (summary.bySideOutcome[event.side][outcomeType] || 0) + 1;

        if (
          ["SINGLE", "DOUBLE", "TRIPLE", "HOME_RUN", "WALK", "HBP"].includes(
            outcomeType
          )
        ) {
          summary.bySideShape[event.side].onBase += 1;
        }

        if (["DOUBLE", "TRIPLE", "HOME_RUN"].includes(outcomeType)) {
          summary.bySideShape[event.side].extraBase += 1;
        }

        if (
          [
            "GROUNDBALL",
            "FLYBALL",
            "LINEOUT",
            "POPOUT",
            "FOULOUT",
            "STRIKEOUT",
          ].includes(outcomeType)
        ) {
          summary.bySideShape[event.side].outs += 1;
        }

        if (outcomeType === "STRIKEOUT") {
          summary.bySideShape[event.side].strikeouts += 1;
        }
      };

      addOutcome(event.outcomeType);

      event.splitOutcomes?.forEach((splitOutcome) => {
        addOutcome(splitOutcome.outcomeType);
      });

      if (event.splitOutcomes?.length) {
        summary.splitEvents += 1;
      }

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
      bySideOutcome: {},
      bySideShape: {},
      splitEvents: 0,
      xChances: 0,
      injuryEvents: 0,
      ballparkSingles: 0,
      ballparkHomeRuns: 0,
    }
  );
}