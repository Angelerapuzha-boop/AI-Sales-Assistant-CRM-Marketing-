import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companiesApi, Company } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { formatCurrency } from '@/lib/utils'
import { Plus, Search, Sparkles, Trash2 } from 'lucide-react'

export default function CompaniesPage() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', industry: '', revenue: '', employee_count: '', description: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['companies', search],
    queryFn: () => companiesApi.list({ search: search || undefined }).then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Company>) => companiesApi.create(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['companies'] }); setShowForm(false); setForm({ name: '', industry: '', revenue: '', employee_count: '', description: '' }) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  })

  const aiSummaryMutation = useMutation({
    mutationFn: (id: string) => companiesApi.aiSummary(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      name: form.name,
      industry: form.industry || undefined,
      revenue: form.revenue ? parseFloat(form.revenue) : undefined,
      employee_count: form.employee_count ? parseInt(form.employee_count) : undefined,
      description: form.description || undefined,
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Companies</h2>
          <p className="text-muted-foreground">Manage your company accounts</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}><Plus className="h-4 w-4 mr-2" /> Add Company</Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input className="pl-10" placeholder="Search companies..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>New Company</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
              <div><Label>Name *</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
              <div><Label>Industry</Label><Input value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} /></div>
              <div><Label>Revenue</Label><Input type="number" value={form.revenue} onChange={(e) => setForm({ ...form, revenue: e.target.value })} /></div>
              <div><Label>Employees</Label><Input type="number" value={form.employee_count} onChange={(e) => setForm({ ...form, employee_count: e.target.value })} /></div>
              <div className="md:col-span-2"><Label>Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              <div><Button type="submit" disabled={createMutation.isPending}>Create</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((company) => (
            <Card key={company.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{company.name}</CardTitle>
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" onClick={() => aiSummaryMutation.mutate(company.id)} title="AI Summary">
                      <Sparkles className="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="ghost" onClick={() => deleteMutation.mutate(company.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p><span className="text-muted-foreground">Industry:</span> {company.industry || 'N/A'}</p>
                <p><span className="text-muted-foreground">Revenue:</span> {company.revenue ? formatCurrency(company.revenue) : 'N/A'}</p>
                <p><span className="text-muted-foreground">Employees:</span> {company.employee_count ?? 'N/A'}</p>
                {company.ai_summary && (
                  <div className="mt-3 p-3 bg-secondary rounded-md text-xs">
                    <p className="font-medium mb-1">AI Summary</p>
                    <p className="line-clamp-4">{company.ai_summary}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
