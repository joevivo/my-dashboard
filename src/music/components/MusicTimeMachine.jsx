import { useState } from "react";
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

export default function MusicTimeMachine() {
  const [selectedMonthKey, setSelectedMonthKey] = useState("2020-03");
  const [startDate, setStartDate] = useState("2020-03-01");
  const [endDate, setEndDate] = useState("2020-04-30");
  const [rangeRead, setRangeRead] = useState(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState("");

  const month = getMusicTimeMachineMonth(selectedMonthKey);

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
              onChange={(event) => setStartDate(event.target.value)}
            />
          </label>

          <label className="text-sm text-slate-300">
            End Date
            <input
              type="date"
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
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
              onClick={() => {
                setStartDate(start);
                setEndDate(end);
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {rangeError && (
          <p className="mt-3 text-sm text-rose-300">{rangeError}</p>
        )}

        {rangeRead && (
          <div className="mt-5 space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              <Metric
                label="Date Range"
                value={`${rangeRead.startDate} → ${rangeRead.endDate}`}
              />
              <Metric
                label="Tracks Matched"
                value={`${rangeRead.tracksMatched ?? 0} tracks`}
              />
              <Metric label="Source" value="Live Query" />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <LiveJsonList title="Top Albums" items={rangeRead.topAlbums} />
              <LiveJsonList title="Top Artists" items={rangeRead.topArtists} />
            </div>

            <LiveTextCard title="Memory Read" items={rangeRead.memoryRead} />
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

function LiveJsonList({ title, items = [] }) {
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
                <span>{label}</span>
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