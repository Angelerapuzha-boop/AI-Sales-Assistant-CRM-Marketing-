import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { authApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState({ full_name: user?.full_name ?? '', phone: user?.phone ?? '' })
  const [saved, setSaved] = useState(false)

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    await authApi.updateMe(form)
    await refreshUser()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h2 className="text-3xl font-bold">Profile</h2>
        <p className="text-muted-foreground">Manage your account</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Account Details</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div><Label>Email</Label><Input value={user?.email ?? ''} disabled /></div>
            <div><Label>Role</Label><Input value={user?.role ?? ''} disabled /></div>
            <div><Label>Full Name</Label><Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
            <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
            <Button type="submit">Save Changes</Button>
            {saved && <p className="text-sm text-green-400">Profile updated!</p>}
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
