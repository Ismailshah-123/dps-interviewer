import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { Activity, Play, RotateCcw, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState, ErrorState, KeyValue, LoadingRows, PageHeader, Pagination, Spinner, ToneBadge } from '@/components/common'
import { api, errorMessage } from '@/lib/api'
import { formatBytes, formatDateTime } from '@/lib/status'

const JOB_TONE: Record<string, 'neutral' | 'progress' | 'success' | 'danger'> = { queued: 'progress', running: 'progress', completed: 'success', failed: 'danger', cancelled: 'neutral' }

export function JobsPage() {
  const qc = useQueryClient()
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? ''
  const [skip, setSkip] = useState(0)
  const jobs = useQuery({ queryKey: ['admin-jobs', { status, skip }], queryFn: () => api.adminJobs({ status: status || undefined, skip, limit: 25 }), refetchInterval: 5000 })
  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-jobs'] })
  const retry = useMutation({ mutationFn: api.retryJob, onSuccess: () => (toast.success('Job requeued'), invalidate()), onError: (e) => toast.error(errorMessage(e)) })
  const cancel = useMutation({ mutationFn: api.cancelJob, onSuccess: () => (toast.success('Job cancelled'), invalidate()), onError: (e) => toast.error(errorMessage(e)) })
  const runOnce = useMutation({ mutationFn: api.runProcessingOnce, onSuccess: () => (toast.success('Processed pending jobs'), invalidate()), onError: (e) => toast.error(errorMessage(e)) })

  return (
    <>
      <PageHeader
        title="Processing jobs"
        description="Transcription and summarization jobs run in the background worker. Errors are shown without transcript content."
        actions={
          <Button variant="outline" onClick={() => runOnce.mutate()} disabled={runOnce.isPending} title="Process pending jobs in the API process (demo aid when no worker is running)">
            {runOnce.isPending ? <Spinner /> : <Play />} Run pending now
          </Button>
        }
      />
      <Card>
        <CardContent className="space-y-4">
          <Select value={status || 'all'} onValueChange={(v) => (setSkip(0), setParams(v === 'all' ? {} : { status: v }))}>
            <SelectTrigger className="w-48" aria-label="Filter jobs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {['all', 'queued', 'running', 'completed', 'failed', 'cancelled'].map((s) => (
                <SelectItem key={s} value={s}>
                  {s === 'all' ? 'All statuses' : s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {jobs.isPending ? (
            <LoadingRows />
          ) : jobs.isError ? (
            <ErrorState error={jobs.error} onRetry={() => jobs.refetch()} />
          ) : jobs.data.items.length === 0 ? (
            <EmptyState title="No jobs" />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Attempts</TableHead>
                    <TableHead>Error</TableHead>
                    <TableHead className="sr-only">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.data.items.map((j) => (
                    <TableRow key={j.id}>
                      <TableCell>
                        <div className="font-medium capitalize">{j.type}</div>
                        <Link to={`/interviews/${j.interview_id}`} className="font-mono text-xs text-muted-foreground hover:underline">
                          {j.interview_id.slice(0, 8)}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <ToneBadge tone={JOB_TONE[j.status] ?? 'neutral'}>{j.status}</ToneBadge>
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {j.attempts}/{j.max_attempts}
                      </TableCell>
                      <TableCell className="max-w-md truncate text-sm text-muted-foreground" title={j.error ?? undefined}>
                        {j.error ?? '—'}
                      </TableCell>
                      <TableCell className="space-x-2 text-right whitespace-nowrap">
                        {['failed', 'cancelled'].includes(j.status) && (
                          <Button size="sm" variant="outline" onClick={() => retry.mutate(j.id)}>
                            <RotateCcw /> Retry
                          </Button>
                        )}
                        {['queued', 'running'].includes(j.status) && (
                          <Button size="sm" variant="ghost" onClick={() => cancel.mutate(j.id)}>
                            <XCircle /> Cancel
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Pagination meta={jobs.data.meta} onPage={setSkip} />
            </>
          )}
        </CardContent>
      </Card>
    </>
  )
}

export function AuditPage() {
  const [skip, setSkip] = useState(0)
  const [action, setAction] = useState('')
  const [applied, setApplied] = useState('')
  const audit = useQuery({ queryKey: ['audit', { applied, skip }], queryFn: () => api.audit({ action: applied || undefined, skip, limit: 50 }) })
  return (
    <>
      <PageHeader title="Audit log" description="Security-relevant actions. Entries record who did what to which record, never transcript text, passwords or tokens. Read-only." />
      <Card>
        <CardContent className="space-y-4">
          <form
            className="flex max-w-md gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setSkip(0)
              setApplied(action.trim())
            }}
          >
            <Input placeholder="Exact action, e.g. auth.login" value={action} onChange={(e) => setAction(e.target.value)} aria-label="Filter by action" />
            <Button type="submit" variant="outline">
              Filter
            </Button>
          </form>
          {audit.isPending ? (
            <LoadingRows />
          ) : audit.isError ? (
            <ErrorState error={audit.error} onRetry={() => audit.refetch()} />
          ) : audit.data.items.length === 0 ? (
            <EmptyState title="No audit events" />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Actor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {audit.data.items.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="whitespace-nowrap text-muted-foreground">{formatDateTime(a.created_at)}</TableCell>
                      <TableCell className="font-mono text-xs">{a.action}</TableCell>
                      <TableCell className="text-sm">
                        {a.resource_type} <span className="font-mono text-xs text-muted-foreground">{a.resource_id?.slice(0, 8)}</span>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{a.actor_user_id?.slice(0, 8) ?? 'system'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Pagination meta={audit.data.meta} onPage={setSkip} />
            </>
          )}
        </CardContent>
      </Card>
    </>
  )
}

export function TemplatesPage() {
  const templates = useQuery({ queryKey: ['templates'], queryFn: api.templates })
  const [selected, setSelected] = useState<string | null>(null)
  const versions = useQuery({ queryKey: ['template-versions', selected], queryFn: () => api.templateVersions(selected!), enabled: !!selected })
  return (
    <>
      <PageHeader
        title="Interview templates"
        description="Versioned form definitions. Interviews keep the template version they were created with. The official DPS template has not yet been provided; the demo template is a placeholder."
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Templates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {templates.isPending && <LoadingRows rows={2} />}
            {templates.isError && <ErrorState error={templates.error} />}
            {templates.data?.map((t) => (
              <button key={t.id} onClick={() => setSelected(t.id)} className={`w-full rounded-md border p-3 text-left text-sm hover:bg-muted ${selected === t.id ? 'border-primary bg-accent' : ''}`}>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-muted-foreground">{t.description}</div>
              </button>
            ))}
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Fields</CardTitle>
            <CardDescription>Field ID, section, and whether the AI may draft it or the interviewer must write it.</CardDescription>
          </CardHeader>
          <CardContent>
            {!selected ? (
              <EmptyState title="Select a template" />
            ) : versions.isPending ? (
              <LoadingRows />
            ) : versions.isError ? (
              <ErrorState error={versions.error} />
            ) : (
              versions.data.map((v) => (
                <div key={v.id} className="mb-6">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                    Version {v.version} {v.is_current && <ToneBadge tone="success">Current</ToneBadge>}
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Label</TableHead>
                        <TableHead>Section</TableHead>
                        <TableHead>Filled by</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {v.fields.map((f) => (
                        <TableRow key={f.id}>
                          <TableCell>
                            <div>{f.label}</div>
                            <div className="font-mono text-xs text-muted-foreground">{f.id}</div>
                          </TableCell>
                          <TableCell>{f.section ?? '—'}</TableCell>
                          <TableCell>{f.source === 'manual_only' ? <ToneBadge tone="attention">Interviewer only</ToneBadge> : <ToneBadge tone="progress">AI draft + human review</ToneBadge>}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}

export function SystemPage() {
  const ready = useQuery({ queryKey: ['health-ready'], queryFn: api.healthReady, retry: false })
  const ai = useQuery({ queryKey: ['health-ai'], queryFn: api.healthAi, retry: false })
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  return (
    <>
      <PageHeader title="System" description="Service health and non-secret configuration. Secrets and infrastructure settings are managed on the server, never in the browser." />
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="size-4" /> Readiness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {ready.isPending ? (
              <LoadingRows rows={2} />
            ) : ready.isError ? (
              <ErrorState error={ready.error} title="Not ready" />
            ) : (
              <dl className="grid grid-cols-2 gap-4">
                {Object.entries(ready.data.checks).map(([k, v]) => (
                  <KeyValue key={k} label={k.replace(/_/g, ' ')}>
                    {v === 'ok' ? <ToneBadge tone="success">ok</ToneBadge> : v === 'unavailable' ? <ToneBadge tone="danger">unavailable</ToneBadge> : v}
                  </KeyValue>
                ))}
              </dl>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI providers</CardTitle>
            <CardDescription>Configuration check only; no model is called.</CardDescription>
          </CardHeader>
          <CardContent>
            {ai.isPending ? (
              <LoadingRows rows={2} />
            ) : ai.isError ? (
              <ErrorState error={ai.error} />
            ) : (
              <dl className="grid gap-4">
                {Object.entries(ai.data.checks).map(([k, v]) => (
                  <KeyValue key={k} label={k}>
                    <span className="flex flex-wrap items-center gap-2">
                      <ToneBadge tone={v.status === 'configured' ? 'success' : 'danger'}>{v.status}</ToneBadge>
                      {v.provider} {v.model && <span className="font-mono text-xs">{v.model}</span>}
                    </span>
                  </KeyValue>
                ))}
              </dl>
            )}
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Limits</CardTitle>
          </CardHeader>
          <CardContent>
            {meta.data && (
              <dl className="grid gap-4 sm:grid-cols-3">
                <KeyValue label="Environment">{meta.data.environment}</KeyValue>
                <KeyValue label="API version">{meta.data.api_version}</KeyValue>
                <KeyValue label="Maximum upload">{formatBytes(meta.data.upload.max_bytes)}</KeyValue>
                <KeyValue label="Accepted audio types">{meta.data.upload.allowed_mime_types.join(', ')}</KeyValue>
              </dl>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}
