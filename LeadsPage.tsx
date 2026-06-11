import { useQuery } from '@tanstack/react-query'
import { leadsApi } from '@/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

const categoryColors = {
  hot: 'bg-red-500/20 text-red-400 border-red-500/30',
  warm: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  cold: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
}

export default function LeadsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: () => leadsApi.list().then((r) => r.data),
  })

  const { data: topLeads } = useQuery({
    queryKey: ['top-leads'],
    queryFn: () => leadsApi.top(5).then((r) => r.data),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Leads</h2>
        <p className="text-muted-foreground">Lead scoring and qualification</p>
      </div>

      {topLeads && topLeads.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Top Leads</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-4 flex-wrap">
              {topLeads.map((lead) => (
                <div key={lead.id} className={cn('px-4 py-2 rounded-lg border', categoryColors[lead.category])}>
                  Score: {lead.score}/100 ({lead.category.toUpperCase()})
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {isLoading ? <p>Loading...</p> : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((lead) => (
            <Card key={lead.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-3xl font-bold">{lead.score}</span>
                  <span className={cn('px-3 py-1 rounded-full text-xs font-medium border', categoryColors[lead.category])}>
                    {lead.category.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Calculated: {new Date(lead.calculated_at).toLocaleDateString()}</p>
              </CardContent>
            </Card>
          ))}
          {!data?.items.length && <p className="text-muted-foreground col-span-full">No leads yet. Add companies to generate lead scores.</p>}
        </div>
      )}
    </div>
  )
}
