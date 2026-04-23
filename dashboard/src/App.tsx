import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import MainLayout from "./layout/MainLayout";
import { runOptimizer } from "./services/api";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Overview from "./pages/Overview";
import LiveInfra from "./pages/LiveInfra";
import Intelligence from "./pages/Intelligence";
import AIOptimizer from "./pages/AIOptimizer";
import Governance from "./pages/Governance";
import Explainability from "./pages/Explainability";
import Resources from "./pages/Resources";

type AuthPage = "landing" | "login" | "register" | "dashboard";
type DashPage = "overview" | "liveinfra" | "intelligence" | "aioptimizer" | "governance" | "explainability" | "resources";

function AppInner() {
  const { user, logout } = useAuth();
  const [authPage, setAuthPage] = useState<AuthPage>("landing");
  const [dashPage, setDashPage] = useState<DashPage>("overview");
  const [refreshKey, setRefreshKey] = useState(0);

  function handleNavigate(page: AuthPage) {
    setAuthPage(page);
  }

  function handleRefresh() {
    setRefreshKey(k => k + 1);
  }

  async function handleRunOptimizer() {
    try { await runOptimizer(); handleRefresh(); } catch {}
  }

  function handleLogout() {
    logout();
    setAuthPage("landing");
  }

  if (authPage === "login") return <Login onNavigate={handleNavigate} />;
  if (authPage === "register") return <Register onNavigate={handleNavigate} />;

  if (!user || authPage === "landing") {
    return <Landing onNavigate={handleNavigate} />;
  }

  const renderDashPage = () => {
    switch (dashPage) {
      case "overview":       return <Overview key={refreshKey} onNavigate={p => setDashPage(p as DashPage)} onRunOptimizer={handleRunOptimizer} />;
      case "liveinfra":      return <LiveInfra key={refreshKey} />;
      case "intelligence":   return <Intelligence key={refreshKey} />;
      case "aioptimizer":    return <AIOptimizer key={refreshKey} onRunOptimizer={handleRunOptimizer} />;
      case "governance":     return <Governance key={refreshKey} />;
      case "explainability": return <Explainability key={refreshKey} />;
      case "resources":      return <Resources key={refreshKey} />;
      default:               return <Overview key={refreshKey} onNavigate={p => setDashPage(p as DashPage)} onRunOptimizer={handleRunOptimizer} />;
    }
  };

  return (
    <MainLayout setPage={p => setDashPage(p as DashPage)} currentPage={dashPage} onRefresh={handleRefresh} onLogout={handleLogout} user={user}>
      {renderDashPage()}
    </MainLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}