import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emailsApi, companiesApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Send, Sparkles } from 'lucide-react'

export default function EmailsPage() {
  const [showGenerate, setShowGenerate] = useState(false)
  const [genForm, setGenForm] = useState({ company_id: '', email_type: 'cold' })
  const [draft, setDraft] = useState({ subject: '', body: '', company_id: '', contact_id: '' })
  const queryClient = useQueryClient()

  const { data: emails, isLoading } = useQuery({
    queryKey: ['emails'],
    queryFn: () => emailsApi.list().then((r) => r.data),
  })

  const { data: companies } = useQuery({
    queryKey: ['companies-list'],
    queryFn: () => companiesApi.list({ page_size: 100 }).then((r) => r.data),
  })

  const { data: analytics } = useQuery({
    queryKey: ['email-analytics'],
    queryFn: () => emailsApi.analytics().then((r) => r.data),
  })

  const generateMutation = useMutation({
    mutationFn: () => emailsApi.generate({ company_id: genForm.company_id, email_type: genForm.email_type }),
    onSuccess: ({ data }) => {
      setDraft({ ...draft, subject: data.subject, body: data.body, company_id: genForm.company_id })
      setShowGenerate(false)
    },
  })

  const createMutation = useMutation({
    mutationFn: () => emailsApi.create({ subject: draft.subject, body: draft.body, company_id: draft.company_id || undefined, email_type: genForm.email_type }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emails'] }),
  })

  const sendMutation = useMutation({
    mutationFn: (id: string) => emailsApi.send(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emails'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Emails</h2>
          <p className="text-muted-foreground">AI-powered email generation and sending</p>
        </div>
        <Button onClick={() => setShowGenerate(!showGenerate)}><Sparkles className="h-4 w-4 mr-2" /> Generate Email</Button>
      </div>

      {analytics && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Sent</p><p className="text-2xl font-bold">{analytics.sent}</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Drafts</p><p className="text-2xl font-bold">{analytics.drafts}</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Open Rate</p><p className="text-2xl font-bold">{analytics.open_rate}%</p></CardContent></Card>
          <Card><CardContent className="pt-6"><p className="text-sm text-muted-foreground">Reply Rate</p><p className="text-2xl font-bold">{analytics.reply_rate}%</p></CardContent></Card>
        </div>
      )}

      {showGenerate && (
        <Card>
          <CardHeader><CardTitle>Generate AI Email</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><Label>Company</Label>
              <select className="w-full h-10 rounded-md border border-input bg-background px-3" value={genForm.company_id} onChange={(e) => setGenForm({ ...genForm, company_id: e.target.value })}>
                <option value="">Select company</option>
                {companies?.items.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div><Label>Type</Label>
              <select className="w-full h-10 rounded-md border border-input bg-background px-3" value={genForm.email_type} onChange={(e) => setGenForm({ ...genForm, email_type: e.target.value })}>
                <option value="cold">Cold Email</option>
                <option value="follow_up">Follow-up</option>
                <option value="meeting_request">Meeting Request</option>
              </select>
            </div>
            <Button onClick={() => generateMutation.mutate()} disabled={!genForm.company_id || generateMutation.isPending}>Generate</Button>
          </CardContent>
        </Card>
      )}

      {(draft.subject || draft.body) && (
        <Card>
          <CardHeader><CardTitle>Draft</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><Label>Subject</Label><Input value={draft.subject} onChange={(e) => setDraft({ ...draft, subject: e.target.value })} /></div>
            <div><Label>Body</Label><Textarea rows={8} value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} /></div>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>Save Draft</Button>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="space-y-3">
          {emails?.items.map((email) => (
            <Card key={email.id}>
              <CardContent className="pt-6 flex justify-between items-start">
                <div>
                  <p className="font-medium">{email.subject}</p>
                  <p className="text-sm text-muted-foreground mt-1">{email.email_type} · {email.status}</p>
                </div>
                {email.status === 'draft' && (
                  <Button size="sm" onClick={() => sendMutation.mutate(email.id)} disabled={sendMutation.isPending}>
                    <Send className="h-4 w-4 mr-1" /> Send
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
