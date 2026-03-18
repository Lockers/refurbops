export const appRoutes = {
  root: "/",
  setup: "/setup",
  inbound: "/inbound",
} as const

/**
 * Push a new browser history entry and notify the app router listeners.
 */
export function navigateTo(path: string) {
  if (window.location.pathname === path) {
    return
  }

  window.history.pushState({}, "", path)
  window.dispatchEvent(new PopStateEvent("popstate"))
}
