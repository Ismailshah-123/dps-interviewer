import type { ReactNode } from 'react'
import { AlertTriangle, ChevronLeft, ChevronRight, Inbox, Loader2 } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError, errorMessage } from '@/lib/api'
import { STATUS_META, type Tone } from '@/lib/status'
import type { InterviewStatus, PageMeta } from '@/lib/types'
import { cn } from '@/lib/utils'

const TONE_CLASS: Record<Tone, string> = {
  neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  info: 'bg-blue-50 text-blue-800 border-blue-200',
  progress: 'bg-indigo-50 text-indigo-800 border-indigo-200',
  attention: 'bg-amber-50 text-amber-900 border-amber-200',
  success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  danger: 'bg-red-50 text-red-800 border-red-200',
}

export function ToneBadge({ tone, children, className }: { tone: Tone; children: ReactNode; className?: string }) {
  return (
    <Badge variant="outline" className={cn('font-medium', TONE_CLASS[tone], className)}>
      {children}
    </Badge>
  )
}

export function StatusBadge({ status }: { status: InterviewStatus }) {
  const meta = STATUS_META[status] ?? { label: status, tone: 'neutral' as Tone, description: '' }
  return (
    <ToneBadge tone={meta.tone}>
      <span title={meta.description}>{meta.label}</span>
    </ToneBadge>
  )
}

export function PageHeader({ title, description, actions, eyebrow }: { title: string; description?: ReactNode; actions?: ReactNode; eyebrow?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">{eyebrow}</div>}
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function ErrorState({ error, onRetry, title = 'Unable to load' }: { error: unknown; onRetry?: () => void; title?: string }) {
  const correlationId = error instanceof ApiError ? error.correlationId : undefined
  return (
    <Alert variant="destructive" role="alert">
      <AlertTriangle />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        <p>{errorMessage(error)}</p>
        {correlationId && <p className="text-xs opacity-80">Reference: {correlationId}</p>}
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
            Try again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

export function EmptyState({ title, description, action, icon }: { title: string; description?: string; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 py-12 text-center">
      <div className="mb-3 text-muted-foreground">{icon ?? <Inbox className="size-8" aria-hidden />}</div>
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function LoadingRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('size-4 animate-spin', className)} aria-hidden />
}

export function Pagination({ meta, onPage }: { meta: PageMeta; onPage: (skip: number) => void }) {
  if (meta.total <= meta.limit) return null
  const from = meta.total === 0 ? 0 : meta.skip + 1
  const to = Math.min(meta.skip + meta.limit, meta.total)
  return (
    <div className="flex items-center justify-between pt-4 text-sm text-muted-foreground">
      <span>
        {from}–{to} of {meta.total}
      </span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={meta.skip === 0} onClick={() => onPage(Math.max(0, meta.skip - meta.limit))}>
          <ChevronLeft /> Previous
        </Button>
        <Button variant="outline" size="sm" disabled={!meta.has_more} onClick={() => onPage(meta.skip + meta.limit)}>
          Next <ChevronRight />
        </Button>
      </div>
    </div>
  )
}

export function KeyValue({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm">{children}</dd>
    </div>
  )
}

/** Visible marker for anything produced by the AI pipeline rather than a person. */
export function AiBadge({ label = 'AI-generated draft' }: { label?: string }) {
  return <ToneBadge tone="progress">{label}</ToneBadge>
}
