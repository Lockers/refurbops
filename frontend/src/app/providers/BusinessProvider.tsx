import { ReactNode, useMemo, useState } from "react"
import { BusinessContext, DEFAULT_BUSINESS_ID, STORAGE_KEY } from "./business-context"

/**
 * Provide the active business identifier to every business-scoped screen.
 *
 * The backend still expects `business_id` explicitly, so the frontend keeps a
 * lightweight tenant context in local storage until auth is introduced.
 */
export function BusinessProvider({ children }: { children: ReactNode }) {
  const [businessId, setBusinessIdState] = useState(() => {
    if (typeof window === "undefined") {
      return DEFAULT_BUSINESS_ID
    }

    return window.localStorage.getItem(STORAGE_KEY) || DEFAULT_BUSINESS_ID
  })

  function setBusinessId(nextBusinessId: string) {
    const normalizedBusinessId = nextBusinessId.trim() || DEFAULT_BUSINESS_ID
    window.localStorage.setItem(STORAGE_KEY, normalizedBusinessId)
    setBusinessIdState(normalizedBusinessId)
  }

  const value = useMemo(
    () => ({
      businessId,
      setBusinessId,
    }),
    [businessId]
  )

  return <BusinessContext.Provider value={value}>{children}</BusinessContext.Provider>
}
