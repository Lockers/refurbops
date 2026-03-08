import { useEffect, useState } from "react"
import { fetchInbound, syncInbound } from "../services/inboundApi"
import { InboundQueueRow } from "../types/inbound"
import InboundTable from "../components/InboundTable"

const BUSINESS_ID = "biz_001"

export default function InboundPage() {
  const [rows, setRows] = useState<InboundQueueRow[]>([])
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    const data = await fetchInbound(BUSINESS_ID)
    setRows(data.items)
    setLoading(false)
  }

  async function handleSync() {
    setLoading(true)
    await syncInbound(BUSINESS_ID)
    await load()
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div>
      <h1>Inbound Orders</h1>

      <button onClick={handleSync}>
        Sync BackMarket
      </button>

      {loading ? <p>Loading...</p> : <InboundTable rows={rows} />}
    </div>
  )
}
