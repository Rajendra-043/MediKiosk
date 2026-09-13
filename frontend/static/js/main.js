/* =================================
   MEDIKIOSK JAVASCRIPT
================================= */


/* =================================
   PASSWORD TOGGLE
================================= */

function togglePassword(inputId) {

    const input = document.getElementById(inputId);

    if (!input) return;

    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}


/* =================================
   PATIENT LOGIN - FRONTEND DEMO
================================= */

function handleLogin(event) {

    event.preventDefault();

    const patientId =
        document.getElementById("patientId").value;

    if (!patientId) {
        alert("Please enter your Patient ID.");
        return;
    }

    /*
       TEMPORARY FRONTEND REDIRECT

       Later Django authentication will
       handle this.
    */

    window.location.href = "/patient/dashboard/";
}


/* =================================
   DOCTOR LOGIN - FRONTEND DEMO
================================= */

function handleDoctorLogin(event) {

    event.preventDefault();

    /*
       Temporary redirect.
       Django authentication will replace this.
    */

    window.location.href = "/doctor/dashboard/";
}


/* =================================
   PATIENT REGISTRATION
================================= */

function handleRegistration(event) {

    event.preventDefault();

    const password =
        document.getElementById("registerPassword").value;

    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }

    alert(
        "Registration form submitted successfully.\n\n" +
        "Django database connection will be added next."
    );
}


/* =================================
   DOCTOR REGISTRATION
================================= */

function handleDoctorRegistration(event) {

    event.preventDefault();

    const password =
        document.getElementById(
            "doctorRegisterPassword"
        ).value;

    const confirmPassword =
        document.getElementById(
            "doctorConfirmPassword"
        ).value;

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }

    alert(
        "Doctor registration submitted successfully."
    );
}


/* =================================
   SIDEBAR
================================= */

function toggleSidebar() {

    const sidebar =
        document.getElementById("sidebar");

    if (!sidebar) return;

    sidebar.classList.toggle("-translate-x-full");
}


/* =================================
   COPY PATIENT ID
================================= */

function copyPatientId() {

    const patientId = "MKP-2026-00001";

    navigator.clipboard.writeText(patientId)
        .then(() => {

            alert("Patient ID copied!");

        })
        .catch(() => {

            alert("Unable to copy Patient ID.");

        });
}


/* =================================
   LOGOUT
================================= */

function logout() {

    const confirmLogout =
        confirm("Are you sure you want to logout?");

    if (confirmLogout) {

        window.location.href = "/patient/login/";

    }
}


/* =================================
    LIVE BAR – Go Live only (no text area)
   ================================= */

(function initLiveBar() {
    const timeEl = document.getElementById("live-time");
    const statusEl = document.getElementById("live-status");
    const roleEl = document.getElementById("live-role");
    const queueEl = document.getElementById("live-queue-count");
    const goBtn = document.getElementById("live-go-btn");

    function tick() {
        if (timeEl) timeEl.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    tick();
    setInterval(tick, 1000);

    function detectRole() {
        const p = location.pathname;
        if (p.startsWith("/doctor")) return "Doctor Live";
        if (p.startsWith("/patient")) return "Patient Live";
        return "Live";
    }
    if (roleEl) roleEl.textContent = "• " + detectRole();

    async function pollQueue() {
        try {
            const r = await fetch("/api/patients/", { headers: { "Accept": "application/json" } });
            if (!r.ok) throw new Error();
            const j = await r.json();
            const n = Array.isArray(j.patients) ? j.patients.length : (j.count ?? "—");
            if (queueEl) queueEl.textContent = n;
        } catch (e) {
            if (queueEl) queueEl.textContent = "—";
        }
    }
    pollQueue();
    setInterval(pollQueue, 20000);

    function updateOnline() {
        if (!statusEl) return;
        const online = navigator.onLine;
        statusEl.innerHTML = '<span class="live-status-dot" style="background:' + (online ? '#16a34a' : '#ef4444') + '"></span>' + (online ? 'System Online' : 'Offline');
        statusEl.style.color = online ? '#86efac' : '#f87171';
        if (!online) statusEl.style.color = '#f87171';
    }
    updateOnline();
    window.addEventListener("online", updateOnline);
    window.addEventListener("offline", updateOnline);

    // --- Live working: poll server state (shared doctor<->patient) ---
    let liveState = false;
    function applyLiveState(state) {
        liveState = !!state.live;
        if (!goBtn) return;
        goBtn.classList.toggle("is-live", liveState);
        // circle button always shows LIVE text – no label swap needed
        const label = goBtn.querySelector("span:nth-child(2)");
        if (label) {
            label.textContent = liveState ? "Live" : "Go Live";
        } else {
            // circle variant: keep LIVE text, toggle title only
            goBtn.textContent = "LIVE";
        }
        goBtn.title = liveState ? "Live is ON — click to end" : "Click to Go Live";
        // update status text when live
        if (liveState) {
            const by = state.by ? " • " + state.by : "";
            statusEl.innerHTML = '<span class="live-status-dot" style="background:#16a34a"></span>Live' + by;
            statusEl.style.color = "#86efac";
        } else {
            updateOnline();
        }
    }

    async function fetchLiveStatus() {
        try {
            const r = await fetch("/api/live/status/", { headers: { "Accept": "application/json" } });
            if (!r.ok) return;
            const j = await r.json();
            applyLiveState(j);
        } catch (e) {}
    }
    fetchLiveStatus();
    setInterval(fetchLiveStatus, 3000);
    // expose for handleGoLive
    window._fetchLiveStatus = fetchLiveStatus;
    window._applyLiveState = applyLiveState;
    window._getLiveState = () => liveState;
})();

function getLiveRole() {
    if (location.pathname.startsWith("/doctor")) return "doctor";
    return "patient";
}

async function handleGoLive() {
    const btn = document.getElementById("live-go-btn");
    const panel = document.getElementById("live-assist-panel");
    // Toggle panel first so button always feels active
    if (panel) {
        const willOpen = panel.hidden;
        if (willOpen) openLiveAssist();
        else closeLiveAssist(true);
    }
    if (!btn) return;
    const current = window._getLiveState ? window._getLiveState() : btn.classList.contains("is-live");
    // When opening panel we always want LIVE green/active
    const desired = panel && !panel.hidden ? true : !current;
    btn.classList.toggle("is-live", desired);
    btn.textContent = "LIVE";
    try { btn.animate([{ transform: "scale(0.97)" }, { transform: "scale(1)" }], { duration: 140 }); } catch (e) {}
    try {
        const r = await fetch("/api/live/toggle/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ live: desired, by: getLiveRole() })
        });
        const j = await r.json();
        if (window._applyLiveState) window._applyLiveState(j);
    } catch (e) {}
}

function openLiveAssist() {
    const panel = document.getElementById("live-assist-panel");
    if (!panel) return;
    panel.hidden = false;
    const roleEl = document.getElementById("live-assist-role");
    if (roleEl) roleEl.textContent = "• " + (getLiveRole() === "doctor" ? "Doctor" : "Patient");
    renderLiveQuickLinks();
    const input = document.getElementById("live-assist-input");
    if (input) setTimeout(() => input.focus(), 50);
}

function closeLiveAssist(silent) {
    const panel = document.getElementById("live-assist-panel");
    if (panel) panel.hidden = true;
    try { stopLiveAssistMic(); } catch (e) {}
    if (!silent) {
        // turning panel off also turns LIVE off
        fetch("/api/live/toggle/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ live: false, by: getLiveRole() })
        }).then(r => r.json()).then(j => {
            if (window._applyLiveState) window._applyLiveState(j);
        }).catch(() => {});
    }
}

function liveAssistAddMsg(text, who) {
    const box = document.getElementById("live-assist-messages");
    if (!box) return null;
    const div = document.createElement("div");
    div.className = "live-assist-msg " + (who || "ai");
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
}

function renderLiveQuickLinks() {
    const wrap = document.getElementById("live-assist-quick");
    if (!wrap) return;
    const role = getLiveRole();
    const links = role === "doctor"
        ? [{ label: "Dashboard", url: "/doctor/dashboard/" }, { label: "Profile", url: "/doctor/profile/" }, { label: "Chatbot", url: "/patient/chatbot/" }]
        : [{ label: "Dashboard", url: "/patient/dashboard/" }, { label: "Chatbot", url: "/patient/chatbot/" }, { label: "Documents", url: "/patient/documents/" }, { label: "Medications", url: "/patient/medications/" }, { label: "History", url: "/patient/medical-history/" }, { label: "Timeline", url: "/patient/timeline/" }];
    wrap.innerHTML = "";
    links.forEach(l => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "live-assist-chip";
        b.textContent = l.label;
        b.addEventListener("click", () => { window.location.href = l.url; });
        wrap.appendChild(b);
    });
}

let _liveAssistPending = null;

async function sendLiveAssist(text) {
    text = (text || "").trim();
    if (!text) return;
    liveAssistAddMsg(text, "user");
    const thinking = liveAssistAddMsg("Thinking...", "ai thinking");
    const row = document.getElementById("live-assist-action-row");
    if (row) row.hidden = true;
    _liveAssistPending = null;
    try {
        const r = await fetch("/api/ai/assist/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: text, role: getLiveRole() })
        });
        const j = await r.json();
        if (thinking) thinking.remove();
        liveAssistAddMsg(j.answer || "I'm here to help.", "ai");
        // Speak the answer in background like chatbot voice
        try {
            if ("speechSynthesis" in window && j.answer) {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(String(j.answer).slice(0, 280));
                u.rate = 0.95;
                window.speechSynthesis.speak(u);
            }
        } catch (e) {}
        if (j.action || j.chatbot_url) {
            _liveAssistPending = { action: j.action, question: j.question || text, chatbot_url: j.chatbot_url };
            if (row) row.hidden = false;
            const gotoBtn = document.getElementById("live-assist-goto");
            const chatBtn = document.getElementById("live-assist-chatbot");
            if (gotoBtn) {
                if (j.action) {
                    gotoBtn.hidden = false;
                    gotoBtn.textContent = j.action.label || "Take me there";
                } else {
                    gotoBtn.hidden = true;
                }
            }
            if (chatBtn) chatBtn.textContent = "Continue in Chatbot";
        }
        if (j.quick_links) {
            const wrap = document.getElementById("live-assist-quick");
            if (wrap && Array.isArray(j.quick_links)) {
                wrap.innerHTML = "";
                j.quick_links.forEach(l => {
                    const b = document.createElement("button");
                    b.type = "button";
                    b.className = "live-assist-chip";
                    b.textContent = l.label;
                    b.addEventListener("click", () => { window.location.href = l.url; });
                    wrap.appendChild(b);
                });
            }
        }
    } catch (e) {
        if (thinking) thinking.remove();
        liveAssistAddMsg("Connection issue. Try again or open the chatbot.", "ai");
        _liveAssistPending = { action: null, question: text, chatbot_url: "/patient/chatbot/" };
        if (row) row.hidden = false;
    }
}

let _liveAssistRecog = null;
function stopLiveAssistMic() {
    try {
        if (_liveAssistRecog) _liveAssistRecog.stop();
    } catch (e) {}
    const mic = document.getElementById("live-assist-mic");
    if (mic) mic.classList.remove("listening");
    _liveAssistRecog = null;
}

(function initLiveAssist() {
    document.addEventListener("DOMContentLoaded", function () {
        const panel = document.getElementById("live-assist-panel");
        if (!panel) return;
        const closeBtn = document.getElementById("live-assist-close");
        if (closeBtn) closeBtn.addEventListener("click", () => closeLiveAssist(false));
        const form = document.getElementById("live-assist-form");
        const input = document.getElementById("live-assist-input");
        if (form) form.addEventListener("submit", (e) => {
            e.preventDefault();
            const v = input ? input.value : "";
            if (input) input.value = "";
            sendLiveAssist(v);
        });
        const gotoBtn = document.getElementById("live-assist-goto");
        if (gotoBtn) gotoBtn.addEventListener("click", () => {
            if (_liveAssistPending && _liveAssistPending.action && _liveAssistPending.action.url) {
                window.location.href = _liveAssistPending.action.url;
            }
        });
        const chatBtn = document.getElementById("live-assist-chatbot");
        if (chatBtn) chatBtn.addEventListener("click", () => {
            const q = _liveAssistPending ? _liveAssistPending.question : (input ? input.value : "");
            try {
                if (q) localStorage.setItem("medikiosk_live_handoff", q);
            } catch (e) {}
            const base = (_liveAssistPending && _liveAssistPending.chatbot_url) || "/patient/chatbot/";
            window.location.href = q ? base + "?q=" + encodeURIComponent(q) : base;
        });
        const mic = document.getElementById("live-assist-mic");
        if (mic) mic.addEventListener("click", () => {
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SR) {
                liveAssistAddMsg("Voice not supported here. Please type instead.", "ai");
                return;
            }
            if (_liveAssistRecog) { stopLiveAssistMic(); return; }
            try {
                const rec = new SR();
                _liveAssistRecog = rec;
                rec.lang = "en-IN";
                rec.interimResults = false;
                rec.continuous = false;
                mic.classList.add("listening");
                liveAssistAddMsg("Listening... speak your problem.", "ai");
                rec.onresult = (ev) => {
                    const txt = ev.results && ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript : "";
                    if (txt) sendLiveAssist(txt);
                };
                rec.onend = () => stopLiveAssistMic();
                rec.onerror = () => {
                    stopLiveAssistMic();
                    liveAssistAddMsg("Mic issue. Please type your problem.", "ai");
                };
                rec.start();
            } catch (e) {
                stopLiveAssistMic();
            }
        });
        // ESC closes panel
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && panel && !panel.hidden) closeLiveAssist(false);
        });
    });
})();

/* =================================
    ABOUT
   ================================= */

function showInfo() {

    alert(
        "MediKiosk\n\n" +
        "A digital healthcare platform for " +
        "organizing patient medical information " +
        "and assisting doctors with clinical records."
    );
}