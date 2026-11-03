/**
 * Durable, browser-local storage for in-progress recordings.
 *
 * MediaRecorder emits a chunk every few seconds; each chunk is written to IndexedDB at once and
 * then released, so a 40-minute interview never sits in one JavaScript buffer and survives a tab
 * crash or accidental close. Data is removed only after the backend confirms durable storage.
 * The chunks never leave the device except through the authenticated upload.
 */
const DB_NAME = 'dps-recordings'
const DB_VERSION = 1
const CHUNKS = 'chunks'
const SESSIONS = 'sessions'

export interface LocalRecordingSession {
  interviewId: string
  mimeType: string
  startedAt: string
  durationMs: number
  chunkCount: number
  finalized: boolean
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('IndexedDB is not available in this browser'))
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(CHUNKS)) {
        const store = db.createObjectStore(CHUNKS, { keyPath: ['interviewId', 'seq'] })
        store.createIndex('interviewId', 'interviewId')
      }
      if (!db.objectStoreNames.contains(SESSIONS)) db.createObjectStore(SESSIONS, { keyPath: 'interviewId' })
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

function tx<T>(stores: string[], mode: IDBTransactionMode, run: (t: IDBTransaction) => IDBRequest<T> | void): Promise<T | undefined> {
  return openDb().then(
    (db) =>
      new Promise<T | undefined>((resolve, reject) => {
        const t = db.transaction(stores, mode)
        const req = run(t)
        t.oncomplete = () => {
          db.close()
          resolve(req ? req.result : undefined)
        }
        t.onerror = () => reject(t.error)
        t.onabort = () => reject(t.error ?? new Error('Storage transaction aborted (the device may be out of space)'))
      }),
  )
}

export async function saveSession(session: LocalRecordingSession) {
  await tx([SESSIONS], 'readwrite', (t) => t.objectStore(SESSIONS).put(session))
}

export async function getSession(interviewId: string): Promise<LocalRecordingSession | undefined> {
  return tx<LocalRecordingSession>([SESSIONS], 'readonly', (t) => t.objectStore(SESSIONS).get(interviewId))
}

export async function appendChunk(interviewId: string, seq: number, data: Blob) {
  await tx([CHUNKS], 'readwrite', (t) => t.objectStore(CHUNKS).put({ interviewId, seq, data }))
}

/** Reassemble the recording. The Blob references stored chunks, so the browser can page it to disk. */
export async function assembleRecording(interviewId: string, mimeType: string): Promise<Blob> {
  const rows = (await tx<{ seq: number; data: Blob }[]>([CHUNKS], 'readonly', (t) => t.objectStore(CHUNKS).index('interviewId').getAll(interviewId))) ?? []
  rows.sort((a, b) => a.seq - b.seq)
  return new Blob(
    rows.map((r) => r.data),
    { type: mimeType },
  )
}

export async function clearRecording(interviewId: string) {
  const db = await openDb()
  await new Promise<void>((resolve, reject) => {
    const t = db.transaction([CHUNKS, SESSIONS], 'readwrite')
    t.objectStore(SESSIONS).delete(interviewId)
    const range = IDBKeyRange.bound([interviewId, 0], [interviewId, Number.MAX_SAFE_INTEGER])
    t.objectStore(CHUNKS).delete(range)
    t.oncomplete = () => {
      db.close()
      resolve()
    }
    t.onerror = () => reject(t.error)
  })
}

export async function storageEstimate(): Promise<{ available: number | null }> {
  if (!navigator.storage?.estimate) return { available: null }
  const { quota = 0, usage = 0 } = await navigator.storage.estimate()
  return { available: quota - usage }
}
