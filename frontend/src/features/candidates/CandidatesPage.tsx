import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { Plus, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, ErrorState, LoadingRows, PageHeader, Pagination } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/status'
import { CandidateFormDialog } from './CandidateFormDialog'

const LIMIT = 20

export function CandidatesPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const skip = Number(params.get('skip') ?? 0)
  const [search, setSearch] = useState(q)
  const [creating, setCreating] = useState(false)

  // Debounced search kept in the URL (search terms only; never personal details beyond what was typed).
  useEffect(() => {
    const t = setTimeout(() => {
      if (search !== q) setParams(search ? { q: search } : {}, { replace: true })
    }, 300)
    return () => clearTimeout(t)
  }, [search, q, setParams])

  const list = useQuery({ queryKey: ['candidates', { q, skip }], queryFn: () => api.candidates({ q, skip, limit: LIMIT }), placeholderData: (prev) => prev })
  const canCreate = user?.role === 'administrator' || user?.role === 'interviewer'

  return (
    <>
      <PageHeader
        title="Candidates"
        description={user?.role === 'interviewer' ? 'Candidates assigned to you.' : 'All candidate records for this admission cycle.'}
        actions={
          canCreate && (
            <Button onClick={() => setCreating(true)}>
              <Plus /> New candidate
            </Button>
          )
        }
      />
      <Card>
        <CardContent className="space-y-4">
          <div className="relative max-w-sm">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input className="pl-9" placeholder="Search name or reference" aria-label="Search candidates" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          {list.isPending ? (
            <LoadingRows />
          ) : list.isError ? (
            <ErrorState error={list.error} onRetry={() => list.refetch()} />
          ) : list.data.items.length === 0 ? (
            <EmptyState
              title={q ? 'No matching candidates' : 'No candidates yet'}
              description={q ? 'Try a different name or reference number.' : 'Create the first candidate record to schedule an interview.'}
              action={canCreate && !q && <Button onClick={() => setCreating(true)}>New candidate</Button>}
            />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Reference</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>Application ref.</TableHead>
                    <TableHead>Interview</TableHead>
                    <TableHead className="sr-only">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {list.data.items.map((c) => (
                    <TableRow key={c.id} className="cursor-pointer" onClick={() => navigate(`/candidates/${c.id}`)}>
                      <TableCell className="font-mono text-xs">{c.reference_number}</TableCell>
                      <TableCell className="font-medium">{c.name}</TableCell>
                      <TableCell>{c.grade ?? '—'}</TableCell>
                      <TableCell>{c.application_reference ?? '—'}</TableCell>
                      <TableCell className="text-muted-foreground">{formatDateTime(c.interview_datetime)}</TableCell>
                      <TableCell className="text-right">
                        <Button asChild variant="ghost" size="sm" onClick={(e) => e.stopPropagation()}>
                          <Link to={`/candidates/${c.id}`}>Open</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Pagination meta={list.data.meta} onPage={(s) => setParams({ ...(q ? { q } : {}), skip: String(s) })} />
            </>
          )}
        </CardContent>
      </Card>
      <CandidateFormDialog open={creating} onOpenChange={setCreating} onSaved={(c) => navigate(`/candidates/${c.id}`)} />
    </>
  )
}
