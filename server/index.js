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
import { execFile, execFileSync } from "child_process";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ARTIST_FAMILIES_FILE = path.join(
  __dirname,
  "..",
  "data",
  "music",
  "curated",
  "artistFamilies.json"
);

function loadArtistFamilies() {
  try {

    const raw = fs.readFileSync(ARTIST_FAMILIES_FILE, "utf8");
    const families = JSON.parse(raw);


    return families;
  } catch (error) {
    console.error("Failed to load artist families:", error.message);
    return [];
  }
}

const ARTIST_ALIASES = {
  "h sker d": "husker du",
  "h?sker d?": "husker du",
  "husker du": "husker du",
  "love rockets": "love and rockets",
  "love and rockets": "love and rockets",
  "the scorpions": "scorpions",
  "scorpions": "scorpions",
  "the eagles": "eagles",
  "eagles": "eagles",
};

function normalizeArtistKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function stripLeadingArticle(value) {
  return String(value || "").replace(/^the\s+/, "");
}

function canonicalArtistKey(value) {
  const normalized = normalizeArtistKey(value);
  const aliased = ARTIST_ALIASES[normalized] || normalized;
  const stripped = stripLeadingArticle(aliased);
  return ARTIST_ALIASES[stripped] || stripped;
}

function resolveArtistFamily(artistName) {
  const families = loadArtistFamilies();
  const targetKey = canonicalArtistKey(artistName);

  return (
    families.find((family) =>
      family.members.some((member) => canonicalArtistKey(member) === targetKey)
    ) || null
  );
}

dotenv.config({
  path: path.join(__dirname, ".env"),
});


function buildFamilyMetrics(family, runArtistQuery) {
  if (!family || !Array.isArray(family.members)) return null;

  const metrics = {
    familyName: family.familyName,
    primaryArtist: family.primaryArtist,
    actualPlays: 0,
    actualSkips: 0,
    hoursListened: 0,
    listeningDurationMs: 0,
    libraryEvidenceRecords: 0,
    yearsActive: 0,
    firstPlayedDate: null,
    latestPlayedDate: null,
    membersMatched: [],
  };

  const seenCanonicalArtists = new Set();

  for (const member of family.members) {
    const memberResult = runArtistQuery(member);
    if (!memberResult || memberResult.error) continue;

    const canonicalArtist = canonicalArtistKey(memberResult.artist || member);
    if (seenCanonicalArtists.has(canonicalArtist)) continue;
    seenCanonicalArtists.add(canonicalArtist);

    metrics.actualPlays += Number(memberResult.actualPlays || 0);
    metrics.actualSkips += Number(memberResult.actualSkips || 0);
    metrics.hoursListened += Number(memberResult.hoursListened || 0);
    metrics.listeningDurationMs += Number(memberResult.listeningDurationMs || 0);
    metrics.libraryEvidenceRecords += Number(memberResult.libraryEvidenceRecords || 0);

    if (memberResult.firstPlayedDate) {
      if (!metrics.firstPlayedDate || memberResult.firstPlayedDate < metrics.firstPlayedDate) {
        metrics.firstPlayedDate = memberResult.firstPlayedDate;
      }
    }

    if (memberResult.latestPlayedDate) {
      if (!metrics.latestPlayedDate || memberResult.latestPlayedDate > metrics.latestPlayedDate) {
        metrics.latestPlayedDate = memberResult.latestPlayedDate;
      }
    }

    metrics.membersMatched.push({
      artist: memberResult.artist || member,
      query: member,
      actualPlays: Number(memberResult.actualPlays || 0),
      actualSkips: Number(memberResult.actualSkips || 0),
      hoursListened: Number(memberResult.hoursListened || 0),
      libraryEvidenceRecords: Number(memberResult.libraryEvidenceRecords || 0),
      yearsActive: Number(memberResult.yearsActive || 0),
      firstPlayedDate: memberResult.firstPlayedDate || null,
      latestPlayedDate: memberResult.latestPlayedDate || null,
      timeline: Array.isArray(memberResult.timeline) ? memberResult.timeline : [],
    });
  }

  const activeYears = new Set();
  for (const member of metrics.membersMatched) {
    for (const row of member.timeline || []) {
      if (row && row.year) activeYears.add(String(row.year));
    }
  }

  metrics.yearsActive = activeYears.size;
  metrics.hoursListened = Number(metrics.hoursListened.toFixed(1));
  metrics.familyAmplificationFactor =
    metrics.membersMatched.length && Number(metrics.membersMatched[0].actualPlays || 0)
      ? Number((metrics.actualPlays / Number(metrics.membersMatched[0].actualPlays || 0)).toFixed(2))
      : null;

  return metrics;
}
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
    const { name, url, category } = req.body;

    if (!url) {
      return res.status(400).json({ error: "URL required" });
    }

    const newFeed = {
      name: name?.trim() || "RSS Feed",
      url: url.trim(),
      category: category?.trim() || "General",
    };

    const alreadyExists = feeds.some((feed) => {
      if (typeof feed === "string") {
        return feed === newFeed.url;
      }

      return feed.url === newFeed.url;
    });

    if (!alreadyExists) {
      feeds.push(newFeed);
      saveFeeds(feeds);
    }

    res.json(feeds);
  } catch (error) {
    console.error("Feed save error:", error);
    res.status(500).json({ error: "Failed to save feed" });
  }
});

app.put("/api/news/feeds/:index", (req, res) => {
  try {
    const feeds = loadFeeds();
    const index = Number(req.params.index);
    const { name, url, category } = req.body;

    if (Number.isNaN(index) || index < 0 || index >= feeds.length) {
      return res.status(400).json({ error: "Invalid feed index" });
    }

    if (!url) {
      return res.status(400).json({ error: "URL required" });
    }

    feeds[index] = {
      name: name?.trim() || "RSS Feed",
      url: url.trim(),
      category: category?.trim() || "General",
    };

    saveFeeds(feeds);

    res.json(feeds);
  } catch (error) {
    console.error("Feed update error:", error);
    res.status(500).json({ error: "Failed to update feed" });
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
        const manualQuotes = {
  CASH: {
    price: 1,
    previousClose: 1,
    change: 0,
    changePercent: 0,
    high: 1,
    low: 1,
    open: 1,
    timestamp: null,
    error: null,
  },
  VMFXX: {
    price: 1,
    previousClose: 1,
    change: 0,
    changePercent: 0,
    high: 1,
    low: 1,
    open: 1,
    timestamp: null,
    error: null,
  },
};

if (manualQuotes[symbol]) {
  return {
    symbol,
    ...manualQuotes[symbol],
  };
}
        try {
          const manualQuotes = {
  CASH: {
    price: 1,
    previousClose: 1,
    change: 0,
    changePercent: 0,
    high: 1,
    low: 1,
    open: 1,
    timestamp: null,
    error: null,
  },
  VMFXX: {
    price: 1,
    previousClose: 1,
    change: 0,
    changePercent: 0,
    high: 1,
    low: 1,
    open: 1,
    timestamp: null,
    error: null,
  },
};

if (manualQuotes[symbol]) {
  return {
    symbol,
    ...manualQuotes[symbol],
  };
}
          const url = `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(
            symbol
          )}&token=${apiKey}`;

          const response = await fetch(url);

          if (!response.ok) {
            throw new Error(`Finnhub error ${response.status}`);
          }

        const data = await response.json();

const hasQuoteData =
  Number(data.c) > 0 ||
  Number(data.pc) > 0 ||
  Number(data.h) > 0 ||
  Number(data.l) > 0 ||
  Number(data.o) > 0;

if (!hasQuoteData) {
  return {
    symbol,
    price: null,
    previousClose: null,
    change: null,
    changePercent: null,
    high: null,
    low: null,
    open: null,
    timestamp: data.t ?? null,
    error: "No quote data returned",
  };
}

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


function cleanText(value = "") {
  return value
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function extractField(html, label) {
  const regex = new RegExp(`<b>${label}:<\\/b>\\s*([^<]+|<a[^>]*>[^<]+<\\/a>)`, "i");
  const match = html.match(regex);
  return match ? cleanText(match[1]) : "";
}

function parseRosterRows(html) {
  const rows = [...html.matchAll(/<tr class="(?:odd|even)">([\s\S]*?)<\/tr>/g)];

  return rows
    .map((rowMatch) => {
      const row = rowMatch[1];
      const fields = {};

      for (const cellMatch of row.matchAll(/<td([^>]*)name="([^"]+)"([^>]*)>([\s\S]*?)<\/td>/g)) {
        const [, beforeAttrs, name, afterAttrs, cellHtml] = cellMatch;
        const attrs = `${beforeAttrs} ${afterAttrs}`;
        const titleMatch = attrs.match(/title="([^"]+)"/);

        fields[name] = cleanText(cellHtml);

        if (titleMatch) {
          fields[`${name}Detail`] = cleanText(titleMatch[1]);
        }
      }

      if (!fields.name) return null;

      const isHitter = Boolean(fields.bats || fields.pos || fields.def || fields.ba || fields.obp || fields.slg);

      const common = {
        name: fields.name,
        balance: fields.bal || "",
        price: fields.price || "",
      };

      if (!isHitter) {
        return {
          type: "pitcher",
          ...common,
          innings: fields.h || "",
          hitsAllowed: fields.h || "",
          hrAllowed: fields.hr || "",
          walksAllowed: fields.bb || "",
          strikeouts: fields.so || "",
        };
      }

      return {
        type: "hitter",
        ...common,
        bats: fields.bats || "",
        position: fields.pos || "",
        defense: fields.def || "",
        defenseDetail: fields.posDetail || fields.defDetail || "",
        ab: fields.ab || "",
        r: fields.r || "",
        h: fields.h || "",
        doubles: fields["2b"] || "",
        triples: fields["3b"] || "",
        hr: fields.hr || "",
        rbi: fields.rbi || "",
        bb: fields.bb || "",
        so: fields.so || "",
        hbp: fields.hbp || "",
        sb: fields.sb || "",
        cs: fields.cs || "",
        stealing: fields.steal || "",
        stealingDetail: fields.stealDetail || "",
        running: fields.run || "",
        ba: fields.ba || "",
        obp: fields.obp || "",
        slg: fields.slg || "",
        injury: fields.inj || "",
      };
    })
    .filter(Boolean);
}

app.get("/api/strat/team/:teamId", async (req, res) => {
  try {
    const { teamId } = req.params;

    if (!/^\d+$/.test(teamId)) {
      return res.status(400).json({ error: "Invalid team ID" });
    }

    const url = `https://365.strat-o-matic.com/team/${teamId}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Strat fetch failed: ${response.status}`);
    }

    const html = await response.text();
    const roster = parseRosterRows(html);
    const pitchers = roster.filter((player) => player.type === "pitcher");
    const hitters = roster.filter((player) => player.type === "hitter");

    res.json({
      source: url,
      importedAt: new Date().toISOString(),
      teamId,
      owner: extractField(html, "Owner"),
      manager: extractField(html, "Manager"),
      record: extractField(html, "Record"),
      homeBallpark: extractField(html, "Home Ballpark"),
      initialSalaryCap: extractField(html, "Initial Salary Cap"),
      totalCurrentValue: extractField(html, "Total Current Value"),
      rosterValue: extractField(html, "Roster Value"),
      cashAvailable: extractField(html, "Cash Available"),
      pitcherCount: pitchers.length,
      hitterCount: hitters.length,
      pitchers,
      hitters,
      roster,
    });
  } catch (error) {
    console.error("Strat team import error:", error);
    res.status(500).json({ error: "Failed to import Strat team" });
  }
});


function parseDefensePositions(defenseDetail = "") {
  return defenseDetail
    .split("/")
    .map((part) => part.trim())
    .map((part) => {
      const match = part.match(/^([a-z0-9]+)-(\d)/i);
      if (!match) return null;

      return {
        position: match[1].toUpperCase(),
        rating: Number(match[2]),
        raw: part,
      };
    })
    .filter(Boolean);
}

function parsePriceMillions(price = "") {
  const cleaned = String(price).replace("$", "").replace("M", "").trim();
  const number = Number(cleaned);
  return Number.isFinite(number) ? number : 0;
}

function parseRunning(running = "") {
  const match = String(running).match(/1-(\d+)/);
  return match ? Number(match[1]) : 0;
}

function analyzeStratTeam(team) {
  const hitters = team.hitters || [];
  const pitchers = team.pitchers || [];

  const positionCoverage = {};
  const positionQuality = {};
  const playerCoverage = hitters.map((player) => {
    const positions = parseDefensePositions(player.defenseDetail);

    positions.forEach((pos) => {
      positionCoverage[pos.position] = (positionCoverage[pos.position] || 0) + 1;

      if (!positionQuality[pos.position]) {
        positionQuality[pos.position] = [];
      }

      positionQuality[pos.position].push({
        name: player.name,
        rating: pos.rating,
        raw: pos.raw,
      });
    });

    return {
      name: player.name,
      primaryPosition: player.position,
      defenseDetail: player.defenseDetail,
      positions,
    };
  });

  const defensiveFlags = [];

  const requireQuality = [
    { position: "C", maxRating: 2, label: "Catcher lacks a strong defensive anchor if Boone is not starting." },
    { position: "SS", maxRating: 2, label: "Shortstop coverage is acceptable only if Burleson remains healthy." },
    { position: "CF", maxRating: 2, label: "Center field has elite top-end defense but limited true backup quality." },
    { position: "2B", maxRating: 2, label: "Second base has at least one usable defensive option." },
  ];

  requireQuality.forEach((rule) => {
    const options = positionQuality[rule.position] || [];
    const hasQuality = options.some((option) => option.rating <= rule.maxRating);

    if (!hasQuality) {
      defensiveFlags.push(rule.label);
    }
  });

  const positionDepth = Object.fromEntries(
    Object.entries(positionQuality).map(([position, options]) => [
      position,
      options
        .sort((a, b) => a.rating - b.rating)
        .map((option) => `${option.name} ${option.raw}`),
    ])
  );

  const benchPower = hitters
    .filter((player) => Number(player.hr) >= 10 || Number(player.slg) >= 0.45)
    .sort((a, b) => Number(b.hr) - Number(a.hr))
    .map((player) => ({
      name: player.name,
      hr: Number(player.hr) || 0,
      slg: player.slg,
      price: player.price,
      balance: player.balance,
    }));

  const speedOptions = hitters
    .filter((player) => parseRunning(player.running) >= 15 || ["A", "AA", "AAA"].includes(player.stealing))
    .map((player) => ({
      name: player.name,
      running: player.running,
      stealing: player.stealing,
      stealingDetail: player.stealingDetail,
    }));

  const lowCostPlayers = hitters
    .filter((player) => parsePriceMillions(player.price) <= 1.1)
    .map((player) => ({
      name: player.name,
      position: player.position,
      defenseDetail: player.defenseDetail,
      price: player.price,
      obp: player.obp,
      slg: player.slg,
      hr: player.hr,
      running: player.running,
      stealing: player.stealing,
    }));

  const redundancies = Object.entries(positionCoverage)
    .filter(([position, count]) => count >= 4 && !["1B", "OF"].includes(position))
    .map(([position, count]) => ({
      position,
      count,
      note: `${position} has ${count} rostered coverage options.`,
    }));

  const oneBaseOptions = positionQuality["1B"] || [];
  const centerFieldOptions = positionQuality["CF"] || [];
  const shortstopOptions = positionQuality["SS"] || [];

  const recommendations = [];

  if (oneBaseOptions.length < 2) {
    recommendations.push("Add a credible backup first baseman.");
  } else {
    const bestBackup1b = oneBaseOptions
      .filter((option) => !option.name.includes("Money"))
      .sort((a, b) => a.rating - b.rating)[0];

    if (!bestBackup1b || bestBackup1b.rating >= 4) {
      recommendations.push("Backup first base coverage exists but is weak; a 1B-2 or 1B-3 bench bat would help.");
    }
  }

  if (centerFieldOptions.filter((option) => option.rating <= 3).length < 2) {
    recommendations.push("Preserve at least one backup CF option; Murphy is the only elite CF.");
  }

  if (shortstopOptions.filter((option) => option.rating <= 3).length < 2) {
    recommendations.push("Shortstop depth behind Burleson is thin defensively.");
  }

  if (benchPower.length < 4) {
    recommendations.push("Bench power is light for Tiger Stadium; prioritize cheap HR card shape when possible.");
  }

  if (lowCostPlayers.length) {
    recommendations.push("Review low-cost bench players first for upgrades rather than cutting core defensive coverage.");
  }

  return {
    teamId: team.teamId,
    homeBallpark: team.homeBallpark,
    rosterValue: team.rosterValue,
    cashAvailable: team.cashAvailable,
    pitcherCount: pitchers.length,
    hitterCount: hitters.length,
    positionCoverage,
    positionDepth,
    defensiveFlags,
    benchPower,
    speedOptions,
    lowCostPlayers,
    redundancies,
    recommendations,
  };
}

app.get("/api/strat/team-analysis/:teamId", async (req, res) => {
  try {
    const { teamId } = req.params;

    if (!/^\d+$/.test(teamId)) {
      return res.status(400).json({ error: "Invalid team ID" });
    }

    const url = `https://365.strat-o-matic.com/team/${teamId}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Strat fetch failed: ${response.status}`);
    }

    const html = await response.text();
    const roster = parseRosterRows(html);
    const pitchers = roster.filter((player) => player.type === "pitcher");
    const hitters = roster.filter((player) => player.type === "hitter");

    const team = {
      teamId,
      homeBallpark: extractField(html, "Home Ballpark"),
      rosterValue: extractField(html, "Roster Value"),
      cashAvailable: extractField(html, "Cash Available"),
      pitchers,
      hitters,
    };

    res.json(analyzeStratTeam(team));
  } catch (error) {
    console.error("Strat team analysis error:", error);
    res.status(500).json({ error: "Failed to analyze Strat team" });
  }
});
app.get("/api/music/time-machine", async (req, res) => {
  const { start, end } = req.query;

  if (!start || !end) {
    return res.status(400).json({
      error: "start and end query parameters are required",
    });
  }

  const scriptPath =
    "../data/music/scripts/library_range_summary.py";

  execFile(
    "python",
    [scriptPath, start, end],
    { cwd: __dirname },
    (error, stdout, stderr) => {
      if (error) {
        console.error(stderr);
        return res.status(500).json({
          error: "Failed to run time machine script",
        });
      }

      try {
  const result = JSON.parse(stdout);


  res.json(result);
} catch (parseError) {
  console.error(parseError);

  res.status(500).json({
    error: "Failed to parse time machine output",
  });
}    }
  );
});

app.get("/api/music/query/artist", async (req, res) => {
  const { name } = req.query;

  if (!name || !String(name).trim()) {
    return res.status(400).json({ error: "Artist name required" });
  }

  const scriptPath = "../data/music/scripts/artist_query_summary.py";

  execFile(
    "python",
    [scriptPath, String(name).trim()],
    {
      cwd: __dirname,
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      maxBuffer: 1024 * 1024 * 10,
    },
    (error, stdout, stderr) => {
      if (error) {
        console.error("Artist query error:", error);
        console.error(stderr);
        return res.status(500).json({
          error: "Failed to query artist",
          details: stderr || error.message,
        });
      }

      try {
        const result = JSON.parse(stdout);

          result.family =
            resolveArtistFamily(String(result.artist || name).trim()) ||
            resolveArtistFamily(String(name).trim());

          result.familyMetrics = buildFamilyMetrics(result.family, (memberName) => {
            const memberOutput = execFileSync(
              "python",
              [scriptPath, memberName],
              {
                cwd: __dirname,
                encoding: "utf8",
                env: {
                  ...process.env,
                  PYTHONIOENCODING: "utf-8",
                  PYTHONUTF8: "1",
                },
                maxBuffer: 1024 * 1024 * 10,
              }
            );

            return JSON.parse(memberOutput);
          });

          res.json(result);
      } catch (parseError) {
        console.error("Artist query parse error:", parseError);
        console.error(stdout);
        res.status(500).json({
          error: "Failed to parse artist query output",
        });
      }
    }
  );
});

app.get("/api/music/query/song", async (req, res) => {
  const { artist, song } = req.query;

  if (!artist || !String(artist).trim()) {
    return res.status(400).json({ error: "Artist required" });
  }

  if (!song || !String(song).trim()) {
    return res.status(400).json({ error: "Song required" });
  }

  const scriptPath = "../data/music/scripts/music_artist_song_context_probe.py";
  const artistSong = `${String(artist).trim()}::${String(song).trim()}`;

  execFile(
    "python",
    [scriptPath, "--artist-song", artistSong, "--json"],
    {
      cwd: __dirname,
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      maxBuffer: 1024 * 1024 * 10,
    },
    (error, stdout, stderr) => {
      if (error) {
        console.error("Song query error:", error);
        console.error(stderr);
        return res.status(500).json({
          error: "Failed to query song",
          details: stderr || error.message,
        });
      }

      try {
        const results = JSON.parse(stdout);
        res.json(results[0] || null);
      } catch (parseError) {
        console.error("Song query parse error:", parseError);
        console.error(stdout);
        res.status(500).json({
          error: "Failed to parse song query output",
        });
      }
    }
  );
});


app.get("/api/test", (req, res) => {
  res.json({ message: "test route works" });
});

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "defending-sisyphus-api",
    timestamp: new Date().toISOString(),
  });
});


app.get("/api/music/playlist-intelligence", (req, res) => {
  const playlistIntelligenceFile = path.join(
    __dirname,
    "..",
    "data",
    "music",
    "playlist_intelligence.json"
  );

  try {
    const raw = fs.readFileSync(playlistIntelligenceFile, "utf8");
    res.json(JSON.parse(raw));
  } catch (error) {
    console.error("Failed to load playlist intelligence:", error.message);
    res.status(500).json({
      error: "Failed to load playlist intelligence",
      details: error.message,
    });
  }
});

app.get("/api/music/playlist-intelligence/summary", (req, res) => {
  const playlistIntelligenceFile = path.join(
    __dirname,
    "..",
    "data",
    "music",
    "playlist_intelligence.json"
  );

  try {
    const raw = fs.readFileSync(playlistIntelligenceFile, "utf8");
    const data = JSON.parse(raw);

    res.json({
      playlists: data.playlists,
      sharedCoreArtists: data.sharedCoreArtists
        .filter((artist) => artist.playlistCount === 3)
        .slice(0, 12),
      bridgeSongs: data.bridgeSongs.slice(0, 12),
      playlistSignatures: data.playlistSignatures,
    });
  } catch (error) {
    console.error("Failed to load playlist intelligence summary:", error.message);
    res.status(500).json({
      error: "Failed to load playlist intelligence summary",
      details: error.message,
    });
  }
});

app.get("/api/apple-music/recent-tracks", async (req, res) => {
  const developerToken = process.env.APPLE_MUSIC_DEVELOPER_TOKEN;
  const musicUserToken = process.env.APPLE_MUSIC_USER_TOKEN;

  if (!developerToken || !musicUserToken) {
    return res.status(501).json({
      error: "Apple Music tokens not configured",
      requiredEnv: [
        "APPLE_MUSIC_DEVELOPER_TOKEN",
        "APPLE_MUSIC_USER_TOKEN"
      ],
      purpose: "POC endpoint for Apple Music recently played tracks"
    });
  }

  const limit = Math.min(Number(req.query.limit || 30), 30);
  const types = String(req.query.types || "songs,library-songs");

  const url = new URL("https://api.music.apple.com/v1/me/recent/played/tracks");
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("types", types);

  try {
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${developerToken}`,
        "Music-User-Token": musicUserToken
      }
    });

    const payload = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: "Apple Music API request failed",
        status: response.status,
        payload
      });
    }

    const tracks = (payload.data || []).map((item) => ({
      id: item.id,
      type: item.type,
      href: item.href,
      name: item.attributes?.name || null,
      artistName: item.attributes?.artistName || null,
      albumName: item.attributes?.albumName || null,
      durationInMillis: item.attributes?.durationInMillis || null,
      releaseDate: item.attributes?.releaseDate || null,
      isrc: item.attributes?.isrc || null,
      playParams: item.attributes?.playParams || null
    }));

    res.json({
      source: "apple_music_api_recent_played_tracks",
      limit,
      returned: tracks.length,
      next: payload.next || null,
      tracks,
      rawShapeSample: payload.data?.[0] || null
    });
  } catch (error) {
    res.status(500).json({
      error: "Apple Music API POC failed",
      message: error.message
    });
  }
});
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});























