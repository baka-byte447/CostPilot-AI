import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { fetchAzureACI, fetchAzureCost, fetchAzureCostByService } from "../services/api"
import { RefreshCw, Container, DollarSign } from "lucide-react"

export default function AzurePanel() {
  const [aci, setAci]         = useState<any[]>([])
  const [cost, setCost]       = useState<any>(null)
  const [byService, setByService] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [a, c, b] = await Promise.allSettled([
        fetchAzureACI(),
        fetchAzureCost(),
        fetchAzureCostByService(),
      ])
      if (a.status === "fulfilled") setAci(a.value.data ?? [])
      if (c.status === "fulfilled") setCost(c.value.data)
      if (b.status === "fulfilled") setByService(b.value.data ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t) }, [])

  const maxCost = byService.length > 0 ? Math.max(...byService.map((s: any) => s.cost)) : 1

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text">Azure Resources</h2>
        <div className="flex items-center gap-2">
          <span className="badge badge-green">REAL CLOUD</span>
          <button onClick={load} className="text-textMuted hover:text-text transition-colors">
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign size={13} className="text-green" />
            <span className="card-title">Cost (Month-to-Date)</span>
          </div>
          {cost ? (
            <div className="space-y-4">
              <div>
                <p className="text-[10px] font-mono text-textMuted mb-1">TOTAL SPEND</p>
                <p className="font-mono text-4xl font-semibold text-green tabular-nums">
                  ${cost.amount?.toFixed(2)}
                </p>
                <p className="text-[11px] font-mono text-textMuted mt-1">
                  {cost.period_start} → {cost.period_end}
                </p>
              </div>
              <div className="bg-surfaceHigh rounded-md p-3">
                <p className="text-[10px] font-mono text-textMuted mb-1">STUDENT CREDITS REMAINING (EST.)</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-surfaceBorder rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-green rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.max(0, ((100 - cost.amount) / 100) * 100)}%` }}
                      transition={{ duration: 1 }}
                    />
                  </div>
                  <span className="text-[11px] font-mono text-green font-semibold">
                    ${(100 - cost.amount).toFixed(2)} left
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="animate-pulse space-y-3">
              <div className="h-12 bg-surfaceHigh rounded" />
              <div className="h-8 bg-surfaceHigh rounded" />
            </div>
          )}
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Container size={13} className="text-cyan" />
            <span className="card-title">Container Instances (ACI)</span>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-12 bg-surfaceHigh rounded" />
            </div>
          ) : aci.length > 0 ? (
            <div className="space-y-2">
              {aci.map((group: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-surfaceHigh rounded-md p-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-semibold text-text">{group.name}</span>
                    <span className={`badge ${group.state === "Running" || group.state === "Unknown" ? "badge-green" : "badge-red"}`}>
                      {group.state === "Unknown" ? "RUNNING" : group.state?.toUpperCase() ?? "UNKNOWN"}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-[10px] font-mono text-textMuted">
                    <span>location: <span className="text-text">{group.location}</span></span>
                    {group.ip && <span>ip: <span className="text-cyan">{group.ip}</span></span>}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="rounded-md p-4 bg-surfaceHigh text-center">
              <p className="text-textMuted text-xs font-mono">No container groups running</p>
              <p className="text-textDim text-[10px] font-mono mt-1">Run: az container start --resource-group nimbusopt-rg --name nimbusopt-containers-1</p>
            </div>
          )}
        </div>
      </div>

      {byService.length > 0 && (
        <div className="card p-5">
          <span className="card-title block mb-4">Cost by Service</span>
          <div className="space-y-2">
            {byService.slice(0, 8).map((s: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[11px] font-mono text-textMuted w-48 truncate">{s.service}</span>
                <div className="flex-1 h-2 bg-surfaceBorder rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-cyan rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(s.cost / maxCost) * 100}%` }}
                    transition={{ duration: 0.8, delay: i * 0.05 }}
                  />
                </div>
                <span className="text-[11px] font-mono text-cyan w-16 text-right">${s.cost?.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}