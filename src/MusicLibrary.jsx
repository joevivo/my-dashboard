import { useEffect, useMemo, useRef, useState } from "react";
import DashboardSection from "./components/DashboardSection";
import { loadImportedMusicLibrary } from "./music/musicStore";
import { selectImportedMusicStats } from "./music/musicSelectors";
import { parseAlbumCsv } from "./music/albumCsvImport";
import {
  BarChart3,
  ChevronDown,
  Clock3,
  Compass,
  Disc3,
  Headphones,
  ListMusic,
  Mic2,
  Sparkles,
  Star,
  Tags,
  Ticket,
  UserRoundSearch,
} from "lucide-react";
const defaultData = {
  artists: [],
  albums: [],
  playlists: [],
  shows: [],
  explore: [],
  eras: [],
};

const emptyArtist = {
  name: "",
  tags: "",
  favoriteEra: "",
  notes: "",
};

const emptyAlbum = {
  artist: "",
  title: "",
  year: "",
  rating: "",
  favoriteTracks: "",
  tags: "",
  essential: false,
  coverUrl: "",
  appleMusicUrl: "",
  notes: "",
};

const emptyPlaylist = {
  title: "",
  theme: "",
  tags: "",
  platform: "",
  link: "",
  notes: "",
};

const emptyShow = {
  artist: "",
  venue: "",
  date: "",
  rating: "",
  tags: "",
  notes: "",
};

const emptyExplore = {
  name: "",
  type: "",
  tags: "",
  reason: "",
  link: "",
  notes: "",
};
const emptyEra = {
  title: "",
  timeframe: "",
  emotionalState: "",
  keyArtists: "",
  keyAlbums: "",
  playlists: "",
  locations: "",
  season: "",
  notes: "",
};
function normalizeMusicData(data) {
  return {
    artists: Array.isArray(data?.artists) ? data.artists : [],
    albums: Array.isArray(data?.albums) ? data.albums : [],
    playlists: Array.isArray(data?.playlists) ? data.playlists : [],
    shows: Array.isArray(data?.shows) ? data.shows : [],
    explore: Array.isArray(data?.explore) ? data.explore : [],
    eras: Array.isArray(data?.eras) ? data.eras : [],
  };
}

function normalizeText(value) {
  return String(value || "").trim().toLowerCase();
}

function itemMentionsArtist(item, artistName) {
  const target = normalizeText(artistName);

  if (!target) return false;

  return Object.values(item).some((value) =>
    normalizeText(value).includes(target)
  );
}

function itemHasTag(item, selectedTag) {
  const target = normalizeText(selectedTag);

  if (!target) return true;

  return String(item.tags || "")
    .split(",")
    .map((tag) => normalizeText(tag))
    .includes(target);
}

function collectAllTags(data) {
  const tagCounts = {};

  ["artists", "albums", "playlists", "shows", "explore"].forEach((section) => {
    data[section].forEach((item) => {
      String(item.tags || "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean)
        .forEach((tag) => {
          tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        });
    });
  });

  return Object.entries(tagCounts).sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];
    return a[0].localeCompare(b[0]);
  });
}

export default function MusicLibrary() {
  const fileInputRef = useRef(null);
  const albumCsvInputRef = useRef(null);

  const [musicData, setMusicData] = useState(() => {
    const saved = localStorage.getItem("musicLibrary");

    if (!saved) return defaultData;

    try {
      return normalizeMusicData(JSON.parse(saved));
    } catch {
      return defaultData;
    }
  });

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedArtist, setSelectedArtist] = useState("");
  const [selectedTag, setSelectedTag] = useState("");

  const [importedMusicLibrary, setImportedMusicLibrary] = useState(null);
  const [importedMusicStatus, setImportedMusicStatus] = useState("idle");
  const [importedMusicError, setImportedMusicError] = useState("");

  useEffect(() => {
    let isMounted = true;

    setImportedMusicStatus("loading");

    loadImportedMusicLibrary()
      .then((library) => {
        if (!isMounted) return;

        setImportedMusicLibrary(library || null);
        setImportedMusicStatus("loaded");
      })
      .catch((error) => {
        if (!isMounted) return;

        console.error("Failed loading imported music library", error);
        setImportedMusicError("Unable to load imported music library.");
        setImportedMusicStatus("error");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const importedMusicStats = useMemo(
    () => selectImportedMusicStats(importedMusicLibrary),
    [importedMusicLibrary]
  );

  const latestImportedMusicImport =
    importedMusicLibrary?.imports?.[importedMusicLibrary.imports.length - 1] ||
    null;

  const [artist, setArtist] = useState(emptyArtist);
  const [album, setAlbum] = useState(emptyAlbum);
  const [playlist, setPlaylist] = useState(emptyPlaylist);
  const [show, setShow] = useState(emptyShow);
  const [explore, setExplore] = useState(emptyExplore);
  const [era, setEra] = useState(emptyEra);
  const [editingEraIndex, setEditingEraIndex] = useState(null);
  const [editingAlbumIndex, setEditingAlbumIndex] = useState(null);
  const [importMessage, setImportMessage] = useState("");
const [openSections, setOpenSections] = useState(() => {
  const defaultOpenSections = {
    eras: false,
    essentialAlbums: false,
    favoriteArtists: false,
    favoriteAlbums: false,
    playlists: false,
    shows: false,
    explore: false,
  };

  const saved = localStorage.getItem("musicOpenSections");

  if (!saved) return defaultOpenSections;

  try {
    return {
      ...defaultOpenSections,
      ...JSON.parse(saved),
    };
  } catch {
    return defaultOpenSections;
  }
});

const toggleSection = (sectionName) => {
  setOpenSections((current) => ({
    ...current,
    [sectionName]: !current[sectionName],
  }));
};

useEffect(() => {
  try {
    localStorage.setItem("musicLibrary", JSON.stringify(musicData));
  } catch (error) {
    console.error("Failed saving music library", error);
  }
}, [musicData]);

useEffect(() => {
  localStorage.setItem("musicOpenSections", JSON.stringify(openSections));
}, [openSections]);

const addItem = (section, item, resetFn, emptyItem) => {
    const hasValue = Object.values(item).some((value) =>
      String(value || "").trim()
    );

    if (!hasValue) return;

    setMusicData((prev) => ({
      ...prev,
      [section]: [...prev[section], item],
    }));

    resetFn(emptyItem);
  };

  const removeItem = (section, index) => {
    setMusicData((prev) => ({
      ...prev,
      [section]: prev[section].filter((_, i) => i !== index),
    }));

    if (section === "albums" && editingAlbumIndex === index) {
      setEditingAlbumIndex(null);
      setAlbum(emptyAlbum);
    }
  };

  const saveAlbum = () => {
    const hasValue = Object.values(album).some((value) =>
      String(value || "").trim()
    );

    if (!hasValue) return;

    if (editingAlbumIndex !== null) {
      const updatedAlbums = [...musicData.albums];

      updatedAlbums[editingAlbumIndex] = album;

      setMusicData((prev) => ({
        ...prev,
        albums: updatedAlbums,
      }));

      setEditingAlbumIndex(null);
      setAlbum(emptyAlbum);

      return;
    }

    addItem("albums", album, setAlbum, emptyAlbum);
  };

  const cancelAlbumEdit = () => {
    setEditingAlbumIndex(null);
    setAlbum(emptyAlbum);
  };
const saveEra = () => {
  const hasValue = Object.values(era).some((value) =>
    String(value || "").trim()
  );

  if (!hasValue) return;

  if (editingEraIndex !== null) {
    const updatedEras = [...musicData.eras];

    updatedEras[editingEraIndex] = era;

    setMusicData((prev) => ({
      ...prev,
      eras: updatedEras,
    }));

    setEditingEraIndex(null);
    setEra(emptyEra);

    return;
  }

  addItem("eras", era, setEra, emptyEra);
};

const cancelEraEdit = () => {
  setEditingEraIndex(null);
  setEra(emptyEra);
};
  const exportMusicLibrary = () => {
    const payload = {
      exportedAt: new Date().toISOString(),
      version: 1,
      musicLibrary: normalizeMusicData(musicData),
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "music-library-backup.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const importMusicLibrary = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result);

        const importedData = parsed.musicLibrary ? parsed.musicLibrary : parsed;

        setMusicData(normalizeMusicData(importedData));
        setEditingAlbumIndex(null);
        setSelectedArtist("");
        setSelectedTag("");
        setAlbum(emptyAlbum);
        setImportMessage("Music library imported successfully.");
      } catch (error) {
        console.error("Failed importing music library", error);
        setImportMessage("Import failed. Make sure this is a valid JSON backup.");
      }

      event.target.value = "";
    };

    reader.readAsText(file);
  };

  const downloadAlbumCsvTemplate = () => {
    const csv = [
      "artist,title,year,rating,favoriteTracks,tags,essential,coverUrl,appleMusicUrl,notes",
      "Big Star,Radio City,1974,10,\"September Gurls, Back of a Car\",\"power pop, 70s\",true,,,Sample row - replace or delete.",
      "The Replacements,Let It Be,1984,9.5,\"I Will Dare, Unsatisfied\",\"college rock, 80s\",yes,,,Sample row - replace or delete.",
    ].join("\n");

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "album-import-template.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const importAlbumCsv = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const input = event.target;
    const reader = new FileReader();

    reader.onload = () => {
      try {
        const { albums, skipped } = parseAlbumCsv(String(reader.result || ""));

        if (!albums.length) {
          setImportMessage(
            skipped
              ? `No albums imported. Skipped ${skipped} incomplete row${skipped === 1 ? "" : "s"}.`
              : "No albums imported. Make sure the CSV includes artist and title columns."
          );

          return;
        }

        setMusicData((prev) => ({
          ...prev,
          albums: [...prev.albums, ...albums],
        }));

        setEditingAlbumIndex(null);
        setAlbum(emptyAlbum);

        setImportMessage(
          `Imported ${albums.length} album${albums.length === 1 ? "" : "s"} from CSV${skipped ? `; skipped ${skipped} incomplete row${skipped === 1 ? "" : "s"}` : ""}.`
        );
      } catch (error) {
        console.error("Failed importing album CSV", error);
        setImportMessage("Album CSV import failed. Check the file format.");
      } finally {
        input.value = "";
      }
    };

    reader.readAsText(file);
  };

  const filteredData = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    const matchesSearch = (item) => {
      if (!query) return true;

      return Object.values(item).some((value) =>
        String(value || "").toLowerCase().includes(query)
      );
    };

    const matchesFilters = (item) =>
      matchesSearch(item) && itemHasTag(item, selectedTag);

    return {
      artists: musicData.artists.filter(matchesFilters),
      albums: musicData.albums.filter(matchesFilters),
      playlists: musicData.playlists.filter(matchesFilters),
      shows: musicData.shows.filter(matchesFilters),
      explore: musicData.explore.filter(matchesFilters),
    };
  }, [musicData, searchTerm, selectedTag]);

  const allTags = useMemo(() => collectAllTags(musicData), [musicData]);

  const recentItems = useMemo(() => {
    const combined = [
      ...musicData.albums.map((item, index) => ({
        ...item,
        section: "Album",
        display: item.title || "Untitled Album",
        subdisplay: item.artist || "",
        key: `album-${index}`,
      })),
      ...musicData.artists.map((item, index) => ({
        ...item,
        section: "Artist",
        display: item.name || "Untitled Artist",
        subdisplay: item.favoriteEra || "",
        key: `artist-${index}`,
      })),
      ...musicData.playlists.map((item, index) => ({
        ...item,
        section: "Playlist",
        display: item.title || "Untitled Playlist",
        subdisplay: item.theme || "",
        key: `playlist-${index}`,
      })),
      ...musicData.shows.map((item, index) => ({
        ...item,
        section: "Show",
        display: item.artist || "Untitled Show",
        subdisplay: item.venue || "",
        key: `show-${index}`,
      })),
    ];

    return combined.slice(-6).reverse();
  }, [musicData]);

  const selectedArtistRecord = useMemo(() => {
    if (!selectedArtist) return null;

    return musicData.artists.find(
      (item) => normalizeText(item.name) === normalizeText(selectedArtist)
    );
  }, [musicData.artists, selectedArtist]);

  const artistRelated = useMemo(() => {
    if (!selectedArtist) {
      return {
        albums: [],
        playlists: [],
        shows: [],
        explore: [],
      };
    }

    return {
      albums: musicData.albums.filter((item) =>
        itemMentionsArtist(item, selectedArtist)
      ),
      playlists: musicData.playlists.filter((item) =>
        itemMentionsArtist(item, selectedArtist)
      ),
      shows: musicData.shows.filter((item) =>
        itemMentionsArtist(item, selectedArtist)
      ),
      explore: musicData.explore.filter((item) =>
        itemMentionsArtist(item, selectedArtist)
      ),
    };
  }, [musicData, selectedArtist]);

  const essentialAlbums = filteredData.albums.filter((item) => item.essential);

  return (
    <div className="space-y-6">
      <div className="dashboard-panel p-6">
        <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] lg:items-start">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:border-slate-700 dark:bg-slate-800/70 dark:text-slate-300">
              <Headphones className="h-3.5 w-3.5" />
              Music command center
            </div>

            <h1 className="mt-4 text-3xl font-bold tracking-tight">
              Music Library
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Favorite artists, albums, playlists, shows attended, listening eras,
              and future exploration notes.
            </p>

            <div className="mt-5 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full bg-slate-900 px-3 py-1 font-semibold text-white dark:bg-slate-100 dark:text-slate-900">
                {musicData.albums.length} albums
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 font-semibold text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                {musicData.artists.length} artists
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 font-semibold text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                {musicData.shows.length} shows
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-800/60">
            <label className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Search Library
            </label>

            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search artists, albums, tags, notes..."
              className="mt-2 w-full border border-slate-200 bg-white rounded-lg p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
            />

            <div className="mt-4 grid grid-cols-1 gap-2">
              <button
                onClick={exportMusicLibrary}
                className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg text-sm"
              >
                Export Music Library
              </button>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-3 py-2 rounded-lg text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Restore JSON
                </button>

                <button
                  onClick={() => albumCsvInputRef.current?.click()}
                  className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-3 py-2 rounded-lg text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Add Albums CSV
                </button>
              </div>

              <button
                onClick={downloadAlbumCsvTemplate}
                className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-3 py-2 rounded-lg text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                Download Album Template
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/json,.json"
              onChange={importMusicLibrary}
              className="hidden"
            />

            <input
              ref={albumCsvInputRef}
              type="file"
              accept=".csv,text/csv"
              onChange={importAlbumCsv}
              className="hidden"
            />

            {importMessage && (
              <div className="mt-3 text-sm text-slate-500">
                {importMessage}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-panel p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Curated Library
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Your manually maintained artists, albums, shows, playlists, eras, and notes.
            </p>
          </div>

          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
              JSON Backup
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Full backup and restore for the curated library.
            </p>
          </div>

          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Album CSV
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Bulk-add curated albums only. It appends; it does not replace the library.
            </p>
          </div>

          <div>
            <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Apple Export
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Future imported listening data, kept separate from curated notes.
            </p>
          </div>
        </div>
      </div>
      <DashboardSection title="Music Dashboard" Icon={BarChart3} color="sky">
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
          <StatCard
            icon={Star}
            label="Avg Rating"
            value={
              musicData.albums.length
                ? (
                    musicData.albums.reduce(
                      (sum, album) => sum + Number(album.rating || 0),
                      0
                    ) / musicData.albums.length
                  ).toFixed(1)
                : "0"
            }
          />

          <StatCard
            icon={Sparkles}
            label="Essential"
            value={
              musicData.albums.filter((album) => album.essential).length
            }
          />

          <StatCard
            icon={Ticket}
            label="Shows"
            value={musicData.shows.length}
          />

          <StatCard
            icon={ListMusic}
            label="Playlists"
            value={musicData.playlists.length}
          />

          <StatCard
            icon={UserRoundSearch}
            label="Artists"
            value={musicData.artists.length}
          />

          <StatCard
            icon={Disc3}
            label="Albums"
            value={musicData.albums.length}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <TopTagsCard albums={musicData.albums} />
          <TopArtistsCard albums={musicData.albums} />
        </div>
      </DashboardSection>

      {importedMusicStatus === "loaded" && !importedMusicLibrary ? (
        <div className="dashboard-panel p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <span className="dashboard-section-icon flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/70 border border-white/80 shadow-sm">
                <Headphones className="dashboard-section-icon-svg h-5 w-5 text-slate-500" />
              </span>

              <div>
                <h2 className="text-base font-bold">Imported Music Library</h2>
                <p className="text-sm text-slate-500">
                  Apple Music export staging area. No imported library is loaded yet.
                </p>
              </div>
            </div>

            <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Ready for future Apple data
            </div>
          </div>
        </div>
      ) : (
        <DashboardSection title="Imported Music Library" Icon={Headphones} color="slate">
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
            <StatCard
              icon={Disc3}
              label="Tracks"
              value={importedMusicStats.tracks.toLocaleString()}
            />

            <StatCard
              icon={UserRoundSearch}
              label="Artists"
              value={importedMusicStats.artists.toLocaleString()}
            />

            <StatCard
              icon={Headphones}
              label="Albums"
              value={importedMusicStats.albums.toLocaleString()}
            />

            <StatCard
              icon={ListMusic}
              label="Playlists"
              value={importedMusicStats.playlists.toLocaleString()}
            />

            <StatCard
              icon={Tags}
              label="Playlist Links"
              value={importedMusicStats.playlistTrackLinks.toLocaleString()}
            />

            <StatCard
              icon={Clock3}
              label="Imports"
              value={importedMusicStats.imports.toLocaleString()}
            />
          </div>

          {importedMusicStatus === "loading" && (
            <p className="text-sm text-slate-500">
              Checking for imported music data...
            </p>
          )}

          {importedMusicStatus === "error" && (
            <p className="text-sm text-red-600">{importedMusicError}</p>
          )}

          {latestImportedMusicImport && (
            <p className="text-sm text-slate-500">
              Last import: {latestImportedMusicImport.source} {" - "}
              {new Date(latestImportedMusicImport.importedAt).toLocaleString()}
            </p>
          )}
        </DashboardSection>
      )}
<DashboardSection
  title="Listening Eras"
  Icon={Clock3}
  color="purple"
  summary="Map listening periods to artists, albums, moods, places, and notes."
  isOpen={openSections.eras}
  onToggle={() => toggleSection("eras")}
>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Input
      label="Title"
      value={era.title}
      onChange={(v) => setEra({ ...era, title: v })}
    />

    <Input
      label="Timeframe"
      value={era.timeframe}
      onChange={(v) => setEra({ ...era, timeframe: v })}
    />

    <Input
      label="Emotional State"
      value={era.emotionalState}
      onChange={(v) => setEra({ ...era, emotionalState: v })}
    />

    <Input
      label="Season"
      value={era.season}
      onChange={(v) => setEra({ ...era, season: v })}
    />

    <Input
      label="Key Artists"
      value={era.keyArtists}
      onChange={(v) => setEra({ ...era, keyArtists: v })}
    />

    <Input
      label="Key Albums"
      value={era.keyAlbums}
      onChange={(v) => setEra({ ...era, keyAlbums: v })}
    />

    <Input
      label="Playlists"
      value={era.playlists}
      onChange={(v) => setEra({ ...era, playlists: v })}
    />

    <Input
      label="Locations"
      value={era.locations}
      onChange={(v) => setEra({ ...era, locations: v })}
    />

    <div className="md:col-span-2">
      <Input
        label="Notes"
        value={era.notes}
        onChange={(v) => setEra({ ...era, notes: v })}
      />
    </div>
  </div>

  <div className="flex gap-2">
  <AddButton
    label={editingEraIndex !== null ? "Save Changes" : "Add Era"}
    onClick={saveEra}
  />

  {editingEraIndex !== null && (
    <button
      onClick={cancelEraEdit}
      className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-4 py-2 rounded-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
    >
      Cancel
    </button>
  )}
</div>

  {musicData.eras.length === 0 ? (
    <p className="text-sm text-slate-500">
      No listening eras yet. Add one to begin mapping music to emotional seasons.
    </p>
  ) : (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {musicData.eras.map((item, index) => (
        <div
          key={`${item.title}-${index}`}
          className="bg-white border border-purple-100 rounded-2xl p-5 shadow-sm dark:border-purple-900/40 dark:bg-slate-800/80"
        >
          <div className="flex justify-between gap-4">
            <div>
              <div className="text-xs uppercase text-purple-400 font-bold">
                {item.timeframe || "Untimed Era"}
              </div>

              <h3 className="text-xl font-bold text-slate-900 mt-1">
                {item.title || "Untitled Era"}
              </h3>

              {item.emotionalState && (
                <div className="text-sm text-purple-700 font-medium mt-1">
                  {item.emotionalState}
                </div>
              )}
            </div>

            <div className="flex gap-3">
  <button
    onClick={() => {
      setEra({
        title: item.title || "",
        timeframe: item.timeframe || "",
        emotionalState: item.emotionalState || "",
        keyArtists: item.keyArtists || "",
        keyAlbums: item.keyAlbums || "",
        playlists: item.playlists || "",
        locations: item.locations || "",
        season: item.season || "",
        notes: item.notes || "",
      });

      setEditingEraIndex(index);

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }}
    className="text-xs text-purple-700 hover:underline"
  >
    Edit
  </button>

  <button
    onClick={() => removeItem("eras", index)}
    className="text-xs text-slate-400 hover:text-red-500"
  >
    Delete
  </button>
</div>
          </div>

          <div className="mt-4 space-y-2 text-sm text-slate-600">
            {item.season && (
              <div>
                <span className="font-semibold">Season:</span> {item.season}
              </div>
            )}

            {item.keyArtists && (
              <div>
                <span className="font-semibold">Key artists:</span>{" "}
                {item.keyArtists}
              </div>
            )}

            {item.keyAlbums && (
              <div>
                <span className="font-semibold">Key albums:</span>{" "}
                {item.keyAlbums}
              </div>
            )}

            {item.playlists && (
              <div>
                <span className="font-semibold">Playlists:</span>{" "}
                {item.playlists}
              </div>
            )}

            {item.locations && (
              <div>
                <span className="font-semibold">Locations:</span>{" "}
                {item.locations}
              </div>
            )}

            {item.notes && (
              <p className="pt-2 text-slate-700 leading-relaxed">
                {item.notes}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )}
</DashboardSection>

      <DashboardSection title="Tag Browser" Icon={Tags} color="green">
        <TagBrowser
          tags={allTags}
          selectedTag={selectedTag}
          setSelectedTag={setSelectedTag}
        />
      </DashboardSection>

      <DashboardSection title="Artist Spotlight" Icon={UserRoundSearch} color="purple">
        {!selectedArtist ? (
          <p className="text-sm text-slate-500">
            Click an artist card below to see related albums, playlists, shows,
            and exploration notes.
          </p>
        ) : (
          <ArtistSpotlight
            artistName={selectedArtist}
            artist={selectedArtistRecord}
            related={artistRelated}
            clearArtist={() => setSelectedArtist("")}
          />
        )}
      </DashboardSection>

      <DashboardSection title="Recently Added" Icon={Clock3} color="slate">
        {recentItems.length === 0 ? (
          <p className="text-sm text-slate-500">No recent entries yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {recentItems.map((item) => (
              <div
                key={item.key}
                className="border border-slate-200 rounded-xl p-4 bg-slate-50"
              >
                <div className="text-xs uppercase text-slate-400 font-bold">
                  {item.section}
                </div>
                <div className="font-bold text-slate-900">{item.display}</div>
                {item.subdisplay && (
                  <div className="text-sm text-slate-500">
                    {item.subdisplay}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </DashboardSection>

      <DashboardSection
  title="Essential Albums" Icon={Sparkles}
  color="amber"
  summary="A focused view of albums marked essential in your curated library."
  isOpen={openSections.essentialAlbums}
  onToggle={() => toggleSection("essentialAlbums")}
>
        <AlbumGallery
          items={essentialAlbums}
          removeItem={removeItem}
          setAlbum={setAlbum}
          setEditingAlbumIndex={setEditingAlbumIndex}
          sourceItems={musicData.albums}
        />
      </DashboardSection>

      <DashboardSection
  title="Favorite Artists" Icon={UserRoundSearch}
  color="purple"
  summary="Core artists, genre tags, favorite eras, and spotlight links."
  isOpen={openSections.favoriteArtists}
  onToggle={() => toggleSection("favoriteArtists")}
>
        <Input
          label="Artist"
          value={artist.name}
          onChange={(v) => setArtist({ ...artist, name: v })}
        />

        <Input
          label="Tags / Genres"
          value={artist.tags}
          onChange={(v) => setArtist({ ...artist, tags: v })}
        />

        <Input
          label="Favorite Era"
          value={artist.favoriteEra}
          onChange={(v) => setArtist({ ...artist, favoriteEra: v })}
        />

        <Input
          label="Notes"
          value={artist.notes}
          onChange={(v) => setArtist({ ...artist, notes: v })}
        />

        <AddButton
          onClick={() => addItem("artists", artist, setArtist, emptyArtist)}
        />

        <StandardCardList
          items={filteredData.artists}
          section="artists"
          removeItem={removeItem}
          titleKey="name"
          sourceItems={musicData.artists}
          onTitleClick={(item) => setSelectedArtist(item.name)}
          actionLabel="Spotlight"
        />
      </DashboardSection>

      <DashboardSection
  title="Favorite Albums" Icon={Disc3}
  color="amber"
  summary="Curated albums with ratings, favorite tracks, tags, covers, and notes."
  isOpen={openSections.favoriteAlbums}
  onToggle={() => toggleSection("favoriteAlbums")}
>
        {editingAlbumIndex !== null && (
          <div className="bg-amber-100 border border-amber-200 text-amber-900 rounded-xl px-4 py-3 text-sm">
            Editing album. Update the fields below, then click{" "}
            <span className="font-semibold">Save Changes</span>.
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Artist"
            value={album.artist}
            onChange={(v) => setAlbum({ ...album, artist: v })}
          />

          <Input
            label="Album"
            value={album.title}
            onChange={(v) => setAlbum({ ...album, title: v })}
          />

          <Input
            label="Year"
            value={album.year}
            onChange={(v) => setAlbum({ ...album, year: v })}
          />

          <Input
            label="Rating"
            value={album.rating}
            onChange={(v) => setAlbum({ ...album, rating: v })}
          />

          <Input
            label="Favorite Tracks"
            value={album.favoriteTracks}
            onChange={(v) => setAlbum({ ...album, favoriteTracks: v })}
          />

          <Input
            label="Tags / Genres"
            value={album.tags}
            onChange={(v) => setAlbum({ ...album, tags: v })}
          />

          <Checkbox
            label="Essential album"
            checked={album.essential}
            onChange={(checked) =>
              setAlbum({ ...album, essential: checked })
            }
          />

          <Input
            label="Cover Image URL"
            value={album.coverUrl}
            onChange={(v) => setAlbum({ ...album, coverUrl: v })}
          />

          <Input
            label="Apple Music URL"
            value={album.appleMusicUrl}
            onChange={(v) => setAlbum({ ...album, appleMusicUrl: v })}
          />

          <Input
            label="Notes"
            value={album.notes}
            onChange={(v) => setAlbum({ ...album, notes: v })}
          />
        </div>

        <div className="flex gap-2">
          <AddButton
            label={editingAlbumIndex !== null ? "Save Changes" : "Add Album"}
            onClick={saveAlbum}
          />

          {editingAlbumIndex !== null && (
            <button
              onClick={cancelAlbumEdit}
              className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-4 py-2 rounded-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
          )}
        </div>

        <AlbumGallery
          items={filteredData.albums}
          removeItem={removeItem}
          setAlbum={setAlbum}
          setEditingAlbumIndex={setEditingAlbumIndex}
          sourceItems={musicData.albums}
          onArtistClick={setSelectedArtist}
        />
      </DashboardSection>

      <DashboardSection
  title="Playlists" Icon={ListMusic}
  color="sky"
  summary="Playlist ideas, themes, platforms, links, and notes."
  isOpen={openSections.playlists}
  onToggle={() => toggleSection("playlists")}
>
        <Input
          label="Title"
          value={playlist.title}
          onChange={(v) => setPlaylist({ ...playlist, title: v })}
        />

        <Input
          label="Theme"
          value={playlist.theme}
          onChange={(v) => setPlaylist({ ...playlist, theme: v })}
        />

        <Input
          label="Tags"
          value={playlist.tags}
          onChange={(v) => setPlaylist({ ...playlist, tags: v })}
        />

        <Input
          label="Platform"
          value={playlist.platform}
          onChange={(v) => setPlaylist({ ...playlist, platform: v })}
        />

        <Input
          label="Link"
          value={playlist.link}
          onChange={(v) => setPlaylist({ ...playlist, link: v })}
        />

        <Input
          label="Notes"
          value={playlist.notes}
          onChange={(v) => setPlaylist({ ...playlist, notes: v })}
        />

        <AddButton
          onClick={() =>
            addItem("playlists", playlist, setPlaylist, emptyPlaylist)
          }
        />

        <StandardCardList
          items={filteredData.playlists}
          section="playlists"
          removeItem={removeItem}
          titleKey="title"
          sourceItems={musicData.playlists}
        />
      </DashboardSection>

      <DashboardSection
  title="Shows Attended" Icon={Ticket}
  color="rose"
  summary="Concert history, venues, dates, ratings, and related artist notes."
  isOpen={openSections.shows}
  onToggle={() => toggleSection("shows")}
>
        <Input
          label="Artist"
          value={show.artist}
          onChange={(v) => setShow({ ...show, artist: v })}
        />

        <Input
          label="Venue"
          value={show.venue}
          onChange={(v) => setShow({ ...show, venue: v })}
        />

        <Input
          label="Date"
          value={show.date}
          onChange={(v) => setShow({ ...show, date: v })}
        />

        <Input
          label="Rating"
          value={show.rating}
          onChange={(v) => setShow({ ...show, rating: v })}
        />

        <Input
          label="Tags"
          value={show.tags}
          onChange={(v) => setShow({ ...show, tags: v })}
        />

        <Input
          label="Notes"
          value={show.notes}
          onChange={(v) => setShow({ ...show, notes: v })}
        />

        <AddButton onClick={() => addItem("shows", show, setShow, emptyShow)} />

        <StandardCardList
          items={filteredData.shows}
          section="shows"
          removeItem={removeItem}
          titleKey="artist"
          sourceItems={musicData.shows}
          onTitleClick={(item) => setSelectedArtist(item.artist)}
          actionLabel="Spotlight"
        />
      </DashboardSection>

      <DashboardSection
  title="Want to Explore" Icon={Compass}
  color="green"
  summary="Artists, genres, records, and ideas to investigate later."
  isOpen={openSections.explore}
  onToggle={() => toggleSection("explore")}
>
        <Input
          label="Name"
          value={explore.name}
          onChange={(v) => setExplore({ ...explore, name: v })}
        />

        <Input
          label="Type"
          value={explore.type}
          onChange={(v) => setExplore({ ...explore, type: v })}
        />

        <Input
          label="Tags"
          value={explore.tags}
          onChange={(v) => setExplore({ ...explore, tags: v })}
        />

        <Input
          label="Reason"
          value={explore.reason}
          onChange={(v) => setExplore({ ...explore, reason: v })}
        />

        <Input
          label="Link"
          value={explore.link}
          onChange={(v) => setExplore({ ...explore, link: v })}
        />

        <Input
          label="Notes"
          value={explore.notes}
          onChange={(v) => setExplore({ ...explore, notes: v })}
        />

        <AddButton
          onClick={() => addItem("explore", explore, setExplore, emptyExplore)}
        />

        <StandardCardList
          items={filteredData.explore}
          section="explore"
          removeItem={removeItem}
          titleKey="name"
          sourceItems={musicData.explore}
        />
      </DashboardSection>
    </div>
  );
}


function TagBrowser({ tags, selectedTag, setSelectedTag }) {
  if (!tags.length) {
    return (
      <p className="text-sm text-slate-500">
        No tags yet. Add comma-separated tags to albums, artists, playlists,
        shows, or explore notes.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {tags.map(([tag, count]) => {
          const active = normalizeText(tag) === normalizeText(selectedTag);

          return (
            <button
              key={tag}
              onClick={() => setSelectedTag(active ? "" : tag)}
              className={
                active
                  ? "text-xs bg-slate-900 text-white px-3 py-1 rounded-full border border-slate-900"
                  : "text-xs bg-white border border-slate-200 text-slate-700 px-3 py-1 rounded-full hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              }
            >
              {tag} ({count})
            </button>
          );
        })}
      </div>

      {selectedTag && (
        <button
          onClick={() => setSelectedTag("")}
          className="text-sm text-slate-500 hover:text-slate-900 hover:underline"
        >
          Clear tag filter: {selectedTag}
        </button>
      )}
    </div>
  );
}

function ArtistSpotlight({ artistName, artist, related, clearArtist }) {
  return (
    <div className="space-y-5">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <div className="text-xs uppercase text-slate-400 font-bold">
            Selected Artist
          </div>

          <h2 className="text-3xl font-bold text-slate-900">
            {artistName}
          </h2>

          {artist?.favoriteEra && (
            <div className="text-sm text-slate-500 mt-1">
              Favorite era: {artist.favoriteEra}
            </div>
          )}

          {artist?.tags && <TagPills value={artist.tags} />}

          {artist?.notes && (
            <p className="text-sm text-slate-600 mt-3 max-w-3xl">
              {artist.notes}
            </p>
          )}
        </div>

        <button
          onClick={clearArtist}
          className="bg-white border border-slate-200 hover:bg-slate-50 transition text-slate-700 px-4 py-2 rounded-lg text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          Clear Spotlight
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Albums" value={related.albums.length} />
        <StatCard label="Playlists" value={related.playlists.length} />
        <StatCard label="Shows" value={related.shows.length} />
        <StatCard label="Explore" value={related.explore.length} />
      </div>

      <SpotlightMiniSection title="Related Albums" items={related.albums} primaryKey="title" secondaryKey="artist" />
      <SpotlightMiniSection title="Related Playlists" items={related.playlists} primaryKey="title" secondaryKey="theme" />
      <SpotlightMiniSection title="Related Shows" items={related.shows} primaryKey="venue" secondaryKey="date" />
      <SpotlightMiniSection title="Explore Notes" items={related.explore} primaryKey="name" secondaryKey="reason" />
    </div>
  );
}

function SpotlightMiniSection({ title, items, primaryKey, secondaryKey }) {
  return (
    <div>
      <h3 className="font-bold text-slate-900 mb-2">{title}</h3>

      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No related entries yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {items.map((item, index) => (
            <div
              key={`${title}-${index}`}
              className="border border-slate-200 rounded-xl p-4 bg-white dark:border-slate-700 dark:bg-slate-800/80"
            >
              <div className="font-bold text-slate-900">
                {item[primaryKey] || "Untitled"}
              </div>

              {item[secondaryKey] && (
                <div className="text-sm text-slate-500">
                  {item[secondaryKey]}
                </div>
              )}

              {item.tags && <TagPills value={item.tags} />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Input({ label, value, onChange }) {
  return (
    <div>
      <label className="text-xs uppercase text-slate-400 font-bold">
        {label}
      </label>

      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-slate-200 bg-white/80 rounded-lg p-2.5 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
      />
    </div>
  );
}

function Checkbox({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700 mt-5">
      <input
        type="checkbox"
        checked={Boolean(checked)}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );
}

function AddButton({ onClick, label = "Add" }) {
  return (
    <button
      onClick={onClick}
      className="bg-slate-900 hover:bg-slate-800 transition text-white px-4 py-2 rounded-lg"
    >
      {label}
    </button>
  );
}

function AlbumGallery({
  items,
  removeItem,
  setAlbum,
  setEditingAlbumIndex,
  sourceItems,
  onArtistClick,
}) {
  if (!items.length) {
    return (
      <p className="text-sm text-slate-500">
        No albums added yet.
      </p>
    );
  }

  const getSourceIndex = (item, fallbackIndex) => {
    const index = sourceItems.findIndex((sourceItem) => sourceItem === item);
    return index === -1 ? fallbackIndex : index;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-5">
      {items.map((item, index) => {
        const sourceIndex = getSourceIndex(item, index);

        return (
          <div
            key={`${item.title}-${item.artist}-${index}`}
            className="group bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-lg transition dark:border-slate-700 dark:bg-slate-800/80"
          >
            <div className="aspect-square bg-slate-100 overflow-hidden">
              {item.coverUrl ? (
                <img
                  src={item.coverUrl}
                  alt={item.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
                  No Cover
                </div>
              )}
            </div>

            <div className="p-4 space-y-2">
              <div>
                <div className="font-bold text-slate-900 leading-tight">
                  {item.title || "Untitled"}
                </div>

                {item.artist && onArtistClick ? (
                  <button
                    onClick={() => onArtistClick(item.artist)}
                    className="text-sm text-purple-700 hover:underline text-left"
                  >
                    {item.artist}
                  </button>
                ) : (
                  <div className="text-sm text-slate-500">
                    {item.artist || "Unknown Artist"}
                  </div>
                )}
              </div>

              {item.year && (
                <div className="text-xs text-slate-400">
                  {item.year}
                </div>
              )}

              {item.rating && (
                <div className="text-sm font-medium text-amber-600">
                  Rating: {item.rating}
                </div>
              )}

              {item.essential && (
                <div className="inline-flex text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
                  Essential
                </div>
              )}

              {item.tags && <TagPills value={item.tags} />}

              {item.favoriteTracks && (
                <div className="text-xs text-slate-500 line-clamp-3">
                  {item.favoriteTracks}
                </div>
              )}

              <div className="flex justify-between items-center pt-2">
                <div className="flex gap-3">
                  {item.appleMusicUrl && (
                    <a
                      href={item.appleMusicUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-rose-600 hover:underline"
                    >
                      Apple Music
                    </a>
                  )}

             
                  <button
                    onClick={() => {
                      setAlbum({
                        artist: item.artist || "",
                        title: item.title || "",
                        year: item.year || "",
                        rating: item.rating || "",
                        favoriteTracks: item.favoriteTracks || "",
                        tags: item.tags || "",
                        essential: Boolean(item.essential),
                        coverUrl: item.coverUrl || "",
                        appleMusicUrl: item.appleMusicUrl || "",
                        notes: item.notes || "",
                      });

                      setEditingAlbumIndex(sourceIndex);

                      window.scrollTo({
                        top: 0,
                        behavior: "smooth",
                      });
                    }}
                    className="text-xs text-slate-500 hover:text-slate-900"
                  >
                    Edit
                  </button>
                </div>

                <button
                  onClick={() => removeItem("albums", sourceIndex)}
                  className="text-xs text-slate-400 hover:text-red-500"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StandardCardList({
  items,
  section,
  removeItem,
  titleKey,
  sourceItems,
  onTitleClick,
  actionLabel = "Open",
}) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No entries yet.</p>;
  }

  const getSourceIndex = (item, fallbackIndex) => {
    const index = sourceItems.findIndex((sourceItem) => sourceItem === item);
    return index === -1 ? fallbackIndex : index;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {items.map((item, index) => {
        const sourceIndex = getSourceIndex(item, index);

        return (
          <div
            key={`${item[titleKey]}-${index}`}
            className="border border-slate-200 rounded-xl p-4 bg-slate-50"
          >
            <div className="flex justify-between gap-4">
              <div>
                {onTitleClick ? (
                  <button
                    onClick={() => onTitleClick(item)}
                    className="font-bold text-purple-700 hover:underline text-left"
                  >
                    {item[titleKey] || "Untitled"}
                  </button>
                ) : (
                  <div className="font-bold text-slate-900">
                    {item[titleKey] || "Untitled"}
                  </div>
                )}

                {Object.entries(item)
                  .filter(
                    ([key, value]) =>
                      key !== titleKey &&
                      value &&
                      key !== "coverUrl" &&
                      key !== "appleMusicUrl" &&
                      key !== "essential"
                  )
                  .map(([key, value]) =>
                    key === "tags" ? (
                      <TagPills key={key} value={value} />
                    ) : (
                      <div
                        key={key}
                        className="text-sm text-slate-500"
                      >
                        <span className="font-semibold">
                          {formatLabel(key)}:
                        </span>{" "}
                        {value}
                      </div>
                    )
                  )}
              </div>
{onTitleClick && (
  <button
    onClick={() => onTitleClick(item)}
    className="text-xs text-purple-700 hover:underline mt-2"
  >
    {actionLabel}
  </button>
)}
              <button
                onClick={() => removeItem(section, sourceIndex)}
                className="text-red-600 text-sm hover:underline"
              >
                Delete
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TagPills({ value }) {
  const tags = String(value || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  if (!tags.length) return null;

  return (
    <div className="flex flex-wrap gap-1 mt-2">
      {tags.map((tag) => (
        <span
          key={tag}
          className="text-xs bg-white border border-slate-200 text-slate-600 px-2 py-1 rounded-full dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}

function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs uppercase text-slate-400 font-bold">
          {label}
        </div>

        {Icon && <Icon className="h-4 w-4 text-sky-500" />}
      </div>

      <div className="text-2xl font-bold text-slate-900 mt-2">
        {value}
      </div>
    </div>
  );
}

function TopTagsCard({ albums }) {
  const tagCounts = {};

  albums.forEach((album) => {
    String(album.tags || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean)
      .forEach((tag) => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });
  });

  const topTags = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
      <h3 className="font-bold text-slate-900 mb-3">
        Top Genres / Tags
      </h3>

      <div className="flex flex-wrap gap-2">
        {topTags.length ? (
          topTags.map(([tag, count]) => (
            <span
              key={tag}
              className="text-xs bg-white border border-slate-200 text-slate-700 px-3 py-1 rounded-full dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {tag} ({count})
            </span>
          ))
        ) : (
          <p className="text-sm text-slate-500">
            No tags yet.
          </p>
        )}
      </div>
    </div>
  );
}

function TopArtistsCard({ albums }) {
  const artistCounts = {};

  albums.forEach((album) => {
    const artist = album.artist?.trim();

    if (!artist) return;

    artistCounts[artist] = (artistCounts[artist] || 0) + 1;
  });

  const topArtists = Object.entries(artistCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
      <h3 className="font-bold text-slate-900 mb-3">
        Top Artists
      </h3>

      <div className="space-y-2">
        {topArtists.length ? (
          topArtists.map(([artist, count]) => (
            <div
              key={artist}
              className="flex justify-between text-sm"
            >
              <span>{artist}</span>
              <span className="text-slate-500">
                {count} albums
              </span>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-500">
            No artist data yet.
          </p>
        )}
      </div>
    </div>
  );
}
function formatLabel(key) {
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (char) => char.toUpperCase());
}





