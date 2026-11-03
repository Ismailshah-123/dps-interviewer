import type { ReactNode } from 'react'
import { Link, Navigate, Outlet, isRouteErrorResponse, useLocation, useRouteError } from 'react-router'
import { FileQuestion, Lock, TriangleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import type { Role } from '@/lib/types'

export function RequireAuth() {
  const { status, signedOut } = useAuth()
  const location = useLocation()
  if (status === 'loading')
    return (
      <div className="flex min-h-screen items-center justify-center gap-2 text-sm text-muted-foreground">
        <Spinner /> Restoring session…
      </div>
    )
  if (status === 'anonymous') return <Navigate to="/login" replace state={signedOut ? undefined : { from: location.pathname }} />
  return <Outlet />
}

/** UX-only gate. The backend independently rejects every unauthorized request. */
export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { hasRole } = useAuth()
  return hasRole(...roles) ? <>{children}</> : <AccessDeniedPage />
}

function SystemMessage({ icon, title, body, action }: { icon: ReactNode; title: string; body: string; action?: ReactNode }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="mb-4 rounded-full bg-muted p-4 text-muted-foreground">{icon}</div>
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">{body}</p>
      <div className="mt-6">{action ?? <Button asChild><Link to="/dashboard">Back to dashboard</Link></Button>}</div>
    </div>
  )
}

export function AccessDeniedPage() {
  return <SystemMessage icon={<Lock className="size-6" />} title="Access denied" body="Your role does not permit access to this page. If you believe this is wrong, contact the system administrator." />
}

export function NotFoundPage() {
  return <SystemMessage icon={<FileQuestion className="size-6" />} title="Page not found" body="The page does not exist or the record is not available to your account." />
}

export function RouteErrorPage() {
  const error = useRouteError()
  const status = isRouteErrorResponse(error) ? error.status : undefined
  if (status === 404) return <NotFoundPage />
  return (
    <SystemMessage
      icon={<TriangleAlert className="size-6" />}
      title="Something went wrong"
      body="An unexpected error occurred while displaying this page. No data was changed by this error. Reload the page to continue."
      action={<Button onClick={() => window.location.reload()}>Reload</Button>}
    />
  )
}
