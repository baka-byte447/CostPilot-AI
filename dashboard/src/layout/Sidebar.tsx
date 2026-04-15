interface SidebarProps {
  setPage: (page: string) => void;
  currentPage: string;
  onRunOptimizer: () => void;
}

const navItems = [
  { id: "overview", icon: "dashboard", label: "Overview", group: "Platform" },
  { id: "liveinfra", icon: "hub", label: "Live Infra", group: "Platform" },
  { id: "intelligence", icon: "insights", label: "Intelligence", group: "Platform" },
  { id: "aioptimizer", icon: "psychology", label: "AI Optimizer", group: "AI Engine" },
  { id: "governance", icon: "gavel", label: "Governance", group: "AI Engine" },
  { id: "explainability", icon: "visibility", label: "Explainability", group: "AI Engine" },
  { id: "resources", icon: "cloud", label: "Resources", group: "Infrastructure" },
];

export default function Sidebar({ setPage, currentPage, onRunOptimizer }: SidebarProps) {
  const groups = ["Platform", "AI Engine", "Infrastructure"];

  return (
    <aside className="flex flex-col fixed left-0 top-0 h-full w-64 bg-[#191c22]/80 backdrop-blur-2xl border-r border-[#3cddc7]/10 shadow-[0_0_64px_rgba(60,221,199,0.04)] z-50 overflow-y-auto">
      <div className="p-7 flex items-center gap-3 border-b border-[#3cddc7]/10">
        <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center shadow-[0_0_20px_rgba(87,241,219,0.3)]">
          <span className="material-symbols-outlined text-on-primary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>hub</span>
        </div>
        <div>
          <div className="text-[18px] font-bold text-[#57f1db] tracking-tighter font-headline">CostPilot</div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-600 font-bold">Enterprise AI</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1">
        {groups.map((group) => (
          <div key={group}>
            <p className="px-4 text-[9px] font-bold text-slate-600 uppercase tracking-widest mb-2 mt-5 first:mt-0">{group}</p>
            {navItems
              .filter((item) => item.group === group)
              .map((item) => (
                <button
                  key={item.id}
                  onClick={() => setPage(item.id)}
                  className={`nav-item w-full text-left flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold font-headline transition-all ${
                    currentPage === item.id ? "nav-active" : "nav-inactive"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                  {item.label}
                </button>
              ))}
          </div>
        ))}
      </nav>

      <div className="p-5 border-t border-[#3cddc7]/10">
        <button
          onClick={onRunOptimizer}
          className="w-full py-3 rounded-full bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold text-sm shadow-[0_0_20px_rgba(87,241,219,0.25)] hover:opacity-90 active:scale-95 transition-all"
        >
          Apply Changes
        </button>
      </div>
    </aside>
  );
}