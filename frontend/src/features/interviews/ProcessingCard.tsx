import { useQuery } from '@tanstack/react-query'
import { Check, Circle, Loader2, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { isProcessing } from '@/lib/status'
import type { Interview, InterviewStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

const STEPS: { label: string; done: InterviewStatus[]; active: InterviewStatus[] }[] = [
  { label: 'Audio stored', done: ['uploaded', 'queued', 'transcribing', 'transcript_ready', 'summarizing', 'form_draft_ready', 'needs_review'], active: ['uploading'] },
  { label: 'Transcribing', done: ['transcript_ready', 'summarizing', 'form_draft_ready', 'needs_review'], active: ['uploaded', 'queued', 'transcribing'] },
  { label: 'Structured summary', done: ['form_draft_ready', 'needs_review'], active: ['transcript_ready', 'summarizing'] },
  { label: 'Form draft ready for review', done: ['needs_review'], active: ['form_draft_ready'] },
]

export function ProcessingCard({ interview }: { interview: Interview }) {
  const processing = isProcessing(interview.status)
  const status = useQuery({
    queryKey: ['processing', interview.id],
    queryFn: () => api.processing(interview.id),
    refetchInterval: processing ? 3000 : false,
  })
  const failedJob = status.data?.jobs.find((j) => j.status === 'failed' || j.error)
  const failed = interview.status === 'failed'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Processing</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-3">
          {STEPS.map((s) => {
            const done = s.done.includes(interview.status) || !['draft', 'recording', 'failed', ...STEPS.flatMap((x) => [...x.done, ...x.active])].includes(interview.status)
            const active = s.active.includes(interview.status)
            return (
              <li key={s.label} className="flex items-center gap-3 text-sm">
                <span className={cn('flex size-6 items-center justify-center rounded-full border', done && 'border-emerald-500 bg-emerald-50 text-emerald-700', active && 'border-indigo-400 text-indigo-700')}>
                  {done ? <Check className="size-3.5" /> : active ? <Loader2 className="size-3.5 animate-spin" /> : <Circle className="size-2 fill-muted text-muted" />}
                </span>
                <span className={cn(!done && !active && 'text-muted-foreground')}>{s.label}</span>
              </li>
            )
          })}
        </ol>
        {failed && (
          <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
            <X className="mt-0.5 size-4 shrink-0" />
            <div>
              <p className="font-medium">Processing failed</p>
              <p>{failedJob?.error ?? 'The job failed.'} An administrator can retry it from Processing jobs once the cause is fixed. No transcript or summary was invented.</p>
            </div>
          </div>
        )}
        {processing && <p className="text-xs text-muted-foreground">Local transcription of a 40-minute interview can take a long time on CPU-only hardware. This page updates automatically.</p>}
      </CardContent>
    </Card>
  )
}
