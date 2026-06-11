import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const COLORS = ['#ef4444', '#eab308', '#3b82f6']

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => analyticsApi.analytics().then((r) => r.data),
  })

  if (isLoading) return <div>Loading analytics...</div>

  const leadData = data ? [
    { name: 'Hot', value: data.lead_distribution.hot },
    { name: 'Warm', value: data.lead_distribution.warm },
    { name: 'Cold', value: data.lead_distribution.cold },
  ] : []

  const funnelData = data ? [
    { stage: 'Leads', count: data.conversion_funnel.leads },
    { stage: 'Contacted', count: data.conversion_funnel.contacted },
    { stage: 'Meetings', count: data.conversion_funnel.meetings },
    { stage: 'Qualified', count: data.conversion_funnel.qualified },
  ] : []

  const revenueData = data ? Object.entries(data.revenue_pipeline).map(([name, value]) => ({ name, value })) : []

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Analytics</h2>
        <p className="text-muted-foreground">Performance insights and metrics</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Lead Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={leadData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {leadData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Conversion Funnel</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={funnelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Email Performance</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div><p className="text-sm text-muted-foreground">Sent</p><p className="text-2xl font-bold">{data?.email_performance.sent ?? 0}</p></div>
              <div><p className="text-sm text-muted-foreground">Opened</p><p className="text-2xl font-bold">{data?.email_performance.opened ?? 0}</p></div>
              <div><p className="text-sm text-muted-foreground">Replied</p><p className="text-2xl font-bold">{data?.email_performance.replied ?? 0}</p></div>
              <div><p className="text-sm text-muted-foreground">Failed</p><p className="text-2xl font-bold">{data?.email_performance.failed ?? 0}</p></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Meeting Analytics</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div><p className="text-sm text-muted-foreground">Scheduled</p><p className="text-2xl font-bold">{data?.meeting_analytics.scheduled ?? 0}</p></div>
              <div><p className="text-sm text-muted-foreground">Completed</p><p className="text-2xl font-bold">{data?.meeting_analytics.completed ?? 0}</p></div>
              <div><p className="text-sm text-muted-foreground">Cancelled</p><p className="text-2xl font-bold">{data?.meeting_analytics.cancelled ?? 0}</p></div>
            </div>
          </CardContent>
        </Card>

        {revenueData.length > 0 && (
          <Card className="md:col-span-2">
            <CardHeader><CardTitle>Revenue Pipeline by Industry</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#22c55e" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
