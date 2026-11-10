import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCheck, Eye, Lock, Undo2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { EmptyState, ErrorState, LoadingRows, Spinner, ToneBadge } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api, errorMessage } from '@/lib/api'
import { formatDateTime, statusLabel } from '@/lib/status'
import type { Interview, ReviewAction } from '@/lib/types'

const ACTION_LABEL: Record<ReviewAction, string> = { review: 'Reviewed', request_correction: 'Correction requested', finalize: 'Finalized' }

export function ReviewPanel({ interview }: { interview: Interview }) {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [remarks, setRemarks] = useState('')
  const [recommendation, setRecommendation] = useState('')
  const history = useQuery({ queryKey: ['reviews', interview.id], queryFn: () => api.reviews(interview.id) })
  const isReviewer = user?.role === 'principal' || user?.role === 'reviewer' || user?.role === 'administrator'

  const act = useMutation({
    mutationFn: (action: ReviewAction) => api.review(interview.id, action, remarks, recommendation),
    onSuccess: (r) => {
      toast.success(`Status: ${r.status.replace(/_/g, ' ')}`)
      setRemarks('')
      qc.invalidateQueries({ queryKey: ['interview', interview.id] })
      qc.invalidateQueries({ queryKey: ['reviews', interview.id] })
      qc.invalidateQueries({ queryKey: ['interviews'] })
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  const s = interview.status
  return (
    <div className="grid gap-6 lg:grid-cols-5">
      {isReviewer && ['submitted', 'principal_review', 'reviewed'].includes(s) && (
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">Principal review</CardTitle>
            <CardDescription>
              Check the form against the transcript and, where needed, the recording. AI-assisted content is not an objective assessment and carries no score. The admission decision
              stays with authorized school personnel and is not recorded by this system.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="remarks">Review remarks</Label>
              <Textarea id="remarks" value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Required when requesting a correction." />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="recommendation">Reviewer note for the admissions file (optional, human-entered)</Label>
              <Input id="recommendation" maxLength={100} value={recommendation} onChange={(e) => setRecommendation(e.target.value)} />
            </div>
            <div className="flex flex-wrap gap-2">
              {s === 'submitted' && (
                <Button onClick={() => act.mutate('review')} disabled={act.isPending}>
                  {act.isPending ? <Spinner /> : <Eye />} Begin review
                </Button>
              )}
              {s === 'principal_review' && (
                <>
                  <Button onClick={() => act.mutate('review')} disabled={act.isPending}>
                    <CheckCheck /> Mark documentation reviewed
                  </Button>
                  <Button variant="outline" onClick={() => act.mutate('request_correction')} disabled={act.isPending || !remarks.trim()} title={!remarks.trim() ? 'Write remarks first' : undefined}>
                    <Undo2 /> Request correction
                  </Button>
                </>
              )}
              {s === 'reviewed' && (
                <Button onClick={() => act.mutate('finalize')} disabled={act.isPending}>
                  <Lock /> Finalize record
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      <Card className={isReviewer && ['submitted', 'principal_review', 'reviewed'].includes(s) ? 'lg:col-span-2' : 'lg:col-span-5'}>
        <CardHeader>
          <CardTitle className="text-base">Review history</CardTitle>
        </CardHeader>
        <CardContent>
          {history.isPending ? (
            <LoadingRows rows={3} />
          ) : history.isError ? (
            <ErrorState error={history.error} />
          ) : history.data.length === 0 ? (
            <EmptyState title="No review actions yet" />
          ) : (
            <ol className="space-y-4 border-l pl-4">
              {history.data.map((h) => (
                <li key={h.id} className="relative">
                  <span className="absolute top-1.5 -left-[21px] size-2.5 rounded-full bg-primary" aria-hidden />
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <ToneBadge tone={h.action === 'request_correction' ? 'attention' : 'success'}>{ACTION_LABEL[h.action]}</ToneBadge>
                    <span className="text-muted-foreground">{formatDateTime(h.created_at)}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {h.reviewer_name ? `By ${h.reviewer_name}` : 'Authorized reviewer'}
                    {h.status_from && h.status_to ? ` · ${statusLabel(h.status_from)} → ${statusLabel(h.status_to)}` : ''}
                  </p>
                  {h.remarks && <p className="mt-1 text-sm whitespace-pre-wrap">{h.remarks}</p>}
                  {h.recommendation && <p className="mt-1 text-xs text-muted-foreground">Reviewer note: {h.recommendation}</p>}
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
