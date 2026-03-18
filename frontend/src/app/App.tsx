import { useEffect, useMemo, useState } from "react"
import { AppShell } from "./layout/AppShell"
import { BusinessProvider } from "./providers/BusinessProvider"
import { useBusiness } from "./providers/useBusiness"
import { LoadingState } from "../components/ui/LoadingState"
import { ErrorState } from "../components/ui/ErrorState"
import SetupPage from "../pages/SetupPage"
import InboundPage from "../pages/InboundPage"
import InboundDetailPage from "../pages/InboundDetailPage"
import { fetchSetupStatus } from "../services/setupApi"
import { getApiErrorMessage } from "../services/api/client"
import { appRoutes, navigateTo } from "../routes"

/**
 * Application entry point. It coordinates setup status, simple routing, and the
 * business-scoped shell used by the current frontend slice.
 */
function App() {
  return (
    <BusinessProvider>
      <AppController />
    </BusinessProvider>
  )
}

function AppController() {
  const { setBusinessId } = useBusiness()
  const [pathname, setPathname] = useState(window.location.pathname)
  const [loading, setLoading] = useState(true)
  const [isConfigured, setIsConfigured] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname)
    window.addEventListener("popstate", handlePopState)

    return () => {
      window.removeEventListener("popstate", handlePopState)
    }
  }, [])

  useEffect(() => {
    let active = true

    async function loadStatus() {
      setLoading(true)
      setError("")

      try {
        const result = await fetchSetupStatus()
        if (!active) {
          return
        }

        setIsConfigured(result.is_configured)
      } catch (statusError) {
        if (!active) {
          return
        }

        setError(getApiErrorMessage(statusError, "Failed to fetch setup status."))
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadStatus()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (loading || error) {
      return
    }

    if (!isConfigured && pathname !== appRoutes.setup) {
      navigateTo(appRoutes.setup)
      return
    }

    if (isConfigured && (pathname === appRoutes.root || pathname === appRoutes.setup)) {
      navigateTo(appRoutes.inbound)
    }
  }, [error, isConfigured, loading, pathname])

  const route = useMemo(() => {
    if (pathname.startsWith(`${appRoutes.inbound}/`)) {
      return {
        kind: "inbound-detail" as const,
        inboundId: pathname.replace(`${appRoutes.inbound}/`, ""),
      }
    }

    if (pathname === appRoutes.inbound) {
      return { kind: "inbound" as const }
    }

    return { kind: "setup" as const }
  }, [pathname])

  if (loading) {
    return <LoadingState message="Loading RefurbOps..." />
  }

  if (error) {
    return <ErrorState message={error} actionLabel="Reload" onAction={() => window.location.reload()} />
  }

  if (!isConfigured || route.kind === "setup") {
    return (
      <SetupPage
        onComplete={(businessId) => {
          setBusinessId(businessId)
          setIsConfigured(true)
          navigateTo(appRoutes.inbound)
        }}
      />
    )
  }

  return (
    <AppShell currentPath={pathname}>
      {route.kind === "inbound-detail" ? <InboundDetailPage inboundId={route.inboundId} /> : <InboundPage />}
    </AppShell>
  )
}

export default App
