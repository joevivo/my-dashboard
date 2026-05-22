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
  if (/\binj\b/.test(text) || /\binjury\b/.test(text)) return "INJURY";
  if (/\bpopout\b/.test(text)) return "POPOUT";
  if (/\bfoulout\b/.test(text)) return "FOULOUT";

  return "UNKNOWN";
}

function parseRollPrefix(line = "") {
  const match = line.match(/^\s*[#$>]*\s*(\d{1,2})\s*[-–]\s*(.*)$/);

  if (!match) {
    return {
      column: null,
      roll: null,
      result: line.trim(),
      isPrimaryRoll: false,
    };
  }

  const rollNumber = Number(match[1]);
  const result = match[2].trim();

  const isPrimaryRoll = rollNumber >= 2 && rollNumber <= 12;

  return {
    column: null,
    roll: String(rollNumber),
    result,
    isPrimaryRoll,
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

export function parseCardEvents(rawText = "") {
  const lines = rawText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  let currentSide = "unknown";
  let copiedTableMode = false;
  let blockIndex = -1;
  let currentColumn = null;

  return lines
    .map((line, index) => {
      const handednessHeader = detectHandednessHeader(line);

      if (handednessHeader === "dual") {
        copiedTableMode = true;
        currentSide = "vsLHP";
        return null;
      }

      if (handednessHeader) {
        currentSide = handednessHeader;
        return null;
      }

      if (isColumnHeader(line)) {
        return null;
      }

      const parsed = parseRollPrefix(line);

      if (copiedTableMode && parsed.isPrimaryRoll && parsed.roll === "2") {
        blockIndex += 1;
        currentSide = getSideFromBlockIndex(blockIndex);
        currentColumn = getColumnFromBlockIndex(blockIndex);
      }

      const outcomeType = detectOutcomeType(parsed.result);

      if (!parsed.result || outcomeType === "UNKNOWN") return null;

      return {
        id: `${currentSide}-${index}`,
        side: currentSide,
        column: currentColumn,
        roll: parsed.roll,
        result: parsed.result,
        outcomeType,
        rawLine: line,
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