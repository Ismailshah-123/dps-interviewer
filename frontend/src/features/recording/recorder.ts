/** Pure helpers for MediaRecorder capability detection, kept separate so they are unit-testable. */

// Preference order: Opus in WebM (Chrome, Edge, Firefox), Opus in Ogg, then AAC in MP4 (Safari).
export const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'] as const

export interface RecorderSupport {
  supported: boolean
  reason?: string
  mimeType?: string
}

type RecorderEnv = { isSecureContext?: boolean; mediaDevices?: unknown; MediaRecorder?: { isTypeSupported?: (t: string) => boolean } }

function browserEnv(): RecorderEnv {
  if (typeof window === 'undefined') return {}
  return { isSecureContext: window.isSecureContext, mediaDevices: navigator.mediaDevices, MediaRecorder: window.MediaRecorder }
}

export function detectRecorderSupport(env: RecorderEnv = browserEnv()): RecorderSupport {
  if (env.isSecureContext === false) return { supported: false, reason: 'Recording requires a secure (HTTPS or localhost) connection.' }
  if (!env.mediaDevices) return { supported: false, reason: 'This browser does not allow microphone access.' }
  if (!env.MediaRecorder) return { supported: false, reason: 'This browser cannot record audio. Use a current version of Chrome, Edge, Firefox or Safari.' }
  const isTypeSupported = env.MediaRecorder.isTypeSupported?.bind(env.MediaRecorder)
  const mimeType = MIME_CANDIDATES.find((t) => isTypeSupported?.(t))
  if (!mimeType) return { supported: false, reason: 'None of the audio formats accepted by the server can be recorded in this browser.' }
  return { supported: true, mimeType }
}

/** The media type the backend validates (it strips codec parameters too, this is belt and braces). */
export function uploadMimeType(recorderMime: string): string {
  return recorderMime.split(';')[0].trim()
}

export function fileExtension(mime: string): string {
  const base = uploadMimeType(mime)
  if (base === 'audio/webm') return 'webm'
  if (base === 'audio/ogg') return 'ogg'
  if (base === 'audio/mp4') return 'm4a'
  return 'bin'
}

export function describeMediaError(error: unknown): string {
  const name = error instanceof DOMException || error instanceof Error ? error.name : ''
  switch (name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'Microphone permission was denied. Allow microphone access for this site in the browser settings, then try again.'
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'No microphone was found. Connect a microphone or choose another input device.'
    case 'NotReadableError':
      return 'The microphone is in use by another application or could not be started.'
    default:
      return 'The microphone could not be started.'
  }
}

/** Root-mean-square level of a time-domain buffer, scaled to 0..1 for a meter. */
export function rmsLevel(samples: Uint8Array): number {
  let sum = 0
  for (let i = 0; i < samples.length; i++) {
    const v = (samples[i] - 128) / 128
    sum += v * v
  }
  return Math.min(1, Math.sqrt(sum / Math.max(1, samples.length)) * 3)
}
