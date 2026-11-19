import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, ClipboardCheck, Download, Search, Send, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { EmptyState, ErrorState, LoadingRows, Spinner, ToneBadge } from '@/components/common'
import { ApiError, api, errorMessage } from '@/lib/api'
import { containsArabicScript, formatDateTime } from '@/lib/status'
import type { FormField, Interview, TemplateFieldSpec } from '@/lib/types'
import { getFormMetrics } from './formMetrics'

export function sourceBadge(field: FormField) {
  if (field.human_edited) return <ToneBadge tone="success">Entered / edited by staff</ToneBadge>
  switch (field.value.source) {
    case 'manual_required':
      return <ToneBadge tone="attention">Interviewer entry required</ToneBadge>
    case 'not_mentioned':
      return <ToneBadge tone="neutral">Not mentioned in transcript</ToneBadge>
    default:
      return <ToneBadge tone="progress">AI draft from transcript</ToneBadge>
  }
}

export async function downloadPdf(interview: Interview) {
  try {
    const blob = await api.formPdf(interview.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${interview.candidate_reference ?? 'interview'}-interview-form.pdf`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  } catch (e) {
    toast.error(errorMessage(e))
  }
}

function FieldEditor({ formId, field, spec, editable }: { formId: string; field: FormField; spec?: TemplateFieldSpec; editable: boolean }) {
  const qc = useQueryClient()
  const [text, setText] = useState(field.value.text ?? '')
  const dirty = text !== (field.value.text ?? '')
  const rtl = containsArabicScript(text)
  const onDone = () => qc.invalidateQueries({ queryKey: ['form'] })
  const save = useMutation({ mutationFn: () => api.updateField(formId, field.field_id, text), onSuccess: () => (toast.success('Field saved'), onDone()), onError: (e) => toast.error(errorMessage(e)) })
  const manualEmpty = field.value.source === 'manual_required' && !field.human_edited
  const id = `field-${field.field_id}`
  const label = spec?.label ?? field.field_id

  return (
    <article id={id} className="scroll-mt-24 border-b py-5 last:border-0" aria-label={label}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor={id} className="text-sm font-semibold">
            {label}
            {spec?.required && <span className="ml-1 text-destructive" aria-label="required">*</span>}
          </label>
          {sourceBadge(field)}
        </div>
        {field.review_status === 'reviewed' ? <ToneBadge tone="success">Reviewed</ToneBadge> : <ToneBadge tone="progress">Needs review</ToneBadge>}
      </div>
      {spec?.human_review && <p className="mt-1 text-xs text-muted-foreground">Please verify this field against the original interview before submitting.</p>}
      {editable ? (
        <Textarea
          id={id}
          value={text}
          dir={rtl ? 'rtl' : 'auto'}
          lang={rtl ? 'ur' : undefined}
          className={rtl ? 'urdu mt-3 min-h-28' : 'mt-3 min-h-28'}
          placeholder={manualEmpty ? 'Enter the interviewer’s professional observation. Leave blank if not applicable.' : 'Review the draft and make corrections where needed.'}
          onChange={(e) => setText(e.target.value)}
        />
      ) : (
        <p dir="auto" className="mt-3 min-h-12 rounded-lg bg-muted/40 px-3 py-3 text-sm whitespace-pre-wrap">
          {field.value.text || <span className="text-muted-foreground italic">No response recorded</span>}
        </p>
      )}
      {field.human_edited && field.generated_value && field.generated_value.text !== field.value.text && (
        <details className="mt-2 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-medium">Compare with original AI draft</summary>
          <p className="mt-2 rounded-md bg-muted/40 p-3 whitespace-pre-wrap">{field.generated_value.text || '(empty)'}</p>
        </details>
      )}
      {editable && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">Last updated {formatDateTime(field.updated_at)}</span>
          <Button size="sm" variant={dirty ? 'default' : 'outline'} disabled={!dirty || save.isPending} onClick={() => save.mutate()} aria-label={`Save field: ${label}`}>
            {save.isPending ? <Spinner /> : <ClipboardCheck />} {save.isPending ? 'Saving…' : dirty ? 'Save changes' : 'Saved'}
          </Button>
        </div>
      )}
    </article>
  )
}

export function FormPanel({ interview, editable, canSubmit }: { interview: Interview; editable: boolean; canSubmit: boolean }) {
  const qc = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [search, setSearch] = useState('')
  const form = useQuery({ queryKey: ['form', interview.id], queryFn: () => api.form(interview.id), retry: (n, e) => !(e instanceof ApiError && e.status === 404) && n < 2 })
  const template = useQuery({ queryKey: ['template-version', interview.template_version_id], queryFn: () => api.templateVersion(interview.template_version_id!), enabled: !!interview.template_version_id, staleTime: Infinity })
  const summary = useQuery({ queryKey: ['summary', interview.id], queryFn: () => api.summary(interview.id), retry: false })
  const submit = useMutation({
    mutationFn: () => api.submitInterview(interview.id),
    onSuccess: () => {
      toast.success('Submitted for principal review')
      setConfirmOpen(false)
      qc.invalidateQueries({ queryKey: ['interview', interview.id] })
      qc.invalidateQueries({ queryKey: ['interviews'] })
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  const specs = useMemo(() => new Map((template.data?.fields ?? []).map((f) => [f.id, f])), [template.data])
  const sections = useMemo(() => {
    const groups = new Map<string, FormField[]>()
    const order = template.data?.fields.map((f) => f.id) ?? []
    const fields = [...(form.data?.fields ?? [])].sort((a, b) => {
      const ai = order.indexOf(a.field_id), bi = order.indexOf(b.field_id)
      return (ai < 0 ? Number.MAX_SAFE_INTEGER : ai) - (bi < 0 ? Number.MAX_SAFE_INTEGER : bi)
    })
    for (const field of fields) {
      const section = specs.get(field.field_id)?.section ?? 'Other'
      groups.set(section, [...(groups.get(section) ?? []), field])
    }
    return [...groups.entries()]
  }, [form.data, template.data, specs])
  const metrics = useMemo(() => getFormMetrics(form.data?.fields ?? [], specs), [form.data, specs])
  const filteredSections = useMemo(() => {
    const q = search.trim().toLocaleLowerCase()
    if (!q) return sections
    return sections.map(([name, fields]) => [name, fields.filter((field) => {
      const label = specs.get(field.field_id)?.label ?? field.field_id
      return label.toLocaleLowerCase().includes(q) || (field.value.text ?? '').toLocaleLowerCase().includes(q)
    })] as [string, FormField[]]).filter(([, fields]) => fields.length > 0)
  }, [sections, search, specs])

  if (form.isPending) return <LoadingRows rows={8} />
  if (form.isError)
    return form.error instanceof ApiError && form.error.status === 404 ? (
      <EmptyState title="Form not ready" description="The form draft is created after the transcript and summary are complete." />
    ) : (
      <ErrorState error={form.error} onRetry={() => form.refetch()} />
    )

  const additionalConversation = summary.data?.data.additional_conversation ?? []
  const completion = metrics.required ? Math.round((metrics.requiredComplete / metrics.required) * 100) : 100
  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="gap-4">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-base">{template.data?.template_name ?? 'Interview form'}</CardTitle>
                <ToneBadge tone={editable ? 'progress' : 'neutral'}>{editable ? 'Editable draft' : 'Read only'}</ToneBadge>
              </div>
              <CardDescription>
                Template version {template.data?.version ?? '—'} · form revision {form.data.version_number}
                {template.data?.template_description ? ` · ${template.data.template_description}` : ''}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => void downloadPdf(interview)}>
                <Download /> Export PDF
              </Button>
              {canSubmit && (
                <Button onClick={() => setConfirmOpen(true)}>
                  <Send /> {interview.status === 'correction_requested' ? 'Resubmit for review' : 'Submit for review'}
                </Button>
              )}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Form fields</p>
              <p className="mt-1 text-xl font-semibold tabular-nums">{metrics.total}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Required completed</p>
              <p className="mt-1 text-xl font-semibold tabular-nums">{metrics.requiredComplete}<span className="text-sm font-normal text-muted-foreground"> / {metrics.required}</span></p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Awaiting review</p>
              <p className="mt-1 text-xl font-semibold tabular-nums">{metrics.awaitingReview}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">AI draft fields</p>
              <p className="mt-1 text-xl font-semibold tabular-nums">{metrics.aiDrafts}</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium">Required-field completion</span>
              <span className="tabular-nums text-muted-foreground">{completion}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted" role="progressbar" aria-label="Required field completion" aria-valuemin={0} aria-valuemax={100} aria-valuenow={completion}>
              <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${completion}%` }} />
            </div>
            {metrics.missingRequired > 0 && (
              <p className="flex items-center gap-2 text-xs text-amber-700">
                <AlertCircle className="size-4" /> {metrics.missingRequired} required {metrics.missingRequired === 1 ? 'field is' : 'fields are'} still blank. Please check before submission.
              </p>
            )}
            {metrics.missingRequired === 0 && (
              <p className="flex items-center gap-2 text-xs text-emerald-700"><CheckCircle2 className="size-4" /> All required fields have a response.</p>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {canSubmit && (
            <p className="text-sm text-muted-foreground">
              Review the form, transcript and additional conversation before submitting. Required-field indicators are guidance; the system does not block submission solely because a field is blank.
            </p>
          )}
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search questions or answers…" className="pl-9" aria-label="Search interview form fields" />
          </div>
          {!search && sections.length > 1 && (
            <nav aria-label="Interview form sections" className="flex flex-wrap gap-2">
              {sections.map(([section, fields]) => (
                <a key={section} href={`#section-${encodeURIComponent(section)}`} className="rounded-full border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
                  {section} <span className="ml-1 tabular-nums">{fields.length}</span>
                </a>
              ))}
            </nav>
          )}
          {filteredSections.length ? filteredSections.map(([section, fields]) => (
            <section id={`section-${encodeURIComponent(section)}`} key={section} className="scroll-mt-24">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
                <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{section}</h3>
                <span className="text-xs text-muted-foreground">{fields.length} {fields.length === 1 ? 'field' : 'fields'}</span>
              </div>
              {fields.map((field) => (
                <FieldEditor key={`${field.id}-${field.updated_at}`} formId={form.data.id} field={field} spec={specs.get(field.field_id)} editable={editable} />
              ))}
            </section>
          )) : (
            <div className="rounded-lg border border-dashed px-4 py-10 text-center">
              <Search className="mx-auto size-5 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium">No matching fields</p>
              <p className="mt-1 text-xs text-muted-foreground">Try another question, section or answer keyword.</p>
              <Button className="mt-3" size="sm" variant="outline" onClick={() => setSearch('')}>Clear search</Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Sparkles className="size-4" /> Additional conversation</CardTitle>
          <CardDescription>Follow-up questions and parent/interviewer exchanges are kept separate from the official form fields.</CardDescription>
        </CardHeader>
        <CardContent>
          {summary.isPending ? (
            <p className="text-sm text-muted-foreground">Loading additional conversation…</p>
          ) : additionalConversation.length ? (
            <div className="space-y-3">
              {additionalConversation.map((item, index) => (
                <article key={index} className="rounded-lg border p-4">
                  <p className="text-xs font-medium text-muted-foreground">Question {index + 1} · Asked by {item.asked_by}</p>
                  <p className="mt-1 text-sm font-semibold" dir="auto">{item.question}</p>
                  <p className="mt-3 text-xs font-medium text-muted-foreground">Answer · {item.answered_by}</p>
                  <p className="mt-1 text-sm whitespace-pre-wrap" dir="auto">{item.answer || 'No clear answer captured'}</p>
                  {item.evidence_quotes?.length > 0 && <p className="mt-2 text-xs text-muted-foreground">Transcript evidence: {item.evidence_quotes.join(' · ')}</p>}
                </article>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">No additional question-and-answer exchanges were detected.</p>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit this interview for principal review?</AlertDialogTitle>
            <AlertDialogDescription>
              You confirm that you have reviewed the complete interview, including form answers, blank or unclear fields, transcript and additional conversation. Fields do not need to be individually confirmed. After submission, the transcript and form are locked unless the principal requests a correction.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep editing</AlertDialogCancel>
            <AlertDialogAction onClick={() => submit.mutate()} disabled={submit.isPending}>
              {submit.isPending ? <Spinner /> : null} Submit interview
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
