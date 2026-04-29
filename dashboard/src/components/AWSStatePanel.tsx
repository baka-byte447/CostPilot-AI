import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { fetchAWSState, fetchAWSActions } from "../services/api"
import { RefreshCw, Server, Layers, Box } from "lucide-react"

export default function AWSStatePanel() {
  const [awsState, setAwsState] = useState<any>(null)
  const [actions, setActions]   = useState<any[]>([])
  const [loading, setLoading]   = useState(true)

  const source = awsState?.source === "real" ? "real" : "mock"
  const sourceLabel = source === "real" ? "REAL AWS" : "MOCK"
  const sourceBadge = source === "real" ? "badge badge-green" : "badge badge-cyan"
  const sourceSuffix = source === "real" ? "" : " (LocalStack)"

  const load = async () => {
    setLoading(true)
    try {
      const [s, a] = await Promise.allSettled([
        fetchAWSState(),
        fetchAWSActions(),
      ])
      if (s.status === "fulfilled") setAwsState(s.value.data)
      if (a.status === "fulfilled") setActions(a.value.data ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t) }, [])

  const CapacityBar = ({ current, max }: { current: number; max: number }) => (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-cyan rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${(current / max) * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
      <span className="text-[10px] font-mono text-textMuted w-12 text-right">{current}/{max}</span>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text">AWS Resources{sourceSuffix}</h2>
        <div className="flex items-center gap-2">
          <span className={sourceBadge}>{sourceLabel}</span>
          <button onClick={load} className="text-textMuted hover:text-text transition-colors">
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Server size={13} className="text-cyan" />
            <span className="card-title">Auto Scaling Groups</span>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-16 bg-surfaceHigh rounded" />
            </div>
          ) : awsState?.asgs?.length > 0 ? (
            awsState.asgs.map((asg: any, i: number) => (
              <div key={i} className="bg-surfaceHigh rounded-md p-3 space-y-2">
                <p className="text-xs font-mono font-semibold text-text">{asg.name}</p>
                <CapacityBar current={asg.desired} max={asg.max} />
                <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-textMuted">
                  <span>min: <span className="text-text">{asg.min}</span></span>
                  <span>desired: <span className="text-cyan">{asg.desired}</span></span>
                  <span>max: <span className="text-text">{asg.max}</span></span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-textMuted text-xs font-mono">No ASGs found</p>
          )}
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Layers size={13} className="text-green" />
            <span className="card-title">ECS Services</span>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-16 bg-surfaceHigh rounded" />
            </div>
          ) : awsState?.ecs ? (
            Object.entries(awsState.ecs).map(([cluster, services]: any) => (
              <div key={cluster}>
                <p className="text-[10px] font-mono text-textMuted mb-2">{cluster}</p>
                {services.map((svc: any, i: number) => (
                  <div key={i} className="bg-surfaceHigh rounded-md p-3 mb-2 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="badge badge-green">{svc.status}</span>
                      <span className="text-[10px] font-mono text-textMuted">{svc.pending > 0 ? `${svc.pending} pending` : "stable"}</span>
                    </div>
                    <CapacityBar current={svc.running} max={Math.max(svc.desired, 1)} />
                    <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-textMuted">
                      <span>desired: <span className="text-cyan">{svc.desired}</span></span>
                      <span>running: <span className="text-green">{svc.running}</span></span>
                    </div>
                  </div>
                ))}
              </div>
            ))
          ) : (
            <p className="text-textMuted text-xs font-mono">No ECS services found</p>
          )}
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Box size={13} className="text-purple" />
            <span className="card-title">EKS Node Groups</span>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-16 bg-surfaceHigh rounded" />
            </div>
          ) : awsState?.eks ? (
            Object.entries(awsState.eks).map(([cluster, nodegroups]: any) => (
              <div key={cluster}>
                <p className="text-[10px] font-mono text-textMuted mb-2">{cluster}</p>
                {nodegroups.map((ng: any, i: number) => (
                  <div key={i} className="bg-surfaceHigh rounded-md p-3 mb-2 space-y-2">
                    <span className="badge badge-purple">{ng.status}</span>
                    <CapacityBar current={ng.desired} max={ng.max} />
                    <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-textMuted">
                      <span>min: <span className="text-text">{ng.min}</span></span>
                      <span>desired: <span className="text-purple">{ng.desired}</span></span>
                      <span>max: <span className="text-text">{ng.max}</span></span>
                    </div>
                    {ng.instance_types?.length > 0 && (
                      <p className="text-[10px] font-mono text-textMuted">{ng.instance_types.join(", ")}</p>
                    )}
                  </div>
                ))}
              </div>
            ))
          ) : (
            <p className="text-textMuted text-xs font-mono">No EKS clusters found</p>
          )}
        </div>
      </div>

      <div className="card p-5">
        <span className="card-title block mb-4">
          Action Log{source === "real" ? " (simulated)" : ""}
        </span>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {actions.length === 0 ? (
            <p className="text-textMuted text-xs font-mono">No actions logged yet</p>
          ) : (
            actions.slice(0, 10).map((a: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center gap-3 bg-surfaceHigh rounded px-4 py-2"
              >
                <span className="font-mono text-[10px] text-textDim shrink-0 w-20">
                  {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "--"}
                </span>
                <span className="badge badge-cyan shrink-0">{a.resource_type?.toUpperCase()}</span>
                <span className={`font-mono text-xs font-medium ${a.action === "scale_up" ? "text-cyan" : a.action === "scale_down" ? "text-amber" : "text-green"}`}>
                  {a.action}
                </span>
                <span className="font-mono text-xs text-textMuted flex-1 truncate">{a.target}</span>
                {a.previous !== undefined && (
                  <span className="font-mono text-xs text-textMuted shrink-0">{a.previous} → {a.new}</span>
                )}
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}