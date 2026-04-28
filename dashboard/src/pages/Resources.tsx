import { useEffect, useState } from "react";
import { fetchAzureCost, fetchAzureVMSSStatus, fetchMetrics } from "@/services/api";

export default function Resources() {
  const [azure, setAzure] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [latest, setLatest] = useState<any>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const [az, st, m] = await Promise.all([
        fetchAzureCost(),
        fetchAzureVMSSStatus(),
        fetchMetrics(),
      ]);
      setAzure(az.data);
      setStatus(st.data);
      const metrics = m.data?.metrics ?? [];
      setLatest(metrics.length ? metrics[metrics.length - 1] : null);
    } catch {}
  }

  const creditsRem = azure ? 100 - azure.amount : 0;
  const creditsPct = Math.max(0, (creditsRem / 100) * 100);
  const creditsColor = creditsRem > 20 ? "bg-emerald-400" : creditsRem > 0 ? "bg-amber-400" : "bg-red-400";

  const vmss = status?.vmss;
  const statusLabel = status?.status ?? "not_configured";

  return (
    <div className="p-10 fade-in">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Azure VMSS Service</h1>
          <p className="text-slate-400 mt-1.5 text-sm">Selected scale set, subscription context, and live signal health</p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-emerald-400/10 text-emerald-400 text-[10px] font-bold rounded-full border border-emerald-400/20 uppercase">Azure Monitor</span>
        </div>
      </header>

      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Selected VMSS */}
        <div className="glass-panel p-7 rounded-xl col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">cloud</span>
              <h3 className="text-base font-bold headline text-white">Selected VM Scale Set</h3>
            </div>
            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase border ${
              statusLabel === "ok"
                ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                : statusLabel === "degraded"
                ? "border-amber-400/20 bg-amber-400/10 text-amber-300"
                : "border-slate-500/20 bg-slate-500/10 text-slate-300"
            }`}>
              {statusLabel === "ok" ? "Live" : statusLabel === "degraded" ? "Degraded" : "Not connected"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#272a31]/40 rounded-xl p-4 border border-[#3c4a46]/10">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">Resource</div>
              <div className="text-sm font-semibold text-white font-mono break-words">
                {vmss?.resource_group && vmss?.name ? `${vmss.resource_group}/${vmss.name}` : "—"}
              </div>
              <div className="text-[10px] text-slate-500 mt-2 font-mono break-words">
                {vmss?.resource_id ?? "—"}
              </div>
            </div>
            <div className="bg-[#272a31]/40 rounded-xl p-4 border border-[#3c4a46]/10">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">Subscription</div>
              <div className="text-sm font-semibold text-white font-mono break-words">{vmss?.subscription_id ?? "—"}</div>
              <div className="text-[9px] text-slate-600 mt-2 uppercase font-bold tracking-widest">Region</div>
              <div className="text-xs text-slate-300 font-mono">{vmss?.location ?? "—"}</div>
            </div>
          </div>

          {(status?.last_validation_error || status?.last_metrics_error) && (
            <div className="mt-4 p-4 rounded-xl border border-amber-400/20 bg-amber-400/10 text-amber-200/80 text-xs font-mono break-words">
              {status?.last_metrics_error ?? status?.last_validation_error}
            </div>
          )}
        </div>

        {/* Azure Cost */}
        <div className="glass-panel p-7 rounded-xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-emerald-400">payments</span>
            <h3 className="text-base font-bold headline text-white">Azure Cost (MTD)</h3>
          </div>
          <div className="text-5xl font-extrabold headline text-emerald-400 mb-2">
            {azure ? "$" + azure.amount?.toFixed(2) : "—"}
          </div>
          <div className="text-xs text-slate-500 mb-4">
            {azure ? `${azure.period_start} → ${azure.period_end}` : "—"}
          </div>
          <div className="h-2 bg-[#1d2026] rounded-full overflow-hidden mb-1">
            <div className={`h-full rounded-full transition-all duration-700 ${creditsColor}`} style={{ width: creditsPct + "%" }}></div>
          </div>
          <div className="text-[10px] text-slate-500">
            {azure ? (creditsRem > 0 ? `$${creditsRem.toFixed(2)} credits remaining` : `$${Math.abs(creditsRem).toFixed(2)} over budget`) : "—"}
          </div>
        </div>
      </div>

      <div className="glass-panel p-7 rounded-xl">
        <div className="flex items-center gap-2 mb-5">
          <span className="material-symbols-outlined text-secondary">monitoring</span>
          <h3 className="text-base font-bold headline text-white">Latest captured signal</h3>
        </div>
        {!latest ? (
          <div className="text-slate-600 text-xs">No metrics stored yet.</div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#272a31]/40 rounded-xl p-4 border border-[#3c4a46]/10">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">CPU</div>
              <div className="text-2xl font-extrabold headline text-primary">{latest.cpu_usage.toFixed(2)}%</div>
              <div className="text-[10px] text-slate-600 font-mono mt-2">{new Date(latest.timestamp).toLocaleString()}</div>
            </div>
            <div className="bg-[#272a31]/40 rounded-xl p-4 border border-[#3c4a46]/10">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">Network In (KB)</div>
              <div className="text-2xl font-extrabold headline text-secondary">
                {typeof latest.request_load === "number" ? latest.request_load.toFixed(2) : "—"}
              </div>
              <div className="text-[10px] text-slate-600 mt-2">Proxy value derived from Azure Monitor “Network In”</div>
            </div>
            <div className="bg-[#272a31]/40 rounded-xl p-4 border border-[#3c4a46]/10">
              <div className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-2">Memory</div>
              <div className="text-2xl font-extrabold headline text-amber-400">
                {typeof latest.memory_usage === "number" ? latest.memory_usage.toFixed(2) + "%" : "N/A"}
              </div>
              <div className="text-[10px] text-slate-600 mt-2">Guest-level metrics required for VMSS memory%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}