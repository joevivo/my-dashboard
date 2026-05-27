import { useEffect, useState } from "react";
import { NotebookPen, StickyNote, Tags, Clock } from "lucide-react";
import { seedBooksLibrary } from "./books/seedBooks";
import { loadBooksLibrary } from "./books/booksStore";
import {
  getNotesArray,
  getRecentNotes,
  getReadingStats,
} from "./books/bookSelectors";

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-zinc-500">
            {label}
          </p>

          <p className="mt-2 text-3xl font-semibold text-zinc-100">
            {value}
          </p>
        </div>

        <Icon className="h-6 w-6 text-zinc-500" />
      </div>
    </div>
  );
}

function formatDate(value) {
  if (!value) return "Undated";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Undated";

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function NotesView() {
  const [library, setLibrary] = useState(seedBooksLibrary);
  const [loadStatus, setLoadStatus] = useState("Loading knowledge notes...");

  useEffect(() => {
    let isMounted = true;

    loadBooksLibrary()
      .then((storedLibrary) => {
        if (!isMounted) return;

        if (storedLibrary) {
          setLibrary(storedLibrary);
          setLoadStatus("Loaded from books knowledge store.");
          return;
        }

        setLoadStatus("Seed knowledge library active.");
      })
      .catch((error) => {
        if (isMounted) {
          setLoadStatus(`Seed knowledge library active. Storage unavailable: ${error.message}`);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const notes = getNotesArray(library);
  const recentNotes = getRecentNotes(library, 8);
  const stats = getReadingStats(library);

  const uniqueTags = Array.from(
    new Set(
      notes.flatMap((note) =>
        Array.isArray(note.tags)
          ? note.tags.map((tag) => String(tag || "").trim()).filter(Boolean)
          : []
      )
    )
  );

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Knowledge
            </p>

            <h2 className="mt-2 text-3xl font-semibold text-zinc-100">
              Notes
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-400">
              A lightweight operational surface for reading notes, thought fragments,
              and future cross-linked knowledge captured through the books library.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-xs text-zinc-400">
            {loadStatus}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <StatCard icon={StickyNote} label="Notes" value={notes.length} />
        <StatCard icon={NotebookPen} label="Book Notes" value={stats.notes} />
        <StatCard icon={Tags} label="Tags" value={uniqueTags.length} />
        <StatCard icon={Clock} label="Recent" value={recentNotes.length} />
      </section>

      <section className="rounded-3xl border border-zinc-800 bg-zinc-950 p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-zinc-100">
              Recent Notes
            </h3>
            <p className="mt-1 text-sm text-zinc-500">
              Latest notes from the shared books knowledge store.
            </p>
          </div>
        </div>

        {recentNotes.length ? (
          <div className="space-y-3">
            {recentNotes.map((note) => (
              <article
                key={note.id}
                className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4"
              >
                <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h4 className="font-semibold text-zinc-100">
                      {note.title || "Untitled note"}
                    </h4>

                    <p className="mt-2 text-sm leading-6 text-zinc-400">
                      {note.body || note.content || note.text || "No note body captured yet."}
                    </p>
                  </div>

                  <div className="shrink-0 text-xs uppercase tracking-wide text-zinc-600">
                    {formatDate(note.updatedAt || note.createdAt)}
                  </div>
                </div>

                {Array.isArray(note.tags) && note.tags.length ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {note.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-400"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 p-6 text-sm leading-6 text-zinc-400">
            No notes captured yet. This view is now staged for future quote notes,
            reading fragments, AI research observations, and philosophy entries.
          </div>
        )}
      </section>
    </div>
  );
}