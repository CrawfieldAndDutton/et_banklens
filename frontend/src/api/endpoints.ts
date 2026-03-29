import { apiFetch, apiSuccess, type ApiSuccess } from './client'
import type {
  BsiRunResult,
  CustomerDetail,
  DashboardStats,
  MeResult,
  MonitoredCustomer,
  OutboundMessageRow,
  SignalItem,
} from './types'

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  return apiFetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function fetchMe(): Promise<MeResult> {
  return apiSuccess<MeResult>('/api/v1/dashboard/me')
}

export async function fetchDashboard(): Promise<DashboardStats> {
  return apiSuccess<DashboardStats>('/api/v1/dashboard/dashboard_info')
}

export async function fetchMonitoredCustomers(page = 1, size = 50): Promise<{
  page: number
  size: number
  total: number
  items: MonitoredCustomer[]
}> {
  return apiSuccess(`/api/v1/customers/monitored?page=${page}&size=${size}`)
}

export async function fetchCustomer(id: number): Promise<CustomerDetail> {
  return apiSuccess<CustomerDetail>(`/api/v1/customers/${id}`)
}

export async function triggerBsi(customerId: number): Promise<BsiRunResult> {
  const res = await apiFetch<ApiSuccess<BsiRunResult>>(`/api/v1/bsi/customers/${customerId}/runs`, {
    method: 'POST',
  })
  return res.result
}

export async function fetchSignalsForCustomer(customerId: number): Promise<{
  customer_id: number
  count: number
  items: SignalItem[]
}> {
  return apiSuccess(`/api/v1/signals/customers/${customerId}`)
}

export async function fetchLatestSignals(page = 1, size = 50): Promise<{ items: SignalItem[] }> {
  return apiSuccess(`/api/v1/signals/latest?page=${page}&size=${size}`)
}

export async function sendOmnichannel(body: {
  customer_id: number
  channel: 'whatsapp' | 'email'
  subject?: string
  body: string
}): Promise<unknown> {
  const res = await apiFetch<ApiSuccess<unknown>>('/api/v1/omnichannel/messages', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return res.result
}

export async function fetchOmnichannelMessages(page = 1, size = 50): Promise<{
  items: OutboundMessageRow[]
}> {
  return apiSuccess(`/api/v1/omnichannel/messages?page=${page}&size=${size}`)
}
