import * as fs from "node:fs";
import * as path from "node:path";

const SERIES_ID =
  /^league-(\d+)-team-(\d+)-games-(\d+(?:-\d+)*)$/;

const CAPTURE_ORDER = [
  "NOT_CAPTURED",
  "CAPTURED",
  "PARSED",
  "REVIEW_READY",
];

class SeriesReplayError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.name = "SeriesReplayError";
    this.statusCode = statusCode;
  }
}

const clone = (value) =>
  value === undefined
    ? undefined
    : JSON.parse(JSON.stringify(value));

const utcNow = () => new Date().toISOString();

function validateIdentity(leagueId, teamId, seriesId) {
  const league = String(leagueId);
  const team = String(teamId);
  const id = String(seriesId);

  if (!/^\d+$/.test(league)) {
    throw new SeriesReplayError(400, "Invalid league ID");
  }

  if (!/^\d+$/.test(team)) {
    throw new SeriesReplayError(400, "Invalid team ID");
  }

  const match = id.match(SERIES_ID);

  if (!match) {
    throw new SeriesReplayError(400, "Invalid BIE series ID");
  }

  if (match[1] !== league || match[2] !== team) {
    throw new SeriesReplayError(
      400,
      "Series ID does not match route identity"
    );
  }
}

function loadCanonicalSeriesArtifact(
  repoRoot,
  leagueId,
  teamId,
  seriesId
) {
  validateIdentity(leagueId, teamId, seriesId);

  const seriesFile = path.join(
    repoRoot,
    "data",
    "baseball",
    "state",
    "strat365",
    "series-v1",
    `league-${leagueId}`,
    `team-${teamId}`,
    seriesId,
    "series-v1.json"
  );

  let raw;

  try {
    raw = fs.readFileSync(seriesFile, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") {
      throw new SeriesReplayError(
        404,
        "BIE series artifact unavailable"
      );
    }
    throw error;
  }

  const payload = JSON.parse(raw);
  const identity = payload?.seriesIdentity;

  if (
    !identity ||
    String(identity.seriesId) !== String(seriesId) ||
    String(identity.leagueId) !== String(leagueId) ||
    String(identity.teamId) !== String(teamId)
  ) {
    throw new SeriesReplayError(
      409,
      "Persisted BIE series identity mismatch"
    );
  }

  return { seriesFile, payload };
}

function writeCanonicalSeriesArtifact(seriesFile, payload) {
  const tempFile =
    `${seriesFile}.tmp-${process.pid}-${Date.now()}`;

  fs.writeFileSync(
    tempFile,
    `${JSON.stringify(payload, null, 2)}\n`,
    "utf8"
  );

  try {
    fs.renameSync(tempFile, seriesFile);
  } catch (error) {
    if (!["EPERM", "EEXIST"].includes(error?.code)) {
      throw error;
    }

    fs.copyFileSync(tempFile, seriesFile);
    fs.unlinkSync(tempFile);
  } finally {
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile);
    }
  }
}

function requireGame(series, ordinalValue) {
  const ordinal = Number(ordinalValue);

  if (!Number.isInteger(ordinal) || ordinal < 1) {
    throw new SeriesReplayError(
      400,
      "Invalid series game ordinal"
    );
  }

  const games = series?.replay?.games;

  if (!Array.isArray(games)) {
    throw new SeriesReplayError(
      409,
      "Persisted replay contract is invalid"
    );
  }

  const game = games.find(
    (candidate) => Number(candidate?.ordinal) === ordinal
  );

  if (!game) {
    throw new SeriesReplayError(
      404,
      "Series game ordinal not found"
    );
  }

  return { ordinal, games, game };
}

function snapshotSignature(series) {
  return JSON.stringify(series?.preSeriesSnapshot);
}

function assertSnapshot(signature, series) {
  if (snapshotSignature(series) !== signature) {
    throw new SeriesReplayError(
      409,
      "Immutable pre-series snapshot mutation blocked"
    );
  }
}

function recomputeCapture(series) {
  const games = series?.replay?.games || [];

  const statuses = games.map(
    (game) => game?.captureState?.status || "NOT_CAPTURED"
  );

  const ready = statuses.filter(
    (status) => status === "REVIEW_READY"
  ).length;

  if (statuses.every((status) => status === "NOT_CAPTURED")) {
    series.replay.status = "NOT_CAPTURED";
  } else if (games.length > 0 && ready === games.length) {
    series.replay.status = "AVAILABLE";
  } else {
    series.replay.status = "PARTIAL";
  }

  if (series.lifecycle) {
    series.lifecycle.replayAvailable =
      games[0]?.captureState?.status === "REVIEW_READY";

    series.lifecycle.completedGameCount = ready;
  }
}

function transitionCaptureState(
  source,
  ordinalValue,
  request = {}
) {
  const signature = snapshotSignature(source);
  const series = clone(source);
  const { game } = requireGame(series, ordinalValue);

  const current =
    game?.captureState?.status || "NOT_CAPTURED";

  const next = String(request.status || "")
    .trim()
    .toUpperCase();

  const currentIndex = CAPTURE_ORDER.indexOf(current);
  const nextIndex = CAPTURE_ORDER.indexOf(next);

  if (nextIndex < 0) {
    throw new SeriesReplayError(
      400,
      "Invalid capture state"
    );
  }

  if (currentIndex < 0 || nextIndex < currentIndex) {
    throw new SeriesReplayError(
      409,
      "Capture state cannot regress"
    );
  }

  const timestamp = utcNow();

  game.captureState.status = next;

  if (nextIndex >= 1 && !game.captureState.capturedAtUtc) {
    game.captureState.capturedAtUtc =
      request.capturedAtUtc || timestamp;
  }

  if (nextIndex >= 2 && !game.captureState.parsedAtUtc) {
    game.captureState.parsedAtUtc =
      request.parsedAtUtc || timestamp;
  }

  if (nextIndex >= 3 && !game.captureState.reviewReadyAtUtc) {
    game.captureState.reviewReadyAtUtc =
      request.reviewReadyAtUtc || timestamp;
  }

  if (
    Object.prototype.hasOwnProperty.call(request, "gameId")
  ) {
    game.gameId =
      request.gameId == null
        ? null
        : String(request.gameId);
  }

  if (Array.isArray(request.sourceEvidence)) {
    game.captureState.sourceEvidence =
      clone(request.sourceEvidence);
  }

  game.evidenceStatus = next;

  recomputeCapture(series);
  assertSnapshot(signature, series);

  return series;
}

function previousRevealed(games, ordinal) {
  if (ordinal === 1) {
    return true;
  }

  const previous = games.find(
    (game) => Number(game?.ordinal) === ordinal - 1
  );

  return previous?.revealState?.status === "REVEALED";
}

function requireRevealReady(game, games, ordinal) {
  if (game?.captureState?.status !== "REVIEW_READY") {
    throw new SeriesReplayError(
      409,
      "Game is not review ready"
    );
  }

  if (!previousRevealed(games, ordinal)) {
    throw new SeriesReplayError(
      409,
      "Prior series game must be revealed first"
    );
  }
}

function boundary(value, label) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return null;
  }

  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new SeriesReplayError(
      400,
      `Invalid ${label}`
    );
  }

  return parsed;
}

function transitionRevealState(
  source,
  ordinalValue,
  request = {}
) {
  const signature = snapshotSignature(source);
  const series = clone(source);

  const { ordinal, games, game } =
    requireGame(series, ordinalValue);

  const action = String(request.action || "")
    .trim()
    .toLowerCase();

  const current =
    game?.revealState?.status || "LOCKED";

  const timestamp = utcNow();

  if (action === "unlock") {
    if (current !== "LOCKED") {
      throw new SeriesReplayError(
        409,
        "Only a locked game may be unlocked"
      );
    }

    requireRevealReady(game, games, ordinal);

    game.revealState.status = "UNVIEWED";
    game.reviewState.status = "REPLAY_READY";
  } else if (action === "begin") {
    if (current !== "UNVIEWED") {
      throw new SeriesReplayError(
        409,
        "Game must be unlocked before replay begins"
      );
    }

    requireRevealReady(game, games, ordinal);

    game.revealState.status = "IN_PROGRESS";
    game.revealState.startedAtUtc =
      game.revealState.startedAtUtc || timestamp;

    game.reviewState.status = "IN_PROGRESS";
  } else if (action === "advance") {
    if (current !== "IN_PROGRESS") {
      throw new SeriesReplayError(
        409,
        "Replay must be in progress before advancing"
      );
    }

    const eventSequence =
      boundary(request.eventSequence, "event sequence");

    const inning =
      boundary(request.inning, "inning");

    if (eventSequence === null && inning === null) {
      throw new SeriesReplayError(
        400,
        "Replay advance requires an event or inning boundary"
      );
    }

    const priorSequence =
      game.revealState.revealedThroughEventSequence;

    const priorInning =
      game.revealState.revealedThroughInning;

    if (
      eventSequence !== null &&
      priorSequence !== null &&
      eventSequence < priorSequence
    ) {
      throw new SeriesReplayError(
        409,
        "Reveal event boundary cannot regress"
      );
    }

    if (
      inning !== null &&
      priorInning !== null &&
      inning < priorInning
    ) {
      throw new SeriesReplayError(
        409,
        "Reveal inning boundary cannot regress"
      );
    }

    if (eventSequence !== null) {
      game.revealState.revealedThroughEventSequence =
        eventSequence;

      game.reviewState.spoilerSafeThroughEventSequence =
        eventSequence;
    }

    if (inning !== null) {
      game.revealState.revealedThroughInning = inning;
    }
  } else if (action === "complete") {
    if (current !== "IN_PROGRESS") {
      throw new SeriesReplayError(
        409,
        "Replay must be in progress before completion"
      );
    }

    const replayEvents = Array.isArray(game.events)
      ? game.events
      : Array.isArray(game.playByPlay)
        ? game.playByPlay
        : [];

    const finalEventSequence = replayEvents.reduce(
      (highest, event) => {
        const sequence = eventSequence(event);

        return sequence == null
          ? highest
          : Math.max(highest, sequence);
      },
      0
    );

    const revealedThrough =
      game.revealState.revealedThroughEventSequence;

    if (
      finalEventSequence < 1 ||
      revealedThrough == null ||
      revealedThrough < finalEventSequence
    ) {
      throw new SeriesReplayError(
        409,
        "Final replay event must be deliberately revealed before completion"
      );
    }

    game.revealState.status = "REVEALED";
    game.revealState.completedAtUtc = timestamp;

    game.reviewState.status = "POSTGAME_READY";
    game.reviewState.postgameAvailable = true;
  } else {
    throw new SeriesReplayError(
      400,
      "Invalid reveal-state action"
    );
  }

  assertSnapshot(signature, series);

  return series;
}

function transitionReviewState(
  source,
  ordinalValue,
  request = {}
) {
  const signature = snapshotSignature(source);
  const series = clone(source);
  const { game } = requireGame(series, ordinalValue);

  const action = String(request.action || "")
    .trim()
    .toLowerCase();

  if (action !== "complete") {
    throw new SeriesReplayError(
      400,
      "Invalid review-state action"
    );
  }

  if (
    game?.revealState?.status !== "REVEALED" ||
    game?.reviewState?.status !== "POSTGAME_READY"
  ) {
    throw new SeriesReplayError(
      409,
      "Postgame review is not eligible for completion"
    );
  }

  game.reviewState.status = "COMPLETE";
  game.reviewState.completedAtUtc = utcNow();

  assertSnapshot(signature, series);

  return series;
}

function eventSequence(event) {
  for (const key of [
    "eventSequence",
    "sequence",
    "ordinal",
  ]) {
    const value = Number(event?.[key]);

    if (Number.isFinite(value)) {
      return value;
    }
  }

  return null;
}

function filterEvents(events, revealState) {
  if (!Array.isArray(events)) {
    return undefined;
  }

  const sequenceBoundary =
    revealState?.revealedThroughEventSequence;

  const inningBoundary =
    revealState?.revealedThroughInning;

  if (sequenceBoundary != null) {
    return events.filter(
      (event) => {
        const sequence = eventSequence(event);

        return (
          sequence != null &&
          sequence <= sequenceBoundary
        );
      }
    );
  }

  if (inningBoundary != null) {
    return events.filter(
      (event) => {
        const inning = Number(event?.inning);

        return (
          Number.isFinite(inning) &&
          inning <= inningBoundary
        );
      }
    );
  }

  return [];
}

function stateOnly(game) {
  return {
    ordinal: game.ordinal,
    scheduleGameNumber: game.scheduleGameNumber,
    gameId:
      game?.revealState?.status === "LOCKED"
        ? null
        : game.gameId ?? null,
    evidenceStatus: game.evidenceStatus,
    captureState: {
      status:
        game?.captureState?.status || "NOT_CAPTURED",
    },
    revealState: clone(game.revealState),
    reviewState: clone(game.reviewState),
  };
}

function redactGame(game) {
  const status =
    game?.revealState?.status || "LOCKED";

  if (status === "REVEALED") {
    return clone(game);
  }

  const safe = stateOnly(game);

  if (status !== "IN_PROGRESS") {
    return safe;
  }

  const events =
    filterEvents(game.events, game.revealState);

  const playByPlay =
    filterEvents(game.playByPlay, game.revealState);

  if (events !== undefined) {
    safe.events = clone(events);
  }

  if (playByPlay !== undefined) {
    safe.playByPlay = clone(playByPlay);
  }

  return safe;
}

function redactSeriesForClient(source) {
  const series = clone(source);

  const games =
    Array.isArray(series?.replay?.games)
      ? series.replay.games
      : [];

  const revealedCount =
    games.filter(
      (game) =>
        game?.revealState?.status === "REVEALED"
    ).length;

  const allRevealed =
    games.length > 0 &&
    revealedCount === games.length;

  const replayReady =
    games[0]?.captureState?.status === "REVIEW_READY";

  const inProgress =
    games.some(
      (game) =>
        game?.revealState?.status === "IN_PROGRESS"
    );

  series.replay.games =
    games.map(redactGame);

  series.replay.status =
    allRevealed
      ? "REVEALED"
      : inProgress
        ? "IN_PROGRESS"
        : replayReady
          ? "REVIEW_READY"
          : "NOT_CAPTURED";

  if (series.lifecycle) {
    series.lifecycle.completedGameCount =
      revealedCount;

    series.lifecycle.replayAvailable =
      replayReady;

    series.lifecycle.reviewAvailable =
      allRevealed &&
      series?.review?.status !== "NOT_CAPTURED";

    series.lifecycle.learningAvailable =
      allRevealed &&
      series?.learning?.status !== "NOT_CAPTURED";
  }

  if (!allRevealed) {
    series.review = {
      status: "LOCKED",
      artifact: null,
    };

    series.learning = {
      status: "LOCKED",
      artifact: null,
    };
  }

  return series;
}

export {
  SeriesReplayError,
  loadCanonicalSeriesArtifact,
  writeCanonicalSeriesArtifact,
  redactSeriesForClient,
  transitionCaptureState,
  transitionRevealState,
  transitionReviewState,
};
