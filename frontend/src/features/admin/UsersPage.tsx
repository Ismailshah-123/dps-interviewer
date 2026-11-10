import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { UserPlus } from 'lucide-react'
import { toast } from 'sonner'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ErrorState, LoadingRows, PageHeader, Pagination, Spinner, ToneBadge } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { api, errorMessage } from '@/lib/api'
import { ROLE_LABEL, formatDateTime } from '@/lib/status'
import type { Role, User } from '@/lib/types'

const ROLES: Role[] = ['interviewer', 'principal', 'reviewer', 'administrator']

export const staffSchema = z.object({
  full_name: z.string().trim().min(1, 'Name is required').max(200),
  email: z.string().trim().email('Enter a valid email address'),
  password: z
    .string()
    .min(12, 'At least 12 characters')
    .regex(/[A-Z]/, 'Include an upper-case letter')
    .regex(/[a-z]/, 'Include a lower-case letter')
    .regex(/[0-9]/, 'Include a number'),
  role: z.enum(['administrator', 'interviewer', 'reviewer', 'principal']),
})
type StaffValues = z.infer<typeof staffSchema>

function CreateStaffDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const qc = useQueryClient()
  const form = useForm<StaffValues>({ resolver: zodResolver(staffSchema), defaultValues: { role: 'interviewer', full_name: '', email: '', password: '' } })
  const create = useMutation({
    mutationFn: api.createUser,
    onSuccess: (u) => {
      toast.success(`Account created for ${u.full_name}`)
      qc.invalidateQueries({ queryKey: ['users'] })
      form.reset()
      onOpenChange(false)
    },
  })
  const e = form.formState.errors
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create staff account</DialogTitle>
          <DialogDescription>There is no self-registration. Share the initial password securely and ask the person to change it.</DialogDescription>
        </DialogHeader>
        <form id="staff-form" className="space-y-4" onSubmit={form.handleSubmit((v) => create.mutate(v))} noValidate>
          {create.isError && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage(create.error)}</AlertDescription>
            </Alert>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" {...form.register('full_name')} />
            {e.full_name && <p className="text-xs text-destructive">{e.full_name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="staff-email">Email</Label>
            <Input id="staff-email" type="email" {...form.register('email')} />
            {e.email && <p className="text-xs text-destructive">{e.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="staff-password">Initial password</Label>
            <Input id="staff-password" type="password" autoComplete="new-password" {...form.register('password')} />
            {e.password && <p className="text-xs text-destructive">{e.password.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select value={form.watch('role')} onValueChange={(v) => form.setValue('role', v as Role)}>
              <SelectTrigger className="w-full" aria-label="Role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROLES.map((r) => (
                  <SelectItem key={r} value={r}>
                    {ROLE_LABEL[r]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="submit" form="staff-form" disabled={create.isPending}>
            {create.isPending && <Spinner />} Create account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function UserRow({ u, self }: { u: User; self: boolean }) {
  const qc = useQueryClient()
  const update = useMutation({
    mutationFn: (body: Partial<Pick<User, 'role' | 'is_active'>>) => api.updateUser(u.id, body),
    onSuccess: () => (toast.success('Account updated'), qc.invalidateQueries({ queryKey: ['users'] })),
    onError: (e) => toast.error(errorMessage(e)),
  })
  return (
    <TableRow>
      <TableCell>
        <div className="font-medium">{u.full_name}</div>
        <div className="text-xs text-muted-foreground">{u.email}</div>
      </TableCell>
      <TableCell>
        <Select value={u.role} onValueChange={(v) => update.mutate({ role: v as Role })} disabled={update.isPending}>
          <SelectTrigger className="w-48" aria-label={`Role for ${u.full_name}`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROLES.map((r) => (
              <SelectItem key={r} value={r}>
                {ROLE_LABEL[r]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableCell>
      <TableCell>{u.is_active ? <ToneBadge tone="success">Active</ToneBadge> : <ToneBadge tone="neutral">Deactivated</ToneBadge>}</TableCell>
      <TableCell className="text-muted-foreground">{formatDateTime(u.created_at)}</TableCell>
      <TableCell className="text-right">
        <Button variant="outline" size="sm" disabled={self || update.isPending} onClick={() => update.mutate({ is_active: !u.is_active })}>
          {u.is_active ? 'Deactivate' : 'Reactivate'}
        </Button>
      </TableCell>
    </TableRow>
  )
}

export function UsersPage() {
  const { user } = useAuth()
  const [skip, setSkip] = useState(0)
  const [open, setOpen] = useState(false)
  const users = useQuery({ queryKey: ['users', { skip }], queryFn: () => api.users({ skip, limit: 25 }) })
  return (
    <>
      <PageHeader
        title="Staff accounts"
        description="Create accounts, assign roles and deactivate access. Role changes and deactivation take effect on the next request."
        actions={
          <Button onClick={() => setOpen(true)}>
            <UserPlus /> New account
          </Button>
        }
      />
      <Card>
        <CardContent>
          {users.isPending ? (
            <LoadingRows />
          ) : users.isError ? (
            <ErrorState error={users.error} onRetry={() => users.refetch()} />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="sr-only">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.data.items.map((u) => (
                    <UserRow key={u.id} u={u} self={u.id === user?.id} />
                  ))}
                </TableBody>
              </Table>
              <Pagination meta={users.data.meta} onPage={setSkip} />
            </>
          )}
        </CardContent>
      </Card>
      <CreateStaffDialog open={open} onOpenChange={setOpen} />
    </>
  )
}
