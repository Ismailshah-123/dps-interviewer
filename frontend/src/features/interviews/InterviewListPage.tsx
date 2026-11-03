import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, ErrorState, LoadingRows, PageHeader, Pagination, StatusBadge } from '@/components/common'
import { api } from '@/lib/api'
import { STATUS_META, formatDateTime } from '@/lib/status'
import type { InterviewStatus } from '@/lib/types'

const LIMIT = 20

export function InterviewListPage({ title, description, statuses }: { title: string; description: string; statuses?: InterviewStatus[] }) {
  const [params, setParams] = useSearchParams()
  const filter = params.get('status') as InterviewStatus | null
  const skip = Number(params.get('skip') ?? 0)
  const effective = filter ? [filter] : statuses
  const list = useQuery({
    queryKey: ['interviews', { effective, skip }],
    queryFn: () => api.interviews({ status: effective, skip, limit: LIMIT }),
    placeholderData: (prev) => prev,
    refetchInterval: 15000,
  })
  const options = statuses ?? (Object.keys(STATUS_META) as InterviewStatus[])

  return (
    <>
      <PageHeader title={title} description={description} />
      <Card>
        <CardContent className="space-y-4">
          <Select value={filter ?? 'all'} onValueChange={(v) => setParams(v === 'all' ? {} : { status: v })}>
            <SelectTrigger className="w-56" aria-label="Filter by status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {options.map((s) => (
                <SelectItem key={s} value={s}>
                  {STATUS_META[s].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {list.isPending ? (
            <LoadingRows />
          ) : list.isError ? (
            <ErrorState error={list.error} onRetry={() => list.refetch()} />
          ) : list.data.items.length === 0 ? (
            <EmptyState title="No interviews" description="Nothing matches this view right now." />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead className="sr-only">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {list.data.items.map((i) => (
                    <TableRow key={i.id}>
                      <TableCell>
                        <div className="font-medium">{i.candidate_name}</div>
                        <div className="font-mono text-xs text-muted-foreground">{i.candidate_reference}</div>
                      </TableCell>
                      <TableCell>{i.candidate_grade ?? '—'}</TableCell>
                      <TableCell>
                        <StatusBadge status={i.status} />
                      </TableCell>
                      <TableCell>{formatDateTime(i.submitted_at)}</TableCell>
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
              <Pagination meta={list.data.meta} onPage={(s) => setParams({ ...(filter ? { status: filter } : {}), skip: String(s) })} />
            </>
          )}
        </CardContent>
      </Card>
    </>
  )
}
