import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Outlet, RouterProvider, createBrowserRouter } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppShell } from '@/components/AppShell'
import { AuditPage, JobsPage, SystemPage, TemplatesPage } from '@/features/admin/OperationsPages'
import { UsersPage } from '@/features/admin/UsersPage'
import { StoragePage } from '@/features/admin/StoragePage'
import { AuthProvider } from '@/features/auth/AuthProvider'
import { LoginPage } from '@/features/auth/LoginPage'
import { CandidateDetailPage } from '@/features/candidates/CandidateDetailPage'
import { CandidatesPage } from '@/features/candidates/CandidatesPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { InterviewListPage } from '@/features/interviews/InterviewListPage'
import { InterviewWorkspace } from '@/features/interviews/InterviewWorkspace'
import { ApiError } from '@/lib/api'
import { REVIEW_QUEUE_STATUSES } from '@/lib/status'
import { NotFoundPage, RequireAuth, RequireRole, RouteErrorPage } from '@/routes/system'

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 10_000,
        refetchOnWindowFocus: false,
        // Never retry authorization or not-found answers; they will not change on retry.
        retry: (count, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && count < 2,
      },
    },
  })
}

function Root() {
  return <Outlet />
}

export const routes = [
  {
    element: <Root />,
    errorElement: <RouteErrorPage />,
    children: [
      { path: '/login', element: <LoginPage /> },
      {
        element: <RequireAuth />,
        children: [
          {
            element: <AppShell />,
            errorElement: <RouteErrorPage />,
            children: [
              { index: true, element: <Navigate to="/dashboard" replace /> },
              { path: '/dashboard', element: <DashboardPage /> },
              { path: '/candidates', element: <CandidatesPage /> },
              { path: '/candidates/:id', element: <CandidateDetailPage /> },
              {
                path: '/interviews',
                element: (
                  <RequireRole roles={['administrator', 'interviewer']}>
                    <InterviewListPage title="Interviews" description="Interviews assigned to you, with their recording and review status." />
                  </RequireRole>
                ),
              },
              { path: '/interviews/:id', element: <InterviewWorkspace /> },
              {
                path: '/reviews',
                element: (
                  <RequireRole roles={['administrator', 'reviewer', 'principal']}>
                    <InterviewListPage title="Review queue" description="Interviews submitted by interviewers for principal review." statuses={[...REVIEW_QUEUE_STATUSES, 'finalized']} />
                  </RequireRole>
                ),
              },
              { path: '/admin/users', element: <RequireRole roles={['administrator']}><UsersPage /></RequireRole> },
              { path: '/admin/storage', element: <RequireRole roles={['administrator']}><StoragePage /></RequireRole> },
              { path: '/admin/templates', element: <RequireRole roles={['administrator']}><TemplatesPage /></RequireRole> },
              { path: '/admin/jobs', element: <RequireRole roles={['administrator']}><JobsPage /></RequireRole> },
              { path: '/admin/audit', element: <RequireRole roles={['administrator']}><AuditPage /></RequireRole> },
              { path: '/admin/system', element: <RequireRole roles={['administrator']}><SystemPage /></RequireRole> },
              { path: '*', element: <NotFoundPage /> },
            ],
          },
        ],
      },
    ],
  },
]

const router = createBrowserRouter(routes)
const queryClient = createQueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <RouterProvider router={router} />
          <Toaster richColors position="top-right" />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
