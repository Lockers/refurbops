import { FormEvent, useState } from "react"
import { bootstrapSystem } from "../services/setupApi"
import { SetupBootstrapRequest } from "../types/setup"

interface Props {
  onComplete: () => void
}

export default function SetupPage({ onComplete }: Props) {
  const [form, setForm] = useState<SetupBootstrapRequest>({
    business: {
      _id: "biz_001",
      name: "",
      vat_registered: true,
      vat_scheme: "margin",
      vat_period: "quarterly",
      vat_period_start: "2026-01-01T00:00:00Z",
      backmarket: {
        enabled: true,
        api_key: "",
        accept_language: "en-gb",
        company_name: "",
        integration_name: "RefurbOps",
        contact_email: "",
        proxy_url: "",
      },
    },
    user: {
      _id: "usr_001",
      name: "",
      email: "",
      role: "business_admin",
    },
  })

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string>("")
  const [success, setSuccess] = useState<string>("")

  function updateBusinessField<K extends keyof SetupBootstrapRequest["business"]>(
    key: K,
    value: SetupBootstrapRequest["business"][K]
  ) {
    setForm((prev) => ({
      ...prev,
      business: {
        ...prev.business,
        [key]: value,
      },
    }))
  }

  function updateBackMarketField<
    K extends keyof SetupBootstrapRequest["business"]["backmarket"]
  >(
    key: K,
    value: SetupBootstrapRequest["business"]["backmarket"][K]
  ) {
    setForm((prev) => ({
      ...prev,
      business: {
        ...prev.business,
        backmarket: {
          ...prev.business.backmarket,
          [key]: value,
        },
      },
    }))
  }

  function updateUserField<K extends keyof SetupBootstrapRequest["user"]>(
    key: K,
    value: SetupBootstrapRequest["user"][K]
  ) {
    setForm((prev) => ({
      ...prev,
      user: {
        ...prev.user,
        [key]: value,
      },
    }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")

    try {
      await bootstrapSystem(form)
      setSuccess("Setup completed successfully.")
      onComplete()
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Setup failed.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={containerStyle}>
      <h1>RefurbOps Setup</h1>
      <p>Create the first business and admin user.</p>

      <form onSubmit={handleSubmit} style={formStyle}>
        <section style={sectionStyle}>
          <h2>Business</h2>

          <label style={labelStyle}>
            Business ID
            <input
              value={form.business._id}
              onChange={(e) => updateBusinessField("_id", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Business Name
            <input
              value={form.business.name}
              onChange={(e) => updateBusinessField("name", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Scheme
            <input
              value={form.business.vat_scheme}
              onChange={(e) => updateBusinessField("vat_scheme", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Period
            <input
              value={form.business.vat_period}
              onChange={(e) => updateBusinessField("vat_period", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Period Start
            <input
              value={form.business.vat_period_start}
              onChange={(e) => updateBusinessField("vat_period_start", e.target.value)}
              style={inputStyle}
            />
          </label>
        </section>

        <section style={sectionStyle}>
          <h2>Back Market</h2>

          <label style={labelStyle}>
            API Key
            <input
              value={form.business.backmarket.api_key}
              onChange={(e) => updateBackMarketField("api_key", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Accept Language
            <input
              value={form.business.backmarket.accept_language}
              onChange={(e) => updateBackMarketField("accept_language", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Company Name
            <input
              value={form.business.backmarket.company_name}
              onChange={(e) => updateBackMarketField("company_name", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Integration Name
            <input
              value={form.business.backmarket.integration_name}
              onChange={(e) => updateBackMarketField("integration_name", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Contact Email
            <input
              value={form.business.backmarket.contact_email}
              onChange={(e) => updateBackMarketField("contact_email", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Proxy URL
            <input
              value={form.business.backmarket.proxy_url}
              onChange={(e) => updateBackMarketField("proxy_url", e.target.value)}
              style={inputStyle}
            />
          </label>
        </section>

        <section style={sectionStyle}>
          <h2>First User</h2>

          <label style={labelStyle}>
            User ID
            <input
              value={form.user._id}
              onChange={(e) => updateUserField("_id", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Name
            <input
              value={form.user.name}
              onChange={(e) => updateUserField("name", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Email
            <input
              value={form.user.email}
              onChange={(e) => updateUserField("email", e.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Role
            <input
              value={form.user.role}
              onChange={(e) => updateUserField("role", e.target.value)}
              style={inputStyle}
            />
          </label>
        </section>

        {error ? <div style={errorStyle}>{error}</div> : null}
        {success ? <div style={successStyle}>{success}</div> : null}

        <button type="submit" disabled={submitting} style={buttonStyle}>
          {submitting ? "Saving..." : "Create Business and User"}
        </button>
      </form>
    </div>
  )
}

const containerStyle: React.CSSProperties = {
  maxWidth: 900,
  margin: "40px auto",
  padding: 24,
}

const formStyle: React.CSSProperties = {
  display: "grid",
  gap: 24,
}

const sectionStyle: React.CSSProperties = {
  padding: 20,
  border: "1px solid #ddd",
  borderRadius: 12,
  background: "#fff",
  display: "grid",
  gap: 12,
}

const labelStyle: React.CSSProperties = {
  display: "grid",
  gap: 6,
  fontWeight: 500,
}

const inputStyle: React.CSSProperties = {
  padding: 10,
  borderRadius: 8,
  border: "1px solid #ccc",
}

const buttonStyle: React.CSSProperties = {
  padding: "12px 16px",
  borderRadius: 10,
  border: "none",
  background: "#111827",
  color: "#fff",
  cursor: "pointer",
}

const errorStyle: React.CSSProperties = {
  padding: 12,
  borderRadius: 8,
  background: "#fee2e2",
  color: "#991b1b",
}

const successStyle: React.CSSProperties = {
  padding: 12,
  borderRadius: 8,
  background: "#dcfce7",
  color: "#166534",
}