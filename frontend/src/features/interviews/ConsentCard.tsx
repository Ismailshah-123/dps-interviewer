import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldCheck, ShieldX } from 'lucide-react'
import { toast } from 'sonner'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Spinner, ToneBadge } from '@/components/common'
import { api, errorMessage } from '@/lib/api'
import type { Interview } from '@/lib/types'

// Placeholder wording. DPS management and legal/privacy review must approve the real notice,
// and changing it must change NOTICE_VERSION so each consent record names the text shown.
export const NOTICE_VERSION = 'DPS-DEMO-NOTICE-1.0'
const NOTICE = [
  'This admission interview will be audio recorded to help the interviewer prepare accurate written notes.',
  'The recording, a transcript and an AI-assisted draft of the interview form are stored privately by the school and are accessible only to authorized staff.',
  'The school’s interviewer and principal review all notes. No admission decision is made by software.',
  'You may decline recording, or ask for it to stop at any time, without affecting the interview.',
]
const CONFIRMATIONS = [
  { id: 'read', label: 'I read or showed this notice to the parent or guardian present.' },
  { id: 'guardian', label: 'The parent or guardian agreed to the interview being recorded.' },
  { id: 'student', label: 'The student was told, in an age-appropriate way, that the conversation is being recorded.' },
]

export function ConsentCard({ interview, canAct }: { interview: Interview; canAct: boolean }) {
  const qc = useQueryClient()
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const [withdrawOpen, setWithdrawOpen] = useState(false)
  const all = CONFIRMATIONS.every((c) => checked[c.id])
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['interview', interview.id] })
    qc.invalidateQueries({ queryKey: ['interviews'] })
  }

  const confirm = useMutation({
    mutationFn: () => api.confirmConsent(interview.id, NOTICE_VERSION),
    onSuccess: () => {
      toast.success('Consent recorded')
      refresh()
    },
    onError: (e) => toast.error(errorMessage(e)),
  })
  const withdraw = useMutation({
    mutationFn: () => api.withdrawConsent(interview.id),
    onSuccess: (r) => {
      toast.message(r.interview_status === 'cancelled' ? 'Consent withdrawn. The interview was cancelled.' : 'Consent withdrawn.')
      setWithdrawOpen(false)
      refresh()
    },
    onError: (e) => toast.error(errorMessage(e)),
  })

  const status = interview.consent_status
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-base">
          Recording consent
          {status === 'confirmed' && <ToneBadge tone="success">Confirmed</ToneBadge>}
          {status === 'withdrawn' && <ToneBadge tone="danger">Withdrawn</ToneBadge>}
          {!status && <ToneBadge tone="attention">Not confirmed</ToneBadge>}
        </CardTitle>
        <CardDescription>
          Notice version <span className="font-mono">{NOTICE_VERSION}</span> · placeholder wording pending school approval
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="list-disc space-y-1.5 rounded-md border bg-muted/40 py-3 pr-4 pl-8 text-sm">
          {NOTICE.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
        {status !== 'confirmed' && canAct && interview.status === 'draft' && (
          <>
            <fieldset className="space-y-3">
              <legend className="sr-only">Consent confirmations</legend>
              {CONFIRMATIONS.map((c) => (
                <div key={c.id} className="flex items-start gap-3">
                  <Checkbox id={`consent-${c.id}`} checked={!!checked[c.id]} onCheckedChange={(v) => setChecked((s) => ({ ...s, [c.id]: v === true }))} />
                  <Label htmlFor={`consent-${c.id}`} className="leading-snug font-normal">
                    {c.label}
                  </Label>
                </div>
              ))}
            </fieldset>
            <Button onClick={() => confirm.mutate()} disabled={!all || confirm.isPending}>
              {confirm.isPending ? <Spinner /> : <ShieldCheck />} Confirm consent
            </Button>
          </>
        )}
        {status === 'confirmed' && canAct && ['draft', 'recording'].includes(interview.status) && (
          <Button variant="outline" className="text-destructive" onClick={() => setWithdrawOpen(true)}>
            <ShieldX /> Record consent withdrawal
          </Button>
        )}
      </CardContent>
      <AlertDialog open={withdrawOpen} onOpenChange={setWithdrawOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Record that consent was withdrawn?</AlertDialogTitle>
            <AlertDialogDescription>
              Stop the recording first. Withdrawing cancels this interview’s recording workflow. Any audio still held only in this browser should be discarded.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Back</AlertDialogCancel>
            <AlertDialogAction className="bg-destructive text-white hover:bg-destructive/90" onClick={() => withdraw.mutate()}>
              Withdraw consent
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}
