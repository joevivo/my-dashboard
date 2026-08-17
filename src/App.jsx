import React, { useEffect, useState } from "react";

import AppleMusicAnalytics from "./AppleMusicAnalytics";

import CalendarView from "./CalendarView";

import LineupAnalyzer from "./LineupAnalyzer";

import PitchingAnalyzer from "./PitchingAnalyzer";

import MatchupAnalyzer from "./MatchupAnalyzer";

import FinanceView from "./FinanceView";

import SeriesPlanner from "./SeriesPlanner";
import SeriesPreview from "./SeriesPreview";
import { getStratTeamIdentity } from "./strat/teamIdentityRegistry";

import GameSimulator from "./GameSimulator";

import LeagueManager from "./LeagueManager";

import OpponentManager from "./OpponentManager";

import WeatherBug from "./WeatherBug";

import NewsView from "./NewsView";


import MusicLibrary from "./MusicLibrary";

import MusicTimeMachine from "./music/components/MusicTimeMachine";
import MusicDashboard from "./MusicDashboard";

import BooksView from "./BooksView";

import NotesView from "./NotesView";

import QueryWorkbench from "./QueryWorkbench";

import ArtistIntelligence from "./ArtistIntelligence";

import PlaylistIntelligence from "./PlaylistIntelligence";

import ScrollToTopButton from "./ScrollToTopButton";


const ACTIVE_STRAT_TEAMS = [
  {
    teamId: "1851052",
    leagueId: "479336",
    teamName: "Aquarium Drinkers",
    season: "1968",
    teamUrl: "https://365.strat-o-matic.com/team/1851052",
    scheduleUrl: "https://365.strat-o-matic.com/team/schedule/1851052",
    bie: {
      phase: "ACTIVE_SEASON",
    },
  },
  {
    teamId: "1853975",
    leagueId: "479431",
    teamName: "Aquarium Drinkers",
    season: "1968",
    teamUrl: "https://365.strat-o-matic.com/team/1853975",
    scheduleUrl: "https://365.strat-o-matic.com/team/schedule/1853975",
    bie: {
      phase: "ACTIVE_SEASON",
    },
  },
  {
    teamId: "1854215",
    leagueId: "479610",
    teamName: "Aquarium Drinkers",
    season: "1968",
    teamUrl: "https://365.strat-o-matic.com/team/1854215",
    scheduleUrl: "https://365.strat-o-matic.com/team/schedule/1854215",
    bie: {
      phase: "ACTIVE_SEASON",
    },
  },
];

function formatOrdinal(value) {
  const number = Number(value);

  if (!Number.isFinite(number) || number < 1) {
    return "—";
  }

  const mod100 = number % 100;

  if (mod100 >= 11 && mod100 <= 13) {
    return `${number}th`;
  }

  if (number % 10 === 1) {
    return `${number}st`;
  }

  if (number % 10 === 2) {
    return `${number}nd`;
  }

  if (number % 10 === 3) {
    return `${number}rd`;
  }

  return `${number}th`;
}

function parseRecordValue(record) {
  const match = String(record || "").match(/^(\d+)-(\d+)$/);

  if (!match) {
    return null;
  }

  const wins = Number(match[1]);
  const losses = Number(match[2]);
  const games = wins + losses;

  if (!games) {
    return null;
  }

  return {
    wins,
    losses,
    pct: wins / games,
  };
}

function parseRunDiff(value) {
  const parsed = Number.parseInt(
    String(value || "").replace("+", ""),
    10
  );

  return Number.isFinite(parsed) ? parsed : null;
}

function parseLast10(value) {
  return parseRecordValue(value);
}

function buildSeriesRead({
  isPreseason,
  homeAway,
  teamStanding,
  opponentStanding,
}) {
  if (isPreseason) {
    return {
      label: "Preseason",
      tone: "neutral",
      summary:
        "No performance read yet. Opening Day will establish the first competitive evidence.",
    };
  }

  if (!teamStanding || !opponentStanding) {
    return {
      label: "Evidence incomplete",
      tone: "neutral",
      summary:
        "Current standings evidence is not complete enough for a series read.",
    };
  }

  const teamRecord = parseRecordValue(
    `${teamStanding.wins}-${teamStanding.losses}`
  );

  const opponentRecord = parseRecordValue(
    `${opponentStanding.wins}-${opponentStanding.losses}`
  );

  const teamDiff = parseRunDiff(
    teamStanding.runDifferential
  );

  const opponentDiff = parseRunDiff(
    opponentStanding.runDifferential
  );

  const teamForm = parseLast10(teamStanding.last10);
  const opponentForm = parseLast10(
    opponentStanding.last10
  );

  let score = 0;
  const evidence = [];

  if (teamRecord && opponentRecord) {
    const pctGap =
      teamRecord.pct - opponentRecord.pct;

    if (pctGap >= 0.08) {
      score += 2;
      evidence.push("better overall record");
    } else if (pctGap <= -0.08) {
      score -= 2;
      evidence.push("opponent owns the better overall record");
    } else {
      evidence.push("overall records are relatively close");
    }
  }

  if (
    teamDiff !== null &&
    opponentDiff !== null
  ) {
    const diffGap = teamDiff - opponentDiff;

    if (diffGap >= 15) {
      score += 2;
      evidence.push("stronger run differential");
    } else if (diffGap <= -15) {
      score -= 2;
      evidence.push("opponent has the stronger run differential");
    }
  }

  if (teamForm && opponentForm) {
    const formGap =
      teamForm.pct - opponentForm.pct;

    if (formGap >= 0.2) {
      score += 1;
      evidence.push("better recent form");
    } else if (formGap <= -0.2) {
      score -= 1;
      evidence.push("opponent has better recent form");
    }
  }

  const teamVenue = parseRecordValue(
    homeAway === "Away"
      ? teamStanding.roadRecord
      : teamStanding.homeRecord
  );

  const opponentVenue = parseRecordValue(
    homeAway === "Away"
      ? opponentStanding.homeRecord
      : opponentStanding.roadRecord
  );

  if (teamVenue && opponentVenue) {
    const venueGap =
      teamVenue.pct - opponentVenue.pct;

    if (venueGap >= 0.12) {
      score += 2;
      evidence.push("venue split favors Aquarium Drinkers");
    } else if (venueGap <= -0.12) {
      score -= 2;
      evidence.push("venue split favors the opponent");
    } else {
      evidence.push("venue records are broadly comparable");
    }
  }

  let label = "Balanced matchup";
  let tone = "neutral";

  if (score >= 4) {
    label = "Contextual edge";
    tone = "positive";
  } else if (score >= 2) {
    label = "Slight contextual edge";
    tone = "positive";
  } else if (score <= -4) {
    label = "Challenging context";
    tone = "warning";
  } else if (score <= -2) {
    label = "Slight contextual disadvantage";
    tone = "warning";
  }

  return {
    label,
    tone,
    summary:
      evidence.length > 0
        ? evidence.slice(0, 3).join(" · ")
        : "No meaningful statistical separation detected.",
  };
}

function formatRotationPitcher(value) {
  const parts = String(value || "")
    .split(",")
    .map((part) => part.trim());

  return parts.length >= 2
    ? `${parts.slice(1).join(" ")} ${parts[0]}`
    : value || "—";
}

function rotationConfidenceClasses(value) {
  if (value === "HIGH") {
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300";
  }

  if (value === "MEDIUM") {
    return "bg-cyan-100 text-cyan-800 dark:bg-cyan-950/50 dark:text-cyan-300";
  }

  if (value === "LOW") {
    return "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300";
  }

  return "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400";
}


function starterNameIdentity(value) {
  const raw = String(value || "")
    .replace(/\([^)]*\)/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  if (!raw) {
    return null;
  }

  let firstPart = "";
  let surnamePart = "";

  if (raw.includes(",")) {
    const [surname, given = ""] =
      raw.split(",", 2);

    surnamePart = surname.trim();
    firstPart = given.trim();
  } else {
    const parts = raw
      .split(/\s+/)
      .filter(Boolean);

    surnamePart =
      parts[parts.length - 1] || "";

    firstPart =
      parts[0] || "";
  }

  const normalize = (part) =>
    String(part || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "");

  const surname =
    normalize(surnamePart);

  const first =
    normalize(firstPart);

  const full =
    normalize(raw.includes(",")
      ? `${firstPart} ${surnamePart}`
      : raw);

  return {
    full,
    surname,
    firstInitial:
      first.slice(0, 1),
  };
}

function findProjectedStarterRosterRow(
  liveTeam,
  projectedPitcher,
) {
  const target =
    starterNameIdentity(
      projectedPitcher,
    );

  const pitchers =
    Array.isArray(liveTeam?.pitchers)
      ? liveTeam.pitchers
      : [];

  if (
    !target ||
    !target.surname ||
    !pitchers.length
  ) {
    return null;
  }

  const candidates =
    pitchers.map((pitcher) => ({
      pitcher,
      identity:
        starterNameIdentity(
          pitcher?.name,
        ),
    }));

  const exact =
    candidates.find(
      ({ identity }) =>
        identity?.full &&
        identity.full === target.full,
    );

  if (exact) {
    return exact.pitcher;
  }

  const surnameAndInitial =
    candidates.filter(
      ({ identity }) =>
        identity?.surname ===
          target.surname &&
        identity?.firstInitial ===
          target.firstInitial,
    );

  if (
    surnameAndInitial.length === 1
  ) {
    return surnameAndInitial[0]
      .pitcher;
  }

  const surnameOnly =
    candidates.filter(
      ({ identity }) =>
        identity?.surname ===
        target.surname,
    );

  return surnameOnly.length === 1
    ? surnameOnly[0].pitcher
    : null;
}

function formatStarterThrowingHand(value) {
  const hand = String(value || "")
    .trim()
    .toUpperCase();

  if (hand === "L") {
    return "LHP";
  }

  if (hand === "R") {
    return "RHP";
  }

  return hand || "—";
}

function formatStarterRecord(row) {
  const wins = String(
    row?.wins ?? "",
  ).trim();

  const losses = String(
    row?.losses ?? "",
  ).trim();

  if (!wins && !losses) {
    return "—";
  }

  return `${wins || "0"}-${losses || "0"}`;
}

function formatStarterStat(
  value,
  digits,
) {
  if (
    value == null ||
    String(value).trim() === ""
  ) {
    return "—";
  }

  const numeric = Number(value);

  if (!Number.isFinite(numeric)) {
    return String(value).trim();
  }

  return numeric.toFixed(digits);
}

function formatStarterKbb(row) {
  const strikeouts = Number(
    row?.strikeouts,
  );

  const walks = Number(
    row?.walksAllowed,
  );

  if (
    !Number.isFinite(strikeouts) ||
    !Number.isFinite(walks)
  ) {
    return "—";
  }

  if (walks === 0) {
    return strikeouts > 0
      ? "∞"
      : "—";
  }

  return (
    strikeouts / walks
  ).toFixed(2);
}

function formatStarterHold(value) {
  const raw = String(value || "")
    .trim();

  if (!raw) {
    return "Hold —";
  }

  if (/^hold\b/i.test(raw)) {
    return raw;
  }

  return `Hold ${raw}`;
}

export default function App() {

  const [activeView, setActiveView] = useState("StratHome");
  const [selectedSeriesPreview, setSelectedSeriesPreview] = useState(null);

  const [selectedArtistForIntelligence, setSelectedArtistForIntelligence] = useState("Billie Holiday");

  const [queryWorkbenchArtist, setQueryWorkbenchArtist] = useState("");
  const [stratTeamData, setStratTeamData] = useState({});
  const [stratTeamStatus, setStratTeamStatus] = useState({});
  const [stratLeagueData, setStratLeagueData] = useState({});
  const [stratLeagueStatus, setStratLeagueStatus] = useState({});
  const [stratRotationData, setStratRotationData] = useState({});
  const [stratRotationStatus, setStratRotationStatus] = useState({});
  const [stratCurrentPreviewData, setStratCurrentPreviewData] = useState({});
  const [stratCurrentPreviewStatus, setStratCurrentPreviewStatus] = useState({});
  const [stratActionMessage, setStratActionMessage] = useState("");


  const [queryWorkbenchSource, setQueryWorkbenchSource] = useState("");

  const [theme, setTheme] = useState(() => {

    return localStorage.getItem("dashboardTheme") || "light";

  });



  const isDark = theme === "dark";



  useEffect(() => {

    localStorage.setItem("dashboardTheme", theme);

    document.documentElement.classList.toggle("dark", isDark);

  }, [theme, isDark]);



  const toggleTheme = () => {

    setTheme((current) => (current === "dark" ? "light" : "dark"));

  };


  const refreshStratTeam = async (teamId) => {
    setStratTeamStatus((current) => ({
      ...current,
      [teamId]: "loading",
    }));

    try {
      const response = await fetch(
        `http://localhost:4000/api/strat/team/${teamId}`
      );

      if (!response.ok) {
        throw new Error(`Team refresh failed: ${response.status}`);
      }

      const payload = await response.json();

      setStratTeamData((current) => ({
        ...current,
        [teamId]: payload,
      }));

      setStratTeamStatus((current) => ({
        ...current,
        [teamId]: "ready",
      }));
    } catch (error) {
      console.error("Active team refresh failed:", teamId, error);

      setStratTeamStatus((current) => ({
        ...current,
        [teamId]: "error",
      }));
    }
  };

  const refreshStratTeamAndOpponent = async (team) => {
    refreshStratTeam(team.teamId);

    const rotation =
      await refreshStratRotation(
        team.leagueId,
        team.teamId
      );

    const opponentTeamId =
      rotation?.currentSeries?.opponentTeamId ||
      null;

    if (opponentTeamId) {
      refreshStratTeam(opponentTeamId);

      refreshStratRotation(
        team.leagueId,
        opponentTeamId
      );
    }

    return rotation;
  };
  const refreshStratCurrentPreview = async (team) => {
    const key = `${team.leagueId}:${team.teamId}`;

    setStratCurrentPreviewStatus((current) => ({
      ...current,
      [key]: "loading",
    }));

    try {
      const response = await fetch(
        `http://localhost:4000/api/strat/league/${team.leagueId}/team/${team.teamId}/series-preview/current`
      );

      if (!response.ok) {
        throw new Error(
          `Current Series Preview fetch failed: ${response.status}`
        );
      }

      const payload = await response.json();

      setStratCurrentPreviewData((current) => ({
        ...current,
        [key]: payload,
      }));

      setStratCurrentPreviewStatus((current) => ({
        ...current,
        [key]: "ready",
      }));

      const opponentTeamId =
        payload?.seriesIdentity?.opponentTeamId || null;

      if (opponentTeamId) {
        await refreshStratTeam(opponentTeamId);

        void refreshStratRotation(
          team.leagueId,
          opponentTeamId
        );
      }

      return payload;
    } catch (error) {
      console.error(
        "Current BIE Series Preview refresh failed",
        error
      );

      setStratCurrentPreviewData((current) => ({
        ...current,
        [key]: null,
      }));

      setStratCurrentPreviewStatus((current) => ({
        ...current,
        [key]: "error",
      }));

      return null;
    }
  };
  const refreshStratLeague = async (leagueId) => {
    setStratLeagueStatus((current) => ({
      ...current,
      [leagueId]: "loading",
    }));

    try {
      const response = await fetch(
        `http://localhost:4000/api/strat/league/${leagueId}/standings`
      );

      if (!response.ok) {
        throw new Error(
          `League standings refresh failed: ${response.status}`
        );
      }

      const payload = await response.json();

      setStratLeagueData((current) => ({
        ...current,
        [leagueId]: payload,
      }));

      setStratLeagueStatus((current) => ({
        ...current,
        [leagueId]: "ready",
      }));
    } catch (error) {
      console.error(
        "Active league refresh failed:",
        leagueId,
        error
      );

      setStratLeagueStatus((current) => ({
        ...current,
        [leagueId]: "error",
      }));
    }
  };

  const refreshStratRotation = async (leagueId, teamId) => {
    const key = `${leagueId}:${teamId}`;

    setStratRotationStatus((current) => ({
      ...current,
      [key]: "loading",
    }));

    try {
      const response = await fetch(
        `http://localhost:4000/api/strat/league/${leagueId}/team/${teamId}/rotation`
      );

      if (!response.ok) {
        throw new Error(
          `Rotation projection failed: ${response.status}`
        );
      }

      const payload = await response.json();

      setStratRotationData((current) => ({
        ...current,
        [key]: payload,
      }));

      setStratRotationStatus((current) => ({
        ...current,
        [key]: "ready",
      }));

      return payload;
    } catch (error) {
      console.error(
        "Rotation projection refresh failed:",
        leagueId,
        teamId,
        error
      );

      setStratRotationStatus((current) => ({
        ...current,
        [key]: "error",
      }));

      return null;
    }
  };
  const refreshAllStratTeams = () => {
    ACTIVE_STRAT_TEAMS.forEach((team) => {
      void refreshStratTeamAndOpponent(team);
      void refreshStratCurrentPreview(team);
      refreshStratLeague(team.leagueId);
    });

    setStratActionMessage(
      "Refreshing current teams, opponents, schedules, rotations, and standings from Strat365."
    );
  };
  const openSeriesPreview = async (team) => {
    const currentPreview =
      await refreshStratCurrentPreview(team);

    const currentIdentity =
      currentPreview?.seriesIdentity || null;

    if (!currentIdentity?.opponentTeamId) {
      setStratActionMessage(
        `${team.teamName} · League ${team.leagueId}: current BIE Series Preview is not yet resolved.`
      );
      return;
    }

    setSelectedSeriesPreview({
      leagueId: String(team.leagueId),
      teamId: String(team.teamId),
      scheduleUrl: team.scheduleUrl,
      opponentTeamId:
        String(currentIdentity.opponentTeamId),
      opponentDisplayName:
        currentIdentity.opponentDisplayName || null,
    });

    setActiveView("SeriesPreview");

    setStratActionMessage(
      `${team.teamName} · League ${team.leagueId}: current BIE Series Preview opened.`
    );
  };
  useEffect(() => {
    ACTIVE_STRAT_TEAMS.forEach((team) => {
      void refreshStratTeamAndOpponent(team);
      void refreshStratCurrentPreview(team);
      refreshStratLeague(team.leagueId);
    });
  }, []);
  const navSections = [
    {
      title: "Operations",
      groups: [
        {
          title: "StratOperations",
          items: [
            ["StratHome", "Strat-O-Matic Active Teams"],
          ],
        },
      ],
    },
    {
      title: "Intelligence",
      groups: [
        {
          title: "Personal Intelligence",
          items: [
            ["IntelligenceHome", "Intelligence Home"],
            ["MusicDashboard", "Music Dashboard"],
            ["QueryWorkbench", "Query Workbench"],
            ["Music", "Music Intelligence"],
            ["PlaylistIntelligence", "Playlist Intelligence"],
            ["Books", "Books"],
            ["Notes", "Notes"],
          ],
        },
      ],
    },
    {
      title: "Signals",
      groups: [
        {
          title: "Live Signals",
          items: [
            ["Calendar", "Calendar"],
            ["News", "News"],
            ["Finance", "Finance"],
          ],
        },
      ],
    },

  ];

  const navButton = (view, label) => (

    <button

      onClick={() => {

        if (view === "QueryWorkbench") {

          setQueryWorkbenchArtist("");

          setQueryWorkbenchSource("");

        }



        setActiveView(view);

      }}

      className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition ${

        activeView === view

          ? "bg-slate-900 text-white font-semibold shadow-sm"

          : isDark

            ? "text-slate-300 hover:bg-slate-800 hover:text-white"

            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"

      }`}

    >

      {label}

    </button>

  );





  function ActiveTeamHeroMark({
  identity,
  alt,
  tone = "cyan",
}) {
  const [imageFailed, setImageFailed] =
    useState(false);

  const palette =
    tone === "rose"
      ? "border-rose-800 bg-rose-950/60 text-rose-200"
      : "border-cyan-800 bg-cyan-950/60 text-cyan-200";

  const sizeClass =
    "h-36 w-36 sm:h-40 sm:w-40 lg:h-44 lg:w-44";

  if (
    identity?.logoPath &&
    !imageFailed
  ) {
    return (
      <img
        src={identity.logoPath}
        alt={alt || identity?.teamName || "Team"}
        className={`${sizeClass} object-contain`}
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <div
      data-bie-logo-fallback="monogram"
      aria-label={alt || identity?.teamName || "Team"}
      className={`flex ${sizeClass} items-center justify-center rounded-3xl border text-4xl font-black ${palette}`}
    >
      {identity?.monogram || "?"}
    </div>
  );
}

const STRAT_1968_PARK_EFFECTS = {
  "Astrodome 1968": {
    singlesLeft: 9,
    singlesRight: 9,
    homeRunsLeft: 1,
    homeRunsRight: 1,
  },
  "Comiskey Park 1968": {
    singlesLeft: 7,
    singlesRight: 10,
    homeRunsLeft: 5,
    homeRunsRight: 5,
  },
  "Busch Stadium 1968": {
    singlesLeft: 1,
    singlesRight: 6,
    homeRunsLeft: 1,
    homeRunsRight: 4,
  },
};
const StratHome = () => (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-[#06172f] via-[#08243d] to-cyan-950 p-6 text-white shadow-[0_18px_50px_rgba(8,47,73,0.22)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <div className="inline-flex rounded-xl bg-slate-950 px-3 py-2">
              <img
                src="https://365.strat-o-matic.com/img/redesign/header_logo_som.png"
                alt="Strat-O-Matic"
                className="h-8 w-auto"
              />
            </div>

            <p className="-mt-0.5 whitespace-nowrap text-[11px] font-black uppercase tracking-[0.16em] text-cyan-300 sm:text-xs">
              Active Teams · BIE-backed workspace
            </p>

            <h2 className="mt-2 whitespace-nowrap text-3xl font-black leading-none tracking-tight text-white sm:text-4xl">
              Active Teams
            </h2>

            <p className="mt-3 max-w-3xl text-sm font-medium leading-6 text-slate-200">
              Current position, upcoming opposition, and the decisions that matter before and after each series.
              BIE surfaces evidence-backed intelligence and leaves unsupported fields explicitly unresolved.
            </p>
          </div>

          <button
            type="button"
            onClick={refreshAllStratTeams}
            className="rounded-xl border border-cyan-300/40 bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-sm font-black text-white shadow-[0_8px_24px_rgba(6,182,212,0.28)] transition hover:from-cyan-400 hover:to-blue-500"
          >
            Refresh All Teams
          </button>
        </div>

        {stratActionMessage && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">
            {stratActionMessage}
          </div>
        )}
      </section>

      <section className="grid gap-7">
        {ACTIVE_STRAT_TEAMS.map((team) => {
          const live = stratTeamData[team.teamId];
          const liveStatus =
            stratTeamStatus[team.teamId] || "loading";

          const currentPreviewKey =
            `${team.leagueId}:${team.teamId}`;

          const currentPreview =
            stratCurrentPreviewData[
              currentPreviewKey
            ] || null;

          const currentSeries =
            currentPreview?.seriesIdentity || null;

          const currentOpponentTeamId =
            currentSeries?.opponentTeamId || null;

          const currentOpponentName =
            currentSeries?.opponentDisplayName || "Resolving...";

          const currentOpponentIdentity =
            currentOpponentTeamId
              ? getStratTeamIdentity(
                  currentOpponentTeamId,
                  currentOpponentName,
                )
              : null;

          const currentOpponentDisplayName =
            currentOpponentIdentity?.teamName ||
            currentOpponentName;

          const currentSeriesDate =
            currentSeries?.scheduledDate || "Resolving...";

          const currentGameCount =
            currentSeries?.gameCount ?? null;

          const currentHomeAway =
            currentSeries?.homeAway || "—";

          const opponentLive =
            currentOpponentTeamId ? stratTeamData[currentOpponentTeamId] : null;
          const opponentStatus =
            currentOpponentTeamId ? stratTeamStatus[currentOpponentTeamId] || "loading" : "loading";

          const league =
            stratLeagueData[team.leagueId];
          const leagueStatus =
            stratLeagueStatus[team.leagueId] || "loading";

          const standings =
            league?.standings || [];

          const teamStanding =
            standings.find(
              (row) => row.teamId === team.teamId
            );

          const opponentStanding =
            standings.find(
              (row) =>
                row.teamId === currentOpponentTeamId
            );

          const isPreseason =
            team.bie.phase === "PRESEASON";

          const seriesBallpark =
            currentHomeAway === "Away"
              ? opponentLive?.homeBallpark
              : live?.homeBallpark;
          const seriesParkEffects =
            STRAT_1968_PARK_EFFECTS[seriesBallpark] || null;

          const teamVenueRecord =
            currentHomeAway === "Away"
              ? teamStanding?.roadRecord
              : teamStanding?.homeRecord;

          const opponentVenueRecord =
            currentHomeAway === "Away"
              ? opponentStanding?.homeRecord
              : opponentStanding?.roadRecord;

          const teamRotationKey =
            `${team.leagueId}:${team.teamId}`;

          const opponentRotationKey =
            currentOpponentTeamId ? `${team.leagueId}:${currentOpponentTeamId}` : null;

          const teamRotation =
            stratRotationData[teamRotationKey];

          const opponentRotation =
            stratRotationData[opponentRotationKey];

          const teamRotationState =
            stratRotationStatus[teamRotationKey] || "loading";

          const opponentRotationState =
            stratRotationStatus[opponentRotationKey] || "loading";

          const rotationLoading =
            teamRotationState === "loading" ||
            opponentRotationState === "loading";

          const rotationError =
            teamRotationState === "error" ||
            opponentRotationState === "error";

          const rotationReady =
            teamRotation?.status === "PROJECTED" &&
            opponentRotation?.status === "PROJECTED";

          const seriesRead = buildSeriesRead({
            isPreseason,
            homeAway: currentHomeAway,
            teamStanding,
            opponentStanding,
          });

          return (
            <article
              key={team.teamId}
              className="group overflow-hidden rounded-3xl border border-cyan-200/90 bg-gradient-to-b from-cyan-50/70 via-white to-white shadow-[0_12px_34px_rgba(8,47,73,0.10)] ring-1 ring-cyan-100/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-[0_18px_44px_rgba(8,47,73,0.16)] dark:border-cyan-900/70 dark:from-[#07192e] dark:via-slate-900 dark:to-slate-900 dark:ring-cyan-950"
            >
              <div
                data-bie-surface="active-team-matchup-hero"
                data-bie-polish="active-team-hero-v2"
                className="relative overflow-hidden border-b border-slate-800 bg-slate-950 px-5 py-5 text-white sm:px-7 sm:py-6 lg:px-9"
              >
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0"
                >
                  <div className="absolute -left-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-cyan-500/15 blur-3xl" />
                  <div className="absolute -right-24 top-1/2 h-72 w-72 -translate-y-1/2 rounded-full bg-rose-500/15 blur-3xl" />
                </div>

                <div className="relative flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-300">
                      1968 · League {team.leagueId}
                    </p>

                    <p className="mt-1 text-xs font-semibold text-slate-400">
                      Active Series Command
                    </p>
                  </div>

                  {isPreseason ? (
                    <span className="rounded-full border border-sky-700 bg-sky-950/70 px-3 py-1 text-[10px] font-black uppercase tracking-[0.14em] text-sky-300">
                      Preseason
                    </span>
                  ) : null}
                </div>

                <div className="relative mt-5 grid items-center gap-5 md:grid-cols-[minmax(0,1fr)_170px_minmax(0,1fr)]">
                  <div className="flex flex-col items-center text-center">
                    <ActiveTeamHeroMark
                      key={`aquarium-${team.teamId}`}
                      identity={getStratTeamIdentity(
                        team.teamId,
                        team.teamName
                      )}
                      alt="Aquarium Drinkers"
                      tone="cyan"
                    />

                    <p className="mt-4 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                      Aquarium Drinkers
                    </p>

                    <h3 className="mt-1 text-2xl font-black tracking-tight">
                      {team.teamName}
                    </h3>

                    <p className="mt-2 text-3xl font-black">
                      {live?.record ||
                        (liveStatus === "error"
                          ? "Unavailable"
                          : "—")}
                    </p>

                    {!isPreseason && teamStanding ? (
                      <p className="mt-1 text-sm font-bold text-slate-300">
                        {formatOrdinal(
                          teamStanding.divisionRank
                        )}{" "}
                        {teamStanding.division}
                      </p>
                    ) : null}
                  </div>

                  <div className="text-center">
                    <p className="text-[9px] font-black uppercase tracking-[0.24em] text-slate-500">
                      Next Series
                    </p>

                    <p className="mt-2 text-5xl font-black tracking-[-0.05em]">
                      VS
                    </p>

                    <p className="mt-4 text-base font-black text-white">
                      {currentSeriesDate}
                    </p>

                    <div className="mt-2 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs font-semibold text-slate-400">
                      <span>{currentHomeAway}</span>
                      <span aria-hidden="true">·</span>
                      <span>
                        {currentGameCount ?? "—"} games
                      </span>
                    </div>

                    <p className="mt-3 text-xs font-bold leading-5 text-slate-300">
                      {seriesBallpark || "Ballpark resolving"}
                    </p>
                  </div>

                  <div className="flex flex-col items-center text-center">
                    <ActiveTeamHeroMark
                      key={
                        currentOpponentIdentity?.teamId ||
                        currentOpponentDisplayName
                      }
                      identity={currentOpponentIdentity}
                      alt={currentOpponentDisplayName}
                      tone="rose"
                    />

                    <p className="mt-4 text-[10px] font-black uppercase tracking-[0.2em] text-rose-300">
                      Opponent
                    </p>

                    <h3 className="mt-1 text-2xl font-black tracking-tight">
                      {currentOpponentDisplayName}
                    </h3>

                    <p className="mt-2 text-3xl font-black">
                      {opponentLive?.record ||
                        (opponentStatus === "error"
                          ? "Unavailable"
                          : "—")}
                    </p>

                    {!isPreseason && opponentStanding ? (
                      <p className="mt-1 text-sm font-bold text-slate-300">
                        {formatOrdinal(
                          opponentStanding.divisionRank
                        )}{" "}
                        {opponentStanding.division}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className="relative mt-4 flex flex-col gap-3 border-t border-slate-800 pt-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-[0.18em] text-emerald-300">
                      BIE Read
                    </p>

                    <p className="mt-1 text-sm font-bold text-white">
                      {seriesRead?.label ||
                        seriesRead?.classification ||
                        "Series matchup ready"}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => openSeriesPreview(team)}
                    className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-black text-slate-950 transition hover:bg-cyan-300"
                  >
                    View Series Matchup →
                  </button>
                </div>
              </div>

              <div className="hidden">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <img
                    src="/aquarium-drinkers-shield.svg"
                    alt="Aquarium Drinkers"
                    title="Aquarium Drinkers"
                    className="h-32 w-32 object-contain sm:h-36 sm:w-36 lg:h-44 lg:w-44"
                  />

                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">
                        {team.season} · LEAGUE {team.leagueId}
                      </p>

                      <h3 className="mt-1 text-2xl font-black text-white">
                        {team.teamName}
                      </h3>
                    </div>
                  </div>

                  <div className="flex flex-wrap justify-end gap-2">
                    {isPreseason && (
                      <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
                        Preseason
                      </span>
                    )}

                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${
                        liveStatus === "ready"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                          : liveStatus === "error"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {liveStatus === "ready"
                        ? "Live"
                        : liveStatus === "error"
                          ? "Live unavailable"
                          : "Refreshing"}
                    </span>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-white/10 bg-white/10 p-3 text-white shadow-inner backdrop-blur-sm">
                    <p className="text-xs font-semibold text-cyan-100/70">
                      Record
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {live?.record ||
                        (liveStatus === "error"
                          ? "Unavailable"
                          : "Loading…")}
                    </p>
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/10 p-3 text-white shadow-inner backdrop-blur-sm">
                    <p className="text-xs font-semibold text-cyan-100/70">
                      Standing
                    </p>
                    <p className="mt-1 text-lg font-black">
                      {isPreseason
                        ? "—"
                        : teamStanding
                          ? `${formatOrdinal(
                              teamStanding.divisionRank
                            )} ${teamStanding.division}`
                          : leagueStatus === "error"
                            ? "Unavailable"
                            : "Loading…"}
                    </p>

                    {!isPreseason && teamStanding && (
                      <p className="mt-0.5 text-xs font-semibold text-slate-300">
                        {teamStanding.gamesBehind === "-"
                          ? "Division leader"
                          : `${teamStanding.gamesBehind} GB`}
                      </p>
                    )}
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/10 p-3 text-white shadow-inner backdrop-blur-sm">
                    <p className="text-xs font-semibold text-cyan-100/70">
                      Run Diff
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {isPreseason
                        ? "—"
                        : teamStanding?.runDifferential ||
                          (leagueStatus === "error"
                            ? "Unavailable"
                            : "Loading…")}
                    </p>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold text-slate-300">
                  {isPreseason ? (
                    <span>
                      Performance data begins Opening Day
                    </span>
                  ) : (
                    <>
                      <span>
                        Recent form · L10 {teamStanding?.last10 || "…"}
                      </span>
                      <span>·</span>
                      <span>
                        Streak {teamStanding?.streak || "…"}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div
                data-bie-surface="starter-matchup-strip"
                className="border-t border-cyan-100 bg-slate-50/80 px-5 py-4 dark:border-slate-800 dark:bg-slate-950/40"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">
                      Probable Starters
                    </p>
                    <p className="mt-0.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
                      Projected series rotation
                    </p>
                  </div>

                  {rotationReady ? (
                    <span className="rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.12em] text-cyan-800 dark:border-cyan-900 dark:bg-cyan-950/60 dark:text-cyan-300">
                      Live projection
                    </span>
                  ) : null}
                </div>

                {rotationError ? (
                  <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                    Rotation evidence unavailable
                  </div>
                ) : rotationLoading ? (
                  <div className="mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-400 dark:border-slate-800 dark:bg-slate-900/70">
                    Loading rotation evidence…
                  </div>
                ) : !rotationReady ? (
                  <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-white/70 px-4 py-3 text-sm font-semibold text-slate-400 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-500">
                    Rotation projection not yet available
                  </div>
                ) : (
                  <>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      {[1, 2, 3].map((gameNumber) => {
                        const teamProjection =
                          teamRotation?.projections?.find(
                            (projection) =>
                              Number(projection.slot) === gameNumber
                          );

                        const opponentProjection =
                          opponentRotation?.projections?.find(
                            (projection) =>
                              Number(projection.slot) === gameNumber
                          );

                        const confidence =
                          teamProjection?.effectiveConfidence ||
                          opponentProjection?.effectiveConfidence ||
                          "NONE";

                        const teamPitcher =
                          findProjectedStarterRosterRow(
                            live,
                            teamProjection?.pitcher,
                          );

                        const opponentPitcher =
                          findProjectedStarterRosterRow(
                            opponentLive,
                            opponentProjection?.pitcher,
                          );

                        return (
                          <div
                            key={gameNumber}
                            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900/80"
                          >
                            <div className="flex items-center justify-between border-b border-slate-100 px-3.5 py-2 dark:border-slate-800">
                              <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                                Game {gameNumber}
                              </p>

                              <span
                                className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${rotationConfidenceClasses(
                                  confidence
                                )}`}
                              >
                                {confidence.toLowerCase()}
                              </span>
                            </div>

                            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-3 py-4">
                              <div className="min-w-0 text-left">
                                <p className="text-[9px] font-black uppercase tracking-[0.12em] text-cyan-700 dark:text-cyan-300">
                                  Aquarium
                                </p>
                                <p className="mt-1 truncate text-sm font-black text-[#06172f] dark:text-white">
                                  {teamProjection
                                    ? formatRotationPitcher(
                                        teamProjection.pitcher
                                      )
                                    : "TBD"}
                                </p>

                                <p className="mt-1 text-[10px] font-bold tabular-nums text-slate-600 dark:text-slate-300">
                                  {formatStarterThrowingHand(
                                    teamPitcher?.throws,
                                  )}
                                  {" · "}
                                  {formatStarterRecord(
                                    teamPitcher,
                                  )}
                                  {" · "}
                                  ERA{" "}
                                  {formatStarterStat(
                                    teamPitcher?.era,
                                    2,
                                  )}
                                  {" · "}
                                  WHIP{" "}
                                  {formatStarterStat(
                                    teamPitcher?.whip,
                                    2,
                                  )}
                                </p>

                                <p className="mt-0.5 text-[9px] font-semibold tabular-nums text-slate-400">
                                  IP{" "}
                                  {teamPitcher?.innings ||
                                    "—"}
                                  {" · "}
                                  K/BB{" "}
                                  {formatStarterKbb(
                                    teamPitcher,
                                  )}
                                  {" · "}
                                  {formatStarterHold(
                                    teamPitcher?.holdRating,
                                  )}
                                  {teamPitcher?.endurance
                                    ? ` · ${teamPitcher.endurance}`
                                    : ""}
                                </p>
                              </div>

                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-[9px] font-black text-white dark:bg-slate-700">
                                VS
                              </div>

                              <div className="min-w-0 text-right">
                                <p className="truncate text-[9px] font-black uppercase tracking-[0.12em] text-rose-700 dark:text-rose-300">
                                  {currentOpponentDisplayName}
                                </p>
                                <p className="mt-1 truncate text-sm font-black text-[#06172f] dark:text-white">
                                  {opponentProjection
                                    ? formatRotationPitcher(
                                        opponentProjection.pitcher
                                      )
                                    : "TBD"}
                                </p>

                                <p className="mt-1 text-[10px] font-bold tabular-nums text-slate-600 dark:text-slate-300">
                                  {formatStarterThrowingHand(
                                    opponentPitcher?.throws,
                                  )}
                                  {" · "}
                                  {formatStarterRecord(
                                    opponentPitcher,
                                  )}
                                  {" · "}
                                  ERA{" "}
                                  {formatStarterStat(
                                    opponentPitcher?.era,
                                    2,
                                  )}
                                  {" · "}
                                  WHIP{" "}
                                  {formatStarterStat(
                                    opponentPitcher?.whip,
                                    2,
                                  )}
                                </p>

                                <p className="mt-0.5 text-[9px] font-semibold tabular-nums text-slate-400">
                                  IP{" "}
                                  {opponentPitcher?.innings ||
                                    "—"}
                                  {" · "}
                                  K/BB{" "}
                                  {formatStarterKbb(
                                    opponentPitcher,
                                  )}
                                  {" · "}
                                  {formatStarterHold(
                                    opponentPitcher?.holdRating,
                                  )}
                                  {opponentPitcher?.endurance
                                    ? ` · ${opponentPitcher.endurance}`
                                    : ""}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <p className="mt-2.5 text-[10px] leading-4 text-slate-400 dark:text-slate-500">
                      Projection from recent completed starts and observed rotation transitions; not announced starters.
                    </p>
                  </>
                )}

                <div className="mt-3 flex flex-wrap justify-end gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={() => refreshStratTeam(team.teamId)}
                    className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    Refresh Team
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      window.open(
                        team.teamUrl,
                        "_blank",
                        "noopener,noreferrer"
                      )
                    }
                    className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    Open Strat
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <h3 className="text-lg font-black">
          BIE Operations
        </h3>

        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Series capture, parsing, League Intelligence, card analysis,
          simulation, and other internal engines are no longer exposed as
          primary navigation. They remain available in the codebase while
          this operating view becomes the normal way to use BIE.
        </p>
      </section>
    </div>
  );


  const IntelligenceHome = () => (

    <div className="space-y-6">

      <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">

        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">

          Defending Sisyphus

        </p>

        <h2 className="mt-2 text-3xl font-black tracking-tight">

          Personal Intelligence System

        </h2>

        <p className="mt-3 max-w-3xl text-sm font-medium leading-6 text-slate-200">

          Query your archives, surface long-running patterns, and turn personal data into usable memory.

        </p>

      </section>

<section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">

        <h3 className="text-lg font-black">Next Intelligence Actions</h3>

        <div className="mt-4 grid gap-3 md:grid-cols-3">

          <button

            type="button"

            className="rounded-xl border border-slate-300 px-4 py-3 text-left text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"

          >

            Query Workbench

            <span className="block pt-1 text-xs font-medium text-slate-500">

              Coming soon: artist, album, song, and date-range lookup.

            </span>

          </button>

          <button

            type="button"

            onClick={() => setActiveView("MusicTimeMachine")}
            className="rounded-xl border border-slate-300 px-4 py-3 text-left text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"

          >

            Music Time Machine
            <span className="block pt-1 text-xs font-medium text-slate-500">

              Investigate listening evidence across a selected period.
            </span>

          </button>

          <button

            type="button"

            onClick={() => setActiveView("Calendar")}

            className="rounded-xl border border-slate-300 px-4 py-3 text-left text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"

          >

            Signals

            <span className="block pt-1 text-xs font-medium text-slate-500">

              Review calendar, news, and finance signals.

            </span>

          </button>

        </div>

      </section>

    </div>

  );



  return (

    <div className={`min-h-screen transition-colors duration-200 ${isDark ? "bg-gradient-to-br from-slate-950 via-cyan-950/80 to-slate-900 text-slate-100" : "bg-gradient-to-br from-slate-100 via-cyan-50/70 to-blue-100/70 text-slate-900"}`}>

      <header className="bg-[#06172f] text-white border-b border-cyan-800/50 shadow-sm">

        <div className="px-6 py-4 flex items-center justify-between">

          <div>

            <h1 className="text-xl font-bold tracking-tight">

              Defending Sisyphus · Strat-O-Matic

            </h1>

            <p className="text-xs text-cyan-100/60 mt-1">

              Personal command center

            </p>

          </div>



          <div className="flex items-center gap-4">

            <div className="text-xs text-slate-400">

              Active teams / intelligence / signals

            </div>



            <button

              type="button"

              onClick={toggleTheme}

              className="rounded-full border border-cyan-800/60 bg-[#0a2342] px-3 py-1.5 text-xs font-semibold text-cyan-50/90 transition hover:border-cyan-600 hover:bg-[#0d3156] hover:text-white"

            >

              {isDark ? "Light Mode" : "Dark Mode"}

            </button>

          </div>

        </div>

      </header>



      <div className="flex">

        <aside className={`w-64 backdrop-blur border-r p-4 space-y-8 min-h-screen shadow-sm transition-colors duration-200 ${isDark ? "bg-[#07192e]/95 border-cyan-900/60" : "bg-white/90 border-cyan-100"}`}>

          {navSections.map((section) => (

            <div key={section.title} className="space-y-3">

              <div className={`text-[11px] font-black uppercase tracking-[0.18em] border-b pb-2 ${isDark ? "text-cyan-100/80 border-cyan-900/70" : "text-slate-600 border-cyan-200/80"}`}>

                {section.title}

              </div>



              {section.groups.map((group) => (

                <details

                  key={group.title}

                  open={group.title !== "Administration"}

                  className={`group rounded-xl px-2 py-2 transition-colors ${isDark ? "hover:bg-cyan-950/60" : "hover:bg-cyan-50/80"}`}

                >

                  <summary className={`mb-2 cursor-pointer list-none text-[10px] font-bold uppercase tracking-[0.16em] transition-colors ${isDark ? "text-cyan-200/45 hover:text-cyan-100/80" : "text-slate-400 hover:text-cyan-700"}`}>

                    <div className="flex items-center justify-between">

                      <span>{group.title}</span>

                      <span className="text-[10px] transition-transform group-open:rotate-90">

                        &gt;

                      </span>

                    </div>

                  </summary>



                  <div className="space-y-1 pl-1">

                    {group.items.map(([view, label]) => (

                      <React.Fragment key={view}>

                        {navButton(view, label)}

                      </React.Fragment>

                    ))}

                  </div>

                </details>

              ))}

            </div>

          ))}

        </aside>



        <main className="flex-1 p-6">

          <div className="max-w-screen-2xl mx-auto px-4">

            {activeView === "StratHome" ? (


              <StratHome />


            ) : activeView === "MusicDashboard" ? (

              <MusicDashboard

                onOpenArtist={(artist) => {

                  setQueryWorkbenchArtist(artist);

                  setQueryWorkbenchSource("dashboard");

                  setActiveView("QueryWorkbench");

                }}

              />

            ) : activeView === "QueryWorkbench" ? (

              <QueryWorkbench

                initialArtist={queryWorkbenchArtist}

                fromDashboard={queryWorkbenchSource === "dashboard"}

                onBackToDashboard={() => setActiveView("MusicDashboard")}

                onOpenArtist={(artistName) => {

                  setSelectedArtistForIntelligence(artistName);

                  setActiveView("ArtistIntelligence");

                }}

              />

            ) : activeView === "ArtistIntelligence" ? (

              <ArtistIntelligence

                artistName={selectedArtistForIntelligence}

                onBack={() => setActiveView("QueryWorkbench")}

              />

            ) : activeView === "IntelligenceHome" ? (

              <IntelligenceHome />

            ) : activeView === "Calendar" ? (

              <>

                <WeatherBug />

                <CalendarView />

              </>

            ) : activeView === "Pitching" ? (

              <PitchingAnalyzer />

            ) : activeView === "Matchup" ? (

              <MatchupAnalyzer />

            ) : activeView === "SeriesPreview" ? (

        <SeriesPreview
          selection={selectedSeriesPreview}
          onBack={() => {
            setSelectedSeriesPreview(null);
            setActiveView("StratHome");
          }}
        />

      ) : activeView === "Series" ? (

        <SeriesPlanner />

            ) : activeView === "GameSim" ? (

              <GameSimulator />

            ) : activeView === "LeagueManager" ? (

  <LeagueManager />

) : activeView === "Opponents" ? (

  <OpponentManager />

) : activeView === "News" ? (

              <NewsView />

            ) : activeView === "Finance" ? (

              <FinanceView />



            ) : activeView === "PlaylistIntelligence" ? (

              <PlaylistIntelligence />

            ) : activeView === "MusicTimeMachine" ? (

              <MusicTimeMachine />

            ) : activeView === "Music" ? (
              <MusicLibrary />

            ) : activeView === "MusicAnalytics" ? (

              <AppleMusicAnalytics />

            ) : activeView === "Books" ? (

              <BooksView />

            ) : activeView === "Notes" ? (

              <NotesView />

            ) : (

              <LineupAnalyzer />

            )}

                   </div>

        </main>

      </div>



      <ScrollToTopButton />

    </div>

  );

}
