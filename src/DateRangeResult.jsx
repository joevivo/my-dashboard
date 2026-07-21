const STATUS_LABELS = {
  searched_with_evidence: "Searched — evidence found",
  searched_no_evidence: "Searched — no evidence found",
  not_searched: "Not searched",
  unavailable: "Unavailable",
  stale: "Stale",
  unsupported_for_period: "Outside coverage",
  available: "Available",
};

const SOURCE_LABELS = {
  actual_listening: "Actual Listening",
  library_evidence: "Library Evidence",
  recent_apple_observation: "Recent Apple Objects",
  playback_context: "Playback Context",
};

function statusLabel(value) {
  return STATUS_LABELS[value] || String(value || "unknown").replace(/_/g, " ");
}

function sourceLabel(item) {
  return SOURCE_LABELS[item?.sourceType] || item?.sourceId || "Unknown source";
}

function numeric(value) {
  if (value === null || value === undefined || value === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumber(value, digits = 0) {
  const parsed = numeric(value);

  if (parsed === null) return "—";

  return parsed.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  });
}

function plural(value, singular, pluralValue = `${singular}s`) {
  return Number(value) === 1 ? singular : pluralValue;
}

function buildPresentation(result) {
  const activity = result?.activity || {};
  const library = result?.libraryEvidence || {};
  const recent = result?.recentAppleEvidence || {};
  const coverage = Array.isArray(result?.coverage) ? result.coverage : [];

  const actualCoverage = coverage.find(
    (item) => item.sourceId === "apple_daily_track_summary"
  );

  const plays = numeric(activity.actualPlays);
  const skips = numeric(activity.actualSkips);
  const hours = numeric(activity.listeningHours);
  const tracks = numeric(activity.uniqueTrackCount);
  const albums = numeric(activity.uniqueAlbumCount);
  const libraryCount = numeric(library.recordCount) || 0;
  const recentObservationCount =
    numeric(recent.observationCount) || 0;
  const recentSnapshotCount =
    numeric(recent.snapshotCount) || 0;
  const recentObservedDayCount =
    numeric(recent.observedDayCount) || 0;
  const recentUniqueEntityCount =
    numeric(recent.uniqueEntityCount) || 0;
  const recentTopItems = Array.isArray(recent.topItems)
    ? recent.topItems
    : [];

  const period =
    result?.period?.label ||
    [result?.request?.startDate, result?.request?.endDate]
      .filter(Boolean)
      .join(" to ") ||
    "the selected period";

  const findings = [];
  let answer;

  if (activity.status === "available" && plays > 0) {
    const sentences = [
      `You had ${formatNumber(plays)} confirmed ${plural(
        plays,
        "play"
      )} during ${period}${
        hours === null ? "" : `, totaling ${formatNumber(hours, 1)} hours`
      }.`,
    ];

    if (tracks !== null || albums !== null) {
      const breadth = [];

      if (tracks !== null) {
        breadth.push(
          `${formatNumber(tracks)} ${plural(tracks, "track")}`
        );
      }

      if (albums !== null) {
        breadth.push(
          `${formatNumber(albums)} ${plural(albums, "album")}`
        );
      }

      sentences.push(`Listening covered ${breadth.join(" across ")}.`);
    }

    if (activity.uniqueArtistCount == null) {
      sentences.push(
        "Artist identity was unavailable for confirmed play events."
      );
    }

    answer = sentences.slice(0, 3).join(" ");

    const volume = [
      `${formatNumber(plays)} confirmed ${plural(plays, "play")}`,
    ];

    if (hours !== null) {
      volume.push(`${formatNumber(hours, 1)} listening hours`);
    }

    if (tracks !== null) {
      volume.push(`${formatNumber(tracks)} unique ${plural(tracks, "track")}`);
    }

    if (albums !== null) {
      volume.push(`${formatNumber(albums)} unique ${plural(albums, "album")}`);
    }

    findings.push(volume.join(" · "));

    const outcomes = activity.playbackOutcomes || {};
    const outcomeItems = [];

    if (numeric(outcomes.naturalCompletions) !== null) {
      outcomeItems.push(
        `${formatNumber(outcomes.naturalCompletions)} natural completions`
      );
    }

    if (skips !== null) {
      outcomeItems.push(`${formatNumber(skips)} recorded forward skips`);
    }

    if (numeric(outcomes.manualTrackChanges) !== null) {
      outcomeItems.push(
        `${formatNumber(outcomes.manualTrackChanges)} manual track changes`
      );
    }

    if (outcomeItems.length) {
      findings.push(outcomeItems.join(" · "));
    }

    const topTracks = Array.isArray(activity.topTracks)
      ? activity.topTracks
      : [];

    if (topTracks.length) {
      const leadCount =
        numeric(topTracks[0]?.actualPlays ?? topTracks[0]?.plays) || 0;

      const tied = topTracks.filter(
        (item) =>
          numeric(item?.actualPlays ?? item?.plays) === leadCount
      );

      if (tied.length > 1) {
        findings.push(
          `${tied.length} tracks tied for the lead with ${formatNumber(
            leadCount
          )} confirmed ${plural(leadCount, "play")} each.`
        );
      } else {
        findings.push(
          `${topTracks[0]?.track || topTracks[0]?.song || "The leading track"} ` +
            `led with ${formatNumber(leadCount)} confirmed ${plural(
              leadCount,
              "play"
            )}.`
        );
      }
    }
  } else if (activity.status === "available" && plays === 0) {
    answer =
      `Actual Listening was searched for ${period} and returned no confirmed plays.`;

    answer +=
      libraryCount > 0
        ? ` Library Evidence returned ${formatNumber(
            libraryCount
          )} ${plural(libraryCount, "record")}.`
        : " Library Evidence was searched and returned no matching evidence.";
  } else if (activity.status === "unsupported_for_period") {
    const range =
      actualCoverage?.coverageStart && actualCoverage?.coverageEnd
        ? `${actualCoverage.coverageStart} through ${actualCoverage.coverageEnd}`
        : null;

    answer = range
      ? `Actual Listening does not cover ${period}. Its available range is ${range}.`
      : `Actual Listening does not cover ${period}.`;

    answer +=
      libraryCount > 0
        ? ` Library Evidence returned ${formatNumber(
            libraryCount
          )} ${plural(libraryCount, "record")}.`
        : " Library Evidence was searched and returned no matching evidence.";
  } else if (activity.status === "unavailable") {
    answer =
      `Actual Listening was unavailable for ${period}. ` +
      (libraryCount > 0
        ? `Library Evidence returned ${formatNumber(
            libraryCount
          )} ${plural(libraryCount, "record")}.`
        : "Library Evidence was searched independently.");
  } else {
    answer =
      result?.summary?.narrative ||
      result?.summary?.headline ||
      "The available evidence could not produce a supported answer.";
  }

  if (
    recentObservationCount > 0 &&
    !answer.includes("Recent Apple Objects")
  ) {
    answer +=
      ` Recent Apple Objects returned ${formatNumber(
        recentObservationCount
      )} observations across ${formatNumber(
        recentSnapshotCount
      )} ${plural(recentSnapshotCount, "snapshot")} on ${formatNumber(
        recentObservedDayCount
      )} observed calendar ${plural(recentObservedDayCount, "day")}. ` +
      "These are snapshot observations, not confirmed plays.";
  }

  if (!findings.length && libraryCount > 0) {
    findings.push(
      `${formatNumber(libraryCount)} Library Evidence ${plural(
        libraryCount,
        "record"
      )} matched the period.`
    );

    const topArtist = library?.topArtists?.[0];

    if (topArtist?.artist) {
      findings.push(
        `${topArtist.artist} led Library Evidence with ${formatNumber(
          topArtist.count
        )} ${plural(topArtist.count, "record")}.`
      );
    }

    const topAlbum = library?.topAlbums?.[0];

    if (topAlbum?.album) {
      findings.push(
        `${topAlbum.album} was the leading Library Evidence album with ` +
          `${formatNumber(topAlbum.count)} ${plural(
            topAlbum.count,
            "record"
          )}.`
      );
    }
  }

  if (recentObservationCount > 0) {
    findings.push(
      `${formatNumber(recentObservationCount)} Recent Apple ` +
        `${plural(recentObservationCount, "observation")} across ` +
        `${formatNumber(recentSnapshotCount)} ${plural(
          recentSnapshotCount,
          "snapshot"
        )} on ${formatNumber(recentObservedDayCount)} observed calendar ` +
        `${plural(recentObservedDayCount, "day")}.`
    );

    if (recentUniqueEntityCount > 0) {
      findings.push(
        `${formatNumber(recentUniqueEntityCount)} unique Apple ` +
          `${plural(recentUniqueEntityCount, "object")} appeared in ` +
          "the snapshot evidence."
      );
    }

    const leadRecentItem = recentTopItems[0];

    if (leadRecentItem?.name) {
      findings.push(
        `${leadRecentItem.name} appeared in ${formatNumber(
          leadRecentItem.snapshotCount
        )} ${plural(leadRecentItem.snapshotCount, "snapshot")}.`
      );
    }
  }

  const coverageText = coverage
    .map(
      (item) =>
        `${sourceLabel(item)}: ${statusLabel(item?.status)}.`
    )
    .join(" ");

  const level =
    result?.confidence?.level ||
    (activity.status === "available" ? "medium" : "low");

  const confidenceNotes = [];

  if (
    activity.status === "available" &&
    plays > 0 &&
    activity.uniqueArtistCount == null
  ) {
    confidenceNotes.push(
      "Artist identity is unavailable for Actual Listening."
    );
  }

  return {
    answer,
    findings: findings.slice(0, 3),
    confidenceLabel:
      level.charAt(0).toUpperCase() + level.slice(1),
    confidenceText: [coverageText, ...confidenceNotes]
      .filter(Boolean)
      .join(" "),
    actualCoverage,
  };
}

export default function DateRangeResult({ result }) {
  const presentation = buildPresentation(result);
  const activity = result?.activity || {};
  const library = result?.libraryEvidence || {};
  const recent = result?.recentAppleEvidence || {};
  const recentTopItems = Array.isArray(recent.topItems)
    ? recent.topItems
    : [];
  const recentObservedDays = Array.isArray(recent.observedDays)
    ? recent.observedDays
    : [];
  const coverage = Array.isArray(result?.coverage) ? result.coverage : [];
  const warnings = Array.isArray(result?.warnings) ? result.warnings : [];
  const provenance = Array.isArray(result?.provenance)
    ? result.provenance
    : [];
  const investigations = Array.isArray(result?.suggestedInvestigations)
    ? result.suggestedInvestigations
    : [];

  const facts = (Array.isArray(result?.facts) ? result.facts : []).filter(
    (fact) =>
      !(
        activity.status === "available" &&
        activity.actualPlays === 0 &&
        String(fact?.statement || "").includes("0 confirmed plays")
      )
  );

  const topTracks = Array.isArray(activity.topTracks)
    ? activity.topTracks
    : [];
  const topAlbums = Array.isArray(activity.topAlbums)
    ? activity.topAlbums
    : [];
  const libraryArtists = Array.isArray(library.topArtists)
    ? library.topArtists
    : [];
  const libraryAlbums = Array.isArray(library.topAlbums)
    ? library.topAlbums
    : [];
  const libraryRead = Array.isArray(library.memoryRead)
    ? library.memoryRead
    : [];

  const metrics = [
    ["Actual Plays", activity.actualPlays, 0],
    ["Forward Skips", activity.actualSkips, 0],
    ["Listening Hours", activity.listeningHours, 1],
    ["Unique Albums", activity.uniqueAlbumCount, 0],
    ["Unique Tracks", activity.uniqueTrackCount, 0],
  ];

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <p className="text-xs font-black uppercase tracking-[0.16em] text-blue-700 dark:text-blue-300">
          Date Range
        </p>
        <h3 className="mt-2 text-xl font-black">What Happened</h3>
        <p className="mt-3 max-w-4xl text-base leading-7 text-slate-700 dark:text-slate-200">
          {presentation.answer}
        </p>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
        <h3 className="text-base font-black">What Stood Out</h3>

        {presentation.findings.length ? (
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            {presentation.findings.map((finding, index) => (
              <div
                key={`${index}-${finding}`}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
              >
                {finding}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-slate-500">
            No additional evidence-backed findings were available.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-black">Confidence and Coverage</h3>
        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          <span className="font-black">
            Confidence: {presentation.confidenceLabel}.
          </span>{" "}
          {presentation.confidenceText}
        </p>
      </section>

      <details className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <summary className="cursor-pointer px-5 py-4 text-sm font-black">
          Show listening detail
        </summary>

        <div className="border-t border-slate-200 p-5 dark:border-slate-800">
          {activity.status === "available" ? (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                {metrics.map(([label, value, digits]) => (
                  <div
                    key={label}
                    className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900"
                  >
                    <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                      {label}
                    </p>
                    <p className="mt-1 text-lg font-black">
                      {formatNumber(value, digits)}
                    </p>
                  </div>
                ))}
              </div>

              {activity.playbackOutcomes ? (
                <div>
                  <h4 className="text-sm font-black">Playback Outcomes</h4>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-800">
                      Natural completions:{" "}
                      {formatNumber(
                        activity.playbackOutcomes.naturalCompletions
                      )}
                    </span>
                    <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-800">
                      Recorded forward skips:{" "}
                      {formatNumber(
                        activity.playbackOutcomes.recordedForwardSkips
                      )}
                    </span>
                    <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-800">
                      Manual track changes:{" "}
                      {formatNumber(
                        activity.playbackOutcomes.manualTrackChanges
                      )}
                    </span>
                  </div>
                </div>
              ) : null}

              {topTracks.length || topAlbums.length ? (
                <div className="grid gap-5 md:grid-cols-2">
                  {topTracks.length ? (
                    <div>
                      <h4 className="text-sm font-black">
                        Top Tracks by Actual Plays
                      </h4>
                      <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                        {topTracks.slice(0, 5).map((item, index) => (
                          <li key={`${item.track || item.song}-${index}`}>
                            <span className="font-semibold">
                              {item.track || item.song}
                            </span>{" "}
                            ({formatNumber(
                              item.actualPlays ?? item.plays
                            )}{" "}
                            {plural(
                              item.actualPlays ?? item.plays,
                              "play"
                            )})
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : null}

                  {topAlbums.length ? (
                    <div>
                      <h4 className="text-sm font-black">
                        Top Albums by Actual Plays
                      </h4>
                      <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                        {topAlbums.slice(0, 5).map((item, index) => (
                          <li key={`${item.album}-${index}`}>
                            <span className="font-semibold">
                              {item.album}
                            </span>{" "}
                            ({formatNumber(
                              item.actualPlays ?? item.plays
                            )}{" "}
                            {plural(
                              item.actualPlays ?? item.plays,
                              "play"
                            )})
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : null}
                </div>
              ) : null}

              {activity.sourceNote ? (
                <p className="text-xs leading-5 text-slate-500">
                  {activity.sourceNote}
                </p>
              ) : null}
            </div>
          ) : (
            <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <p className="font-black">
                {statusLabel(activity.status)}
              </p>
              {presentation.actualCoverage?.coverageStart &&
              presentation.actualCoverage?.coverageEnd ? (
                <p>
                  Available range:{" "}
                  {presentation.actualCoverage.coverageStart} through{" "}
                  {presentation.actualCoverage.coverageEnd}
                </p>
              ) : null}
            </div>
          )}
        </div>
      </details>

      <details className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <summary className="cursor-pointer px-5 py-4 text-sm font-black">
          Show evidence and sources
        </summary>

        <div className="space-y-6 border-t border-slate-200 p-5 dark:border-slate-800">
          <section>
            <h4 className="text-sm font-black">Source Coverage</h4>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {coverage.map((item) => (
                <div
                  key={item.sourceId}
                  className="rounded-xl border border-slate-200 p-4 dark:border-slate-800"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-black">{sourceLabel(item)}</p>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold dark:bg-slate-900">
                      {statusLabel(item.status)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Matched records:{" "}
                    {item.recordsMatched == null
                      ? "Not applicable"
                      : formatNumber(item.recordsMatched)}
                  </p>
                  {item.limitations?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-500">
                      {item.limitations.map((limitation) => (
                        <li key={limitation}>{limitation}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ))}
            </div>
          </section>

          {warnings.length ? (
            <section>
              <h4 className="text-sm font-black">Coverage Warnings</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {warnings.map((warning, index) => (
                  <li key={`${warning.code}-${index}`}>
                    {warning.message}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section>
            <h4 className="text-sm font-black">Library Evidence</h4>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {formatNumber(library.recordCount)}{" "}
              {plural(library.recordCount, "record")} matched. Library
              Evidence is Last Played Date reconstruction, not confirmed
              play history.
            </p>

            {libraryRead.length ? (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
                {libraryRead.map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ul>
            ) : null}

            {libraryArtists.length || libraryAlbums.length ? (
              <div className="mt-4 grid gap-5 md:grid-cols-2">
                {libraryArtists.length ? (
                  <div>
                    <h5 className="text-sm font-black">
                      Top Artists by Library Evidence
                    </h5>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                      {libraryArtists.slice(0, 5).map((item) => (
                        <li key={item.artist}>
                          {item.artist} ({formatNumber(item.count)}{" "}
                          {plural(item.count, "record")})
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {libraryAlbums.length ? (
                  <div>
                    <h5 className="text-sm font-black">
                      Top Albums by Library Evidence
                    </h5>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                      {libraryAlbums.slice(0, 5).map((item) => (
                        <li key={item.album}>
                          {item.album} ({formatNumber(item.count)}{" "}
                          {plural(item.count, "record")})
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </section>

          {recent.status === "available" ? (
            <section>
              <h4 className="text-sm font-black">
                Recent Apple Evidence
              </h4>

              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                These are captured Apple snapshot observations, not confirmed
                plays or complete listening history.
              </p>

              <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  ["Source Observations", recent.observationCount],
                  ["Snapshots", recent.snapshotCount],
                  ["Observed Days", recent.observedDayCount],
                  ["Unique Objects", recent.uniqueEntityCount],
                ].map(([label, value]) => (
                  <div
                    key={label}
                    className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900"
                  >
                    <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                      {label}
                    </p>
                    <p className="mt-1 text-lg font-black">
                      {formatNumber(value)}
                    </p>
                  </div>
                ))}
              </div>

              {numeric(recent.entitySnapshotObservationCount) !== null ? (
                <p className="mt-3 text-xs text-slate-500">
                  Distinct entity-snapshot observations:{" "}
                  {formatNumber(recent.entitySnapshotObservationCount)}
                </p>
              ) : null}

              {recentObservedDays.length ? (
                <p className="mt-2 text-xs text-slate-500">
                  Observed calendar days: {recentObservedDays.join(", ")}
                </p>
              ) : null}

              {recentTopItems.length ? (
                <div className="mt-4">
                  <h5 className="text-sm font-black">
                    Leading Observed Objects
                  </h5>

                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {recentTopItems.slice(0, 5).map((item, index) => (
                      <li
                        key={`${item.entityType}-${item.name}-${index}`}
                      >
                        {item.artist ? `${item.artist} — ` : ""}
                        {item.name} appeared in{" "}
                        {formatNumber(item.snapshotCount)}{" "}
                        {plural(item.snapshotCount, "snapshot")} (
                        {formatNumber(item.observationCount)} source{" "}
                        {plural(item.observationCount, "observation")})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {recent.sourceNote ? (
                <p className="mt-3 text-xs leading-5 text-slate-500">
                  {recent.sourceNote}
                </p>
              ) : null}
            </section>
          ) : null}

          {facts.length ? (
            <section>
              <h4 className="text-sm font-black">Investigation Facts</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {facts.map((fact, index) => (
                  <li key={fact.id || `${index}-${fact.statement}`}>
                    {fact.statement}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {investigations.length ? (
            <section>
              <h4 className="text-sm font-black">
                Suggested Investigations
              </h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {investigations.map((item, index) => (
                  <li key={`${index}-${item.label}`}>
                    {item.label}
                    {item.reason ? ` — ${item.reason}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {provenance.length ? (
            <section>
              <h4 className="text-sm font-black">Provenance</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-500">
                {provenance.map((item, index) => (
                  <li
                    key={item.evidenceId || item.sourceId || index}
                  >
                    {item.sourceLabel || item.sourceId || "Unknown source"}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <p className="border-t border-slate-200 pt-4 text-xs text-slate-500 dark:border-slate-800">
            Response schema: {result.schemaVersion || "unknown"}
          </p>
        </div>
      </details>
    </div>
  );
}
