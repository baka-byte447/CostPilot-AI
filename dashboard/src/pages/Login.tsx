import { useState, type FormEvent } from "react";
import { useAuth } from "@/context/AuthContext";

type NavPage = "landing" | "login" | "register" | "dashboard";
interface Props { onNavigate: (page: NavPage) => void; }

export default function Login({ onNavigate }: Props) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      onNavigate("dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  const GRAD = "linear-gradient(135deg,#006b5f 0%,#2dd4bf 100%)";
  const PRIMARY = "#006b5f";

  return (
    <div style={{ fontFamily: "'Inter',sans-serif", background: "#f7f9fb", color: "#191c1e", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800;900&family=Inter:wght@400;500;600&family=Material+Symbols+Outlined:wght,FILL@400,0&display=swap');
        .ms{font-family:'Material Symbols Outlined';font-style:normal;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}
        .auth-input{width:100%;padding:.75rem .75rem .75rem 2.65rem;background:#f2f4f6;border:1px solid rgba(186,202,197,.25);border-radius:.5rem;font-size:.875rem;outline:none;font-family:'Inter',sans-serif;transition:border-color .2s,box-shadow .2s;box-sizing:border-box;color:#191c1e;}
        .auth-input:focus{border-color:#006b5f;box-shadow:0 0 0 2px rgba(0,107,95,.12);}
        .auth-btn{width:100%;padding:.875rem;border:none;border-radius:.75rem;background:${GRAD};color:#fff;font-weight:700;font-family:'Manrope',sans-serif;font-size:.9rem;letter-spacing:.04em;cursor:pointer;box-shadow:0 4px 14px rgba(0,107,95,.2);transition:opacity .15s,transform .15s;}
        .auth-btn:hover{opacity:.91;}
        .auth-btn:active{transform:scale(.98);}
        .auth-btn:disabled{opacity:.6;cursor:not-allowed;}
        .social-btn{display:flex;align-items:center;justify-content:center;gap:8px;padding:.75rem 1rem;background:#e6e8ea;border:none;border-radius:.5rem;cursor:pointer;font-size:.875rem;font-weight:500;font-family:'Inter',sans-serif;transition:background .15s;}
        .social-btn:hover{background:#dde0e2;}
        .social-btn:active{transform:scale(.98);}
        .link-btn{background:none;border:none;color:#006b5f;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;font-size:.875rem;padding:0;}
        .link-btn:hover{text-decoration:underline;}
      `}</style>

      {/* NAV */}
      <nav style={{ position: "fixed", top: 0, left: 0, width: "100%", zIndex: 50, padding: "1.25rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button onClick={() => onNavigate("landing")} style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer" }}>
          <div style={{ width: 38, height: 38, borderRadius: ".75rem", background: GRAD, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span className="ms" style={{ color: "#fff", fontSize: 20, fontVariationSettings: "'FILL' 1" }}>account_balance_wallet</span>
          </div>
          <span style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 800, fontSize: "1.05rem", color: "#191c1e" }}>CostPilot</span>
        </button>
        <div style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
          <button style={{ background: "none", border: "none", fontSize: ".875rem", color: "#3c4a46", cursor: "pointer", fontFamily: "'Inter',sans-serif" }}>Support</button>
          <button className="link-btn" onClick={() => onNavigate("login")}>Sign In</button>
        </div>
      </nav>

      <main style={{ flex: 1, display: "flex", minHeight: "100vh" }}>
        {/* LEFT PANEL (desktop only) */}
        <section style={{ flex: 1, background: "#f2f4f6", position: "relative", overflow: "hidden", alignItems: "center", justifyContent: "center", padding: "3rem", display: "none" }}
          ref={el => { if (el) { const mq = window.matchMedia("(min-width:768px)"); const toggle = (m: MediaQueryListEvent | MediaQueryList) => { el.style.display = m.matches ? "flex" : "none"; }; toggle(mq); mq.addEventListener("change", toggle as (e: MediaQueryListEvent) => void); } }}>
          <div style={{ position: "absolute", top: "-10%", right: "-10%", width: 360, height: 360, borderRadius: "50%", background: "rgba(0,107,95,.05)", filter: "blur(48px)" }} />
          <div style={{ position: "absolute", bottom: "-5%", left: "-5%", width: 280, height: 280, borderRadius: "50%", background: "rgba(45,212,191,.07)", filter: "blur(36px)" }} />
          <div style={{ position: "relative", zIndex: 10, maxWidth: 460 }}>
            <div style={{ display: "inline-flex", padding: "4px 14px", borderRadius: 9999, background: "rgba(45,212,191,.14)", color: "#00574d", fontSize: ".68rem", fontWeight: 700, letterSpacing: ".1em", textTransform: "uppercase", marginBottom: "1.75rem" }}>Platform v2.4</div>
            <h1 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "2.5rem", fontWeight: 900, color: "#191c1e", lineHeight: 1.15, marginBottom: "1.25rem" }}>
              Welcome back to <span style={{ color: PRIMARY }}>CostPilot</span>
            </h1>
            <p style={{ color: "#3c4a46", fontSize: "1rem", lineHeight: 1.7, marginBottom: "2.5rem" }}>
              Your RL agent has been running autonomously. Check the latest scaling decisions, LSTM forecasts, and live cost metrics.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: ".875rem", marginBottom: "2.5rem" }}>
              {[
                { icon: "insights", label: "Real-time Analytics", offset: false },
                { icon: "psychology", label: "RL Optimizer", offset: true },
                { icon: "bolt", label: "LSTM Forecasting", offset: false },
                { icon: "security", label: "SLO Engine", offset: true },
              ].map(({ icon, label, offset }) => (
                <div key={label} style={{ background: "#fff", borderRadius: ".75rem", padding: "1.1rem", display: "flex", flexDirection: "column", gap: 8, border: "1px solid rgba(186,202,197,.15)", boxShadow: "0 4px 12px rgba(25,28,30,.04)", marginTop: offset ? 22 : 0 }}>
                  <span className="ms" style={{ color: offset ? "#2dd4bf" : PRIMARY, fontSize: 26 }}>{icon}</span>
                  <div style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 700, fontSize: ".875rem" }}>{label}</div>
                </div>
              ))}
            </div>
            <div style={{ paddingTop: "1.75rem", borderTop: "1px solid rgba(186,202,197,.2)", display: "flex", alignItems: "center", gap: "1rem" }}>
              <div style={{ display: "flex" }}>
                {["#00687a", "#2dd4bf", "#732ee4"].map((bg, i) => (
                  <div key={i} style={{ width: 34, height: 34, borderRadius: "50%", background: bg, border: "2px solid #f2f4f6", marginLeft: i > 0 ? -10 : 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span className="ms" style={{ color: "#fff", fontSize: 14, fontVariationSettings: "'FILL' 1" }}>person</span>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: ".875rem", color: "#3c4a46" }}>Trusted by <strong style={{ color: "#191c1e" }}>cloud engineers</strong> worldwide</p>
            </div>
          </div>
        </section>

        {/* RIGHT FORM */}
        <section style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "1.5rem", paddingTop: "5rem", background: "#f7f9fb" }}>
          <div style={{ width: "100%", maxWidth: 440 }}>
            <div style={{ background: "#fff", borderRadius: ".875rem", padding: "2.5rem 2.25rem", boxShadow: "0 4px 20px rgba(25,28,30,.04),0 10px 40px rgba(25,28,30,.02)" }}>
              <div style={{ marginBottom: "1.75rem" }}>
                <h2 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.5rem", fontWeight: 800, marginBottom: 6 }}>Sign In</h2>
                <p style={{ fontSize: ".875rem", color: "#3c4a46" }}>Welcome back! Please enter your details.</p>
              </div>

              {error && (
                <div style={{ marginBottom: "1.25rem", padding: ".75rem 1rem", background: "rgba(186,26,26,.06)", borderRadius: ".5rem", border: "1px solid rgba(186,26,26,.15)", color: "#ba1a1a", fontSize: ".875rem" }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
                {/* Email */}
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label htmlFor="email" style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".08em", color: "#3c4a46" }}>Email Address</label>
                  <div style={{ position: "relative" }}>
                    <span className="ms" style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#3c4a46", fontSize: 18 }}>mail</span>
                    <input id="email" className="auth-input" type="email" placeholder="name@company.com" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" />
                  </div>
                </div>

                {/* Password */}
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <label htmlFor="password" style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".08em", color: "#3c4a46" }}>Password</label>
                    <button type="button" style={{ fontSize: ".78rem", color: PRIMARY, background: "none", border: "none", cursor: "pointer", fontWeight: 500, fontFamily: "'Inter',sans-serif" }}>Forgot password?</button>
                  </div>
                  <div style={{ position: "relative" }}>
                    <span className="ms" style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#3c4a46", fontSize: 18 }}>lock</span>
                    <input id="password" className="auth-input" type={showPw ? "text" : "password"} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" />
                    <button type="button" onClick={() => setShowPw(s => !s)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#3c4a46" }}>
                      <span className="ms" style={{ fontSize: 18 }}>{showPw ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>

                {/* Remember */}
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} style={{ width: 15, height: 15, accentColor: PRIMARY }} />
                  <span style={{ fontSize: ".875rem", color: "#3c4a46" }}>Remember me for 30 days</span>
                </label>

                <button type="submit" className="auth-btn" disabled={loading}>{loading ? "Signing in…" : "Sign In"}</button>
              </form>

              {/* Divider */}
              <div style={{ position: "relative", margin: "1.75rem 0" }}>
                <div style={{ borderTop: "1px solid rgba(186,202,197,.22)", position: "absolute", inset: 0, top: "50%" }} />
                <div style={{ position: "relative", display: "flex", justifyContent: "center" }}>
                  <span style={{ padding: "0 1rem", background: "#fff", fontSize: ".68rem", color: "#3c4a46", textTransform: "uppercase", letterSpacing: ".06em" }}>or continue with</span>
                </div>
              </div>

              {/* Social */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: ".75rem" }}>
                <button className="social-btn" type="button">
                  <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
                  <span>Google</span>
                </button>
                <button className="social-btn" type="button">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" /></svg>
                  <span>GitHub</span>
                </button>
              </div>

              <p style={{ marginTop: "1.75rem", textAlign: "center", fontSize: ".875rem", color: "#3c4a46" }}>
                Don't have an account? <button className="link-btn" onClick={() => onNavigate("register")}>Sign Up</button>
              </p>
            </div>

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "center", gap: "1.5rem" }}>
              {["Privacy Policy", "Terms of Service", "Contact Support"].map(l => (
                <a key={l} href="#" style={{ fontSize: ".75rem", color: "rgba(60,74,70,.55)", textDecoration: "none" }}>{l}</a>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer style={{ borderTop: "1px solid rgba(186,202,197,.15)", background: "#f7f9fb", padding: "1.75rem 2rem" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: ".75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 800, fontSize: "1rem", color: "#191c1e" }}>CostPilot</span>
            <span style={{ fontSize: ".8rem", color: "rgba(60,74,70,.5)" }}>© 2025 CostPilot AI. All rights reserved.</span>
          </div>
          <div style={{ display: "flex", gap: "2rem" }}>
            {["Privacy Policy", "Terms of Service", "Security"].map(l => (
              <a key={l} href="#" style={{ fontSize: ".875rem", color: "#6b7a76", textDecoration: "none" }}>{l}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
