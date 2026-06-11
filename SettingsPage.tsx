import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { healthApi, importApi } from '@/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'

export default function SettingsPage() {
  const [importResult, setImportResult] = useState<string>('')

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.health().then((r) => r.data),
  })

  const handleImport = async (type: 'companies' | 'contacts', file: File) => {
    const fn = type === 'companies' ? importApi.companies : importApi.contacts
    const { data } = await fn(file)
    setImportResult(`Imported ${data.imported}/${data.total_rows} rows. Errors: ${data.errors?.length ?? 0}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Settings</h2>
        <p className="text-muted-foreground">System configuration and data import</p>
      </div>

      <Card>
        <CardHeader><CardTitle>System Health</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm">Status: <span className="text-green-400 font-medium">{health?.status ?? 'checking...'}</span></p>
          {health?.services && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4">
              {Object.entries(health.services).map(([key, val]) => (
                <div key={key} className="text-xs p-2 bg-secondary rounded">
                  <span className="text-muted-foreground">{key}:</span> {String(val)}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>CSV Import</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Import Companies (CSV)</Label>
            <p className="text-xs text-muted-foreground mb-2">Columns: name, industry, website, revenue, employee_count, description, phone</p>
            <input type="file" accept=".csv" onChange={(e) => e.target.files?.[0] && handleImport('companies', e.target.files[0])} className="text-sm" />
          </div>
          <div>
            <Label>Import Contacts (CSV)</Label>
            <p className="text-xs text-muted-foreground mb-2">Columns: first_name, last_name, email, phone, title, seniority, company_id</p>
            <input type="file" accept=".csv" onChange={(e) => e.target.files?.[0] && handleImport('contacts', e.target.files[0])} className="text-sm" />
          </div>
          {importResult && <p className="text-sm text-primary">{importResult}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Integration Status</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-2 text-muted-foreground">
          <p>Groq AI, Gmail, Google Calendar, Bland AI, and Telegram are configured via environment variables.</p>
          <p>See .env.example for required configuration keys.</p>
        </CardContent>
      </Card>
    </div>
  )
}
