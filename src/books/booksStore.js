const DB_NAME = "defending-sisyphus-books";
const DB_VERSION = 1;
const STORE_NAME = "importedBooks";
const ACTIVE_LIBRARY_KEY = "active-books-library";

function openBooksDatabase() {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(new Error("IndexedDB is not available in this browser."));
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;

      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function runStoreOperation(mode, operation) {
  return openBooksDatabase().then(
    (db) =>
      new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, mode);
        const store = transaction.objectStore(STORE_NAME);
        const request = operation(store);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
        transaction.oncomplete = () => db.close();
        transaction.onerror = () => {
          db.close();
          reject(transaction.error);
        };
      })
  );
}

export function saveBooksLibrary(library) {
  return runStoreOperation("readwrite", (store) =>
    store.put(library, ACTIVE_LIBRARY_KEY)
  );
}

export function loadBooksLibrary() {
  return runStoreOperation("readonly", (store) =>
    store.get(ACTIVE_LIBRARY_KEY)
  );
}

export function clearBooksLibrary() {
  return runStoreOperation("readwrite", (store) =>
    store.delete(ACTIVE_LIBRARY_KEY)
  );
}