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
        <h1 className="text-4xl font-extrabold headline text-text tracking-tighter">Safety & Governance</h1>
        <p className="text-textMuted mt-1.5 text-sm">SLO enforcement · Constraint engine · Cooldown management</p>
      </header>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Constraint Engine */}
        <div className="glass-panel p-7">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-primary">shield</span>
            <h3 className="text-base font-bold headline text-text">Constraint Engine</h3>
          </div>

          <div className="rounded-[14px] p-5 mb-5 border border-[rgba(255,255,255,0.07)] bg-[rgba(255,255,255,0.03)]">
            <div className="flex items-center gap-2 mb-3">
              <span className={`material-symbols-outlined text-sm text-primary ${safety ? "" : "animate-spin"}`}>
                {safety ? (cooldownActive ? "timer" : "check_circle") : "progress_activity"}
              </span>
              <span className="text-xs font-bold uppercase tracking-widest text-primary">
                {safety ? (cooldownActive ? "COOLDOWN ACTIVE" : "READY") : "Loading..."}
              </span>
            </div>
            <div className="h-1.5 bg-[rgba(255,255,255,0.08)] rounded-full overflow-hidden mb-2">
              <div
                className="h-full rounded-full transition-all duration-1000 bg-[linear-gradient(90deg,_#E94F37,_#ff6b4a)] shadow-[0_0_10px_rgba(233,79,55,0.6)]"
                style={{ width: cooldownPct + "%" }}
              ></div>
            </div>
            <div className="text-[10px] text-textMuted">
              {cooldownActive ? `${cooldownRemaining}s remaining` : "No cooldown active"}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {["CPU SLO", "Memory SLO", "Request SLO"].map((label) => (
              <div key={label} className="rounded-[12px] p-3 text-center bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.07)]">
                <div className="text-primary font-bold text-sm">✓</div>
                <div className="text-[10px] text-textMuted mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* SLO Configuration */}
        <div className="glass-panel p-7">
          <h3 className="text-base font-bold headline text-text mb-5">SLO Configuration</h3>
          <div className="space-y-2">
            {sloItems.length === 0 ? (
              <div className="text-textMuted text-xs">Loading...</div>
            ) : (
              sloItems.map(([k, v]) => (
                <div key={k} className="flex justify-between items-center bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.07)] rounded-[12px] px-4 py-2.5">
                  <span className="text-[11px] font-medium text-textMuted">{k}</span>
                  <span className="text-[11px] font-bold text-primary font-mono">{String(v)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Latest Safety Decision */}
      <div className="glass-panel p-7">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-base font-bold headline text-text">Latest Safety Decision</h3>
          <span className="px-2 py-0.5 text-[9px] font-bold uppercase rounded-full badge-neutral">
            {overridden ? "Overridden" : "Approved"}
          </span>
        </div>
        <p className="text-sm text-textMuted leading-relaxed bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.07)] p-5 rounded-[12px]">
          {exp?.explanation ?? "Loading..."}
        </p>
        {exp && (
          <div className="flex gap-6 mt-4 text-[10px] font-mono text-textMuted">
            <span>action: <span className="text-text">{exp.action}</span></span>
            <span>cpu: <span className="text-primary">{exp.cpu}%</span></span>
            <span>memory: <span className="text-primary">{exp.memory}%</span></span>
            <span>replicas: <span className="text-primary">{exp.replicas}</span></span>
          </div>
        )}
      </div>
    </div>
  );
}