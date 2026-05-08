import React, { useEffect, useState } from "react";

export default function CalendarView() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("Loading events...");

  useEffect(() => {
    fetch("http://localhost:4000/api/calendar/events")
      .then((res) => res.json())
      .then((data) => {
        setEvents(data);
        setStatus("");
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setStatus("Could not load calendar events. Make sure backend is running.");
      });
  }, []);

  const today = new Date().toISOString().split("T")[0];

  const nextEvent = events[0];

  const todaysEvents = events.filter((event) => event.date === today);

  const getIcon = (title) => {
    const lower = title.toLowerCase();

    if (lower.includes("flight")) return "✈️";
    if (lower.includes("cubs") || lower.includes("mets")) return "⚾";
    if (lower.includes("anniversary")) return "🎉";
    if (lower.includes("birthday")) return "🎂";
    if (lower.includes("concert") || lower.includes("slide") || lower.includes("primus")) return "🎵";

    return "📅";
  };

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-xl shadow-sm border p-5">
        <h1 className="text-2xl font-bold mb-1">Calendar</h1>
        <p className="text-sm text-slate-500">
          Google Calendar events from your backend.
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <div className="text-xs uppercase text-blue-600 font-bold mb-1">
          Next Event
        </div>

        {nextEvent ? (
          <div>
            <div className="text-xl font-bold">
              {getIcon(nextEvent.title)} {nextEvent.title}
            </div>
            <div className="text-sm text-slate-600">
              {nextEvent.date} {nextEvent.time && `at ${nextEvent.time}`}
            </div>
          </div>
        ) : (
          <div className="text-sm text-slate-500">No upcoming events.</div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-5">
        <h2 className="text-lg font-bold mb-3">Today</h2>

        {todaysEvents.length === 0 ? (
          <div className="text-sm text-slate-500">No events today.</div>
        ) : (
          <div className="space-y-2">
            {todaysEvents.map((event) => (
              <div key={event.id} className="border rounded-lg p-3">
                {getIcon(event.title)} {event.time || "All day"} — {event.title}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-5">
        <h2 className="text-lg font-bold mb-3">Upcoming Events</h2>

        {status && <div className="text-sm text-slate-500">{status}</div>}

        {!status && events.length === 0 && (
          <div className="text-sm text-slate-500">No upcoming events found.</div>
        )}

        <div className="space-y-2">
          {events.map((event) => (
            <div
              key={event.id}
              className="border rounded-lg p-3 flex items-center justify-between hover:bg-slate-50"
            >
              <div>
                <div className="font-semibold">
                  {getIcon(event.title)} {event.title}
                </div>
                <div className="text-sm text-slate-500">
                  {event.date} {event.time && `at ${event.time}`} · {event.category}
                </div>
              </div>

              <span className="text-xs bg-slate-100 px-2 py-1 rounded">
                {event.source}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}