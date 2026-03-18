interface LoadingStateProps {
  message?: string
}

/**
 * Display a consistent loading state across setup and inbound screens.
 */
export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return <div className="state-panel">{message}</div>
}
