import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { formatDateTime } from '@/lib/utils'
import { Plus, Trash2 } from 'lucide-react'

export default function MeetingsPage() {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', start_time: '', end_time: '', location: '' })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: () => meetingsApi.list().then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: meetingsApi.create,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['meetings'] }); setShowForm(false) },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => meetingsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['meetings'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Meetings</h2>
          <p className="text-muted-foreground">Schedule and manage meetings</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}><Plus className="h-4 w-4 mr-2" /> Schedule Meeting</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>New Meeting</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2"><Label>Title *</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
              <div><Label>Start *</Label><Input type="datetime-local" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} required /></div>
              <div><Label>End *</Label><Input type="datetime-local" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} required /></div>
              <div><Label>Location</Label><Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /></div>
              <div className="md:col-span-2"><Label>Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              <div><Button type="submit">Schedule</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="space-y-3">
          {data?.items.map((meeting) => (
            <Card key={meeting.id}>
              <CardContent className="pt-6 flex justify-between items-start">
                <div>
                  <p className="font-medium">{meeting.title}</p>
                  <p className="text-sm text-muted-foreground">{formatDateTime(meeting.start_time)} - {formatDateTime(meeting.end_time)}</p>
                  <p className="text-xs text-muted-foreground mt-1">{meeting.status}</p>
                  {meeting.meeting_link && <a href={meeting.meeting_link} className="text-xs text-primary hover:underline" target="_blank" rel="noreferrer">Calendar Link</a>}
                </div>
                <Button size="icon" variant="ghost" onClick={() => deleteMutation.mutate(meeting.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
