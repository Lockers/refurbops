import { useEffect, useMemo, useState } from "react"
import InboundTable from "../components/InboundTable"
import { PageShell } from "../components/layout/PageShell"
import { EmptyState } from "../components/ui/EmptyState"
import { ErrorState } from "../components/ui/ErrorState"
import { LoadingState } from "../components/ui/LoadingState"
import { useBusiness } from "../app/providers/useBusiness"
import { getApiErrorMessage } from "../services/api/client"
import { fetchInbound, syncInbound } from "../services/inboundApi"
import { InboundQueryParams, InboundQueueRow, InboundSyncResult } from "../types/inbound"
import { navigateTo } from "../routes"

const DEFAULT_PAGE_SIZE = 25

/**
 * Render the inbound queue for the currently selected business.
 */
export default function InboundPage() {
  const { businessId } = useBusiness()
  const [rows, setRows] = useState<InboundQueueRow[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState("")
  const [syncResult, setSyncResult] = useState<InboundSyncResult | null>(null)
  const [filters, setFilters] = useState({
    externalStatus: "",
    market: "",
    hasTracking: "all",
    trackingStatusGroup: "",
    likelyArrivalBucket: "",
    arrivedClicked: "all",
  })
  const [page, setPage] = useState(1)

  const query = useMemo<InboundQueryParams>(
    () => ({
      businessId,
      externalStatus: filters.externalStatus,
      market: filters.market,
      hasTracking:
        filters.hasTracking === "all"
          ? undefined
          : filters.hasTracking === "tracked",
      trackingStatusGroup: filters.trackingStatusGroup,
      likelyArrivalBucket: filters.likelyArrivalBucket,
      arrivedClicked:
        filters.arrivedClicked === "all"
          ? undefined
          : filters.arrivedClicked === "arrived",
      page,
      pageSize: DEFAULT_PAGE_SIZE,
    }),
    [businessId, filters, page]
  )

  useEffect(() => {
    let active = true

    async function loadInboundQueue() {
      setLoading(true)
      setError("")

      try {
        const result = await fetchInbound(query)
        if (!active) {
          return
        }

        setRows(result.items)
        setTotal(result.total)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(getApiErrorMessage(loadError, "Failed to load inbound queue."))
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadInboundQueue()

    return () => {
      active = false
    }
  }, [query])

  async function handleSync() {
    setSyncing(true)
    setError("")

    try {
      const result = await syncInbound(businessId)
      setSyncResult(result)

      const refreshed = await fetchInbound(query)
      setRows(refreshed.items)
      setTotal(refreshed.total)
    } catch (syncError) {
      setError(getApiErrorMessage(syncError, "Failed to sync inbound orders."))
    } finally {
      setSyncing(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / DEFAULT_PAGE_SIZE))

  return (
    <PageShell
      title="Inbound queue"
      subtitle="Operational entry point for synced Back Market orders. The next backend slice should add Arrived -> Device creation from this screen."
    >
      <div className="toolbar card">
        <div className="toolbar-row">
          <div>
            <p className="eyebrow">Selected business</p>
            <strong>{businessId}</strong>
          </div>

          <div className="button-row">
            <button className="secondary-button" onClick={() => window.location.reload()} type="button">
              Refresh
            </button>
            <button className="primary-button" onClick={handleSync} type="button" disabled={syncing}>
              {syncing ? "Syncing..." : "Sync Back Market"}
            </button>
          </div>
        </div>

        <div className="filter-grid">
          <label>
            External status
            <input
              value={filters.externalStatus}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, externalStatus: event.target.value }))
              }}
            />
          </label>

          <label>
            Market
            <input
              value={filters.market}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, market: event.target.value }))
              }}
            />
          </label>

          <label>
            Tracking coverage
            <select
              value={filters.hasTracking}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, hasTracking: event.target.value }))
              }}
            >
              <option value="all">All</option>
              <option value="tracked">Tracked only</option>
              <option value="untracked">Untracked only</option>
            </select>
          </label>

          <label>
            Tracking status group
            <input
              value={filters.trackingStatusGroup}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, trackingStatusGroup: event.target.value }))
              }}
            />
          </label>

          <label>
            Arrival bucket
            <input
              value={filters.likelyArrivalBucket}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, likelyArrivalBucket: event.target.value }))
              }}
            />
          </label>

          <label>
            Local arrival state
            <select
              value={filters.arrivedClicked}
              onChange={(event) => {
                setPage(1)
                setFilters((current) => ({ ...current, arrivedClicked: event.target.value }))
              }}
            >
              <option value="all">All</option>
              <option value="arrived">Arrived clicked</option>
              <option value="not-arrived">Not arrived</option>
            </select>
          </label>
        </div>
      </div>

      {syncResult ? (
        <div className="card sync-summary">
          <p>
            Sync complete for <strong>{syncResult.business_id}</strong>. Fetched {syncResult.fetched}, inserted {syncResult.inserted}, updated {syncResult.updated}.
          </p>
          <p className="muted-text">
            Started {new Date(syncResult.started_at).toLocaleString()} · Completed {new Date(syncResult.completed_at).toLocaleString()}
          </p>
        </div>
      ) : null}

      {error ? <ErrorState message={error} actionLabel="Reload" onAction={() => window.location.reload()} /> : null}

      {loading ? (
        <LoadingState message="Loading inbound queue..." />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No inbound orders found"
          description="Adjust the queue filters or run a sync to bring in the latest Back Market orders."
        />
      ) : (
        <InboundTable rows={rows} onSelectRow={(row) => navigateTo(`/inbound/${row._id}`)} />
      )}

      <div className="pagination-bar">
        <span>
          Page {page} of {totalPages} · {total} total rows
        </span>

        <div className="button-row">
          <button className="secondary-button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">
            Previous
          </button>
          <button className="secondary-button" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)} type="button">
            Next
          </button>
        </div>
      </div>
    </PageShell>
  )
}
