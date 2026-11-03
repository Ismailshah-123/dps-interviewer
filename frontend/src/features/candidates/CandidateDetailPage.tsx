import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router'
import { Mic, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, ErrorState, KeyValue, LoadingRows, PageHeader, Spinner, StatusBadge } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api, errorMessage } from '@/lib/api'
import { formatDateTime } from '@/lib/status'
import { CandidateFormDialog } from './CandidateFormDialog'

export function CandidateDetailPage() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const candidate = useQuery({ queryKey: ['candidate', id], queryFn: () => api.candidate(id) })
  const canManage = user?.role === 'administrator' || user?.role === 'interviewer'
  const interviews = useQuery({ queryKey: ['interviews', { candidate: id }], queryFn: () => api.interviews({ candidate_id: id, limit: 50 }) })

  const start = useMutation({
    mutationFn: () => api.createInterview(id),
    onSuccess: (i) => {
      qc.invalidateQueries({ queryKey: ['interviews'] })
      navigate(`/interviews/${i.id}`)
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  if (candidate.isPending) return <LoadingRows rows={6} />
  if (candidate.isError) return <ErrorState error={candidate.error} onRetry={() => candidate.refetch()} />
  const c = candidate.data
  const hasOpenInterview = interviews.data?.items.some((i) => !['finalized', 'cancelled'].includes(i.status))

  return (
    <>
      <PageHeader
        eyebrow={<span className="font-mono">{c.reference_number}</span>}
        title={c.name}
        description="Candidate record. Interviews, recordings and forms are linked below."
        actions={
          canManage && (
            <>
              <Button variant="outline" onClick={() => setEditing(true)}>
                <Pencil /> Edit
              </Button>
              <Button onClick={() => start.mutate()} disabled={start.isPending || hasOpenInterview} title={hasOpenInterview ? 'An interview is already in progress for this candidate' : undefined}>
                {start.isPending ? <Spinner /> : <Mic />} Start interview
              </Button>
            </>
          )
        }
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4">
              <KeyValue label="Class / grade">{c.grade ?? '—'}</KeyValue>
              <KeyValue label="Application reference">{c.application_reference ?? '—'}</KeyValue>
              <KeyValue label="Interview scheduled">{formatDateTime(c.interview_datetime)}</KeyValue>
              <KeyValue label="Created">{formatDateTime(c.created_at)}</KeyValue>
              <KeyValue label="Last updated">{formatDateTime(c.updated_at)}</KeyValue>
            </dl>
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Interviews</CardTitle>
          </CardHeader>
          <CardContent>
            {interviews.isPending ? (
              <LoadingRows rows={2} />
            ) : interviews.isError ? (
              <ErrorState error={interviews.error} />
            ) : interviews.data.items.length === 0 ? (
              <EmptyState title="No interviews yet" description={canManage ? 'Start an interview when the candidate and family are present.' : 'No interviews are available to your account.'} />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead className="sr-only">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {interviews.data.items.map((i) => (
                    <TableRow key={i.id}>
                      <TableCell>{formatDateTime(i.created_at)}</TableCell>
                      <TableCell>
                        <StatusBadge status={i.status} />
                      </TableCell>
                      <TableCell>{formatDateTime(i.submitted_at)}</TableCell>
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
      </div>
      <CandidateFormDialog open={editing} onOpenChange={setEditing} candidate={c} />
    </>
  )
}
