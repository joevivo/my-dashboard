import { BookOpen, Quote, Library, Bookmark } from "lucide-react";

const sampleBooks = [
  {
    id: "book-1",
    title: "Meditations",
    author: "Marcus Aurelius",
    status: "reading",
    rating: "10",
    format: "paperback",
    tags: ["stoicism", "philosophy"],
  },
  {
    id: "book-2",
    title: "The Republic",
    author: "Plato",
    status: "completed",
    rating: "9",
    format: "hardcover",
    tags: ["philosophy", "politics"],
  },
  {
    id: "book-3",
    title: "The Myth of Sisyphus",
    author: "Albert Camus",
    status: "completed",
    rating: "10",
    format: "ebook",
    tags: ["existentialism", "philosophy"],
  },
];

const sampleQuotes = [
  {
    id: "quote-1",
    quote:
      "The happiness of your life depends upon the quality of your thoughts.",
    author: "Marcus Aurelius",
  },
  {
    id: "quote-2",
    quote:
      "One must imagine Sisyphus happy.",
    author: "Albert Camus",
  },
];

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

export default function BooksView() {
  const currentlyReading = sampleBooks.filter(
    (book) => book.status === "reading"
  );

  return (
    <div className="space-y-6 text-zinc-100">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">
          Books Intelligence
        </h1>

        <p className="mt-1 text-sm text-zinc-400">
          Reading operations, notes, quotes, and intellectual tracking.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Library}
          label="Total Books"
          value={sampleBooks.length}
        />

        <StatCard
          icon={BookOpen}
          label="Currently Reading"
          value={currentlyReading.length}
        />

        <StatCard
          icon={Bookmark}
          label="Completed"
          value={
            sampleBooks.filter((book) => book.status === "completed").length
          }
        />

        <StatCard
          icon={Quote}
          label="Quotes Captured"
          value={sampleQuotes.length}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5 xl:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-zinc-100">
                Library
              </h2>

              <p className="text-sm text-zinc-500">
                Operational reading inventory
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-zinc-800 text-zinc-500">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Title</th>
                  <th className="px-3 py-2 text-left font-medium">Author</th>
                  <th className="px-3 py-2 text-left font-medium">Status</th>
                  <th className="px-3 py-2 text-left font-medium">Rating</th>
                  <th className="px-3 py-2 text-left font-medium">Format</th>
                  <th className="px-3 py-2 text-left font-medium">Tags</th>
                </tr>
              </thead>

              <tbody>
                {sampleBooks.map((book) => (
                  <tr
                    key={book.id}
                    className="border-b border-zinc-800/60"
                  >
                    <td className="px-3 py-3 font-medium text-zinc-200">
                      {book.title}
                    </td>

                    <td className="px-3 py-3 text-zinc-400">
                      {book.author}
                    </td>

                    <td className="px-3 py-3">
                      <span className="rounded-full border border-zinc-700 px-2 py-1 text-xs uppercase tracking-wide text-zinc-300">
                        {book.status}
                      </span>
                    </td>

                    <td className="px-3 py-3 text-zinc-300">
                      {book.rating}
                    </td>

                    <td className="px-3 py-3 text-zinc-400">
                      {book.format}
                    </td>

                    <td className="px-3 py-3 text-zinc-400">
                      {book.tags.join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-zinc-100">
              Quote Surface
            </h2>

            <p className="text-sm text-zinc-500">
              Recently captured philosophical fragments
            </p>
          </div>

          <div className="space-y-4">
            {sampleQuotes.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4"
              >
                <p className="text-sm leading-relaxed text-zinc-300">
                  "{item.quote}"
                </p>

                <p className="mt-3 text-xs uppercase tracking-wide text-zinc-500">
                  {item.author}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}