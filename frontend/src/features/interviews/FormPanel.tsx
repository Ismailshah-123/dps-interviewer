import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Save, Send } from 'lucide-react'
import { toast } from 'sonner'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { EmptyState, ErrorState, LoadingRows, Spinner, ToneBadge } from '@/components/common'
import { ApiError, api, errorMessage } from '@/lib/api'
import { containsArabicScript, formatDateTime } from '@/lib/status'
import type { FormField, Interview, TemplateFieldSpec } from '@/lib/types'

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
    <div className="space-y-2 border-b py-5 last:border-0">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor={id} className="text-sm font-semibold">
          {spec?.label ?? field.field_id}
          {spec?.required && <span className="text-destructive"> *</span>}
        </label>
        {sourceBadge(field)}
        {field.review_status === 'reviewed' ? <ToneBadge tone="success">Reviewed</ToneBadge> : <ToneBadge tone="progress">Included in interview review</ToneBadge>}
      </div>
      {editable ? (
        <Textarea
          id={id}
          value={text}
          dir={rtl ? 'rtl' : 'auto'}
          lang={rtl ? 'ur' : undefined}
          className={rtl ? 'urdu min-h-24' : 'min-h-24'}
          placeholder={manualEmpty ? 'Professional judgement — to be written by the interviewer. Leave blank only if not applicable.' : undefined}
          onChange={(e) => setText(e.target.value)}
        />
      ) : (
        <p id={id} dir="auto" className="rounded-md bg-muted/40 px-3 py-2 text-sm whitespace-pre-wrap">
          {field.value.text || <span className="text-muted-foreground italic">Left blank</span>}
        </p>
      )}
      {field.human_edited && field.generated_value && field.generated_value.text !== field.value.text && (
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer">Show original AI draft</summary>
          <p className="mt-1 whitespace-pre-wrap">{field.generated_value.text || '(empty)'}</p>
        </details>
      )}
      {editable && (
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant={dirty ? 'default' : 'outline'} disabled={!dirty || save.isPending} onClick={() => save.mutate()} aria-label={`Save field: ${label}`}>
            {save.isPending ? <Spinner /> : <Save />} Save edit
          </Button>
          <span className="text-xs text-muted-foreground">Updated {formatDateTime(field.updated_at)}</span>
        </div>
      )}
    </div>
  )
}

export function FormPanel({ interview, editable, canSubmit }: { interview: Interview; editable: boolean; canSubmit: boolean }) {
  const qc = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)
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
    const fields = [...(form.data?.fields ?? [])].sort((a, b) => order.indexOf(a.field_id) - order.indexOf(b.field_id))
    for (const f of fields) {
      const section = specs.get(f.field_id)?.section ?? 'Other'
      groups.set(section, [...(groups.get(section) ?? []), f])
    }
    return [...groups.entries()]
  }, [form.data, template.data, specs])

  if (form.isPending) return <LoadingRows rows={8} />
  if (form.isError)
    return form.error instanceof ApiError && form.error.status === 404 ? (
      <EmptyState title="Form not ready" description="The form draft is created after the transcript and summary are complete." />
    ) : (
      <ErrorState error={form.error} onRetry={() => form.refetch()} />
    )

  const additionalConversation = summary.data?.data.additional_conversation ?? []
  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="text-base">{template.data?.template_name ?? 'Interview form'}</CardTitle>
          <CardDescription>
            Template version {template.data?.version ?? '—'} · form revision {form.data.version_number}.{' '}
            {template.data?.template_description && <span className="font-medium text-amber-800">{template.data.template_description}</span>}
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void downloadPdf(interview)}>
            <Download /> PDF
          </Button>
          {canSubmit && (
            <Button onClick={() => setConfirmOpen(true)}>
              <Send /> {interview.status === 'correction_requested' ? 'Resubmit' : 'Submit for review'}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {canSubmit && (
          <p className="mb-2 text-sm text-muted-foreground">
            Review the complete interview, including the transcript and any additional conversation below. You can submit once the interview-level review is complete; individual field confirmations are not required.
          </p>
        )}
        {sections.map(([section, fields]) => (
          <section key={section} className="mt-4">
            <h3 className="border-b pb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{section}</h3>
            {fields.map((f) => (
              <FieldEditor key={`${f.id}-${f.updated_at}`} formId={form.data.id} field={f} spec={specs.get(f.field_id)} editable={editable} />
            ))}
          </section>
        ))}
        <section className="mt-8 border-t pt-5">
          <div className="mb-3">
            <h3 className="text-sm font-semibold">Additional conversation</h3>
            <p className="text-xs text-muted-foreground">Distinct follow-up questions and parent/interviewer exchanges that do not belong to the official DPS form. These are kept separate so the original form stays unchanged.</p>
          </div>
          {summary.isPending ? (
            <p className="text-sm text-muted-foreground">Loading additional conversation…</p>
          ) : additionalConversation.length ? (
            <div className="space-y-4">
              {additionalConversation.map((item, index) => (
                <div key={index} className="rounded-lg border p-3">
                  <p className="text-xs font-medium text-muted-foreground">Question {index + 1} · Asked by {item.asked_by}</p>
                  <p className="mt-1 text-sm font-semibold" dir="auto">{item.question}</p>
                  <p className="mt-2 text-xs font-medium text-muted-foreground">Answer · {item.answered_by}</p>
                  <p className="mt-1 text-sm whitespace-pre-wrap" dir="auto">{item.answer || 'No clear answer captured'}</p>
                  {item.evidence_quotes?.length > 0 && (
                    <p className="mt-2 text-xs text-muted-foreground">Transcript evidence: {item.evidence_quotes.join(' · ')}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">No additional question-and-answer exchanges were detected.</p>
          )}
        </section>
      </CardContent>
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit this interview for principal review?</AlertDialogTitle>
            <AlertDialogDescription>
              You confirm that you have checked every field against the conversation and the transcript. After submission the transcript and form are locked unless the principal
              requests a correction.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep editing</AlertDialogCancel>
            <AlertDialogAction onClick={() => submit.mutate()} disabled={submit.isPending}>
              Submit
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}
