import React, { useEffect, useState } from "react";

import AppleMusicAnalytics from "./AppleMusicAnalytics";

import CalendarView from "./CalendarView";

import LineupAnalyzer from "./LineupAnalyzer";

import PitchingAnalyzer from "./PitchingAnalyzer";

import MatchupAnalyzer from "./MatchupAnalyzer";

import FinanceView from "./FinanceView";

import SeriesPlanner from "./SeriesPlanner";

import GameSimulator from "./GameSimulator";

import LeagueManager from "./LeagueManager";

import OpponentManager from "./OpponentManager";

import WeatherBug from "./WeatherBug";

import NewsView from "./NewsView";

import CardImporter from "./CardImporter";

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
      opponentTeamId: "1853519",
      nextOpponent: "Busch League Arkinals™",
      nextSeriesDate: "Aug 11",
      homeAway: "Away",
      gameCount: 3,
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
      opponentTeamId: "1854468",
      nextOpponent: "Hey Jude",
      nextSeriesDate: "Aug 11",
      homeAway: "Home",
      gameCount: 3,
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
      phase: "PRESEASON",
      opponentTeamId: "1855876",
      nextOpponent: "Georgia Peaches",
      nextSeriesDate: "Aug 13",
      homeAway: "Away",
      gameCount: 3,
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

export default function App() {

  const [activeView, setActiveView] = useState("StratHome");

  const [selectedArtistForIntelligence, setSelectedArtistForIntelligence] = useState("Billie Holiday");

  const [queryWorkbenchArtist, setQueryWorkbenchArtist] = useState("");
  const [stratTeamData, setStratTeamData] = useState({});
  const [stratTeamStatus, setStratTeamStatus] = useState({});
  const [stratLeagueData, setStratLeagueData] = useState({});
  const [stratLeagueStatus, setStratLeagueStatus] = useState({});
  const [stratRotationData, setStratRotationData] = useState({});
  const [stratRotationStatus, setStratRotationStatus] = useState({});
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

  const refreshStratTeamAndOpponent = (team) => {
    refreshStratTeam(team.teamId);
    refreshStratTeam(team.bie.opponentTeamId);
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
    }
  };

  const refreshAllStratTeams = () => {
    ACTIVE_STRAT_TEAMS.forEach((team) => {
      refreshStratTeamAndOpponent(team);
      refreshStratLeague(team.leagueId);
      refreshStratRotation(team.leagueId, team.teamId);
      refreshStratRotation(
        team.leagueId,
        team.bie.opponentTeamId
      );
    });

    setStratActionMessage(
      "Refreshing current teams, opponents, and standings from Strat365."
    );
  };

  const updateUpcomingSeries = (team) => {
    refreshStratTeamAndOpponent(team);

    window.open(
      team.scheduleUrl,
      "_blank",
      "noopener,noreferrer"
    );

    setStratActionMessage(
      `${team.teamName} · League ${team.leagueId}: live team refreshed and current schedule opened.`
    );
  };

  useEffect(() => {
    ACTIVE_STRAT_TEAMS.forEach((team) => {
      refreshStratTeamAndOpponent(team);
      refreshStratLeague(team.leagueId);
      refreshStratRotation(team.leagueId, team.teamId);
      refreshStratRotation(
        team.leagueId,
        team.bie.opponentTeamId
      );
    });
  }, []);

  const navSections = [
    {
      title: "Operations",
      groups: [
        {
          title: "StratOperations",
          items: [
            ["StratHome", "Strat-o-Matic Active Teams"],
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
    {
      title: "Utilities",
      groups: [
        {
          title: "Tools",
          items: [
            ["CardImporter", "Card Importer"],
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





  const StratHome = () => (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
              StratOperations
            </p>

            <div className="mb-3 inline-flex rounded-xl bg-slate-950 px-3 py-2">
              <img
                src="https://365.strat-o-matic.com/img/redesign/header_logo_som.png"
                alt="Strat-O-Matic"
                className="h-8 w-auto"
              />
            </div>
            <h2 className="mt-2 text-3xl font-black tracking-tight">
              Strat-o-Matic Active Teams
            </h2>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              Current position, upcoming opposition, and the decisions that matter before and after each series.
              BIE surfaces evidence-backed intelligence and leaves unsupported fields explicitly unresolved.
            </p>
          </div>

          <button
            type="button"
            onClick={refreshAllStratTeams}
            className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white"
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

      <section className="grid gap-5 xl:grid-cols-3">
        {ACTIVE_STRAT_TEAMS.map((team) => {
          const live = stratTeamData[team.teamId];
          const liveStatus =
            stratTeamStatus[team.teamId] || "loading";

          const opponentLive =
            stratTeamData[team.bie.opponentTeamId];
          const opponentStatus =
            stratTeamStatus[team.bie.opponentTeamId] || "loading";

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
                row.teamId === team.bie.opponentTeamId
            );

          const isPreseason =
            team.bie.phase === "PRESEASON";

          const seriesBallpark =
            team.bie.homeAway === "Away"
              ? opponentLive?.homeBallpark
              : live?.homeBallpark;

          const teamVenueRecord =
            team.bie.homeAway === "Away"
              ? teamStanding?.roadRecord
              : teamStanding?.homeRecord;

          const opponentVenueRecord =
            team.bie.homeAway === "Away"
              ? opponentStanding?.homeRecord
              : opponentStanding?.roadRecord;

          const teamRotationKey =
            `${team.leagueId}:${team.teamId}`;

          const opponentRotationKey =
            `${team.leagueId}:${team.bie.opponentTeamId}`;

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
            homeAway: team.bie.homeAway,
            teamStanding,
            opponentStanding,
          });

          return (
            <article
              key={team.teamId}
              className="overflow-hidden rounded-2xl border border-cyan-200/80 bg-white/95 shadow-[0_8px_24px_rgba(8,47,73,0.08)] transition-shadow hover:shadow-[0_12px_30px_rgba(8,47,73,0.13)] dark:border-cyan-900/60 dark:bg-slate-900/90"
            >
              <div className="border-b border-cyan-100 bg-gradient-to-r from-cyan-50/70 via-white to-blue-50/50 p-5 dark:border-cyan-900/60 dark:from-[#07192e] dark:via-slate-900 dark:to-cyan-950/40">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-cyan-400 bg-[#06172f] shadow-sm"
                      aria-label="Aquarium Drinkers"
                      title="Aquarium Drinkers"
                    >
                      <span className="translate-x-px -translate-y-px font-serif text-xl font-black italic leading-none tracking-[-0.04em] text-white">
                        AD
                      </span>
                    </div>

                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-800/70 dark:text-cyan-200/65">
                        {team.season} · League {team.leagueId}
                      </p>

                      <h3 className="mt-1 text-2xl font-black text-[#06172f] dark:text-white">
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
                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Record
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {live?.record ||
                        (liveStatus === "error"
                          ? "Unavailable"
                          : "Loading…")}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
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
                      <p className="mt-0.5 text-xs font-semibold text-slate-400 dark:text-slate-500">
                        {teamStanding.gamesBehind === "-"
                          ? "Division leader"
                          : `${teamStanding.gamesBehind} GB`}
                      </p>
                    )}
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
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

                <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {isPreseason ? (
                    <span>
                      Performance data begins Opening Day
                    </span>
                  ) : (
                    <>
                      <span>
                        L10 {teamStanding?.last10 || "…"}
                      </span>
                      <span>·</span>
                      <span>
                        Streak {teamStanding?.streak || "…"}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="p-5">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  Upcoming Series
                </p>

                <p className="mt-2 text-xl font-black">
                  {team.bie.homeAway} · {team.bie.nextOpponent}
                </p>

                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {team.bie.nextSeriesDate} · {team.bie.gameCount} games
                </p>

                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Opp Record
                    </p>
                    <p className="mt-1 font-black">
                      {opponentLive?.record ||
                        (opponentStatus === "error"
                          ? "Unavailable"
                          : "Loading…")}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Opp Standing
                    </p>
                    <p className="mt-1 font-black">
                      {isPreseason
                        ? "—"
                        : opponentStanding
                          ? `${formatOrdinal(
                              opponentStanding.divisionRank
                            )} ${opponentStanding.division}`
                          : leagueStatus === "error"
                            ? "Unavailable"
                            : "Loading…"}
                    </p>

                    {!isPreseason && opponentStanding && (
                      <p className="mt-0.5 text-xs font-semibold text-slate-400 dark:text-slate-500">
                        {opponentStanding.gamesBehind === "-"
                          ? "Division leader"
                          : `${opponentStanding.gamesBehind} GB`}
                      </p>
                    )}
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Opp Diff
                    </p>
                    <p className="mt-1 font-black">
                      {isPreseason
                        ? "—"
                        : opponentStanding?.runDifferential ||
                          (leagueStatus === "error"
                            ? "Unavailable"
                            : "Loading…")}
                    </p>
                  </div>
                </div>

                {!isPreseason && (
                  <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                    <span>
                      Opp L10 {opponentStanding?.last10 || "…"}
                    </span>
                    <span>·</span>
                    <span>
                      Streak {opponentStanding?.streak || "…"}
                    </span>
                  </div>
                )}

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="text-xs font-semibold text-slate-500">
                      Series Ballpark
                    </p>
                    <p className="mt-1 font-bold">
                      {seriesBallpark ||
                        (liveStatus === "error" ||
                        opponentStatus === "error"
                          ? "Unavailable"
                          : "Loading…")}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="text-xs font-semibold text-slate-500">
                      Venue Records
                    </p>
                    <p className="mt-1 font-bold">
                      {isPreseason
                        ? "—"
                        : teamVenueRecord && opponentVenueRecord
                          ? `${team.bie.homeAway} ${teamVenueRecord} · Opp ${
                              team.bie.homeAway === "Away"
                                ? "Home"
                                : "Road"
                            } ${opponentVenueRecord}`
                          : leagueStatus === "error"
                            ? "Unavailable"
                            : "Loading…"}
                    </p>
                  </div>
                </div>

                {(liveStatus === "error" ||
                  opponentStatus === "error" ||
                  leagueStatus === "error") && (
                  <p className="mt-3 text-xs font-semibold text-amber-700 dark:text-amber-300">
                    Live Strat data is unavailable for one or more teams.
                    Missing current values are not inferred.
                  </p>
                )}

                <div
                  className={`mt-4 rounded-xl border p-3 ${
                    seriesRead.tone === "positive"
                      ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/60 dark:bg-emerald-950/20"
                      : seriesRead.tone === "warning"
                        ? "border-amber-200 bg-amber-50/70 dark:border-amber-900/60 dark:bg-amber-950/20"
                        : isPreseason
                          ? "border-blue-200 bg-blue-50/70 dark:border-blue-900/60 dark:bg-blue-950/20"
                          : "border-cyan-200 bg-cyan-50/50 dark:border-cyan-900/60 dark:bg-cyan-950/20"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                      Series Read
                    </p>

                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                        seriesRead.tone === "positive"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                          : seriesRead.tone === "warning"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {seriesRead.label}
                    </span>
                  </div>

                  <p className="mt-2 text-sm font-semibold leading-relaxed text-slate-700 dark:text-slate-300">
                    {seriesRead.summary}
                  </p>

                  {!isPreseason && (
                    <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                      Based on record, run differential, recent form, and venue splits.
                    </p>
                  )}
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-xl border border-cyan-200 bg-cyan-50/40 p-3 dark:border-cyan-900/60 dark:bg-cyan-950/15">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
                        Probable starters
                      </p>

                      {rotationReady && (
                        <span className="rounded-full bg-cyan-100 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-300">
                          Live projection
                        </span>
                      )}
                    </div>

                    {rotationError ? (
                      <p className="mt-2 text-sm font-semibold text-amber-700 dark:text-amber-300">
                        Rotation evidence unavailable
                      </p>
                    ) : rotationLoading ? (
                      <p className="mt-2 text-sm font-semibold text-slate-400">
                        Loading rotation evidence…
                      </p>
                    ) : !rotationReady ? (
                      <p className="mt-2 text-sm font-semibold text-slate-400 dark:text-slate-500">
                        Evidence gated
                      </p>
                    ) : (
                      <div className="mt-3 space-y-2">
                        {[
                          ["Aquarium", teamRotation],
                          [team.bie.nextOpponent, opponentRotation],
                        ].map(([label, rotation]) => {
                          const projections =
                            rotation?.projections?.slice(0, 3) || [];

                          const confidence =
                            projections[0]?.effectiveConfidence || "NONE";

                          return (
                            <div
                              key={label}
                              className="rounded-lg border border-slate-200 bg-white/85 p-2.5 dark:border-slate-800 dark:bg-slate-900/70"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-xs font-black text-[#06172f] dark:text-white">
                                  {label}
                                </p>

                                <span
                                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${rotationConfidenceClasses(
                                    confidence
                                  )}`}
                                >
                                  {confidence.toLowerCase()} confidence
                                </span>
                              </div>

                              <div className="mt-2 grid grid-cols-3 gap-1.5">
                                {projections.map((projection) => (
                                  <div
                                    key={projection.slot}
                                    className="rounded-md bg-slate-50 px-2 py-1.5 dark:bg-slate-950/60"
                                  >
                                    <p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">
                                      G{projection.slot}
                                    </p>
                                    <p className="mt-0.5 text-[11px] font-black text-slate-700 dark:text-slate-200">
                                      {formatRotationPitcher(
                                        projection.pitcher
                                      )}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}

                        <p className="text-[10px] leading-4 text-slate-400 dark:text-slate-500">
                          Projection from recent completed starts and observed rotation transitions; not announced starters.
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 p-3 dark:border-slate-800 dark:bg-slate-950/30">
                    <p className="text-xs font-semibold text-slate-500">
                      Likely lineup
                    </p>
                    <p className="mt-1 text-sm font-semibold text-slate-400 dark:text-slate-500">
                      Evidence gated
                    </p>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => updateUpcomingSeries(team)}
                    className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-blue-500"
                  >
                    Open Series Schedule
                  </button>

                  <button
                    type="button"
                    onClick={() => refreshStratTeam(team.teamId)}
                    className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
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
                    className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
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

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">

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

            ) : activeView === "Series" ? (

              <SeriesPlanner />

            ) : activeView === "GameSim" ? (

              <GameSimulator />

            ) : activeView === "LeagueManager" ? (

  <LeagueManager />

) : activeView === "Opponents" ? (

  <OpponentManager />

) : activeView === "Cards" ? (

  <CardImporter />

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
