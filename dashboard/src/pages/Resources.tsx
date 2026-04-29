import { useEffect, useState } from "react";
import { fetchAzureCost, fetchAzureACI, fetchAWSState } from "@/services/api";

export default function Resources() {
  const [azure, setAzure] = useState<any>(null);
  const [aci, setAci] = useState<any[]>([]);
  const [aws, setAws] = useState<any>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const [az, aciRes, awsRes] = await Promise.all([
        fetchAzureCost(),
        fetchAzureACI(),
        fetchAWSState(),
      ]);
      setAzure(az.data);
      setAci(aciRes.data || []);
      setAws(awsRes.data);
    } catch {}
  }

  const creditsRem = azure ? 100 - azure.amount : 0;
  const creditsPct = Math.max(0, (creditsRem / 100) * 100);
  const creditsColor = creditsRem > 20 ? "bg-emerald-400" : creditsRem > 0 ? "bg-amber-400" : "bg-red-400";

  const awsSource = aws?.source === "real" ? "Real AWS" : "Mock AWS";
  const awsBadgeClass = aws?.source === "real"
    ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
    : "bg-primary/10 text-primary border-primary/20";

  const ecsList = aws ? Object.entries(aws.ecs ?? {}).flatMap(([cluster, svcs]: any) =>
    (svcs as any[]).map((s: any) => ({ ...s, cluster }))
  ) : [];

  const eksList = aws ? Object.entries(aws.eks ?? {}).flatMap(([cluster, ngs]: any) =>
    (ngs as any[]).map((ng: any) => ({ ...ng, cluster }))
  ) : [];

  return (
    <div className="p-10 fade-in">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Infrastructure Resources</h1>
          <p className="text-slate-400 mt-1.5 text-sm">Primary: {awsSource} · Optional: Azure</p>
        </div>
        <div className="flex gap-2">
          <span className={`px-3 py-1 text-[10px] font-bold rounded-full border uppercase ${awsBadgeClass}`}>{awsSource}</span>
          <span className="px-3 py-1 bg-emerald-400/10 text-emerald-400 text-[10px] font-bold rounded-full border border-emerald-400/20 uppercase">Azure (optional)</span>
        </div>
      </header>
      <div className="grid grid-cols-3 gap-6">
        {/* ASG */}
        <div className="glass-panel p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-primary text-sm">dns</span>
            <h3 className="text-sm font-bold headline text-white">Auto Scaling Groups</h3>
          </div>
          <div className="space-y-3">
            {!aws ? (
              <div className="text-slate-600 text-xs">Loading...</div>
            ) : (aws.asgs ?? []).length === 0 ? (
              <div className="text-slate-600 text-xs">No ASGs</div>
            ) : (
              (aws.asgs ?? []).map((a: any, i: number) => (
                <div key={i} className="bg-[#272a31]/40 rounded-xl p-4">
                  <div className="text-sm font-semibold text-white mb-2">{a.name}</div>
                  <div className="h-1 bg-[#1d2026] rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-primary rounded-full" style={{ width: Math.round((a.desired / a.max) * 100) + "%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>min: {a.min}</span>
                    <span className="text-primary">desired: {a.desired}</span>
                    <span>max: {a.max}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ECS */}
        <div className="glass-panel p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-secondary text-sm">layers</span>
            <h3 className="text-sm font-bold headline text-white">ECS Services</h3>
          </div>
          <div className="space-y-3">
            {!aws ? (
              <div className="text-slate-600 text-xs">Loading...</div>
            ) : ecsList.length === 0 ? (
              <div className="text-slate-600 text-xs">No ECS services</div>
            ) : (
              ecsList.map((s: any, i: number) => (
                <div key={i} className="bg-[#272a31]/40 rounded-xl p-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-semibold text-white">{s.cluster}</span>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-secondary/10 text-secondary border border-secondary/20">{s.status}</span>
                  </div>
                  <div className="h-1 bg-[#1d2026] rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-secondary rounded-full" style={{ width: Math.round((s.running / Math.max(s.desired, 1)) * 100) + "%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>running: <span className="text-secondary">{s.running}</span></span>
                    <span>desired: {s.desired}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* EKS */}
        <div className="glass-panel p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-amber-400 text-sm">hub</span>
            <h3 className="text-sm font-bold headline text-white">EKS Node Groups</h3>
          </div>
          <div className="space-y-3">
            {!aws ? (
              <div className="text-slate-600 text-xs">Loading...</div>
            ) : eksList.length === 0 ? (
              <div className="text-slate-600 text-xs">No EKS clusters</div>
            ) : (
              eksList.map((ng: any, i: number) => (
                <div key={i} className="bg-[#272a31]/40 rounded-xl p-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-semibold text-white">{ng.cluster}</span>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-400/10 text-amber-400 border border-amber-400/20">{ng.status}</span>
                  </div>
                  <div className="h-1 bg-[#1d2026] rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-amber-400 rounded-full" style={{ width: Math.round((ng.desired / ng.max) * 100) + "%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>min: {ng.min}</span>
                    <span className="text-amber-400">desired: {ng.desired}</span>
                    <span>max: {ng.max}</span>
                  </div>
                  {ng.instance_types?.length && (
                    <div className="text-[10px] text-slate-600 mt-1">{ng.instance_types.join(", ")}</div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold headline text-white">Azure (Optional)</h2>
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">Optional</span>
        </div>
        <div className="grid grid-cols-2 gap-6">
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

          {/* Azure ACI */}
          <div className="glass-panel p-7 rounded-xl">
            <div className="flex items-center gap-2 mb-5">
              <span className="material-symbols-outlined text-primary">deployed_code</span>
              <h3 className="text-base font-bold headline text-white">Container Instances (ACI)</h3>
            </div>
            <div className="space-y-2 max-h-52 overflow-y-auto">
              {aci.length === 0 ? (
                <div className="text-slate-600 text-xs text-center py-4">No container groups running</div>
              ) : (
                aci.map((g: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-[#272a31]/40 rounded-xl px-4 py-3">
                    <div>
                      <div className="text-sm font-semibold text-white">{g.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{g.location}{g.ip ? " · " + g.ip : ""}</div>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">Running</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}