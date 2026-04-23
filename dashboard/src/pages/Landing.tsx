import { useAuth } from "@/context/AuthContext";

type NavPage = "landing" | "login" | "register" | "dashboard";

interface Props {
  onNavigate: (page: NavPage) => void;
}

const PRIMARY = "#00687a";
const PRIMARY_GRAD = "linear-gradient(135deg,#00687a 0%,#00aac6 100%)";
const TERTIARY = "#732ee4";

export default function Landing({ onNavigate }: Props) {
  const { user, logout } = useAuth();

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div style={{ fontFamily: "'Inter',sans-serif", background: "#f7f9fb", color: "#191c1e", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800;900&family=Inter:wght@400;500;600&family=Material+Symbols+Outlined:wght,FILL@400,0&display=swap');
        .lp-nav-link{color:#3e4850;font-weight:600;font-size:.875rem;text-decoration:none;transition:color .15s;cursor:pointer;background:none;border:none;}
        .lp-nav-link:hover{color:${PRIMARY};}
        .lp-nav-link.active{color:${PRIMARY};border-bottom:2px solid ${PRIMARY};padding-bottom:2px;}
        .lp-btn-primary{background:${PRIMARY_GRAD};color:#fff;border:none;cursor:pointer;font-weight:700;font-family:'Manrope',sans-serif;transition:transform .15s,opacity .15s;border-radius:.75rem;}
        .lp-btn-primary:hover{opacity:.9;transform:scale(1.015);}
        .lp-btn-primary:active{transform:scale(.98);}
        .lp-btn-ghost{background:#e0e3e5;color:#191c1e;border:none;cursor:pointer;font-weight:700;font-family:'Manrope',sans-serif;border-radius:.75rem;transition:background .15s;}
        .lp-btn-ghost:hover{background:#d8dadc;}
        .hover-lift{transition:transform .2s;}
        .hover-lift:hover{transform:translateY(-5px);}
        .lp-card{background:#fff;border-radius:1rem;box-shadow:0 8px 24px rgba(0,104,122,.07);}
        .lp-input{width:100%;background:#f7f9fb;border:none;border-radius:.75rem;padding:1rem;font-size:.95rem;outline:none;font-family:'Inter',sans-serif;transition:box-shadow .2s;box-sizing:border-box;}
        .lp-input:focus{box-shadow:0 0 0 2px rgba(0,104,122,.22);}
        .lp-section-label{display:inline-flex;align-items:center;gap:6px;padding:4px 14px;border-radius:9999px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:1.5rem;}
        .lp-stat-num{font-family:'Manrope',sans-serif;font-size:2rem;font-weight:900;}
        .lp-flow-arrow{display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
        .lp-flow-pill{padding:4px 12px;background:rgba(0,104,122,.1);border-radius:9999px;font-size:.73rem;font-weight:700;color:${PRIMARY};}
        .lp-flow-sep{color:${PRIMARY};font-size:16px;}
        .ms{font-family:'Material Symbols Outlined';font-style:normal;font-size:1.25rem;vertical-align:middle;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}
      `}</style>

      {/* ── NAV ── */}
      <nav style={{ position: "fixed", top: 0, width: "100%", zIndex: 50, background: "rgba(247,249,251,.9)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(190,200,210,.3)" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", padding: "1rem 1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 900, fontSize: "1.25rem", color: PRIMARY, letterSpacing: "-.02em" }}>CostPilot</div>
          <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
            <button className="lp-nav-link active" onClick={() => scrollTo("hero")}>Intelligence</button>
            <button className="lp-nav-link" onClick={() => scrollTo("features")}>Features</button>
            <button className="lp-nav-link" onClick={() => scrollTo("network")}>Partners</button>
            <button className="lp-nav-link" onClick={() => scrollTo("contact")}>Contact</button>
          </div>
          <div style={{ display: "flex", gap: ".75rem", alignItems: "center" }}>
            {user ? (
              <>
                <span style={{ fontSize: ".8rem", color: "#3e4850" }}>Hi, {user.name.split(" ")[0]}</span>
                <button className="lp-btn-primary" style={{ padding: ".6rem 1.4rem", fontSize: ".875rem" }} onClick={() => onNavigate("dashboard")}>Dashboard</button>
                <button style={{ background: "none", border: "none", color: "#3e4850", cursor: "pointer", fontSize: ".8rem" }} onClick={() => { logout(); }}>Sign out</button>
              </>
            ) : (
              <>
                <button className="lp-nav-link" onClick={() => onNavigate("login")}>Sign In</button>
                <button className="lp-btn-primary" style={{ padding: ".6rem 1.5rem", fontSize: ".875rem" }} onClick={() => onNavigate("register")}>Get Started</button>
              </>
            )}
          </div>
        </div>
      </nav>

      <main style={{ paddingTop: 72 }}>

        {/* ── HERO ── */}
        <section id="hero" style={{ maxWidth: 1280, margin: "0 auto", padding: "6rem 1.5rem 4rem", display: "flex", flexWrap: "wrap", gap: "4rem", alignItems: "center" }}>
          <div style={{ flex: "1 1 400px" }}>
            <div className="lp-section-label" style={{ background: "rgba(115,46,228,.08)", border: "1px solid rgba(115,46,228,.2)", color: TERTIARY }}>
              <span className="ms">auto_awesome</span> AI-Powered Optimization
            </div>
            <h1 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "clamp(2.5rem,5.5vw,4.25rem)", fontWeight: 900, lineHeight: 1.08, color: "#191c1e", marginBottom: "1.5rem" }}>
              The Cloud Spending<br /><span style={{ color: PRIMARY }}>Revolution</span>
            </h1>
            <p style={{ fontSize: "1.1rem", color: "#3e4850", maxWidth: 500, lineHeight: 1.7, marginBottom: "2rem" }}>
              CostPilot combines a Reinforcement Learning agent, pure-NumPy LSTM forecasting, and LLM explainability to autonomously scale your AWS and Azure infrastructure — slashing waste before it hits your bill.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
              <button className="lp-btn-primary" style={{ padding: "1rem 2rem", fontSize: "1.05rem" }} onClick={() => onNavigate(user ? "dashboard" : "register")}>
                {user ? "Open Dashboard" : "Launch Dashboard"}
              </button>
              <button className="lp-btn-ghost" style={{ padding: "1rem 2rem", fontSize: "1.05rem" }} onClick={() => scrollTo("features")}>
                View Demo
              </button>
            </div>
          </div>

          <div style={{ flex: "1 1 360px", position: "relative", minHeight: 360 }}>
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,rgba(0,104,122,.07),rgba(115,46,228,.07))", borderRadius: "2.5rem", transform: "rotate(3deg)" }} />
            <div style={{ position: "absolute", inset: 0, background: "rgba(255,255,255,.85)", backdropFilter: "blur(24px)", borderRadius: "2.5rem", transform: "rotate(-3deg)", border: "1px solid rgba(255,255,255,.6)", boxShadow: "0 24px 60px rgba(0,104,122,.1)", overflow: "hidden", padding: "1.75rem", display: "flex", flexDirection: "column", gap: ".875rem" }}>
              {/* mock dashboard card */}
              <div style={{ background: "#fff", borderRadius: ".875rem", padding: "1.1rem 1.25rem", boxShadow: "0 4px 16px rgba(0,104,122,.06)" }}>
                <div style={{ fontSize: ".6rem", fontWeight: 700, color: "#3e4850", textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 6 }}>RL Agent — Latest Decision</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.4rem", fontWeight: 900, color: PRIMARY }}>SCALE UP</span>
                  <span style={{ padding: "3px 10px", background: "rgba(0,104,122,.1)", borderRadius: 9999, fontSize: ".72rem", fontWeight: 700, color: PRIMARY }}>+2 replicas</span>
                </div>
                <div style={{ marginTop: 6, fontSize: ".78rem", color: "#3e4850" }}>CPU 74% · Mem 68% · Reward +2.8</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: ".75rem" }}>
                {[
                  ["LSTM Forecast", "CPU +12% in 30 min", PRIMARY],
                  ["Safety Engine", "SLO Compliant ✓", TERTIARY],
                  ["Azure Cost", "$3.21 MTD", "#3e4850"],
                  ["Q-Table", "84% explored", PRIMARY],
                ].map(([lbl, val, col]) => (
                  <div key={lbl} style={{ background: "#f2f4f6", borderRadius: ".75rem", padding: ".875rem" }}>
                    <div style={{ fontSize: ".58rem", fontWeight: 700, color: "#3e4850", textTransform: "uppercase", marginBottom: 4 }}>{lbl}</div>
                    <div style={{ fontSize: ".88rem", fontWeight: 700, color: col }}>{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── CLOUD INTELLIGENCE ── */}
        <section id="intelligence" style={{ background: "#f2f4f6", padding: "5rem 1.5rem" }}>
          <div style={{ maxWidth: 1280, margin: "0 auto" }}>
            <h2 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "clamp(1.75rem,3.5vw,2.5rem)", fontWeight: 800, marginBottom: ".75rem" }}>Cloud Intelligence</h2>
            <p style={{ color: "#3e4850", marginBottom: "3rem", maxWidth: 580 }}>Sophisticated AI analysis that looks beyond numbers to provide proactive, explainable infrastructure decisions.</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: "1.5rem" }}>
              {[
                { icon: "memory", color: PRIMARY, bg: "rgba(0,104,122,.08)", title: "LSTM Forecasting", desc: "Pure-NumPy LSTM with BPTT predicts CPU, memory, and request load 30 minutes ahead. Auto-dispatches to Prophet for cold starts." },
                { icon: "psychology", color: TERTIARY, bg: "rgba(115,46,228,.08)", title: "RL Optimizer", desc: "Q-learning agent with 1,000-state space (CPU × Memory × Requests) autonomously decides: scale up, maintain, or scale down every 10 seconds." },
                { icon: "account_balance", color: "#505f76", bg: "rgba(80,95,118,.08)", title: "Fiscal Governance", desc: "Professional-grade cost reporting from AWS Cost Explorer and Azure Cost Management aligned with real engineering decisions." },
              ].map(({ icon, color, bg, title, desc }) => (
                <div key={title} className="hover-lift lp-card" style={{ padding: "2rem" }}>
                  <div style={{ width: 48, height: 48, borderRadius: ".75rem", background: bg, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1rem" }}>
                    <span className="ms" style={{ color, fontSize: 24 }}>{icon}</span>
                  </div>
                  <h3 style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 800, fontSize: "1.05rem", marginBottom: ".5rem" }}>{title}</h3>
                  <p style={{ fontSize: ".875rem", color: "#3e4850", lineHeight: 1.65 }}>{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── FEATURES BENTO ── */}
        <section id="features" style={{ padding: "5rem 1.5rem", maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "2rem", marginBottom: "3rem" }}>
            <div>
              <h2 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "clamp(1.75rem,4vw,2.75rem)", fontWeight: 900, marginBottom: ".75rem" }}>Designed for Precision</h2>
              <p style={{ color: "#3e4850", fontSize: "1.05rem" }}>Every feature is engineered to reduce cloud waste while maximising reliability.</p>
            </div>
            <button className="lp-nav-link" style={{ display: "flex", alignItems: "center", gap: 6, color: PRIMARY }} onClick={() => onNavigate(user ? "dashboard" : "register")}>
              Explore all features <span className="ms" style={{ fontSize: 20 }}>arrow_forward</span>
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(12,1fr)", gap: "1.5rem" }}>
            {/* Large */}
            <div style={{ gridColumn: "span 8", background: "#f2f4f6", borderRadius: "2rem", padding: "2.5rem", overflow: "hidden", position: "relative" }}>
              <h3 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.6rem", fontWeight: 800, marginBottom: ".75rem" }}>Autonomous Scaling Loop</h3>
              <p style={{ color: "#3e4850", maxWidth: 420, marginBottom: "1.75rem" }}>Prometheus → LSTM forecast → RL agent → Safety Engine → AWS/Azure executor → LLM explanation. Every 10 seconds, automatically.</p>
              <div className="lp-flow-arrow">
                {["Metrics", "Forecast", "RL Decision", "Safety Check", "Execute", "Explain"].map((s, i) => (
                  <span key={s} className="lp-flow-arrow">
                    <span className="lp-flow-pill">{s}</span>
                    {i < 5 && <span className="ms lp-flow-sep">arrow_forward</span>}
                  </span>
                ))}
              </div>
            </div>

            {/* Small 1 */}
            <div style={{ gridColumn: "span 4", background: `rgba(115,46,228,.04)`, borderRadius: "2rem", padding: "2.5rem", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", gap: "1.25rem", border: `1px solid rgba(115,46,228,.1)` }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "rgba(115,46,228,.12)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(115,46,228,.2)" }}>
                <span className="ms" style={{ color: TERTIARY, fontSize: 30 }}>bolt</span>
              </div>
              <div>
                <h3 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.4rem", fontWeight: 800, marginBottom: ".5rem" }}>Instant Audit</h3>
                <p style={{ fontSize: ".875rem", color: "#3e4850" }}>Full cost + compliance audit generated in under 60 seconds.</p>
              </div>
            </div>

            {/* Small 2 */}
            <div style={{ gridColumn: "span 4", background: `rgba(0,104,122,.04)`, borderRadius: "2rem", padding: "2.5rem", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", gap: "1.25rem", border: `1px solid rgba(0,104,122,.1)` }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "rgba(0,104,122,.12)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(0,104,122,.2)" }}>
                <span className="ms" style={{ color: PRIMARY, fontSize: 30 }}>security</span>
              </div>
              <div>
                <h3 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.4rem", fontWeight: 800, marginBottom: ".5rem" }}>SLO Guardrails</h3>
                <p style={{ fontSize: ".875rem", color: "#3e4850" }}>Configurable CPU/mem ceilings and cooldown timers block unsafe RL actions.</p>
              </div>
            </div>

            {/* Wide bottom */}
            <div style={{ gridColumn: "span 8", background: "#e6e8ea", borderRadius: "2rem", padding: "2.5rem", display: "flex", alignItems: "center", gap: "2rem" }}>
              <span className="ms" style={{ color: "#505f76", fontSize: 64, flexShrink: 0 }}>cloud_sync</span>
              <div>
                <h3 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.4rem", fontWeight: 800, marginBottom: ".5rem" }}>Real AWS + Azure, Today</h3>
                <p style={{ color: "#3e4850" }}>LocalStack-backed AWS (ASG, ECS, EKS) and live Azure SDK (VMSS, ACI, Cost Management) — both active in a single docker-compose.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── NETWORK / JOIN ── */}
        <section id="network" style={{ background: PRIMARY, color: "#fff", padding: "5rem 1.5rem", overflow: "hidden", position: "relative" }}>
          <span className="ms" style={{ position: "absolute", top: "-2rem", right: "-2rem", fontSize: "22rem", opacity: .06, color: "#fff", transform: "rotate(12deg)", pointerEvents: "none" }}>hub</span>
          <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "3rem", position: "relative", zIndex: 10 }}>
            <div style={{ maxWidth: 580 }}>
              <h2 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "clamp(2rem,5vw,3.25rem)", fontWeight: 900, marginBottom: "1.25rem" }}>Join the Network</h2>
              <p style={{ fontSize: "1.1rem", lineHeight: 1.7, opacity: .9, marginBottom: "2.5rem" }}>
                CostPilot is open to cloud engineers and teams who want autonomous, intelligent cost management without the enterprise price tag. Sign up and connect your cloud in minutes.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "2.5rem" }}>
                {[["1 K", "RL States"], ["6-step", "LSTM Horizon"], ["10 s", "Decision Loop"], ["99%", "SLO Uptime"]].map(([num, lab]) => (
                  <div key={lab} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span className="lp-stat-num">{num}</span>
                    <span style={{ fontSize: ".65rem", textTransform: "uppercase", letterSpacing: ".12em", opacity: .75 }}>{lab}</span>
                  </div>
                ))}
              </div>
            </div>
            <button
              style={{ background: "#fff", color: PRIMARY, border: "none", borderRadius: "1.25rem", padding: "1.25rem 2.5rem", fontWeight: 800, fontFamily: "'Manrope',sans-serif", fontSize: "1.2rem", cursor: "pointer", boxShadow: "0 8px 24px rgba(0,0,0,.12)", transition: "transform .15s", flexShrink: 0 }}
              onMouseEnter={e => (e.currentTarget.style.transform = "scale(1.05)")}
              onMouseLeave={e => (e.currentTarget.style.transform = "scale(1)")}
              onClick={() => onNavigate(user ? "dashboard" : "register")}
            >
              {user ? "Open Dashboard" : "Partner with Us"}
            </button>
          </div>
        </section>

        {/* ── CONTACT ── */}
        <section id="contact" style={{ padding: "5rem 1.5rem", maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ background: "#fff", borderRadius: "2rem", boxShadow: "0 8px 40px rgba(0,104,122,.06)", overflow: "hidden", display: "flex", flexWrap: "wrap", border: "1px solid rgba(190,200,210,.2)" }}>
            <div style={{ flex: "1 1 260px", background: "#f2f4f6", padding: "3rem" }}>
              <h2 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.75rem", fontWeight: 800, marginBottom: "1rem" }}>Inquiry</h2>
              <p style={{ color: "#3e4850", marginBottom: "2rem", lineHeight: 1.7 }}>Speak with our team to get a personalized analysis of your cloud environment and see CostPilot in action.</p>
              {[["mail", "hello@costpilot.ai"], ["call", "+91 800 COSTPILOT"]].map(([icon, val]) => (
                <div key={icon} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: "1rem" }}>
                  <div style={{ width: 40, height: 40, borderRadius: "50%", background: "rgba(0,104,122,.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span className="ms" style={{ color: PRIMARY, fontSize: 20 }}>{icon}</span>
                  </div>
                  <span style={{ fontSize: ".875rem", fontWeight: 500 }}>{val}</span>
                </div>
              ))}
              <div style={{ marginTop: "2.5rem", paddingTop: "2rem", borderTop: "1px solid rgba(190,200,210,.3)" }}>
                <p style={{ fontSize: ".6rem", fontWeight: 700, color: "#3e4850", textTransform: "uppercase", letterSpacing: ".12em", marginBottom: ".75rem" }}>Enterprise Grade</p>
                <div style={{ display: "flex", gap: "1rem", opacity: .45 }}>
                  {["verified_user", "cloud_done", "encrypted"].map(i => <span key={i} className="ms" style={{ fontSize: 24 }}>{i}</span>)}
                </div>
              </div>
            </div>
            <div style={{ flex: "2 1 380px", padding: "3rem" }}>
              <form onSubmit={e => { e.preventDefault(); alert("Message sent! We'll be in touch soon."); }} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                  {[["Full Name", "text", "Alexander Hamilton"], ["Email Address", "email", "alex@company.com"]].map(([lbl, type, ph]) => (
                    <div key={lbl} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      <label style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".1em", color: "#3e4850" }}>{lbl}</label>
                      <input className="lp-input" type={type} placeholder={ph} required />
                    </div>
                  ))}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".1em", color: "#3e4850" }}>Organization</label>
                  <input className="lp-input" type="text" placeholder="Global Infrastructure Corp" />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".1em", color: "#3e4850" }}>Message</label>
                  <textarea className="lp-input" rows={4} placeholder="Tell us about your current cloud environment..." style={{ resize: "vertical" }} />
                </div>
                <button type="submit" className="lp-btn-primary" style={{ width: "100%", padding: "1.1rem", fontSize: "1rem" }}>Send Request</button>
              </form>
            </div>
          </div>
        </section>
      </main>

      {/* ── FOOTER ── */}
      <footer style={{ borderTop: "1px solid #e0e3e5", background: "#f7f9fb", padding: "3rem 1.5rem" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "1.5rem" }}>
          <div>
            <div style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 900, fontSize: "1.1rem", color: "#191c1e", marginBottom: 4 }}>CostPilot</div>
            <div style={{ fontSize: ".75rem", color: "#6e7881" }}>© 2025 CostPilot AI. All rights reserved.</div>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem" }}>
            {["Privacy Policy", "Terms of Service", "Cloud Security", "API Docs"].map(l => (
              <a key={l} href="#" style={{ fontSize: ".75rem", color: "#6e7881", textDecoration: "underline" }}>{l}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
