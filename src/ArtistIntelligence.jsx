import { useEffect, useMemo, useState } from "react";
import { loadImportedMusicLibrary } from "./music/musicStore";

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

function classifyArtist(result) {
  const totalPlays = Number(result?.totalPlays || 0);
  const yearsActive = Number(result?.yearsActive || 0);

  if (!totalPlays || !yearsActive) {
    return {
      label: "Limited Evidence",
      summary: "Not enough library-track evidence to classify this artist yet.",
      rationale:
        "This does not mean the artist is unimportant. It means the current Library Tracks source has limited evidence for this lookup.",
    };
  }

  if (yearsActive >= 10 && totalPlays >= 75) {
    return {
      label: "Permanent Companion",
      summary: `${yearsActive} years represented - ${totalPlays} library evidence records`,
      rationale:
        "This artist shows both long-term persistence and substantial library evidence across the archive.",
    };
  }

  if (yearsActive >= 8 && totalPlays < 75) {
    return {
      label: "Hidden Pillar",
      summary: `${yearsActive} years represented - ${totalPlays} library evidence records`,
      rationale:
        "This artist appears repeatedly across the archive despite relatively modest volume.",
    };
  }

  if (yearsActive >= 4 && totalPlays >= 10) {
    return {
      label: "Established Companion",
      summary: `${yearsActive} years represented - ${totalPlays} library evidence records`,
      rationale:
        "This artist has enough recurrence to suggest an established relationship, but not enough evidence for Permanent Companion status.",
    };
  }

  if (yearsActive <= 3) {
    return {
      label: "Recent Signal",
      summary: `${yearsActive} years represented - ${totalPlays} library evidence records`,
      rationale:
        "This artist has limited or recent evidence in the Library Tracks reconstruction.",
    };
  }

  return {
    label: "Limited Evidence",
    summary: `${yearsActive} years represented - ${totalPlays} library evidence records`,
    rationale:
      "This artist has some evidence, but the current pattern does not fit a v0 classification cleanly.",
  };
}


function buildWhyBullets(result, classification) {
  const totalPlays = Number(result?.totalPlays || 0);
  const yearsActive = Number(result?.yearsActive || 0);
  const albumCount = Array.isArray(result?.topAlbums) ? result.topAlbums.length : 0;
  const timelineCount = Array.isArray(result?.timeline) ? result.timeline.length : 0;

  const bullets = [];

  if (yearsActive > 0) {
    bullets.push(`${yearsActive} years represented in Library Evidence.`);
  }

  if (totalPlays > 0) {
    bullets.push(`${totalPlays} Library Footprint records found.`);
  }

  if (timelineCount >= 8) {
    bullets.push("Persistent archive presence across many years.");
  } else if (timelineCount >= 4) {
    bullets.push("Recurring archive presence across multiple periods.");
  }

  if (albumCount >= 7) {
    bullets.push("Broad album spread suggests a catalog-level relationship.");
  } else if (albumCount >= 3) {
    bullets.push("Multiple albums are represented in the surviving archive.");
  } else if (albumCount === 1) {
    bullets.push("Evidence is concentrated around a single album.");
  }

  if (classification?.label === "Hidden Pillar") {
    bullets.push("Modest footprint combined with long persistence suggests a hidden pillar.");
  }

  if (classification?.label === "Permanent Companion") {
    bullets.push("Long-term persistence and substantial footprint suggest a permanent companion.");
  }

  return bullets;
}


function classifyRelationshipPattern(result) {
  const albums = Array.isArray(result?.topAlbums)
    ? result.topAlbums
    : [];

  const songs = Array.isArray(result?.topSongs)
    ? result.topSongs
    : [];

  const totalPlays = Number(result?.totalPlays || 0);

  if (!albums.length) {
    return {
      label: "Unknown Relationship",
      rationale: "Not enough album evidence to determine a relationship pattern.",
    };
  }

  const topAlbumShare =
    totalPlays > 0 ? (albums[0]?.plays || 0) / totalPlays : 0;

  const topSongShare =
    totalPlays > 0 ? (songs[0]?.plays || 0) / totalPlays : 0;

  if (topSongShare >= 0.60) {
    return {
      label: "Song-Centered Relationship",
      rationale:
        "A single song appears to dominate the surviving evidence.",
    };
  }

  const greatestHitsAlbums = albums.filter((a) =>
    /(greatest|best of|anthology|portrait|hits|retrospective|collection|essential|man and his music|man who invented soul)/i.test(
      a.album || ""
    )
  );

  const topAlbumIsCompilation =
    /(greatest|best of|anthology|portrait|hits|retrospective|collection|essential|man and his music|man who invented soul)/i.test(
      albums[0]?.album || ""
    );

  if (greatestHitsAlbums.length >= 2 || topAlbumIsCompilation) {
    return {
      label: "Greatest-Hits Relationship",
      rationale:
        "Compilation, retrospective, or legacy albums drive much of the evidence.",
    };
  }

  if (topAlbumShare >= 0.40) {
    return {
      label: "Album-Centered Relationship",
      rationale:
        "A single non-compilation album accounts for a large share of the relationship.",
    };
  }

  if (albums.length >= 7) {
    return {
      label: "Catalog Relationship",
      rationale:
        "Evidence spans many albums without a single dominant source.",
    };
  }

  if (albums.length >= 3) {
    return {
      label: "Multi-Album Relationship",
      rationale:
        "Several albums contribute meaningfully to the relationship.",
    };
  }

  return {
    label: "Emerging Relationship",
    rationale:
      "A pattern exists, but there is not yet enough evidence for a stronger classification.",
  };
}


const emptyData = {
  artists: [],
  albums: [],
  playlists: [],
  shows: [],
  explore: [],
  eras: [],
};

export default function ArtistIntelligence({ artistName, onBack }) {
  const [queryResult, setQueryResult] = useState(null);
  const [musicData, setMusicData] = useState(emptyData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setMusicData(loadImportedMusicLibrary() || emptyData);
  }, []);

  useEffect(() => {
    const runLookup = async () => {
      if (!artistName) return;

      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          `http://localhost:4000/api/music/query/artist?name=${encodeURIComponent(artistName)}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Artist query failed.");
        }

        setQueryResult(data);
      } catch (err) {
        setError(err.message || "Artist query failed.");
        setQueryResult(null);
      } finally {
        setLoading(false);
      }
    };

    runLookup();
  }, [artistName]);

  const displayArtist = queryResult?.artist || artistName;

  const selectedArtistRecord = useMemo(() => {
    if (!displayArtist) return null;

    return (musicData.artists || []).find(
      (item) => normalizeText(item.name) === normalizeText(displayArtist)
    );
  }, [musicData, displayArtist]);

  const related = useMemo(() => {
    if (!displayArtist) {
      return {
        albums: [],
        playlists: [],
        shows: [],
        explore: [],
      };
    }

    return {
      albums: (musicData.albums || []).filter((item) =>
        itemMentionsArtist(item, displayArtist)
      ),
      playlists: (musicData.playlists || []).filter((item) =>
        itemMentionsArtist(item, displayArtist)
      ),
      shows: (musicData.shows || []).filter((item) =>
        itemMentionsArtist(item, displayArtist)
      ),
      explore: (musicData.explore || []).filter((item) =>
        itemMentionsArtist(item, displayArtist)
      ),
    };
  }, [musicData, displayArtist]);

  const songs = queryResult?.topSongs || [];
  const albums = queryResult?.topAlbums || [];
  const timeline = queryResult?.timeline || [];
  const artistClassification = classifyArtist(queryResult);
  const whyBullets = buildWhyBullets(queryResult, artistClassification);
  const relationshipPattern =
    classifyRelationshipPattern(queryResult);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-gradient-to-br from-white via-blue-50/70 to-purple-50/70 p-6 shadow-sm border border-blue-100 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 dark:border-slate-800">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
              Artist Intelligence
            </p>
            <h2 className="mt-2 text-3xl font-black tracking-tight">
              {displayArtist || "Artist"}
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              Unified artist view combining live query evidence with curated library context.
            </p>
          </div>

          <button
            type="button"
            onClick={onBack}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-bold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Back to Query Workbench
          </button>
        </div>
      </section>

      {error ? (
        <section className="rounded-2xl bg-white/90 p-6 shadow-sm border border-red-200 dark:bg-slate-900/80 dark:border-red-900">
          <h3 className="text-lg font-black">Artist query failed</h3>
          <p className="mt-2 text-sm text-red-600 dark:text-red-300">{error}</p>
        </section>
      ) : loading ? (
        <section className="rounded-2xl bg-white/95 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
          <h3 className="text-lg font-black">Loading artist intelligence...</h3>
        </section>
      ) : (
        <>
          <section className="rounded-2xl bg-white/95 p-6 shadow-sm border border-amber-200 dark:bg-slate-900/80 dark:border-amber-900">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-amber-600 dark:text-amber-300">
              Artist Intelligence
            </p>

            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <StatCard
                label="Relationship Shape"
                value={artistClassification.label}
              />
              <StatCard
                label="Relationship Pattern"
                value={relationshipPattern.label}
              />
              <StatCard
                label="Importance"
                value="Not Rated"
              />
              <StatCard
                label="Confidence"
                value="Medium"
              />
            </div>

            <div className="mt-5 rounded-xl border border-amber-100 bg-amber-50/60 p-4 dark:border-amber-900 dark:bg-amber-950/20">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100">
                Why
              </h3>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
                {whyBullets.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="text-amber-600 dark:text-amber-300">-</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {artistClassification.rationale}
              </p>

              <p className="mt-4 text-sm font-black text-slate-900 dark:text-slate-100">
                Pattern
              </p>
              <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {relationshipPattern.rationale}
              </p>
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Relationship Shape is generated from Library Footprint and Years Represented. Relationship Pattern is generated from album and song evidence.
            </p>
          </section>

          <section className="rounded-2xl bg-white/95 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-300">
              {queryResult?.classification || "Library Evidence"}
            </p>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {queryResult?.notes || "No query evidence loaded yet."}
            </p>

            <div className="mt-5 grid gap-3 md:grid-cols-4">
              <StatCard label="Library Footprint" value={queryResult?.totalPlays ?? 0} />
              <StatCard label="Years Represented" value={queryResult?.yearsActive ?? 0} />
              <StatCard label="First Seen" value={queryResult?.firstSeen || "?"} />
              <StatCard label="Latest Seen" value={queryResult?.latestSeen || "?"} />
            </div>

            {timeline.length ? (
              <div className="mt-6">
                <h4 className="text-sm font-black">Timeline</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  {timeline.map((item) => (
                    <span
                      key={item.year}
                      className="rounded-full border border-slate-300 px-3 py-1 text-xs dark:border-slate-700"
                    >
                      {item.year}: {item.count}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </section>

          <section className="rounded-2xl bg-white/95 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
            <h3 className="text-lg font-black">Top Library Evidence</h3>

            <div className="mt-4 grid gap-6 md:grid-cols-2">
              <div>
                <h4 className="text-sm font-black">Top Songs</h4>
                {songs.length ? (
                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                    {songs.map((item) => (
                      <li key={item.song}>
                        {item.song}
                        {item.plays ? ` - ${item.plays}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No song evidence found.</p>
                )}
              </div>

              <div>
                <h4 className="text-sm font-black">Top Albums</h4>
                {albums.length ? (
                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                    {albums.map((item) => (
                      <li key={item.album}>
                        {item.album}
                        {item.plays ? ` - ${item.plays}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">No album evidence found.</p>
                )}
              </div>
            </div>
          </section>

          <section className="rounded-2xl bg-white/95 p-6 shadow-sm border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800">
            <ArtistSpotlight
              artistName={displayArtist}
              artist={selectedArtistRecord}
              related={related}
            />
          </section>
        </>
      )}
    </div>
  );
}

function ArtistSpotlight({ artistName, artist, related }) {
  return (
    <div className="space-y-5">
      <div>
        <div className="text-xs uppercase text-slate-400 font-bold">
          Curated Library Context
        </div>

        <h3 className="mt-1 text-2xl font-black text-slate-900 dark:text-slate-100">
          {artistName}
        </h3>

        {artist?.favoriteEra && (
          <div className="text-sm text-slate-500 mt-1">
            Favorite era: {artist.favoriteEra}
          </div>
        )}

        {artist?.tags && <TagPills value={artist.tags} />}

        {artist?.notes && (
          <p className="text-sm text-slate-600 mt-3 max-w-3xl dark:text-slate-300">
            {artist.notes}
          </p>
        )}
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
      <h4 className="font-bold text-slate-900 mb-2 dark:text-slate-100">{title}</h4>

      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No related entries yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {items.map((item, index) => (
            <div
              key={`${title}-${index}`}
              className="border border-slate-200 rounded-xl p-4 bg-white dark:border-slate-700 dark:bg-slate-800/80"
            >
              <div className="font-bold text-slate-900 dark:text-slate-100">
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

function StatCard({ label, value }) {
  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
      <div className="text-xs uppercase text-slate-400 font-bold">
        {label}
      </div>

      <div className="text-2xl font-bold text-slate-900 mt-2 dark:text-slate-100">
        {value}
      </div>
    </div>
  );
}
