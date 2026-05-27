import {
  BOOK_FORMATS,
  BOOK_IMPORT_SOURCES,
  BOOK_SOURCES,
  BOOK_STATUSES,
  createBookImportRecord,
  createEmptyBook,
} from "./bookSchema";

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/['"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function normalizeChoice(value, allowedValues, fallback) {
  const normalized = String(value || "").trim().toLowerCase();

  if (!normalized) return fallback;

  return allowedValues.includes(normalized) ? normalized : fallback;
}

function normalizeNumberString(value) {
  const trimmed = String(value || "").trim();
  return trimmed;
}

function createAuthorId(authorName) {
  const slug = slugify(authorName);
  return slug ? `author-${slug}` : `author-${Date.now()}`;
}

function createBookId(book) {
  const slug = slugify(`${book.title}-${book.author}`);
  return slug ? `book-${slug}` : `book-${Date.now()}`;
}

function createQuoteId(bookId, index) {
  return `quote-${bookId.replace(/^book-/, "")}-${index + 1}`;
}

function createCanonicalBookKey(book) {
  return slugify(`${book?.title || ""}-${book?.author || ""}`);
}

function createCanonicalQuoteKey(quote) {
  return slugify(`${quote?.bookId || ""}-${quote?.quote || ""}`);
}

function findExistingBookIdByKey(books, importedBook) {
  const importedKey = createCanonicalBookKey(importedBook);

  if (!importedKey) return "";

  return Object.values(books || {}).find(
    (existingBook) => createCanonicalBookKey(existingBook) === importedKey
  )?.id || "";
}

export function normalizeImportedBooks(parsedBooks, { fileName = "" } = {}) {
  const now = new Date().toISOString();

  const books = {};
  const authors = {};
  const quotes = {};

  parsedBooks.forEach((parsedBook, index) => {
    const authorName = String(parsedBook.author || "").trim();
    const authorId = createAuthorId(authorName);

    if (authorName && !authors[authorId]) {
      authors[authorId] = {
        id: authorId,
        name: authorName,
        tags: [],
        createdAt: now,
        updatedAt: now,
      };
    }

    const bookId = createBookId(parsedBook);

    const quoteText = String(parsedBook.quote || "").trim();

    const book = createEmptyBook({
      id: bookId,
      title: String(parsedBook.title || "").trim(),
      author: authorName,
      authorIds: authorId ? [authorId] : [],
      publisher: String(parsedBook.publisher || "").trim(),
      publicationYear: normalizeNumberString(parsedBook.publicationYear),
      format: normalizeChoice(parsedBook.format, BOOK_FORMATS, "paperback"),
      source: normalizeChoice(parsedBook.source, BOOK_SOURCES, "owned"),
      status: normalizeChoice(parsedBook.status, BOOK_STATUSES, "unread"),
      purchasedDate: String(parsedBook.purchasedDate || "").trim(),
      startedDate: String(parsedBook.startedDate || "").trim(),
      completedDate: String(parsedBook.completedDate || "").trim(),
      firstCompletedDate: String(parsedBook.completedDate || "").trim(),
      lastCompletedDate: String(parsedBook.completedDate || "").trim(),
      rereadCount: normalizeNumberString(parsedBook.rereadCount),
      rating: normalizeNumberString(parsedBook.rating),
      pageCount: normalizeNumberString(parsedBook.pageCount),
      genre: String(parsedBook.genre || "").trim(),
      tags: Array.isArray(parsedBook.tags) ? parsedBook.tags : [],
      isbn: String(parsedBook.isbn || "").trim(),
      coverUrl: String(parsedBook.coverUrl || "").trim(),
      favorite: Boolean(parsedBook.favorite),
      notesCount: parsedBook.notes ? 1 : 0,
      quotesCount: quoteText ? 1 : 0,
      notes: String(parsedBook.notes || "").trim(),
      createdAt: now,
      updatedAt: now,
    });

    books[bookId] = book;

    if (quoteText) {
      const quoteId = createQuoteId(bookId, index);

      quotes[quoteId] = {
        id: quoteId,
        bookId,
        quote: quoteText,
        author: authorName,
        tags: book.tags,
        capturedAt: now,
        createdAt: now,
        updatedAt: now,
      };
    }
  });

  return {
    books,
    authors,
    quotes,
    notes: {},
    readingSessions: {},
    imports: [
      createBookImportRecord({
        source: BOOK_IMPORT_SOURCES.CSV_IMPORT,
        fileName,
        bookCount: Object.keys(books).length,
        authorCount: Object.keys(authors).length,
        quoteCount: Object.keys(quotes).length,
        noteCount: 0,
      }),
    ],
  };
}

export function mergeBooksLibrary(baseLibrary, importedLibrary) {
  const mergedBooks = { ...(baseLibrary?.books || {}) };
  const mergedAuthors = {
    ...(baseLibrary?.authors || {}),
    ...(importedLibrary?.authors || {}),
  };
  const mergedQuotes = { ...(baseLibrary?.quotes || {}) };
  const quoteBookIdMap = {};

  Object.values(importedLibrary?.books || {}).forEach((importedBook) => {
    const existingBookId = findExistingBookIdByKey(mergedBooks, importedBook);

    if (existingBookId) {
      quoteBookIdMap[importedBook.id] = existingBookId;

      mergedBooks[existingBookId] = {
        ...importedBook,
        ...mergedBooks[existingBookId],
        tags: Array.from(
          new Set([
            ...(mergedBooks[existingBookId].tags || []),
            ...(importedBook.tags || []),
          ])
        ),
        quotesCount:
          Number(mergedBooks[existingBookId].quotesCount || 0) +
          Number(importedBook.quotesCount || 0),
        notesCount:
          Number(mergedBooks[existingBookId].notesCount || 0) +
          Number(importedBook.notesCount || 0),
        updatedAt: new Date().toISOString(),
      };

      return;
    }

    quoteBookIdMap[importedBook.id] = importedBook.id;
    mergedBooks[importedBook.id] = importedBook;
  });

  Object.values(importedLibrary?.quotes || {}).forEach((importedQuote) => {
    const quote = {
      ...importedQuote,
      bookId: quoteBookIdMap[importedQuote.bookId] || importedQuote.bookId,
    };

    const quoteKey = createCanonicalQuoteKey(quote);
    const duplicateQuoteExists = Object.values(mergedQuotes).some(
      (existingQuote) => createCanonicalQuoteKey(existingQuote) === quoteKey
    );

    if (!duplicateQuoteExists) {
      mergedQuotes[quote.id] = quote;
    }
  });

  return {
    ...baseLibrary,
    books: mergedBooks,
    authors: mergedAuthors,
    quotes: mergedQuotes,
    notes: {
      ...(baseLibrary?.notes || {}),
      ...(importedLibrary?.notes || {}),
    },
    readingSessions: {
      ...(baseLibrary?.readingSessions || {}),
      ...(importedLibrary?.readingSessions || {}),
    },
    imports: [
      ...(baseLibrary?.imports || []),
      ...(importedLibrary?.imports || []),
    ],
  };
}