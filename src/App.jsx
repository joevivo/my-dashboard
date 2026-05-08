import React, { useState } from "react";
import CalendarView from "./CalendarView";
import LineupAnalyzer from "./LineupAnalyzer";
import PitchingAnalyzer from "./PitchingAnalyzer";
import LeagueManager from "./LeagueManager";

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
            <CalendarView />
          ) : activeView === "Pitching" ? (
            <PitchingAnalyzer />
          ) : activeView === "LeagueManager" ? (
            <LeagueManager />
          ) : activeView === "News" ? (
            <PlaceholderPage title="News" />
          ) : activeView === "Finance" ? (
            <PlaceholderPage title="Finance" />
          ) : (
            <LineupAnalyzer />
          )}
        </div>
      </div>
    </div>
  );
}