/* === AWS Cost Optimizer — Tabbed Dashboard JS === */

let allResources = [];
let currentFilter = "all";
let searchQuery = "";
let sortColumn = "waste";
let sortDirection = "desc";
let trendChart = null;
let breakdownChart = null;
let serviceBarChart = null;
let highestSeverity = "low";


Chart.defaults.color = "rgba(246,247,235,0.55)";

// === UTILS ===
function animateValue(id, value, prefix = "") {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    if (value === undefined || value === null) {
        obj.textContent = prefix + (prefix === "$" ? "0.00" : "0");
        return;
    }
    
    if (typeof value !== 'number') {
        obj.textContent = prefix + value;
        return;
    }

    const start = 0;
    const end = value;
    const duration = 1000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = progress * (2 - progress);
        const current = start + (end - start) * ease;
        
        if (prefix === "$") {
            obj.textContent = prefix + current.toFixed(2);
        } else {
            obj.textContent = Math.floor(current);
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            if (prefix === "$") {
                obj.textContent = prefix + end.toFixed(2);
            } else {
                obj.textContent = end;
            }
        }
    }
    requestAnimationFrame(update);
}

function formatTimeAgo(dateString) {
    const now = new Date();
    const past = new Date(dateString);
    const diffMs = now - past;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHr / 24);

    if (diffSec < 60) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    return `${diffDays}d ago`;
}
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;

const COLORS = {
    EBS: { bg: "rgba(233,79,55,0.15)", border: "#E94F37", solid: "#f0735f" },
    "Stopped EC2": { bg: "rgba(233,79,55,0.12)", border: "#E94F37", solid: "#f0735f" },
    "Idle EC2": { bg: "rgba(233,79,55,0.15)", border: "#E94F37", solid: "#f0735f" },
    ElasticIP: { bg: "rgba(245,158,11,0.15)", border: "#f59e0b", solid: "#fbbf24" },
    Snapshot: { bg: "rgba(34,197,94,0.15)", border: "#22c55e", solid: "#4ade80" },
};

// === INIT ===
document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initTypingEffect();
    checkAuthStatus();
    setupFilters();
    setupSorting();
    loadAIProvider();
    switchTab('home');
});

// === AUTHENTICATION ===
let authMode = 'login';

async function checkAuthStatus() {
    try {
        const res = await fetch("/api/auth/status");
        const data = await res.json();
        const overlay = document.getElementById("auth-overlay");
        
        if (data.authenticated) {
            if (overlay) overlay.style.display = "none";
            
            // Only load data once we know we are authenticated
            loadDashboard();
            syncStatus(true);

            // Check if AWS is configured
            const sRes = await fetch("/api/settings");
            if (sRes.ok) {
                const sData = await sRes.json();
                if (!sData.aws.configured) {
                    switchTab('settings');
                    showToast('warning', 'Setup Required', 'Please configure your AWS credentials to continue.', 10000);
                }
            }
        } else {
            if (overlay) overlay.style.display = "flex";
        }
    } catch (e) {
        console.error("Auth check failed", e);
    }
}

function toggleAuthMode() {
    authMode = authMode === 'login' ? 'signup' : 'login';
    document.getElementById('auth-title').textContent = authMode === 'login' ? 'Welcome to CostPilot' : 'Create an Account';
    document.getElementById('auth-submit-btn').textContent = authMode === 'login' ? 'Sign In' : 'Sign Up';
    const toggleBtn = document.querySelector('button[onclick="toggleAuthMode()"]');
    document.getElementById('auth-toggle-text').textContent = authMode === 'login' ? "Don't have an account?" : 'Already have an account?';
    if(toggleBtn) toggleBtn.textContent = authMode === 'login' ? 'Sign Up' : 'Sign In';
    document.getElementById('auth-error').style.display = 'none';
}

async function handleAuth(e) {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const errorEl = document.getElementById('auth-error');
    
    try {
        const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/signup';
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            errorEl.style.display = 'none';
            if (authMode === 'signup') {
                document.getElementById('auth-card-main').style.display = 'none';
                document.getElementById('aws-connect-card').style.display = 'block';
            } else {
                checkAuthStatus();
            }
        } else {
            errorEl.textContent = data.message;
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.reload();
    } catch (e) {
        console.error("Logout failed", e);
    }
}

async function handleConnectAWS(e) {
    e.preventDefault();
    const accessKey = document.getElementById('setup-aws-key').value;
    const secretKey = document.getElementById('setup-aws-secret').value;
    const region = document.getElementById('setup-aws-region').value;
    const errorEl = document.getElementById('aws-setup-error');
    
    try {
        const res = await fetch('/api/auth/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ access_key: accessKey, secret_key: secretKey, region })
        });
        const data = await res.json();
        
        if (res.ok) {
            errorEl.style.display = 'none';
            showToast('success', 'AWS Connected', 'Scanning will begin automatically.');
            checkAuthStatus();
        } else {
            errorEl.textContent = data.message;
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

function skipAWSSetup() {
    checkAuthStatus();
}




function initTypingEffect() {
    const words = ["Idle Cloud Resources", "Unused EBS Volumes", "Abandoned Snapshots", "Orphaned Elastic IPs"];
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    const target = document.getElementById("typing-text");
    if (!target) return;
    
    function type() {
        const currentWord = words[wordIndex];
        if (isDeleting) {
            target.textContent = currentWord.substring(0, charIndex - 1);
            charIndex--;
        } else {
            target.textContent = currentWord.substring(0, charIndex + 1);
            charIndex++;
        }
        
        let typingSpeed = isDeleting ? 50 : 100;
        
        if (!isDeleting && charIndex === currentWord.length) {
            typingSpeed = 2000;
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            wordIndex = (wordIndex + 1) % words.length;
            typingSpeed = 500;
        }
        setTimeout(type, typingSpeed);
    }
    type();
}


async function loadAIProvider() {
    try {
        const res = await fetch("/api/ai-provider");
        const data = await res.json();
        if (data && data.provider) {
            const titleMain = document.getElementById("ai-provider-title-main");
            const descMain = document.getElementById("ai-provider-desc-main");
            const subtitleChat = document.getElementById("ai-provider-subtitle-chat");
            
            if (titleMain) titleMain.textContent = data.provider;
            if (descMain) descMain.textContent = `Click "Ask AI" to generate cost-saving recommendations powered by ${data.provider}...`;
            if (subtitleChat) subtitleChat.textContent = `Chat directly with ${data.provider} about your infrastructure waste`;
        }
    } catch (e) {
        console.error("Failed to load AI provider", e);
    }
}


// === TAB SWITCHING ===
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    const tab = document.getElementById("tab-" + tabId);
    const nav = document.getElementById("nav-" + tabId);
    if (tab) tab.classList.add("active");
    if (nav) nav.classList.add("active");
    
    const canvas = document.getElementById("particle-canvas");
    if (canvas) {
        canvas.style.display = (tabId === "home") ? "block" : "none";
    }

    if (tabId === "dashboard" || tabId === "analytics") loadDashboard();
    if (tabId === "settings") loadSettings();
    if (tabId === "alerts") loadAlerts();
    if (tabId === "active") loadActiveServices();
    if (tabId === "inventory" && typeof window.loadInventory === "function") window.loadInventory();
    if (tabId === "optimizations") {
        loadOptimizations();
        loadForecasts();
    }
}

// === PARTICLE BACKGROUND (disabled — kept as no-op) ===
function initParticles() {
    // Particle canvas removed; only the typing text animation is active.
    const canvas = document.getElementById("particle-canvas");
    if (canvas) canvas.style.display = "none";
}




// === DATA LOADING ===
async function loadDashboard() {
    try {
        // Add subtle refresh pulse to cards
        document.querySelectorAll('.card').forEach(c => {
            c.classList.remove('refreshing');
            void c.offsetWidth;
            c.classList.add('refreshing');
        });
        await Promise.all([loadSummary(), loadTrendChart(), loadResources(), loadHistory(), loadBudget(), loadAIAdvice()]);
        setTimeout(() => document.querySelectorAll('.card.refreshing').forEach(c => c.classList.remove('refreshing')), 700);
    } catch (e) { console.error("Load error:", e); }
}

async function loadSummary() {
    try {
        const res = await fetch("/api/summary");
        const d = await res.json();
        
        animateValue("stat-waste", d.total_waste, "$");
        animateValue("stat-resources", d.resources_found);
        animateValue("stat-scans", d.total_scans);
        animateValue("home-waste", d.total_waste, "$");
        animateValue("home-resources", d.resources_found);
        animateValue("home-scans", d.total_scans);

        // Live count-up ticker for annual projection
        const annualTarget = d.annual_projection;
        let annualCurrent = 0;
        const annualDuration = 2000; // 2 seconds
        const annualStart = performance.now();
        function tickAnnual(now) {
            const elapsed = now - annualStart;
            const progress = Math.min(elapsed / annualDuration, 1);
            // Ease-out cubic for smooth deceleration
            const eased = 1 - Math.pow(1 - progress, 3);
            annualCurrent = annualTarget * eased;
            const formatted = "$" + annualCurrent.toFixed(2);
            const sAnn = document.getElementById("stat-annual");
            const hAnn = document.getElementById("home-annual");
            if (sAnn) sAnn.textContent = formatted;
            if (hAnn) hAnn.textContent = formatted;
            if (progress < 1) requestAnimationFrame(tickAnnual);
        }
        requestAnimationFrame(tickAnnual);

        // Trend
        const trendEl = document.getElementById("stat-trend");
        if (d.trend_change !== 0) {
            const up = d.trend_change > 0;
            trendEl.className = "stat-trend " + (up ? "up" : "down");
            trendEl.textContent = (up ? "\u25b2" : "\u25bc") + " $" + Math.abs(d.trend_change).toFixed(2) + " vs last scan";
        } else { trendEl.textContent = ""; }
        // Status
        const st = document.getElementById("sidebar-status-text");
        if (st) st.textContent = d.last_scan ? "Last scan: " + formatTimeAgo(d.last_scan) : "No scans yet";
        // Breakdown + analytics
        renderBreakdownChart(d.breakdown);
        renderServiceBarChart(d.breakdown);
        // Projections
        setProj(d.total_waste);
        
        // Load AWS Cost
        loadAWSCost();
    } catch (e) { console.error("Error loading dashboard", e); }
}

async function loadAWSCost() {
    const body = document.getElementById("aws-cost-body");
    const periodBadge = document.getElementById("aws-cost-period");
    if (!body) return;
    
    body.innerHTML = '<div class="empty-state" style="padding:28px;"><span class="spin" style="font-size:24px;">⏳</span><p>Fetching from AWS Cost Explorer...</p></div>';
    periodBadge.innerText = "Loading";
    
    try {
        const res = await fetch("/api/aws-cost");
        const data = await res.json();
        if (data.status === "ok") {
            periodBadge.innerText = `${data.period.start} to ${data.period.end}`;
            
            let html = `<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:16px; border-bottom:1px solid rgba(246,247,235,0.08); padding-bottom:12px;">
                <span style="font-size:13px; color:rgba(246,247,235,0.55); font-weight:600; text-transform:uppercase;">Total Month-to-Date</span>
                <span style="font-size:28px; font-weight:800; color:#F6F7EB;">$${data.total.toFixed(2)}</span>
            </div>`;
            
            html += `<table style="width:100%; border-collapse:collapse;">`;
            data.services.forEach(s => {
                const pct = ((s.cost / data.total) * 100).toFixed(1);
                html += `<tr style="border-bottom:1px solid rgba(246,247,235,0.04);">
                    <td style="padding:8px 0; font-size:13px; color:rgba(246,247,235,0.8); font-weight:500;">${s.service}</td>
                    <td style="padding:8px 0; text-align:right;">
                        <span style="font-size:11px; color:rgba(246,247,235,0.55); margin-right:8px;">${pct}%</span>
                        <span style="font-size:13px; font-weight:700; color:#E94F37;">$${s.cost.toFixed(2)}</span>
                    </td>
                </tr>`;
            });
            html += `</table>`;
            body.innerHTML = html;
        } else {
            body.innerHTML = `<div class="empty-state" style="padding:28px;"><span class="empty-icon" style="color:#E94F37;">⚠️</span><p>Failed to load cost data</p><span style="font-size:12px;">${data.message}</span></div>`;
            periodBadge.innerText = "Error";
        }
    } catch (e) {
        body.innerHTML = `<div class="empty-state" style="padding:28px;"><p>Network error fetching cost data</p></div>`;
        periodBadge.innerText = "Error";
    }
}

function setProj(monthly) {
    const pm = document.getElementById("proj-monthly");
    const pq = document.getElementById("proj-quarterly");
    const pa = document.getElementById("proj-annual");
    if (pm) pm.textContent = "$" + monthly.toFixed(2);
    if (pq) pq.textContent = "$" + (monthly * 3).toFixed(2);
    if (pa) pa.textContent = "$" + (monthly * 12).toFixed(2);
}

function updateSeverity() {
    let high = 0, med = 0, low = 0;
    allResources.forEach(r => {
        if (r.severity === "high") high++;
        else if (r.severity === "medium") med++;
        else low++;
    });
    
    if (high > 0) highestSeverity = "high";
    else if (med > 0) highestSeverity = "medium";
    else highestSeverity = "low";

    const total = allResources.length || 1;
    const hb = document.getElementById("sev-high-bar");
    const mb = document.getElementById("sev-med-bar");
    const lb = document.getElementById("sev-low-bar");
    if (hb) hb.style.width = (high / total * 100) + "%";
    if (mb) mb.style.width = (med / total * 100) + "%";
    if (lb) lb.style.width = (low / total * 100) + "%";
    const hc = document.getElementById("sev-high-count");
    const mc = document.getElementById("sev-med-count");
    const lc = document.getElementById("sev-low-count");
    if (hc) hc.textContent = high;
    if (mc) mc.textContent = med;
    if (lc) lc.textContent = low;
}

// === BUDGET ===
async function loadBudget() {
    try {
        const res = await fetch("/api/budget");
        const b = await res.json();
        const card = document.getElementById("budget-card");
        if (!card) return;

        const pct = Math.min(b.percentage, 200);
        const exceeded = b.exceeded;

        // Toggle exceeded class
        card.classList.toggle("exceeded", exceeded);

        // Circular gauge
        const circumference = 326.73;
        const gaugeFill = document.getElementById("budget-gauge-fill");
        const gaugeOffset = circumference - (Math.min(pct, 100) / 100) * circumference;
        if (gaugeFill) gaugeFill.style.strokeDashoffset = gaugeOffset;

        // Percentage text
        const pctEl = document.getElementById("budget-pct");
        if (pctEl) pctEl.textContent = b.percentage.toFixed(0) + "%";

        // Status badge
        const badge = document.getElementById("budget-status-badge");
        if (badge) {
            badge.className = "budget-status-badge";
            if (exceeded) { badge.classList.add("exceeded"); badge.textContent = "EXCEEDED"; }
            else if (b.percentage >= 75) { badge.classList.add("warning"); badge.textContent = "WARNING"; }
            else { badge.classList.add("ok"); badge.textContent = "OK"; }
        }

        // Progress bar
        const barFill = document.getElementById("budget-bar-fill");
        if (barFill) barFill.style.width = Math.min(pct, 100) + "%";

        // Marker position (threshold line)
        const marker = document.getElementById("budget-bar-marker");
        const markerLabel = document.getElementById("budget-marker-label");
        if (marker) {
            const markerPos = exceeded ? (b.threshold / b.total_waste) * 100 : 100;
            marker.style.left = Math.min(markerPos, 100) + "%";
        }
        if (markerLabel) markerLabel.textContent = "$" + b.threshold.toFixed(0);

        // Values
        const we = document.getElementById("budget-waste");
        const te = document.getElementById("budget-threshold");
        const oe = document.getElementById("budget-overage");
        if (we) we.textContent = "$" + b.total_waste.toFixed(2);
        if (te) te.textContent = "$" + b.threshold.toFixed(2);
        if (oe) oe.textContent = exceeded ? "+$" + b.overage.toFixed(2) : "$0.00";

        // Alert box
        const alertIcon = document.getElementById("budget-alert-icon");
        const alertText = document.getElementById("budget-alert-text");
        if (exceeded) {
            if (alertIcon) alertIcon.textContent = "\u26a0\ufe0f";
            if (alertText) alertText.textContent = "Over budget!";
        } else if (b.percentage >= 75) {
            if (alertIcon) alertIcon.textContent = "\u26a0\ufe0f";
            if (alertText) alertText.textContent = "Approaching limit";
        } else {
            if (alertIcon) alertIcon.textContent = "\u2705";
            if (alertText) alertText.textContent = "Under budget";
        }
    } catch (e) { console.error("Budget error:", e); }
}

// === CHARTS ===
async function loadTrendChart() {
    try {
        const res = await fetch("/api/cost-trend");
        const data = await res.json();
        renderTrendChart(data);
    } catch (e) { console.error("Trend error:", e); }
}

function renderTrendChart(data) {
    const ctx = document.getElementById("trendChart");
    if (!ctx) return;
    if (trendChart) trendChart.destroy();
    const labels = data.map(d => new Date(d.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }));
    const values = data.map(d => d.total_waste_usd);
    const counts = data.map(d => d.resources_found);
    const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 250);
    gradient.addColorStop(0, "rgba(233,79,55,0.25)");
    gradient.addColorStop(1, "rgba(233,79,55,0)");
    trendChart = new Chart(ctx, {
        type: "line",
        data: { labels, datasets: [
            { label: "Monthly Waste ($)", data: values, borderColor: "#E94F37", backgroundColor: gradient, borderWidth: 2.5, fill: true, tension: 0.4, pointBackgroundColor: "#E94F37", pointBorderColor: "#1a1c1e", pointBorderWidth: 2, pointRadius: 4, pointHoverRadius: 7 },
            { label: "Resources", data: counts, borderColor: "#22c55e", borderWidth: 2, borderDash: [5, 5], fill: false, tension: 0.4, pointRadius: 3, yAxisID: "y1" }
        ]},
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
            plugins: { legend: { position: "top", labels: { usePointStyle: true, padding: 16, font: { size: 11, weight: "600" } } },
                tooltip: { backgroundColor: "rgba(26,28,30,0.95)", borderColor: "rgba(233,79,55,0.3)", borderWidth: 1, padding: 12, cornerRadius: 8 } },
            scales: { x: { grid: { color: "rgba(246,247,235,0.04)" } }, y: { grid: { color: "rgba(246,247,235,0.04)" }, ticks: { callback: v => "$" + v } }, y1: { position: "right", grid: { display: false } } }
        }
    });
}

function renderBreakdownChart(breakdown) {
    const ctx = document.getElementById("breakdownChart");
    if (!ctx) return;
    if (breakdownChart) breakdownChart.destroy();
    const labels = Object.keys(breakdown);
    const values = Object.values(breakdown);
    if (!labels.length) return;
    breakdownChart = new Chart(ctx, {
        type: "doughnut",
        data: { labels, datasets: [{ data: values, backgroundColor: labels.map(l => COLORS[l]?.bg || "rgba(148,163,184,0.15)"), borderColor: labels.map(l => COLORS[l]?.border || "#94a3b8"), borderWidth: 2, hoverOffset: 8 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: "65%",
            plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 14, font: { size: 11, weight: "600" } } },
                tooltip: { backgroundColor: "rgba(26,28,30,0.95)", borderColor: "rgba(233,79,55,0.3)", borderWidth: 1, padding: 12, cornerRadius: 8,
                    callbacks: { label: c => { const t = c.dataset.data.reduce((a, b) => a + b, 0); return " " + c.label + ": $" + c.parsed.toFixed(2) + " (" + ((c.parsed / t) * 100).toFixed(1) + "%)"; } } } }
        }
    });
}

function renderServiceBarChart(breakdown) {
    const ctx = document.getElementById("serviceBarChart");
    if (!ctx) return;
    if (serviceBarChart) serviceBarChart.destroy();
    const labels = Object.keys(breakdown);
    const values = Object.values(breakdown);
    if (!labels.length) return;
    serviceBarChart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: "Waste ($)", data: values, backgroundColor: labels.map(l => COLORS[l]?.bg || "#94A3B8"), borderColor: labels.map(l => COLORS[l]?.border || "#94A3B8"), borderWidth: 2, borderRadius: 6, barPercentage: 0.6 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: "y",
            plugins: { legend: { display: false }, tooltip: { backgroundColor: "rgba(26,28,30,0.95)", padding: 12, cornerRadius: 8, callbacks: { label: c => " $" + c.parsed.x.toFixed(2) } } },
            scales: { x: { grid: { color: "rgba(246,247,235,0.04)" }, ticks: { callback: v => "$" + v } }, y: { grid: { display: false } } }
        }
    });
}

// === RESOURCES ===
async function loadResources() {
    try {
        const res = await fetch("/api/latest-scan");
        if (!res.ok) { showEmptyTable(); return; }
        const data = await res.json();
        allResources = data.resources || [];
        updateResourceCounts();
        updateSeverity();
        renderTable(allResources);
    } catch (e) { showEmptyTable(); }
}

function updateResourceCounts() {
    const counts = { EBS: 0, EC2: 0, ElasticIP: 0, Snapshot: 0 };
    allResources.forEach(r => { if (counts[r.resource_type] !== undefined) counts[r.resource_type]++; });
    const ce = document.getElementById("count-ebs"); if (ce) ce.textContent = counts.EBS;
    const cc = document.getElementById("count-ec2"); if (cc) cc.textContent = counts.EC2;
    const ci = document.getElementById("count-eip"); if (ci) ci.textContent = counts.ElasticIP;
    const cs = document.getElementById("count-snap"); if (cs) cs.textContent = counts.Snapshot;
}

function renderTable(resources) {
    const tbody = document.getElementById("resources-tbody");
    if (!resources.length) { showEmptyTable(); return; }
    let filtered = currentFilter === "all" ? resources : resources.filter(r => r.resource_type.includes(currentFilter));
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(r => (r.resource_id + " " + (r.detail || "") + " " + r.resource_type).toLowerCase().includes(q));
    }
    const sorted = [...filtered].sort((a, b) => {
        let av, bv;
        switch (sortColumn) {
            case "type": av = a.resource_type; bv = b.resource_type; break;
            case "id": av = a.resource_id; bv = b.resource_id; break;
            case "detail": av = a.detail || ""; bv = b.detail || ""; break;
            case "waste": av = a.waste_usd; bv = b.waste_usd; break;
            case "severity": const so = { high: 3, medium: 2, low: 1 }; av = so[a.severity] || 0; bv = so[b.severity] || 0; break;
            default: av = a.waste_usd; bv = b.waste_usd;
        }
        if (typeof av === "string") return sortDirection === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
        return sortDirection === "asc" ? av - bv : bv - av;
    });
    if (!sorted.length) { tbody.innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><span class="empty-icon">🔍</span><p>No matching resources</p></div></td></tr>'; return; }
    tbody.innerHTML = sorted.map(r => {
        const tc = { EBS: "type-ebs", EC2: "type-ec2", ElasticIP: "type-eip", Snapshot: "type-snapshot" }[r.resource_type] || "";
        const ti = { EBS: "\ud83d\udcbe", EC2: "\ud83d\udda5\ufe0f", ElasticIP: "\ud83c\udf10", Snapshot: "\ud83d\udcf8" }[r.resource_type] || "\ud83d\udce6";
        const si = r.severity === "high" ? "\ud83d\udd34" : r.severity === "medium" ? "\ud83d\udfe1" : "\ud83d\udfe2";
        return '<tr><td><span class="resource-type ' + tc + '">' + ti + " " + r.resource_type + '</span></td><td><span class="resource-id">' + r.resource_id + "</span></td><td>" + (r.detail || "-") + '</td><td class="cost-cell">$' + r.waste_usd.toFixed(2) + '</td><td><span class="severity-badge severity-' + r.severity + '">' + si + " " + r.severity + '</span></td><td><span class="status-badge status-' + r.status + '">' + r.status + "</span></td><td>" + getActionButtons(r.resource_type, r.resource_id, r.status) + "</td></tr>";
    }).join("");
}

function showEmptyTable() {
    document.getElementById("resources-tbody").innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><span class="empty-icon">\ud83d\udced</span><p>No scan data yet</p><code>python main.py --scan</code></div></td></tr>';
}

// === HISTORY ===
async function loadHistory() {
    try {
        const res = await fetch("/api/scans");
        const scans = await res.json();
        const el = document.getElementById("history-timeline");
        if (!scans.length) { el.innerHTML = '<div class="empty-state"><span class="empty-icon">\ud83d\udccb</span><p>No scan history</p></div>'; return; }
        el.innerHTML = scans.map((s, i) => {
            const d = new Date(s.timestamp);
            const fmt = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
            return '<div class="history-card" onclick="loadScanDetail(' + s.id + ')"><div class="history-card-left"><span class="history-card-number">#' + (scans.length - i) + '</span><div><div class="history-card-date">' + fmt + '</div><div class="history-card-meta">' + s.resources_found + ' resources detected</div></div></div><div class="history-card-cost">$' + s.total_waste_usd.toFixed(2) + "</div></div>";
        }).join("");
    } catch (e) { console.error("History error:", e); }
}

async function clearHistory() {
    if (!confirm("Are you sure you want to clear all scan history? This will also remove the detected resources for past scans.")) return;
    try {
        const res = await fetch("/api/history/clear", { method: "POST" });
        const result = await res.json();
        if (result.status === "ok") {
            showToast("success", "History Cleared", "All scan history has been removed.");
            await refreshAllData();
        } else {
            showToast("error", "Error", result.message || "Failed to clear history.");
        }
    } catch (e) {
        showToast("error", "Network Error", "Failed to contact the server.");
        console.error("Clear history error:", e);
    }
}

async function loadScanDetail(id) {
    try {
        const res = await fetch("/api/scan/" + id + "/resources");
        allResources = await res.json();
        currentFilter = "all";
        searchQuery = "";
        updateFilterButtons();
        updateResourceCounts();
        updateSeverity();
        renderTable(allResources);
        switchTab("resources");
    } catch (e) { console.error("Scan detail error:", e); }
}

// === FILTERS & SORT ===
function setupFilters() {
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", () => { currentFilter = btn.dataset.filter; updateFilterButtons(); renderTable(allResources); });
    });
}
function updateFilterButtons() {
    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.toggle("active", btn.dataset.filter === currentFilter));
}
function setupSorting() {
    document.querySelectorAll(".sortable").forEach(th => {
        th.addEventListener("click", () => { const c = th.dataset.sort; if (sortColumn === c) sortDirection = sortDirection === "asc" ? "desc" : "asc"; else { sortColumn = c; sortDirection = "desc"; } renderTable(allResources); });
    });
}
function onSearch(val) { searchQuery = val; renderTable(allResources); }

// === EXPORT ===
function exportCSV() {
    if (!allResources.length) { alert("No data to export."); return; }
    const h = ["Type", "Resource ID", "Detail", "Cost/Month", "Severity", "Status", "Region"];
    const rows = allResources.map(r => [r.resource_type, r.resource_id, '"' + (r.detail || "").replace(/"/g, '""') + '"', r.waste_usd.toFixed(2), r.severity, r.status, r.region]);
    const csv = [h.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "aws-waste-" + new Date().toISOString().slice(0, 10) + ".csv"; a.click();
}

// === PASSWORD TOGGLE ===
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    const eyeOpen = btn.querySelector(".eye-open");
    const eyeClosed = btn.querySelector(".eye-closed");
    if (eyeOpen) eyeOpen.style.display = isHidden ? "none" : "block";
    if (eyeClosed) eyeClosed.style.display = isHidden ? "block" : "none";
}

// === SETTINGS ===
async function loadSettings() {
    try {
        const res = await fetch("/api/settings");
        const s = await res.json();
        
        // AWS
        const awsKey = document.getElementById("set-aws-key");
        const awsSecret = document.getElementById("set-aws-secret");
        const awsRegion = document.getElementById("set-aws-region");
        if (awsKey) awsKey.value = s.aws.access_key || "";
        if (awsSecret) awsSecret.value = s.aws.secret_key || "";
        if (awsRegion) awsRegion.value = s.aws.region || "ap-south-1";
        const awsRegions = document.getElementById("set-aws-regions");
        if (awsRegions) awsRegions.value = s.aws.regions || "ap-south-1";


        const awsStatus = document.getElementById("aws-status");
        if (awsStatus) {
            awsStatus.className = "settings-status " + (s.aws.configured ? "configured" : "not-configured");
            awsStatus.textContent = s.aws.configured ? "Configured" : "Not configured";
        }

        // Email
        const sh = document.getElementById("set-smtp-host");
        const sp = document.getElementById("set-smtp-port");
        const su = document.getElementById("set-smtp-user");
        const spw = document.getElementById("set-smtp-password");
        const sf = document.getElementById("set-alert-from");
        const st = document.getElementById("set-alert-to");
        if (sh) sh.value = s.email.smtp_host || "";
        if (sp) sp.value = s.email.smtp_port || "";
        if (su) su.value = s.email.smtp_user || "";
        if (spw) spw.value = s.email.smtp_password || "";
        if (sf) sf.value = s.email.alert_from || "";
        if (st) st.value = s.email.alert_to || "";

        const emailStatus = document.getElementById("email-status");
        if (emailStatus) {
            emailStatus.className = "settings-status " + (s.email.configured ? "configured" : "not-configured");
            emailStatus.textContent = s.email.configured ? "Configured" : "Not configured";
        }

        // Budget
        const budgetInput = document.getElementById("set-budget");
        if (budgetInput) budgetInput.value = s.budget.threshold;

        // App
        const snapAge = document.getElementById("set-snap-age");
        const cpuThresh = document.getElementById("set-cpu-thresh");
        if (snapAge) snapAge.value = s.app.snapshot_age_days || "";
        if (cpuThresh) cpuThresh.value = s.app.ec2_cpu_threshold || "";


        // Check schedule status
        const schedRes = await fetch("/api/schedule/status");
        const schedData = await schedRes.json();
        const schedBtn = document.getElementById("btn-schedule");
        if (schedBtn) {
            if (schedData.scheduled) {
                schedBtn.innerHTML = "Task Scheduled \u2705";
                schedBtn.style.background = "rgba(34,197,94,0.15)";
                schedBtn.style.color = "#22c55e";
                schedBtn.style.borderColor = "rgba(34,197,94,0.3)";
            } else {
                schedBtn.innerHTML = "Enable Auto-Scan";
            }
        }
    } catch (e) { console.error("Settings load error:", e); }
}

async function scheduleScan() {
    const btn = document.getElementById("btn-schedule");
    if (btn) btn.disabled = true;
    
    showToast('info', 'Scheduling...', 'Creating Windows scheduled task', 0);
    try {
        const res = await fetch("/api/schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frequency: "daily", hour: "02", minute: "00" })
        });
        const result = await res.json();
        dismissToast(document.querySelector('.toast-info'));
        if (result.status === "ok") {
            showToast('success', 'Auto-Scan Enabled', result.message);
            if (btn) {
                btn.innerHTML = "Task Scheduled \u2705";
                btn.style.background = "rgba(34,197,94,0.15)";
                btn.style.color = "#22c55e";
                btn.style.borderColor = "rgba(34,197,94,0.3)";
            }
        } else {
            showToast('error', 'Schedule Failed', result.message);
        }
    } catch (e) {
        showToast('error', 'Error', e.message);
    }
    if (btn) btn.disabled = false;
}

async function saveSettings() {
    const statusEl = document.getElementById("settings-save-status");
    const btn = document.getElementById("save-settings-btn");
    if (btn) btn.disabled = true;
    if (statusEl) { statusEl.className = "settings-save-status"; statusEl.textContent = "Saving..."; }

    const data = {
        aws_access_key: document.getElementById("set-aws-key")?.value || "",
        aws_secret_key: document.getElementById("set-aws-secret")?.value || "",
        aws_region: document.getElementById("set-aws-region")?.value || "",
        aws_regions: document.getElementById("set-aws-regions")?.value || "",
        smtp_host: document.getElementById("set-smtp-host")?.value || "",

        smtp_port: document.getElementById("set-smtp-port")?.value || "",
        smtp_user: document.getElementById("set-smtp-user")?.value || "",
        smtp_password: document.getElementById("set-smtp-password")?.value || "",
        alert_from: document.getElementById("set-alert-from")?.value || "",
        alert_to: document.getElementById("set-alert-to")?.value || "",
        budget_threshold: document.getElementById("set-budget")?.value || "",
        snapshot_age_days: document.getElementById("set-snap-age")?.value || "",
        ec2_cpu_threshold: document.getElementById("set-cpu-thresh")?.value || "",
    };


    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.status === "ok") {
            if (statusEl) { statusEl.className = "settings-save-status success"; statusEl.textContent = "\u2705 Settings saved successfully!"; }
            setTimeout(() => loadSettings(), 500);
        } else {
            if (statusEl) { statusEl.className = "settings-save-status error"; statusEl.textContent = "\u274c " + result.message; }
        }
    } catch (e) {
        if (statusEl) { statusEl.className = "settings-save-status error"; statusEl.textContent = "\u274c Failed to save"; }
    }
    if (btn) btn.disabled = false;
}

// === RUN SCAN (Improved with progress overlay) ===
function showScanOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'scan-overlay';
    overlay.id = 'scan-overlay';
    overlay.innerHTML = `
        <div class="scan-progress-card">
            <div class="scan-progress-icon" id="scan-icon">🔍</div>
            <div class="scan-progress-title" id="scan-title">Scanning AWS Infrastructure</div>
            <div class="scan-progress-subtitle" id="scan-subtitle">Connecting to AWS APIs across all regions...</div>
            <div class="scan-progress-bar-track">
                <div class="scan-progress-bar-fill" id="scan-bar" style="width: 5%"></div>
            </div>
            <div class="scan-phases" id="scan-phases">
                <div class="scan-phase active" id="phase-connect">
                    <span class="scan-phase-icon">⚡</span>
                    <span>Authenticating with AWS</span>
                </div>
                <div class="scan-phase" id="phase-regions">
                    <span class="scan-phase-icon">🌐</span>
                    <span>Scanning EC2, EBS, EIP, Snapshots, S3, Lambda</span>
                </div>
                <div class="scan-phase" id="phase-process">
                    <span class="scan-phase-icon">📊</span>
                    <span>Processing results & estimating costs</span>
                </div>
                <div class="scan-phase" id="phase-save">
                    <span class="scan-phase-icon">💾</span>
                    <span>Saving to database & syncing status</span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

function updateScanPhase(phaseId, progress, subtitle) {
    const bar = document.getElementById('scan-bar');
    const sub = document.getElementById('scan-subtitle');
    if (bar) bar.style.width = progress + '%';
    if (sub) sub.textContent = subtitle;
    
    // Mark phases
    const phases = ['phase-connect', 'phase-regions', 'phase-process', 'phase-save'];
    const idx = phases.indexOf(phaseId);
    phases.forEach((p, i) => {
        const el = document.getElementById(p);
        if (!el) return;
        if (i < idx) {
            el.className = 'scan-phase done';
            el.querySelector('.scan-phase-icon').textContent = '✅';
        } else if (i === idx) {
            el.className = 'scan-phase active';
        } else {
            el.className = 'scan-phase';
        }
    });
}

function closeScanOverlay(success = true) {
    const overlay = document.getElementById('scan-overlay');
    if (!overlay) return;
    
    if (success) {
        const icon = document.getElementById('scan-icon');
        const title = document.getElementById('scan-title');
        const bar = document.getElementById('scan-bar');
        if (icon) icon.textContent = '✅';
        if (title) { title.textContent = 'Scan Complete!'; title.style.background = 'linear-gradient(135deg, #22c55e, #06f6f6)'; title.style.webkitBackgroundClip = 'text'; }
        if (bar) bar.style.width = '100%';
        
        // Mark all phases done
        ['phase-connect', 'phase-regions', 'phase-process', 'phase-save'].forEach(p => {
            const el = document.getElementById(p);
            if (el) { el.className = 'scan-phase done'; el.querySelector('.scan-phase-icon').textContent = '✅'; }
        });
        
        // Flash success burst
        const burst = document.createElement('div');
        burst.className = 'scan-success-burst';
        document.body.appendChild(burst);
        setTimeout(() => burst.remove(), 800);
    }
    
    setTimeout(() => {
        overlay.classList.add('closing');
        setTimeout(() => overlay.remove(), 400);
    }, success ? 1200 : 300);
}

async function runScan() {
    const btn = document.getElementById("run-scan-btn");
    const sidebarBtn = document.getElementById("sidebar-scan-btn");
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spin-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg></span> Scanning...';
    }
    if (sidebarBtn) {
        sidebarBtn.disabled = true;
        sidebarBtn.innerHTML = '<span class="spin-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg></span> Scanning...';
    }
    
    showScanOverlay();

    try {
        const res = await fetch("/api/scan/run", { method: "POST" });
        const result = await res.json();
        if (result.status === "ok") {
            let pollCount = 0;
            while (true) {
                await new Promise(resolve => setTimeout(resolve, 2500));
                pollCount++;
                const statusRes = await fetch("/api/scan/status");
                const statusData = await statusRes.json();
                
                // Animate phases based on poll count (approximate timing)
                if (pollCount === 1) updateScanPhase('phase-connect', 15, 'AWS credentials verified. Starting region scan...');
                if (pollCount === 2) updateScanPhase('phase-regions', 30, 'Scanning EC2 instances across regions...');
                if (pollCount === 3) updateScanPhase('phase-regions', 45, 'Scanning EBS volumes and Elastic IPs...');
                if (pollCount === 4) updateScanPhase('phase-regions', 55, 'Scanning S3 buckets and Lambda functions...');
                if (pollCount === 5) updateScanPhase('phase-regions', 65, 'Scanning EBS snapshots...');
                if (pollCount >= 6 && pollCount < 8) updateScanPhase('phase-process', 75, 'Estimating costs and calculating waste...');
                if (pollCount >= 8) updateScanPhase('phase-save', 85, 'Saving results to database...');
                
                if (statusData.status === "success") {
                    updateScanPhase('phase-save', 95, 'Finalizing...');
                    closeScanOverlay(true);
                    // Refresh everything
                    await refreshAllData();
                    showToast('success', 'Scan Complete', `AWS scan finished. All data refreshed.`);
                    break;
                } else if (statusData.status === "failed") {
                    closeScanOverlay(false);
                    showToast('error', 'Scan Failed', statusData.message || 'Unknown error');
                    break;
                }
            }
        } else {
            closeScanOverlay(false);
            showToast('error', 'Scan Error', result.message || 'Could not start scan');
        }
    } catch (e) {
        closeScanOverlay(false);
        showToast('error', 'Connection Error', 'Could not reach the dashboard server.');
        console.error("Run scan error:", e);
    }

    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Scan Now';
    }
    if (sidebarBtn) {
        sidebarBtn.disabled = false;
        sidebarBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Scan';
    }
}

// === REFRESH ALL DATA (with visual pulse) ===
async function refreshAllData(showPulse = true) {
    if (showPulse) {
        document.querySelectorAll('.stat-card').forEach(c => {
            c.classList.remove('refreshing');
            void c.offsetWidth; // Force reflow
            c.classList.add('refreshing');
        });
    }
    
    await Promise.all([
        loadSummary(),
        loadTrendChart(),
        loadResources(),
        loadHistory(),
        loadBudget(),
        loadActiveServices(),
        typeof window.loadInventory === "function" ? window.loadInventory(true) : Promise.resolve()
    ]);
    
    // Clean up pulse class
    setTimeout(() => {
        document.querySelectorAll('.stat-card.refreshing').forEach(c => c.classList.remove('refreshing'));
    }, 700);
}


// === SYNC STATUS ===
async function syncStatus(silent = false) {
    const btn = document.getElementById("sync-status-btn");
    if (btn && !silent) {
        btn.disabled = true;
        btn.innerHTML = '<svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg> Syncing...';
    }

    try {
        const res = await fetch("/api/sync-status", { method: "POST" });
        const result = await res.json();
        if (!silent) {
            if (result.status === "ok") {
                showToast('success', 'Sync Complete', result.message || `Reconciled ${result.synced} resources`);
                await refreshAllData();
            } else {
                showToast('error', 'Sync Failed', result.message);
            }
        } else if (result.synced > 0) {
            // Silent sync found stale resources — refresh data quietly
            await refreshAllData(false);
        }
    } catch (e) {
        if (!silent) showToast('error', 'Sync Error', e.message);
    }

    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '🔄 Sync Status';
    }
}
window.syncStatus = syncStatus;



// === ALERTS ===
async function loadAlerts() {
    try {
        const res = await fetch("/api/alerts");
        const alerts = await res.json();
        const el = document.getElementById("alerts-timeline");
        if (!el) return;

        if (!alerts.length) {
            el.innerHTML = '<div class="empty-state"><span class="empty-icon">\ud83d\udd14</span><p>No alerts yet</p><code>Alerts appear when budget threshold is exceeded</code></div>';
            return;
        }

        el.innerHTML = alerts.map(a => {
            const isExceeded = a.alert_type === "budget_exceeded";
            const cls = isExceeded ? "alert-exceeded" : "alert-ok";
            const icon = isExceeded ? "\ud83d\udea8" : "\u2705";
            const d = new Date(a.timestamp);
            const fmt = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
            const emailBadge = a.email_sent
                ? '<span class="alert-email-badge alert-email-sent">Email Sent</span>'
                : '<span class="alert-email-badge alert-email-failed">No Email</span>';
            return '<div class="alert-card ' + cls + '">'
                + '<div class="alert-card-icon">' + icon + '</div>'
                + '<div class="alert-card-body">'
                + '<div class="alert-card-message">' + (a.message || "Budget alert") + '</div>'
                + '<div class="alert-card-time">' + fmt + '</div>'
                + '</div>'
                + '<div class="alert-card-right">'
                + '<span class="alert-card-amount">$' + a.total_waste.toFixed(2) + '</span>'
                + emailBadge
                + '</div></div>';
        }).join("");
    } catch (e) { console.error("Alerts error:", e); }
}

async function clearAlerts() {
    if (!confirm("Are you sure you want to clear all alerts?")) return;
    try {
        const res = await fetch("/api/alerts/clear", { method: "POST" });
        const result = await res.json();
        if (result.status === "ok") {
            showToast("success", "Alerts Cleared", "All alert history has been removed.");
            await loadAlerts();
        } else {
            showToast("error", "Error", result.message || "Failed to clear alerts.");
        }
    } catch (e) {
        showToast("error", "Network Error", "Failed to contact the server.");
        console.error("Clear alerts error:", e);
    }
}

// === ACTIVE SERVICES ===
async function loadActiveServices() {
    try {
        const tbodyAct = document.getElementById("active-tbody");
        const tbodyStop = document.getElementById("stopped-tbody");
        const skeletonRows = Array(4).fill(0).map(() => `
            <tr>
                <td colspan="6" style="padding:0; border:none; background:transparent;">
                    <div class="aws-skeleton-row">
                        <div class="aws-skeleton-cell sk-type"></div>
                        <div class="aws-skeleton-cell sk-id"></div>
                        <div class="aws-skeleton-cell sk-detail"></div>
                        <div class="aws-skeleton-cell sk-region"></div>
                        <div class="aws-skeleton-cell sk-status"></div>
                        <div class="aws-skeleton-cell sk-action"></div>
                    </div>
                </td>
            </tr>
        `).join("");
        
        if (tbodyAct) tbodyAct.innerHTML = skeletonRows;
        if (tbodyStop) tbodyStop.innerHTML = skeletonRows;
        
        const res = await fetch("/api/active");
        const allInfra = await res.json();
        
        // Filter into running vs stopped
        const active = allInfra.filter(r => {
            const type = r.resource_type || r.type;
            return (type === 'EC2' && r.status === 'running') ||
            (type === 'EBS' && r.status === 'in-use') ||
            (type === 'RDS' && r.status === 'available');
        });
        
        const stopped = allInfra.filter(r => {
            const type = r.resource_type || r.type;
            return (type === 'EC2' && r.status === 'stopped') ||
            (type === 'EBS' && r.status === 'available') ||
            (type === 'RDS' && r.status === 'stopped');
        });

        // Update active table
        if (!active.length) {
            if (tbodyAct) tbodyAct.innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><span class="empty-icon">✅</span><p>No running services found</p></div></td></tr>';
        } else {
            if (tbodyAct) tbodyAct.innerHTML = active.map(r => {
                const type = r.resource_type || r.type;
                const id = r.resource_id || r.id;
                const ti = { EBS: "💾", EC2: "🖥️", RDS: "🗄️" }[type] || "📦";
                return `<tr>
                    <td><span class="resource-type" style="color:#10b981; background:rgba(16,185,129,0.1)">${ti} ${type}</span></td>
                    <td><span class="resource-id">${id}</span></td>
                    <td>${r.detail || "-"}</td>
                    <td>${r.region}</td>
                    <td><span class="status-badge" style="color:#10b981; background:rgba(16,185,129,0.15); display: inline-flex; align-items: center;"><span class="pulse-indicator pulse-indicator-running"></span>${r.status}</span></td>
                    <td style="text-align:right;">${getActionButtons(type, id, r.status)}</td>
                </tr>`;
            }).join("");
        }

        // Update stopped table
        const stopCount = document.getElementById("stopped-count");
        if (stopCount) stopCount.innerText = stopped.length;

        if (!stopped.length) {
            if (tbodyStop) tbodyStop.innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><span class="empty-icon">✅</span><p>No stopped services found</p></div></td></tr>';
        } else {
            if (tbodyStop) tbodyStop.innerHTML = stopped.map(r => {
                const type = r.resource_type || r.type;
                const id = r.resource_id || r.id;
                const ti = { EBS: "💾", EC2: "🖥️", RDS: "🗄️" }[type] || "📦";
                return `<tr>
                    <td><span class="resource-type" style="color:#f59e0b; background:rgba(245,158,11,0.1)">${ti} ${type}</span></td>
                    <td><span class="resource-id">${id}</span></td>
                    <td>${r.detail || "-"}</td>
                    <td>${r.region}</td>
                    <td><span class="status-badge" style="color:#f59e0b; background:rgba(245,158,11,0.15); display: inline-flex; align-items: center;"><span class="pulse-indicator pulse-indicator-stopped"></span>${r.status}</span></td>
                    <td style="text-align:right;">${getActionButtons(type, id, r.status)}</td>
                </tr>`;
            }).join("");
        }


    } catch (e) {
        console.error("Active services error:", e);
        const tbodyAct = document.getElementById("active-tbody");
        const tbodyStop = document.getElementById("stopped-tbody");
        if (tbodyAct) tbodyAct.innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><p>Error fetching services</p></div></td></tr>';
        if (tbodyStop) tbodyStop.innerHTML = '<tr class="empty-row"><td colspan="6"><div class="empty-state"><p>Error fetching services</p></div></td></tr>';
    }
}

// === TOAST NOTIFICATION SYSTEM ===
function showToast(type, title, message, duration = 10000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || '🔔'}</span>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-msg">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="dismissToast(this.parentElement)">×</button>
    `;
    container.appendChild(toast);
    if (duration > 0) setTimeout(() => dismissToast(toast), duration);
    toast.onclick = (e) => { if (!e.target.classList.contains('toast-close')) dismissToast(toast); };
    return toast;
}
function dismissToast(toast) {
    if (!toast || toast.classList.contains('hiding')) return;
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
}

// === ACTION HANDLERS ===
window.performAction = async function(action, resourceType, resourceId, btnEl) {
    const actionLabel = action.charAt(0).toUpperCase() + action.slice(1);
    const confirmed = confirm(`Are you sure you want to ${action} this resource?\n\nID: ${resourceId}\nType: ${resourceType}`);
    if (!confirmed) return;

    // Button loading state
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.classList.add('loading');
        // Disable all sibling buttons too
        const group = btnEl.closest('.action-btn-group');
        if (group) group.querySelectorAll('.action-btn').forEach(b => b.disabled = true);
    }

    const loadingToast = showToast('info', `${actionLabel} in progress...`, `Sending command to AWS for ${resourceId}`, 0);

    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, resource_type: resourceType, resource_id: resourceId })
        });
        const result = await res.json();
        dismissToast(loadingToast);

        if (result.status === 'ok') {
            showToast('success', `${actionLabel} Successful`, result.message || `${resourceId} has been ${action}ped.`);
            
            let targetRow = btnEl ? btnEl.closest('tr') : null;
            if (targetRow) {
                targetRow.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                targetRow.style.opacity = '0';
                targetRow.style.transform = 'translateX(30px)';
                setTimeout(async () => {
                    await refreshAllData();
                }, 400);
            } else {
                await refreshAllData();
            }
        }
 else {
            showToast('error', `${actionLabel} Failed`, result.message || 'An unexpected error occurred.');
            // Re-enable buttons on failure
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.classList.remove('loading');
                const group = btnEl.closest('.action-btn-group');
                if (group) group.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
            }
        }
    } catch (e) {
        dismissToast(loadingToast);
        showToast('error', 'Connection Error', 'Could not reach the server. Check if the dashboard is running.');
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.classList.remove('loading');
        }
    }
};

function getActionButtons(type, id, status = '') {
    const t = type.toLowerCase();
    const st = (status || '').toLowerCase();
    const safeId = id.replace(/'/g, "\\'");
    const safeType = type.replace(/'/g, "\\'");
    let btns = [];

    const tooltips = {
        stop:    'Stops this instance and halts compute charges. Data is preserved.',
        start:   'Starts this stopped instance so it becomes available again.',
        restart: 'Reboots the instance without losing data or its IP address.',
        deleteEC2:      'Permanently terminates this instance. This cannot be undone.',
        deleteEBS:      'Deletes this volume. All stored data will be permanently lost.',
        deleteEIP:      'Releases this IP back to AWS and stops the hourly charge.',
        deleteSnapshot: 'Deletes this snapshot. The backup will be gone permanently.',
        deleteRDS:      'Permanently deletes this database. All data will be lost.',
        deleteDefault:  'Permanently removes this resource from your AWS account.',
    };

    const makeBtn = (action, label, cls, tipKey) => {
        const tip = tooltips[tipKey] || tooltips.deleteDefault;
        return `<span class="has-tooltip">
            <button class="action-btn ${cls}" onclick="performAction('${action}','${safeType}','${safeId}',this)">
                <span class="btn-label">${label}</span>
            </button>
            <span class="tooltip-text">${tip}</span>
        </span>`;
    };

    if (t.includes('ec2') || t.includes('rds')) {
        if (st === 'running' || t.includes('active')) {
            btns.push(makeBtn('stop',    'Stop',    'btn-stop',    'stop'));
            btns.push(makeBtn('restart', 'Restart', 'btn-restart', 'restart'));
        } else {
            btns.push(makeBtn('start', 'Start', 'btn-start', 'start'));
        }
    }

    const deleteKey = t.includes('ebs') ? 'deleteEBS'
                    : t.includes('eip') || t.includes('elastic') ? 'deleteEIP'
                    : t.includes('snapshot') ? 'deleteSnapshot'
                    : t.includes('rds') ? 'deleteRDS'
                    : t.includes('ec2') ? 'deleteEC2'
                    : 'deleteDefault';
    btns.push(makeBtn('delete', 'Delete', 'btn-delete', deleteKey));

    return `<div class="action-btn-group">${btns.join('')}</div>`;
}

// === AI ADVISOR SYSTEM ===
async function loadAIAdvice(force = false) {
    const container = document.getElementById("ai-advice-container");
    if (!container) return;
    
    // Show loading state
    container.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; color: #eab308;">
            <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
            <span style="font-family: inherit;">Analyzing cloud infrastructure...</span>
        </div>
    `;
    
    try {
        const res = await fetch(`/api/ai-advice?force=${force}`);

        const data = await res.json();
        
        if (data.status === "ok") {
            let text = data.advice;
            
            // Replace markdown-like syntax
            text = text
                .replace(/^### (.*?)$/gm, '<h3 style="background: linear-gradient(90deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 18px; margin-bottom: 8px; font-weight: 700; font-size: 16px;">$1</h3>')
                .replace(/^## (.*?)$/gm, '<h2 style="background: linear-gradient(90deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 22px; margin-bottom: 12px; font-weight: 800; font-size: 18px;">$1</h2>')
                .replace(/^# (.*?)$/gm, '<h1 style="background: linear-gradient(90deg, #4f46e5, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 26px; margin-bottom: 16px; font-weight: 900; font-size: 22px;">$1</h1>')
                .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #60a5fa; font-weight: 600;">$1</strong>')
                .replace(/^\* (.*?)$/gm, '<div class="ai-recommendation-item" style="margin-left: 4px; margin-bottom: 8px; color: #e2e8f0; padding: 12px 16px; background: rgba(255,255,255,0.03); border-left: 3px solid #6366f1; border-radius: 0 10px 10px 0; backdrop-filter: blur(4px); animation: slideIn 0.4s ease forwards;">$1</div>')
                .replace(/^\- (.*?)$/gm, '<div class="ai-recommendation-item" style="margin-left: 4px; margin-bottom: 8px; color: #e2e8f0; padding: 12px 16px; background: rgba(255,255,255,0.03); border-left: 3px solid #6366f1; border-radius: 0 10px 10px 0; backdrop-filter: blur(4px); animation: slideIn 0.4s ease forwards;">$1</div>')
                .replace(/\n/g, '<br>');
                
            container.innerHTML = `<div style="color: #f8fafc; font-size: 14px; line-height: 1.8; letter-spacing: 0.2px;">${text}</div>`;

            const ribbon = document.getElementById("hero-insight-text");
            if (ribbon && data.advice) {
                const adviceLines = data.advice.split('\n').filter(l => l.trim().startsWith('*') || l.trim().startsWith('-') || (l.trim() && !l.trim().startsWith('#')));
                if (adviceLines.length > 0) {
                    let firstTip = adviceLines[0].replace(/^[\*\-\s]+/, '').trim();
                    firstTip = firstTip.replace(/\*\*/g, '');
                    ribbon.innerText = "AI Insight: " + (firstTip.length > 110 ? firstTip.substring(0, 110) + "..." : firstTip);
                }
            }


        } else {
            container.innerHTML = `<span style="color: #ef4444;">${data.advice || data.message || 'Unknown error occurred.'}</span>`;
        }
    } catch (e) {
        console.error("AI Advisor error:", e);
        container.innerHTML = `<span style="color: #ef4444;">Failed to connect to the backend AI service. Ensure Ollama is running.</span>`;
    }
}

let chatHistory = [];

async function sendChatMessage() {
    const inputEl = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send-btn");
    const message = inputEl.value.trim();
    
    if (!message) return;
    
    inputEl.value = "";
    inputEl.disabled = true;
    sendBtn.disabled = true;
    
    const messagesContainer = document.getElementById("chat-messages");
    
    const userDiv = document.createElement("div");
    userDiv.className = "chat-message user";
    userDiv.innerHTML = `
        <div class="chat-bubble user" style="background: #2563eb; padding: 12px 16px; border-radius: 12px; max-width: 80%; align-self: flex-end; margin-left: auto; color: white;">
            ${message}
        </div>
    `;
    messagesContainer.appendChild(userDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "chat-message ai loading";
    loadingDiv.id = "chat-loading";
    loadingDiv.innerHTML = `
        <div class="chat-bubble ai" style="background: #1e293b; border: 1px solid #334155; padding: 12px 16px; border-radius: 12px; align-self: flex-start; color: #94a3b8;">
            AI is typing...
        </div>
    `;
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const res = await fetch("/api/ai-chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, history: chatHistory })
        });
        const result = await res.json();
        
        document.getElementById("chat-loading").remove();
        
        if (result.status === "ok") {
            const aiDiv = document.createElement("div");
            aiDiv.className = "chat-message ai";
            
            let text = result.reply;
            text = text
                .replace(/\n/g, "<br>")
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/\*(.*?)\*/g, "<em>$1</em>");
                
            aiDiv.innerHTML = `
                <div class="chat-bubble ai" style="background: #1e293b; border: 1px solid #334155; padding: 12px 16px; border-radius: 12px; max-width: 80%; align-self: flex-start; color: #e2e8f0;">
                    ${text}
                </div>
            `;
            messagesContainer.appendChild(aiDiv);
            
            chatHistory.push({ sender: "user", message: message });
            chatHistory.push({ sender: "ai", message: result.reply });
        } else {
            alert("AI Error: " + result.message);
        }
    } catch (e) {
        console.error("Chat error:", e);
        if (document.getElementById("chat-loading")) {
            document.getElementById("chat-loading").remove();
        }
        alert("Failed to reach AI endpoint.");
    }
    
    inputEl.disabled = false;
    sendBtn.disabled = false;
    inputEl.focus();
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


// === CLOUD INVENTORY ===
let allInventory = [];
let activeInventoryFilter = "all";

window.loadInventory = async function(force = false) {
    const tbody = document.getElementById("inventory-tbody");
    if (!tbody) return;
    
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7"><div class="empty-state"><span class="spin" style="font-size:28px;">⏳</span><p>Aggregating cross-account inventory data...</p></div></td></tr>';
    
    try {
        const url = force ? `/api/inventory?force=true&_t=${Date.now()}` : '/api/inventory';
        const res = await fetch(url, { cache: "no-store" });
        
        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }
        
        const items = await res.json();
        
        allInventory = [];
        
        if (Array.isArray(items)) {
            items.forEach(r => {
                const cat = r.category || "Other";
                const isWaste = cat === "Waste";
                const isActive = cat === "Healthy / Active";
                
                let color, bg, pulse;
                if (isWaste) {
                    color = "#ef4444";
                    bg = "rgba(239,68,68,0.15)";
                    pulse = "pulse-indicator-stopped";
                } else if (isActive) {
                    color = "#10b981";
                    bg = "rgba(16,185,129,0.15)";
                    pulse = "pulse-indicator-running";
                } else {
                    color = "#f59e0b";
                    bg = "rgba(245,158,11,0.15)";
                    pulse = "pulse-indicator-stopped";
                }
                
                allInventory.push({
                    type: r.type || "Unknown",
                    id: r.id || "-",
                    detail: r.detail || "-",
                    region: r.region || "-",
                    status: r.status || "unknown",
                    cost: Number(r.cost) || 0,
                    category: cat,
                    cssClass: "status-badge",
                    color: color,
                    bg: bg,
                    pulse: pulse
                });
            });
        }
        
        if (allInventory.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7"><div class="empty-state"><span class="empty-icon">📭</span><p>No resources found</p><span style="font-size:12px;color:#64748b;">Run a scan first or check your AWS credentials in Settings</span></div></td></tr>';
            return;
        }
        
        renderInventory();
    } catch (e) {
        console.error("Inventory error:", e);
        tbody.innerHTML = `<tr class="empty-row"><td colspan="7"><div class="empty-state"><span class="empty-icon" style="font-size:28px;">⚠️</span><p>Failed to load inventory</p><span style="font-size:12px;color:#64748b;">${e.message}</span></div></td></tr>`;
    }
}

function renderInventory() {
    const tbody = document.getElementById("inventory-tbody");
    if (!tbody) return;
    
    let filtered = allInventory;
    
    if (activeInventoryFilter === "running") {
        filtered = allInventory.filter(r => r.category === "Healthy / Active");
    } else if (activeInventoryFilter === "stopped") {
        filtered = allInventory.filter(r => r.category === "Inactive");
    } else if (activeInventoryFilter === "waste") {
        filtered = allInventory.filter(r => r.category === "Waste");
    }
    
    if (inventorySearchQuery) {
        const q = inventorySearchQuery.toLowerCase();
        filtered = filtered.filter(r => 
            String(r.id || "").toLowerCase().includes(q) || 
            String(r.type || "").toLowerCase().includes(q) || 
            String(r.region || "").toLowerCase().includes(q) ||
            String(r.detail || "").toLowerCase().includes(q)
        );
    }
    
    if (!filtered.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="7"><div class="empty-state"><span class="empty-icon">🔍</span><p>No matching infrastructure mapped</p></div></td></tr>';
        return;
    }
    
    tbody.innerHTML = filtered.map(r => {
        const ti = { EBS: "💾", EC2: "🖥️", RDS: "🗄️", ElasticIP: "🌐", Snapshot: "📸" }[r.type] || "📦";
        const actions = getActionButtons(r.type, r.id, r.status);
        return `<tr>
            <td><span class="resource-type" style="color:${r.color}; background:${r.bg.replace('0.15', '0.1')}">${ti} ${r.type}</span></td>
            <td><span class="resource-id">${r.id}</span></td>
            <td>${r.detail}</td>
            <td>${r.region}</td>
            <td><span class="${r.cssClass}" style="color:${r.color}; background:${r.bg}; display: inline-flex; align-items: center;"><span class="pulse-indicator ${r.pulse}"></span>${r.status}</span></td>
            <td class="cost-cell" style="${r.cost === 0 ? 'color: #a1afc2 !important; font-weight: normal; text-shadow: none;' : ''}">$${r.cost.toFixed(2)}</td>
            <td><span class="badge" style="font-size:11px; font-weight:600; padding:3px 10px; border-radius:100px; border:1px solid ${r.color}; color:${r.color}; background:${r.bg.replace('0.15', '0.05')}">${r.category}</span></td>
            <td>${actions}</td>
        </tr>`;
    }).join("");
}

let inventorySearchQuery = "";

// === OPTIMIZATIONS ===
async function loadOptimizations() {
    try {
        const res = await fetch("/api/optimizations");
        const actions = await res.json();
        
        let totalSavings = 0;
        let plannedCount = 0;
        let appliedCount = 0;
        let rlUp = 0;
        let rlMaintain = 0;
        let rlDown = 0;
        
        actions.forEach(a => {
            totalSavings += parseFloat(a.estimated_savings) || 0;
            if (a.status === "planned") plannedCount++;
            else if (a.status === "applied") appliedCount++;
            const rlDecision = a?.parameters?.rl_decision || (a.action === "maintain" ? "maintain" : null);
            if (rlDecision === "scale_up") rlUp++;
            else if (rlDecision === "maintain") rlMaintain++;
            else if (rlDecision === "scale_down") rlDown++;
        });
        
        animateValue("opt-actions-count", plannedCount);
        animateValue("opt-applied-count", appliedCount);
        animateValue("opt-savings", totalSavings, "$");
        const upEl = document.getElementById("rl-scale-up-count");
        const maintainEl = document.getElementById("rl-maintain-count");
        const downEl = document.getElementById("rl-scale-down-count");
        if (upEl) upEl.textContent = String(rlUp);
        if (maintainEl) maintainEl.textContent = String(rlMaintain);
        if (downEl) downEl.textContent = String(rlDown);
        
        const tbody = document.getElementById("optimizations-tbody");
        if (!actions.length) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="8"><div class="empty-state"><span class="empty-icon">🚀</span><p>No optimizations yet</p><span style="font-size:12px;color:#64748b;">Run the optimizer to generate recommendations</span></div></td></tr>';
            return;
        }
        
        tbody.innerHTML = actions.map(a => {
            const statusColor = a.status === "applied" ? "#10b981" : a.status === "failed" ? "#ef4444" : "#f59e0b";
            const confidenceColor = a.confidence > 0.8 ? "#10b981" : a.confidence > 0.6 ? "#f59e0b" : "#ef4444";
            const actionIcon = { resize: "↔️", stop: "⏹️", delete: "🗑️" }[a.action] || "⚙️";
            
            const showApply = a.status === "planned";
            const showSkip = a.status === "planned";
            const showRollback = a.status === "applied" || a.status === "failed";

            return `<tr id="opt-row-${a.id}">
                <td><span class="resource-id">${a.resource_id || "-"}</span></td>
                <td>${a.resource_type || "-"}</td>
                <td><span style="font-weight:600;">${actionIcon} ${a.action}</span></td>
                <td><span style="font-size:12px;color:#cbd5e1;">${(a.reason || "-").substring(0, 80)}${(a.reason && a.reason.length>80? '...' : '')}</span></td>
                <td><span style="color:${confidenceColor};font-weight:600;">${(a.confidence || 0).toFixed(2)}</span></td>
                <td style="color:#10b981;font-weight:600;">$${(a.estimated_savings || 0).toFixed(2)}</td>
                <td><span id="opt-status-${a.id}" class="status-badge" style="color:${statusColor};background:${statusColor}18;border:1px solid ${statusColor}30;">${a.status}</span></td>
                <td style="display:flex; gap:6px; align-items:center;">
                    ${showApply ? `<button class="action-btn btn-apply" onclick="applyOptimization(${a.id}, this)" style="font-size:11px;padding:4px 8px;background:#059669;color:white;border:1px solid #10b981;">Apply</button>` : ``}
                    ${showSkip ? `<button class="action-btn btn-skip" onclick="skipOptimization(${a.id}, this)" style="font-size:11px;padding:4px 8px;background:#ef4444;color:white;border:1px solid #fb7185;">Skip</button>` : ``}
                    <button class="action-btn btn-explain" onclick="explainOptimization(${a.id}, this)" style="font-size:11px;padding:4px 8px;background:#0ea5e9;color:white;border:1px solid #38bdf8;">Explain</button>
                    <button class="action-btn" onclick="showOptimizationDetail(${a.id})" style="font-size:11px;padding:4px 8px;background:#4f46e5;color:white;border:1px solid #6366f1;">Details</button>
                    ${showRollback ? `<button class="action-btn btn-rollback" onclick="rollbackOptimization(${a.id}, this)" style="font-size:11px;padding:4px 8px;background:#374151;color:white;border:1px solid #6b7280;">Rollback</button>` : ``}
                    <span id="opt-audit-${a.id}" style="font-size:11px;color:#94a3b8;margin-left:6px;">—</span>
                </td>
            </tr>`;
        }).join("");

        // Kick off small audit badge refresh for visible actions
        actions.slice(0, 20).forEach(a => fetchAuditCount(a.id));
    } catch (e) {
        console.error("Optimizations error:", e);
        showToast("error", "Load Failed", e.message);
    }
}

async function loadForecasts() {
    try {
        const res = await fetch("/api/forecasts");
        const forecasts = await res.json();
        
        animateValue("opt-forecast-count", forecasts.length);
        
        const tbody = document.getElementById("forecasts-tbody");
        if (!forecasts.length) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="8"><div class="empty-state"><span class="empty-icon">📊</span><p>No forecasts available</p></div></td></tr>';
            return;
        }
        
        tbody.innerHTML = forecasts.slice(0, 20).map(f => {
            const model = f.method || "trend_fallback";
            return `<tr>
                <td><span class="resource-id">${f.resource_id || "-"}</span></td>
                <td>${f.metric_name || "-"}</td>
                <td style="color:#cbd5e1;">${(f.current_avg || 0).toFixed(1)}</td>
                <td style="color:#60a5fa;font-weight:600;">${(f.predicted_avg || 0).toFixed(1)}</td>
                <td style="color:#f59e0b;font-weight:600;">${(f.predicted_peak || 0).toFixed(1)}</td>
                <td>${f.horizon_hours || "-"}h</td>
                <td><span class="badge" style="font-size:11px;">${model}</span></td>
                <td>${f.region || "-"}</td>
            </tr>`;
        }).join("");
    } catch (e) {
        console.error("Forecasts error:", e);
    }
}

async function runOptimizationPipeline() {
    const btn = document.querySelector("button[onclick='runOptimizationPipeline()']");
    if (btn) btn.disabled = true;
    
    showToast("info", "Starting Optimizer", "Running metrics collection, forecasting, and recommendations...", 0);
    
    try {
        const res = await fetch("/api/run-optimizer", { method: "POST" });
        const result = await res.json();
        
        dismissToast(document.querySelector(".toast-info"));
        
        if (result.status === "ok") {
            showToast("success", "Optimizer Complete", `${result.actions || 0} recommendations generated`);
            const summary = result.summary || {};
            const upEl = document.getElementById("rl-scale-up-count");
            const maintainEl = document.getElementById("rl-maintain-count");
            const downEl = document.getElementById("rl-scale-down-count");
            if (upEl) upEl.textContent = String(summary.scale_up || 0);
            if (maintainEl) maintainEl.textContent = String(summary.maintain || 0);
            if (downEl) downEl.textContent = String(summary.scale_down || 0);
            await Promise.all([loadOptimizations(), loadForecasts()]);
        } else {
            showToast("error", "Optimizer Failed", result.message || "Unknown error");
        }
    } catch (e) {
        showToast("error", "Error", e.message);
    }
    
    if (btn) btn.disabled = false;
}

function showOptimizationDetail(actionId) {
    fetch(`/api/optimizations/${actionId}`)
        .then(r => r.json())
        .then(action => {
            showToast("info", 
                `${action.action.toUpperCase()} - ${action.resource_id}`,
                `<strong>Reason:</strong> ${action.reason}\n<strong>Explanation:</strong> ${action.explanation || "No explanation available"}`,
                0
            );
        })
        .catch(e => showToast("error", "Error", e.message));
}

async function applyOptimization(actionId) {
    const confirmed = confirm("Apply this optimization action? This may modify your AWS infrastructure.");
    if (!confirmed) return;
    
    const loadingToast = showToast("info", "Applying...", "Sending command to AWS...", 0);
    // Start background polling to refresh stats while apply runs
    const pollId = startRefreshPolling(2 * 60 * 1000, 3000);

    try {
        const res = await fetch(`/api/optimizations/${actionId}/apply`, { method: "POST" });
        const result = await res.json();

        if (result.status === "ok") {
            showToast("info", "Apply queued", "Waiting for action to complete...", 0);
            // Poll single action status until it finishes
            const finalAction = await pollActionStatus(actionId, 5 * 60 * 1000, 3000);
            dismissToast(loadingToast);
            clearInterval(pollId);
            if (finalAction && finalAction.status === 'applied') {
                showToast("success", "Applied", "Optimization action executed successfully");
            } else if (finalAction && finalAction.status === 'failed') {
                showToast("error", "Failed", finalAction.apply_result || 'Action failed');
            } else {
                showToast("warning", "Unknown state", 'Action did not reach a terminal state within the timeout');
            }
            await loadOptimizations();
        } else {
            dismissToast(loadingToast);
            clearInterval(pollId);
            showToast("error", "Failed", result.message);
        }
    } catch (e) {
        dismissToast(loadingToast);
        showToast("error", "Error", e.message);
    }
}

// === OPTIMIZATION ACTION HELPERS ===
async function fetchAuditCount(actionId) {
    try {
        const res = await fetch(`/api/optimizations/${actionId}/audit`);
        const data = await res.json();
        if (data && data.status === 'ok') {
            const el = document.getElementById(`opt-audit-${actionId}`);
            if (el) {
                const count = (data.logs || []).length;
                el.textContent = `logs: ${count}`;
            }
        }
    } catch (e) {
        // ignore
    }
}

async function skipOptimization(actionId, btn) {
    if (!confirm('Skip this recommendation? This will record the decision.')) return;
    try {
        if (btn) { btn.disabled = true; }
        const res = await fetch(`/api/optimizations/${actionId}/skip`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({reason: 'Skipped via UI'}) });
        const data = await res.json();
        if (data.status === 'ok') {
            showToast('success', 'Skipped', data.message || 'Action skipped');
            await loadOptimizations();
        } else {
            showToast('error', 'Skip Failed', data.message || 'Could not skip action');
        }
    } catch (e) {
        showToast('error', 'Network Error', e.message || 'Could not reach server');
    } finally { if (btn) btn.disabled = false; }
}

async function explainOptimization(actionId, btn) {
    try {
        if (btn) { btn.disabled = true; }
        const loading = showToast('info', 'Generating explanation', 'Requesting audit explanation from AI...', 0);
        const res = await fetch(`/api/optimizations/${actionId}/explain`, { method: 'POST' });
        const data = await res.json();
        dismissToast(loading);
        if (data.status === 'ok') {
            showToast('info', 'Explanation', data.explanation || 'No explanation available', 10000);
            await loadOptimizations();
        } else {
            showToast('error', 'Explain Failed', data.message || 'Could not generate explanation');
        }
    } catch (e) {
        showToast('error', 'Network Error', e.message || 'Could not reach server');
    } finally { if (btn) btn.disabled = false; }
}

async function rollbackOptimization(actionId, btn) {
    if (!confirm('Request rollback for this action? This records intent and may require manual steps.')) return;
    try {
        if (btn) btn.disabled = true;
        const res = await fetch(`/api/optimizations/${actionId}/rollback`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({reason: 'Rollback requested via UI'}) });
        const data = await res.json();
        if (data.status === 'ok') {
            showToast('success', 'Rollback Recorded', data.message || 'Rollback request saved');
            await loadOptimizations();
        } else {
            showToast('error', 'Rollback Failed', data.message || 'Could not record rollback');
        }
    } catch (e) {
        showToast('error', 'Network Error', e.message || 'Could not reach server');
    } finally { if (btn) btn.disabled = false; }
}

// Poll a single action until its status changes from applying
async function pollActionStatus(actionId, timeoutMs = 600000, intervalMs = 3000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
        try {
            const res = await fetch(`/api/optimizations/${actionId}`);
            if (!res.ok) return null;
            const action = await res.json();
            const status = action.status;
            const statusEl = document.getElementById(`opt-status-${actionId}`);
            if (statusEl) statusEl.textContent = status;
            if (status !== 'applying' && status !== 'in_progress') {
                return action;
            }
        } catch (e) {
            // ignore network blips
        }
        await new Promise(r => setTimeout(r, intervalMs));
    }
    return null;
}

function startRefreshPolling(durationMs = 60000, intervalMs = 4000) {
    const end = Date.now() + durationMs;
    const id = setInterval(async () => {
        await loadOptimizations();
        await loadForecasts();
        if (Date.now() >= end) clearInterval(id);
    }, intervalMs);
    return id;
}

window.filterInventory = function(filter) {
    activeInventoryFilter = filter;
    document.querySelectorAll('#tab-inventory .filter-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`inv-filter-${filter}`);
    if (btn) btn.classList.add('active');
    renderInventory();
}

// === ENHANCED ANALYTICS TAB FUNCTIONALITY ===

let liveMetricsChart = null;
let serviceCpuChart = null;
let forecastChart = null;
let currentServiceId = null;

// Initialize Analytics tab when switched to
window.switchTab = function(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Update nav buttons
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('active');
    });
    const activeNav = document.getElementById(`nav-${tabName}`);
    if (activeNav) {
        activeNav.classList.add('active');
    }
    
    // Load analytics data when analytics tab is opened
    if (tabName === 'analytics') {
        loadAnalyticsData();
    }
}

// Load all analytics data
async function loadAnalyticsData() {
    await Promise.all([
        loadLiveMetrics(),
        loadRLForecast(),
        loadServiceBreakdown()
    ]);
}

// Load live metrics for cloud services
async function loadLiveMetrics() {
    try {
        const response = await fetch('/api/live-metrics');
        const data = await response.json();
        
        if (data.status === 'ok') {
            renderServicesGrid(data.metrics);
            updateLastUpdated(data.last_updated);
        } else {
            console.error('Failed to load live metrics:', data.message);
        }
    } catch (error) {
        console.error('Error loading live metrics:', error);
        renderServicesGrid([]);
    }
}

// Render services grid with live metrics
function renderServicesGrid(services) {
    const grid = document.getElementById('services-grid');
    if (!grid) return;
    
    if (!services || services.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; padding: 40px;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(168,85,247,0.4)" stroke-width="1.5">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <p style="color:#cbd5e1;font-weight:600;margin-top:12px;">No live services detected</p>
                <span style="font-size:12px;color:#64748b;">Configure AWS credentials to see live metrics</span>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = services.map(service => `
        <div class="service-card" onclick="selectService('${service.service_id}', '${service.service_type}')">
            <div class="service-card-header">
                <div class="service-card-title">
                    ${getServiceIcon(service.service_type)}
                    ${service.service_type}
                </div>
                <span class="service-status ${service.status}">${service.status}</span>
            </div>
            <div class="service-metrics">
                <div class="service-metric">
                    <div class="service-metric-value">${service.cpu_usage}%</div>
                    <div class="service-metric-label">CPU Usage</div>
                </div>
                <div class="service-metric">
                    <div class="service-metric-value">${service.request_load}</div>
                    <div class="service-metric-label">Requests/s</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Get service icon based on type
function getServiceIcon(serviceType) {
    const icons = {
        'EC2': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
        'EBS': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        'RDS': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
        'Lambda': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
        'ECS': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="5" rx="1"/><rect x="2" y="17" width="20" height="5" rx="1"/></svg>',
        'EKS': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>'
    };
    return icons[serviceType] || '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>';
}

// Update last updated timestamp
function updateLastUpdated(timestamp) {
    const element = document.getElementById('last-updated');
    if (element && timestamp) {
        const date = new Date(timestamp);
        element.textContent = `Last updated: ${date.toLocaleTimeString()}`;
    }
}

// Select a service for detailed view
window.selectService = async function(serviceId, serviceType) {
    currentServiceId = serviceId;
    
    // Show service detail section, hide services grid
    document.getElementById('services-grid').parentElement.style.display = 'none';
    document.getElementById('service-detail-section').style.display = 'block';
    
    // Update service detail headers
    document.getElementById('selected-service-name').textContent = `${serviceType} Details`;
    document.getElementById('selected-service-id').textContent = `Service ID: ${serviceId}`;
    
    // Load detailed metrics
    await loadServiceMetrics(serviceId);
}

// Load detailed metrics for a specific service
async function loadServiceMetrics(serviceId) {
    try {
        const response = await fetch(`/api/service-metrics/${serviceId}`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            renderServiceCpuChart(data.metrics);
            updateServicePredictions(data.predictions);
        } else {
            console.error('Failed to load service metrics:', data.message);
        }
    } catch (error) {
        console.error('Error loading service metrics:', error);
    }
}

// Render CPU chart for selected service
function renderServiceCpuChart(metrics) {
    const ctx = document.getElementById('serviceCpuChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (serviceCpuChart) {
        serviceCpuChart.destroy();
    }
    
    serviceCpuChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: metrics.map(m => new Date(m.timestamp).toLocaleTimeString()),
            datasets: [{
                label: 'CPU Usage %',
                data: metrics.map(m => m.cpu_usage),
                borderColor: '#818cf8',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 1,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Update current CPU badge
    const currentCpu = metrics[metrics.length - 1]?.cpu_usage || 0;
    document.getElementById('current-cpu-badge').textContent = `${currentCpu}%`;
}

// Update service predictions
function updateServicePredictions(predictions) {
    document.getElementById('next-hour-cpu').textContent = `${predictions.next_hour_cpu}%`;
    document.getElementById('next-hour-requests').textContent = `${predictions.next_hour_requests} req/s`;
    document.getElementById('next-6hour-cpu').textContent = `${predictions.next_6hour_cpu}%`;
    document.getElementById('model-confidence').textContent = `${(predictions.confidence * 100).toFixed(1)}%`;
    document.getElementById('prediction-badge').textContent = `Predicted: ${predictions.next_hour_cpu}%`;
}

// Go back to services grid
window.backToServicesGrid = function() {
    document.getElementById('services-grid').parentElement.style.display = 'block';
    document.getElementById('service-detail-section').style.display = 'none';
    currentServiceId = null;
}

// Load RL forecasting data
async function loadRLForecast() {
    try {
        const response = await fetch('/api/rl-forecast');
        const data = await response.json();
        
        if (data.status === 'ok') {
            renderRLForecast(data);
        } else {
            console.error('Failed to load RL forecast:', data.message);
        }
    } catch (error) {
        console.error('Error loading RL forecast:', error);
    }
}

// Render RL forecast data
function renderRLForecast(data) {
    // Update current decision
    const decisionBadge = document.getElementById('current-decision-badge');
    if (decisionBadge) {
        decisionBadge.textContent = data.current_decision.toUpperCase();
        decisionBadge.style.background = getDecisionColor(data.current_decision);
    }
    
    // Update Q-values
    updateQValues(data.q_values);
    
    // Update current state
    updateCurrentState(data.current_state);
    
    // Update AI explanation
    updateAIExplanation(data.explanation);
    
    // Render forecast chart
    renderForecastChart(data.forecast);
    
    // Update model performance
    updateModelPerformance(data.model_performance);
}

// Get decision color based on action
function getDecisionColor(decision) {
    const colors = {
        'scale_up': 'linear-gradient(135deg, #ef4444, #f97316)',
        'maintain': 'linear-gradient(135deg, #22c55e, #06f6f6)',
        'scale_down': 'linear-gradient(135deg, #3b82f6, #8b5cf6)'
    };
    return colors[decision] || 'linear-gradient(135deg, #a855f7, #6366f1)';
}

// Update Q-values display
function updateQValues(qValues) {
    const maxValue = Math.max(...Object.values(qValues));
    
    Object.entries(qValues).forEach(([action, value]) => {
        const fillElement = document.getElementById(`q-${action.replace('_', '-')}`);
        const valueElement = document.getElementById(`q-${action.replace('_', '-')}-value`);
        
        if (fillElement && valueElement) {
            const percentage = (value / maxValue) * 100;
            fillElement.style.width = `${percentage}%`;
            valueElement.textContent = value.toFixed(3);
        }
    });
}

// Update current state display
function updateCurrentState(state) {
    document.getElementById('state-cpu').textContent = `${state.cpu_bucket}/10`;
    document.getElementById('state-memory').textContent = `${state.memory_bucket}/10`;
    document.getElementById('state-requests').textContent = `${state.request_bucket}/10`;
    document.getElementById('state-replicas').textContent = state.current_replicas;
    
    // Update cost information
    const costElement = document.getElementById('state-cost');
    const budgetElement = document.getElementById('state-budget');
    
    if (state.hourly_cost !== undefined) {
        costElement.textContent = `$${state.hourly_cost}/hr`;
        
        // Color code based on cost level
        if (state.hourly_cost > 40) {
            costElement.style.color = '#ef4444';  // Red for high cost
        } else if (state.hourly_cost > 25) {
            costElement.style.color = '#f59e0b';  // Orange for medium cost
        } else {
            costElement.style.color = '#22c55e';  // Green for low cost
        }
    }
    
    if (state.budget_status !== undefined) {
        budgetElement.textContent = state.budget_status === 'exceeded' ? 'Budget Exceeded!' : 'Within Budget';
        budgetElement.style.color = state.budget_status === 'exceeded' ? '#ef4444' : '#22c55e';
    }
}

// Update AI explanation
function updateAIExplanation(explanation) {
    const explanationElement = document.getElementById('rl-explanation');
    if (explanationElement) {
        explanationElement.innerHTML = `<div style="white-space: pre-wrap;">${explanation}</div>`;
    }
}

// Render 24-hour forecast chart
function renderForecastChart(forecastData) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: forecastData.map(f => new Date(f.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})),
            datasets: [{
                label: 'Predicted CPU %',
                data: forecastData.map(f => f.predicted_cpu),
                borderColor: '#818cf8',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }, {
                label: 'Predicted Requests/s',
                data: forecastData.map(f => f.predicted_requests * 20), // Scale for visibility
                borderColor: '#22d3ee',
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'CPU %'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Requests/s (scaled)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Update model performance metrics
function updateModelPerformance(performance) {
    document.getElementById('model-accuracy').textContent = `${(performance.accuracy * 100).toFixed(1)}%`;
    document.getElementById('total-decisions').textContent = performance.total_decisions;
    document.getElementById('success-rate').textContent = `${performance.successful_decisions}%`;
    
    const lastTraining = new Date(performance.last_training);
    document.getElementById('last-training').textContent = lastTraining.toLocaleDateString();
}

// Refresh live metrics
window.refreshLiveMetrics = async function() {
    await loadLiveMetrics();
    showToast('success', 'Refreshed', 'Live metrics updated successfully');
}

// Refresh RL forecast
window.refreshRLForecast = async function() {
    await loadRLForecast();
    showToast('success', 'Refreshed', 'RL forecast updated successfully');
}

// Execute RL decision
window.executeRLDecision = async function() {
    try {
        const btn = document.getElementById('execute-rl-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width: 14px; height: 14px; margin: 0;"></div> Executing...';
        }
        
        // Get current decision and service info
        const currentDecision = document.getElementById('current-decision-badge').textContent.toLowerCase();
        
        // Get a service ID from the metrics (use first available service)
        const response = await fetch('/api/live-metrics');
        const data = await response.json();
        
        if (data.status === 'ok' && data.metrics.length > 0) {
            const service = data.metrics[0];
            
            // Execute the RL decision
            const executeResponse = await fetch('/api/rl-execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    decision: currentDecision,
                    service_id: service.service_id,
                    service_type: service.service_type
                })
            });
            
            const executeData = await executeResponse.json();
            
            if (executeData.status === 'ok' || executeData.status === 'success') {
                let message = executeData.message;
                
                // Add cost information to the message
                if (executeData.result) {
                    const result = executeData.result;
                    if (result.cost_increase) {
                        message += ` Cost increase: $${result.cost_increase}/hr`;
                    } else if (result.cost_savings) {
                        message += ` Cost savings: $${result.cost_savings}/hr`;
                    }
                    
                    if (result.optimized_type) {
                        message += ` Optimized instance: ${result.optimized_type}`;
                    }
                }
                
                showToast('success', 'RL Decision Executed', message);
                
                // Refresh metrics to show the change
                setTimeout(() => {
                    loadLiveMetrics();
                    loadRLForecast();
                }, 2000);
            } else if (executeData.status === 'blocked') {
                // Cost protection blocked the decision
                showToast('warning', 'Decision Blocked', executeData.reason || 'Scaling blocked for cost protection');
            } else if (executeData.status === 'skipped') {
                showToast('info', 'Decision Skipped', executeData.reason || 'Scaling action skipped');
            } else {
                showToast('error', 'Execution Failed', executeData.message || 'Unknown error occurred');
            }
        } else {
            showToast('warning', 'No Services', 'No running services available for execution');
        }
        
    } catch (error) {
        console.error('Error executing RL decision:', error);
        showToast('error', 'Execution Error', 'Failed to execute RL decision');
    } finally {
        const btn = document.getElementById('execute-rl-btn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Execute';
        }
    }
}

// Load service breakdown (existing functionality)
async function loadServiceBreakdown() {
    try {
        const response = await fetch('/api/summary');
        const data = await response.json();
        
        if (data.breakdown) {
            renderServiceBreakdownChart(data.breakdown);
        }
    } catch (error) {
        console.error('Error loading service breakdown:', error);
    }
}

// Render service breakdown chart
function renderServiceBreakdownChart(breakdown) {
    const ctx = document.getElementById('serviceBarChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (serviceBarChart) {
        serviceBarChart.destroy();
    }
    
    const labels = Object.keys(breakdown);
    const values = Object.values(breakdown);
    
    serviceBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Waste ($)',
                data: values,
                backgroundColor: [
                    'rgba(99, 102, 241, 0.7)',
                    'rgba(6, 182, 212, 0.7)',
                    'rgba(168, 85, 247, 0.7)',
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(236, 72, 153, 0.7)'
                ],
                borderColor: [
                    '#6366f1',
                    '#06b6d4',
                    '#a855f7',
                    '#f59e0b',
                    '#ec4899'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

window.searchInventory = function(val) {
    inventorySearchQuery = val;
    renderInventory();
}
