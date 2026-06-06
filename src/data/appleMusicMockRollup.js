export const appleMusicMockRollup = {
  generatedAt: "2026-06-02T12:00:00",
  source: "mock Apple Music rollup",
  privacyLevel: "aggregate-only",
  excludedContent: [
    "track names",
    "artist names",
    "album names",
    "playlist names",
    "station descriptions"
  ],
  totals: {
    totalPlays: 86615,
    totalSkips: 44155,
    totalDurationHoursCapped: 4976.97,
    firstDatePlayed: "2016-01-01",
    lastDatePlayed: "2026-05-19"
  },
  durationSanity: {
    quality: "needs-review",
    cappedDurationHours: 4976.97,
    suspiciousAverageDurationRows: 30,
    suspiciousDailyDurationRows: 8
  },
  activity: {
    activeListeningDays: 3088,
    activeDayRate: 0.8143,
    averagePlaysPerActiveDay: 28.05,
    averageHoursPerActiveDayCapped: 1.61,
    skipRate: 0.5098,
    averageMinutesPerPlayCapped: 3.45
  },
  recent: {
    last12MonthStart: "2025-05-20",
    last12MonthEnd: "2026-05-19",
    last12MonthsPlays: 12000,
    last12MonthsSkips: 6100,
    last12MonthsHoursCapped: 690.5,
    mostRecentCompleteYear: 2025,
    priorCompleteYear: 2024,
    yearOverYearPlayDelta: 850,
    yearOverYearHourDeltaCapped: 42.3
  },
  favoritesByType: [
    { favoriteType: "Songs", count: 240 },
    { favoriteType: "Albums", count: 130 },
    { favoriteType: "Playlists", count: 95 },
    { favoriteType: "Stations", count: 61 }
  ],
  playsByYear: [
    { year: "2016", plays: 4300, skips: 1900, durationHoursCapped: 240, activeDays: 210 },
    { year: "2017", plays: 6100, skips: 2800, durationHoursCapped: 350, activeDays: 245 },
    { year: "2018", plays: 7200, skips: 3300, durationHoursCapped: 415, activeDays: 260 },
    { year: "2019", plays: 7900, skips: 3700, durationHoursCapped: 460, activeDays: 275 },
    { year: "2020", plays: 9400, skips: 4800, durationHoursCapped: 560, activeDays: 300 },
    { year: "2021", plays: 8700, skips: 4500, durationHoursCapped: 520, activeDays: 292 },
    { year: "2022", plays: 8300, skips: 4200, durationHoursCapped: 500, activeDays: 286 },
    { year: "2023", plays: 9100, skips: 4700, durationHoursCapped: 545, activeDays: 298 },
    { year: "2024", plays: 10100, skips: 5200, durationHoursCapped: 610, activeDays: 310 },
    { year: "2025", plays: 10950, skips: 5600, durationHoursCapped: 652, activeDays: 318 },
    { year: "2026", plays: 4565, skips: 2455, durationHoursCapped: 124.97, activeDays: 94 }
  ],
    playsByMonth: [
    { month: "2025-06", plays: 960, skips: 480, durationHoursCapped: 54, activeDays: 26 },
    { month: "2025-07", plays: 1040, skips: 520, durationHoursCapped: 61, activeDays: 28 },
    { month: "2025-08", plays: 990, skips: 510, durationHoursCapped: 57, activeDays: 27 },
    { month: "2025-09", plays: 880, skips: 455, durationHoursCapped: 50, activeDays: 24 },
    { month: "2025-10", plays: 1120, skips: 590, durationHoursCapped: 65, activeDays: 29 },
    { month: "2025-11", plays: 1180, skips: 610, durationHoursCapped: 69, activeDays: 30 },
    { month: "2025-12", plays: 1250, skips: 650, durationHoursCapped: 74, activeDays: 31 },
    { month: "2026-01", plays: 1015, skips: 530, durationHoursCapped: 58, activeDays: 27 },
    { month: "2026-02", plays: 920, skips: 470, durationHoursCapped: 52, activeDays: 25 },
    { month: "2026-03", plays: 1065, skips: 540, durationHoursCapped: 62, activeDays: 28 },
    { month: "2026-04", plays: 1115, skips: 570, durationHoursCapped: 66, activeDays: 29 },
    { month: "2026-05", plays: 465, skips: 225, durationHoursCapped: 22.5, activeDays: 14 }
  ],
  artistYearStats: [
    { artist: "The dB's", year: 2016, plays: 42 },
    { artist: "The dB's", year: 2017, plays: 88 },
    { artist: "The dB's", year: 2018, plays: 61 },
    { artist: "The dB's", year: 2025, plays: 180 },
    { artist: "Big Star", year: 2016, plays: 120 },
    { artist: "Big Star", year: 2017, plays: 85 },
    { artist: "Big Star", year: 2024, plays: 95 },
    { artist: "Big Star", year: 2025, plays: 140 },
    { artist: "R.E.M.", year: 2019, plays: 210 },
    { artist: "R.E.M.", year: 2020, plays: 175 },
    { artist: "R.E.M.", year: 2021, plays: 130 },
    { artist: "Matthew Sweet", year: 2023, plays: 60 },
    { artist: "Matthew Sweet", year: 2024, plays: 125 },
    { artist: "Matthew Sweet", year: 2025, plays: 160 }
  ]
};
