export function SettingsPage() {
  return (
    <div className="max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
      <p className="text-sm text-slate-600">
        Tenant and integration settings are configured via backend environment variables (SMTP, WhatsApp, OpenAI).
        This UI is a placeholder for future admin endpoints.
      </p>
    </div>
  )
}
