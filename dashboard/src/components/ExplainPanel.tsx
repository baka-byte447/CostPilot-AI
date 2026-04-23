import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { fetchRLExplanation } from "../services/api"
import { MessageSquare, Cpu, MemoryStick, Zap, RefreshCw } from "lucide-react"

export default function ExplainPanel() {
  const [current, setCurrent]   = useState<any>(null)
  const [history, setHistory]   = useState<any[]>([])
  const [loading, setLoading]   = useState(true)

  const load = async () => {
    try {
      const [e] = await Promise.allSettled([
        fetchRLExplanation(),
      ])

      if (e.status === "fulfilled" && e.value.data?.explanation) {
        const expl = e.value.data.explanation
        setCurrent(expl)
        setHistory(prev => {
          if (prev[0]?.timestamp === expl.timestamp) return prev
          return [expl, ...prev].slice(0, 12)
        })
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t) }, [])

  const ACTION_COLORS: Record<string, string> = {
    scale_up:   "text-cyan",
    maintain:   "text-green",
    scale_down: "text-amber",
  }

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <span className="card-title flex items-center gap-2">
            <MessageSquare size={14} className="text-purple" />
            Current Explanation
          </span>
          <div className="flex items-center gap-2">
            {current?.source && (
              <span className="badge badge-purple">{current.source}</span>
            )}
            <button onClick={load} className="text-textMuted hover:text-text transition-colors">
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>

        {loading && !current ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-4 bg-surfaceHigh rounded w-full" />
            <div className="h-4 bg-surfaceHigh rounded w-5/6" />
            <div className="h-4 bg-surfaceHigh rounded w-4/6" />
          </div>
        ) : current ? (
          <div className="space-y-4">
            <div className={`rounded-lg p-5 bg-surfaceHigh border border-surfaceBorder`}>
              <p className="text-sm text-text leading-relaxed font-mono">{current.explanation}</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-surfaceHigh rounded-md p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Zap size={11} className="text-textMuted" />
                  <span className="text-[10px] font-mono text-textMuted">ACTION</span>
                </div>
                <span className={`font-mono text-sm font-semibold ${ACTION_COLORS[current.action] ?? "text-text"}`}>
                  {current.action?.toUpperCase().replace("_", " ")}
                </span>
              </div>
              <div className="bg-surfaceHigh rounded-md p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Cpu size={11} className="text-textMuted" />
                  <span className="text-[10px] font-mono text-textMuted">CPU</span>
                </div>
                <span className="font-mono text-sm font-semibold text-cyan">{current.cpu}%</span>
              </div>
              <div className="bg-surfaceHigh rounded-md p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <MemoryStick size={11} className="text-textMuted" />
                  <span className="text-[10px] font-mono text-textMuted">MEMORY</span>
                </div>
                <span className="font-mono text-sm font-semibold text-green">{current.memory}%</span>
              </div>
              <div className="bg-surfaceHigh rounded-md p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Zap size={11} className="text-textMuted" />
                  <span className="text-[10px] font-mono text-textMuted">REPLICAS</span>
                </div>
                <span className="font-mono text-sm font-semibold text-amber">{current.replicas}</span>
              </div>
            </div>

            {current.safety_overridden && (
              <div className="rounded-md p-3 bg-amberDim border border-amber/20 text-xs font-mono text-amber">
                ⚠ Safety engine overrode the RL agent's proposed action
              </div>
            )}
          </div>
        ) : (
          <p className="text-textMuted text-sm font-mono">Waiting for first decision...</p>
        )}
      </div>

      <div className="card p-5">
        <span className="card-title block mb-4">Explanation History</span>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          <AnimatePresence initial={false}>
            {history.map((item, i) => (
              <motion.div
                key={item.timestamp ?? i}
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="bg-surfaceHigh rounded-lg p-4 border border-surfaceBorder"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={`badge ${item.safety_overridden ? "badge-amber" : "badge-green"}`}>
                    {item.action?.toUpperCase().replace("_", " ")}
                  </span>
                  <span className="badge badge-purple">{item.source}</span>
                  <span className="text-[10px] font-mono text-textDim ml-auto">
                    {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : "--"}
                  </span>
                </div>
                <p className="text-xs font-mono text-textMuted leading-relaxed">{item.explanation}</p>
              </motion.div>
            ))}
          </AnimatePresence>
          {history.length === 0 && (
            <p className="text-textMuted text-sm font-mono text-center py-8">No history yet</p>
          )}
        </div>
      </div>
    </div>
  )
}