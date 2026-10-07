const DATABASE_NAME = "sismolab-local-map";
const DATABASE_VERSION = 1;
const STORE_NAME = "images";
const IMAGE_KEY = "background";

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE_NAME)) {
        request.result.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      database.close();
      reject(request.error);
    };
  });
}

async function transact(mode, action) {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, mode);
    const request = action(transaction.objectStore(STORE_NAME));
    let result = null;
    request.onsuccess = () => {
      result = request.result ?? null;
    };
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => {
      database.close();
      resolve(result);
    };
    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
    transaction.onabort = () => {
      database.close();
      reject(transaction.error);
    };
  });
}

export const localMapImageStorage = {
  load: () => transact("readonly", (store) => store.get(IMAGE_KEY)),
  save: (image) => transact("readwrite", (store) => store.put(image, IMAGE_KEY)),
  clear: () => transact("readwrite", (store) => store.delete(IMAGE_KEY)),
};
