import { parks1980 } from "../parks1980";

function getSinglesLeft(park) {
  return park.singlesLeft ?? park.siLeft ?? park.singleLeft ?? park.SIL ?? 0;
}

function getSinglesRight(park) {
  return park.singlesRight ?? park.siRight ?? park.singleRight ?? park.SIR ?? 0;
}

function getHomeRunsLeft(park) {
  return park.homeRunsLeft ?? park.hrLeft ?? park.homeRunLeft ?? park.HRL ?? 0;
}

function getHomeRunsRight(park) {
  return park.homeRunsRight ?? park.hrRight ?? park.homeRunRight ?? park.HRR ?? 0;
}

export function findParkByName(name) {
  return parks1980.find((park) => park.name === name);
}

export function getParkRunEnvironment(park) {
  if (!park) return "Unknown";

  const avgSingles = (getSinglesLeft(park) + getSinglesRight(park)) / 2;
  const avgHomeRuns = (getHomeRunsLeft(park) + getHomeRunsRight(park)) / 2;

  if (avgHomeRuns <= 4 && avgSingles >= 10) return "Low / Contact";
  if (avgHomeRuns <= 4) return "Low";
  if (avgHomeRuns >= 15) return "High Power";
  if (avgSingles >= 12) return "Contact Friendly";

  return "Moderate";
}

export function getParkNotes(park) {
  if (!park) return "No park notes available.";

  const avgSingles = (getSinglesLeft(park) + getSinglesRight(park)) / 2;
  const avgHomeRuns = (getHomeRunsLeft(park) + getHomeRunsRight(park)) / 2;

  if (avgHomeRuns <= 4 && avgSingles >= 10) {
    return "Suppresses HRs while allowing singles; rewards defense, speed, contact, bullpen leverage, and avoiding dead innings.";
  }

  if (avgHomeRuns <= 4) {
    return "Suppresses HRs; rewards defense, pitching, speed, and low-variance offense.";
  }

  if (avgHomeRuns >= 15) {
    return "Power-friendly environment; HR prevention and platoon HR exposure become major concerns.";
  }

  if (avgSingles >= 12) {
    return "Singles-friendly environment; OBP, range defense, baserunning, and sequencing gain value.";
  }

  return "Moderate offensive environment; balance lineup quality, platoon advantage, and run prevention.";
}

export function getParkData(name) {
  const park = findParkByName(name);

  if (!park) {
    return {
      name,
      singlesLeft: null,
      singlesRight: null,
      homeRunsLeft: null,
      homeRunsRight: null,
      environment: "Unknown",
      notes: "No park data found.",
    };
  }

  const normalizedPark = {
    ...park,
    singlesLeft: getSinglesLeft(park),
    singlesRight: getSinglesRight(park),
    homeRunsLeft: getHomeRunsLeft(park),
    homeRunsRight: getHomeRunsRight(park),
  };

  return {
    ...normalizedPark,
    environment: getParkRunEnvironment(normalizedPark),
    notes: getParkNotes(normalizedPark),
  };
}

export function getParkStrategySummary(name) {
  const park = getParkData(name);

  if (park.environment === "Low / Contact") {
    return "Prioritize defense, contact, bullpen leverage, speed, and avoiding dead innings.";
  }

  if (park.environment === "Low") {
    return "Run prevention and defensive range matter heavily.";
  }

  if (park.environment === "High Power") {
    return "Power bats and HR prevention become central strategic concerns.";
  }

  if (park.environment === "Contact Friendly") {
    return "OBP, sequencing, and baserunning gain additional value.";
  }

  return "Balanced environment.";
}