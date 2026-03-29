import { useEffect, useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { RefreshCw, Cpu, HardDrive, Activity, Zap, ShieldCheck } from "lucide-react"

import Sidebar from "./components/dashboard/Sidebar"
import AnimatedCharts from "./components/dashboard/AnimatedCharts"
import MetricCard from "./components/dashboard/MetricCard"
import CostPanel from "./components/CostPanel"
import RLPanel from "./components/RLPanel"
import SafetyPanel from "./components/SafetyPanel"
import ExplainPanel from "./components/ExplainPanel"
import AWSStatePanel from "./components/AWSStatePanel"
import AzurePanel from "./components/AzurePanel"

import {
  fetchMetrics,
  fetchCostForecast,
  fetchRLDecision,
  fetchSafetyStatus,
  fetchAzureCost,
} from "./services/api"

const TAB_ANIM = {
  initial:  { opacity: 0, y: 8 },
  animate:  { opacity: 1, y: 0 },
  exit:     { opacity: 0, y: -8 },
  transition: { duration: 0.2 },
}

function App() {
  const [currentTab, setCurrentTab] = useState("overview")
  const [metrics, setMetrics]       = useState<any[]>([])
  const [cost, setCost]             = useState<any>(null)
  const [rlDecision, setRLDecision] = useState<any>(null)
  const [safety, setSafety]         = useState<any>(null)
  const [azureCost, setAzureCost]   = useState<any>(null)
  const [loading, setLoading]       = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadOverviewData = useCallback(async () => {
    setLoading(true)
    try {
      const results = await Promise.allSettled([
        fetchMetrics(),
        fetchCostForecast(),
        fetchRLDecision(),
        fetchSafetyStatus(),
        fetchAzureCost(),
      ])

      if (results[0].status === "fulfilled") {
        const data = results[0].value.data
        if (Array.isArray(data)) setMetrics(data.slice(-20))
      }
      if (results[1].status === "fulfilled") setCost(results[1].value.data)
      if (results[2].status === "fulfilled") setRLDecision(results[2].value.data?.decision)
      if (results[3].status === "fulfilled") setSafety(results[3].value.data)
      if (results[4].status === "fulfilled") setAzureCost(results[4].value.data)

      setLastUpdated(new Date())
    } catch (err) {
      console.error("Failed to load overview data", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadOverviewData()
    const interval = setInterval(() => {
      fetchMetrics()
        .then(res => { if (Array.isArray(res.data)) setMetrics(res.data.slice(-20)) })
        .catch(() => {})
    }, 15000)
    return () => clearInterval(interval)
  }, [loadOverviewData])

  const latestMetric  = metrics.length > 0 ? metrics[metrics.length - 1] : null
  const rlAction      = rlDecision?.action ?? "--"
  const rlActionColor = rlAction === "scale_up" ? "cyan" : rlAction === "scale_down" ? "amber" : "green"

  const TAB_TITLE: Record<string, string> = {
    overview:  "System Overview",
    metrics:   "Live Metrics",
    cost:      "Cost Intelligence",
    rl:        "RL Agent",
    safety:    "Safety Engine",
    explain:   "Explainability",
    aws:       "AWS Resources",
    azure:     "Azure Resources",
  }

  return (
    <div className="flex min-h-screen bg-bg text-text font-sans">
      <Sidebar currentTab={currentTab} setTab={setCurrentTab} />

      <main className="flex-1 ml-56 flex flex-col min-h-screen">
        <header className="h-12 bg-surface border-b border-surfaceBorder flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center gap-2 text-[11px] font-mono text-textMuted">
            <span className="text-textDim">nimbusopt</span>
            <span>/</span>
            <span className="text-text">{TAB_TITLE[currentTab] ?? currentTab}</span>
          </div>

          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-[10px] font-mono text-textDim hidden md:block">
                updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            {safety?.cooldown_active && (
              <span className="badge badge-amber flex items-center gap-1">
                <ShieldCheck size={9} />COOLDOWN {safety.cooldown_remaining}s
              </span>
            )}
            <button
              onClick={loadOverviewData}
              className="flex items-center gap-1.5 text-[11px] font-mono text-textMuted hover:text-text transition-colors px-2 py-1 rounded hover:bg-surfaceHigh"
            >
              <RefreshCw size={11} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>
        </header>

        <div className="flex-1 p-6 max-w-[1400px] w-full mx-auto">
          <AnimatePresence mode="wait">
            {currentTab === "overview" && (
              <motion.div key="overview" {...TAB_ANIM} className="space-y-5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    title="CPU Usage"
                    value={latestMetric ? `${latestMetric.cpu_usage.toFixed(1)}%` : "--"}
                    sub={latestMetric ? `${latestMetric.cpu_usage > 70 ? "HIGH LOAD" : "normal"}` : undefined}
                    loading={loading}
                    accent="cyan"
                    icon={<Cpu size={13} />}
                    badge={latestMetric?.cpu_usage > 80 ? "HIGH" : undefined}
                    badgeVariant="red"
                  />
                  <MetricCard
                    title="Memory Usage"
                    value={latestMetric ? `${latestMetric.memory_usage.toFixed(1)}%` : "--"}
                    loading={loading}
                    accent="green"
                    icon={<HardDrive size={13} />}
                  />
                  <MetricCard
                    title="RL Decision"
                    value={rlAction.replace("_", " ").toUpperCase()}
                    sub={rlDecision ? `reward: ${rlDecision.reward}` : undefined}
                    loading={loading}
                    accent={rlActionColor as any}
                    icon={<Zap size={13} />}
                    badge={rlDecision?.safety?.blocked ? "OVERRIDDEN" : undefined}
                    badgeVariant="amber"
                  />
                  <MetricCard
                    title="Azure MTD Cost"
                    value={azureCost ? `$${azureCost.amount?.toFixed(2)}` : "--"}
                    sub={azureCost ? `$${(100 - azureCost.amount).toFixed(2)} credits left` : undefined}
                    loading={loading}
                    accent="amber"
                    icon={<Activity size={13} />}
                  />
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 h-[380px]">
                  <div className="xl:col-span-2 h-full">
                    {loading && metrics.length === 0 ? (
                      <div className="card w-full h-full flex items-center justify-center">
                        <div className="flex items-center gap-2 text-textMuted font-mono text-sm">
                          <RefreshCw size={16} className="animate-spin" />
                          Loading telemetry...
                        </div>
                      </div>
                    ) : (
                      <AnimatedCharts data={metrics} title="Cluster Telemetry Timeline" />
                    )}
                  </div>

                  <div className="xl:col-span-1 h-full flex flex-col gap-4">
                    <div className="flex-1">
                      <CostPanel cost={cost} />
                    </div>

                    <div className="card p-5 flex-1">
                      <span className="text-[11px] font-mono font-medium text-textMuted uppercase tracking-wider block mb-3">
                        RL State Buckets
                      </span>
                      {rlDecision?.state ? (
                        <div className="space-y-3">
                          {[
                            { label: "CPU Bucket",     value: rlDecision.state.cpu_bucket,     max: 9, color: "bg-cyan" },
                            { label: "Memory Bucket",  value: rlDecision.state.memory_bucket,  max: 9, color: "bg-green" },
                            { label: "Request Bucket", value: rlDecision.state.request_bucket, max: 9, color: "bg-amber" },
                          ].map(b => (
                            <div key={b.label}>
                              <div className="flex justify-between text-[10px] font-mono text-textMuted mb-1">
                                <span>{b.label}</span>
                                <span className="text-text">{b.value}/9</span>
                              </div>
                              <div className="h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
                                <motion.div
                                  className={`h-full ${b.color} rounded-full`}
                                  initial={{ width: 0 }}
                                  animate={{ width: `${((b.value + 1) / 10) * 100}%` }}
                                  transition={{ duration: 0.6 }}
                                />
                              </div>
                            </div>
                          ))}
                          <div className="pt-2 border-t border-surfaceBorder">
                            <p className="text-[10px] font-mono text-textMuted">
                              ε = <span className="text-text">{rlDecision.epsilon}</span>
                              <span className="mx-2">·</span>
                              replicas = <span className="text-cyan">{rlDecision.replicas}</span>
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2 animate-pulse">
                          {[1,2,3].map(i => <div key={i} className="h-6 bg-surfaceHigh rounded" />)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {currentTab === "metrics" && (
              <motion.div key="metrics" {...TAB_ANIM} className="space-y-5">
                <div className="h-[440px]">
                  <AnimatedCharts data={metrics} title="Live Metrics — CPU & Memory" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MetricCard title="Latest CPU"    value={latestMetric ? `${latestMetric.cpu_usage.toFixed(2)}%` : "--"}    accent="cyan"   loading={loading} />
                  <MetricCard title="Latest Memory" value={latestMetric ? `${latestMetric.memory_usage.toFixed(2)}%` : "--"} accent="green"  loading={loading} />
                  <MetricCard title="Request Load"  value={latestMetric ? latestMetric.request_load?.toFixed(4) : "--"}      accent="amber"  loading={loading} sub="req/s" />
                </div>
              </motion.div>
            )}

            {currentTab === "cost" && (
              <motion.div key="cost" {...TAB_ANIM}>
                <AzurePanel />
              </motion.div>
            )}

            {currentTab === "rl" && (
              <motion.div key="rl" {...TAB_ANIM}>
                <RLPanel />
              </motion.div>
            )}

            {currentTab === "safety" && (
              <motion.div key="safety" {...TAB_ANIM}>
                <SafetyPanel />
              </motion.div>
            )}

            {currentTab === "explain" && (
              <motion.div key="explain" {...TAB_ANIM}>
                <ExplainPanel />
              </motion.div>
            )}

            {currentTab === "aws" && (
              <motion.div key="aws" {...TAB_ANIM}>
                <AWSStatePanel />
              </motion.div>
            )}

            {currentTab === "azure" && (
              <motion.div key="azure" {...TAB_ANIM}>
                <AzurePanel />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}

export default App