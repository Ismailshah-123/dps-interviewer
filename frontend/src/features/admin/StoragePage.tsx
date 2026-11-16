import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Archive, AudioLines, Download, FileText, HardDrive, Play, Search, RefreshCw, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { EmptyState, ErrorState, LoadingRows, PageHeader, Pagination } from '@/components/common'
import { api, errorMessage } from '@/lib/api'
import { formatBytes, formatDateTime } from '@/lib/status'
import type { StorageAsset } from '@/lib/types'

export function StoragePage() {
  const [kind, setKind] = useState<'all' | 'recording' | 'pdf'>('all')
  const [search, setSearch] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [skip, setSkip] = useState(0)
  const [selected, setSelected] = useState<StorageAsset | null>(null)
  const qc = useQueryClient()
  const health = useQuery({
    queryKey: ['admin-storage-health'],
    queryFn: api.storageHealth,
    staleTime: 15_000,
    refetchInterval: 30_000,
    retry: 1,
  })
  const unarchived = useQuery({
    queryKey: ['admin-storage-unarchived'],
    queryFn: () => api.unarchivedInterviews(),
    staleTime: 15_000,
  })
  const archive = useMutation({
    mutationFn: api.archiveFinalizedPdf,
    onSuccess: (document) => {
      toast.success(`Archived ${document.filename}`)
      qc.invalidateQueries({ queryKey: ['admin-storage'] })
      qc.invalidateQueries({ queryKey: ['admin-storage-unarchived'] })
      qc.invalidateQueries({ queryKey: ['admin-storage-health'] })
    },
    onError: (error) => {
      toast.error(`PDF archival failed: ${errorMessage(error)}. You can retry safely from this list.`)
      qc.invalidateQueries({ queryKey: ['admin-storage-health'] })
    },
  })
  const assets = useQuery({
    queryKey: ['admin-storage', { kind, q: appliedSearch, skip }],
    queryFn: () => api.storageAssets({ kind, q: appliedSearch || undefined, skip, limit: 25 }),
    staleTime: 15_000,
  })
  const playback = useQuery({
    queryKey: ['admin-storage-url', selected?.kind, selected?.id],
    queryFn: () => api.storageAssetUrl(selected!),
    enabled: !!selected,
    staleTime: 240_000,
    retry: 1,
  })
  const file = useQuery({
    queryKey: ['admin-storage-blob', selected?.kind, selected?.id],
    queryFn: () => api.storageAssetBlob(selected!),
    enabled: !!selected && !playback.isPending && !playback.data?.url,
    staleTime: 60_000,
    retry: 1,
  })
  const [blobPreviewUrl, setBlobPreviewUrl] = useState<string | null>(null)
  const previewUrl = playback.data?.url ?? blobPreviewUrl

  useEffect(() => {
    if (!file.data) {
      setBlobPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file.data)
    setBlobPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file.data])

  const downloadSelected = async () => {
    if (!selected) return
    try {
      const blob = await api.storageAssetBlob({ ...selected }, 'attachment')
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = selected.filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      // Keep the object URL alive long enough for the browser to start the download.
      window.setTimeout(() => URL.revokeObjectURL(url), 10_000)
    } catch (error) {
      toast.error(errorMessage(error))
    }
  }

  const items = assets.data?.items ?? []
  const totalBytes = items.reduce((sum, item) => sum + item.size_bytes, 0)

  return (
    <div className="page-enter space-y-6">
      <PageHeader
        eyebrow="Administration / Records"
        title="Storage library"
        description="Private interview recordings and finalized PDF documents stored through the configured secure storage provider."
        actions={<div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm text-muted-foreground"><HardDrive className="size-4" /> {items.length} shown · {formatBytes(totalBytes)}</div>}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="storage-summary-card">
          <CardContent className="flex items-center gap-3 pt-5">
            <div className="rounded-xl bg-blue-50 p-3 text-blue-800"><Archive className="size-5" /></div>
            <div><p className="text-xs text-muted-foreground">Total stored items</p><p className="font-display text-2xl font-semibold tabular-nums">{health.data ? health.data.recordings + health.data.pdfs : '—'}</p></div>
          </CardContent>
        </Card>
        <Card className="storage-summary-card">
          <CardContent className="flex items-center gap-3 pt-5">
            <div className="rounded-xl bg-indigo-50 p-3 text-indigo-800"><AudioLines className="size-5" /></div>
            <div><p className="text-xs text-muted-foreground">Total recordings</p><p className="font-display text-2xl font-semibold tabular-nums">{health.data?.recordings ?? '—'}</p></div>
          </CardContent>
        </Card>
        <Card className="storage-summary-card">
          <CardContent className="flex items-center gap-3 pt-5">
            <div className="rounded-xl bg-emerald-50 p-3 text-emerald-800"><FileText className="size-5" /></div>
            <div><p className="text-xs text-muted-foreground">Total PDFs</p><p className="font-display text-2xl font-semibold tabular-nums">{health.data?.pdfs ?? '—'}</p></div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">Storage health</CardTitle>
            <CardDescription>Live provider check and database-to-object integrity scan. Automatically refreshes every 30 seconds.</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => { void health.refetch(); void assets.refetch() }} disabled={health.isFetching}>
            <RefreshCw className={health.isFetching ? 'size-4 animate-spin' : 'size-4'} /> Refresh
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {health.isPending ? <LoadingRows rows={2} /> : health.isError ? (
            <ErrorState error={health.error} onRetry={() => health.refetch()} />
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Provider</p>
                  <p className="mt-1 font-semibold uppercase">{health.data.provider}</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Connection</p>
                  <p className="mt-1 flex items-center gap-2 font-semibold">
                    {health.data.connection === 'connected' ? <CheckCircle2 className="size-4 text-emerald-600" /> : <XCircle className="size-4 text-destructive" />}
                    {health.data.connection}
                  </p>
                  {health.data.connection_error && <p className="mt-1 text-xs text-destructive">{health.data.connection_error}</p>}
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Recordings / PDFs</p>
                  <p className="mt-1 font-semibold tabular-nums">{health.data.recordings} / {health.data.pdfs}</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Objects checked</p>
                  <p className="mt-1 font-semibold tabular-nums">{health.data.checked_objects}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                <span className={health.data.missing_count ? 'rounded-full bg-destructive/10 px-3 py-1 text-destructive' : 'rounded-full bg-emerald-500/10 px-3 py-1 text-emerald-700'}>
                  {health.data.missing_count} missing files
                </span>
                <span className="rounded-full bg-amber-500/10 px-3 py-1 text-amber-800">{health.data.pending_archives} PDFs awaiting archival</span>
                <span className={health.data.failed_archivals ? 'rounded-full bg-destructive/10 px-3 py-1 text-destructive' : 'rounded-full bg-muted px-3 py-1 text-muted-foreground'}>
                  {health.data.failed_archivals} failed archival attempts
                </span>
              </div>
              {health.data.checked_objects >= health.data.checked_limit && <p className="text-xs text-muted-foreground">Integrity scan is limited to the latest {health.data.checked_limit} stored objects. A zero missing count applies only to the objects checked.</p>}
              {health.data.missing_assets.length > 0 && (
                <div className="rounded-lg border border-destructive/30 p-3">
                  <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-destructive"><AlertTriangle className="size-4" /> Missing storage objects</p>
                  <ul className="space-y-1 text-sm">
                    {health.data.missing_assets.map((item) => <li key={item.id}>{item.kind.toUpperCase()} · {item.filename}</li>)}
                  </ul>
                  <p className="mt-2 text-xs text-muted-foreground">These database records point to files that could not be found in the configured storage provider. Do not delete records automatically.</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {unarchived.data?.items.length ? (
        <Card className="border-amber-200/80">
          <CardHeader>
            <CardTitle className="text-base">PDF archival needs attention</CardTitle>
            <CardDescription>These finalized records or previously failed finalizations need a PDF archive. Retry is safe and does not duplicate an identical PDF.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {unarchived.data.items.map((item) => (
              <div key={item.interview_id} className="flex flex-col gap-3 rounded-lg border p-3 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{item.candidate_name}</p>
                  <p className="text-xs text-muted-foreground">{item.candidate_reference} · {item.finalized_at ? `Finalized ${formatDateTime(item.finalized_at)}` : 'Finalization retry required'}</p>
                </div>
                <Button size="sm" variant="outline" onClick={() => archive.mutate(item.interview_id)} disabled={archive.isPending}>
                  {archive.isPending ? 'Archiving…' : 'Retry PDF archival'}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Stored files</CardTitle>
            <CardDescription>Only administrators can browse these records. Files remain private; access is streamed through authenticated endpoints.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form className="flex flex-col gap-2 sm:flex-row" onSubmit={(event) => { event.preventDefault(); setSelected(null); setAppliedSearch(search.trim()); setSkip(0) }}>
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search candidate or file" aria-label="Search stored files" />
              </div>
              <Select value={kind} onValueChange={(value) => { setSelected(null); setKind(value as 'all' | 'recording' | 'pdf'); setSkip(0) }}>
                <SelectTrigger className="w-full sm:w-40" aria-label="Filter storage type"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All files</SelectItem>
                  <SelectItem value="recording">Recordings</SelectItem>
                  <SelectItem value="pdf">PDF documents</SelectItem>
                </SelectContent>
              </Select>
              <Button type="submit" variant="outline">Search</Button>
            </form>

            {assets.isPending ? <LoadingRows rows={5} /> : assets.isError ? <ErrorState error={assets.error} onRetry={() => assets.refetch()} /> : items.length === 0 ? (
              <EmptyState title={kind === 'pdf' ? 'No archived PDFs yet' : 'No stored files found'} description={kind === 'pdf' ? 'PDFs appear here after an authorized reviewer completes principal review and finalizes the interview record. Approval alone does not archive the PDF; finalization generates and stores it in the private storage library.' : 'Recordings appear here after an interview recording has been uploaded successfully to private storage.'} />
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelected(item)}
                    className={`storage-file-row flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-all hover:border-primary/40 hover:bg-accent/50 ${selected?.id === item.id ? 'border-primary bg-accent/60 shadow-sm' : 'bg-card'}`}
                  >
                    <div className="rounded-lg bg-muted p-2 text-muted-foreground">{item.kind === 'recording' ? <AudioLines className="size-5" /> : <FileText className="size-5" />}</div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.candidate_name}</p>
                      <p className="truncate text-xs text-muted-foreground">{item.candidate_reference} · {item.filename}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{formatBytes(item.size_bytes)} · {formatDateTime(item.created_at)}</p>
                    </div>
                    <span className="rounded-full border px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{item.kind === 'pdf' ? `PDF · v${item.version_number ?? 1}` : 'Audio'}</span>
                  </button>
                ))}
                <Pagination meta={assets.data!.meta} onPage={(nextSkip) => { setSelected(null); setSkip(nextSkip) }} />
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="storage-preview-card xl:sticky xl:top-20">
          <CardHeader>
            <CardTitle className="text-base">File preview</CardTitle>
            <CardDescription>{selected ? selected.filename : 'Select a file to inspect it securely.'}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selected ? <EmptyState title="Nothing selected" description="Choose a recording or PDF from the library." /> : playback.isPending || (!playback.data?.url && file.isPending) ? <LoadingRows rows={3} /> : playback.isError && file.isError ? <ErrorState error={file.error} onRetry={() => { void playback.refetch(); void file.refetch() }} /> : previewUrl && selected.kind === 'recording' ? (
              <div className="rounded-xl border bg-muted/30 p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium"><AudioLines className="size-4" /> Recording playback</div>
                <audio className="w-full" controls preload="metadata" src={previewUrl}>Your browser does not support audio playback.</audio>
              </div>
            ) : previewUrl ? (
              <iframe title={`PDF preview: ${selected.filename}`} src={previewUrl} className="h-[560px] w-full rounded-lg border bg-white" />
            ) : null}
            {selected && (
              <div className="space-y-3 border-t pt-4">
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-xs text-muted-foreground">Candidate</dt><dd className="mt-1 font-medium">{selected.candidate_name}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">Reference</dt><dd className="mt-1 font-mono text-xs">{selected.candidate_reference}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">File size</dt><dd className="mt-1">{formatBytes(selected.size_bytes)}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">Added</dt><dd className="mt-1">{formatDateTime(selected.created_at)}</dd></div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <Button className="flex-1" onClick={() => void downloadSelected()} ><Download /> Download file</Button>
                  <Button variant="outline" onClick={() => window.open(`/interviews/${selected.interview_id}`, '_self')}><Play /> Interview</Button>
                </div>
                {file.isError && <p className="text-xs text-destructive">{errorMessage(file.error)}</p>}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
