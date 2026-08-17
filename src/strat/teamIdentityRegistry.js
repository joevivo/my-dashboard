const RAW_STRAT_TEAM_IDENTITIES = [
  // Aquarium Drinkers — canonical BIE identity.
  ["1851052", "479336", "Aquarium Drinkers", true],
  ["1853975", "479431", "Aquarium Drinkers", true],
  ["1854215", "479610", "Aquarium Drinkers", true],
["1856033", "479640", "Aquarium Drinkers", true],

  // League 479336.
  ["1853382", "479336", "Iowa bombers", false],
  ["1853443", "479336", "Mighty Yankees", false],
  ["1853506", "479336", "Norwich Not Flatlanders", false],
  ["1853519", "479336", "Busch League Arkinals™", false],
  ["1853534", "479336", "Northside Hogs", false],
  ["1853540", "479336", "Classic City Crazy Eights", false],
  ["1853550", "479336", "Boquete Bombers", false],
  ["1853594", "479336", "Funk Brothers", false],
  ["1853598", "479336", "New York Highlanders", false],
  ["1853667", "479336", "Fresno Raisin Eaters", false],
  ["1853674", "479336", "RainRain 80's Mustache", false],

  // League 479431.
  ["1854055", "479431", "Gashouse Gorillas", false],
  ["1854297", "479431", "Milan Azzurri", false],
  ["1854324", "479431", "Toledo Knights", false],
  ["1854355", "479431", "Ohio Players", false],
  ["1854376", "479431", "Ukrainian Drones", false],
  ["1854378", "479431", "MemorialCardnal Arkinals™", false],
  ["1854429", "479431", "Crystal Sky Chanticleers", false],
  ["1854461", "479431", "Willis Towers", false],
  ["1854468", "479431", "Hey Jude", false],
  ["1854491", "479431", "Atlanta Crew", false],
  ["1854501", "479431", "Brooklyn Bombers", false],

  // League 479610.
  ["1851199", "479610", "Cabrillo Beach rhino rats", false],
  ["1851816", "479610", "MotorCity Mashers", false],
  ["1854054", "479610", "Hey Judes", false],
  ["1855742", "479610", "Cape Coral Dabblers-80", false],
  ["1855828", "479610", "Sixties Hippies", false],
  ["1855876", "479610", "Georgia Peaches", false],
  ["1855893", "479610", "Tulsa Drillers", false],
  ["1855969", "479610", "Napa Valley Crushers", false],
  ["1855976", "479610", "Grant Park Weathermen", false],
  ["1855985", "479610", "Virginia Outlaws", false],
  ["1856003", "479610", "Taguig Moto Kings", false],
// League 479640.
["1856113", "479640", "Harlem Fences", false],
["1856487", "479640", "Fairfield Judds", false],
["1854059", "479640", "norwich Herbie's", false],
["1856196", "479640", "Faraway Galaxys", false],
["1856488", "479640", "Alicante Singers", false],
["1855793", "479640", "Boquete Bombers 3", false],
["1853415", "479640", "Piermont Fireflies", false],
["1856313", "479640", "Tidewater Thunder", false],
["1856460", "479640", "Port Orchard Pansies", false],
["1856148", "479640", "Marble Mothmen", false],
["1856417", "479640", "Back To the future", false],
];

function buildMonogram(teamName) {
  const words = String(teamName || "")
    .replace(/[™®]/g, "")
    .replace(/[^A-Za-z0-9' -]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

  if (!words.length) {
    return "?";
  }

  const meaningfulWords = words.filter(
    (word) =>
      !["the", "of", "and"].includes(word.toLowerCase()),
  );

  const source =
    meaningfulWords.length > 0
      ? meaningfulWords
      : words;

  if (source.length === 1) {
    return source[0]
      .slice(0, 2)
      .toUpperCase();
  }

  return source
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

export const STRAT_TEAM_IDENTITIES =
  Object.freeze(
    Object.fromEntries(
      RAW_STRAT_TEAM_IDENTITIES.map(
        ([teamId, leagueId, teamName, isAquarium]) => [
          teamId,
          Object.freeze({
            teamId,
            leagueId,
            teamName,
            isAquarium,
            monogram: buildMonogram(teamName),

            // Aquarium already has its canonical shield.
            // Opponent logos become active only after artwork is approved.
            logoPath: isAquarium
              ? "/aquarium-drinkers-shield.svg"
              : `/strat/team-logos/${teamId}.png`,

            // Deterministic target for future approved opponent artwork.
            proposedLogoPath: isAquarium
              ? "/aquarium-drinkers-shield.svg"
              : `/strat/team-logos/${teamId}.png`,

            logoStatus: "AVAILABLE",
          }),
        ],
      ),
    ),
  );

export function getStratTeamIdentity(
  teamId,
  fallbackName = "Unknown Team",
) {
  const normalizedTeamId =
    String(teamId || "");

  const known =
    STRAT_TEAM_IDENTITIES[normalizedTeamId];

  if (known) {
    return known;
  }

  return {
    teamId: normalizedTeamId || null,
    leagueId: null,
    teamName: fallbackName,
    isAquarium: false,
    monogram: buildMonogram(fallbackName),
    logoPath: null,
    proposedLogoPath: normalizedTeamId
      ? `/strat/team-logos/${normalizedTeamId}.png`
      : null,
    logoStatus: "UNREGISTERED_FALLBACK",
  };
}

export function getStratTeamMark(
  teamId,
  fallbackName,
) {
  const identity =
    getStratTeamIdentity(
      teamId,
      fallbackName,
    );

  return {
    teamId: identity.teamId,
    teamName: identity.teamName,
    logoPath: identity.logoPath,
    monogram: identity.monogram,
    logoStatus: identity.logoStatus,
  };
}