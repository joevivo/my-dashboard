import React, { useEffect, useMemo, useState } from "react";

const categories = [
  "All",
  "Saved",
  "AI",
  "Baseball",
  "Chicago",
  "Music",
  "Markets",
];

export default function NewsView() {
  const [stories, setStories] = useState([]);
  const [feeds, setFeeds] = useState([]);
  const [savedStories, setSavedStories] = useState([]);
  const [error, setError] = useState("");
  const [feedError, setFeedError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [showFeedManager, setShowFeedManager] = useState(false);
  const [newFeed, setNewFeed] = useState({
    name: "",
    url: "",
    category: "General",
  });
  const [editingFeedIndex, setEditingFeedIndex] = useState(null);
  const [editingFeed, setEditingFeed] = useState({
    name: "",
    url: "",
    category: "General",
  });
  async function loadNews() {
    try {
      setError("");

      const response = await fetch("http://localhost:4000/api/news");

      if (!response.ok) {
        throw new Error("Failed to load news");
      }

      const data = await response.json();
      setStories(data);
    } catch (err) {
      setError("News is unavailable because the local backend is not reachable. Start the backend with: cd C:\\Users\\joevi\\my-dashboard\\server and then run node .\\index.js");
    }
  }

  async function loadFeeds() {
    try {
      setFeedError("");

      const response = await fetch("http://localhost:4000/api/news/feeds");

      if (!response.ok) {
        throw new Error("Failed to load RSS feeds");
      }

      const data = await response.json();
      setFeeds(data);
    } catch (err) {
      setFeedError(err.message);
    }
  }

  useEffect(() => {
    loadNews();
    loadFeeds();

    const saved = localStorage.getItem("savedNewsStories");

    if (saved) {
      setSavedStories(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      "savedNewsStories",
      JSON.stringify(savedStories)
    );
  }, [savedStories]);

  function isSaved(story) {
    return savedStories.some(
      (saved) => saved.link === story.link
    );
  }
  async function addFeed() {
    try {
      setFeedError("");

      if (!newFeed.url.trim()) {
        setFeedError("RSS URL is required.");
        return;
      }

      const response = await fetch("http://localhost:4000/api/news/feeds", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newFeed),
      });

      if (!response.ok) {
        throw new Error("Failed to add RSS feed");
      }

      const data = await response.json();
      setFeeds(data);
      setNewFeed({
        name: "",
        url: "",
        category: "General",
      });

      await loadNews();
    } catch (err) {
      setFeedError(err.message);
    }
  }
  function startEditingFeed(feed, index) {
    setEditingFeedIndex(index);

    if (typeof feed === "string") {
      setEditingFeed({
        name: "RSS Feed",
        url: feed,
        category: "General",
      });
      return;
    }

    setEditingFeed({
      name: feed.name || "RSS Feed",
      url: feed.url || "",
      category: feed.category || "General",
    });
  }

  function cancelEditingFeed() {
    setEditingFeedIndex(null);
    setEditingFeed({
      name: "",
      url: "",
      category: "General",
    });
  }

  async function saveEditingFeed() {
    try {
      setFeedError("");

      if (editingFeedIndex === null) {
        setFeedError("No feed selected for editing.");
        return;
      }

      if (!editingFeed.url.trim()) {
        setFeedError("RSS URL is required.");
        return;
      }

      const response = await fetch(
        `http://localhost:4000/api/news/feeds/${editingFeedIndex}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(editingFeed),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update RSS feed");
      }

      const data = await response.json();
      setFeeds(data);
      cancelEditingFeed();
      await loadNews();
    } catch (err) {
      setFeedError(err.message);
    }
  }
  async function deleteFeed(index) {
    try {
      setFeedError("");

      const response = await fetch(
        `http://localhost:4000/api/news/feeds/${index}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete RSS feed");
      }

      const data = await response.json();
      setFeeds(data);
      await loadNews();
    } catch (err) {
      setFeedError(err.message);
    }
    }

  function toggleSaved(story) {
    if (isSaved(story)) {
      setSavedStories((prev) =>
        prev.filter((saved) => saved.link !== story.link)
      );
    } else {
      setSavedStories((prev) => [story, ...prev]);
    }
  }

  const filteredStories = useMemo(() => {
    if (selectedCategory === "Saved") {
      return savedStories;
    }

    if (selectedCategory === "All") {
      return stories;
    }

    return stories.filter(
      (story) => story.category === selectedCategory
    );
  }, [stories, savedStories, selectedCategory]);

  return (
    <div className="space-y-5">
      <div className="dashboard-panel p-5">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">News</h1>

            <p className="text-sm text-slate-500 mt-1">
              Latest stories from your curated RSS feeds.
            </p>
          </div>

          <div className="text-xs text-slate-400">
            {filteredStories.length} shown Ãƒâ€šÃ‚Â· {stories.length} total
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-4">
          {categories.map((category) => {
            const active = selectedCategory === category;

            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                  active
                    ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                    : "bg-white/80 text-slate-700 border-slate-200 hover:bg-slate-100 hover:border-slate-300 dark:bg-slate-800/80 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700 dark:hover:border-slate-600"
                }`}
              >
                {category}
              </button>
            );
          })}
        </div>
      </div>
      <div className="dashboard-panel p-5">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Manage RSS Feeds
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Add or remove feeds used by the News dashboard.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={loadNews}
              className="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Refresh Stories
            </button>

            <button
              onClick={() => setShowFeedManager((prev) => !prev)}
              className="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {showFeedManager ? "Hide Feeds" : "Manage Feeds"}
            </button>
          </div>
        </div>

        {showFeedManager && (
          <>
        {feedError && (
          <p className="text-sm text-red-600 mb-3">{feedError}</p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
          <input
            value={newFeed.name}
            onChange={(e) =>
              setNewFeed((prev) => ({ ...prev, name: e.target.value }))
            }
            placeholder="Feed name"
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
          />

          <input
            value={newFeed.category}
            onChange={(e) =>
              setNewFeed((prev) => ({ ...prev, category: e.target.value }))
            }
            placeholder="Category"
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
          />

          <input
            value={newFeed.url}
            onChange={(e) =>
              setNewFeed((prev) => ({ ...prev, url: e.target.value }))
            }
            placeholder="RSS URL"
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm md:col-span-2"
          />
        </div>

        <button
          onClick={addFeed}
          className="mb-4 bg-slate-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-slate-800"
        >
          Add Feed
        </button>

        {feeds.length === 0 ? (
          <p className="text-sm text-slate-500">No feeds configured.</p>
        ) : (
          <div className="space-y-2">
            {feeds.map((feed, index) => {
              const feedName =
                typeof feed === "string" ? "RSS Feed" : feed.name || "RSS Feed";
              const feedUrl = typeof feed === "string" ? feed : feed.url;
              const feedCategory =
                typeof feed === "string" ? "General" : feed.category || "General";

              return (
                <div
                  key={`${feedUrl}-${index}`}
                  className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 border border-slate-200 rounded-lg bg-slate-50 px-3 py-2"
                >
                  {editingFeedIndex === index ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2 flex-1">
                      <input
                        value={editingFeed.name}
                        onChange={(e) =>
                          setEditingFeed((prev) => ({
                            ...prev,
                            name: e.target.value,
                          }))
                        }
                        className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
                      />

                      <input
                        value={editingFeed.category}
                        onChange={(e) =>
                          setEditingFeed((prev) => ({
                            ...prev,
                            category: e.target.value,
                          }))
                        }
                        className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
                      />

                      <input
                        value={editingFeed.url}
                        onChange={(e) =>
                          setEditingFeed((prev) => ({
                            ...prev,
                            url: e.target.value,
                          }))
                        }
                        className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                  ) : (
                    <div>
                      <div className="font-semibold text-sm text-slate-900">
                        {feedName}
                      </div>
                      <div className="text-xs text-slate-500">
                        {feedCategory} Ãƒâ€šÃ‚Â· {feedUrl}
                      </div>
                    </div>
                  )}

                      <div className="flex gap-2 self-start md:self-auto">
  {editingFeedIndex === index ? (
    <>
      <button
        onClick={saveEditingFeed}
        className="text-xs px-2 py-1 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
      >
        Save
      </button>

      <button
        onClick={cancelEditingFeed}
        className="text-xs px-2 py-1 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
      >
        Cancel
      </button>
    </>
  ) : (
    <>
      <button
        onClick={() => startEditingFeed(feed, index)}
        className="text-xs px-2 py-1 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
      >
        Edit
      </button>

      <button
        onClick={() => deleteFeed(index)}
        className="text-xs px-2 py-1 rounded-lg border border-red-200 bg-red-50 text-red-700 hover:bg-red-100"
      >
        Delete
      </button>
    </>
  )}
</div>
                </div>
              );
            })}
          </div>
        )}
          </>
        )}
      </div>
      <div className="dashboard-panel p-5">
        {error ? (
          <p className="text-red-600 text-sm">{error}</p>
        ) : filteredStories.length === 0 ? (
          <p className="text-sm text-slate-500">
            No stories found.
          </p>
        ) : (
          <div className="space-y-3">
            {filteredStories.map((story, index) => {
              const saved = isSaved(story);

              return (
                <article
                  key={`${story.link}-${index}`}
                  className="group border border-slate-200 rounded-xl p-4 bg-slate-50 hover:bg-white hover:border-slate-300 hover:shadow-sm transition dark:border-slate-700 dark:bg-slate-800/70 dark:hover:bg-slate-800 dark:hover:border-slate-600"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="text-xs font-medium text-slate-500">
                        {story.source}
                      </div>

                      {story.pubDate && (
                        <div className="text-xs text-slate-400 mt-1">
                          {new Date(story.pubDate).toLocaleString()}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <div className="text-xs px-2 py-1 rounded-lg bg-slate-200/80 text-slate-700">
                        {story.category || "General"}
                      </div>

                      <button
                        onClick={() => toggleSaved(story)}
                        className={`text-xs px-2 py-1 rounded-lg border transition ${
                          saved
                            ? "bg-amber-200 border-amber-300 text-amber-950"
                            : "bg-white/90 border-slate-200 text-slate-600 hover:bg-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700"
                        }`}
                      >
                        {saved ? "Saved" : "Save"}
                      </button>
                    </div>
                  </div>

                  <a
                    href={story.link}
                    target="_blank"
                    rel="noreferrer"
                    className="block"
                  >
                    <div className="font-semibold text-slate-900 leading-snug group-hover:underline">
                      {story.title}
                    </div>
                  </a>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

