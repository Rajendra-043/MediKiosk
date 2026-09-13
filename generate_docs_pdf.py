"""Generate MediKiosk complete documentation PDF (reportlab)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "MediKiosk_Complete_Documentation.pdf")

ACCENT = HexColor("#0c8aa6")
DARK = HexColor("#163f50")
GRAY = HexColor("#52727e")

styles = getSampleStyleSheet()
sTitle = ParagraphStyle("Title2", parent=styles["Title"], fontSize=26,
                        textColor=DARK, alignment=TA_CENTER, spaceAfter=6)
sSub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=12,
                      textColor=GRAY, alignment=TA_CENTER, spaceAfter=2)
sH1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16,
                     textColor=ACCENT, spaceBefore=18, spaceAfter=8)
sH2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                     textColor=DARK, spaceBefore=12, spaceAfter=6)
sH3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11,
                     textColor=DARK, spaceBefore=8, spaceAfter=4)
sBody = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5,
                       leading=13.5, alignment=TA_LEFT, spaceAfter=5)
sBullet = ParagraphStyle("Bullet", parent=sBody, leftIndent=16,
                         bulletIndent=6, spaceAfter=3)
sCell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.5, leading=11)
sCellH = ParagraphStyle("CellH", parent=sCell, textColor=HexColor("#ffffff"))
sCode = ParagraphStyle("Code", parent=styles["Code"], fontSize=8,
                       leading=11, leftIndent=10)

story = []

def h1(t): story.append(Paragraph(t, sH1))
def h2(t): story.append(Paragraph(t, sH2))
def h3(t): story.append(Paragraph(t, sH3))
def p(t): story.append(Paragraph(t, sBody))
def b(t): story.append(Paragraph(t, sBullet, bulletText="\u2022"))
def code(t):
    for line in t.strip("\n").split("\n"):
        story.append(Paragraph(line.replace(" ", "&nbsp;"), sCode))
def tbl(rows, widths=None):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cfe0e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f1f6f8")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

def C(t): return Paragraph(t, sCell)
def CH(t): return Paragraph(t, sCellH)

# ---------------- COVER ----------------
story.append(Spacer(1, 90))
story.append(Paragraph("MediKiosk", sTitle))
story.append(Paragraph("Complete Project Documentation", sSub))
story.append(Spacer(1, 6))
story.append(Paragraph("Pipelines + Materials + Why / How / Justification / Alternatives + Project Docs", sSub))
story.append(Spacer(1, 12))
story.append(HRFlowable(width="60%", color=ACCENT, thickness=1.5, spaceAfter=12, hAlign="CENTER"))
story.append(Paragraph("AI Health Assistant with Voice, OCR Document Intelligence and Live Clinic Bar", sSub))
story.append(Spacer(1, 24))
story.append(Paragraph("Stack: Django 6.1.1 + SQLite + Ollama (llama3.2:1b) + Gemini 1.5-flash + Tesseract OCR + Web Speech API + Tailwind CSS", sBody))
story.append(Paragraph("Generated from the live codebase. Backend: backend/. Frontend: frontend/templates + frontend/static.", sBody))
story.append(PageBreak())

# ---------------- CONTENTS ----------------
h1("Contents")
for i, t in enumerate([
    "1. Project overview (what, users, goals, safety boundaries)",
    "2. System architecture (apps, request map, data stores)",
    "3. End-to-end pipelines (chat, voice, OCR, live bar, documents)",
    "4. Materials inventory (every technology with version and role)",
    "5. Component deep-dives: why this, how used, justification, alternatives, could it be better",
    "6. AI conversation design (state machine, intro-once, no-repeat, Hindi, suggestions)",
    "7. Project documentation (features, API endpoints, data models, file map)",
    "8. Setup, run and verification log",
    "9. Known limits and roadmap",
], 1):
    p(f"{t}")
story.append(PageBreak())

# ---------------- 1 OVERVIEW ----------------
h1("1. Project overview")
p("MediKiosk is a clinic kiosk web application with two portals (Patient, Doctor), an AI health assistant chatbot with voice (speech in/out), OCR-based medical document understanding, and an always-visible Live clinic bar. It is an informational assistant, not a diagnostic or prescription system.")
h2("1.1 Users")
b("Patients: register/login, dashboard, medical history, medications, documents upload + OCR report, AI chatbot (text + live speech), history timeline, profile.")
b("Doctors: register/login, dashboard with patient list, patient detail (history, medications, documents), profile.")
b("Clinic operators: run the kiosk, use the Live bar queue indicator and Go-Live state.")
h2("1.2 Goals")
b("Understand typed or spoken concerns in English and Hindi (Devanagari + Roman Hinglish).")
b("Hold a polite, non-repeating conversation: introduce once, ask one gentle question at a time, never repeat intro/questions/paragraphs in a session.")
b("Give general self-care suggestions and general over-the-counter (OTC) educational info only when asked, always with a disclaimer, never dosage or prescription.")
b("Extract text and structure from uploaded medical documents (OCR) and show an aligned readable report.")
b("Keep a permanent per-session conversation record while sending only a sliding window to the LLM.")
h2("1.3 Safety boundaries (non-goals)")
b("No diagnosis, no prescription, no dosage. Chest pain / severe / red-flag symptoms always get prompt-care advice.")
b("All medicine content is general educational information with a pharmacist/doctor disclaimer.")

# ---------------- 2 ARCH ----------------
h1("2. System architecture")
h2("2.1 Django apps (backend/config/settings.py INSTALLED_APPS)")
tbl([
    [CH("App"), CH("Role")],
    [C("config"), C("Project settings, root URLconf, shared patient/doctor page views.")],
    [C("ai"), C("Chat API + conversation engine (backend/ai/services.py). Endpoints under /api/ai/.")],
    [C("voice"), C("Non-blocking voice chat API (/api/voice/chat/). Server-mic CLI loop kept only for local testing.")],
    [C("ocr"), C("Document OCR pipeline (/ocr/). Tesseract + OpenCV + medical parsing + report.")],
    [C("patients / doctor / records / history"), C("Domain data: patients, doctors, medical records, timelines.")],
    [C("abdm"), C("Reserved integration area (health ID ecosystem).")],
    [C("live"), C("Shared Go-Live state API (/api/live/) backing the bottom live bar.")],
])
h2("2.2 Request map (backend/config/urls.py)")
code("""
Browser (templates + static JS)
  |-- /patient/... , /doctor/...      -> config/views.py (server-rendered pages)
  |-- /api/ai/chat/  (POST question)  -> ai/views.py ai_chat -> ai/services.ask_ai
  |-- /api/voice/chat/ (POST text)    -> voice/views.py voice_chat -> ai/services.ask_ai
  |-- /ocr/process/ (POST document)   -> ocr/views.py -> ocr_engine + data_extractor
  |-- /api/live/status|toggle/        -> live/views.py (file-persisted live state)
  |-- /api/patients/                  -> patients API (queue count for live bar)
  `-- /static/...                     -> frontend/static (CSS/JS)
Ollama :8000? no - Ollama on 11434 (llama3.2:1b); Gemini cloud fallback.
""")
h2("2.3 Data stores")
b("SQLite db.sqlite3 (Django ORM: patients, doctors, records, documents). Simple, file-based, zero-ops for a kiosk.")
b("Per-session chat state: in-memory dict keyed by Django session_key (backend/ai/services.py _session_states).")
b("Permanent chat record: backend/media/chat_logs/&lt;session&gt;.jsonl (append-only, never truncated).")
b("Live state: backend/media/live_state.json (shared doctor <-> patient).")
b("Uploaded documents: backend/media/.")

# ---------------- 3 PIPELINES ----------------
h1("3. End-to-end pipelines")
h2("3.1 AI chat pipeline (POST /api/ai/chat/)")
code("""
1. ai/views.ai_chat: parse question (form or JSON), resolve session_id
   (fixed bug: session.create() returns None, so key is captured after).
2. services.ask_ai(text, session_id) -> _ask_ai_internal:
   detect language (Devanagari/Hinglish/English) -> remember pain context
   -> exit-offer? -> medication-offer? -> direct medicine-request?
   -> long-chat check -> one-time short offer -> Ollama (fallback Gemini)
   -> intro-once, repetition guard, mark question asked, append history.
3. Response JSON: {question, answer, suggestions[3], otc_info, disclaimer}.
""")
h2("3.2 Voice pipeline (browser-first, responsive like v1)")
code("""
Mic -> Web Speech API recognition (hi-IN/en-IN, Auto follows last message,
manual Auto/EN/HI toggle) -> POST text to /api/voice/chat/ (non-blocking)
-> AI answer JSON -> speechSynthesis TTS (hi-IN/en-IN auto from answer)
-> onend resumes listening. Server mic/Whisper/pyttsx3 loop kept ONLY
for local CLI testing (backend/test_voice.py), never in the web path.
""")
h2("3.3 OCR pipeline (POST /ocr/process/)")
code("""
Upload -> save MedicalDocument -> ocr_engine.extract_document_data:
  preprocess variants (grayscale/contrast/binary/adaptive, 2x upscale)
  -> Tesseract image_to_string (best by valid-word score, not length)
  -> image_to_data word boxes (mapped back /UPSCALE_FACTOR)
  -> median-height row building -> per-row gap thresholds
  -> aligned-text reconstruction (4 spaces at column breaks)
  -> layout rows/groups/hierarchy + image size
-> data_extractor.extract_medical_data (fields, labs, segments)
-> store extracted_text/layout/segments/report -> JSON response.
document_detail re-parses extracted_text so the report page never shows blank.
""")
h2("3.4 Live bar pipeline")
code("""
base.html fixed bottom bar on every page -> main.js polls
GET /api/live/status/ (3s) + GET /api/patients/ (queue, 20s)
-> Go-Live circle POST /api/live/toggle/ {live, by} persists to
media/live_state.json -> all tabs/doctors/patients sync green/red.
""")
h2("3.5 Documents pipeline")
p("documents.html upload modal posts to ocr_process; document_detail.html renders patient info grid, CBC lab table, medical info, segments, raw OCR text and status. Upload toast lifted above the live bar.")

# ---------------- 4 INVENTORY ----------------
h1("4. Materials inventory")
tbl([
    [CH("Material"), CH("Version / source"), CH("Role in project")],
    [C("Django"), C("6.1.1 (pip)"), C("Web framework: routing, templates, ORM, sessions, static.")],
    [C("SQLite"), C("bundled, db.sqlite3"), C("App database (patients, doctors, records, documents).")],
    [C("Ollama + llama3.2:1b"), C("ollama pkg 0.6.2; model 1.2B Q8_0"), C("Primary LLM, local, fast conversational answers.")],
    [C("Google Gemini"), C("google-genai 2.22.0, gemini-1.5-flash"), C("Fallback LLM when Ollama unavailable.")],
    [C("Web Speech API"), C("browser native"), C("Live STT (recognition) + TTS (synthesis), hi-IN/en-IN.")],
    [C("faster-whisper 1.2.1"), C("pip (CLI only)"), C("Local mic transcription for backend/test_voice.py.")],
    [C("SpeechRecognition 3.17.0 + pyttsx3 2.99"), C("pip (CLI only)"), C("Local mic capture + offline TTS for CLI testing.")],
    [C("Tesseract OCR (pytesseract 0.3.13)"), C("system binary + pip shim"), C("Document text + word boxes.")],
    [C("OpenCV (cv2) + numpy"), C("pip"), C("Preprocessing: upscale, denoise, contrast, thresholds.")],
    [C("Pillow 12.3.0"), C("pip"), C("Image open/convert for OCR.")],
    [C("PyMuPDF 1.28.2"), C("pip"), C("PDF document support in OCR path.")],
    [C("Tailwind CSS (CDN)"), C("cdn.tailwindcss.com"), C("Utility styling in templates.")],
    [C("Vanilla JS"), C("no framework"), C("ai-chatbot.js, documents.js, main.js: chat, live speech, live bar.")],
    [C("python-dotenv"), C("pip (settings import)"), C("Loads .env (GEMINI_API_KEY etc.).")],
    [C("requests 2.34.2"), C("pip"), C("Test scripts + any server-side HTTP.")],
    [C("ngrok (+ ALLOWED_HOSTS/CSRF entries)"), C("tunnel"), C("Expose kiosk for remote/phone testing.")],
    [C("reportlab 5.0.1"), C("pip (docs only)"), C("Generated this PDF; not part of app runtime.")],
], widths=[110, 110, 240])

# ---------------- 5 DEEP DIVES ----------------
h1("5. Component deep-dives: why / how / justification / alternatives / better?")
items = [
    ("5.1 Django 6.1 (web framework)",
     "WHY: batteries-included routing, templates, ORM, sessions, admin and static handling in one dependency; team knows Python; fastest path for a server-rendered kiosk.",
     "HOW: config/urls.py maps pages + /api/*; config/views.py renders patient/doctor pages; ai/voice/ocr/live expose JSON APIs; Django sessions give per-user conversation isolation.",
     "JUSTIFIED: yes - avoids gluing Flask+SQLAlchemy+login libs; admin free; SQLite default matches kiosk scale.",
     "ALTERNATIVES: Flask/FastAPI (lighter, but need extra auth/ORM/template wiring), Node/Express (JS everywhere, but team Python + AI libs are Python).",
     "BETTER?: For multi-kiosk production: keep Django, add Gunicorn + PostgreSQL + Redis sessions; add DRF + OpenAPI for the JSON APIs."),
    ("5.2 SQLite (db.sqlite3)",
     "WHY: zero-config file DB, perfect for single-kiosk dev and demos; Django default.",
     "HOW: DATABASES ENGINE django.db.backends.sqlite3; patients/doctors/records/documents models; medikiosk.db legacy file also present.",
     "JUSTIFIED: yes for now - single writer, tiny data, no ops burden.",
     "ALTERNATIVES: PostgreSQL (concurrency, backups), MySQL (similar).",
     "BETTER?: Migrate to PostgreSQL when >1 kiosk or concurrent writers; keep SQLite for offline kiosk image."),
    ("5.3 Django sessions for chat state",
     "WHY: fixes the critical bug where session.create() returns None and everyone shared one global conversation (intro missing, chest-pain hallucinated on 'Hello').",
     "HOW: views capture session_key after create(); services keep _session_states[session_id] = SessionState (history window, asked set, flags); compat shims reset_conversation/reset_chat/reset_patient kept.",
     "JUSTIFIED: yes - minimal, no new infra, matches browser cookie flow.",
     "ALTERNATIVES: JWT stateless (no server memory, but must ship history each call), Redis (best for scale).",
     "BETTER?: Move SessionState to Redis with TTL + persist full_log already in JSONL; add explicit New-Chat endpoint instead of greeting heuristics."),
    ("5.4 Ollama llama3.2:1b (primary LLM)",
     "WHY: local inference = free, offline-capable, low latency (~0.2-1s observed), private patient text stays on machine; 1.2B Q8_0 fits modest hardware with 128k context.",
     "HOW: ai/services.ask_ollama builds SYSTEM_PROMPT + per-state instruction + sliding history + lang directive; temperature 0.45, num_predict 80, keep_alive 10m; Gemini fallback on exception.",
     "JUSTIFIED: yes for kiosk triage chatter - fast and private; quality limits handled by deterministic guardrails (intro, no-repeat, suggestions).",
     "ALTERNATIVES: bigger local models (llama3.1:8b, mistral) - smarter but slower/heavier; cloud-only (GPT/Gemini primary) - smarter but cost/latency/privacy hit.",
     "BETTER?: Keep 1b for speed, add router: red-flag/complex -> bigger model or Gemini; add response caching for repeated FAQs."),
    ("5.5 Gemini 1.5-flash (fallback)",
     "WHY: keeps chat alive when Ollama is down; flash tier is fast/cheap; same prompt contract.",
     "HOW: ask_gemini mirrors ask_ollama (history text, instruction, lang directive, polite post-process, intro). Model constant fixed from invalid gemini-3.6-flash.",
     "JUSTIFIED: yes as fallback only - primary stays local/private.",
     "ALTERNATIVES: OpenAI GPT-4o-mini, Anthropic Haiku (similar role, different vendor).",
     "BETTER?: Health-check Ollama at startup and show AI status in UI; retry with backoff."),
    ("5.6 Web Speech API (live voice in/out)",
     "WHY: the only responsive in-browser voice path: no audio upload, no server GPU, low latency; original server-mic design (mic on server hears nothing from the user's browser) cannot work on web.",
     "HOW: ai-chatbot.js recognition (continuous+interim, hi-IN/en-IN, Auto follows last message + manual Auto/EN/HI toggle) POSTs final text to /api/voice/chat/; answer spoken via speechSynthesis with matching voice/lang; onend resumes listening.",
     "JUSTIFIED: yes - restores the 'responsive voice like v1' requirement with zero server cost.",
     "ALTERNATIVES: server Whisper on uploaded audio (accurate, but 1-5s latency + GPU/CPU load), cloud STT/TTS (Google/Azure - better Hindi voices, but cost + network + privacy).",
     "BETTER?: Optional server-Whisper fallback for noisy audio; cloud neural TTS toggle for nicer Hindi voice; VAD tuning already via 500ms pause timer."),
    ("5.7 faster-whisper + SpeechRecognition + pyttsx3 (kept, CLI-only)",
     "WHY: useful for local Fitzgerald-style testing without a browser; pyttsx3 gives offline TTS on the dev machine.",
     "HOW: voice/services.py listen_and_ask loop + backend/test_voice.py, test_tts.py; never imported by Django views (avoids loading Whisper weights into the web worker).",
     "JUSTIFIED: yes as dev/CLI harness - must stay out of the request path.",
     "ALTERNATIVES: delete it (cleaner) or gate behind an env flag.",
     "BETTER?: Keep but document clearly; add VOICE_CLI=1 guard so `import voice.services` never pulls models in web context."),
    ("5.8 Tesseract OCR + OpenCV + numpy + Pillow (+ PyMuPDF)",
     "WHY: free, offline document reading; OpenCV preprocessing rescues low-contrast scans; word boxes enable layout-aware reconstruction instead of flat text dumps.",
     "HOW: ocr_engine tries grayscale/contrast/binary/adaptive variants at 2x, picks best by valid-word score, scales boxes back (/UPSCALE_FACTOR), median-height rows, per-row gap thresholds, 4-space column breaks; data_extractor parses fields/labs/segments; document_detail re-parses so report never blanks.",
     "JUSTIFIED: yes - commercial OCR APIs cost per page and leak patient documents.",
     "ALTERNATIVES: EasyOCR/PaddleOCR (better handwriting, heavier), Google Vision/AWS Textract (best accuracy, cost + privacy).",
     "BETTER?: Deskew + orientation fix; confidence-weighted voting; cache OCR JSON per file hash; async worker (Celery) so big PDFs never block the request."),
    ("5.9 Tailwind CDN + vanilla JS (frontend)",
     "WHY: fast utility styling without a build step; vanilla JS keeps kiosk pages light and debuggable.",
     "HOW: base.html loads Tailwind + css/style.css; ai-chatbot.js owns chat/live-speech/TTS; documents.js owns upload modal + OCR result cards; main.js owns live bar polling/toggle.",
     "JUSTIFIED: yes for current scale - no SPA complexity needed.",
     "ALTERNATIVES: React/Vue SPA (better state mgmt, but rewrite + build chain), Bootstrap (heavier, less flexible).",
     "BETTER?: Bundle Tailwind locally for offline kiosk; split ai-chatbot.js into modules; add service worker for flaky clinic networks."),
    ("5.10 ngrok + hosts/CSRF entries",
     "WHY: instant public URL for phone/mic testing and demos without deploying.",
     "HOW: ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS include ngrok domains; run `ngrok http 8000`.",
     "JUSTIFIED: yes for dev/demo only.",
     "ALTERNATIVES: Cloudflare Tunnel, Tailscale (more stable/secure).",
     "BETTER?: Move to proper staging with HTTPS + secrets in env, DEBUG off, SECRET_KEY rotated (current key is committed in settings)."),
]
for title, *bullets in items:
    h2(title)
    labels = ["WHY this:", "HOW used here:", "JUSTIFIED:", "ALTERNATIVES:", "COULD IT BE BETTER:"]
    for lab, txt in zip(labels, bullets):
        p(f"<b>{lab}</b> {txt}")

# ---------------- 6 AI DESIGN ----------------
h1("6. AI conversation design")
h2("6.1 State machine (per session)")
code("""
fresh session -> intro ONCE (EN or Hindi per input language)
 -> assessment questions (max 6), one gentle question/turn
 -> ONE-TIME short offer: "I've taken your info. Now feel free to ask me anything."
    (Hindi: short Hindi equivalent)
 -> yes -> suggestions + OTC info | no/ambiguous -> casual chat, NEVER re-offer
 -> medicine keywords anytime -> suggestions + OTC info immediately
 -> 20 turns -> polite exit offer once -> yes ends / no continues
""")
h2("6.2 Intro-once")
p("Flag has_introduced set after the first assistant message; forced-intro runs only when history is empty. Fixed bug: previously the medication-offer paragraph re-fired every turn (screenshot case) because ambiguous replies cleared pending and the offer branch re-triggered; now medication_offered guarantees once-only.")
h2("6.3 No-repeat system")
b("asked_questions normalized set (never cleared mid-session) injected into the prompt as a NEVER-repeat list.")
b("recent_answers similarity check (exact or >85% word overlap) triggers one rephrase retry.")
b("collected_info (duration/severity/location/symptom, incl. Hindi keywords) injected as already-known facts.")
b("Post-assessment instruction tells the model to chat casually, never repeat offers/paragraphs.")
h2("6.4 Full history record (8-question cap removed)")
p("Old code truncated history to 8-30 messages. Now each session keeps full_log (unbounded in memory) AND appends every turn to backend/media/chat_logs/&lt;session&gt;.jsonl. Only a 30-message sliding window is sent to the LLM for speed; get_full_log(session_id) returns the complete record.")
h2("6.5 Hindi: Devanagari + Hinglish, reply-only-matching")
b("Detection: Devanagari regex U+0900-U+097F OR Hinglish word-boundary markers (mujhe, dard, bukhar, dawa, kya, nahi...). Weak words (hai, kal, sir) need a second marker so 'hair fall'/'yes sir' stay English. Verified 10/10 incl. mid-session EN-HI-EN switching.")
b("Per-turn lang directive appended to Ollama+Gemini prompts; polite softening in both languages; Hindi suggestion/OTC tables; Hindi short offer; frontend TTS hi-IN/en-IN auto + mic Auto/EN/HI toggle.")
h2("6.6 Medicine suggestions (safe)")
p("Deterministic tables by pain type (headache/back/stomach/joint-muscle/tooth/throat/chest/general) + OTC educational note (paracetamol/ibuprofen commonly, label + pharmacist/doctor disclaimer, no dosage, no prescription). Chest pain always gets urgent-care advice, never OTC encouragement.")

# ---------------- 7 PROJECT DOCS ----------------
h1("7. Project documentation")
h2("7.1 Features delivered")
b("Patient: landing, register/login/logout, dashboard, medical history, medications, documents upload + OCR report + delete, chatbot (text + live speech + TTS), timeline, profile.")
b("Doctor: landing, register/login, dashboard with patient search, patient detail (history/meds/documents/age/last visit), profile.")
b("Live bar on every page (base.html): clock, online status, role, queue count, red LIVE circle -> green when live, synced via /api/live/ across tabs and roles.")
b("Chat UX: welcome card, bubbles, image attach UI, recording popup, live overlay with wave + transcript + Auto/EN/HI toggle, disclaimer footer.")
h2("7.2 API endpoints")
tbl([
    [CH("Method + path"), CH("Purpose")],
    [C("POST /api/ai/chat/"), C("Chat: {question|text} -> {answer, suggestions[3], otc_info, disclaimer}.")],
    [C("POST /api/voice/chat/"), C("Voice: {question|text} -> same AI JSON (browser does STT/TTS).")],
    [C("POST /ocr/process/"), C("Document OCR: {document} -> {text, medical_data, report, layout}.")],
    [C("GET /api/live/status/"), C("Live state {live, since, by}.")],
    [C("POST /api/live/toggle/"), C("Set live {live, by} -> persisted JSON.")],
    [C("GET /api/patients/"), C("Patient list (queue count).")],
    [C("GET|POST patient/*, doctor/*"), C("Server-rendered pages + auth + CRUD.")],
])
h2("7.3 Data models (essentials)")
b("Patient(name, dob, gender, blood_group, phone, email, address, passward[hashed], patient_id PATxxxx).")
b("MedicalHistory(patient FK, condition, diagnosis, diagnosed_date, doctor_name, notes).")
b("Medication(patient FK, name, generic_name, dosage, frequency, route, dates, instructions, doctor).")
b("MedicalDocument(patient FK, document_name, file, document_type, extracted_text, ocr_layout/segments JSON, report).")
b("Doctor(full_name, reg. number unique, specialization, qualification, experience, phone, email, password[hashed], doctor_id DOCxxxx).")
h2("7.4 File map (where things live)")
code("""
backend/config/      settings, urls, page views (views.py), wsgi/asgi
backend/ai/          services.py (engine), views.py (chat API), urls.py, prompts.py
backend/voice/       views.py (web API), services.py (CLI mic loop only), urls.py
backend/ocr/         ocr_engine.py, data_extractor.py, medical_parser.py, views.py
backend/patients|doctor|records|history|abdm|database|live
backend/media/       uploads + chat_logs/ + live_state.json
frontend/templates/  base.html, landing/, paitent/* (note folder spelling), doctor/*
frontend/static/     css/style.css, css/ai-chatbot.css, js/main.js, js/ai-chatbot.js, ...
""")
# ---------------- 8 SETUP/VERIFY ----------------
h1("8. Setup, run and verification log")
h2("8.1 Setup & run")
code("""
python -m venv venv
venv\\Scripts\\activate
pip install django ollama google-genai faster-whisper SpeechRecognition
  pyttsx3 pytesseract pillow opencv-python numpy pymupdf requests python-dotenv
# Tesseract binary required on PATH for OCR.
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000
# AI needs Ollama running: ollama serve ; ollama pull llama3.2:1b
# .env: GEMINI_API_KEY=... (fallback only)
""")
h2("8.2 Verification evidence (from live runs)")
tbl([
    [CH("Check"), CH("Result")],
    [C("manage.py check"), C("0 issues.")],
    [C("py_compile services/views"), C("OK.")],
    [C("POST /api/ai/chat/ Hello (fresh)"), C("Intro once, polite, no ordering.")],
    [C("Same-session follow-ups"), C("No intro repeat; varied questions; recorded info reused.")],
    [C("Medication offer loop (screenshot bug)"), C("Fixed: short offer fires once; follow-ups never repeat it.")],
    [C("'What medicine can I take'"), C("Suggestions + paracetamol/ibuprofen note returned.")],
    [C("Hindi Devanagari (5 msgs)"), C("All replies Hindi.")],
    [C("Hinglish / EN / EN-HI-EN switch"), C("All correct (10/10 incl. hair-fall/yes-sir negatives).")],
    [C("POST /api/voice/chat/"), C("200 + intro + 3 suggestions.")],
    [C("GET /api/live/*"), C("status/toggle sync across tabs.")],
    [C("test_ai.py"), C("Passes: intro, assessment, reset_chat fresh patient.")],
])
# ---------------- 9 LIMITS ----------------
h1("9. Known limits and roadmap")
h2("9.1 Limits")
b("In-memory session states reset on server restart (JSONL logs survive, live reload not yet implemented).")
b("llama3.2:1b can hallucinate; guardrails (no-repeat lists, short offer, disclaimer) mitigate but do not eliminate.")
b("Roman-Hindi replies come back in Devanagari script (proper Hindi) by design.")
b("Browser Hindi TTS quality depends on installed voices; mic accuracy depends on Chrome/Edge + noise.")
b("SECRET_KEY committed, DEBUG=True, SQLite, no rate limiting: dev-only posture.")
h2("9.2 Roadmap (highest value first)")
b("Redis sessions + reload full_log on restart; explicit New-Chat button calling reset.")
b("Gunicorn + PostgreSQL + env secrets + DEBUG off for any shared deployment.")
b("Model router (1b fast path, larger/cloud for red-flag or complex turns) + startup Ollama health check.")
b("OCR async worker + deskew + per-file-hash cache.")
b("Cloud neural TTS toggle for Hindi; server-Whisper fallback for noisy audio.")
b("Fix passward field typo (migration), rename paitent/ folder, OpenAPI docs for JSON APIs.")

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=1.6*cm,
                        bottomMargin=1.6*cm, leftMargin=1.8*cm, rightMargin=1.8*cm,
                        title="MediKiosk Complete Documentation",
                        author="MediKiosk project")
doc.build(story)
print("WROTE", OUT)
