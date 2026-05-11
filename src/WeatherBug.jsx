import React, { useEffect, useState } from "react";

const NAPERVILLE_60565 = {
  lat: 41.7476,
  lon: -88.1658,
};

function weatherEmoji(forecast = "") {
  const text = forecast.toLowerCase();

  if (text.includes("thunder")) return "⛈️";
  if (text.includes("rain") || text.includes("showers")) return "🌧️";
  if (text.includes("snow")) return "❄️";
  if (text.includes("cloud")) return "☁️";
  if (text.includes("sun") || text.includes("clear")) return "☀️";
  if (text.includes("fog")) return "🌫️";

  return "🌤️";
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
    <div className="bg-white border rounded p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-bold">60565 Weather</h2>
          <p className="text-xs text-slate-500">Naperville · 3-day forecast</p>
        </div>
        <div className="text-2xl">🌦️</div>
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
              <div className="text-3xl my-2">{weatherEmoji(day.shortForecast)}</div>
              <div className="text-xl font-bold">
                {day.temperature}°{day.temperatureUnit}
              </div>
              <div className="text-xs text-slate-600 mt-1">
                {day.shortForecast}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}