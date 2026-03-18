interface ErrorStateProps {
  message: string
  actionLabel?: string
  onAction?: () => void
}

/**
 * Display recoverable application errors with an optional retry action.
 */
export function ErrorState({ message, actionLabel, onAction }: ErrorStateProps) {
  return (
    <div className="state-panel error-panel">
      <p>{message}</p>
      {actionLabel && onAction ? (
        <button className="secondary-button" onClick={onAction} type="button">
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}
