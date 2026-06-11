import api from '@/lib/api'

export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  phone?: string
  avatar_url?: string
  created_at: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Company {
  id: string
  owner_id: string
  name: string
  industry?: string
  website?: string
  revenue?: number
  employee_count?: number
  description?: string
  ai_summary?: string
  status: string
  created_at: string
}

export interface Contact {
  id: string
  owner_id: string
  company_id?: string
  first_name: string
  last_name: string
  email?: string
  phone?: string
  title?: string
  seniority?: string
}

export interface LeadScore {
  id: string
  company_id: string
  contact_id?: string
  score: number
  category: 'cold' | 'warm' | 'hot'
  calculated_at: string
}

export interface Email {
  id: string
  subject: string
  body: string
  email_type: string
  status: string
  sent_at?: string
  created_at: string
}

export interface Meeting {
  id: string
  title: string
  description?: string
  start_time: string
  end_time: string
  status: string
  meeting_link?: string
}

export interface DashboardStats {
  total_leads: number
  hot_leads: number
  warm_leads: number
  cold_leads: number
  revenue_pipeline: number
  meetings_scheduled: number
  emails_sent: number
  open_rate: number
  reply_rate: number
  recent_activities: { type: string; action: string; timestamp: string }[]
}

export const authApi = {
  login: (email: string, password: string) => api.post('/auth/login', { email, password }),
  register: (data: { email: string; password: string; full_name: string }) => api.post('/auth/register', data),
  me: () => api.get<User>('/auth/me'),
  updateMe: (data: Partial<User>) => api.put('/auth/me', data),
}

export const companiesApi = {
  list: (params?: Record<string, unknown>) => api.get<Paginated<Company>>('/companies', { params }),
  get: (id: string) => api.get<Company>(`/companies/${id}`),
  create: (data: Partial<Company>) => api.post<Company>('/companies', data),
  update: (id: string, data: Partial<Company>) => api.put<Company>(`/companies/${id}`, data),
  delete: (id: string) => api.delete(`/companies/${id}`),
  aiSummary: (id: string) => api.post(`/companies/${id}/ai-summary`),
  buyingSignals: (id: string) => api.post(`/companies/${id}/buying-signals`),
}

export const contactsApi = {
  list: (params?: Record<string, unknown>) => api.get<Paginated<Contact>>('/contacts', { params }),
  create: (data: Partial<Contact>) => api.post<Contact>('/contacts', data),
  update: (id: string, data: Partial<Contact>) => api.put<Contact>(`/contacts/${id}`, data),
  delete: (id: string) => api.delete(`/contacts/${id}`),
}

export const leadsApi = {
  list: (params?: Record<string, unknown>) => api.get<Paginated<LeadScore>>('/leads', { params }),
  top: (limit = 10) => api.get<LeadScore[]>('/leads/top', { params: { limit } }),
  recalculate: (companyId: string) => api.post(`/leads/recalculate/${companyId}`),
  insights: (companyId: string) => api.post('/leads/insights', { company_id: companyId }),
}

export const emailsApi = {
  list: (params?: Record<string, unknown>) => api.get<Paginated<Email>>('/emails', { params }),
  create: (data: { subject: string; body: string; company_id?: string; contact_id?: string; email_type?: string }) =>
    api.post<Email>('/emails', data),
  generate: (data: { company_id: string; contact_id?: string; email_type?: string }) =>
    api.post<{ subject: string; body: string; provider: string }>('/emails/generate', data),
  send: (id: string) => api.post<Email>(`/emails/${id}/send`),
  analytics: () => api.get('/emails/analytics/summary'),
}

export const meetingsApi = {
  list: (params?: Record<string, unknown>) => api.get<Paginated<Meeting>>('/meetings', { params }),
  create: (data: Partial<Meeting>) => api.post<Meeting>('/meetings', data),
  update: (id: string, data: Partial<Meeting>) => api.put<Meeting>(`/meetings/${id}`, data),
  delete: (id: string) => api.delete(`/meetings/${id}`),
  prepNotes: (id: string) => api.post(`/meetings/${id}/prep-notes`),
}

export const analyticsApi = {
  dashboard: () => api.get<DashboardStats>('/analytics/dashboard'),
  analytics: () => api.get('/analytics'),
}

export const notificationsApi = {
  list: (params?: Record<string, unknown>) => api.get('/notifications', { params }),
  markRead: (id: string) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
}

export const callsApi = {
  list: (params?: Record<string, unknown>) => api.get('/calls', { params }),
  create: (data: { phone_number: string; company_id?: string; contact_id?: string }) =>
    api.post('/calls', data),
  get: (id: string) => api.get(`/calls/${id}`),
  analytics: () => api.get('/calls/analytics/summary'),
}

export const importApi = {
  companies: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/import/companies', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  contacts: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/import/contacts', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export const healthApi = {
  health: () => api.get('/health'),
  status: () => api.get('/status'),
  info: () => api.get('/info'),
}
