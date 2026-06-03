import { booksMockData } from "./data/booksMockData";

function countBy(items, selector) {
  return items.reduce((counts, item) => {
    const key = selector(item) || "Unknown";
    counts[key] = (counts[key] || 0) + 1;
    return counts;
  }, {});
}

function flattenThemes(books) {
  return books.flatMap((book) => book.themes || []);
}

function sortEntriesDescending(entries) {
  return [...entries].sort((a, b) => b[1] - a[1]);
}

export default function BooksView() {
  const books = booksMockData;

  const currentlyReading = books.filter((book) => book.status === "Current");

  const recentlyFinished = books
    .filter((book) => book.status === "Finished")
    .sort((a, b) => (b.readYear || 0) - (a.readYear || 0))
    .slice(0, 3);

  const timelineYears = [
    ...new Set(
      books
        .filter((book) => book.readYear)
        .map((book) => book.readYear)
    ),
  ].sort((a, b) => b - a);

  const impactCounts = sortEntriesDescending(
    Object.entries(countBy(books, (book) => book.impact))
  );

  const themeCounts = sortEntriesDescending(
    Object.entries(countBy(flattenThemes(books), (theme) => theme))
  );

  return (
    <main className="space-y-6">
      <section>
        <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
          Library
        </p>
        <h1 className="text-3xl font-semibold text-slate-100">Books</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-400">
          What you are reading now, what you have read, and the ideas that keep
          returning.
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-slate-100">
            Currently Reading
          </h2>

          {currentlyReading.length ? (
            <div className="mt-4 space-y-3">
              {currentlyReading.map((book) => (
                <div key={book.id}>
                  <div className="font-medium text-slate-100">
                    {book.title}
                  </div>
                  <div className="text-sm text-slate-400">{book.author}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-400">No active books.</p>
          )}
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-slate-100">
            Recently Finished
          </h2>

          <div className="mt-4 space-y-3">
            {recentlyFinished.map((book) => (
              <div key={book.id}>
                <div className="font-medium text-slate-100">
                  {book.title}
                </div>
                <div className="text-sm text-slate-400">{book.readYear}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-slate-100">
            Reading Timeline
          </h2>

          <div className="mt-4 flex flex-wrap gap-2">
            {timelineYears.map((year) => (
              <span
                key={year}
                className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-slate-300"
              >
                {year}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-slate-100">
            Impact Distribution
          </h2>
          <div className="mt-4 space-y-3">
            {impactCounts.map(([impact, count]) => (
              <div
                key={impact}
                className="flex items-center justify-between rounded-xl bg-slate-900/70 px-4 py-3"
              >
                <span className="text-sm text-slate-300">{impact}</span>
                <span className="text-sm font-semibold text-slate-100">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-slate-100">
            Theme Signals
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {themeCounts.map(([theme, count]) => (
              <span
                key={theme}
                className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-sm text-slate-300"
              >
                {theme} · {count}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
        <h2 className="text-lg font-semibold text-slate-100">Library Shelf</h2>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {books.map((book) => (
            <article
              key={book.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-100">
                    {book.title}
                  </h3>
                  <p className="text-sm text-slate-400">{book.author}</p>
                </div>

                <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-300">
                  {book.impact}
                </span>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-slate-500">Published</dt>
                  <dd className="text-slate-300">
                    {book.publicationYear || "Unknown"}
                  </dd>
                </div>

                <div>
                  <dt className="text-slate-500">Read Year</dt>
                  <dd className="text-slate-300">
                    {book.readYear || "Unknown"}
                  </dd>
                </div>

                <div>
                  <dt className="text-slate-500">Format</dt>
                  <dd className="text-slate-300">{book.format}</dd>
                </div>

                <div>
                  <dt className="text-slate-500">Times Read</dt>
                  <dd className="text-slate-300">{book.timesRead}</dd>
                </div>
              </dl>

              <div className="mt-4 flex flex-wrap gap-2">
                {(book.themes || []).map((theme) => (
                  <span
                    key={theme}
                    className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
