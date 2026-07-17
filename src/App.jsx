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
import MusicDashboard from "./MusicDashboard";
import BooksView from "./BooksView";
import NotesView from "./NotesView";
import QueryWorkbench from "./QueryWorkbench";
import ArtistIntelligence from "./ArtistIntelligence";
import PlaylistIntelligence from "./PlaylistIntelligence";
import ScrollToTopButton from "./ScrollToTopButton";
export default function App() {
  const [activeView, setActiveView] = useState("IntelligenceHome");
  const [selectedArtistForIntelligence, setSelectedArtistForIntelligence] = useState("Billie Holiday");
  const [queryWorkbenchArtist, setQueryWorkbenchArtist] = useState("");
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
  const navSections = [
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
      title: "Strat Tools",
      groups: [
        {
          title: "Simulation",
          items: [
            ["Lineup", "Lineup Analyzer"],
            ["GameSim", "Game Simulator"],
            ["Pitching", "Pitching Analyzer"],
          ],
        },
        {
          title: "Preparation",
          items: [
            ["Series", "Series Planner"],
            ["Matchup", "Matchup Analyzer"],
            ["Opponents", "Opponent Manager"],
          ],
        },
        {
          title: "Administration",
          items: [
            ["LeagueManager", "League Manager"],
            ["CardImporter", "Card Importer"],
          ],
        },
      ],
    },
  ]

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
            onClick={() => setActiveView("Music")}
            className="rounded-xl border border-slate-300 px-4 py-3 text-left text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Music Intelligence
            <span className="block pt-1 text-xs font-medium text-slate-500">
              Open the current music intelligence workspace.
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
              Strat / Finance / News / Calendar
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
            {activeView === "MusicDashboard" ? (
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
