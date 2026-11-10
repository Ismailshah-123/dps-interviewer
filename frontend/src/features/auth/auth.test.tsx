import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router'
import { AuthProvider } from './AuthProvider'
import { LoginPage } from './LoginPage'
import { AppShell } from '@/components/AppShell'
import { RequireAuth } from '@/routes/system'

type Handler = (url: string, init?: RequestInit) => Response

function mockFetch(handler: Handler) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => handler(url, init)))
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

function renderApp(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppShell />}>
                <Route path="/dashboard" element={<p>dashboard content</p>} />
              </Route>
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('authentication flow', () => {
  it('redirects anonymous users to the login page', async () => {
    mockFetch((url) => (url.endsWith('/auth/refresh') ? json({ detail: 'Invalid refresh token' }, 401) : json({}, 404)))
    renderApp('/dashboard')
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
  })

  it('validates the form before calling the API', async () => {
    mockFetch(() => json({ detail: 'x' }, 401))
    renderApp('/login')
    await userEvent.click(await screen.findByRole('button', { name: /^sign in$/i }))
    expect(await screen.findByText(/enter your password/i)).toBeInTheDocument()
  })

  it('toggles password visibility without submitting the form', async () => {
    mockFetch((url) => (url.endsWith('/auth/refresh') ? json({ detail: 'Invalid refresh token' }, 401) : json({}, 404)))
    renderApp('/login')
    const password = await screen.findByLabelText(/password/i)
    expect(password).toHaveAttribute('type', 'password')

    await userEvent.click(screen.getByRole('button', { name: /show password/i }))
    expect(password).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: /hide password/i })).toHaveAttribute('aria-pressed', 'true')

    await userEvent.click(screen.getByRole('button', { name: /hide password/i }))
    expect(password).toHaveAttribute('type', 'password')
  })

  it('shows a generic message on bad credentials', async () => {
    mockFetch((url) => (url.endsWith('/auth/login') ? json({ detail: 'Invalid credentials' }, 401) : json({ detail: 'no' }, 401)))
    renderApp('/login')
    await userEvent.type(await screen.findByLabelText(/email/i), 'someone@dps.example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/email or password is incorrect/i)
  })

  it.each([
    ['interviewer', ['Dashboard', 'Candidates', 'Interviews'], ['Review queue', 'Staff accounts', 'Audit log']],
    ['reviewer', ['Dashboard', 'Review queue'], ['Interviews', 'Staff accounts']],
    ['principal', ['Dashboard', 'Candidates', 'Review queue'], ['Interviews', 'Staff accounts']],
    ['administrator', ['Staff accounts', 'Audit log', 'Processing jobs', 'Review queue'], []],
  ])('shows %s navigation only for permitted areas', async (role, visible, hidden) => {
    mockFetch((url) => {
      if (url.endsWith('/auth/refresh')) return json({ access_token: 'token', refresh_token: 'r' })
      if (url.endsWith('/auth/me')) return json({ id: 'u1', email: 'x@dps.example.com', full_name: 'Synthetic User', role, is_active: true })
      return json({}, 404)
    })
    renderApp('/dashboard')
    await waitFor(() => expect(screen.getByText('dashboard content')).toBeInTheDocument())
    const nav = screen.getAllByRole('navigation', { name: /main navigation/i })[0]
    for (const label of visible) expect(nav).toHaveTextContent(label)
    for (const label of hidden) expect(nav).not.toHaveTextContent(label)
  })
})
