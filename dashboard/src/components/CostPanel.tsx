import { DollarSign, TrendingDown } from "lucide-react"
import { motion } from "framer-motion"

export default function CostPanel({ cost }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="card p-5 flex flex-col gap-4 h-full cursor-default"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber" />
          <span className="text-[11px] font-mono font-medium text-textMuted uppercase tracking-wider">Predicted Cost</span>
        </div>
        <DollarSign size={13} className="text-textDim" />
      </div>

      <div>
        <p className="font-mono text-[36px] font-semibold text-amber tabular-nums leading-none">
          ${cost?.predicted_hourly_cost ? cost.predicted_hourly_cost.toFixed(4) : "0.0000"}
        </p>
        <p className="text-[11px] font-mono text-textMuted mt-1">per hour · estimated</p>
      </div>

      {cost?.predicted_cpu !== undefined && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[10px] font-mono">
            <TrendingDown size={11} className="text-green" />
            <span className="text-textMuted">forecast cpu: <span className="text-cyan">{cost.predicted_cpu?.toFixed(1)}%</span></span>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-mono">
            <TrendingDown size={11} className="text-green" />
            <span className="text-textMuted">forecast mem: <span className="text-green">{cost.predicted_memory?.toFixed(1)}%</span></span>
          </div>
        </div>
      )}
    </motion.div>
  )
}