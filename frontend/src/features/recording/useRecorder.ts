import { useCallback, useEffect, useRef, useState } from 'react'
import { describeMediaError, detectRecorderSupport, rmsLevel } from './recorder'
import { appendChunk, saveSession } from './recordingStore'

export type RecorderState = 'idle' | 'starting' | 'recording' | 'paused' | 'stopping' | 'stopped' | 'error'

const TIMESLICE_MS = 5000

export function useRecorder(interviewId: string, { maxDurationMs }: { maxDurationMs: number }) {
  const [support] = useState(detectRecorderSupport)
  const [state, setState] = useState<RecorderState>('idle')
  const [elapsedMs, setElapsedMs] = useState(0)
  const [level, setLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([])
  const [deviceId, setDeviceId] = useState<string>('')
  const [permission, setPermission] = useState<PermissionState | 'unknown'>('unknown')

  const recorder = useRef<MediaRecorder | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const audioCtx = useRef<AudioContext | null>(null)
  const raf = useRef<number | null>(null)
  const seq = useRef(0)
  const accumulated = useRef(0)
  const segmentStart = useRef<number | null>(null)
  const writes = useRef<Promise<void>>(Promise.resolve())
  const stopResolver = useRef<(() => void) | null>(null)
  const startedAt = useRef<string>('')

  const currentElapsed = () => accumulated.current + (segmentStart.current ? performance.now() - segmentStart.current : 0)

  const refreshDevices = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return
    const all = await navigator.mediaDevices.enumerateDevices()
    setDevices(all.filter((d) => d.kind === 'audioinput'))
  }, [])

  useEffect(() => {
    void refreshDevices()
    // Permissions API is not available in every browser; treat absence as "unknown".
    navigator.permissions
      ?.query({ name: 'microphone' as PermissionName })
      .then((status) => {
        setPermission(status.state)
        status.onchange = () => setPermission(status.state)
      })
      .catch(() => setPermission('unknown'))
  }, [refreshDevices])

  const releaseMedia = useCallback(() => {
    if (raf.current) cancelAnimationFrame(raf.current)
    raf.current = null
    stream.current?.getTracks().forEach((t) => t.stop())
    stream.current = null
    void audioCtx.current?.close().catch(() => undefined)
    audioCtx.current = null
    setLevel(0)
  }, [])

  const persistSession = useCallback(
    (finalized: boolean) =>
      saveSession({
        interviewId,
        mimeType: recorder.current?.mimeType || support.mimeType || 'audio/webm',
        startedAt: startedAt.current,
        durationMs: Math.round(currentElapsed()),
        chunkCount: seq.current,
        finalized,
      }),
    [interviewId, support.mimeType],
  )

  const start = useCallback(async () => {
    if (!support.supported || !support.mimeType) return
    setError(null)
    setState('starting')
    try {
      const media = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId ? { exact: deviceId } : undefined, echoCancellation: true, noiseSuppression: true, channelCount: 1 },
      })
      stream.current = media
      setPermission('granted')
      void refreshDevices()

      const ctx = new AudioContext()
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 1024
      ctx.createMediaStreamSource(media).connect(analyser)
      audioCtx.current = ctx
      const buf = new Uint8Array(analyser.fftSize)
      const tick = () => {
        analyser.getByteTimeDomainData(buf)
        setLevel(rmsLevel(buf))
        raf.current = requestAnimationFrame(tick)
      }
      tick()

      // ~64 kbit/s Opus: about 19 MB for 40 minutes, enough for speech recognition.
      const rec = new MediaRecorder(media, { mimeType: support.mimeType, audioBitsPerSecond: 64000 })
      recorder.current = rec
      seq.current = 0
      accumulated.current = 0
      startedAt.current = new Date().toISOString()
      rec.ondataavailable = (e) => {
        if (!e.data || e.data.size === 0) return
        const n = seq.current++
        writes.current = writes.current
          .then(() => appendChunk(interviewId, n, e.data))
          .then(() => persistSession(false))
          .catch(() => {
            setError('This device ran out of browser storage while recording. Stop now and upload what was captured.')
          })
      }
      rec.onstop = () => {
        void writes.current.then(() => persistSession(true)).finally(() => {
          setState('stopped')
          stopResolver.current?.()
          stopResolver.current = null
        })
      }
      rec.onerror = () => {
        setError('The recorder stopped unexpectedly. Captured audio has been kept in this browser.')
      }
      media.getAudioTracks()[0]?.addEventListener('ended', () => {
        setError('The microphone was disconnected. Recording stopped; captured audio has been kept.')
        if (rec.state !== 'inactive') rec.stop()
        releaseMedia()
      })
      await persistSession(false)
      rec.start(TIMESLICE_MS)
      segmentStart.current = performance.now()
      setState('recording')
    } catch (e) {
      releaseMedia()
      if (e instanceof DOMException && e.name === 'NotAllowedError') setPermission('denied')
      setError(describeMediaError(e))
      setState('error')
    }
  }, [deviceId, interviewId, persistSession, refreshDevices, releaseMedia, support])

  const pause = useCallback(() => {
    if (recorder.current?.state !== 'recording') return
    recorder.current.pause()
    accumulated.current = currentElapsed()
    segmentStart.current = null
    setState('paused')
  }, [])

  const resume = useCallback(() => {
    if (recorder.current?.state !== 'paused') return
    recorder.current.resume()
    segmentStart.current = performance.now()
    setState('recording')
  }, [])

  /** Resolves once the final chunk has been written to IndexedDB. */
  const stop = useCallback(
    () =>
      new Promise<void>((resolve) => {
        const rec = recorder.current
        if (!rec || rec.state === 'inactive') return resolve()
        accumulated.current = currentElapsed()
        segmentStart.current = null
        stopResolver.current = resolve
        setState('stopping')
        rec.stop()
        releaseMedia()
      }),
    [releaseMedia],
  )

  const reset = useCallback(() => {
    recorder.current = null
    accumulated.current = 0
    setElapsedMs(0)
    setError(null)
    setState('idle')
  }, [])

  // Elapsed-time display and the maximum-duration guard.
  useEffect(() => {
    if (state !== 'recording' && state !== 'paused') return
    const t = setInterval(() => {
      const ms = currentElapsed()
      setElapsedMs(ms)
      if (ms >= maxDurationMs && state === 'recording') {
        setError(`Maximum recording length reached (${Math.round(maxDurationMs / 60000)} minutes). Recording was stopped automatically.`)
        void stop()
      }
    }, 250)
    return () => clearInterval(t)
  }, [state, maxDurationMs, stop])

  // Warn before closing the tab mid-recording. Chunks already captured remain recoverable.
  useEffect(() => {
    if (state !== 'recording' && state !== 'paused') return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [state])

  useEffect(
    () => () => {
      if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop()
      releaseMedia()
    },
    [releaseMedia],
  )

  return { support, state, elapsedMs, level, error, devices, deviceId, setDeviceId, permission, start, pause, resume, stop, reset }
}
