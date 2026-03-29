import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts"

import { Card } from "@/components/ui/card"

export default function MetricsChart({ data }: any) {

  return (
    <Card className="p-6">

      <h2 className="text-lg font-semibold mb-4">
        System Metrics
      </h2>

      <ResponsiveContainer width="100%" height={300}>

        <LineChart data={data}>

          <XAxis dataKey="timestamp" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="cpu_usage"
            stroke="#38bdf8"
            strokeWidth={3}
          />

          <Line
            type="monotone"
            dataKey="memory_usage"
            stroke="#22c55e"
            strokeWidth={3}
          />

        </LineChart>

      </ResponsiveContainer>

    </Card>
  )
}



