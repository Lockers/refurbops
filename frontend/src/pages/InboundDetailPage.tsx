import { useEffect, useState } from "react"
import { PageShell } from "../components/layout/PageShell"
import { ErrorState } from "../components/ui/ErrorState"
import { LoadingState } from "../components/ui/LoadingState"
import { getApiErrorMessage } from "../services/api/client"
import { fetchInboundOrder } from "../services/inboundApi"
import { InboundOrderDocument } from "../types/inbound"
import { useBusiness } from "../app/providers/useBusiness"
import { navigateTo } from "../routes"

interface InboundDetailPageProps {
  inboundId: string
}

/**
 * Render the full inbound order detail returned by the backend.
 */
export default function InboundDetailPage({ inboundId }: InboundDetailPageProps) {
  const { businessId } = useBusiness()
  const [order, setOrder] = useState<InboundOrderDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true

    async function loadOrder() {
      setLoading(true)
      setError("")

      try {
        const result = await fetchInboundOrder({ businessId, inboundId })
        if (!active) {
          return
        }

        setOrder(result)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(getApiErrorMessage(loadError, "Failed to load inbound order."))
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadOrder()

    return () => {
      active = false
    }
  }, [businessId, inboundId])

  if (loading) {
    return <LoadingState message="Loading inbound order..." />
  }

  if (error) {
    return <ErrorState message={error} actionLabel="Back to inbound queue" onAction={() => navigateTo("/inbound")} />
  }

  if (!order) {
    return <ErrorState message="Inbound order not found." actionLabel="Back to inbound queue" onAction={() => navigateTo("/inbound")} />
  }

  return (
    <PageShell
      title={`Inbound order ${order.source_reference}`}
      subtitle="Detail view for the current inbound sync slice. This will become the launch point for Arrived -> Device creation in the next module."
    >
      <div className="detail-actions">
        <button className="secondary-button" onClick={() => navigateTo("/inbound")} type="button">
          Back to queue
        </button>
      </div>

      <div className="card-grid">
        <article className="card">
          <h2>Order summary</h2>
          <dl className="key-values">
            <div><dt>Business</dt><dd>{order.business_id}</dd></div>
            <div><dt>Source</dt><dd>{order.source}</dd></div>
            <div><dt>External status</dt><dd>{order.external_status || "—"}</dd></div>
            <div><dt>Market</dt><dd>{order.market || "—"}</dd></div>
            <div><dt>Created</dt><dd>{formatDate(order.creation_date)}</dd></div>
            <div><dt>Modified</dt><dd>{formatDate(order.modification_date)}</dd></div>
          </dl>
        </article>

        <article className="card">
          <h2>Listing</h2>
          <dl className="key-values">
            <div><dt>Title</dt><dd>{order.listing.title || "—"}</dd></div>
            <div><dt>Grade</dt><dd>{order.listing.grade || "—"}</dd></div>
            <div><dt>SKU</dt><dd>{order.listing.sku || "—"}</dd></div>
            <div><dt>Product ID</dt><dd>{order.listing.product_id ?? "—"}</dd></div>
          </dl>
        </article>

        <article className="card">
          <h2>Customer</h2>
          <dl className="key-values">
            <div><dt>Name</dt><dd>{[order.customer.first_name, order.customer.last_name].filter(Boolean).join(" ") || "—"}</dd></div>
            <div><dt>Phone</dt><dd>{order.customer.phone || "—"}</dd></div>
            <div><dt>Date of birth</dt><dd>{order.customer.date_of_birth || "—"}</dd></div>
          </dl>
        </article>

        <article className="card">
          <h2>Tracking</h2>
          <dl className="key-values">
            <div><dt>Shipper</dt><dd>{order.tracking.shipper || "—"}</dd></div>
            <div><dt>Tracking number</dt><dd>{order.tracking.tracking_number || "—"}</dd></div>
            <div><dt>Status group</dt><dd>{order.tracking.status_group || "—"}</dd></div>
            <div><dt>Arrival bucket</dt><dd>{order.tracking.likely_arrival_bucket || "—"}</dd></div>
          </dl>
        </article>

        <article className="card">
          <h2>Commercial</h2>
          <dl className="key-values">
            <div><dt>Original price</dt><dd>{formatMoney(order.original_price.value, order.original_price.currency)}</dd></div>
            <div><dt>Counter offer</dt><dd>{formatMoney(order.counter_offer_price?.value, order.counter_offer_price?.currency)}</dd></div>
            <div><dt>Payment date</dt><dd>{formatDate(order.payment_date)}</dd></div>
          </dl>
        </article>

        <article className="card">
          <h2>Local workflow</h2>
          <dl className="key-values">
            <div><dt>Arrived clicked</dt><dd>{String(order.local_state.arrived_clicked)}</dd></div>
            <div><dt>Device created</dt><dd>{String(order.local_state.device_created)}</dd></div>
            <div><dt>Linked device</dt><dd>{order.local_state.linked_device_id || "—"}</dd></div>
            <div><dt>Hidden from inbound</dt><dd>{String(order.local_state.hidden_from_inbound)}</dd></div>
            <div><dt>Archived</dt><dd>{String(order.local_state.archived)}</dd></div>
          </dl>
        </article>
      </div>
    </PageShell>
  )
}

function formatDate(value?: string | null) {
  if (!value) {
    return "—"
  }

  return new Date(value).toLocaleString()
}

function formatMoney(value?: number | null, currency?: string | null) {
  if (typeof value !== "number") {
    return "—"
  }

  return `${value} ${currency || ""}`.trim()
}
