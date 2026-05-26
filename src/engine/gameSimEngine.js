import { buildCardAwareLineup } from "./lineupEngine";
import { getParkData, getParkStrategySummary } from "./parkEngine";

const DEFAULT_SIMS = 1000;
const BASELINE_RUNS = 4.35;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeRate(value) {
  const number = toNumber(value, 0);

  if (number > 100) return number / 1000;
  if (number > 1) return number / 100;

  return number;
}

function hashString(value = "") {
  let hash = 2166136261;

  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
}

function seededRandom(seed) {
  let state = seed || 1;

  return function nextRandom() {
    state += 0x6d2b79f5;

    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);

    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function samplePoisson(lambda, random) {
  const safeLambda = clamp(lambda, 0.1, 12);
  const limit = Math.exp(-safeLambda);

  let product = 1;
  let count = 0;

  do {
    count += 1;
    product *= random();
  } while (product > limit);

  return count - 1;
}

function average(values = []) {
  if (!values.length) return 0;

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function getParkRunAdjustment(park) {
  if (!park) return 0;

  const singlesLeft = toNumber(park.singlesLeft, 10);
  const singlesRight = toNumber(park.singlesRight, 10);
  const homeRunsLeft = toNumber(park.homeRunsLeft, 10);
  const homeRunsRight = toNumber(park.homeRunsRight, 10);

  const singlesAverage = average([singlesLeft, singlesRight]);
  const homeRunsAverage = average([homeRunsLeft, homeRunsRight]);

  const singlesAdjustment = (singlesAverage - 10) * 0.035;
  const homeRunAdjustment = (homeRunsAverage - 10) * 0.055;

  return clamp(singlesAdjustment + homeRunAdjustment, -0.9, 1.25);
}

function getPlayerScore(player = {}, lineupIndex = 0) {
  const explicitScore = [
    player.score,
    player.totalScore,
    player.adjustedScore,
    player.matchupScore,
    player.cardScore,
  ].find((value) => Number.isFinite(Number(value)));

  if (explicitScore !== undefined) {
    return clamp(toNumber(explicitScore), 0, 100);
  }

  const obp = normalizeRate(player.obp);
  const power = toNumber(player.power ?? player.pwr, 0);
  const speed = toNumber(player.speed ?? player.spd, 0);

  const positionBonus = lineupIndex <= 4 ? 2 : 0;

  return clamp(obp * 100 + power * 5 + speed * 1.5 + positionBonus, 0, 100);
}

function getLineupRunAdjustment(lineup = []) {
  if (!lineup.length) return -1.5;

  const playerScores = lineup.map((player, index) => getPlayerScore(player, index));
  const averageScore = average(playerScores);
  const topFourScore = average(playerScores.slice(0, 4));
  const bottomThreeScore = average(playerScores.slice(-3));

  const averageAdjustment = (averageScore - 36) * 0.045;
  const topOrderAdjustment = (topFourScore - averageScore) * 0.018;
  const depthAdjustment = (bottomThreeScore - averageScore) * 0.012;

  return clamp(averageAdjustment + topOrderAdjustment + depthAdjustment, -1.2, 2.2);
}

function getObpForPitcherHand(player, pitcherHand) {
  const hand = String(pitcherHand || "R").toUpperCase();

  if (hand === "L" || hand === "LHP" || hand === "LEFT") {
    return player.obpVsL;
  }

  return player.obpVsR;
}

function parseManualLineup(hittersText = "", pitcherHand = "R") {
  return hittersText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(/\s+/);

      if (parts.length < 8) return null;

      const fieldPos = parts[0];
      const bats = parts[1];
      const defense = toNumber(parts[2], null);
      const speed = toNumber(parts[parts.length - 1], 0);
      const power = toNumber(parts[parts.length - 2], 0);
      const obpVsL = normalizeRate(parts[parts.length - 3]);
      const obpVsR = normalizeRate(parts[parts.length - 4]);
      const name = parts.slice(3, -4).join(" ");

      const player = {
        name,
        fieldPos,
        position: fieldPos,
        positions: String(fieldPos).split("/"),
        bats,
        defense,
        obpVsR,
        obpVsL,
        obp: getObpForPitcherHand({ obpVsR, obpVsL }, pitcherHand),
        power,
        speed,
      };

      return {
        ...player,
        score: Number(getPlayerScore(player).toFixed(2)),
      };
    })
    .filter(Boolean)
    .slice(0, 9);
}
const REQUIRED_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"];

function getLineupPositions(lineup = []) {
  return lineup.map((player) => player.fieldPos || player.position || "").filter(Boolean);
}

function getDuplicatePositions(positions = []) {
  return positions.filter((position, index) => positions.indexOf(position) !== index);
}

function getUniqueValues(values = []) {
  return [...new Set(values)];
}

function validateLineup({ lineup = [], lineupMode = "optimized" }) {
  const positions = getLineupPositions(lineup);
  const missingPositions = REQUIRED_POSITIONS.filter(
    (position) => !positions.includes(position)
  );
  const duplicatePositions = getUniqueValues(getDuplicatePositions(positions));
  const warnings = [];

  if (lineup.length < 9) {
    warnings.push(
      `Lineup has ${lineup.length} player${lineup.length === 1 ? "" : "s"}; expected 9.`
    );
  }

  if (missingPositions.length) {
    warnings.push(`Missing required positions: ${missingPositions.join(", ")}.`);
  }

  if (duplicatePositions.length) {
    warnings.push(`Duplicate positions detected: ${duplicatePositions.join(", ")}.`);
  }

  if (lineupMode === "manual" && warnings.length) {
    warnings.push("Manual mode uses the first nine pasted rows exactly; adjust row order or positions to make the lineup legal.");
  }

  if (lineupMode === "optimized" && warnings.length) {
    warnings.push("Optimized mode could not build a complete legal lineup from the supplied roster.");
  }

  return {
    isValid: warnings.length === 0,
    warnings,
    missingPositions,
    duplicatePositions,
    playerCount: lineup.length,
  };
}

function buildRunDistribution(results = []) {
  const buckets = {
    0: 0,
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 0,
    8: 0,
    9: 0,
    "10+": 0,
  };

  results.forEach((runs) => {
    if (runs >= 10) {
      buckets["10+"] += 1;
    } else {
      buckets[runs] += 1;
    }
  });

  return Object.entries(buckets).map(([runs, count]) => ({
    runs,
    count,
    rate: results.length ? count / results.length : 0,
  }));
}

function estimateWinProbability(avgRuns, opponentRuns = 4.5) {
  const differential = avgRuns - opponentRuns;
  const probability = 1 / (1 + Math.exp(-0.62 * differential));

  return clamp(probability, 0.08, 0.92);
}

function buildNotes({ lineup, park, avgRuns, opponentRuns, validation }) {
  const notes = [];

  if (!lineup.length) {
    notes.push("No lineup could be built from the supplied hitter text.");
    return notes;
  }

  if (validation?.warnings?.length) {
    notes.push("Lineup validation warnings are present; review roster coverage before trusting this projection.");
  }

  if (park?.environment) {
    notes.push(`${park.name || "Selected park"} profiles as ${park.environment}.`);
  }

  if (park?.notes) {
    notes.push(park.notes);
  }

  if (avgRuns >= 5.5) {
    notes.push("Projected as a strong run-scoring environment.");
  } else if (avgRuns <= 3.8) {
    notes.push("Projected as a low-run environment; defense and bullpen leverage matter more.");
  } else {
    notes.push("Projected as a moderate run environment.");
  }

  if (opponentRuns) {
    notes.push(
      `Win estimate assumes ${opponentRuns.toFixed(1)} opponent runs allowed per game.`
    );
  }

  return notes;
}

export function estimateLineupRunEnvironment({
  hittersText = "",
  pitcherHand = "R",
  parkName = "",
  sims = DEFAULT_SIMS,
  opponentRuns = 4.5,
  lineupMode = "optimized",
} = {}) {
  const safeSims = clamp(Math.round(toNumber(sims, DEFAULT_SIMS)), 100, 5000);
  const park = getParkData(parkName);
  const lineup =
    lineupMode === "manual"
      ? parseManualLineup(hittersText, pitcherHand)
      : buildCardAwareLineup({
          hittersText,
          pitcherHand,
          park,
        });

  const validation = validateLineup({
    lineup,
    lineupMode,
  });

  const lineupAdjustment = getLineupRunAdjustment(lineup);
  const parkAdjustment = getParkRunAdjustment(park);

  const avgRuns = clamp(
    BASELINE_RUNS + lineupAdjustment + parkAdjustment,
    1.8,
    8.8
  );

  const seed = hashString(
    JSON.stringify({
      hittersText,
      pitcherHand,
      parkName,
      sims: safeSims,
      avgRuns: avgRuns.toFixed(3),
    })
  );

  const random = seededRandom(seed);
  const results = Array.from({ length: safeSims }, () =>
    samplePoisson(avgRuns, random)
  );

  const simulatedAvgRuns = average(results);
  const lowRunGames = results.filter((runs) => runs <= 2).length;
  const highRunGames = results.filter((runs) => runs >= 6).length;

  return {
    inputs: {
      pitcherHand,
      parkName,
      sims: safeSims,
      opponentRuns,
      lineupMode,
    },
    park: {
      name: park?.name || parkName || "Unknown",
      environment: park?.environment || "Unknown",
      strategy: getParkStrategySummary(parkName),
      singlesLeft: park?.singlesLeft ?? null,
      singlesRight: park?.singlesRight ?? null,
      homeRunsLeft: park?.homeRunsLeft ?? null,
      homeRunsRight: park?.homeRunsRight ?? null,
    },
    validation,
    lineup: lineup.map((player, index) => ({
      slot: index + 1,
      name: player.name || player.player || "Unknown",
      fieldPos: player.fieldPos || player.position || "",
      bats: player.bats || player.hand || "",
      obp: player.obp ?? null,
      power: player.power ?? player.pwr ?? null,
      speed: player.speed ?? player.spd ?? null,
      score: Number(getPlayerScore(player, index).toFixed(2)),
    })),
    avgRuns: Number(avgRuns.toFixed(2)),
    simulatedAvgRuns: Number(simulatedAvgRuns.toFixed(2)),
    winProbability: Number(estimateWinProbability(avgRuns, opponentRuns).toFixed(3)),
    lowRunRate: Number((lowRunGames / safeSims).toFixed(3)),
    highRunRate: Number((highRunGames / safeSims).toFixed(3)),
    runDistribution: buildRunDistribution(results),
    notes: buildNotes({
      lineup,
      park,
      avgRuns,
      opponentRuns,
      validation,
    }),
  };
}