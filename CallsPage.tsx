import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { callsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Phone, Plus } from 'lucide-react'

export default function CallsPage() {
  const [showForm, setShowForm] = useState(false)
  const [phone, setPhone] = useState('')
  const queryClient = useQueryClient()

  const { data: calls, isLoading } = useQuery({
    queryKey: ['calls'],
    queryFn: () => callsApi.list().then((r) => r.data),
  })

  const { data: analytics } = useQuery({
    queryKey: ['call-analytics'],
    queryFn: () => callsApi.analytics().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => callsApi.create({ phone_number: phone }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['calls'] }); setShowForm(false); setPhone('') },
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">AI Calls</h2>
          <p className="text-muted-foreground">Bland AI outbound calling</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}><Plus className="h-4 w-4 mr-2" /> New Call</Button>
      </div>

      {analytics && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Total</p><p className="text-2xl font-bold">{analytics.total}</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Completed</p><p className="text-2xl font-bold">{analytics.completed}</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Failed</p><p className="text-2xl font-bold">{analytics.failed}</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Avg Duration</p><p className="text-2xl font-bold">{analytics.avg_duration}s</p></CardContent></Card>
        </div>
      )}

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Initiate AI Call</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><Label>Phone Number</Label><Input placeholder="+1234567890" value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
            <Button onClick={() => createMutation.mutate()} disabled={!phone || createMutation.isPending}>
              <Phone className="h-4 w-4 mr-2" /> Start Call
            </Button>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="space-y-3">
          {calls?.items.map((call: { id: string; phone_number: string; status: string; summary?: string; transcript?: string }) => (
            <Card key={call.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between">
                  <div>
                    <p className="font-medium">{call.phone_number}</p>
                    <p className="text-sm text-muted-foreground">{call.status}</p>
                  </div>
                  <Phone className="h-5 w-5 text-muted-foreground" />
                </div>
                {call.summary && <p className="text-sm mt-3 p-3 bg-secondary rounded">{call.summary}</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
