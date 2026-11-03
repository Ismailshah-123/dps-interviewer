import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CircleCheck, CloudUpload, FileAudio, Mic, MicOff, Pause, Play, RotateCcw, Square, Trash2, TriangleAlert } from 'lucide-react'
import { toast } from 'sonner'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Spinner, ToneBadge } from '@/components/common'
import { api, errorMessage } from '@/lib/api'
import { formatBytes, formatDuration } from '@/lib/status'
import type { Interview, Recording } from '@/lib/types'
import { cn } from '@/lib/utils'
import { fileExtension, uploadMimeType } from './recorder'
import { assembleRecording, clearRecording, getSession, storageEstimate, type LocalRecordingSession } from './recordingStore'
import { useRecorder } from './useRecorder'

const MAX_DURATION_MS = 90 * 60 * 1000

function LevelMeter({ level, active }: { level: number; active: boolean }) {
  const bars = 24
  return (
    <div className="flex h-8 items-end gap-0.5" role="meter" aria-label="Microphone input level" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(level * 100)}>
      {Array.from({ length: bars }).map((_, i) => {
        const on = active && level * bars > i
        return <div key={i} className={cn('w-1.5 rounded-sm transition-colors', on ? (i > bars * 0.85 ? 'bg-red-500' : i > bars * 0.6 ? 'bg-amber-500' : 'bg-emerald-500') : 'bg-muted')} style={{ height: `${30 + (i / bars) * 70}%` }} />
      })}
    </div>
  )
}

export function RecordingPanel({ interview, maxUploadBytes }: { interview: Interview; maxUploadBytes?: number }) {
  const qc = useQueryClient()
  const rec = useRecorder(interview.id, { maxDurationMs: MAX_DURATION_MS })
  const [local, setLocal] = useState<LocalRecordingSession | null>(null)
  const [localUrl, setLocalUrl] = useState<string | null>(null)
  const [localSize, setLocalSize] = useState(0)
  const [progress, setProgress] = useState(0)
  const [saved, setSaved] = useState<Recording | null>(null)
  const [confirmDiscard, setConfirmDiscard] = useState(false)
  const [lowStorage, setLowStorage] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const abort = useRef<AbortController | null>(null)

  const consentOk = interview.consent_status === 'confirmed'

  // Recover a recording that was captured in this browser but never confirmed by the server.
  const loadLocal = async () => {
    const session = await getSession(interview.id).catch(() => undefined)
    if (session && session.chunkCount > 0) {
      setLocal(session)
      const blob = await assembleRecording(interview.id, session.mimeType)
      setLocalSize(blob.size)
      setLocalUrl((old) => {
        if (old) URL.revokeObjectURL(old)
        return URL.createObjectURL(blob)
      })
    } else {
      setLocal(null)
    }
  }
  useEffect(() => {
    void loadLocal()
    storageEstimate().then(({ available }) => setLowStorage(available !== null && available < 200 * 1024 * 1024))
    return () => {
      if (localUrl) URL.revokeObjectURL(localUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interview.id])

  const startRecording = useMutation({
    mutationFn: async () => {
      await api.startRecording(interview.id)
      await rec.start()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interview', interview.id] }),
    onError: (e) => toast.error(errorMessage(e)),
  })

  const upload = useMutation({
    mutationFn: async (file: File) => {
      if (maxUploadBytes && file.size > maxUploadBytes) throw new Error(`The recording is ${formatBytes(file.size)}, above the ${formatBytes(maxUploadBytes)} limit.`)
      if (file.size === 0) throw new Error('The recording is empty.')
      abort.current = new AbortController()
      setProgress(0)
      return api.uploadRecording(interview.id, file, setProgress, abort.current.signal)
    },
    onSuccess: async (recording, file) => {
      // Only now, after the server has stored and checksummed the audio, is the local copy removed.
      setSaved(recording)
      if (local && file.name.startsWith('interview-')) {
        await clearRecording(interview.id)
        setLocal(null)
        rec.reset()
      }
      toast.success('Recording saved to the school server')
      qc.invalidateQueries({ queryKey: ['interview', interview.id] })
      qc.invalidateQueries({ queryKey: ['processing', interview.id] })
    },
  })

  const stopAndKeep = async () => {
    await rec.stop()
    await loadLocal()
  }

  const uploadLocal = async () => {
    if (!local) return
    const blob = await assembleRecording(interview.id, local.mimeType)
    const type = uploadMimeType(local.mimeType)
    upload.mutate(new File([blob], `interview-${interview.candidate_reference ?? interview.id}.${fileExtension(type)}`, { type }))
  }

  const discardLocal = async () => {
    await clearRecording(interview.id)
    setLocal(null)
    if (localUrl) URL.revokeObjectURL(localUrl)
    setLocalUrl(null)
    rec.reset()
    setConfirmDiscard(false)
  }

  const active = rec.state === 'recording' || rec.state === 'paused'
  const busy = rec.state === 'starting' || rec.state === 'stopping'

  if (saved) {
    return (
      <Card>
        <CardContent className="flex items-start gap-3">
          <CircleCheck className="mt-0.5 size-5 text-success" />
          <div className="text-sm">
            <p className="font-medium">Recording stored securely on the school server.</p>
            <p className="text-muted-foreground">
              {saved.original_filename} · {formatBytes(saved.size_bytes)} · SHA-256 <span className="font-mono">{saved.sha256.slice(0, 16)}…</span>
            </p>
            <p className="mt-1 text-muted-foreground">Transcription has been queued. Progress is shown above.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Mic className="size-4" /> Recording
        </CardTitle>
        <CardDescription>Audio is kept in this browser while recording and is only marked as saved after the server confirms storage.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {!rec.support.supported && (
          <Alert variant="destructive">
            <MicOff />
            <AlertTitle>Browser recording unavailable</AlertTitle>
            <AlertDescription>{rec.support.reason} You can still upload an audio file recorded on another device.</AlertDescription>
          </Alert>
        )}
        {!consentOk && (
          <Alert>
            <TriangleAlert />
            <AlertTitle>Consent required</AlertTitle>
            <AlertDescription>Recording and uploads are disabled until recording consent has been confirmed.</AlertDescription>
          </Alert>
        )}
        {rec.permission === 'denied' && <p className="text-sm text-destructive">Microphone access is blocked for this site. Change it in the browser’s site settings.</p>}
        {lowStorage && <p className="text-sm text-amber-700">This browser reports little free storage. A long recording may not fit; keep the session short or free up space.</p>}
        {rec.error && (
          <Alert variant="destructive" role="alert">
            <TriangleAlert />
            <AlertDescription>{rec.error}</AlertDescription>
          </Alert>
        )}

        {local && !active && rec.state !== 'stopping' && (
          <div className="space-y-3 rounded-md border border-amber-200 bg-amber-50 p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <ToneBadge tone="attention">Not yet saved to server</ToneBadge>
              <span>
                {formatDuration(local.durationMs / 1000)} captured · {formatBytes(localSize)} · started {new Date(local.startedAt).toLocaleTimeString()}
              </span>
            </div>
            {localUrl && <audio controls src={localUrl} className="w-full" aria-label="Local recording preview" />}
            {upload.isPending && (
              <div className="space-y-1">
                <Progress value={progress * 100} aria-label="Upload progress" />
                <p className="text-xs text-muted-foreground">Uploading… {Math.round(progress * 100)}%</p>
              </div>
            )}
            {upload.isError && <p className="text-sm text-destructive">{errorMessage(upload.error)}</p>}
            <div className="flex flex-wrap gap-2">
              <Button onClick={uploadLocal} disabled={upload.isPending || !consentOk}>
                {upload.isPending ? <Spinner /> : upload.isError ? <RotateCcw /> : <CloudUpload />} {upload.isError ? 'Retry upload' : 'Save to server'}
              </Button>
              {upload.isPending && (
                <Button variant="outline" onClick={() => abort.current?.abort()}>
                  Cancel upload
                </Button>
              )}
              <Button variant="ghost" className="text-destructive" onClick={() => setConfirmDiscard(true)} disabled={upload.isPending}>
                <Trash2 /> Discard
              </Button>
            </div>
          </div>
        )}

        {!local && (
          <>
            <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
              <div className="space-y-1.5">
                <Label>Microphone</Label>
                <Select value={rec.deviceId || 'default'} onValueChange={(v) => rec.setDeviceId(v === 'default' ? '' : v)} disabled={active || busy}>
                  <SelectTrigger className="w-full" aria-label="Microphone">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">System default microphone</SelectItem>
                    {rec.devices
                      .filter((d) => d.deviceId && d.deviceId !== 'default')
                      .map((d, i) => (
                        <SelectItem key={d.deviceId} value={d.deviceId}>
                          {d.label || `Microphone ${i + 1}`}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <LevelMeter level={rec.level} active={rec.state === 'recording'} />
            </div>

            <div className="flex flex-col items-center gap-4 rounded-lg border bg-muted/40 py-8">
              <div className="flex items-center gap-2 text-sm font-medium" aria-live="polite">
                {rec.state === 'recording' && <span className="size-2.5 animate-pulse rounded-full bg-red-500" aria-hidden />}
                {rec.state === 'recording' ? 'Recording' : rec.state === 'paused' ? 'Paused' : rec.state === 'stopping' ? 'Finishing…' : 'Ready'}
              </div>
              <div className="font-mono text-5xl font-light tabular-nums" aria-label="Elapsed recording time">
                {formatDuration(rec.elapsedMs / 1000)}
              </div>
              <div className="flex gap-3">
                {!active && (
                  <Button size="lg" onClick={() => startRecording.mutate()} disabled={!consentOk || !rec.support.supported || busy || startRecording.isPending}>
                    {busy || startRecording.isPending ? <Spinner /> : <Mic />} Start recording
                  </Button>
                )}
                {rec.state === 'recording' && (
                  <Button size="lg" variant="outline" onClick={rec.pause}>
                    <Pause /> Pause
                  </Button>
                )}
                {rec.state === 'paused' && (
                  <Button size="lg" variant="outline" onClick={rec.resume}>
                    <Play /> Resume
                  </Button>
                )}
                {active && (
                  <Button size="lg" variant="destructive" onClick={() => void stopAndKeep()}>
                    <Square /> Stop
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">Maximum length {MAX_DURATION_MS / 60000} minutes. Closing the tab keeps what was captured for recovery.</p>
            </div>

            {!active && (
              <div className="flex items-center gap-3 border-t pt-4 text-sm">
                <FileAudio className="size-4 text-muted-foreground" />
                <span className="text-muted-foreground">Recorded on another device?</span>
                <input
                  ref={fileInput}
                  type="file"
                  accept="audio/webm,audio/ogg,audio/mpeg,audio/mp4,audio/x-m4a,audio/wav,.webm,.ogg,.mp3,.m4a,.wav"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) upload.mutate(f)
                    e.target.value = ''
                  }}
                />
                <Button variant="outline" size="sm" disabled={!consentOk || upload.isPending} onClick={() => fileInput.current?.click()}>
                  Upload audio file
                </Button>
                {upload.isPending && <Progress value={progress * 100} className="max-w-40" aria-label="Upload progress" />}
                {upload.isError && <span className="text-destructive">{errorMessage(upload.error)}</span>}
              </div>
            )}
          </>
        )}
      </CardContent>
      <AlertDialog open={confirmDiscard} onOpenChange={setConfirmDiscard}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Discard this recording?</AlertDialogTitle>
            <AlertDialogDescription>The audio has not been saved to the server. Discarding deletes it from this browser permanently.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep it</AlertDialogCancel>
            <AlertDialogAction className="bg-destructive text-white hover:bg-destructive/90" onClick={() => void discardLocal()}>
              Discard
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}
