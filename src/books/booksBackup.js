export function createBooksBackupPayload(library) {
  return {
    exportedAt: new Date().toISOString(),
    schemaVersion: library?.schemaVersion || 1,
    data: library,
  };
}

export function downloadBooksBackup(library) {
  const payload = createBooksBackupPayload(library);

  const blob = new Blob(
    [JSON.stringify(payload, null, 2)],
    { type: "application/json" }
  );

  const url = URL.createObjectURL(blob);

  const timestamp = new Date()
    .toISOString()
    .replace(/[:.]/g, "-");

  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = `defending-sisyphus-backup-${timestamp}.json`;

  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  URL.revokeObjectURL(url);
}

export async function importBooksBackupFile(file) {
  const text = await file.text();

  let parsed;

  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("Backup file is not valid JSON.");
  }

  if (!parsed || typeof parsed !== "object") {
    throw new Error("Backup payload is invalid.");
  }

  if (!parsed.data || typeof parsed.data !== "object") {
    throw new Error("Backup payload is missing data.");
  }

  if (!parsed.data.books || typeof parsed.data.books !== "object") {
    throw new Error("Backup payload is missing books.");
  }

  return parsed.data;
}