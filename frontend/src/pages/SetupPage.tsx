import type { CSSProperties, FormEvent } from "react"
import { useState } from "react"
import { bootstrapSystem } from "../services/setupApi"
import { getApiErrorMessage } from "../services/api/client"
import { SetupBootstrapRequest } from "../types/setup"

interface SetupPageProps {
  onComplete: (businessId: string) => void
}

/**
 * Render the first-time bootstrap form for the initial business and admin user.
 */
export default function SetupPage({ onComplete }: SetupPageProps) {
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
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  function updateBusinessField<K extends keyof SetupBootstrapRequest["business"]>(
    key: K,
    value: SetupBootstrapRequest["business"][K]
  ) {
    setForm((previousForm) => ({
      ...previousForm,
      business: {
        ...previousForm.business,
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
    setForm((previousForm) => ({
      ...previousForm,
      business: {
        ...previousForm.business,
        backmarket: {
          ...previousForm.business.backmarket,
          [key]: value,
        },
      },
    }))
  }

  function updateUserField<K extends keyof SetupBootstrapRequest["user"]>(
    key: K,
    value: SetupBootstrapRequest["user"][K]
  ) {
    setForm((previousForm) => ({
      ...previousForm,
      user: {
        ...previousForm.user,
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
      const response = await bootstrapSystem(form)
      setSuccess("Setup completed successfully.")
      onComplete(response.business_id)
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Setup failed."))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={containerStyle}>
      <div className="setup-hero">
        <p className="eyebrow">Platform bootstrap</p>
        <h1>Configure RefurbOps</h1>
        <p className="muted-text">
          Create the first business and admin user, then continue directly into the inbound queue.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={formStyle}>
        <section style={sectionStyle}>
          <h2>Business</h2>

          <label style={labelStyle}>
            Business ID
            <input
              value={form.business._id}
              onChange={(event) => updateBusinessField("_id", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Business Name
            <input
              value={form.business.name}
              onChange={(event) => updateBusinessField("name", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Scheme
            <input
              value={form.business.vat_scheme}
              onChange={(event) => updateBusinessField("vat_scheme", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Period
            <input
              value={form.business.vat_period}
              onChange={(event) => updateBusinessField("vat_period", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            VAT Period Start
            <input
              value={form.business.vat_period_start}
              onChange={(event) => updateBusinessField("vat_period_start", event.target.value)}
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
              onChange={(event) => updateBackMarketField("api_key", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Accept Language
            <input
              value={form.business.backmarket.accept_language}
              onChange={(event) => updateBackMarketField("accept_language", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Company Name
            <input
              value={form.business.backmarket.company_name}
              onChange={(event) => updateBackMarketField("company_name", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Integration Name
            <input
              value={form.business.backmarket.integration_name}
              onChange={(event) => updateBackMarketField("integration_name", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Contact Email
            <input
              value={form.business.backmarket.contact_email}
              onChange={(event) => updateBackMarketField("contact_email", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Proxy URL
            <input
              value={form.business.backmarket.proxy_url}
              onChange={(event) => updateBackMarketField("proxy_url", event.target.value)}
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
              onChange={(event) => updateUserField("_id", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Name
            <input
              value={form.user.name}
              onChange={(event) => updateUserField("name", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Email
            <input
              value={form.user.email}
              onChange={(event) => updateUserField("email", event.target.value)}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Role
            <input
              value={form.user.role}
              onChange={(event) => updateUserField("role", event.target.value)}
              style={inputStyle}
            />
          </label>
        </section>

        {error ? <div style={errorStyle}>{error}</div> : null}
        {success ? <div style={successStyle}>{success}</div> : null}

        <button type="submit" disabled={submitting} style={buttonStyle}>
          {submitting ? "Saving..." : "Create business and user"}
        </button>
      </form>
    </div>
  )
}

const containerStyle: CSSProperties = {
  maxWidth: 1120,
  margin: "40px auto",
  padding: 24,
}

const formStyle: CSSProperties = {
  display: "grid",
  gap: 24,
}

const sectionStyle: CSSProperties = {
  padding: 20,
  border: "1px solid #dbe3f0",
  borderRadius: 16,
  background: "#ffffff",
  display: "grid",
  gap: 12,
  boxShadow: "0 12px 28px rgba(15, 23, 42, 0.06)",
}

const labelStyle: CSSProperties = {
  display: "grid",
  gap: 6,
  fontWeight: 500,
}

const inputStyle: CSSProperties = {
  padding: 10,
  borderRadius: 10,
  border: "1px solid #cbd5e1",
}

const buttonStyle: CSSProperties = {
  padding: "12px 16px",
  borderRadius: 10,
  border: "none",
  background: "#111827",
  color: "#fff",
  cursor: "pointer",
}

const errorStyle: CSSProperties = {
  padding: 12,
  borderRadius: 10,
  background: "#fee2e2",
  color: "#991b1b",
}

const successStyle: CSSProperties = {
  padding: 12,
  borderRadius: 10,
  background: "#dcfce7",
  color: "#166534",
}
