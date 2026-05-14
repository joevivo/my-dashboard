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
  const [savedStories, setSavedStories] = useState([]);
  const [error, setError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  useEffect(() => {
    async function loadNews() {
      try {
        const response = await fetch("http://localhost:4000/api/news");

        if (!response.ok) {
          throw new Error("Failed to load news");
        }

        const data = await response.json();
        setStories(data);
      } catch (err) {
        setError(err.message);
      }
    }

    loadNews();

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
            <h1 className="text-xl font-bold text-slate-950">News</h1>

            <p className="text-sm text-slate-500 mt-1">
              Latest stories from your curated RSS feeds.
            </p>
          </div>

          <div className="text-xs text-slate-400">
            {filteredStories.length} shown · {stories.length} total
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
                    : "bg-white/80 text-slate-700 border-slate-200 hover:bg-slate-100 hover:border-slate-300"
                }`}
              >
                {category}
              </button>
            );
          })}
        </div>
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
                  className="group border border-slate-200/80 rounded-xl p-4 bg-slate-50/80 hover:bg-white hover:border-slate-300 hover:shadow-sm transition"
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
                            : "bg-white/90 border-slate-200 text-slate-600 hover:bg-slate-100"
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
                    <div className="font-semibold text-slate-950 leading-snug group-hover:underline">
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
