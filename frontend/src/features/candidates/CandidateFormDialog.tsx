import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Spinner } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api, errorMessage } from '@/lib/api'
import type { Candidate } from '@/lib/types'

// Only the minimum the workflow needs. School-specific fields stay configurable, not invented here.
export const candidateSchema = z.object({
  name: z.string().trim().min(1, 'Candidate name is required').max(200),
  application_reference: z.string().trim().max(100).optional(),
  grade: z.string().trim().max(100).optional(),
  interview_datetime: z.string().optional(),
  assigned_interviewer_id: z.string().optional(),
})
export type CandidateValues = z.infer<typeof candidateSchema>

function toLocalInput(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

export function CandidateFormDialog({ open, onOpenChange, candidate, onSaved }: { open: boolean; onOpenChange: (o: boolean) => void; candidate?: Candidate; onSaved?: (c: Candidate) => void }) {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [duplicate, setDuplicate] = useState<Candidate | null>(null)
  const isAdmin = user?.role === 'administrator'
  const interviewers = useQuery({ queryKey: ['users', 'interviewer'], queryFn: () => api.users({ role: 'interviewer', limit: 100 }), enabled: open && isAdmin })
  const form = useForm<CandidateValues>({ resolver: zodResolver(candidateSchema) })

  useEffect(() => {
    if (open) {
      setDuplicate(null)
      form.reset({
        name: candidate?.name ?? '',
        application_reference: candidate?.application_reference ?? '',
        grade: candidate?.grade ?? '',
        interview_datetime: toLocalInput(candidate?.interview_datetime ?? null),
        assigned_interviewer_id: candidate?.assigned_interviewer_id ?? '',
      })
    }
  }, [open, candidate, form])

  const save = useMutation({
    mutationFn: async (values: CandidateValues) => {
      const body = {
        name: values.name,
        application_reference: values.application_reference || null,
        grade: values.grade || null,
        interview_datetime: values.interview_datetime ? new Date(values.interview_datetime).toISOString() : null,
        ...(isAdmin && values.assigned_interviewer_id ? { assigned_interviewer_id: values.assigned_interviewer_id } : {}),
      }
      return candidate ? api.updateCandidate(candidate.id, body) : api.createCandidate(body)
    },
    onSuccess: (c) => {
      qc.invalidateQueries({ queryKey: ['candidates'] })
      qc.invalidateQueries({ queryKey: ['candidate', c.id] })
      toast.success(candidate ? 'Candidate updated' : `Candidate ${c.reference_number} created`)
      onOpenChange(false)
      onSaved?.(c)
    },
  })

  const onSubmit = form.handleSubmit(async (values) => {
    // Duplicate detection: warn once when the application reference or exact name already exists.
    if (!candidate && !duplicate) {
      const probe = values.application_reference || values.name
      const existing = await api.candidates({ q: probe, limit: 5 }).catch(() => null)
      const match = existing?.items.find(
        (c) => (values.application_reference && c.application_reference === values.application_reference) || c.name.toLowerCase() === values.name.toLowerCase(),
      )
      if (match) return setDuplicate(match)
    }
    save.mutate(values)
  })

  const errors = form.formState.errors
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{candidate ? 'Edit candidate' : 'New candidate'}</DialogTitle>
          <DialogDescription>Collect only what the school requires. A reference number is generated automatically.</DialogDescription>
        </DialogHeader>
        <form id="candidate-form" onSubmit={onSubmit} className="space-y-4" noValidate>
          {save.isError && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage(save.error)}</AlertDescription>
            </Alert>
          )}
          {duplicate && (
            <Alert>
              <AlertDescription>
                A candidate with this name or application reference already exists ({duplicate.reference_number}). Submit again to create a separate record anyway.
              </AlertDescription>
            </Alert>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="name">Candidate name</Label>
            <Input id="name" aria-invalid={!!errors.name} {...form.register('name')} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="application_reference">Application reference</Label>
              <Input id="application_reference" {...form.register('application_reference')} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="grade">Class / grade applied for</Label>
              <Input id="grade" {...form.register('grade')} />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="interview_datetime">Interview date and time</Label>
            <Input id="interview_datetime" type="datetime-local" {...form.register('interview_datetime')} />
          </div>
          {isAdmin && (
            <div className="space-y-1.5">
              <Label>Assigned interviewer</Label>
              <Select value={form.watch('assigned_interviewer_id') || undefined} onValueChange={(v) => form.setValue('assigned_interviewer_id', v)}>
                <SelectTrigger className="w-full" aria-label="Assigned interviewer">
                  <SelectValue placeholder="Select an interviewer" />
                </SelectTrigger>
                <SelectContent>
                  {interviewers.data?.items
                    .filter((u) => u.is_active)
                    .map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {u.full_name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">An interview can only be created once an interviewer is assigned.</p>
            </div>
          )}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="submit" form="candidate-form" disabled={save.isPending}>
            {save.isPending && <Spinner />} {candidate ? 'Save changes' : duplicate ? 'Create anyway' : 'Create candidate'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
