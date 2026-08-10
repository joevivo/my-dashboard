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
      record: "34-26",
      runDifferential: "+29",
      nextOpponent: "Boquete Bombers",
      nextSeriesDate: "Aug 10",
      homeAway: "Away",
      gameCount: 3,
      refreshedAt: "Aug 10",
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
      record: "21-12",
      runDifferential: "+41",
      nextOpponent: "Crystal Sky Chanticleers",
      nextSeriesDate: "Aug 10",
      homeAway: "Away",
      gameCount: 3,
      refreshedAt: "Aug 10",
    },
  },
];

export default function App() {
  const [activeView, setActiveView] = useState("StratHome");
  const [selectedArtistForIntelligence, setSelectedArtistForIntelligence] = useState("Billie Holiday");
  const [queryWorkbenchArtist, setQueryWorkbenchArtist] = useState("");
  const [stratTeamData, setStratTeamData] = useState({});
  const [stratTeamStatus, setStratTeamStatus] = useState({});
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

  const refreshAllStratTeams = () => {
    ACTIVE_STRAT_TEAMS.forEach((team) => {
      refreshStratTeam(team.teamId);
    });

    setStratActionMessage(
      "Refreshing current team information from Strat365."
    );
  };

  const updateUpcomingSeries = (team) => {
    refreshStratTeam(team.teamId);

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
      refreshStratTeam(team.teamId);
    });
  }, []);

  const navSections = [
    {
      title: "Operations",
      groups: [
        {
          title: "StratOperations",
          items: [
            ["StratHome", "Active Teams"],
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

            <h2 className="mt-2 text-3xl font-black tracking-tight">
              Active Teams
            </h2>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              Current teams, current position, and what comes next.
              The underlying BIE machinery stays out of the way until you need it.
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

      <section className="grid gap-5 xl:grid-cols-2">
        {ACTIVE_STRAT_TEAMS.map((team) => {
          const live = stratTeamData[team.teamId];
          const liveStatus =
            stratTeamStatus[team.teamId] || "loading";

          return (
            <article
              key={team.teamId}
              className="overflow-hidden rounded-2xl border border-slate-200 bg-white/95 shadow-sm dark:border-slate-800 dark:bg-slate-900/90"
            >
              <div className="border-b border-slate-200 p-5 dark:border-slate-800">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                      {team.season} · League {team.leagueId}
                    </p>

                    <h3 className="mt-2 text-2xl font-black">
                      {team.teamName}
                    </h3>
                  </div>

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
                        ? "BIE snapshot"
                        : "Refreshing"}
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Record
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {live?.record || team.bie.record}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Run Diff
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {team.bie.runDifferential}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Roster
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {live
                        ? live.hitterCount + live.pitcherCount
                        : "—"}
                    </p>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950/60">
                    <p className="text-xs font-semibold text-slate-500">
                      Cash
                    </p>
                    <p className="mt-1 text-xl font-black">
                      {live?.cashAvailable || "—"}
                    </p>
                  </div>
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

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="text-xs font-semibold text-slate-500">
                      Ballpark
                    </p>
                    <p className="mt-1 font-bold">
                      {live?.homeBallpark || "Loading…"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                    <p className="text-xs font-semibold text-slate-500">
                      BIE snapshot
                    </p>
                    <p className="mt-1 font-bold">
                      {team.bie.refreshedAt}
                    </p>
                  </div>
                </div>

                {liveStatus === "error" && (
                  <p className="mt-3 text-xs font-semibold text-amber-700 dark:text-amber-300">
                    Live Strat data is unavailable. The latest BIE snapshot
                    remains visible.
                  </p>
                )}

                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => updateUpcomingSeries(team)}
                    className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-blue-500"
                  >
                    Update Upcoming Series
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
    <div className={`min-h-screen transition-colors duration-200 ${isDark ? "bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-slate-100" : "bg-gradient-to-br from-slate-100 via-slate-50 to-blue-50 text-slate-900"}`}>
      <header className="bg-slate-950 text-white border-b border-slate-800 shadow-sm">
        <div className="px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Defending Sisyphus
            </h1>
            <p className="text-xs text-slate-400 mt-1">
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
              className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:bg-slate-800 hover:text-white"
            >
              {isDark ? "Light Mode" : "Dark Mode"}
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className={`w-64 backdrop-blur border-r p-4 space-y-8 min-h-screen shadow-sm transition-colors duration-200 ${isDark ? "bg-slate-950/85 border-slate-800" : "bg-white/85 border-slate-200"}`}>
          {navSections.map((section) => (
            <div key={section.title} className="space-y-3">
              <div className={`text-[11px] font-black uppercase tracking-[0.18em] border-b pb-2 ${isDark ? "text-slate-300 border-slate-700/60" : "text-slate-500 border-slate-300/70"}`}>
                {section.title}
              </div>

              {section.groups.map((group) => (
                <details
                  key={group.title}
                  open={group.title !== "Administration"}
                  className={`group rounded-xl px-2 py-2 transition-colors ${isDark ? "hover:bg-slate-900/70" : "hover:bg-slate-50/90"}`}
                >
                  <summary className={`mb-2 cursor-pointer list-none text-[10px] font-bold uppercase tracking-[0.16em] transition-colors ${isDark ? "text-slate-500 hover:text-slate-300" : "text-slate-400 hover:text-slate-600"}`}>
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
