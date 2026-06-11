import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contactsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, Search, Trash2 } from 'lucide-react'

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', title: '', seniority: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list({ search: search || undefined }).then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: contactsApi.create,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['contacts'] }); setShowForm(false) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contacts'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Contacts</h2>
          <p className="text-muted-foreground">Manage your sales contacts</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}><Plus className="h-4 w-4 mr-2" /> Add Contact</Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input className="pl-10" placeholder="Search contacts..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>New Contact</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="grid gap-4 md:grid-cols-2">
              <div><Label>First Name *</Label><Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></div>
              <div><Label>Last Name *</Label><Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></div>
              <div><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
              <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
              <div><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
              <div><Label>Seniority</Label><Input placeholder="c-level, vp, director..." value={form.seniority} onChange={(e) => setForm({ ...form, seniority: e.target.value })} /></div>
              <div><Button type="submit">Create</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="p-3 text-left">Name</th>
                <th className="p-3 text-left">Email</th>
                <th className="p-3 text-left">Title</th>
                <th className="p-3 text-left">Seniority</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c) => (
                <tr key={c.id} className="border-b">
                  <td className="p-3">{c.first_name} {c.last_name}</td>
                  <td className="p-3">{c.email || '-'}</td>
                  <td className="p-3">{c.title || '-'}</td>
                  <td className="p-3">{c.seniority || '-'}</td>
                  <td className="p-3 text-right">
                    <Button size="icon" variant="ghost" onClick={() => deleteMutation.mutate(c.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
