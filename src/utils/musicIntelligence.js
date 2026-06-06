export const DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS = {
  minGapYears: 3,
  minMeaningfulPlays: 50,
  recentYearWindow: 2
};

export function groupArtistYears(artistYearStats = []) {
  return artistYearStats.reduce((acc, row) => {
    if (!row?.artist || !Number.isFinite(Number(row.year))) return acc;

    const artist = row.artist;
    const year = Number(row.year);
    const plays = Number(row.plays || 0);

    if (!acc[artist]) acc[artist] = [];

    acc[artist].push({
      year,
      plays
    });

    return acc;
  }, {});
}

export function summarizeArtistYears(artistYearStats = []) {
  const grouped = groupArtistYears(artistYearStats);

  return Object.entries(grouped).map(([artist, rows]) => {
    const sortedRows = rows.sort((a, b) => a.year - b.year);
    const activeYears = [...new Set(sortedRows.map((row) => row.year))];
    const totalPlays = sortedRows.reduce((sum, row) => sum + row.plays, 0);

    return {
      artist,
      rows: sortedRows,
      activeYears,
      firstYear: activeYears[0],
      lastActiveYear: activeYears[activeYears.length - 1],
      totalPlays
    };
  });
}

export function getReturningArtists(
  artistYearStats = [],
  minGapYears = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minGapYears
) {
  return summarizeArtistYears(artistYearStats)
    .map((summary) => {
      for (let i = 1; i < summary.activeYears.length; i += 1) {
        const previousYear = summary.activeYears[i - 1];
        const returnYear = summary.activeYears[i];
        const gapLength = returnYear - previousYear - 1;

        if (gapLength >= minGapYears) {
          return {
            artist: summary.artist,
            firstYear: summary.firstYear,
            lastActiveYear: previousYear,
            returnYear,
            gapLength
          };
        }
      }

      return null;
    })
    .filter(Boolean)
    .sort((a, b) => b.gapLength - a.gapLength || a.artist.localeCompare(b.artist));
}

export function getRediscoveries(
  artistYearStats = [],
  {
    minGapYears = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minGapYears,
    minMeaningfulPlays = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minMeaningfulPlays
  } = {}
) {
  const grouped = groupArtistYears(artistYearStats);
  const returningArtists = getReturningArtists(artistYearStats, minGapYears);

  return returningArtists
    .map((artistReturn) => {
      const returnYearRows = grouped[artistReturn.artist].filter(
        (row) => row.year === artistReturn.returnYear
      );
      const returnYearPlays = returnYearRows.reduce((sum, row) => sum + row.plays, 0);

      if (returnYearPlays < minMeaningfulPlays) return null;

      return {
        ...artistReturn,
        returnYearPlays
      };
    })
    .filter(Boolean)
    .sort(
      (a, b) =>
        b.returnYearPlays - a.returnYearPlays ||
        b.gapLength - a.gapLength ||
        a.artist.localeCompare(b.artist)
    );
}

export function getDormantArtists(
  artistYearStats = [],
  currentYear,
  {
    minDormantYears = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minGapYears,
    minMeaningfulPlays = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minMeaningfulPlays
  } = {}
) {
  if (!Number.isFinite(Number(currentYear))) return [];

  return summarizeArtistYears(artistYearStats)
    .filter((summary) => {
      const dormantYears = Number(currentYear) - summary.lastActiveYear;

      return summary.totalPlays >= minMeaningfulPlays && dormantYears >= minDormantYears;
    })
    .map((summary) => ({
      artist: summary.artist,
      firstYear: summary.firstYear,
      lastActiveYear: summary.lastActiveYear,
      dormantYears: Number(currentYear) - summary.lastActiveYear,
      totalPlays: summary.totalPlays
    }))
    .sort(
      (a, b) =>
        b.dormantYears - a.dormantYears ||
        b.totalPlays - a.totalPlays ||
        a.artist.localeCompare(b.artist)
    );
}

export function getEmergingArtists(
  artistYearStats = [],
  currentYear,
  {
    recentYearWindow = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.recentYearWindow,
    minMeaningfulPlays = DEFAULT_MUSIC_INTELLIGENCE_THRESHOLDS.minMeaningfulPlays
  } = {}
) {
  if (!Number.isFinite(Number(currentYear))) return [];

  return summarizeArtistYears(artistYearStats)
    .filter((summary) => {
      const yearsSinceFirstActive = Number(currentYear) - summary.firstYear;

      return yearsSinceFirstActive <= recentYearWindow && summary.totalPlays >= minMeaningfulPlays;
    })
    .map((summary) => ({
      artist: summary.artist,
      firstYear: summary.firstYear,
      lastActiveYear: summary.lastActiveYear,
      totalPlays: summary.totalPlays
    }))
    .sort((a, b) => b.totalPlays - a.totalPlays || a.artist.localeCompare(b.artist));
}