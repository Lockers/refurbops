import { useEffect, useState } from 'react'

import { PageShell } from '../components/layout/PageShell'
import { fetchHealth } from '../services/api/client'
import type { HealthResponse } from '../types'

export function InboundPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void fetchHealth()
      .then(setHealth)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Unknown error')
      })
  }, [])

  return (
    <PageShell
      title="RefurbOps"
      subtitle="Environment scaffold ready. The next slice is inbound sync and Arrived -> device creation -> label flow."
    >
      <div className="card-grid">
        <section className="card">
          <h2>Backend connectivity</h2>
          {health ? (
            <dl className="key-values">
              <div>
                <dt>App</dt>
                <dd>{health.app}</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>{health.environment}</dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd>{health.database}</dd>
              </div>
            </dl>
          ) : (
            <p>{error ?? 'Waiting for backend...'}</p>
          )}
        </section>

        <section className="card">
          <h2>Locked structure</h2>
          <ul>
            <li>backend/app/api/routers</li>
            <li>backend/app/services</li>
            <li>backend/app/repositories</li>
            <li>backend/app/integrations</li>
            <li>frontend/src/pages</li>
            <li>frontend/src/features</li>
            <li>docs</li>
            <li>scripts</li>
          </ul>
        </section>
      </div>
    </PageShell>
  )
}
