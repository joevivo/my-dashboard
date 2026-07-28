import { useState } from "react";
import ArtistDossierModal from "./ArtistDossierModal";
import MusicIntelligenceErrorBoundary from "./MusicIntelligenceErrorBoundary";

const API_ROOT = "http://localhost:4000";

const quickRanges = [
  ["Spring 2020", "2020-03-01", "2020-04-30"],
  ["Summer 2021", "2021-06-01", "2021-08-31"],
  ["2015", "2015-01-01", "2015-12-31"],
  ["2016", "2016-01-01", "2016-12-31"],
];

const statusLabels = {
  available: "Available",
  searched_with_evidence: "Evidence found",
  searched_no_evidence: "Searched — no evidence",
  not_searched: "Not searched",
  unavailable: "Unavailable",
  stale: "Stale",
  unsupported_for_period: "Unsupported for period",
  partial_coverage: "Partial coverage",
  evidence_found: "Evidence found",
  no_matching_evidence: "No matching evidence",
  unsupported_period: "Unsupported period",
  operational_error: "Operational error",
};

const statusMessages = {
  searched_no_evidence:
    "The source was searched successfully, but no matching evidence was found.",
  not_searched:
    "This source was not searched for the selected period.",
  unavailable:
    "This source is currently unavailable.",
  stale:
    "This source is available, but its evidence is stale.",
  unsupported_for_period:
    "This source does not cover the selected period.",
};

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

function formatMetric(value, suffix = "") {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  return `${value.toLocaleString()}${suffix}`;
}

function formatStatus(status) {
  if (!status) {
    return "Unknown";
  }

  return (
    statusLabels[status] ||
    status
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ")
  );
}

function getErrorMessage(payload) {
  if (typeof payload?.error === "string") {
    return payload.error;
  }

  if (payload?.error?.message) {
    return payload.error.message;
  }

  return "Period Intelligence could not complete the request.";
}

function normalizeListItem(item, index) {
  if (typeof item === "string") {
    return {
      key: `${item}-${index}`,
      label: item,
      count: null,
      raw: item,
    };
  }

  const label =
    item?.artist ||
    item?.album ||
    item?.track ||
    item?.name ||
    item?.label ||
    "Unknown";

  const count =
    item?.actualPlays ??
    item?.count ??
    item?.plays ??
    item?.total ??
    item?.objectCount ??
    null;

  return {
    key: `${label}-${index}`,
    label,
    count,
    raw: item,
  };
}

function Metric({ label, value, detail }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      {detail && <p className="mt-1 text-xs text-slate-400">{detail}</p>}
    </div>
  );
}

function StatusBadge({ status }) {
  return (
    <span className="inline-flex rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-1 text-xs font-semibold text-sky-200">
      {formatStatus(status)}
    </span>
  );
}

function EmptySourceState({ status, fallback }) {
  return (
    <p className="mt-3 text-sm leading-relaxed text-slate-400">
      {statusMessages[status] || fallback}
    </p>
  );
}

function StructuredListCard({
  title,
  items = [],
  status,
  countLabel,
  onItemClick,
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-start justify-between gap-3">
        <h5 className="font-semibold text-white">{title}</h5>
        {status && <StatusBadge status={status} />}
      </div>

      {items.length === 0 ? (
        <EmptySourceState
          status={status}
          fallback="No matching items were returned."
        />
      ) : (
        <ol className="mt-3 space-y-2 text-sm">
          {items.map((item, index) => {
            const normalized = normalizeListItem(item, index);
            const labelContent = onItemClick ? (
              <button
                type="button"
                onClick={() =>
                  onItemClick({
                    ...normalized.raw,
                    label: normalized.label,
                    count: normalized.count,
                  })
                }
                className="text-left font-semibold text-sky-200 underline-offset-4 hover:text-sky-100 hover:underline"
              >
                {normalized.label}
              </button>
            ) : (
              <span className="font-semibold text-slate-200">
                {normalized.label}
              </span>
            );

            return (
              <li
                key={normalized.key}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2"
              >
                {labelContent}

                {normalized.count !== null && (
                  <span className="text-right text-xs font-semibold text-sky-300">
                    {normalized.count.toLocaleString()}
                    {countLabel ? ` ${countLabel}` : ""}
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

function TextEvidenceCard({ title, items = [], emptyMessage }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <h5 className="font-semibold text-white">{title}</h5>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-400">{emptyMessage}</p>
      ) : (
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-300">
          {items.map((item, index) => (
            <li key={`${String(item)}-${index}`}>
              {typeof item === "string"
                ? item
                : item?.message || item?.statement || item?.label || "Unspecified"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CoverageCard({ coverage }) {
  const limitations = coverage?.limitations ?? [];
  const recordsMatched = coverage?.recordsMatched;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">
            {coverage?.sourceType || "Evidence source"}
          </p>
          <h5 className="mt-1 font-semibold text-white">
            {coverage?.sourceId || "Unknown source"}
          </h5>
        </div>

        <StatusBadge status={coverage?.status} />
      </div>

      <p className="mt-3 text-sm text-slate-300">
        Records matched:{" "}
        <span className="font-semibold text-white">
          {recordsMatched === null || recordsMatched === undefined
            ? "Unavailable"
            : recordsMatched.toLocaleString()}
        </span>
      </p>

      {coverage?.coverageStart && coverage?.coverageEnd && (
        <p className="mt-1 text-xs text-slate-400">
          Coverage: {coverage.coverageStart} to {coverage.coverageEnd}
        </p>
      )}

      {limitations.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-xs leading-relaxed text-amber-200">
          {limitations.map((limitation, index) => (
            <li key={`${limitation}-${index}`}>{limitation}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SourceSection({ title, status, note, children }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-lg font-semibold text-white">{title}</h4>
          {note && (
            <p className="mt-1 max-w-4xl text-sm leading-relaxed text-slate-400">
              {note}
            </p>
          )}
        </div>

        <StatusBadge status={status} />
      </div>

      <div className="mt-4">{children}</div>
    </section>
  );
}

function ArtistJourneyCard({ artist, journey, onOpenDossier }) {
  const timeline = journey?.timeline ?? [];
  const maxTimelineCount = timeline.length
    ? Math.max(...timeline.map((item) => item.count ?? 0))
    : 0;

  return (
    <section className="rounded-2xl border border-sky-500/40 bg-sky-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-sky-300">
            Backend Artist Journey
          </p>
          <h4 className="mt-1 text-xl font-semibold text-white">
            {artist.label}
          </h4>
        </div>

        <StatusBadge status={journey?.status || "unavailable"} />
      </div>

      {!journey ? (
        <p className="mt-4 text-sm text-slate-300">
          No governed artist-journey record was returned for this artist.
        </p>
      ) : (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Metric
              label="Evidence in Range"
              value={formatMetric(artist.count)}
              detail="Library Evidence records, not Actual Plays"
            />
            <Metric
              label="First Seen"
              value={journey.firstSeen || "Unavailable"}
            />
            <Metric
              label="Most Active Period"
              value={journey.mostActivePeriod || "Unavailable"}
            />
          </div>

          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <h5 className="font-semibold text-white">Yearly Evidence</h5>

            {timeline.length === 0 ? (
              <p className="mt-3 text-sm text-slate-400">
                Timeline evidence is unavailable.
              </p>
            ) : (
              <div className="mt-3 space-y-2">
                {timeline.map((item) => {
                  const percent = maxTimelineCount
                    ? Math.max(
                        4,
                        Math.round(((item.count ?? 0) / maxTimelineCount) * 100)
                      )
                    : 4;

                  return (
                    <div
                      key={item.year}
                      className="grid grid-cols-[3rem_1fr_4rem] items-center gap-3"
                    >
                      <span className="text-xs font-semibold text-slate-500">
                        {item.year}
                      </span>
                      <div className="h-2 rounded-full bg-slate-800">
                        <div
                          className="h-2 rounded-full bg-sky-400"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                      <span className="text-right text-xs font-semibold text-slate-300">
                        {item.count}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <StructuredListCard
              title="Journey Albums"
              items={journey.topAlbums ?? []}
              status="available"
              countLabel="records"
            />
            <StructuredListCard
              title="Journey Tracks"
              items={journey.topTracks ?? []}
              status="available"
              countLabel="records"
            />
          </div>

          <button
            type="button"
            onClick={onOpenDossier}
            className="mt-4 rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-2 text-sm font-semibold text-sky-100 hover:bg-sky-500/20"
          >
            Open Artist Dossier
          </button>
        </>
      )}
    </section>
  );
}

function MusicTimeMachineContent() {
  const [selectedArtist, setSelectedArtist] = useState(null);
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [startDate, setStartDate] = useState("2020-03-01");
  const [endDate, setEndDate] = useState("2020-04-30");
  const [rangeRead, setRangeRead] = useState(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState("");

  function updateDateRange(nextStartDate, nextEndDate) {
    setStartDate(nextStartDate);
    setEndDate(nextEndDate);
    setRangeRead(null);
    setRangeError("");
    setSelectedArtist(null);
    setIsDossierOpen(false);
  }

  function movePeriod(direction) {
    const nextRange = shiftDateRange(startDate, endDate, direction);
    updateDateRange(nextRange.startDate, nextRange.endDate);
  }

  async function generateRangeRead() {
    setRangeLoading(true);
    setRangeError("");
    setRangeRead(null);
    setSelectedArtist(null);
    setIsDossierOpen(false);

    try {
      const query = new URLSearchParams({
        start: startDate,
        end: endDate,
        timeZone: "America/Chicago",
      });

      const response = await fetch(
        `${API_ROOT}/api/music/query/period?${query.toString()}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(getErrorMessage(data));
      }

      setRangeRead(data);
    } catch (error) {
      setRangeError(error.message);
    } finally {
      setRangeLoading(false);
    }
  }

  const summary = rangeRead?.summary ?? {};
  const period = rangeRead?.period ?? {};
  const activity = rangeRead?.activity ?? {};
  const libraryEvidence = rangeRead?.libraryEvidence ?? {};
  const recentApple = rangeRead?.recentAppleObservations ?? {};
  const coverage = rangeRead?.coverage ?? [];
  const warnings = rangeRead?.warnings ?? [];
  const confidence = rangeRead?.confidence ?? {};
  const artistJourneys = libraryEvidence.artistJourneys ?? {};
  const selectedJourney = selectedArtist
    ? artistJourneys[selectedArtist.label]
    : null;

  return (
    <div className="mb-4 rounded-2xl border border-sky-500/30 bg-slate-950/70 p-5 shadow-lg">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-sky-300">
          Music Time Machine
        </p>
        <h3 className="mt-1 text-xl font-semibold text-white">
          Investigate a listening period
        </h3>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-slate-400">
          Actual Listening, Library Evidence, Recent Apple Objects, and playback
          context remain separate. Unavailable evidence is never converted into
          a zero.
        </p>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
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
          {rangeLoading ? "Investigating..." : "Investigate"}
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
        <p className="mt-4 rounded-xl border border-rose-500/30 bg-rose-950/30 p-3 text-sm text-rose-200">
          {rangeError}
        </p>
      )}

      {rangeRead && (
        <div className="mt-6 space-y-5">
          <section className="rounded-2xl border border-sky-500/40 bg-sky-950/20 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-sky-300">
                  Period Intelligence
                </p>
                <h4 className="mt-1 text-xl font-semibold text-white">
                  {summary.headline || period.label || "Period result"}
                </h4>
              </div>

              <StatusBadge status={summary.status} />
            </div>

            <p className="mt-3 max-w-4xl text-sm leading-relaxed text-slate-300">
              {summary.narrative || "No summary narrative was returned."}
            </p>

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <Metric
                label="Date Range"
                value={period.label || `${startDate} to ${endDate}`}
              />
              <Metric
                label="Inclusive Days"
                value={formatMetric(period.inclusiveDayCount)}
              />
              <Metric
                label="Confidence"
                value={formatStatus(confidence.level)}
                detail={(confidence.reasons ?? []).join(" · ")}
              />
            </div>
          </section>

          <SourceSection
            title="Actual Listening"
            status={activity.status}
            note="Confirmed listening metrics remain separate from reconstructed Library Evidence."
          >
            <div className="grid gap-3 md:grid-cols-4">
              <Metric
                label="Actual Plays"
                value={formatMetric(activity.actualPlays)}
              />
              <Metric
                label="Actual Skips"
                value={formatMetric(activity.actualSkips)}
              />
              <Metric
                label="Listening Hours"
                value={formatMetric(activity.listeningHours)}
              />
              <Metric
                label="Unique Artists"
                value={formatMetric(activity.uniqueArtistCount)}
              />
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              <StructuredListCard
                title="Top Artists by Actual Plays"
                items={activity.topArtists ?? []}
                status={activity.status}
                countLabel="plays"
              />
              <StructuredListCard
                title="Top Albums by Actual Plays"
                items={activity.topAlbums ?? []}
                status={activity.status}
                countLabel="plays"
              />
              <StructuredListCard
                title="Top Tracks by Actual Plays"
                items={activity.topTracks ?? []}
                status={activity.status}
                countLabel="plays"
              />
            </div>
          </SourceSection>

          <SourceSection
            title="Library Evidence"
            status={libraryEvidence.status}
            note={
              libraryEvidence.sourceNote ||
              "Library Last Played Date reconstruction is not complete listening history."
            }
          >
            <div className="grid gap-3 md:grid-cols-4">
              <Metric
                label="Evidence Records"
                value={formatMetric(libraryEvidence.recordCount)}
              />
              <Metric
                label="Unique Artists"
                value={formatMetric(libraryEvidence.uniqueArtistCount)}
              />
              <Metric
                label="Unique Albums"
                value={formatMetric(libraryEvidence.uniqueAlbumCount)}
              />
              <Metric
                label="Unique Tracks"
                value={formatMetric(libraryEvidence.uniqueTrackCount)}
              />
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <StructuredListCard
                title="Top Artists by Library Evidence"
                items={libraryEvidence.topArtists ?? []}
                status={libraryEvidence.status}
                countLabel="records"
                onItemClick={setSelectedArtist}
              />
              <StructuredListCard
                title="Top Albums by Library Evidence"
                items={libraryEvidence.topAlbums ?? []}
                status={libraryEvidence.status}
                countLabel="records"
              />
            </div>

            <div className="mt-4">
              <TextEvidenceCard
                title="Memory Read"
                items={libraryEvidence.memoryRead ?? []}
                emptyMessage="No Library Evidence memory read was returned."
              />
            </div>
          </SourceSection>

          {selectedArtist && (
            <ArtistJourneyCard
              artist={selectedArtist}
              journey={selectedJourney}
              onOpenDossier={() => setIsDossierOpen(true)}
            />
          )}

          <SourceSection
            title="Recent Apple Observations"
            status={recentApple.status}
            note={
              recentApple.sourceNote ||
              "Recent Apple Objects are observations and are not confirmed plays."
            }
          >
            <div className="grid gap-3 md:grid-cols-3">
              <Metric
                label="Observed Objects"
                value={formatMetric(recentApple.objectCount)}
              />
              <Metric
                label="Captured Snapshots"
                value={formatMetric(recentApple.capturedSnapshotCount)}
              />
              <Metric
                label="Latest Capture"
                value={recentApple.latestCapturedAt || "Unavailable"}
              />
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <StructuredListCard
                title="Observed Artists"
                items={recentApple.artists ?? []}
                status={recentApple.status}
                countLabel="observations"
              />
              <StructuredListCard
                title="Observed Albums"
                items={recentApple.albums ?? []}
                status={recentApple.status}
                countLabel="observations"
              />
            </div>
          </SourceSection>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h4 className="text-lg font-semibold text-white">
              Source Coverage
            </h4>
            <p className="mt-1 text-sm text-slate-400">
              Each evidence family reports its own search and availability state.
            </p>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {coverage.map((entry) => (
                <CoverageCard
                  key={`${entry.sourceId}-${entry.sourceType}`}
                  coverage={entry}
                />
              ))}
            </div>
          </section>

          {warnings.length > 0 && (
            <TextEvidenceCard
              title="Warnings"
              items={warnings}
              emptyMessage="No warnings were returned."
            />
          )}

          {isDossierOpen && (
            <ArtistDossierModal
              artist={selectedArtist}
              journey={selectedJourney}
              onClose={() => setIsDossierOpen(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function MusicTimeMachine() {
  return (
    <MusicIntelligenceErrorBoundary>
      <MusicTimeMachineContent />
    </MusicIntelligenceErrorBoundary>
  );
}