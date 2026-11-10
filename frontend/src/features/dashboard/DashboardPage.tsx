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

export function DashboardPage() {
  const { user } = useAuth()
  const stats = useQuery({ queryKey: ['interview-stats'], queryFn: api.interviewStats, refetchInterval: 15000 })
  const candidates = useQuery({ queryKey: ['candidates', { limit: 1 }], queryFn: () => api.candidates({ limit: 1 }) })
  const isReviewer = user?.role === 'reviewer' || user?.role === 'principal'
  const canStartInterview = user?.role === 'administrator' || user?.role === 'interviewer'
  const recent = useQuery({
    queryKey: ['interviews', 'recent', user?.role],
    queryFn: () => api.interviews({ limit: 8, status: isReviewer ? REVIEW_QUEUE_STATUSES : undefined }),
  })
  const by = stats.data?.by_status ?? {}

  return (
    <>
      <PageHeader
        title={`Welcome, ${user?.full_name.split(' ')[0] ?? ''}`}
        description={
          isReviewer
            ? 'Interviews submitted for your review. AI-assisted content is marked and must be verified against the transcript and recording.'
            : 'Overview of interviews visible to your account.'
        }
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
      {stats.isError && <ErrorState error={stats.error} onRetry={() => stats.refetch()} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Candidates" value={candidates.data?.meta.total} hint="Visible to your account" icon={FileAudio} to="/candidates" />
        <StatCard label="Awaiting processing" value={stats.data && sum(by, PROCESSING_STATUSES)} hint="Uploaded, transcribing or summarizing" icon={Hourglass} />
        <StatCard
          label={isReviewer ? 'Correction requested' : 'Awaiting interviewer review'}
          value={stats.data && (isReviewer ? by.correction_requested ?? 0 : sum(by, ['needs_review', 'correction_requested']))}
          hint={isReviewer ? 'Returned to interviewers' : 'Drafts to verify and submit'}
          icon={PenLine}
        />
        <StatCard
          label="Awaiting principal review"
          value={stats.data && sum(by, ['submitted', 'principal_review', 'reviewed'])}
          hint={`${by.finalized ?? 0} finalized`}
          icon={ClipboardCheck}
          to={user?.role === 'interviewer' ? undefined : '/reviews'}
        />
      </div>
      {(by.failed ?? 0) > 0 && (
        <div className="mt-4 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle className="size-4" /> {by.failed} interview(s) failed processing.
          {user?.role === 'administrator' && (
            <Link to="/admin/jobs?status=failed" className="ml-1 underline">
              Review jobs
            </Link>
          )}
        </div>
      )}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">{isReviewer ? 'Review queue' : 'Recent interviews'}</CardTitle>
        </CardHeader>
        <CardContent>
          {recent.isPending ? (
            <LoadingRows rows={4} />
          ) : recent.isError ? (
            <ErrorState error={recent.error} onRetry={() => recent.refetch()} />
          ) : recent.data.items.length === 0 ? (
            <EmptyState title="Nothing here yet" description={isReviewer ? 'No interviews are waiting for principal review.' : 'Create a candidate and start an interview to begin.'} />
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
                    <TableCell>
                      <StatusBadge status={i.status} />
                    </TableCell>
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
