import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Headphones, Pencil, Search } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { AiBadge, EmptyState, ErrorState, LoadingRows, Spinner, ToneBadge } from '@/components/common'
import { ApiError, api, errorMessage } from '@/lib/api'
import { containsArabicScript, formatDuration } from '@/lib/status'
import type { Interview, TranscriptSegment } from '@/lib/types'
import { cn } from '@/lib/utils'

function Highlight({ text, term }: { text: string; term: string }) {
  if (!term) return <>{text}</>
  const parts = text.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return (
    <>
      {parts.map((p, i) =>
        p.toLowerCase() === term.toLowerCase() ? (
          <mark key={i} className="rounded bg-amber-200 px-0.5">
            {p}
          </mark>
        ) : (
          p
        ),
      )}
    </>
  )
}

/** Recording is fetched with the user's credentials into a short-lived object URL; it is never a public link. */
export function AuthorizedAudio({ interviewId, audioRef }: { interviewId: string; audioRef: React.RefObject<HTMLAudioElement | null> }) {
  const [url, setUrl] = useState<string | null>(null)
  const load = useMutation({
    mutationFn: () => api.recordingBlob(interviewId),
    onSuccess: (blob) => setUrl(URL.createObjectURL(blob)),
  })
  useEffect(() => () => void (url && URL.revokeObjectURL(url)), [url])
  if (url) return <audio ref={audioRef} controls src={url} className="w-full" aria-label="Interview recording" />
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button variant="outline" size="sm" onClick={() => load.mutate()} disabled={load.isPending}>
        {load.isPending ? <Spinner /> : <Headphones />} Load recording
      </Button>
      {load.isError && <span className="text-sm text-destructive">{load.error instanceof ApiError && load.error.status === 404 ? 'No recording is stored for this interview.' : errorMessage(load.error)}</span>}
    </div>
  )
}

function SegmentRow({ segment, term, editable, onSeek }: { segment: TranscriptSegment; term: string; editable: boolean; onSeek: (t: number) => void }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(segment.text)
  const [speaker, setSpeaker] = useState(segment.speaker_label ?? '')
  const rtl = containsArabicScript(segment.text)
  const save = useMutation({
    mutationFn: () => api.editSegment(segment.id, text, speaker || null),
    onSuccess: () => {
      setEditing(false)
      toast.success('Segment saved. The machine original is kept for audit.')
      qc.invalidateQueries({ queryKey: ['transcript'] })
    },
    onError: (e) => toast.error(errorMessage(e)),
  })
  return (
    <li className="group grid grid-cols-[auto_1fr] gap-3 rounded-md px-2 py-2 hover:bg-muted/50">
      <button type="button" onClick={() => onSeek(segment.start_seconds)} className="h-fit rounded px-1.5 py-0.5 font-mono text-xs text-primary hover:bg-accent" aria-label={`Play from ${formatDuration(segment.start_seconds)}`}>
        {formatDuration(segment.start_seconds)}
      </button>
      <div className="min-w-0">
        <div className="mb-0.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {segment.speaker_label && <span>{segment.speaker_label} (provisional)</span>}
          {segment.is_human_edited && <ToneBadge tone="success">Edited by staff</ToneBadge>}
          {segment.confidence !== null && segment.confidence < 0.5 && <ToneBadge tone="attention">Low recognition confidence — verify against audio</ToneBadge>}
          {editable && !editing && (
            <Button variant="ghost" size="sm" className="h-6 px-2 opacity-0 group-hover:opacity-100 focus:opacity-100" onClick={() => setEditing(true)}>
              <Pencil className="size-3" /> Edit
            </Button>
          )}
        </div>
        {editing ? (
          <div className="space-y-2">
            <Textarea value={text} dir="auto" onChange={(e) => setText(e.target.value)} aria-label="Segment text" />
            <Input value={speaker} onChange={(e) => setSpeaker(e.target.value)} placeholder="Speaker label (optional)" className="max-w-xs" aria-label="Speaker label" />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending || !text.trim()}>
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={() => (setEditing(false), setText(segment.text))}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <p dir={rtl ? 'rtl' : 'auto'} lang={rtl ? 'ur' : undefined} className={cn('text-sm leading-relaxed whitespace-pre-wrap', rtl && 'urdu')}>
            <Highlight text={segment.text} term={term} />
          </p>
        )}
      </div>
    </li>
  )
}

export function TranscriptPanel({ interview, editable }: { interview: Interview; editable: boolean }) {
  const transcript = useQuery({ queryKey: ['transcript', interview.id], queryFn: () => api.transcript(interview.id), retry: (n, e) => !(e instanceof ApiError && e.status === 404) && n < 2 })
  const [term, setTerm] = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const segments = useMemo(() => {
    const all = transcript.data?.segments ?? []
    return term ? all.filter((s) => s.text.toLowerCase().includes(term.toLowerCase())) : all
  }, [transcript.data, term])

  const seek = (t: number) => {
    const a = audioRef.current
    if (!a) return toast.message('Load the recording first to play from this point.')
    a.currentTime = t
    void a.play()
  }

  if (transcript.isPending) return <LoadingRows rows={8} />
  if (transcript.isError)
    return transcript.error instanceof ApiError && transcript.error.status === 404 ? (
      <EmptyState title="Transcript not ready" description="The transcript appears here once speech recognition has finished." />
    ) : (
      <ErrorState error={transcript.error} onRetry={() => transcript.refetch()} />
    )
  const t = transcript.data
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          Transcript <AiBadge label="Machine transcription" />
        </CardTitle>
        <CardDescription>
          {t.provider} · {t.model_name}
          {t.model_version ? ` ${t.model_version}` : ''} · detected language: {t.language ?? 'unknown'}
          {t.processing_seconds !== null ? ` · processed in ${formatDuration(t.processing_seconds)}` : ''}. Recognition errors are likely, especially for Urdu, names and numbers;
          verify against the audio.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <AuthorizedAudio interviewId={interview.id} audioRef={audioRef} />
        <div className="relative max-w-sm">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input className="pl-9" placeholder="Search transcript" aria-label="Search transcript" value={term} onChange={(e) => setTerm(e.target.value)} />
        </div>
        {term && (
          <p className="text-xs text-muted-foreground">
            {segments.length} matching segment{segments.length === 1 ? '' : 's'}
          </p>
        )}
        <ol className="max-h-[60vh] space-y-0.5 overflow-y-auto pr-1">
          {segments.map((s) => (
            <SegmentRow key={s.id} segment={s} term={term} editable={editable} onSeek={seek} />
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
