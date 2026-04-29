import { useState, useEffect } from "react";
import { fetchSafetyStatus } from "@/services/api";

interface TopbarProps {
  onRunOptimizer: () => void;
  onLoadAll: () => void;
}

export default function Topbar({ onRunOptimizer, onLoadAll }: TopbarProps) {
  const [cooldown, setCooldown] = useState<{ active: boolean; remaining: number }>({
    active: false,
    remaining: 0,
  });

  useEffect(() => {
    checkCooldown();
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

  const handleRefresh = () => {
    onLoadAll();
  };

  const handleRunOptimizer = () => {
    onRunOptimizer();
  };

  return (
    <header className="fixed top-0 right-0 left-64 h-14 bg-[#10131a]/80 backdrop-blur-xl border-b border-[#3cddc7]/10 flex items-center justify-between px-8 z-40">
      <div className="flex items-center gap-6">
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-500 text-sm">search</span>
          <input
            className="bg-[#1d2026] border-none rounded-full py-1.5 pl-9 pr-4 text-xs w-56 focus:outline-none focus:ring-1 ring-[#57f1db]/30 text-on-surface placeholder:text-slate-600"
            placeholder="Global search..."
            type="text"
          />
        </div>
        <nav className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">
          <span className="px-2.5 py-1 rounded-full border border-[#3c4a46]/20 bg-[#1d2026] text-[#57f1db]">
            Live backend
          </span>
          <span>Production / Staging / Dev views are not separate targets yet.</span>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {cooldown.active && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-400/10 border border-amber-400/20 rounded-full text-amber-400 text-[10px] font-bold uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 breathing-pulse"></span>
            Cooldown <span>{cooldown.remaining}s</span>
          </div>
        )}

        <div className="flex items-center gap-1.5 px-3 py-1 glass-panel rounded-full text-primary text-[10px] font-bold uppercase">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary"></span>
          </span>
          Live
        </div>

        <button
          onClick={handleRefresh}
          className="px-3 py-1.5 rounded-full border border-[#3c4a46]/20 text-primary text-xs font-semibold hover:bg-primary/10 transition-all"
        >
          Refresh
        </button>

        <button
          onClick={handleRunOptimizer}
          className="px-3 py-1.5 rounded-full bg-primary text-on-primary text-xs font-bold hover:brightness-110 transition-all"
        >
          Run Optimizer
        </button>

        <div className="h-5 w-px bg-[#3c4a46]/20 mx-1"></div>

        <span className="material-symbols-outlined text-slate-500 hover:text-primary cursor-pointer transition-colors text-xl">notifications</span>
        <span className="material-symbols-outlined text-slate-500 hover:text-primary cursor-pointer transition-colors text-xl">settings</span>

        <div className="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary text-xs font-bold">
          AD
        </div>
      </div>
    </header>
  );
}