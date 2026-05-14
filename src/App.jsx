import React, { useState } from "react";
import CalendarView from "./CalendarView";
import LineupAnalyzer from "./LineupAnalyzer";
import PitchingAnalyzer from "./PitchingAnalyzer";
import MatchupAnalyzer from "./MatchupAnalyzer";
import FinanceView from "./FinanceView";
import SeriesPlanner from "./SeriesPlanner";
import LeagueManager from "./LeagueManager";
import OpponentManager from "./OpponentManager";
import WeatherBug from "./WeatherBug";
import NewsView from "./NewsView";
import CardImporter from "./CardImporter";

export default function App() {
  const [activeView, setActiveView] = useState("Lineup");

  const navButton = (view, label) => (
    <button
      onClick={() => setActiveView(view)}
      className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition ${
        activeView === view
          ? "bg-slate-900 text-white font-semibold shadow-sm"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-blue-50 text-slate-900">
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

          <div className="text-xs text-slate-400">
            Strat · Finance · News · Calendar
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="w-64 bg-white/80 backdrop-blur border-r border-slate-200 p-4 space-y-6 min-h-screen shadow-sm">
          <div>
            <div className="text-xs font-bold uppercase text-slate-400 mb-2 tracking-widest">
              Stratomatic
            </div>

            <div className="space-y-1">
  {navButton("Lineup", "Lineup Analyzer")}
  {navButton("Pitching", "Pitching Analyzer")}
  {navButton("Matchup", "Matchup Analyzer")}
  {navButton("Series", "Series Planner")}
  {navButton("LeagueManager", "League Manager")}
  {navButton("Opponents", "Opponent Manager")}
  {navButton("Cards", "Card Importer")}
</div>
          </div>

          <div>
            <div className="text-xs font-bold uppercase text-slate-400 mb-2 tracking-widest">
              Life
            </div>

            <div className="space-y-1">
              {navButton("Calendar", "Calendar")}
              {navButton("News", "News")}
              {navButton("Finance", "Finance")}
            </div>
          </div>
        </aside>

        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {activeView === "Calendar" ? (
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
            ) : (
              <LineupAnalyzer />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}