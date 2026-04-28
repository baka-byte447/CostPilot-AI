import { useState, useEffect } from "react";
import { fetchAzureVMSSStatus, fetchSafetyStatus } from "@/services/api";

interface TopbarProps {
  onRunOptimizer: () => void;
  onLoadAll: () => void;
  user?: { name: string; email: string } | null;
  onLogout?: () => void;
}

export default function Topbar({ onRunOptimizer, onLoadAll, user, onLogout }: TopbarProps) {
  const [cooldown, setCooldown] = useState<{ active: boolean; remaining: number }>({
    active: false,
    remaining: 0,
  });
  const [azureStatus, setAzureStatus] = useState<any>(null);

  useEffect(() => {
    checkCooldown();
    refreshAzureStatus();
    const interval = setInterval(checkCooldown, 5000);
    return () => clearInterval(interval);
  }, []);

  async function checkCooldown() {
    try {
      const res = await fetchSafetyStatus();
      const s = res.data;
      if (s?.cooldown_active) {
        setCooldown({ active: true, remaining: s.cooldown_remaining });
      } else {
        setCooldown({ active: false, remaining: 0 });
      }
    } catch {}
  }

  async function refreshAzureStatus() {
    try {
      const res = await fetchAzureVMSSStatus();
      setAzureStatus(res.data);
    } catch {
      setAzureStatus(null);
    }
  }

  const vmssLabel =
    azureStatus?.vmss?.resource_group && azureStatus?.vmss?.name
      ? `${azureStatus.vmss.resource_group}/${azureStatus.vmss.name}`
      : "No VMSS selected";
  const subId = azureStatus?.vmss?.subscription_id;
  const subShort = subId ? `${String(subId).slice(0, 8)}…${String(subId).slice(-4)}` : "—";
  const status = azureStatus?.status ?? "not_configured";

  return (
    <header className="fixed top-0 right-0 left-64 h-14 bg-[#10131a]/80 backdrop-blur-xl border-b border-[#3cddc7]/10 flex items-center justify-between px-8 z-40">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase">
          <span className="px-3 py-1 rounded-full border border-white/10 bg-white/5 text-slate-200">
            VMSS: <span className="font-mono font-semibold normal-case">{vmssLabel}</span>
          </span>
          <span className="px-3 py-1 rounded-full border border-white/10 bg-white/5 text-slate-300">
            Subscription: <span className="font-mono normal-case">{subShort}</span>
          </span>
          <span
            className={`px-3 py-1 rounded-full border text-[10px] font-bold uppercase ${
              status === "ok"
                ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                : status === "degraded"
                ? "border-amber-400/20 bg-amber-400/10 text-amber-300"
                : "border-slate-500/20 bg-slate-500/10 text-slate-300"
            }`}
            title={azureStatus?.last_metrics_error ?? azureStatus?.last_validation_error ?? ""}
          >
            {status === "ok" ? "Live" : status === "degraded" ? "Degraded" : "Not connected"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {cooldown.active && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-400/10 border border-amber-400/20 rounded-full text-amber-400 text-[10px] font-bold uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 breathing-pulse"></span>
            Cooldown <span>{cooldown.remaining}s</span>
          </div>
        )}

        <button
          onClick={onLoadAll}
          className="px-3 py-1.5 rounded-full border border-[#3c4a46]/20 text-primary text-xs font-semibold hover:bg-primary/10 transition-all"
        >
          Refresh
        </button>

        <button
          onClick={onRunOptimizer}
          className="px-3 py-1.5 rounded-full bg-primary text-on-primary text-xs font-bold hover:brightness-110 transition-all"
        >
          Apply
        </button>

        <div className="h-5 w-px bg-[#3c4a46]/20 mx-1"></div>

        <button
          onClick={refreshAzureStatus}
          className="material-symbols-outlined text-slate-500 hover:text-primary cursor-pointer transition-colors text-xl"
          title="Refresh Azure service status"
        >
          sync
        </button>

        <button
          onClick={onLogout}
          title={user ? `Sign out (${user.email})` : "Sign out"}
          className="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary text-xs font-bold hover:bg-primary/30 transition-colors cursor-pointer"
        >
          {user ? user.name.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase() : "?"}
        </button>
      </div>
    </header>
  );
}