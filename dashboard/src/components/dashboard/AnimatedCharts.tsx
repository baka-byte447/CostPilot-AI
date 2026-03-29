import type { FC } from "react"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts"
import { motion } from "framer-motion"

interface ChartProps {
  data: any[]
  title: string
}

const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  } catch {
    return ""
  }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surfaceHigh border border-surfaceBorder rounded-lg p-3 shadow-card text-xs font-mono pointer-events-none">
      <p className="text-textMuted mb-2 text-[10px] uppercase tracking-wider">{formatTime(label)}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-6 mb-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-sm" style={{ background: entry.stroke }} />
            <span className="text-textMuted">{entry.name}</span>
          </div>
          <span className="font-semibold" style={{ color: entry.stroke }}>
            {typeof entry.value === "number" ? entry.value.toFixed(2) : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

const AnimatedCharts: FC<ChartProps> = ({ data, title }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card p-5 w-full h-full flex flex-col"
    >
      <div className="flex items-center justify-between mb-5">
        <span className="card-title">{title}</span>
        <div className="flex items-center gap-4 text-[10px] font-mono text-textMuted">
          <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-cyan inline-block rounded" />CPU</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-green inline-block rounded" />Memory</span>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gradCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor="#00D4FF" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#00D4FF" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradMem" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor="#00E599" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#00E599" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A2540" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTime}
              stroke="#2E4060"
              fontSize={10}
              fontFamily="JetBrains Mono, monospace"
              tickLine={false}
              axisLine={false}
              dy={8}
            />
            <YAxis
              stroke="#2E4060"
              fontSize={10}
              fontFamily="JetBrains Mono, monospace"
              tickLine={false}
              axisLine={false}
              tickFormatter={v => `${v}%`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#1A2540", strokeWidth: 1 }} />
            <Area type="monotone" dataKey="cpu_usage"    name="CPU"    stroke="#00D4FF" fill="url(#gradCpu)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#00D4FF", strokeWidth: 0 }} />
            <Area type="monotone" dataKey="memory_usage" name="Memory" stroke="#00E599" fill="url(#gradMem)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#00E599", strokeWidth: 0 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  )
}

export default AnimatedCharts