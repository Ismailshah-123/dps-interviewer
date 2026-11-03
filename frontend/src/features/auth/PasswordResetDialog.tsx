import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api, errorMessage } from '@/lib/api'

/**
 * Two-step reset. The response is deliberately the same whether or not the account exists.
 * In the demo build the backend may return the token directly (EXPOSE_DEMO_RESET_TOKEN); in
 * production it must be delivered out of band (email), and that setting is refused.
 */
export function PasswordResetDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [step, setStep] = useState<'request' | 'confirm' | 'done'>('request')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const reset = () => {
    setStep('request')
    setToken('')
    setPassword('')
    setMessage(null)
    setError(null)
  }

  const request = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await api.requestPasswordReset(email)
      setMessage(res.message)
      if (res.demo_token) setToken(res.demo_token)
      setStep('confirm')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const confirm = async () => {
    if (password.length < 12) return setError('Use at least 12 characters.')
    setBusy(true)
    setError(null)
    try {
      await api.confirmPasswordReset(token, password)
      setStep('done')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset()
        onOpenChange(o)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reset password</DialogTitle>
          <DialogDescription>Reset links expire after 30 minutes and can be used once.</DialogDescription>
        </DialogHeader>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {step === 'request' && (
          <div className="space-y-1.5">
            <Label htmlFor="reset-email">Email</Label>
            <Input id="reset-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
        )}
        {step === 'confirm' && (
          <div className="space-y-3">
            {message && <p className="text-sm text-muted-foreground">{message}</p>}
            <div className="space-y-1.5">
              <Label htmlFor="reset-token">Reset code</Label>
              <Input id="reset-token" value={token} onChange={(e) => setToken(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="reset-password">New password</Label>
              <Input id="reset-password" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          </div>
        )}
        {step === 'done' && <p className="text-sm">Password updated. All other sessions for this account were signed out.</p>}
        <DialogFooter>
          {step === 'request' && (
            <Button onClick={request} disabled={busy || !email}>
              Send reset code
            </Button>
          )}
          {step === 'confirm' && (
            <Button onClick={confirm} disabled={busy || !token}>
              Set new password
            </Button>
          )}
          {step === 'done' && <Button onClick={() => onOpenChange(false)}>Close</Button>}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
