import { ReactNode, useEffect, useState } from "react"
import { appRoutes, navigateTo } from "../../routes"
import { fetchHealth } from "../../services/api/client"
import { useBusiness } from "../providers/useBusiness"

interface AppShellProps {
  currentPath: string
  children: ReactNode
}

/**
 * Render the shared operator shell used for all post-setup screens.
 */
export function AppShell({ currentPath, children }: AppShellProps) {
  const { businessId, setBusinessId } = useBusiness()
  const [draftBusinessId, setDraftBusinessId] = useState(businessId)
  const [healthStatus, setHealthStatus] = useState("checking")

  useEffect(() => {
    setDraftBusinessId(businessId)
  }, [businessId])

  useEffect(() => {
    let active = true

    async function loadHealth() {
      try {
        const health = await fetchHealth()
        if (!active) {
          return
        }

        setHealthStatus(health.database === "ok" ? "healthy" : "degraded")
      } catch {
        if (!active) {
          return
        }

        setHealthStatus("offline")
      }
    }

    loadHealth()

    return () => {
      active = false
    }
  }, [currentPath])

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-block">
          <p className="eyebrow">RefurbOps</p>
          <h1>Operations Console</h1>
          <p className="muted-text">Inbound-first workflow aligned to the current backend slice.</p>
        </div>

        <nav className="app-nav" aria-label="Primary navigation">
          <button
            className={currentPath.startsWith(appRoutes.inbound) ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(appRoutes.inbound)}
            type="button"
          >
            Inbound Queue
          </button>
        </nav>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-section">
            <label className="topbar-label" htmlFor="business-id-input">
              Business
            </label>
            <input
              id="business-id-input"
              className="topbar-input"
              value={draftBusinessId}
              onChange={(event) => setDraftBusinessId(event.target.value)}
              onBlur={() => setBusinessId(draftBusinessId)}
            />
          </div>

          <div className="topbar-section status-stack">
            <span className={`status-pill ${healthStatus}`}>API {healthStatus}</span>
          </div>
        </header>

        <div className="app-content">{children}</div>
      </div>
    </div>
  )
}
