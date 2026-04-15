import { motion } from "framer-motion"
import type { FC, ReactNode } from "react"

interface MetricCardProps {
  title: string
  value: string | number
  sub?: string
  loading?: boolean
  accent?: "cyan" | "green" | "amber" | "red" | "purple"
  icon?: ReactNode
  badge?: string
  badgeVariant?: "green" | "red" | "amber" | "cyan" | "purple"
}

const ACCENT_MAP = {
  cyan:   { value: "text-cyan",   dot: "bg-cyan",   glow: "shadow-[0_0_16px_rgba(0,212,255,0.12)]" },
  green:  { value: "text-green",  dot: "bg-green",  glow: "shadow-[0_0_16px_rgba(0,229,153,0.12)]" },
  amber:  { value: "text-amber",  dot: "bg-amber",  glow: "shadow-[0_0_16px_rgba(255,176,32,0.12)]" },
  red:    { value: "text-red",    dot: "bg-red",    glow: "shadow-[0_0_16px_rgba(255,77,106,0.12)]" },
  purple: { value: "text-purple", dot: "bg-purple", glow: "shadow-[0_0_16px_rgba(167,139,250,0.12)]" },
}

const MetricCard: FC<MetricCardProps> = ({
  title, value, sub, loading, accent = "cyan", icon, badge, badgeVariant = "green"
}) => {
  const a = ACCENT_MAP[accent]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className={`card p-5 flex flex-col gap-3 cursor-default hover:border-surfaceBorder/80 transition-all ${a.glow}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${a.dot}`} />
          <span className="text-[11px] font-mono font-medium text-textMuted uppercase tracking-wider">{title}</span>
        </div>
        {icon && <div className="text-textDim">{icon}</div>}
      </div>

      {loading ? (
        <div className="h-8 w-24 bg-surfaceHigh rounded animate-pulse" />
      ) : (
        <div className="flex items-end gap-2">
          <span className={`font-mono text-[28px] font-semibold tabular-nums leading-none ${a.value}`}>
            {value}
          </span>
          {badge && (
            <span className={`badge badge-${badgeVariant} mb-0.5`}>{badge}</span>
          )}
        </div>
      )}

      {sub && <p className="text-[11px] text-textMuted font-mono">{sub}</p>}
    </motion.div>
  )
}

export default MetricCard