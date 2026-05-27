import { useEffect, useState } from "react";
import { BookOpen, Quote, Library, Bookmark, Upload, Download } from "lucide-react";
import { seedBooksLibrary } from "./books/seedBooks";
import { loadBooksLibrary, saveBooksLibrary } from "./books/booksStore";
import { parseBookCsv } from "./books/bookCsvImport";
import { mergeBooksLibrary, normalizeImportedBooks } from "./books/bookImportAdapter";
import { downloadBooksBackup, importBooksBackupFile } from "./books/booksBackup";
import {
  getBooksArray,
  getCurrentlyReadingBooks,
  getRecentQuotes,
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

export default function BooksView() {
  const [library, setLibrary] = useState(seedBooksLibrary);
  const [loadStatus, setLoadStatus] = useState("Loading books library...");
  const [importStatus, setImportStatus] = useState("");

  useEffect(() => {
    let isMounted = true;

    loadBooksLibrary()
      .then((storedLibrary) => {
        if (!isMounted) return;

        if (storedLibrary) {
          setLibrary(storedLibrary);
          setLoadStatus("Loaded from local browser storage.");
          return;
        }

        saveBooksLibrary(seedBooksLibrary)
          .then(() => {
            if (isMounted) {
              setLoadStatus("Seed library initialized in local browser storage.");
            }
          })
          .catch((error) => {
            if (isMounted) {
              setLoadStatus(`Seed library active. Storage save failed: ${error.message}`);
            }
          });
      })
      .catch((error) => {
        if (isMounted) {
          setLoadStatus(`Seed library active. Storage unavailable: ${error.message}`);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);
  const books = getBooksArray(library);
  const currentlyReading = getCurrentlyReadingBooks(library);
  const recentQuotes = getRecentQuotes(library);
  const stats = getReadingStats(library);

  const exportKnowledgeBackup = () => {
    downloadBooksBackup(library);
    setImportStatus("Knowledge backup exported.");
  };

  const importKnowledgeBackup = async (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const input = event.target;

    try {
      const restoredLibrary = await importBooksBackupFile(file);

      await saveBooksLibrary(restoredLibrary);

      setLibrary(restoredLibrary);

      setImportStatus(
        `Knowledge backup restored from ${file.name}.`
      );
    } catch (error) {
      setImportStatus(`Backup restore failed: ${error.message}`);
    } finally {
      input.value = "";
    }
  };

  const importBookCsv = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const input = event.target;
    const reader = new FileReader();

    reader.onload = () => {
      try {
        const parsed = parseBookCsv(String(reader.result || ""));

        if (!parsed.books.length) {
          setImportStatus(
            parsed.skipped
              ? `No books imported. Skipped ${parsed.skipped} incomplete row${parsed.skipped === 1 ? "" : "s"}.`
              : "No books imported. Make sure the CSV includes title and author columns."
          );

          input.value = "";
          return;
        }

        const importedLibrary = normalizeImportedBooks(parsed.books, {
          fileName: file.name,
        });

        const mergedLibrary = mergeBooksLibrary(library, importedLibrary);

        saveBooksLibrary(mergedLibrary)
          .then(() => {
            setLibrary(mergedLibrary);
            setImportStatus(
              `Imported ${parsed.books.length} book${parsed.books.length === 1 ? "" : "s"} from ${file.name}.` +
                (parsed.skipped
                  ? ` Skipped ${parsed.skipped} incomplete row${parsed.skipped === 1 ? "" : "s"}.`
                  : "")
            );
          })
          .catch((error) => {
            setImportStatus(`Import parsed, but storage save failed: ${error.message}`);
          });
      } catch (error) {
        setImportStatus(`Import failed: ${error.message}`);
      } finally {
        input.value = "";
      }
    };

    reader.onerror = () => {
      setImportStatus("Import failed: unable to read selected file.");
      input.value = "";
    };

    reader.readAsText(file);
  };

  return (
    <div className="space-y-6 text-zinc-100">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">
          Books Intelligence
        </h1>

        <p className="mt-1 text-sm text-zinc-400">
          Reading operations, notes, quotes, and intellectual tracking.
        </p>

        <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              Books Data Pipeline
            </p>

            <p className="mt-1 text-sm text-zinc-400">
              {loadStatus}
            </p>

            {importStatus ? (
              <p className="mt-1 text-sm text-zinc-300">
                {importStatus}
              </p>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={exportKnowledgeBackup}
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800"
            >
              <Download className="h-4 w-4" />
              Export Backup
            </button>

            <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800">
              <Upload className="h-4 w-4" />
              Restore Backup
              <input
                type="file"
                accept=".json,application/json"
                className="hidden"
                onChange={importKnowledgeBackup}
              />
            </label>

            <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800">
              <Upload className="h-4 w-4" />
              Import Books CSV
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={importBookCsv}
              />
            </label>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Library} label="Total Books" value={stats.totalBooks} />

        <StatCard
          icon={BookOpen}
          label="Currently Reading"
          value={stats.currentlyReading}
        />

        <StatCard
          icon={Bookmark}
          label="Completed"
          value={stats.completed}
        />

        <StatCard
          icon={Quote}
          label="Quotes Captured"
          value={stats.quotes}
        />
      </div>

      {currentlyReading.length ? (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-zinc-100">
              Currently Reading
            </h2>

            <p className="text-sm text-zinc-500">
              Active reading queue and current intellectual focus.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {currentlyReading.map((book) => (
              <div
                key={book.id}
                className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4"
              >
                <p className="font-semibold text-zinc-100">{book.title}</p>

                <p className="mt-1 text-sm text-zinc-400">{book.author}</p>

                <div className="mt-3 flex flex-wrap gap-2">
                  {book.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

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
                {books.map((book) => (
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
                      {book.rating || "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â"}
                    </td>

                    <td className="px-3 py-3 text-zinc-400">
                      {book.format || "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â"}
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
            {recentQuotes.map((item) => (
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