import { InboundQueueRow } from "../types/inbound"

interface InboundTableProps {
  rows: InboundQueueRow[]
  onSelectRow: (row: InboundQueueRow) => void
}

/**
 * Render the queue table returned by the inbound list endpoint.
 */
export default function InboundTable({ rows, onSelectRow }: InboundTableProps) {
  return (
    <div className="table-card card">
      <table className="data-table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Listing</th>
            <th>External status</th>
            <th>Market</th>
            <th>Price</th>
            <th>Tracking</th>
            <th>Arrival bucket</th>
            <th>Local state</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row._id} onClick={() => onSelectRow(row)}>
              <td>{row.source_reference}</td>
              <td>{row.customer_full_name || "—"}</td>
              <td>
                <div>{row.listing_title || "—"}</div>
                <div className="muted-text">{row.listing_grade || "—"}</div>
              </td>
              <td>{row.external_status || "—"}</td>
              <td>{row.market || "—"}</td>
              <td>
                {typeof row.original_price_value === "number"
                  ? `${row.original_price_value} ${row.original_price_currency || ""}`.trim()
                  : "—"}
              </td>
              <td>
                <div>{row.tracking_number || "—"}</div>
                <div className="muted-text">{row.tracking_status_group || "No tracking status"}</div>
              </td>
              <td>{row.likely_arrival_bucket || "—"}</td>
              <td>
                {row.arrived_clicked ? "Arrived clicked" : "Awaiting arrival"}
                {row.device_created ? ` · ${row.linked_device_id || "Device created"}` : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
