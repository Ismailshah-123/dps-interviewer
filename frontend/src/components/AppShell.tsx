import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, NavLink, Outlet, useLocation } from 'react-router'
import { ClipboardCheck, FileClock, GraduationCap, LayoutDashboard, LogOut, Menu, Mic, ScrollText, Settings, ShieldCheck, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useAuth } from '@/features/auth/AuthProvider'
import { api } from '@/lib/api'
import { ROLE_LABEL } from '@/lib/status'
import type { Role } from '@/lib/types'
import { cn } from '@/lib/utils'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
  roles: Role[]
}

// Navigation is a convenience only; every route and API call is authorized by the backend.
export const NAV: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['administrator', 'interviewer', 'reviewer', 'principal'] },
  { to: '/candidates', label: 'Candidates', icon: GraduationCap, roles: ['administrator', 'interviewer', 'reviewer', 'principal'] },
  { to: '/interviews', label: 'Interviews', icon: Mic, roles: ['administrator', 'interviewer'] },
  { to: '/reviews', label: 'Review queue', icon: ClipboardCheck, roles: ['administrator', 'reviewer', 'principal'] },
  { to: '/admin/users', label: 'Staff accounts', icon: Users, roles: ['administrator'] },
  { to: '/admin/templates', label: 'Templates', icon: ScrollText, roles: ['administrator'] },
  { to: '/admin/jobs', label: 'Processing jobs', icon: FileClock, roles: ['administrator'] },
  { to: '/admin/audit', label: 'Audit log', icon: ShieldCheck, roles: ['administrator'] },
  { to: '/admin/system', label: 'System', icon: Settings, roles: ['administrator'] },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, signOut } = useAuth()
  const items = NAV.filter((item) => user && item.roles.includes(user.role))
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <Link to="/dashboard" className="flex items-center gap-3 px-5 py-5" onClick={onNavigate}>
        <div className="flex size-9 items-center justify-center rounded-md bg-white/10 text-sm font-semibold">DPS</div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">Interview Documentation</div>
          <div className="text-xs text-sidebar-muted">Dawood Public School</div>
        </div>
      </Link>
      <nav className="flex-1 space-y-0.5 px-3" aria-label="Main navigation">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                isActive ? 'bg-sidebar-accent font-medium text-white' : 'text-sidebar-muted hover:bg-sidebar-accent/60 hover:text-white',
              )
            }
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-4">
        <div className="mb-3 min-w-0">
          <div className="truncate text-sm font-medium">{user?.full_name}</div>
          <div className="truncate text-xs text-sidebar-muted">{user && ROLE_LABEL[user.role]}</div>
        </div>
        <Button variant="ghost" size="sm" className="w-full justify-start text-sidebar-muted hover:bg-sidebar-accent hover:text-white" onClick={() => void signOut()}>
          <LogOut /> Sign out
        </Button>
      </div>
    </div>
  )
}

export function AppShell() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const crumbs = location.pathname.split('/').filter(Boolean)
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: Infinity })
  const external = meta.data?.external_ai ?? []
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[256px_1fr]">
      <aside className="sticky top-0 hidden h-screen lg:block">
        <SidebarContent />
      </aside>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-64 border-0 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarContent onNavigate={() => setOpen(false)} />
        </SheetContent>
      </Sheet>
      <div className="min-w-0">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b bg-background/90 px-4 backdrop-blur lg:px-8">
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setOpen(true)}>
            <Menu />
          </Button>
          <nav aria-label="Breadcrumb" className="text-sm text-muted-foreground">
            <ol className="flex items-center gap-1.5">
              {crumbs.map((c, i) => (
                <li key={i} className="flex items-center gap-1.5">
                  {i > 0 && <span aria-hidden>/</span>}
                  <span className={cn('capitalize', i === crumbs.length - 1 && 'text-foreground')}>{/^[0-9a-f-]{36}$/.test(c) ? 'Detail' : c.replace(/-/g, ' ')}</span>
                </li>
              ))}
            </ol>
          </nav>
          {external.length > 0 ? (
            <div role="status" className="ml-auto rounded-md border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-900">
              Cloud AI on ({external.join(', ')}): transcript text leaves this computer. Synthetic interviews only.
            </div>
          ) : (
            <div className="ml-auto text-xs text-muted-foreground">Demo environment · synthetic data only</div>
          )}
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
