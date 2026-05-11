import React, { useState } from "react";
import CalendarView from "./CalendarView";
import LineupAnalyzer from "./LineupAnalyzer";
import PitchingAnalyzer from "./PitchingAnalyzer";
import MatchupAnalyzer from "./MatchupAnalyzer";
import FinanceView from "./FinanceView";
import SeriesPlanner from "./SeriesPlanner";
import LeagueManager from "./LeagueManager";
import WeatherBug from "./WeatherBug";
import NewsView from "./NewsView";

function PlaceholderPage({ title }) {
  return (
    <div className="bg-white p-6 rounded border">
      <h1 className="text-2xl font-bold mb-2">{title}</h1>
      <p className="text-sm text-slate-500">
        This section is ready to build next.
      </p>
    </div>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState("Lineup");

  const navButton = (view, label) => (
    <button
      onClick={() => setActiveView(view)}
      className={`block w-full text-left px-3 py-2 rounded text-sm ${
        activeView === view
          ? "bg-blue-100 font-semibold text-blue-900"
          : "hover:bg-gray-100 text-slate-700"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="bg-slate-900 text-white p-4 font-semibold text-xl">
        Defending Sisyphus
      </div>

      <div className="flex">
        <div className="w-60 bg-white border-r p-4 space-y-5 min-h-screen">
          <div>
            <div className="text-xs font-bold uppercase text-slate-400 mb-2 tracking-wide">
              Stratomatic
            </div>

            <div className="space-y-1">
              {navButton("Lineup", "Lineup Analyzer")}
              {navButton("Pitching", "Pitching Analyzer")}
              {navButton("Matchup", "Matchup Analyzer")}
              {navButton("Series", "Series Planner")}
              {navButton("LeagueManager", "League Manager")}
            </div>
          </div>

          <div>
            <div className="text-xs font-bold uppercase text-slate-400 mb-2 tracking-wide">
              Life
            </div>

            <div className="space-y-1">
              {navButton("Calendar", "Calendar")}
              {navButton("News", "News")}
              {navButton("Finance", "Finance")}
            </div>
          </div>
        </div>

        <div className="flex-1 p-6">
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
          ) : activeView === "News" ? (
            <NewsView />
          ) : activeView === "Finance" ? (
            <FinanceView />
          ) : (
            <LineupAnalyzer />
          )}
        </div>
      </div>
    </div>
  );
}