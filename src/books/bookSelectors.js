function valuesFromRecord(record) {
  if (!record) return [];
  if (Array.isArray(record)) return record;
  return Object.values(record);
}

function normalizeDateValue(value) {
  if (!value) return 0;

  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function getBooksArray(library) {
  return valuesFromRecord(library?.books);
}

export function getAuthorsArray(library) {
  return valuesFromRecord(library?.authors);
}

export function getQuotesArray(library) {
  return valuesFromRecord(library?.quotes);
}

export function getNotesArray(library) {
  return valuesFromRecord(library?.notes);
}

export function getReadingSessionsArray(library) {
  return valuesFromRecord(library?.readingSessions);
}

export function getCurrentlyReadingBooks(library) {
  return getBooksArray(library).filter((book) => book.status === "reading");
}

export function getCompletedBooks(library) {
  return getBooksArray(library).filter((book) => book.status === "completed");
}

export function getUnreadBooks(library) {
  return getBooksArray(library).filter((book) => book.status === "unread");
}

export function getAbandonedBooks(library) {
  return getBooksArray(library).filter((book) => book.status === "abandoned");
}

export function getFavoriteBooks(library) {
  return getBooksArray(library).filter((book) => Boolean(book.favorite));
}

export function getBooksByTag(library, tag) {
  const normalizedTag = String(tag || "").trim().toLowerCase();

  if (!normalizedTag) return [];

  return getBooksArray(library).filter((book) =>
    Array.isArray(book.tags)
      ? book.tags.some(
          (bookTag) => String(bookTag || "").trim().toLowerCase() === normalizedTag
        )
      : false
  );
}

export function getRecentQuotes(library, limit = 5) {
  return getQuotesArray(library)
    .slice()
    .sort(
      (a, b) =>
        normalizeDateValue(b.capturedAt || b.createdAt) -
        normalizeDateValue(a.capturedAt || a.createdAt)
    )
    .slice(0, limit);
}

export function getRecentNotes(library, limit = 5) {
  return getNotesArray(library)
    .slice()
    .sort(
      (a, b) =>
        normalizeDateValue(b.updatedAt || b.createdAt) -
        normalizeDateValue(a.updatedAt || a.createdAt)
    )
    .slice(0, limit);
}

export function getRecentlyCompletedBooks(library, limit = 5) {
  return getCompletedBooks(library)
    .slice()
    .sort(
      (a, b) =>
        normalizeDateValue(b.completedDate || b.lastCompletedDate) -
        normalizeDateValue(a.completedDate || a.lastCompletedDate)
    )
    .slice(0, limit);
}

export function getReadingStats(library) {
  const books = getBooksArray(library);
  const quotes = getQuotesArray(library);
  const notes = getNotesArray(library);
  const sessions = getReadingSessionsArray(library);

  const completedBooks = books.filter((book) => book.status === "completed");
  const currentlyReadingBooks = books.filter((book) => book.status === "reading");
  const unreadBooks = books.filter((book) => book.status === "unread");
  const abandonedBooks = books.filter((book) => book.status === "abandoned");
  const favoriteBooks = books.filter((book) => Boolean(book.favorite));

  const currentYear = new Date().getFullYear();

  const completedThisYear = completedBooks.filter((book) => {
    const dateValue = book.completedDate || book.lastCompletedDate;
    if (!dateValue) return false;

    const date = new Date(dateValue);
    return !Number.isNaN(date.getTime()) && date.getFullYear() === currentYear;
  });

  return {
    totalBooks: books.length,
    currentlyReading: currentlyReadingBooks.length,
    completed: completedBooks.length,
    completedThisYear: completedThisYear.length,
    unread: unreadBooks.length,
    abandoned: abandonedBooks.length,
    favorites: favoriteBooks.length,
    quotes: quotes.length,
    notes: notes.length,
    readingSessions: sessions.length,
  };
}