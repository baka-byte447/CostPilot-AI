import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { runOptimizer } from "@/services/api";

interface MainLayoutProps {
  children: React.ReactNode;
  setPage: (page: string) => void;
  currentPage: string;
  onRefresh?: () => void;
  onLogout?: () => void;
  user?: { name: string; email: string } | null;
}

export default function MainLayout({ children, setPage, currentPage, onRefresh, onLogout, user }: MainLayoutProps) {
  async function handleRunOptimizer() {
    try {
      await runOptimizer();
      if (onRefresh) onRefresh();
    } catch {}
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar setPage={setPage} currentPage={currentPage} onRunOptimizer={handleRunOptimizer} onLogout={onLogout} />
      <div className="flex-1 ml-64">
        <Topbar onRunOptimizer={handleRunOptimizer} onLoadAll={onRefresh || (() => {})} user={user} onLogout={onLogout} />
        <main className="mt-14 min-h-screen bg-surface">
          {children}
        </main>
      </div>
    </div>
  );
}