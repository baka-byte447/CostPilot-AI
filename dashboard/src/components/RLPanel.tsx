import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { fetchRLDecision, fetchRLStats, fetchAWSActions } from "../services/api"
import { Brain, TrendingUp, TrendingDown, Minus, RefreshCw } from "lucide-react"

const ACTION_CONFIG: Record<string, { label: string; color: string; badgeClass: string; icon: any }> = {
  scale_up:   { label: "SCALE UP",   color: "text-cyan",   badgeClass: "badge-cyan",   icon: TrendingUp },
  maintain:   { label: "MAINTAIN",   color: "text-green",  badgeClass: "badge-green",  icon: Minus },
  scale_down: { label: "SCALE DOWN", color: "text-amber",  badgeClass: "badge-amber",  icon: TrendingDown },
}

export default function RLPanel() {
  const [decision, setDecision] = useState<any>(null)
  const [stats, setStats]       = useState<any>(null)
  const [actions, setActions]   = useState<any[]>([])
  const [loading, setLoading]   = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [d, s, a] = await Promise.allSettled([
        fetchRLDecision(),
        fetchRLStats(),
        fetchAWSActions(),
      ])
      if (d.status === "fulfilled") setDecision(d.value.data?.decision)
      if (s.status === "fulfilled") setStats(s.value.data)
      if (a.status === "fulfilled") setActions(a.value.data?.slice(0, 8) ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t) }, [])

  const actionCfg = decision ? (ACTION_CONFIG[decision.action] ?? ACTION_CONFIG.maintain) : null
  const ActionIcon = actionCfg?.icon ?? Minus

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="card-title flex items-center gap-2"><Brain size={14} className="text-purple" />Latest Decision</span>
            <button onClick={load} className="text-textMuted hover:text-text transition-colors">
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            </button>
          </div>

          {loading || !decision ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-10 bg-surfaceHigh rounded w-32" />
              <div className="h-4 bg-surfaceHigh rounded w-full" />
              <div className="h-4 bg-surfaceHigh rounded w-3/4" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <ActionIcon size={20} className={actionCfg?.color} />
                <span className={`font-mono text-2xl font-semibold ${actionCfg?.color}`}>
                  {actionCfg?.label}
                </span>
                {decision.proposed_action !== decision.action && (
                  <span className="badge badge-amber">OVERRIDDEN</span>
                )}
              </div>

              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "CPU",    value: `${decision.cpu?.toFixed(1)}%`,    color: "text-cyan"   },
                  { label: "MEM",    value: `${decision.memory?.toFixed(1)}%`, color: "text-green"  },
                  { label: "REQ/S",  value: decision.request_load?.toFixed(3), color: "text-amber"  },
                ].map(m => (
                  <div key={m.label} className="bg-surfaceHigh rounded-md p-3">
                    <p className="text-[10px] font-mono text-textMuted mb-1">{m.label}</p>
                    <p className={`font-mono text-sm font-semibold ${m.color}`}>{m.value}</p>
                  </div>
                ))}
              </div>

              <div className="bg-surfaceHigh rounded-md p-3">
                <p className="text-[10px] font-mono text-textMuted mb-2">Q-VALUES</p>
                <div className="space-y-1.5">
                  {Object.entries(decision.q_values ?? {}).map(([k, v]: any) => (
                    <div key={k} className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-textMuted w-20">{k}</span>
                      <div className="flex-1 h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
                        <div
                          className="h-full bg-cyan rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(0, (v + 1) * 50))}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-mono text-text w-12 text-right">{v?.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-textMuted">reward: <span className="text-text">{decision.reward}</span></span>
                <span className="text-textMuted">ε: <span className="text-text">{decision.epsilon}</span></span>
                <span className="text-textMuted">replicas: <span className="text-cyan">{decision.replicas}</span></span>
              </div>
            </div>
          )}
        </div>

        <div className="card p-5">
          <span className="card-title block mb-4">Agent Statistics</span>
          {stats ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Q-Table Shape",   value: stats.shape?.join(" × ") ?? "--" },
                  { label: "Total States",     value: stats.total_states ?? "--" },
                  { label: "Coverage",         value: `${stats.coverage_pct ?? 0}%` },
                  { label: "Non-Zero Entries", value: stats.nonzero_entries ?? "--" },
                  { label: "Max Q-Value",      value: stats.max_q_value?.toFixed(4) ?? "--" },
                  { label: "Mean Q-Value",     value: stats.mean_q_value?.toFixed(4) ?? "--" },
                  { label: "Learning Rate α",  value: stats.alpha ?? "--" },
                  { label: "Discount γ",       value: stats.gamma ?? "--" },
                ].map(s => (
                  <div key={s.label} className="bg-surfaceHigh rounded-md p-3">
                    <p className="text-[10px] font-mono text-textMuted mb-1">{s.label}</p>
                    <p className="font-mono text-sm font-semibold text-cyan">{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="bg-surfaceHigh rounded-md p-3">
                <p className="text-[10px] font-mono text-textMuted mb-2">COVERAGE</p>
                <div className="h-2 bg-surfaceBorder rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-cyan to-green rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${stats.coverage_pct ?? 0}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </div>
                <p className="text-[10px] font-mono text-textMuted mt-1">{stats.coverage_pct}% of state space explored</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2 animate-pulse">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-8 bg-surfaceHigh rounded" />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card p-5">
        <span className="card-title block mb-4">Recent Scaling Actions</span>
        {actions.length === 0 ? (
          <p className="text-textMuted text-sm font-mono">No actions yet</p>
        ) : (
          <div className="space-y-2">
            {actions.map((a, i) => {
              const cfg = ACTION_CONFIG[a.action] ?? ACTION_CONFIG.maintain
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="flex items-center gap-3 bg-surfaceHigh rounded-md px-4 py-2.5"
                >
                  <span className={`badge ${cfg.badgeClass} shrink-0`}>{cfg.label}</span>
                  <span className="font-mono text-xs text-text flex-1">{a.target}</span>
                  {a.previous !== undefined && (
                    <span className="font-mono text-xs text-textMuted">{a.previous} → {a.new}</span>
                  )}
                  <span className="font-mono text-[10px] text-textDim shrink-0">
                    {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "--"}
                  </span>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}