export const IMPORTED_BOOKS_SCHEMA_VERSION = 1;

export const BOOK_IMPORT_SOURCES = {
  CSV_IMPORT: "csv-import",
  MANUAL_ENTRY: "manual-entry",
  GENERIC_JSON: "generic-json",
  MANUAL_BACKUP: "manual-backup",
};

export const BOOK_FORMATS = [
  "hardcover",
  "paperback",
  "ebook",
  "audiobook",
];

export const BOOK_SOURCES = [
  "owned",
  "library",
  "borrowed",
  "audible",
  "kindle",
];

export const BOOK_STATUSES = [
  "unread",
  "reading",
  "completed",
  "abandoned",
];

export function createEmptyBooksLibrary() {
  return {
    schemaVersion: IMPORTED_BOOKS_SCHEMA_VERSION,
    books: {},
    authors: {},
    quotes: {},
    notes: {},
    readingSessions: {},
    imports: [],
  };
}

export function createBookImportRecord({
  source = BOOK_IMPORT_SOURCES.GENERIC_JSON,
  fileName = "",
  bookCount = 0,
  authorCount = 0,
  quoteCount = 0,
  noteCount = 0,
} = {}) {
  return {
    id: `book-import-${Date.now()}`,
    source,
    fileName,
    importedAt: new Date().toISOString(),
    bookCount,
    authorCount,
    quoteCount,
    noteCount,
  };
}

export function createEmptyBook(overrides = {}) {
  const now = new Date().toISOString();

  return {
    id: `book-${Date.now()}`,
    title: "",
    subtitle: "",
    authorIds: [],
    publisher: "",
    publicationYear: "",
    format: "paperback",
    source: "owned",
    status: "unread",
    purchasedDate: "",
    startedDate: "",
    completedDate: "",
    rereadCount: 0,
    rating: "",
    pageCount: "",
    genre: "",
    tags: [],
    isbn: "",
    coverUrl: "",
    favorite: false,
    notesCount: 0,
    quotesCount: 0,
    createdAt: now,
    updatedAt: now,
    ...overrides,
  };
}