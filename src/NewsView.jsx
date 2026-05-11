import React, { useEffect, useState } from "react";

export default function NewsView() {
  const [stories, setStories] = useState([]);
  const [error, setError] = useState("");

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
  }, []);

  return (
    <div className="space-y-5">
      <div className="bg-white p-5 rounded border">
        <h1 className="text-xl font-bold">News</h1>

        <p className="text-sm text-gray-500">
          Latest stories from your RSS feeds.
        </p>
      </div>

      <div className="bg-white p-5 rounded border">
        {error ? (
          <p className="text-red-600 text-sm">{error}</p>
        ) : stories.length === 0 ? (
          <p className="text-sm text-slate-500">
            Loading news...
          </p>
        ) : (
          <div className="space-y-3">
            {stories.map((story, index) => (
              <a
                key={`${story.link}-${index}`}
                href={story.link}
                target="_blank"
                rel="noreferrer"
                className="block border rounded p-4 bg-slate-50 hover:bg-slate-100"
              >
                <div className="text-xs text-slate-500 mb-1">
                  {story.source}
                </div>

                <div className="font-bold text-slate-900">
                  {story.title}
                </div>

                {story.pubDate && (
                  <div className="text-xs text-slate-500 mt-2">
                    {new Date(
                      story.pubDate
                    ).toLocaleString()}
                  </div>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}