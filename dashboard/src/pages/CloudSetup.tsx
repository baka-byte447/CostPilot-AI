import { useState } from "react";
import axios from "axios";
import { useAuth } from "@/context/AuthContext";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type NavPage = "landing" | "login" | "register" | "dashboard" | "cloud-setup";
interface Props {
  onNavigate: (page: NavPage) => void;
}

type Provider = "aws" | "azure" | null;

export default function CloudSetup({ onNavigate }: Props) {
  const { token } = useAuth();
  const [provider, setProvider] = useState<Provider>(null);
  const [awsForm, setAwsForm] = useState({ access_key_id: "", secret_access_key: "", region: "us-east-1", endpoint_url: "" });
  const [azureForm, setAzureForm] = useState({ client_id: "", client_secret: "", tenant_id: "", subscription_id: "", resource_group: "costpilot-rg", location: "eastus" });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const headers = { Authorization: `Bearer ${token}` };

  async function saveAWS(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError(null); setSuccess(null);
    try {
      await axios.post(`${API}/credentials/aws`, {
        access_key_id: awsForm.access_key_id,
        secret_access_key: awsForm.secret_access_key,
        region: awsForm.region,
        endpoint_url: awsForm.endpoint_url || undefined,
      }, { headers });
      setSuccess("AWS credentials saved and encrypted successfully.");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail ?? "Failed to save AWS credentials.");
    } finally {
      setSaving(false);
    }
  }

  async function saveAzure(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError(null); setSuccess(null);
    try {
      await axios.post(`${API}/credentials/azure`, azureForm, { headers });
      setSuccess("Azure credentials saved and encrypted successfully.");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail ?? "Failed to save Azure credentials.");
    } finally {
      setSaving(false);
    }
  }

  const PRIMARY = "#006b5f";
  const GRAD = "linear-gradient(135deg,#006b5f 0%,#2dd4bf 100%)";

  return (
    <div style={{ fontFamily: "'Inter',sans-serif", background: "#f7f9fb", color: "#191c1e", minHeight: "100vh" }}>
      <style>{`
        .cs-input{width:100%;padding:.75rem 1rem;background:#fff;border:1px solid rgba(186,202,197,.25);border-radius:.5rem;font-size:.875rem;font-family:'Inter',sans-serif;outline:none;transition:border-color .2s,box-shadow .2s;color:#191c1e;box-sizing:border-box;}
        .cs-input:focus{border-color:#006b5f;box-shadow:0 0 0 2px rgba(0,107,95,.1);}
        .cs-btn{width:100%;padding:1rem;border:none;border-radius:.75rem;background:${GRAD};color:#fff;font-weight:700;font-family:'Manrope',sans-serif;font-size:.9rem;cursor:pointer;box-shadow:0 4px 14px rgba(0,107,95,.2);transition:opacity .15s;}
        .cs-btn:hover{opacity:.9;}
        .cs-btn:disabled{opacity:.6;cursor:not-allowed;}
        .cs-card{background:#fff;border-radius:1rem;box-shadow:0 4px 20px rgba(25,28,30,.05);padding:2rem;}
        .ms{font-family:'Material Symbols Outlined';font-style:normal;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}
      `}</style>

      <header style={{ borderBottom: "1px solid rgba(186,202,197,.15)", background: "#f7f9fb", padding: "1.2rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 900, fontSize: "1.2rem", color: "#191c1e" }}>CostPilot</span>
        <button onClick={() => onNavigate("dashboard")} style={{ background: "none", border: "none", color: PRIMARY, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontFamily: "'Inter',sans-serif" }}>
          Skip for now <span className="ms" style={{ fontSize: 18 }}>arrow_forward</span>
        </button>
      </header>

      <main style={{ maxWidth: 680, margin: "0 auto", padding: "4rem 1.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "rgba(0,107,95,.1)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.25rem" }}>
            <span className="ms" style={{ color: PRIMARY, fontSize: 28 }}>cloud_done</span>
          </div>
          <h1 style={{ fontFamily: "'Manrope',sans-serif", fontSize: "1.75rem", fontWeight: 900, marginBottom: ".75rem" }}>Connect Your Cloud</h1>
          <p style={{ color: "#3c4a46", lineHeight: 1.7 }}>
            Your credentials are encrypted at rest with AES-256 (Fernet) and never stored in plaintext. CostPilot uses them only to pull metrics and execute RL scaling decisions on <em>your</em> infrastructure.
          </p>
        </div>

        {/* Provider picker */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginBottom: "2rem" }}>
          {(["aws", "azure"] as Provider[]).map(p => (
            <button
              key={p!}
              onClick={() => setProvider(p)}
              style={{
                background: provider === p ? "rgba(0,107,95,.06)" : "#fff",
                border: `2px solid ${provider === p ? PRIMARY : "rgba(186,202,197,.25)"}`,
                borderRadius: "1rem",
                padding: "1.75rem 1rem",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "1rem",
                transition: "border-color .2s",
              }}
            >
              {p === "aws" ? (
                <svg width="48" height="28" viewBox="0 0 58 35" fill="none"><path d="M16.4 14.1c0 .8.1 1.5.3 2 .2.6.5 1.2.9 1.9.1.2.2.4.2.6 0 .3-.2.6-.5.9l-1.7 1.1c-.2.2-.5.2-.7.2-.3 0-.5-.1-.8-.3-.4-.4-.7-.8-1-1.2-.3-.5-.6-1-.9-1.6-2.2 2.6-5 3.9-8.4 3.9-2.4 0-4.3-.7-5.7-2.1-1.4-1.4-2.1-3.2-2.1-5.5 0-2.4.8-4.4 2.5-5.8 1.7-1.4 3.9-2.2 6.7-2.2 .9 0 1.9.1 2.9.2 1 .1 2 .3 3.1.6V5.6c0-2.2-.5-3.7-1.4-4.6-.9-.9-2.5-1.3-4.8-1.3-.9 0-1.9.1-2.9.4-1 .2-1.9.5-2.9.9l-.7.2c-.2 0-.4 0-.5-.1-.3-.2-.4-.5-.4-.9V-.1c0-.3.1-.6.2-.8.2-.2.4-.4.7-.5 1-.5 2.1-.9 3.5-1.2 1.4-.3 2.8-.5 4.3-.5 3.3 0 5.8.7 7.3 2.2 1.5 1.5 2.3 3.8 2.3 6.9v9.1zm-11.7 4.4c.9 0 1.8-.2 2.8-.5 1-.4 1.9-1 2.6-1.9.4-.5.7-1.1.9-1.7.2-.7.3-1.5.3-2.5v-1.2c-.8-.2-1.7-.4-2.6-.5-.9-.1-1.7-.2-2.6-.2-1.9 0-3.2.4-4.2 1.1-1 .7-1.4 1.8-1.4 3.2 0 1.3.3 2.3 1 3 .6.7 1.6 1.2 3.2 1.2z" fill="#252F3E"/></svg>
              ) : (
                <svg width="48" height="28" viewBox="0 0 80 24" fill="none"><path d="M37.2 0H2.8A2.8 2.8 0 0 0 0 2.8v18.4A2.8 2.8 0 0 0 2.8 24h34.4a2.8 2.8 0 0 0 2.8-2.8V2.8A2.8 2.8 0 0 0 37.2 0z" fill="#0089D6"/><path d="M20 6l-8 4.5V15l8 4.5 8-4.5v-4.5L20 6z" fill="#fff"/></svg>
              )}
              <div>
                <div style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 700, fontSize: ".95rem", marginBottom: 3 }}>
                  {p === "aws" ? "Amazon Web Services" : "Microsoft Azure"}
                </div>
                <div style={{ fontSize: ".78rem", color: "#3c4a46" }}>
                  {p === "aws" ? "EC2, ECS, EKS, CloudWatch" : "VMSS, ACI, Monitor, Cost"}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Status messages */}
        {success && (
          <div style={{ marginBottom: "1.5rem", padding: ".875rem 1rem", background: "rgba(0,107,95,.06)", border: "1px solid rgba(0,107,95,.2)", borderRadius: ".5rem", color: PRIMARY, fontSize: ".875rem", display: "flex", alignItems: "center", gap: 8 }}>
            <span className="ms" style={{ fontSize: 18 }}>check_circle</span> {success}
          </div>
        )}
        {error && (
          <div style={{ marginBottom: "1.5rem", padding: ".875rem 1rem", background: "rgba(186,26,26,.06)", border: "1px solid rgba(186,26,26,.2)", borderRadius: ".5rem", color: "#ba1a1a", fontSize: ".875rem" }}>
            {error}
          </div>
        )}

        {/* AWS Form */}
        {provider === "aws" && (
          <div className="cs-card">
            <h2 style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 800, fontSize: "1.1rem", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="ms" style={{ color: PRIMARY }}>key</span> AWS Credentials
            </h2>
            <form onSubmit={saveAWS} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {[
                ["Access Key ID", "access_key_id", "AKIAIOSFODNN7EXAMPLE"],
                ["Secret Access Key", "secret_access_key", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"],
                ["Region", "region", "us-east-1"],
                ["Endpoint URL (optional — for LocalStack)", "endpoint_url", "http://localhost:4566"],
              ].map(([label, field, ph]) => (
                <div key={field} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".08em", color: "#3c4a46" }}>{label}</label>
                  <input
                    className="cs-input"
                    type={field === "secret_access_key" ? "password" : "text"}
                    placeholder={ph}
                    value={awsForm[field as keyof typeof awsForm]}
                    onChange={e => setAwsForm(prev => ({ ...prev, [field]: e.target.value }))}
                    required={field !== "endpoint_url"}
                  />
                </div>
              ))}
              <button type="submit" className="cs-btn" disabled={saving}>{saving ? "Saving…" : "Save & Encrypt AWS Credentials"}</button>
            </form>
            <p style={{ marginTop: "1rem", fontSize: ".78rem", color: "#6b7a76", display: "flex", gap: 6, alignItems: "flex-start" }}>
              <span className="ms" style={{ fontSize: 16, flexShrink: 0 }}>lock</span>
              Credentials are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before database storage. Your keys are never logged.
            </p>
          </div>
        )}

        {/* Azure Form */}
        {provider === "azure" && (
          <div className="cs-card">
            <h2 style={{ fontFamily: "'Manrope',sans-serif", fontWeight: 800, fontSize: "1.1rem", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="ms" style={{ color: PRIMARY }}>key</span> Azure Service Principal
            </h2>
            <form onSubmit={saveAzure} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {[
                ["Tenant ID", "tenant_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"],
                ["Client ID (App ID)", "client_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"],
                ["Client Secret", "client_secret", "••••••••"],
                ["Subscription ID", "subscription_id", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"],
                ["Resource Group", "resource_group", "costpilot-rg"],
                ["Location", "location", "eastus"],
              ].map(([label, field, ph]) => (
                <div key={field} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <label style={{ fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".08em", color: "#3c4a46" }}>{label}</label>
                  <input
                    className="cs-input"
                    type={field === "client_secret" ? "password" : "text"}
                    placeholder={ph}
                    value={azureForm[field as keyof typeof azureForm]}
                    onChange={e => setAzureForm(prev => ({ ...prev, [field]: e.target.value }))}
                    required={!["resource_group", "location"].includes(field)}
                  />
                </div>
              ))}
              <button type="submit" className="cs-btn" disabled={saving}>{saving ? "Saving…" : "Save & Encrypt Azure Credentials"}</button>
            </form>
            <p style={{ marginTop: "1rem", fontSize: ".78rem", color: "#6b7a76", display: "flex", gap: 6, alignItems: "flex-start" }}>
              <span className="ms" style={{ fontSize: 16, flexShrink: 0 }}>lock</span>
              Create a Service Principal via: <code style={{ background: "#f2f4f6", padding: "0 6px", borderRadius: 4 }}>az ad sp create-for-rbac --role Contributor</code>
            </p>
          </div>
        )}

        {!provider && (
          <div style={{ textAlign: "center", padding: "3rem", color: "#6b7a76", fontSize: ".9rem" }}>
            Select a cloud provider above to enter your credentials.
          </div>
        )}

        <div style={{ marginTop: "2rem", display: "flex", justifyContent: "center" }}>
          <button
            onClick={() => onNavigate("dashboard")}
            style={{ background: GRAD, color: "#fff", border: "none", borderRadius: ".75rem", padding: "1rem 3rem", fontWeight: 700, fontFamily: "'Manrope',sans-serif", fontSize: "1rem", cursor: "pointer", boxShadow: "0 4px 14px rgba(0,107,95,.2)", transition: "opacity .15s" }}
            onMouseEnter={e => (e.currentTarget.style.opacity = ".9")}
            onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
          >
            Go to Dashboard →
          </button>
        </div>
      </main>
    </div>
  );
}
