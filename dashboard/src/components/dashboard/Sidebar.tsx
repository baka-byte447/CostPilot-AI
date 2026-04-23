import { LayoutDashboard, Activity, Brain, ShieldCheck, MessageSquare, CloudCog, DollarSign, Zap } from "lucide-react"
import type { FC } from "react"

interface SidebarProps {
  currentTab: string
  setTab: (val: string) => void
  user?: { name: string; email: string } | null
  onLogout?: () => void
}

const NAV = [
  {
    group: "PLATFORM",
    items: [
      { id: "overview",     label: "Overview",        icon: LayoutDashboard },
      { id: "metrics",      label: "Live Metrics",    icon: Activity },
      { id: "cost",         label: "Cost Intelligence", icon: DollarSign },
    ]
  },
  {
    group: "AI ENGINE",
    items: [
      { id: "rl",           label: "RL Agent",        icon: Brain },
      { id: "safety",       label: "Safety Engine",   icon: ShieldCheck },
      { id: "explain",      label: "Explainability",  icon: MessageSquare },
    ]
  },
  {
    group: "INFRASTRUCTURE",
    items: [
      { id: "aws",          label: "AWS Resources",   icon: CloudCog },
      { id: "azure",        label: "Azure Resources", icon: CloudCog },
    ]
  },
]

const Sidebar: FC<SidebarProps> = ({ currentTab, setTab, user, onLogout }) => {
  return (
    <aside className="w-56 bg-surface border-r border-surfaceBorder flex flex-col shrink-0 fixed left-0 top-0 bottom-0 z-20">
      <div className="px-4 py-5 border-b border-surfaceBorder">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-cyan/10 border border-cyan/30 flex items-center justify-center">
            <Zap size={14} className="text-cyan" />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-text leading-tight">NimbusOpt</p>
            <p className="text-[10px] text-textMuted font-mono">v0.1.0 · live</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {NAV.map(group => (
          <div key={group.group}>
            <p className="text-[10px] font-mono font-semibold text-textDim tracking-widest px-3 mb-1.5 select-none">
              {group.group}
            </p>
            <div className="space-y-0.5">
              {group.items.map(item => {
                const active = currentTab === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => setTab(item.id)}
                    className={`nav-item ${active ? "nav-item-active" : "nav-item-inactive"}`}
                  >
                    <item.icon size={15} />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-surfaceBorder">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-7 h-7 rounded-full bg-surfaceHigh border border-surfaceBorder flex items-center justify-center text-textMuted text-[11px] font-mono font-semibold select-none">
            {user ? user.name.split(" ").map((w: string) => w[0]).join("").slice(0, 2).toUpperCase() : "CP"}
          </div>
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-text truncate">{user?.name ?? "Guest"}</p>
            <p className="text-[10px] text-textMuted font-mono truncate">{user?.email ?? "not signed in"}</p>
          </div>
        </div>
        {onLogout && (
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg border border-surfaceBorder text-textMuted hover:text-red-400 hover:border-red-400/40 text-[11px] font-mono transition-colors"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Sign Out
          </button>
        )}
      </div>
    </aside>
  )
}

export default Sidebar