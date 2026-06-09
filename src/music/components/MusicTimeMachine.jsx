import { useState } from "react";
import ArtistDossierModal from "./ArtistDossierModal";
import {
  getMusicTimeMachineMonth,
  musicTimeMachineMonthOptions,
} from "../../utils/musicTimeMachine";

const quickRanges = [
  ["Spring 2020", "2020-03-01", "2020-04-30"],
  ["Summer 2021", "2021-06-01", "2021-08-31"],
  ["2015", "2015-01-01", "2015-12-31"],
  ["2016", "2016-01-01", "2016-12-31"],
  
];
const historicalMoments = [
  ["COVID Lockdown", "2020-03-01", "2020-05-31"],
  ["Pandemic Era", "2020-03-01", "2021-05-31"],
  ["Reopening Era", "2021-06-01", "2021-12-31"],
  ["2016 H1", "2016-01-01", "2016-06-30"],
  ["2016 H2", "2016-07-01", "2016-12-31"],
  ["2020 H1", "2020-01-01", "2020-06-30"],
  ["2020 H2", "2020-07-01", "2020-12-31"],
];
function parseDate(dateString) {
  return new Date(`${dateString}T00:00:00`);
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function getRangeLengthDays(startDate, endDate) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  const millisecondsPerDay = 24 * 60 * 60 * 1000;

  return Math.round((end - start) / millisecondsPerDay) + 1;
}

function shiftDateRange(startDate, endDate, direction) {
  const rangeLengthDays = getRangeLengthDays(startDate, endDate);
  const shiftDays = rangeLengthDays * direction;

  const nextStart = parseDate(startDate);
  const nextEnd = parseDate(endDate);

  nextStart.setDate(nextStart.getDate() + shiftDays);
  nextEnd.setDate(nextEnd.getDate() + shiftDays);

  return {
    startDate: formatDate(nextStart),
    endDate: formatDate(nextEnd),
  };
}

export default function MusicTimeMachine() {
  const [selectedArtist, setSelectedArtist] = useState(null);
  const [selectedDossierArtist, setSelectedDossierArtist] = useState(null);
  const [selectedMonthKey, setSelectedMonthKey] = useState("2020-03");
  const [startDate, setStartDate] = useState("2020-03-01");
  const [endDate, setEndDate] = useState("2020-04-30");
  const [rangeRead, setRangeRead] = useState(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState("");

  const month = getMusicTimeMachineMonth(selectedMonthKey);

  function updateDateRange(nextStartDate, nextEndDate) {
    setStartDate(nextStartDate);
    setEndDate(nextEndDate);
    setRangeRead(null);
    setRangeError("");
  }

  function movePeriod(direction) {
    const nextRange = shiftDateRange(startDate, endDate, direction);
    updateDateRange(nextRange.startDate, nextRange.endDate);
  }

  async function generateRangeRead() {
    setRangeLoading(true);
    setRangeError("");
    setRangeRead(null);

    try {
      const response = await fetch(
        `http://localhost:4000/api/music/time-machine?start=${startDate}&end=${endDate}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate Time Machine read");
      }

      setRangeRead(data);
    } catch (error) {
      setRangeError(error.message);
    } finally {
      setRangeLoading(false);
    }
  }

  return (
    <div className="mb-4 rounded-2xl border border-sky-500/30 bg-slate-950/70 p-5 shadow-lg">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-sky-300">
            Curated Time Machine
          </p>
          <h3 className="mt-1 text-xl font-semibold text-white">
            {month.label}
          </h3>
          <p className="mt-2 text-base italic text-slate-200">
            {month.headline}
          </p>
          <p className="mt-1 text-sm text-slate-400">{month.context}</p>
        </div>

        <select
          className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
          value={selectedMonthKey}
          aria-label="Select Time Machine month"
          onChange={(event) => setSelectedMonthKey(event.target.value)}
        >
          {musicTimeMachineMonthOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <Metric label="Evidence Found" value={month.totalPlays} />
        <Metric label="Source Type" value="Library Last Played" />
        <Metric label="Confidence" value="Directional" />
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <ListCard title="Top Artists" items={month.topArtists} />
        <ListCard title="Top Albums" items={month.topAlbums} />
      </div>

      <div className="mt-5">
        <ListCard title="Behavior Read" items={month.behaviorRead} />
      </div>

      <div className="mt-5 rounded-xl border border-slate-800 bg-slate-900/70 p-4">
        <h4 className="font-semibold text-white">Memory Anchors</h4>
        <p className="mt-2 text-sm text-slate-300">{month.memoryPrompt}</p>
      </div>

      <div className="mt-6 rounded-2xl border border-sky-500/40 bg-slate-900/80 p-5">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-sky-300">
            Live Time Machine Query
          </p>
          <h4 className="mt-1 text-lg font-semibold text-white">
            Explore any date range
          </h4>
          <p className="mt-1 text-sm text-slate-400">
            Query the live Apple Music rollup without reading raw JSON.
          </p>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          <label className="text-sm text-slate-300">
            Start Date
            <input
              type="date"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={startDate}
              onChange={(event) =>
                updateDateRange(event.target.value, endDate)
              }
            />
          </label>

          <label className="text-sm text-slate-300">
            End Date
            <input
              type="date"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={endDate}
              onChange={(event) =>
                updateDateRange(startDate, event.target.value)
              }
            />
          </label>

          <button
            type="button"
            className="self-end rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={generateRangeRead}
            disabled={rangeLoading}
          >
            {rangeLoading ? "Generating..." : "Generate"}
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {quickRanges.map(([label, start, end]) => (
            <button
              key={label}
              type="button"
              className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-sky-400 hover:text-sky-200"
              onClick={() => updateDateRange(start, end)}
            >
              {label}
            </button>
          ))}
        </div>
<div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
    Historical Moments
  </p>

  <div className="mt-3 flex flex-wrap gap-2">
    {historicalMoments.map(([label, start, end]) => (
      <button
        key={label}
        type="button"
        className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-sky-400 hover:text-sky-200"
        onClick={() => updateDateRange(start, end)}
      >
        {label}
      </button>
    ))}
  </div>
</div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-xl border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-300 hover:border-sky-400 hover:text-sky-200"
            onClick={() => movePeriod(-1)}
          >
            Previous Period
          </button>

          <button
            type="button"
            className="rounded-xl border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-300 hover:border-sky-400 hover:text-sky-200"
            onClick={() => movePeriod(1)}
          >
            Next Period
          </button>
        </div>

        {rangeError && (
          <p className="mt-3 text-sm text-rose-300">{rangeError}</p>
        )}

        {rangeRead && (
          <div className="mt-5 space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Metric
                label="Date Range"
                value={`${rangeRead.startDate} to ${rangeRead.endDate}`}
              />
              <Metric
                label="Tracks Matched"
                value={`${rangeRead.tracksMatched ?? 0} tracks`}
              />
              <Metric label="Source" value="Live Query" />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
  <LiveJsonList
    title="Top Albums"
    items={rangeRead.topAlbums}
  />

  <LiveJsonList
    title="Top Artists"
    items={rangeRead.topArtists}
    onItemClick={setSelectedArtist}
  />
</div>

            <LiveTextCard title="Memory Read" items={rangeRead.memoryRead} />
            {selectedArtist && (
              <ArtistJourneyCard
                artist={selectedArtist}
                journey={rangeRead.artistJourneys?.[selectedArtist.label]}
                onOpenDossier={() =>
                  {
                    const journey =
                      rangeRead.artistJourneys?.[selectedArtist.label];

                    const years = (journey?.timeline ?? [])
                      .map((item) => Number(item.year))
                      .filter(Boolean);

                    setSelectedDossierArtist({
                      artist: selectedArtist,
                      journey: {
                        ...journey,
                        journeyType: getArtistJourneyType(years),
                      },
                    });
                  }
                }
              />
            )}

            {selectedDossierArtist && (
              <ArtistDossierModal
                dossier={selectedDossierArtist}
                onClose={() => setSelectedDossierArtist(null)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}


function getArtistJourneyType(years = []) {
  if (!years.length) return "Needs Timeline";

  const sortedYears = [...years].sort((a, b) => a - b);
  const latest = sortedYears[sortedYears.length - 1];
  const previous = sortedYears[sortedYears.length - 2];
  const gapBeforeLatest = previous ? latest - previous : 0;

  if (latest < 2024) return "Dormant";
  if (gapBeforeLatest >= 3) return "Returning";
  if (sortedYears.length >= 6 && latest >= 2024) return "Persistence";

  return "Developing";
}

function ListCard({ title, items }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <h4 className="font-semibold text-white">{title}</h4>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
function ArtistJourneyCard({ artist, journey, onOpenDossier }) {
  const count = artist?.count ?? 0;
  const timeline = journey?.timeline ?? [];
  const maxTimelineCount = timeline.length
    ? Math.max(...timeline.map((item) => item.count))
    : 0;

  const years = timeline.map((item) => Number(item.year)).filter(Boolean);
  const yearsActive = years.length || "Pending";
  const latestYear = years.length ? Math.max(...years) : "Pending";
  const peakYears = timeline
    .filter((item) => maxTimelineCount && item.count === maxTimelineCount)
    .map((item) => item.year);
  const peakYearLabel = peakYears.length ? peakYears.join(", ") : "Pending";

  const journeyType = getArtistJourneyType(years);

  function getNarrative() {
    if (!journey || timeline.length === 0) {
      return `${artist.label} appears in this selected range, but there is not enough timeline data yet to describe the longer journey.`;
    }

    const firstSeen = journey.firstSeen ?? years[0] ?? "an earlier period";
    const peakYear = peakYears[0] ?? journey.mostActivePeriod ?? "one period";

    if (latestYear !== "Pending" && latestYear !== Number(peakYear)) {
      return `${artist.label} appears across ${years.length} listening years, first showing up in ${firstSeen}, peaking in ${peakYear}, and remaining active through ${latestYear}.`;
    }

    return `${artist.label} appears across ${years.length} listening years, first showing up in ${firstSeen} and peaking in ${peakYear}.`;
  }

  return (
    <div className="rounded-xl border border-sky-500/40 bg-slate-900/80 p-4">
      <h4 className="font-semibold text-white">Artist Journey</h4>

      <p className="mt-2 text-lg font-semibold text-sky-100">
        {artist.label}
      </p>

      <div className="mt-2 inline-flex rounded-full border border-amber-400/40 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-200">
        {journeyType}
      </div>

      <p className="mt-3 rounded-lg border border-sky-500/20 bg-sky-950/30 p-3 text-sm leading-relaxed text-sky-100">
        {getNarrative()}
      </p>

      <Metric
  label="Activity in Range"
  value={`${count} ${count === 1 ? "play" : "plays"}`}
/>

      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Yearly Activity
        </p>

        {timeline.length === 0 ? (
          <p className="mt-2 text-sm text-slate-300">
            Timeline data is not available for this artist yet.
          </p>
        ) : (
          <div className="mt-3 space-y-2 text-sm">
            {timeline.map((item) => {
              const percent = maxTimelineCount
                ? Math.max(
                    4,
                    Math.round((item.count / maxTimelineCount) * 100)
                  )
                : 4;
              const isPeak =
                maxTimelineCount && item.count === maxTimelineCount;

              return (
                <div
                  key={item.year}
                  className="grid grid-cols-[3rem_1fr_4rem] items-center gap-3 text-slate-300"
                >
                  <span className="text-xs font-semibold text-slate-500">
                    {item.year}
                  </span>

                  <div className="flex items-center gap-2">
                    <div className="h-2 flex-1 rounded-full bg-slate-800">
                      <div
                        className="h-2 rounded-full bg-sky-400"
                        style={{ width: `${percent}%` }}
                      />
                    </div>

                    {isPeak && (
                      <span className="rounded-full border border-amber-400/40 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
                        Peak
                      </span>
                    )}
                  </div>

                  <span className="text-right text-xs font-semibold text-slate-400">
                    {item.count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={onOpenDossier}
        className="mt-4 rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-2 text-sm font-semibold text-sky-100 hover:bg-sky-500/20"
      >
        Open Artist Dossier
      </button>
    </div>
  );
}
function LiveJsonList({ title, items = [], onItemClick }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4">
      <h4 className="font-semibold text-white">{title}</h4>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No results found.</p>
      ) : (
        <ol className="mt-3 space-y-2 text-sm text-slate-300">
          {items.map((item, index) => {
            const label = item.album || item.artist || item.name || "Unknown";
            const count = item.count ?? item.plays ?? item.total ?? null;

            return (
              <li
                key={`${label}-${index}`}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2"
              >
                <button
  type="button"
  onClick={() => onItemClick?.({ ...item, label, count })}
  className="text-left font-semibold text-sky-200 underline-offset-4 hover:text-sky-100 hover:underline"
>
  {label}
</button>
                {count !== null && (
                  <span className="text-xs font-semibold text-sky-300">
                    {count}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

function LiveTextCard({ title, items = [] }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4">
      <h4 className="font-semibold text-white">{title}</h4>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No memory read available.</p>
      ) : (
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}







