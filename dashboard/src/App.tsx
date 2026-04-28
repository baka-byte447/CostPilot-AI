import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import MainLayout from "./layout/MainLayout";
import { runOptimizer } from "./services/api";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import CloudSetup from "./pages/CloudSetup";
import Overview from "./pages/Overview";
import AIOptimizer from "./pages/AIOptimizer";
import Resources from "./pages/Resources";

type AuthPage = "landing" | "login" | "register" | "cloud-setup" | "dashboard";
type DashPage = "overview" | "aioptimizer" | "cloud-setup" | "resources";

function AppInner() {
  const { user, logout } = useAuth();
  const [authPage, setAuthPage] = useState<AuthPage>(() => {
    if (typeof window !== "undefined" && localStorage.getItem("costpilot_token")) return "dashboard";
    return "landing";
  });
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
  if (authPage === "register") return <Register onNavigate={page => {
    if (page === "dashboard") {
      setAuthPage("cloud-setup");
    } else {
      handleNavigate(page as AuthPage);
    }
  }} />;
  if (authPage === "cloud-setup") return <CloudSetup onNavigate={handleNavigate} />;

  if (!user || authPage === "landing") {
    return <Landing onNavigate={handleNavigate} />;
  }

  const renderDashPage = () => {
    switch (dashPage) {
      case "overview":       return <Overview key={refreshKey} onNavigate={p => setDashPage(p as DashPage)} onRunOptimizer={handleRunOptimizer} />;
      case "aioptimizer":    return <AIOptimizer key={refreshKey} onRunOptimizer={handleRunOptimizer} />;
      case "cloud-setup":    return <CloudSetup onNavigate={(p: any) => {
        if (p === "dashboard") {
          setAuthPage("dashboard");
          setDashPage("overview");
        } else {
          setAuthPage(p as AuthPage);
        }
      }} />;
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