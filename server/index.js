import fetch from "node-fetch";
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { google } from "googleapis";
import { authorize } from "./auth.js";
import Parser from "rss-parser";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({
  path: path.join(__dirname, ".env"),
});

const app = express();
const PORT = 4000;
const parser = new Parser();
const FEEDS_FILE = path.join(__dirname, "rss-feeds.json");

app.use(cors());
app.use(express.json());

const loadFeeds = () => {
  return JSON.parse(fs.readFileSync(FEEDS_FILE, "utf-8"));
};

const saveFeeds = (feeds) => {
  fs.writeFileSync(FEEDS_FILE, JSON.stringify(feeds, null, 2));
};

app.get("/", (req, res) => {
  res.send("Dashboard backend is running");
});

app.get("/api/news", async (req, res) => {
  try {
    const feeds = loadFeeds();

    const results = await Promise.all(
      feeds.map(async (feedSource) => {
        try {
          const feed = await parser.parseURL(feedSource.url);

          return (feed.items || []).slice(0, 5).map((item) => ({
            title: item.title || "Untitled",
            link: item.link || "",
            pubDate: item.pubDate || "",
            source: feedSource.name || feed.title || "RSS Feed",
            category: feedSource.category || "General",
          }));
        } catch (err) {
          console.error("RSS feed failed:", feedSource.url);
          return [];
        }
      })
    );

    const stories = results
      .flat()
      .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
      .slice(0, 20);

    res.json(stories);
  } catch (error) {
    console.error("News error:", error);
    res.status(500).json({ error: "Failed to load news feeds" });
  }
});

app.get("/api/news/feeds", (req, res) => {
  try {
    res.json(loadFeeds());
  } catch (error) {
    console.error("Feed list error:", error);
    res.status(500).json({ error: "Failed to load feeds" });
  }
});

app.post("/api/news/feeds", (req, res) => {
  try {
    const feeds = loadFeeds();
    const newFeed = req.body.url;

    if (!newFeed) {
      return res.status(400).json({ error: "URL required" });
    }

    if (!feeds.includes(newFeed)) {
      feeds.push(newFeed);
      saveFeeds(feeds);
    }

    res.json(feeds);
  } catch (error) {
    console.error("Feed save error:", error);
    res.status(500).json({ error: "Failed to save feed" });
  }
});

app.delete("/api/news/feeds/:index", (req, res) => {
  try {
    const feeds = loadFeeds();
    const index = Number(req.params.index);

    if (Number.isNaN(index) || index < 0 || index >= feeds.length) {
      return res.status(400).json({ error: "Invalid feed index" });
    }

    feeds.splice(index, 1);
    saveFeeds(feeds);

    res.json(feeds);
  } catch (error) {
    console.error("Feed delete error:", error);
    res.status(500).json({ error: "Failed to delete feed" });
  }
});


app.get("/api/quotes", async (req, res) => {
  try {
    const apiKey = process.env.FINNHUB_API_KEY;

    if (!apiKey) {
      return res.status(500).json({
        error: "Missing FINNHUB_API_KEY in .env",
      });
    }

    const symbols = String(req.query.symbols || "")
      .split(",")
      .map((symbol) => symbol.trim().toUpperCase())
      .filter(Boolean);

    if (!symbols.length) {
      return res.status(400).json({
        error:
          "Missing symbols query parameter. Example: /api/quotes?symbols=AAPL,QQQ,SMH",
      });
    }

    const uniqueSymbols = [...new Set(symbols)];

    const quoteResults = await Promise.all(
      uniqueSymbols.map(async (symbol) => {
        try {
          const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(
            symbol
          )}&token=${apiKey}`;

          const response = await fetch(url);

          if (!response.ok) {
            throw new Error(`Finnhub error ${response.status}`);
          }

          const data = await response.json();

          return {
            symbol,
            price: data.c ?? null,
            previousClose: data.pc ?? null,
            change: data.d ?? null,
            changePercent: data.dp ?? null,
            high: data.h ?? null,
            low: data.l ?? null,
            open: data.o ?? null,
            timestamp: data.t ?? null,
            error: null,
          };
        } catch (error) {
          console.error(`Quote failed for ${symbol}:`, error.message);

          return {
            symbol,
            price: null,
            previousClose: null,
            change: null,
            changePercent: null,
            high: null,
            low: null,
            open: null,
            timestamp: null,
            error: "Failed to load quote",
          };
        }
      })
    );

    res.json({
      source: "Finnhub",
      quotes: quoteResults,
    });
  } catch (error) {
    console.error("Quotes error:", error);
    res.status(500).json({ error: "Failed to load quotes" });
  }
});

app.get("/api/calendar/events", async (req, res) => {
  try {
    const auth = await authorize();
    const calendar = google.calendar({ version: "v3", auth });

    const calendarListResponse = await calendar.calendarList.list();

const calendars = calendarListResponse.data.items.filter((cal) => {
  const name = (cal.summary || "").toLowerCase();

  return (
    !name.includes("sunrise") &&
    !name.includes("sunset") &&
    !name.includes("vivo's summer schedule")
  );
});
    const eventRequests = calendars.map(async (cal) => {
      const response = await calendar.events.list({
        calendarId: cal.id,
        timeMin: new Date().toISOString(),
        maxResults: 20,
        singleEvents: true,
        orderBy: "startTime",
      });

      return (response.data.items || []).map((event) => {
        const start = event.start?.dateTime || event.start?.date || "";
        const end = event.end?.dateTime || event.end?.date || "";

        return {
          id: `${cal.id}-${event.id}`,
          calendarId: cal.id,
          source: cal.summary || "Google Calendar",
          title: event.summary || "Untitled event",
          date: start.split("T")[0],
          time: start.includes("T") ? start.split("T")[1].slice(0, 5) : "",
          endDate: end.split("T")[0],
          endTime: end.includes("T") ? end.split("T")[1].slice(0, 5) : "",
          category: cal.primary
            ? "Primary Calendar"
            : cal.summary || "Google Calendar",
        };
      });
    });

    const eventsByCalendar = await Promise.all(eventRequests);

    const events = eventsByCalendar
      .flat()
      .sort((a, b) => {
        const aTime = `${a.date}T${a.time || "00:00"}`;
        const bTime = `${b.date}T${b.time || "00:00"}`;
        return new Date(aTime) - new Date(bTime);
      })
      .slice(0, 25);

    res.json(events);
  } catch (error) {
    console.error("Google Calendar error:", error);
    res.status(500).json({ error: "Failed to load Google Calendar events" });
  }
});

app.get("/api/calendar/list", async (req, res) => {
  try {
    const auth = await authorize();
    const calendar = google.calendar({ version: "v3", auth });

    const response = await calendar.calendarList.list();

    const calendars = response.data.items.map((cal) => ({
      id: cal.id,
      summary: cal.summary,
      primary: cal.primary || false,
    }));

    res.json(calendars);
  } catch (error) {
    console.error("Calendar list error:", error);
    res.status(500).json({ error: "Failed to load calendar list" });
  }
});

app.get("/api/weather/forecast", async (req, res) => {
  try {
    const latitude = 41.7508;
    const longitude = -88.1535;

    const url =
      `https://api.open-meteo.com/v1/forecast` +
      `?latitude=${latitude}` +
      `&longitude=${longitude}` +
      `&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max` +
      `&temperature_unit=fahrenheit` +
      `&timezone=America%2FChicago` +
      `&forecast_days=3`;

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status}`);
    }

    const data = await response.json();

    const weatherCodeLabels = {
      0: "Clear",
      1: "Mostly clear",
      2: "Partly cloudy",
      3: "Cloudy",
      45: "Fog",
      48: "Rime fog",
      51: "Light drizzle",
      53: "Drizzle",
      55: "Heavy drizzle",
      61: "Light rain",
      63: "Rain",
      65: "Heavy rain",
      71: "Light snow",
      73: "Snow",
      75: "Heavy snow",
      80: "Rain showers",
      81: "Rain showers",
      82: "Heavy showers",
      95: "Thunderstorms",
    };

    const forecast = data.daily.time.map((date, index) => ({
      date,
      condition: weatherCodeLabels[data.daily.weather_code[index]] || "Weather",
      high: Math.round(data.daily.temperature_2m_max[index]),
      low: Math.round(data.daily.temperature_2m_min[index]),
      precipChance: data.daily.precipitation_probability_max[index] ?? 0,
    }));

    res.json({
      location: "Naperville, IL 60565",
      forecast,
    });
  } catch (error) {
    console.error("Weather error:", error);
    res.status(500).json({ error: "Failed to load weather forecast" });
  }
});

app.get("/api/test", (req, res) => {
  res.json({ message: "test route works" });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});