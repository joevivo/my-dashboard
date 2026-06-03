import { appleMusicMockRollup } from "./data/appleMusicMockRollup";

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatSignedNumber(value) {
  const number = Number(value || 0);
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toLocaleString()}`;
}

function getListeningSpanYears(data) {
  return (
    (new Date(data.totals.lastDatePlayed) -
      new Date(data.totals.firstDatePlayed)) /
    (1000 * 60 * 60 * 24 * 365.25)
  );
}

function getMostActiveYear(data) {
  return [...data.playsByYear].sort((a, b) => b.plays - a.plays)[0];
}

function MetricCard({ title, value, subtitle }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">
        {title}
      </div>
      <div className="mt-2 text-3xl font-bold text-white">{value}</div>
      {subtitle ? <div className="mt-1 text-sm text-slate-400">{subtitle}</div> : null}
    </div>
  );
}

function MetricSection({ title, description, children }) {
  return (
    <section className="space-y-4">
      <div>
        <h3 className="text-lg font-bold">{title}</h3>
        {description ? (
          <p className="mt-1 text-sm text-slate-400">{description}</p>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {children}
      </div>
    </section>
  );
}

export default function AppleMusicAnalytics() {
  const data = appleMusicMockRollup;
  const listeningSpanYears = getListeningSpanYears(data);
  const mostActiveYear = getMostActiveYear(data);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Listening Analytics</h2>
        <p className="mt-1 text-sm text-slate-400">
          Aggregate-only Apple Music analytics using dashboard-safe mock rollup data.
        </p>
      </div>

      <MetricSection
        title="Overview"
        description="High-level listening totals from the approved dashboard rollup shape."
      >
        <MetricCard title="Total Plays" value={data.totals.totalPlays.toLocaleString()} />
        <MetricCard
          title="Listening Hours"
          value={data.totals.totalDurationHoursCapped.toLocaleString()}
          subtitle="Capped duration"
        />
        <MetricCard title="Active Days" value={data.activity.activeListeningDays.toLocaleString()} />
        <MetricCard title="Skip Rate" value={formatPercent(data.activity.skipRate)} />
        <MetricCard title="Last 12 Month Plays" value={data.recent.last12MonthsPlays.toLocaleString()} />
        <MetricCard title="Data Quality" value={data.durationSanity.quality} />
      </MetricSection>

      <MetricSection
        title="Listening Trends"
        description="Recent behavior and rollup health without exposing tracks, artists, albums, playlists, or stations."
      >
        <MetricCard
          title="Date Range"
          value={`${data.totals.firstDatePlayed} → ${data.totals.lastDatePlayed}`}
        />
        <MetricCard
          title="Active Day Rate"
          value={formatPercent(data.activity.activeDayRate)}
        />
        <MetricCard
          title="Avg Plays / Active Day"
          value={data.activity.averagePlaysPerActiveDay.toLocaleString()}
        />
        <MetricCard
          title="Avg Hours / Active Day"
          value={data.activity.averageHoursPerActiveDayCapped.toLocaleString()}
          subtitle="Capped duration"
        />
        <MetricCard
          title="YoY Play Delta"
          value={formatSignedNumber(data.recent.yearOverYearPlayDelta)}
          subtitle={`${data.recent.priorCompleteYear} → ${data.recent.mostRecentCompleteYear}`}
        />
        <MetricCard
          title="Music Companion Rate"
          value={formatPercent(data.activity.activeDayRate)}
          subtitle={`${data.activity.activeListeningDays.toLocaleString()} active days across ${listeningSpanYears.toFixed(1)} years`}
        />
      </MetricSection>

      <MetricSection
        title="Listening Identity"
        description="Long-view signals that describe how music has accompanied daily life."
      >
        <MetricCard
          title="Listening Span"
          value={`${listeningSpanYears.toFixed(1)} years`}
          subtitle={`${data.totals.firstDatePlayed} → ${data.totals.lastDatePlayed}`}
        />
        <MetricCard
          title="Most Active Year"
          value={mostActiveYear.year}
          subtitle={`${mostActiveYear.plays.toLocaleString()} plays`}
        />
        <MetricCard
          title="Most Active Year Hours"
          value={mostActiveYear.durationHoursCapped.toLocaleString()}
          subtitle="Capped duration"
        />
        <MetricCard
          title="Favorite Type Buckets"
          value={data.favoritesByType.length.toLocaleString()}
        />
        <MetricCard
          title="Avg Minutes / Play"
          value={data.activity.averageMinutesPerPlayCapped.toLocaleString()}
          subtitle="Capped duration"
        />
        <MetricCard
          title="Duration Flags"
          value={(
            data.durationSanity.suspiciousAverageDurationRows +
            data.durationSanity.suspiciousDailyDurationRows
          ).toLocaleString()}
          subtitle="Rows needing review"
        />
      </MetricSection>
    </div>
  );
}
