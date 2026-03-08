import { useEffect, useState } from "react"
import SetupPage from "../pages/SetupPage"
import { fetchSetupStatus } from "../services/setupApi"

function App() {
  const [loading, setLoading] = useState(true)
  const [isConfigured, setIsConfigured] = useState(false)
  const [error, setError] = useState("")

  async function loadStatus() {
    setLoading(true)
    setError("")

    try {
      const result = await fetchSetupStatus()
      setIsConfigured(result.is_configured)
    } catch (err: any) {
      setError(err?.message || "Failed to fetch setup status.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  if (loading) {
    return <div style={{ padding: 40 }}>Loading...</div>
  }

  if (error) {
    return <div style={{ padding: 40 }}>Error: {error}</div>
  }

  if (!isConfigured) {
    return <SetupPage onComplete={loadStatus} />
  }

  return (
    <div style={{ padding: 40 }}>
      <h1>RefurbOps</h1>
      <p>Setup complete. Next step is the inbound queue page.</p>
    </div>
  )
}

export default App