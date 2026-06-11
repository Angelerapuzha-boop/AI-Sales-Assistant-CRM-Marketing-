import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatDateTime } from '@/lib/utils'
import { Flame, Thermometer, Snowflake, DollarSign, Calendar, Mail, TrendingUp } from 'lucide-react'

function StatCard({ title, value, icon: Icon, subtitle }: { title: string; value: string | number; icon: React.ElementType; subtitle?: string }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsApi.dashboard().then((r) => r.data),
  })

  if (isLoading) return <div>Loading dashboard...</div>

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Dashboard</h2>
        <p className="text-muted-foreground">Sales pipeline overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Leads" value={stats?.total_leads ?? 0} icon={TrendingUp} />
        <StatCard title="Hot Leads" value={stats?.hot_leads ?? 0} icon={Flame} />
        <StatCard title="Warm Leads" value={stats?.warm_leads ?? 0} icon={Thermometer} />
        <StatCard title="Cold Leads" value={stats?.cold_leads ?? 0} icon={Snowflake} />
        <StatCard title="Revenue Pipeline" value={formatCurrency(stats?.revenue_pipeline ?? 0)} icon={DollarSign} />
        <StatCard title="Meetings Scheduled" value={stats?.meetings_scheduled ?? 0} icon={Calendar} />
        <StatCard title="Emails Sent" value={stats?.emails_sent ?? 0} icon={Mail} subtitle={`Open: ${stats?.open_rate ?? 0}% | Reply: ${stats?.reply_rate ?? 0}%`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activities</CardTitle>
        </CardHeader>
        <CardContent>
          {stats?.recent_activities?.length ? (
            <ul className="space-y-3">
              {stats.recent_activities.map((a, i) => (
                <li key={i} className="flex justify-between items-center py-2 border-b border-border last:border-0">
                  <span className="text-sm">{a.action}</span>
                  <span className="text-xs text-muted-foreground">{formatDateTime(a.timestamp)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-sm">No recent activities</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
