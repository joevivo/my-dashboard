function parseCsvRows(csvText) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let index = 0; index < csvText.length; index += 1) {
    const char = csvText[index];
    const nextChar = csvText[index + 1];

    if (char === '"' && inQuotes && nextChar === '"') {
      field += '"';
      index += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && nextChar === "\n") index += 1;

      row.push(field);

      if (row.some((value) => String(value || "").trim())) {
        rows.push(row);
      }

      row = [];
      field = "";
      continue;
    }

    field += char;
  }

  row.push(field);

  if (row.some((value) => String(value || "").trim())) {
    rows.push(row);
  }

  return rows;
}

function normalizeCsvHeader(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function splitTags(value) {
  return String(value || "")
    .split(/[;,|]/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function normalizeBoolean(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return ["true", "yes", "y", "1", "favorite"].includes(normalized);
}

export function parseBookCsv(csvText) {
  const rows = parseCsvRows(csvText);

  if (rows.length < 2) {
    return { books: [], skipped: 0, skippedRows: [] };
  }

  const headers = rows[0].map(normalizeCsvHeader);
  const dataRows = rows.slice(1);

  const getValue = (row, ...headerNames) => {
    const normalizedNames = headerNames.map(normalizeCsvHeader);

    for (const name of normalizedNames) {
      const index = headers.indexOf(name);
      if (index !== -1) return String(row[index] || "").trim();
    }

    return "";
  };

  const books = [];
  const skippedRows = [];

  dataRows.forEach((row, index) => {
    const rowNumber = index + 2;

    const book = {
      title: getValue(row, "title", "book", "bookTitle"),
      author: getValue(row, "author", "authors", "authorName"),
      publisher: getValue(row, "publisher"),
      publicationYear: getValue(row, "publicationYear", "year", "published", "publishedYear"),
      format: getValue(row, "format", "bookFormat"),
      source: getValue(row, "source", "ownedFrom", "acquiredFrom"),
      status: getValue(row, "status", "readingStatus"),
      purchasedDate: getValue(row, "purchasedDate", "purchaseDate", "acquiredDate"),
      startedDate: getValue(row, "startedDate", "startDate"),
      completedDate: getValue(row, "completedDate", "readDate", "finishedDate"),
      rereadCount: getValue(row, "rereadCount", "rereads"),
      rating: getValue(row, "rating", "score"),
      pageCount: getValue(row, "pageCount", "pages"),
      genre: getValue(row, "genre", "category"),
      tags: splitTags(getValue(row, "tags", "tag", "categories")),
      isbn: getValue(row, "isbn", "isbn13", "isbn10"),
      coverUrl: getValue(row, "coverUrl", "cover", "coverImageUrl"),
      favorite: normalizeBoolean(getValue(row, "favorite", "essential")),
      notes: getValue(row, "notes", "thoughts", "comments"),
      quote: getValue(row, "quote", "favoriteQuote"),
    };

    const missingFields = [];

    if (!book.title) missingFields.push("title");
    if (!book.author) missingFields.push("author");

    if (missingFields.length) {
      skippedRows.push({
        rowNumber,
        reason: `missing ${missingFields.join(" and ")}`,
      });
      return;
    }

    books.push(book);
  });

  return {
    books,
    skipped: skippedRows.length,
    skippedRows,
  };
}