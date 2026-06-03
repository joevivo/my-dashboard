import { appleMusicMockRollup } from "./data/appleMusicMockRollup";

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

export default function AppleMusicAnalytics() {
  const data = appleMusicMockRollup;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Listening Analytics</h2>
        <p className="mt-1 text-sm text-slate-400">
          Aggregate-only Apple Music analytics using dashboard-safe mock rollup data.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MetricCard title="Total Plays" value={data.totals.totalPlays.toLocaleString()} />
        <MetricCard
          title="Listening Hours"
          value={data.totals.totalDurationHoursCapped.toLocaleString()}
          subtitle="Capped duration"
        />
        <MetricCard title="Active Days" value={data.activity.activeListeningDays.toLocaleString()} />
        <MetricCard title="Skip Rate" value={`${(data.activity.skipRate * 100).toFixed(1)}%`} />
        <MetricCard title="Last 12 Month Plays" value={data.recent.last12MonthsPlays.toLocaleString()} />
        <MetricCard title="Data Quality" value={data.durationSanity.quality} />
      </div>
    </div>
  );
}
