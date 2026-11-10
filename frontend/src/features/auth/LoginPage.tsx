import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Navigate, useLocation, useNavigate } from 'react-router'
import { Eye, EyeOff, KeyRound, ShieldCheck } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Spinner } from '@/components/common'
import { errorMessage } from '@/lib/api'
import { useAuth } from './AuthProvider'
import { PasswordResetDialog } from './PasswordResetDialog'

const schema = z.object({
  email: z.string().trim().min(3, 'Enter your school email address'),
  password: z.string().min(1, 'Enter your password'),
})
type Values = z.infer<typeof schema>

export function LoginPage() {
  const { status, signIn, sessionExpired } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [resetOpen, setResetOpen] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const { register, handleSubmit, formState } = useForm<Values>({ resolver: zodResolver(schema) })
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  if (status === 'authenticated') return <Navigate to={from} replace />

  const onSubmit = handleSubmit(async (values) => {
    setError(null)
    try {
      await signIn(values.email, values.password)
      navigate(from, { replace: true })
    } catch (e) {
      setError(errorMessage(e))
    }
  })

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-sidebar p-10 text-sidebar-foreground lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-md bg-white/10 font-semibold">DPS</div>
          <span className="font-medium">Dawood Public School</span>
        </div>
        <div className="max-w-md space-y-4">
          <h2 className="text-3xl font-semibold leading-tight text-white">Interview documentation, prepared for human review.</h2>
          <p className="text-sidebar-muted">
            Record admission interviews with consent, produce a transcript and a draft of the school’s interview form, and route it to the principal. Staff review every
            field. The system never makes admission decisions.
          </p>
        </div>
        <p className="flex items-center gap-2 text-xs text-sidebar-muted">
          <ShieldCheck className="size-4" /> Authorized school personnel only. Activity is audited.
        </p>
      </div>
      <div className="flex items-center justify-center p-6">
        <Card className="w-full max-w-sm shadow-sm">
          <CardHeader>
            <CardTitle>
              <h1 className="text-xl font-semibold">Sign in</h1>
            </CardTitle>
            <CardDescription>Use the account issued by your administrator.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              {sessionExpired && !error && (
                <Alert>
                  <AlertDescription>Your session ended. Please sign in again.</AlertDescription>
                </Alert>
              )}
              {error && (
                <Alert variant="destructive" role="alert">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" autoComplete="username" aria-invalid={!!formState.errors.email} {...register('email')} />
                {formState.errors.email && <p className="text-xs text-destructive">{formState.errors.email.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    aria-invalid={!!formState.errors.password}
                    className="pr-11"
                    {...register('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((visible) => !visible)}
                    className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    aria-pressed={showPassword}
                    aria-controls="password"
                  >
                    {showPassword ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}
                  </button>
                </div>
                {formState.errors.password && <p className="text-xs text-destructive">{formState.errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full" disabled={formState.isSubmitting}>
                {formState.isSubmitting && <Spinner />} Sign in
              </Button>
              <Button type="button" variant="link" className="w-full text-muted-foreground" onClick={() => setResetOpen(true)}>
                <KeyRound /> Forgot password?
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
      <PasswordResetDialog open={resetOpen} onOpenChange={setResetOpen} />
    </div>
  )
}
