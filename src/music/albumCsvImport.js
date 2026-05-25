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

export function parseAlbumCsv(csvText) {
  const rows = parseCsvRows(csvText);

  if (rows.length < 2) {
    return { albums: [], skipped: 0, skippedRows: [] };
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

  const isEssential = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    return ["true", "yes", "y", "1", "essential"].includes(normalized);
  };

  const albums = [];
  const skippedRows = [];

  dataRows.forEach((row, index) => {
    const rowNumber = index + 2;

    const album = {
      artist: getValue(row, "artist", "artistName"),
      title: getValue(row, "album", "title", "albumTitle"),
      year: getValue(row, "year", "releaseYear"),
      rating: getValue(row, "rating", "score"),
      favoriteTracks: getValue(row, "favoriteTracks", "favorite tracks", "tracks"),
      tags: getValue(row, "tags", "genres", "genre"),
      essential: isEssential(getValue(row, "essential")),
      coverUrl: getValue(row, "coverUrl", "cover", "cover image url"),
      appleMusicUrl: getValue(row, "appleMusicUrl", "apple music url", "url"),
      notes: getValue(row, "notes", "comments"),
    };

    const missingFields = [];

    if (!album.artist) missingFields.push("artist");
    if (!album.title) missingFields.push("album");

    if (missingFields.length) {
      skippedRows.push({
        rowNumber,
        reason: `missing ${missingFields.join(" and ")}`,
      });
      return;
    }

    albums.push(album);
  });

  return {
    albums,
    skipped: skippedRows.length,
    skippedRows,
  };
}