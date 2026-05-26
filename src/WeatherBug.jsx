import React, { useEffect, useState } from "react";

const NAPERVILLE_60565 = {
  lat: 41.7476,
  lon: -88.1658,
};

function weatherBadge(forecast = "") {
  const text = forecast.toLowerCase();

  if (text.includes("thunder")) return "Thunderstorms";
  if (text.includes("rain") || text.includes("showers")) return "Rain";
  if (text.includes("snow")) return "Snow";
  if (text.includes("fog")) return "Fog";
  if (text.includes("mostly sunny")) return "Mostly Sunny";
  if (text.includes("partly sunny")) return "Partly Sunny";
  if (text.includes("sunny")) return "Sunny";
  if (text.includes("clear")) return "Clear";
  if (text.includes("cloud")) return "Cloudy";

  return forecast || "Weather";
}
function getPrecipChance(day) {
  const value = day?.probabilityOfPrecipitation?.value;

  if (value === null || value === undefined) {
    return "—";
  }

  return `${value}%`;
}

function getWindSummary(day) {
  const speed = day?.windSpeed || "";
  const direction = day?.windDirection || "";

  if (!speed && !direction) {
    return "—";
  }

  return `${speed} ${direction}`.trim();
}

export default function WeatherBug() {
  const [days, setDays] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWeather() {
      try {
        const pointRes = await fetch(
          `https://api.weather.gov/points/${NAPERVILLE_60565.lat},${NAPERVILLE_60565.lon}`
        );

        if (!pointRes.ok) throw new Error("Could not load weather point data.");

        const pointData = await pointRes.json();
        const forecastUrl = pointData.properties.forecast;

        const forecastRes = await fetch(forecastUrl);

        if (!forecastRes.ok) throw new Error("Could not load forecast.");

        const forecastData = await forecastRes.json();

        const daytimePeriods = forecastData.properties.periods
          .filter((period) => period.isDaytime)
          .slice(0, 3);

        setDays(daytimePeriods);
      } catch (err) {
        setError(err.message);
      }
    }

    loadWeather();
  }, []);

  return (
    <div className="dashboard-panel p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-bold">60565 Weather</h2>
          <p className="text-xs text-slate-500">Naperville · 3-day forecast</p>
        </div>

        <div className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Weather</div>
      </div>

      {error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : days.length === 0 ? (
        <p className="text-sm text-slate-500">Loading weather...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {days.map((day) => (
            <div key={day.number} className="rounded border bg-slate-50 p-3">
              <div className="text-sm font-semibold">{day.name}</div>

              <div className="my-2 inline-flex rounded-full border border-slate-200 bg-white/70 px-3 py-1 text-xs font-bold uppercase tracking-wide text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                {weatherBadge(day.shortForecast)}
              </div>

              <div className="text-xl font-bold">
                {day.temperature}°{day.temperatureUnit}
              </div>

              <div className="text-xs text-slate-600 mt-1">
                {day.shortForecast}
              </div>

              <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                <div className="rounded border border-slate-200 bg-white/60 p-2 dark:border-slate-700 dark:bg-slate-800/70">
                  <div className="uppercase tracking-wide text-slate-400 font-bold">
                    Precip
                  </div>
                  <div className="font-semibold text-slate-700">
                    {getPrecipChance(day)}
                  </div>
                </div>

                <div className="rounded border border-slate-200 bg-white/60 p-2 dark:border-slate-700 dark:bg-slate-800/70">
                  <div className="uppercase tracking-wide text-slate-400 font-bold">
                    Wind
                  </div>
                  <div className="font-semibold text-slate-700">
                    {getWindSummary(day)}
                  </div>
                </div>
              </div>

              {day.detailedForecast && (
                <div className="mt-3 border-t border-slate-200 pt-3 text-xs text-slate-500 leading-relaxed">
                  {day.detailedForecast}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

