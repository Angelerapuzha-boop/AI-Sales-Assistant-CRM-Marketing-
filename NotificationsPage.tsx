import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatDateTime } from '@/lib/utils'
import { CheckCheck } from 'lucide-react'

export default function NotificationsPage() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list().then((r) => r.data),
  })

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">Notifications</h2>
          <p className="text-muted-foreground">Stay updated on sales activities</p>
        </div>
        <Button variant="outline" onClick={() => markAllMutation.mutate()}>
          <CheckCheck className="h-4 w-4 mr-2" /> Mark All Read
        </Button>
      </div>

      {isLoading ? <p>Loading...</p> : (
        <div className="space-y-3">
          {data?.items.map((n: { id: string; title: string; message: string; is_read: boolean; created_at: string }) => (
            <Card key={n.id} className={n.is_read ? 'opacity-60' : ''}>
              <CardContent className="pt-6 flex justify-between items-start">
                <div>
                  <p className="font-medium">{n.title}</p>
                  <p className="text-sm text-muted-foreground mt-1">{n.message}</p>
                  <p className="text-xs text-muted-foreground mt-2">{formatDateTime(n.created_at)}</p>
                </div>
                {!n.is_read && (
                  <Button size="sm" variant="ghost" onClick={() => markReadMutation.mutate(n.id)}>Mark Read</Button>
                )}
              </CardContent>
            </Card>
          ))}
          {!data?.items.length && <p className="text-muted-foreground">No notifications</p>}
        </div>
      )}
    </div>
  )
}
