import { useState, type FormEvent } from "react";
import { useAuth } from "@/context/AuthContext";

type NavPage = "landing" | "login" | "register" | "dashboard";
interface Props { onNavigate: (page: NavPage) => void; }

interface FormState {
  name: string; company: string; email: string;
  provider: string; password: string; confirmPassword: string;
}

export default function Register({ onNavigate }: Props) {
  const { register } = useAuth();
  const [form, setForm] = useState<FormState>({ name: "", company: "", email: "", provider: "", password: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  function set(field: keyof FormState) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      onNavigate("dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  const filled = [form.name, form.email, form.password].filter(Boolean).length;
  const progress = Math.round((filled / 3) * 100);
  const GRAD = "linear-gradient(135deg,#006b5f 0%,#2dd4bf 100%)";

  return (
    <div style={{ fontFamily: "'Inter',sans-serif", background: "#f7f9fb", color: "#191c1e", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800;900&family=Inter:wght@400;500;600&family=Material+Symbols+Outlined:wght,FILL@400,0&display=swap');
        .ms{font-family:'Material Symbols Outlined';font-style:normal;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}
        .reg-input{width:100%;padding:.75rem 1rem;background:#fff;border:1px solid rgba(186,202,197,.25);border-radius:.5rem;font-size:.875rem;font-family:'Inter',sans-serif;outline:none;transition:border-color .2s,box-shadow .2s;color:#191c1e;box-sizing:border-box;}
        .reg-input:focus{border-color:#006b5f;box-shadow:0 0 0 2px rgba(0,107,95,.1);}
        .reg-btn{width:100%;padding:1rem;border:none;border-radius:.75rem;background:${GRAD};color:#fff;font-weight:700;font-family:'Manrope',sans-serif;font-size:.9rem;cursor:pointer;box-shadow:0 4px 14px rgba(0,107,95,.2);transition:opacity .15s,transform .15s;}
        .reg-btn:hover{opacity:.91;}
        .reg-btn:active{transform:scale(.98);}
        .reg-btn:disabled{opacity:.6;cursor:not-allowed;}
        .reg-social{flex:1;display:flex;justify-content:center;align-items:center;gap:8px;padding:.75rem;background:#e6e8ea;border:none;border-radius:.75rem;cursor:pointer;font-size:.875rem;font-weight:500;font-family:'Inter',sans-serif;transition:background .15s;}
        .reg-social:hover{background:#dde0e2;}
        .link-btn{background:none;border:none;color:#006b5f;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;font-size:.875rem;padding:0;}
        .link-btn:hover{text-decoration:underline;}
        .reg-bg{background:radial-gradient(circle at top right,rgba(45,212,191,.07),transparent 40%),radial-gradient(circle at bottom left,rgba(0,107,95,.05),transparent 40%);}
      `}</style>

      {/* HEADER */}
      <header style={{ width: "100%", background: "#f7f9fb", borderBottom: "1px solid rgba(186,202,197,.15)" }}>
        <nav style={{ maxWidth: 1280, margin: "0 auto", padding: "1.2rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button onClick={() => onNavigate("landing")} style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 900, fontSize: "1.35rem", color: "#191c1e", background: "none", border: "none", cursor: "pointer", letterSpacing: "-.02em" }}>
            CostPilot
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
            <button style={{ background: "none", border: "none", fontSize: ".875rem", color: "#6b7a76", cursor: "pointer", fontFamily: "'Inter',sans-serif" }}>Support</button>
            <button className="link-btn" style={{ fontSize: "1rem", fontFamily: "'Manrope',sans-serif" }} onClick={() => onNavigate("login")}>Sign In</button>
          </div>
        </nav>
      </header>

      <main className="reg-bg" style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2.5rem 1.5rem" }}>
        <div style={{ width: "100%", maxWidth: 560 }}>

          {/* Progress bar */}
          <div style={{ width: "100%", height: 4, background: "#e6e8ea", borderRadius: 9999, overflow: "hidden", marginBottom: "2rem" }}>
            <div style={{ height: "100%", width: `${progress}%`, background: GRAD, transition: "width .35s ease", borderRadius: 9999 }} />
          </div>

          <div style={{ background: "#fff", borderRadius: "1rem", padding: "2.5rem 2.25rem", boxShadow: "0 10px 40px rgba(25,28,30,.04)" }}>
            <div style={{ marginBottom: "2rem", textAlign: "center" }}>
              <h1 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.7rem", fontWeight: 800, marginBottom: 6, letterSpacing: "-.01em" }}>Create your account</h1>
              <p style={{ color: "#3c4a46", fontSize: ".875rem" }}>Join CostPilot to gain deep insights into your cloud infrastructure spending.</p>
            </div>

            {error && (
              <div style={{ marginBottom: "1.25rem", padding: ".75rem 1rem", background: "rgba(186,26,26,.06)", borderRadius: ".5rem", border: "1px solid rgba(186,26,26,.15)", color: "#ba1a1a", fontSize: ".875rem" }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label htmlFor="name" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Full Name</label>
                  <input id="name" className="reg-input" type="text" placeholder="John Doe" value={form.name} onChange={set("name")} required autoComplete="name" />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label htmlFor="company" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Company Name</label>
                  <input id="company" className="reg-input" type="text" placeholder="Acme Corp" value={form.company} onChange={set("company")} autoComplete="organization" />
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                <label htmlFor="reg-email" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Work Email</label>
                <input id="reg-email" className="reg-input" type="email" placeholder="john@company.com" value={form.email} onChange={set("email")} required autoComplete="email" />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                <label htmlFor="provider" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Primary Cloud Provider</label>
                <div style={{ position: "relative" }}>
                  <select id="provider" className="reg-input" value={form.provider} onChange={set("provider")} style={{ appearance: "none", cursor: "pointer" }}>
                    <option value="" disabled>Select a provider</option>
                    <option value="aws">AWS (Amazon Web Services)</option>
                    <option value="azure">Microsoft Azure</option>
                    <option value="gcp">Google Cloud Platform</option>
                    <option value="multi">Multi-Cloud</option>
                  </select>
                  <span className="ms" style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", color: "#3c4a46", fontSize: 20, pointerEvents: "none" }}>keyboard_arrow_down</span>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label htmlFor="reg-pw" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Password</label>
                  <div style={{ position: "relative" }}>
                    <input id="reg-pw" className="reg-input" type={showPw ? "text" : "password"} placeholder="••••••••" value={form.password} onChange={set("password")} required minLength={6} autoComplete="new-password" style={{ paddingRight: "2.5rem" }} />
                    <button type="button" onClick={() => setShowPw(s => !s)} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#3c4a46" }}>
                      <span className="ms" style={{ fontSize: 18 }}>{showPw ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label htmlFor="reg-cpw" style={{ fontSize: ".62rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46" }}>Confirm Password</label>
                  <input id="reg-cpw" className="reg-input" type="password" placeholder="••••••••" value={form.confirmPassword} onChange={set("confirmPassword")} required autoComplete="new-password" />
                </div>
              </div>

              {/* Password strength hint */}
              {form.password.length > 0 && form.password.length < 6 && (
                <p style={{ fontSize: ".78rem", color: "#ba1a1a", marginTop: -8 }}>Password must be at least 6 characters</p>
              )}

              <div style={{ paddingTop: ".25rem" }}>
                <button type="submit" className="reg-btn" disabled={loading}>{loading ? "Creating account…" : "Create Account"}</button>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ flex: 1, height: 1, background: "rgba(186,202,197,.2)" }} />
                <span style={{ fontSize: ".62rem", textTransform: "uppercase", letterSpacing: ".1em", color: "#3c4a46", whiteSpace: "nowrap" }}>or sign up with</span>
                <div style={{ flex: 1, height: 1, background: "rgba(186,202,197,.2)" }} />
              </div>

              <div style={{ display: "flex", gap: ".75rem" }}>
                <button type="button" className="reg-social">
                  <span className="ms" style={{ fontSize: 18 }}>google</span>
                  <span>Google</span>
                </button>
                <button type="button" className="reg-social">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" /></svg>
                  <span>GitHub</span>
                </button>
              </div>
            </form>

            <p style={{ marginTop: "1.75rem", textAlign: "center", fontSize: ".875rem", color: "#6b7a76" }}>
              Already have an account? <button className="link-btn" onClick={() => onNavigate("login")}>Sign In</button>
            </p>
          </div>

          {/* Trust badges */}
          <div style={{ marginTop: "1.75rem", display: "flex", justifyContent: "center", alignItems: "center", gap: "2rem", opacity: .38, filter: "grayscale(1)" }}>
            {[["security", "SOC2 Compliant"], ["encrypted", "AES-256 Secure"]].map(([icon, label]) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span className="ms" style={{ fontSize: 18 }}>{icon}</span>
                <span style={{ fontSize: ".68rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em" }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer style={{ borderTop: "1px solid rgba(186,202,197,.15)", background: "#f7f9fb", padding: "1.75rem 2rem" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: ".75rem" }}>
          <span style={{ fontSize: ".875rem", color: "#6b7a76" }}>© 2025 CostPilot AI. All rights reserved.</span>
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
