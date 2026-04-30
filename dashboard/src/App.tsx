import { useState } from "react";
import MainLayout from "./layout/MainLayout";
import { runOptimizer } from "./services/api";
import { AuthProvider, useAuth } from "./services/AuthContext";
import CustomCursor from "./components/CustomCursor";

import LoginPage from "./pages/LoginPage";
import Overview from "./pages/Overview";
import LiveInfra from "./pages/LiveInfra";
import Intelligence from "./pages/Intelligence";
import AIOptimizer from "./pages/AIOptimizer";
import Governance from "./pages/Governance";
import Explainability from "./pages/Explainability";
import Resources from "./pages/Resources";
import ConnectAWS from "./pages/ConnectAWS";

function AppShell() {
  const { user, loading } = useAuth();
  const [page, setPage] = useState("overview");
  const [refreshKey, setRefreshKey] = useState(0);

  function handleRefresh() {
    setRefreshKey(k => k + 1);
  }

  const renderPage = () => {
    switch (page) {
      case "overview": return <Overview key={refreshKey} onNavigate={setPage} onRunOptimizer={handleRunOptimizer} />;
      case "liveinfra": return <LiveInfra key={refreshKey} />;
      case "intelligence": return <Intelligence key={refreshKey} />;
      case "aioptimizer": return <AIOptimizer key={refreshKey} onRunOptimizer={handleRunOptimizer} />;
      case "governance": return <Governance key={refreshKey} />;
      case "explainability": return <Explainability key={refreshKey} />;
      case "resources": return <Resources key={refreshKey} />;
      case "connectaws": return <ConnectAWS key={refreshKey} />;
      default: return <Overview key={refreshKey} onNavigate={setPage} onRunOptimizer={handleRunOptimizer} />;
    }
  };

  async function handleRunOptimizer() {
    try {
      await runOptimizer();
      handleRefresh();
    } catch {}
  }

  // Show a loading spinner while restoring the session
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f1012] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center shadow-[0_0_30px_rgba(233,79,55,0.2)]">
            <span className="material-symbols-outlined text-primary text-2xl animate-spin">progress_activity</span>
          </div>
          <span className="text-xs text-textDim font-bold uppercase tracking-wider">Loading CostPilot...</span>
        </div>
      </div>
    );
  }

  // Not logged in → show login page
  if (!user) {
    return <LoginPage />;
  }

  // Logged in → show dashboard
  return (
    <MainLayout setPage={setPage} currentPage={page} onRefresh={handleRefresh}>
      {renderPage()}
      <CustomCursor />
    </MainLayout>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}

export default App;