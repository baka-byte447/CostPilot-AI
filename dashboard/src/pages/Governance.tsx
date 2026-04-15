import { useEffect, useState } from "react";
import { fetchSafetyStatus, fetchSLOConfig, fetchRLExplanation } from "@/services/api";

export default function Governance() {
  const [safety, setSafety] = useState<any>(null);
  const [slo, setSlo] = useState<any>(null);
  const [explanation, setExplanation] = useState<any>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const [s, sl, exp] = await Promise.all([
        fetchSafetyStatus(),
        fetchSLOConfig(),
        fetchRLExplanation(),
      ]);
      setSafety(s.data);
      setSlo(sl.data);
      setExplanation(exp.data);
    } catch {}
  }

  const cooldownActive = safety?.cooldown_active;
  const cooldownRemaining = safety?.cooldown_remaining ?? 0;
  const cooldownTotal = slo?.cooldown_seconds ?? 30;
  const cooldownPct = cooldownActive ? (cooldownRemaining / cooldownTotal) * 100 : 100;

  const exp = explanation?.explanation;
  const overridden = exp?.safety_overridden;

  const sloItems = slo ? [
    ["Max CPU %", slo.max_cpu_pct + "%"],
    ["Max Memory %", slo.max_memory_pct + "%"],
    ["Max Requests/s", slo.max_request_load + "/s"],
    ["Min Replicas", slo.min_replicas],
    ["Max Replicas", slo.max_replicas],
    ["Scale-Down CPU ≤", slo.max_cpu_to_scale_down + "%"],
    ["Scale-Down Mem ≤", slo.max_memory_to_scale_down + "%"],
    ["Cooldown", slo.cooldown_seconds + "s"],
  ] : [];

  return (
    <div className="p-10 fade-in">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Safety & Governance</h1>
        <p className="text-slate-400 mt-1.5 text-sm">SLO enforcement · Constraint engine · Cooldown management</p>
      </header>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Constraint Engine */}
        <div className="glass-panel p-7 rounded-xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-primary">shield</span>
            <h3 className="text-base font-bold headline text-white">Constraint Engine</h3>
          </div>

          <div className={`rounded-xl p-5 mb-5 border ${cooldownActive ? "bg-amber-400/10 border-amber-400/20" : "bg-emerald-400/10 border-emerald-400/20"}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className={`material-symbols-outlined text-sm ${cooldownActive ? "text-amber-400" : "text-emerald-400"}`}>
                {cooldownActive ? "timer" : "check_circle"}
              </span>
              <span className={`text-xs font-bold uppercase tracking-widest ${cooldownActive ? "text-amber-400" : "text-emerald-400"}`}>
                {safety ? (cooldownActive ? "COOLDOWN ACTIVE" : "READY") : "Loading..."}
              </span>
            </div>
            <div className="h-1.5 bg-[#1d2026] rounded-full overflow-hidden mb-2">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${cooldownActive ? "bg-amber-400" : "bg-emerald-400"}`}
                style={{ width: cooldownPct + "%" }}
              ></div>
            </div>
            <div className="text-[10px] text-slate-500">
              {cooldownActive ? `${cooldownRemaining}s remaining` : "No cooldown active"}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {["CPU SLO", "Memory SLO", "Request SLO"].map((label) => (
              <div key={label} className="rounded-xl p-3 text-center bg-emerald-400/10 border border-emerald-400/20">
                <div className="text-emerald-400 font-bold text-sm">✓</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* SLO Configuration */}
        <div className="glass-panel p-7 rounded-xl">
          <h3 className="text-base font-bold headline text-white mb-5">SLO Configuration</h3>
          <div className="space-y-2">
            {sloItems.length === 0 ? (
              <div className="text-slate-600 text-xs">Loading...</div>
            ) : (
              sloItems.map(([k, v]) => (
                <div key={k} className="flex justify-between items-center bg-[#272a31]/40 rounded-xl px-4 py-2.5">
                  <span className="text-[11px] font-medium text-slate-400">{k}</span>
                  <span className="text-[11px] font-bold text-primary font-mono">{String(v)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Latest Safety Decision */}
      <div className="glass-panel p-7 rounded-xl">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-base font-bold headline text-white">Latest Safety Decision</h3>
          <span className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded-full border ${
            overridden
              ? "bg-amber-400/10 text-amber-400 border-amber-400/20"
              : "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
          }`}>
            {overridden ? "Overridden" : "Approved"}
          </span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed bg-[#272a31]/40 p-5 rounded-xl">
          {exp?.explanation ?? "Loading..."}
        </p>
        {exp && (
          <div className="flex gap-6 mt-4 text-[10px] font-mono text-slate-500">
            <span>action: <span className="text-white">{exp.action}</span></span>
            <span>cpu: <span className="text-primary">{exp.cpu}%</span></span>
            <span>memory: <span className="text-secondary">{exp.memory}%</span></span>
            <span>replicas: <span className="text-amber-400">{exp.replicas}</span></span>
          </div>
        )}
      </div>
    </div>
  );
}