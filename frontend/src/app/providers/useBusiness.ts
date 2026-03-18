import { useContext } from "react"
import { BusinessContext } from "./business-context"

/**
 * Read and update the active business identifier used by API requests.
 */
export function useBusiness() {
  const context = useContext(BusinessContext)

  if (!context) {
    throw new Error("useBusiness must be used within a BusinessProvider.")
  }

  return context
}
