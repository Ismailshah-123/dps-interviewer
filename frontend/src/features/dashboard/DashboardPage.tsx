import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { AlertTriangle, ArrowRight, ClipboardCheck, FileAudio, Hourglass, PenLine } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, ErrorState, LoadingRows, PageHeader, StatusBadge } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api } from '@/lib/api'
import { PROCESSING_STATUSES, REVIEW_QUEUE_STATUSES, formatDateTime } from '@/lib/status'
import type { InterviewStatus } from '@/lib/types'

function sum(byStatus: Partial<Record<InterviewStatus, number>>, statuses: InterviewStatus[]) {
  return statuses.reduce((n, s) => n + (byStatus[s] ?? 0), 0)
}

function StatCard({ label, value, hint, icon: Icon, to }: { label: string; value: number | undefined; hint: string; icon: typeof FileAudio; to?: string }) {
  const body = (
    <Card className="gap-2 py-5 transition-shadow hover:shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between px-5">
        <CardDescription className="font-medium">{label}</CardDescription>
        <Icon className="size-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent className="px-5">
        <div className="text-3xl font-semibold tabular-nums">{value ?? '—'}</div>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  )
  return to ? <Link to={to}>{body}</Link> : body
}

const STATUS_LABELS: Partial<Record<InterviewStatus, string>> = {
  draft: 'Draft',
  recording: 'Recording',
  uploading: 'Uploading',
  uploaded: 'Uploaded',
  queued: 'Queued',
  transcribing: 'Transcribing',
  transcript_ready: 'Transcript ready',
  summarizing: 'Summarizing',
  form_draft_ready: 'Form draft ready',
  needs_review: 'Interviewer review',
  submitted: 'Submitted',
  principal_review: 'Principal review',
  correction_requested: 'Corrections requested',
  reviewed: 'Approved',
  finalized: 'Finalized',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

const STATUS_ORDER: InterviewStatus[] = [
  'draft', 'recording', 'uploading', 'uploaded', 'queued', 'transcribing',
  'transcript_ready', 'summarizing', 'form_draft_ready', 'needs_review',
  'submitted', 'principal_review', 'correction_requested', 'reviewed',
  'finalized', 'failed', 'cancelled',
]

function AnalyticsBars({ byStatus }: { byStatus: Partial<Record<InterviewStatus, number>> }) {
  const entries = STATUS_ORDER.map((status) => ({ status, value: byStatus[status] ?? 0 }))
    .filter((entry) => entry.value > 0)
  const max = Math.max(1, ...entries.map((entry) => entry.value))

  if (entries.length === 0) {
    return <EmptyState title="No interview activity yet" description="Status analytics will appear when interviews enter the workflow." />
  }

  return (
    <div className="space-y-4" aria-label="Interview counts by workflow status">
      {entries.map(({ status, value }) => (
        <div key={status} className="grid grid-cols-[minmax(112px,1fr)_minmax(0,3fr)_36px] items-center gap-3">
          <span className="truncate text-sm text-muted-foreground">{STATUS_LABELS[status]}</span>
          <div className="h-2.5 overflow-hidden rounded-full bg-muted" role="img" aria-label={`${STATUS_LABELS[status]}: ${value}`}>
            <div className="h-full rounded-full bg-primary transition-[width]" style={{ width: `${Math.max(3, (value / max) * 100)}%` }} />
          </div>
          <span className="text-right text-sm font-semibold tabular-nums">{value}</span>
        </div>
      ))}
    </div>
  )
}


function DailyActivityChart({ items }: { items: Array<{ date: string; interviews: number }> }) {
  const visible = items.slice(-14)
  const max = Math.max(1, ...visible.map((item) => item.interviews))
  if (visible.length === 0) {
    return <EmptyState title="No recent activity" description="Daily interview activity will appear here as new interviews are created." />
  }
  return (
    <div className="flex h-44 items-end gap-2 border-b px-1" aria-label="Daily interview creation over the last 14 active days">
      {visible.map((item) => (
        <div key={item.date} className="flex min-w-0 flex-1 flex-col items-center justify-end gap-2">
          <span className="text-[11px] font-medium tabular-nums text-muted-foreground">{item.interviews}</span>
          <div className="flex h-28 w-full items-end rounded-t bg-muted">
            <div
              className="w-full rounded-t bg-primary/80 transition-[height]"
              style={{ height: `${Math.max(5, (item.interviews / max) * 100)}%` }}
              role="img"
              aria-label={`${item.date}: ${item.interviews} interviews`}
            />
          </div>
          <span className="text-[10px] text-muted-foreground">{new Date(`${item.date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</span>
        </div>
      ))}
    </div>
  )
}

function GradeBars({ items }: { items: Array<{ grade: string; count: number }> }) {
  const max = Math.max(1, ...items.map((item) => item.count))
  if (items.length === 0) return <p className="text-sm text-muted-foreground">No grade data available yet.</p>
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.grade} className="grid grid-cols-[minmax(80px,1fr)_minmax(0,3fr)_32px] items-center gap-3">
          <span className="truncate text-sm text-muted-foreground">{item.grade}</span>
          <div className="h-2.5 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary/70" style={{ width: `${Math.max(3, (item.count / max) * 100)}%` }} />
          </div>
          <span className="text-right text-sm font-semibold tabular-nums">{item.count}</span>
        </div>
      ))}
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const analytics = useQuery({ queryKey: ['interview-analytics', user?.role], queryFn: api.interviewAnalytics, refetchInterval: 30000 })
  const candidates = useQuery({ queryKey: ['candidates', { limit: 1 }], queryFn: () => api.candidates({ limit: 1 }) })
  const isPrincipal = user?.role === 'principal' || user?.role === 'reviewer'
  const isAdmin = user?.role === 'administrator'
  const isInterviewer = user?.role === 'interviewer'
  const canStartInterview = isAdmin || isInterviewer
  const recent = useQuery({
    queryKey: ['interviews', 'recent', user?.role],
    queryFn: () => api.interviews({ limit: 8, status: isPrincipal ? REVIEW_QUEUE_STATUSES : undefined }),
  })
  const by = analytics.data?.by_status ?? {}
  const processingCount = sum(by, PROCESSING_STATUSES)
  const completedCount = by.finalized ?? 0
  const attentionCount = (by.failed ?? 0) + (by.correction_requested ?? 0)
  const title = isAdmin ? 'School operations overview' : isPrincipal ? 'Principal review overview' : 'Interviewer workspace'
  const description = isAdmin
    ? 'Monitor interview operations, staff workflow and system-wide progress.'
    : isPrincipal
      ? 'Review submitted interviews, track decisions and return records that need corrections.'
      : 'Manage your assigned candidates, conduct interviews and submit completed records for review.'

  return (
    <>
      <PageHeader
        title={title}
        description={description}
        actions={
          canStartInterview && (
            <Button asChild>
              <Link to="/candidates">
                Start an interview <ArrowRight />
              </Link>
            </Button>
          )
        }
      />
      {analytics.isError && <ErrorState error={analytics.error} onRetry={() => analytics.refetch()} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Interviews in view" value={analytics.data?.total_interviews} hint={isAdmin ? 'Across the school system' : isPrincipal ? 'Visible in the review workflow' : 'Assigned to your account'} icon={FileAudio} />
        <StatCard label={isPrincipal ? 'Awaiting your review' : 'In processing'} value={isPrincipal ? sum(by, ['submitted', 'principal_review']) : processingCount} hint={isPrincipal ? 'Submitted and under principal review' : 'Uploaded, transcribing or summarizing'} icon={Hourglass} />
        <StatCard label={isPrincipal ? 'Corrections requested' : 'Needs attention'} value={isPrincipal ? by.correction_requested ?? 0 : attentionCount} hint={isPrincipal ? 'Returned to interviewers' : 'Failed processing or returned records'} icon={PenLine} />
        <StatCard label="Finalized records" value={completedCount} hint="Completed and finalized interview records" icon={ClipboardCheck} to={isPrincipal ? '/reviews' : undefined} />
      </div>

      {isAdmin && (
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <StatCard label="Candidates registered" value={candidates.data?.meta.total} hint="Candidate records visible to administrators" icon={FileAudio} to="/candidates" />
          <StatCard label="Awaiting principal review" value={sum(by, ['submitted', 'principal_review'])} hint="Submitted or currently under review" icon={ClipboardCheck} to="/reviews" />
          <StatCard label="Processing failures" value={by.failed ?? 0} hint="Interview processing needs attention" icon={AlertTriangle} to="/admin/jobs?status=failed" />
        </div>
      )}

      {(by.failed ?? 0) > 0 && (
        <div className="mt-4 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle className="size-4" /> {by.failed} interview(s) failed processing.
          {isAdmin && <Link to="/admin/jobs?status=failed" className="ml-1 underline">Review jobs</Link>}
        </div>
      )}

      <div className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Interview workflow analytics</CardTitle>
            <CardDescription>
              {isAdmin ? 'System-wide interview distribution by current status.' : isPrincipal ? 'Interviews currently visible in your review workflow.' : 'Your assigned interviews by current processing and review status.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.isPending ? <LoadingRows rows={5} /> : analytics.isError ? <ErrorState error={analytics.error} onRetry={() => analytics.refetch()} /> : <AnalyticsBars byStatus={by} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Key workflow indicators</CardTitle>
            <CardDescription>Current workload, not lifetime approval rates.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: 'Processing', value: processingCount, note: 'AI and transcription pipeline' },
              { label: 'Awaiting review', value: sum(by, ['needs_review', 'submitted', 'principal_review']), note: 'Interviewer and principal queues' },
              { label: 'Correction cycle', value: by.correction_requested ?? 0, note: 'Returned for updates' },
              { label: 'Finalized', value: completedCount, note: 'Final PDF workflow completed' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between gap-3 border-b pb-3 last:border-0 last:pb-0">
                <div>
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.note}</p>
                </div>
                <span className="text-xl font-semibold tabular-nums">{item.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily interview activity</CardTitle>
            <CardDescription>New interviews created by day, over the last 14 active dates in the 30-day window.</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.isPending ? <LoadingRows rows={3} /> : analytics.isError ? <ErrorState error={analytics.error} onRetry={() => analytics.refetch()} /> : <DailyActivityChart items={analytics.data.daily_activity} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Candidates by grade</CardTitle>
            <CardDescription>Interview records grouped by the candidate's grade.</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.isPending ? <LoadingRows rows={3} /> : analytics.isError ? <ErrorState error={analytics.error} onRetry={() => analytics.refetch()} /> : <GradeBars items={analytics.data.by_grade} />}
          </CardContent>
        </Card>
      </div>

      {isAdmin && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">Interviewer performance</CardTitle>
            <CardDescription>Operational workload by assigned interviewer. Counts reflect current interview status, not a quality score.</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.isPending ? <LoadingRows rows={4} /> : analytics.isError ? <ErrorState error={analytics.error} onRetry={() => analytics.refetch()} /> : analytics.data.interviewer_performance.length === 0 ? (
              <EmptyState title="No interviewer activity yet" description="Interviewer workload will appear when interviews are assigned." />
            ) : (
              <Table>
                <TableHeader><TableRow><TableHead>Interviewer</TableHead><TableHead className="text-right">Total</TableHead><TableHead className="text-right">Submitted</TableHead><TableHead className="text-right">Corrections</TableHead><TableHead className="text-right">Finalized</TableHead></TableRow></TableHeader>
                <TableBody>
                  {analytics.data.interviewer_performance.map((staff) => (
                    <TableRow key={staff.interviewer_id}>
                      <TableCell className="font-medium">{staff.name}</TableCell>
                      <TableCell className="text-right tabular-nums">{staff.total_interviews}</TableCell>
                      <TableCell className="text-right tabular-nums">{staff.submitted}</TableCell>
                      <TableCell className="text-right tabular-nums">{staff.corrections_requested}</TableCell>
                      <TableCell className="text-right tabular-nums">{staff.finalized}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">{isPrincipal ? 'Principal review queue' : 'Recent interviews'}</CardTitle>
          <CardDescription>{isPrincipal ? 'Submitted records requiring review or a decision.' : 'Latest interview activity available to your role.'}</CardDescription>
        </CardHeader>
        <CardContent>
          {recent.isPending ? (
            <LoadingRows rows={4} />
          ) : recent.isError ? (
            <ErrorState error={recent.error} onRetry={() => recent.refetch()} />
          ) : recent.data.items.length === 0 ? (
            <EmptyState title="Nothing here yet" description={isPrincipal ? 'No interviews are waiting in your review queue.' : 'Create a candidate and start an interview to begin.'} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Candidate</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="sr-only">Open</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent.data.items.map((i) => (
                  <TableRow key={i.id}>
                    <TableCell>
                      <div className="font-medium">{i.candidate_name}</div>
                      <div className="font-mono text-xs text-muted-foreground">{i.candidate_reference}</div>
                    </TableCell>
                    <TableCell>{i.candidate_grade ?? '—'}</TableCell>
                    <TableCell><StatusBadge status={i.status} /></TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(i.updated_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link to={`/interviews/${i.id}`}>Open</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  )
}
