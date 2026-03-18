interface EmptyStateProps {
  title: string
  description: string
}

/**
 * Display an empty state for lists that have loaded successfully.
 */
export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="state-panel empty-panel">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  )
}
