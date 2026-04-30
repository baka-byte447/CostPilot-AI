import { useState } from "react";
import { useAuth } from "@/services/AuthContext";
import CustomCursor from "@/components/CustomCursor";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Email and password are required");
      return;
    }
    if (mode === "register" && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail;
      if (typeof msg === "string") setError(msg);
      else setError(mode === "login" ? "Invalid email or password" : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0f1012] flex items-center justify-center relative overflow-hidden">
      <CustomCursor />

      {/* Background glow effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,rgba(233,79,55,0.12)_0%,transparent_70%)]"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[radial-gradient(circle,rgba(233,79,55,0.08)_0%,transparent_70%)]"></div>
        <div className="absolute top-[30%] right-[20%] w-[300px] h-[300px] rounded-full bg-[radial-gradient(circle,rgba(246,247,235,0.03)_0%,transparent_70%)]"></div>
      </div>

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(246,247,235,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(246,247,235,0.5) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      ></div>

      <div className="relative z-10 w-full max-w-md px-6 fade-in">
        {/* Logo & Branding */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 border border-primary/30 mb-5 shadow-[0_0_40px_rgba(233,79,55,0.2)]">
            <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 0" }}>hub</span>
          </div>
          <h1 className="text-3xl font-bold font-headline tracking-tight text-text">CostPilot</h1>
          <p className="text-[10px] uppercase tracking-[0.3em] text-textDim font-bold mt-1">Enterprise AI Platform</p>
        </div>

        {/* Card */}
        <div className="glass-panel p-8 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
          {/* Mode Toggle */}
          <div className="flex rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.07)] p-1 mb-7">
            <button
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === "login"
                  ? "bg-primary/15 text-primary border border-primary/40 shadow-[0_0_12px_rgba(233,79,55,0.15)]"
                  : "text-textDim hover:text-textMuted"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === "register"
                  ? "bg-primary/15 text-primary border border-primary/40 shadow-[0_0_12px_rgba(233,79,55,0.15)]"
                  : "text-textDim hover:text-textMuted"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-primary/10 border border-primary/30 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">error</span>
              <span className="text-xs text-primary font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-[10px] font-bold text-textDim uppercase tracking-wider mb-1.5">Email</label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 material-symbols-outlined text-textDim text-base">mail</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full glass-input rounded-xl py-3 pl-10 pr-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40 placeholder:text-textDim"
                  placeholder="you@company.com"
                  autoComplete="email"
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-[10px] font-bold text-textDim uppercase tracking-wider mb-1.5">Password</label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 material-symbols-outlined text-textDim text-base">lock</span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full glass-input rounded-xl py-3 pl-10 pr-11 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40 placeholder:text-textDim"
                  placeholder="Min. 8 characters"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-textDim hover:text-textMuted transition-colors"
                >
                  <span className="material-symbols-outlined text-base">{showPassword ? "visibility_off" : "visibility"}</span>
                </button>
              </div>
            </div>

            {/* Confirm Password (Register only) */}
            {mode === "register" && (
              <div className="fade-in">
                <label className="block text-[10px] font-bold text-textDim uppercase tracking-wider mb-1.5">Confirm Password</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 material-symbols-outlined text-textDim text-base">lock</span>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full glass-input rounded-xl py-3 pl-10 pr-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40 placeholder:text-textDim"
                    placeholder="Re-enter password"
                    autoComplete="new-password"
                  />
                </div>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 mt-2 rounded-xl optimizer-gradient optimizer-glow text-sm font-semibold flex items-center justify-center gap-2 transition-all hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  {mode === "login" ? "Signing in..." : "Creating account..."}
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-base">{mode === "login" ? "login" : "person_add"}</span>
                  {mode === "login" ? "Sign In" : "Create Account"}
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-[rgba(255,255,255,0.07)]"></div>
            <span className="text-[10px] text-textDim uppercase tracking-wider font-bold">
              {mode === "login" ? "New here?" : "Have an account?"}
            </span>
            <div className="flex-1 h-px bg-[rgba(255,255,255,0.07)]"></div>
          </div>

          <button
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            className="w-full py-2.5 rounded-xl ghost-button text-xs font-semibold"
          >
            {mode === "login" ? "Create a free account" : "Sign in instead"}
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] text-textDim mt-8">
          Automated Cloud Cost Intelligence & Optimization
        </p>
      </div>
    </div>
  );
}
