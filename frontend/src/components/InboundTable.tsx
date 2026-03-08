import { InboundQueueRow } from "../types/inbound"

interface Props {
  rows: InboundQueueRow[]
}

export default function InboundTable({ rows }: Props) {
  return (
    <table>
      <thead>
        <tr>
          <th>Order</th>
          <th>Customer</th>
          <th>Device</th>
          <th>Status</th>
          <th>Price</th>
          <th>Tracking</th>
        </tr>
      </thead>

      <tbody>
        {rows.map(row => (
          <tr key={row._id}>
            <td>{row.source_reference}</td>
            <td>{row.customer_full_name}</td>
            <td>{row.listing_title}</td>
            <td>{row.external_status}</td>
            <td>
              {row.original_price_value} {row.original_price_currency}
            </td>
            <td>{row.tracking_number}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}