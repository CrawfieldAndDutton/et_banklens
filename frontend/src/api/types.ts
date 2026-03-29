export type MeResult = {
  user_id: number
  email: string
  enterprise_id: number
  role: string
}

export type DashboardStats = {
  total_customers: number
  customers_with_monitoring_consent: number
  customers_with_loan_snapshot: number
  risky_customers_signal_based: number
  total_compiled_signals: number
  signals_by_severity: Record<string, number>
  completed_bsi_runs_last_30_days: number
  filters_applied: { year: number | null; month: number | null; loan_type: string | null }
  recovery_rate: number
  note?: string
  latest_signals_preview?: SignalItem[]
}

export type SignalItem = {
  signal_id: number
  customer_id: number
  run_id?: number
  signal_type: string
  severity: string
  narrative: string
  created_at: string
}

export type MonitoredCustomer = {
  customer_id: number
  external_ref: string
  display_name: string
  phone_masked: string
  pan_last4: string
  loan_type: string
  consent_monitoring: boolean
  last_bsi_status: string | null
  has_loan_snapshot: boolean
}

export type CustomerDetail = {
  customer_id: number
  external_ref: string
  display_name: string
  phone_masked: string
  email?: string | null
  pan_last4: string
  loan_type: string
  consent_monitoring: boolean
  consent_recorded_at: string | null
  last_bsi_status: string | null
  loan_snapshot: {
    principal_outstanding: number
    emi_amount: number
    dpd_days: number
    avg_monthly_inflow: number
    eod_negative_days_90d: number
    credit_score_delta_90d: number
    salary_proxy_delta_pct: number
  } | null
}

export type BsiRunResult = {
  run_id: number
  customer_id: number
  status: string
  correlation_id: string
  input_snapshot_json: string | null
  gen_ai_model: string | null
  gen_ai_summary: string | null
}

export type OutboundMessageRow = {
  id: number
  customer_id: number
  channel: string
  subject: string | null
  body_preview: string
  destination_masked: string
  status: string
  provider_reference: string | null
  correlation_id: string
  created_at: string
}
