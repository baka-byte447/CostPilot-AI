import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { fetchSLOConfig, fetchSafetyStatus, fetchRLExplanation } from "../services/api"
import { ShieldCheck, ShieldAlert, Clock } from "lucide-react"

export default function SafetyPanel() {
  const [slo, setSlo]           = useState<any>(null)
  const [status, setStatus]     = useState<any>(null)
  const [explanation, setExpl]  = useState<any>(null)
  const [loading, setLoading]   = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [s, st, e] = await Promise.allSettled([
        fetchSLOConfig(),
        fetchSafetyStatus(),
        fetchRLExplanation(),
      ])
      if (s.status === "fulfilled")  setSlo(s.value.data)
      if (st.status === "fulfilled") setStatus(st.value.data)
      if (e.status === "fulfilled")  setExpl(e.value.data?.explanation)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t) }, [])

  const SLO_ITEMS = slo ? [
    { label: "Max CPU %",           value: slo.max_cpu_pct,              unit: "%",   warn: 85 },
    { label: "Max Memory %",        value: slo.max_memory_pct,           unit: "%",   warn: 90 },
    { label: "Max Requests/s",      value: slo.max_request_load,         unit: "/s",  warn: 2 },
    { label: "Min Replicas",        value: slo.min_replicas,             unit: "",    warn: null },
    { label: "Max Replicas",        value: slo.max_replicas,             unit: "",    warn: null },
    { label: "Max Scale Step",      value: slo.max_scale_step,           unit: "",    warn: null },
    { label: "Scale-Down CPU ≤",    value: slo.max_cpu_to_scale_down,    unit: "%",   warn: null },
    { label: "Scale-Down Mem ≤",    value: slo.max_memory_to_scale_down, unit: "%",   warn: null },
    { label: "Scale-Down Req ≤",    value: slo.max_requests_to_scale_down, unit: "/s", warn: null },
    { label: "Cooldown",            value: slo.cooldown_seconds,         unit: "s",   warn: null },
  ] : []

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            {status?.cooldown_active
              ? <ShieldAlert size={14} className="text-amber" />
              : <ShieldCheck size={14} className="text-green" />
            }
            <span className="card-title">Constraint Engine Status</span>
          </div>

          {status ? (
            <div className="space-y-3">
              <div className={`rounded-md p-4 border ${status.cooldown_active ? "bg-amberDim border-amber/20" : "bg-greenDim border-green/20"}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Clock size={12} className={status.cooldown_active ? "text-amber" : "text-green"} />
                  <span className={`text-xs font-mono font-semibold ${status.cooldown_active ? "text-amber" : "text-green"}`}>
                    {status.cooldown_active ? "COOLDOWN ACTIVE" : "READY"}
                  </span>
                </div>
                {status.cooldown_active && (
                  <div>
                    <div className="h-1.5 bg-surfaceBorder rounded-full overflow-hidden mb-1">
                      <motion.div
                        className="h-full bg-amber rounded-full"
                        initial={{ width: "100%" }}
                        animate={{ width: `${(status.cooldown_remaining / (slo?.cooldown_seconds ?? 30)) * 100}%` }}
                        transition={{ duration: 1 }}
                      />
                    </div>
                    <p className="text-[10px] font-mono text-amber">{status.cooldown_remaining}s remaining</p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "CPU SLO",     ok: true },
                  { label: "Memory SLO",  ok: true },
                  { label: "Request SLO", ok: true },
                ].map(item => (
                  <div key={item.label} className={`rounded-md p-2.5 text-center border ${item.ok ? "bg-greenDim border-green/20" : "bg-redDim border-red/20"}`}>
                    <p className={`text-[10px] font-mono font-semibold ${item.ok ? "text-green" : "text-red"}`}>
                      {item.ok ? "✓" : "✗"}
                    </p>
                    <p className="text-[10px] font-mono text-textMuted mt-0.5">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2 animate-pulse">
              {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-12 bg-surfaceHigh rounded" />)}
            </div>
          )}
        </div>

        <div className="card p-5">
          <span className="card-title block mb-4">SLO Configuration</span>
          {loading ? (
            <div className="space-y-2 animate-pulse">
              {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-8 bg-surfaceHigh rounded" />)}
            </div>
          ) : (
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {SLO_ITEMS.map(item => (
                <div key={item.label} className="flex items-center justify-between bg-surfaceHigh rounded px-3 py-2">
                  <span className="text-[11px] font-mono text-textMuted">{item.label}</span>
                  <span className="text-[11px] font-mono font-semibold text-cyan">{item.value}{item.unit}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {explanation && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="card-title">Latest Safety Decision</span>
            <span className={`badge ${explanation.safety_overridden ? "badge-amber" : "badge-green"}`}>
              {explanation.safety_overridden ? "OVERRIDDEN" : "APPROVED"}
            </span>
            <span className="badge badge-purple ml-auto">{explanation.source}</span>
          </div>
          <p className="text-sm text-text leading-relaxed bg-surfaceHigh rounded-lg p-4 font-mono">
            {explanation.explanation}
          </p>
          <div className="flex items-center gap-4 mt-3 text-[10px] font-mono text-textMuted">
            <span>action: <span className="text-text">{explanation.action}</span></span>
            <span>cpu: <span className="text-cyan">{explanation.cpu}%</span></span>
            <span>memory: <span className="text-green">{explanation.memory}%</span></span>
            <span>replicas: <span className="text-amber">{explanation.replicas}</span></span>
          </div>
        </div>
      )}
    </div>
  )
}