import { useState, useEffect, useCallback } from "react";
import { awsSetup, awsSaveConnection, awsGetConnection, awsDeleteConnection, awsVerifyConnection } from "@/services/api";

const AWS_REGIONS = [
  "us-east-1", "us-east-2", "us-west-1", "us-west-2",
  "eu-west-1", "eu-west-2", "eu-central-1",
  "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
  "sa-east-1", "ca-central-1",
];

type Step = "idle" | "setup" | "deploy" | "connect" | "done";

interface SetupData {
  external_id: string;
  role_name: string;
  control_account_id: string;
  template_yaml: string;
  cloudformation_url: string;
}

interface Connection {
  id: number;
  account_id: string;
  role_arn: string;
  default_region: string;
  regions: string[];
  label: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  external_id_set: boolean;
}

export default function ConnectAWS() {
  const [step, setStep] = useState<Step>("idle");
  const [setupData, setSetupData] = useState<SetupData | null>(null);
  const [connection, setConnection] = useState<Connection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [verifyResult, setVerifyResult] = useState<{ verified: boolean; account_id?: string; arn?: string; error?: string } | null>(null);

  // Form fields
  const [roleName, setRoleName] = useState("CostPilotAccessRole");
  const [controlAccountId, setControlAccountId] = useState("");
  const [allowWrite, setAllowWrite] = useState(false);
  const [accountId, setAccountId] = useState("");
  const [roleArn, setRoleArn] = useState("");
  const [externalId, setExternalId] = useState("");
  const [selectedRegions, setSelectedRegions] = useState<string[]>(["us-east-1"]);
  const [label, setLabel] = useState("");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const loadExistingConnection = useCallback(async () => {
    setLoading(true);
    try {
      const res = await awsGetConnection();
      setConnection(res.data);
      setStep("done");
    } catch {
      setConnection(null);
      setStep("idle");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadExistingConnection();
  }, [loadExistingConnection]);

  async function handleStartSetup() {
    setError("");
    setLoading(true);
    try {
      const res = await awsSetup(controlAccountId, roleName, allowWrite);
      setSetupData(res.data);
      setExternalId(res.data.external_id);
      setStep("deploy");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to generate setup");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveConnection() {
    setError("");
    if (!accountId.trim() || !roleArn.trim() || !externalId.trim()) {
      setError("Account ID, Role ARN, and External ID are required");
      return;
    }
    setSaving(true);
    try {
      const res = await awsSaveConnection({
        account_id: accountId.trim(),
        role_arn: roleArn.trim(),
        external_id: externalId.trim(),
        regions: selectedRegions,
        label: label.trim() || undefined,
      });
      setConnection(res.data);
      setStep("done");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to save connection");
    } finally {
      setSaving(false);
    }
  }

  async function handleVerify() {
    setVerifyResult(null);
    try {
      const res = await awsVerifyConnection();
      setVerifyResult(res.data);
    } catch (e: any) {
      setVerifyResult({ verified: false, error: e?.response?.data?.detail || "Verification failed" });
    }
  }

  async function handleDisconnect() {
    try {
      await awsDeleteConnection();
      setConnection(null);
      setSetupData(null);
      setVerifyResult(null);
      setAccountId("");
      setRoleArn("");
      setExternalId("");
      setLabel("");
      setControlAccountId("");
      setStep("idle");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to disconnect");
    }
  }

  function toggleRegion(r: string) {
    setSelectedRegions((prev) =>
      prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]
    );
  }

  async function copyToClipboard(text: string, key: string) {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  }

  if (loading && step === "idle") {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-textDim">
          <span className="material-symbols-outlined animate-spin">progress_activity</span>
          Loading AWS connection status...
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/40 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-xl">cloud</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold font-headline tracking-tight">Connect AWS Account</h1>
            <p className="text-xs text-textDim">Securely connect via IAM role — no access keys stored</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 glass-panel border-primary/50 rounded-xl flex items-center gap-3">
          <span className="material-symbols-outlined text-primary text-lg">error</span>
          <span className="text-sm text-primary">{error}</span>
          <button onClick={() => setError("")} className="ml-auto text-textDim hover:text-text">
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        </div>
      )}

      {/* ── Connected State ── */}
      {step === "done" && connection && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.6)]"></span>
                <span className="font-bold font-headline text-lg">AWS Account Connected</span>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={handleVerify} className="px-3 py-1.5 rounded-lg ghost-button text-xs font-semibold flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-sm">verified</span>
                  Verify
                </button>
                <button onClick={handleDisconnect} className="px-3 py-1.5 rounded-lg ghost-button text-xs font-semibold text-red-500 flex items-center gap-1.5 hover:bg-red-500/10 border border-red-500/20">
                  <span className="material-symbols-outlined text-sm">delete</span>
                  Delete Details
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <InfoField label="Account ID" value={connection.account_id} />
              <InfoField label="Default Region" value={connection.default_region} />
              <InfoField label="Role ARN" value={connection.role_arn} full />
              <InfoField label="Regions" value={connection.regions.join(", ")} full />
              {connection.label && <InfoField label="Label" value={connection.label} />}
              <InfoField label="Connected" value={new Date(connection.created_at).toLocaleDateString()} />
            </div>
          </div>

          {verifyResult && (
            <div className={`glass-panel p-4 rounded-xl flex items-center gap-3 ${verifyResult.verified ? "border-emerald-500/40" : "border-primary/40"}`}>
              <span className={`material-symbols-outlined text-lg ${verifyResult.verified ? "text-emerald-400" : "text-primary"}`}>
                {verifyResult.verified ? "check_circle" : "cancel"}
              </span>
              <div className="text-sm">
                {verifyResult.verified ? (
                  <span>Connection verified — <span className="text-textDim">{verifyResult.arn}</span></span>
                ) : (
                  <span className="text-primary">{verifyResult.error || "Verification failed"}</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Step Progress ── */}
      {step !== "done" && (
        <div className="flex items-center gap-2 mb-8">
          {["Setup", "Deploy", "Connect"].map((s, i) => {
            const stepMap: Step[] = ["setup", "deploy", "connect"];
            const currentIdx = step === "idle" ? -1 : stepMap.indexOf(step);
            const isActive = i <= currentIdx;
            const isCurrent = i === currentIdx;
            return (
              <div key={s} className="flex items-center gap-2">
                {i > 0 && <div className={`w-12 h-px ${isActive ? "bg-primary" : "bg-[rgba(255,255,255,0.1)]"}`}></div>}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all ${
                  isCurrent
                    ? "bg-primary/15 border border-primary/50 text-primary"
                    : isActive
                    ? "text-primary"
                    : "text-textDim"
                }`}>
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isActive ? "bg-primary text-white" : "bg-[rgba(255,255,255,0.08)] text-textDim"
                  }`}>
                    {i + 1}
                  </span>
                  {s}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Step: Idle — Start ── */}
      {step === "idle" && !connection && (
        <div className="glass-panel p-8 rounded-2xl text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-3xl">cloud_upload</span>
          </div>
          <div>
            <h2 className="text-xl font-bold font-headline mb-2">Connect Your AWS Account</h2>
            <p className="text-sm text-textDim max-w-lg mx-auto">
              CostPilot uses a cross-account IAM role to read your cost and resource data.
              We generate a CloudFormation template — you deploy it in your account.
              <span className="block mt-1 font-medium text-textMuted">No access keys are ever collected or stored.</span>
            </p>
          </div>

          <div className="space-y-4 max-w-md mx-auto text-left">
            <div>
              <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">Role Name</label>
              <input
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                className="w-full glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40"
                placeholder="CostPilotAccessRole"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">App AWS Account ID (Principal)</label>
              <input
                value={controlAccountId}
                onChange={(e) => setControlAccountId(e.target.value)}
                className="w-full glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40"
                placeholder="123456789012"
              />
            </div>
            <label className="flex items-center gap-2.5 text-sm text-textMuted">
              <input
                type="checkbox"
                checked={allowWrite}
                onChange={(e) => setAllowWrite(e.target.checked)}
                className="accent-[#E94F37] w-4 h-4 rounded"
              />
              Allow write access (scaling actions)
            </label>
          </div>

          <button
            onClick={handleStartSetup}
            disabled={loading || !controlAccountId.trim()}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl optimizer-gradient optimizer-glow text-sm font-semibold transition-all hover:brightness-110 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-lg">rocket_launch</span>
            {loading ? "Generating..." : "Start Setup"}
          </button>
        </div>
      )}

      {/* ── Step: Deploy — Show Template + External ID ── */}
      {step === "deploy" && setupData && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="font-bold font-headline text-lg mb-1">Step 1: Deploy CloudFormation Template</h3>
            <p className="text-xs text-textDim mb-6">Deploy this template in your AWS account to create the IAM role.</p>

            <div className="space-y-4">
              {/* External ID */}
              <div className="glass-panel p-4 rounded-xl">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-textDim uppercase tracking-wider">External ID</span>
                  <CopyBtn value={setupData.external_id} label="external_id" copied={copied} onCopy={copyToClipboard} />
                </div>
                <code className="text-sm text-primary font-mono break-all">{setupData.external_id}</code>
              </div>

              {/* Role Name */}
              <div className="grid grid-cols-2 gap-4">
                <div className="glass-panel p-4 rounded-xl">
                  <span className="text-xs font-bold text-textDim uppercase tracking-wider block mb-1">Role Name</span>
                  <code className="text-sm font-mono">{setupData.role_name}</code>
                </div>
                <div className="glass-panel p-4 rounded-xl">
                  <span className="text-xs font-bold text-textDim uppercase tracking-wider block mb-1">Trust Account</span>
                  <code className="text-sm font-mono">{setupData.control_account_id}</code>
                </div>
              </div>

              {/* Template */}
              <div className="glass-panel p-4 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-textDim uppercase tracking-wider">CloudFormation Template (YAML)</span>
                  <CopyBtn value={setupData.template_yaml} label="template" copied={copied} onCopy={copyToClipboard} />
                </div>
                <pre className="text-[11px] font-mono text-textMuted bg-[rgba(0,0,0,0.3)] rounded-lg p-4 overflow-x-auto max-h-64 whitespace-pre">
                  {setupData.template_yaml}
                </pre>
              </div>

              {/* CloudFormation Link */}
              <a
                href={setupData.cloudformation_url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#FF9900]/15 border border-[#FF9900]/40 text-[#FF9900] text-sm font-semibold hover:bg-[#FF9900]/25 transition-all"
              >
                <span className="material-symbols-outlined text-lg">open_in_new</span>
                Open AWS CloudFormation Console
              </a>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => setStep("idle")} className="px-4 py-2 rounded-lg ghost-button text-xs font-semibold">
              ← Back
            </button>
            <button
              onClick={() => setStep("connect")}
              className="px-6 py-2.5 rounded-xl optimizer-gradient text-sm font-semibold flex items-center gap-2"
            >
              I've deployed the template
              <span className="material-symbols-outlined text-base">arrow_forward</span>
            </button>
          </div>
        </div>
      )}

      {/* ── Step: Connect — Enter Role ARN ── */}
      {step === "connect" && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="font-bold font-headline text-lg mb-1">Step 2: Enter Your Connection Details</h3>
            <p className="text-xs text-textDim mb-6">
              After deploying the CloudFormation template, enter the details below.
            </p>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">AWS Account ID *</label>
                  <input
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40"
                    placeholder="123456789012"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">Label (optional)</label>
                  <input
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    className="w-full glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40"
                    placeholder="Production Account"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">Role ARN *</label>
                <input
                  value={roleArn}
                  onChange={(e) => setRoleArn(e.target.value)}
                  className="w-full glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40 font-mono text-xs"
                  placeholder="arn:aws:iam::123456789012:role/CostPilotAccessRole"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-textDim mb-1.5 uppercase tracking-wider">External ID *</label>
                <div className="flex gap-2">
                  <input
                    value={externalId}
                    onChange={(e) => setExternalId(e.target.value)}
                    className="flex-1 glass-input rounded-lg py-2.5 px-4 text-sm text-text focus:outline-none focus:ring-1 ring-primary/40 font-mono text-xs"
                    placeholder="Auto-filled from Step 1"
                    readOnly
                  />
                  <CopyBtn value={externalId} label="ext_id_form" copied={copied} onCopy={copyToClipboard} />
                </div>
              </div>

              {/* Region Selector */}
              <div>
                <label className="block text-xs font-semibold text-textDim mb-2 uppercase tracking-wider">Regions to Scan *</label>
                <div className="flex flex-wrap gap-2">
                  {AWS_REGIONS.map((r) => (
                    <button
                      key={r}
                      onClick={() => toggleRegion(r)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        selectedRegions.includes(r)
                          ? "bg-primary/15 border border-primary/50 text-primary"
                          : "glass-panel text-textDim hover:text-textMuted"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => setStep("deploy")} className="px-4 py-2 rounded-lg ghost-button text-xs font-semibold">
              ← Back
            </button>
            <button
              onClick={handleSaveConnection}
              disabled={saving || !accountId.trim() || !roleArn.trim()}
              className="px-6 py-2.5 rounded-xl optimizer-gradient optimizer-glow text-sm font-semibold flex items-center gap-2 disabled:opacity-50 transition-all"
            >
              <span className="material-symbols-outlined text-lg">{saving ? "progress_activity" : "link"}</span>
              {saving ? "Connecting..." : "Connect Account"}
            </button>
          </div>
        </div>
      )}

      {/* How It Works */}
      {step !== "done" && (
        <div className="mt-10 glass-panel p-6 rounded-2xl">
          <h3 className="font-bold font-headline text-sm mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-base">info</span>
            How it works
          </h3>
          <div className="grid grid-cols-3 gap-6">
            {[
              { icon: "description", title: "1. Generate Template", desc: "We create a CloudFormation template with a unique External ID for your account." },
              { icon: "cloud_upload", title: "2. Deploy in AWS", desc: "You deploy the template which creates an IAM role with least-privilege read-only access." },
              { icon: "link", title: "3. Connect", desc: "Enter the Role ARN — our backend uses STS AssumeRole with temporary credentials. No keys stored." },
            ].map((item) => (
              <div key={item.title} className="text-center space-y-2">
                <div className="w-10 h-10 mx-auto rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary text-lg">{item.icon}</span>
                </div>
                <p className="text-xs font-bold font-headline">{item.title}</p>
                <p className="text-[11px] text-textDim leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Small reusable components ──

function InfoField({ label, value, full }: { label: string; value: string; full?: boolean }) {
  return (
    <div className={full ? "col-span-2" : ""}>
      <span className="text-[10px] font-bold text-textDim uppercase tracking-wider">{label}</span>
      <p className="text-sm font-mono mt-0.5 break-all">{value}</p>
    </div>
  );
}

function CopyBtn({
  value, label, copied, onCopy,
}: { value: string; label: string; copied: string | null; onCopy: (v: string, k: string) => void }) {
  return (
    <button
      onClick={() => onCopy(value, label)}
      className="px-2 py-1 rounded-md ghost-button text-[10px] font-bold flex items-center gap-1"
    >
      <span className="material-symbols-outlined text-xs">{copied === label ? "check" : "content_copy"}</span>
      {copied === label ? "Copied" : "Copy"}
    </button>
  );
}
