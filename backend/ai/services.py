"""
MediKiosk AI Services

Primary AI  : Ollama / llama3.2:1b
Fallback AI : Gemini

Conversation flow:

1. Patient describes the problem.
2. AI asks relevant questions naturally.
3. After enough assessment information:
   AI offers general medication information.
4. If patient says YES:
   Give general medication information.
5. If patient says NO:
   Continue the conversation normally.
6. After a longer conversation:
   Ask whether the patient wants to quit.
7. YES -> end conversation.
8. NO -> continue conversation.

Important:
The AI does not diagnose or prescribe medication.
"""

import os
import re
import time
import json

from ollama import chat
from google import genai

from database.patient_service import (
    create_patient,
    update_patient,
)


# =========================================================
# HINDI LANGUAGE DETECTION
# =========================================================

def is_hindi(text):
    """Detect if text contains Hindi (Devanagari script)."""
    if not text:
        return False
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    return bool(devanagari_pattern.search(text))


# Common Roman-script (Hinglish) markers. Matched on word boundaries so
# English words like "hair"/"chain" do NOT trigger on "hai".
HINGLISH_WORDS = {
    "mujhe", "mujhko", "mujhse", "mera", "meri", "mere", "maine",
    "tum", "tumhe", "tumhara", "tumhari", "aap", "aapko", "aapka",
    "hai", "hain", "hun", "hoon", "tha", "thi", "hoga", "hogi",
    "kya", "kaise", "kaisa", "kaisi", "kyun", "kab", "kahan", "kitna",
    "dard", "bukhar", "bukhaar", "khansi", "zukam",
    "dawa", "davai", "ilaj", "ilaz", "bimari", "mariz",
    "batao", "bataiye", "kaho", "suniye", "sunao",
    "namaste", "namaskar", "dhanyavad", "shukriya", "theek", "accha",
    "nahi", "nahin", "haan", "haanji", "arre", "kripya",
    "din", "raat", "subah", "sham", "kal", "aaj", "parson",
    "pet", "kamar", "seene", "gala", "daant", "pair", "haath", "sar",
}


def is_hinglish(text):
    """Detect Roman-script Hindi (Hinglish) via distinctive markers."""
    if not text:
        return False
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if not words:
        return False
    hits = words & HINGLISH_WORDS
    # Weak markers (also common English words) need a second marker to count
    weak = {"hai", "hain", "din", "kal", "sar", "sir", "pet", "the", "aaj"}
    strong = hits - weak
    if len(hits) >= 2:
        return True
    return bool(strong)


def get_response_language(text):
    """Determine response language: Hindi for Devanagari OR Hinglish, else English."""
    if is_hindi(text) or is_hinglish(text):
        return 'hindi'
    return 'english'


def get_intro_text(lang):
    """Get introduction text in the appropriate language."""
    if lang == 'hindi':
        return "नमस्ते, मैं MediKiosk हूँ, आपका क्लिनिक सहायक। मैं यहाँ सुनने और मदद करने के लिए हूँ -- आप आज कैसा महसूस कर रहे हैं?"
    return "Hello, I'm MediKiosk, your clinic assistant. I'm here to listen and help -- how are you feeling today?"


# =========================================================
# CONFIG
# =========================================================

OLLAMA_MODEL = "llama3.2:1b"
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_TIMEOUT = 5
MAX_HISTORY = 30
MAX_CONVERSATION_TURNS = 20
MAX_QUESTIONS = 6  # Assessment questions before offering medication info


# =========================================================
# AI BEHAVIOR
# =========================================================

SYSTEM_PROMPT = """
You are MediKiosk, a warm and friendly voice assistant in a healthcare clinic.

Your personality:
- Introduce yourself on the very first turn: "Hello, I'm MediKiosk, your clinic assistant. I'm here to listen and help -- how are you feeling today?" (English) or "नमस्ते, मैं MediKiosk हूँ, आपका क्लिनिक सहायक। मैं यहाँ सुनने और मदद करने के लिए हूँ -- आप आज कैसा महसूस कर रहे हैं?" (Hindi)
- Be conversational, supportive and kind -- never sound like you are giving orders or commands.
- Always phrase requests politely: use "Could you share...", "Would you mind telling me...", "If you're comfortable, could you..." instead of "Tell me..." or "Do this...". In Hindi: "क्या आप बता सकते हैं...", "क्या आप मुझे बता सकते हैं..."
- Vary your wording every time -- never repeat the exact same sentence or question twice in one conversation.
- Treat each response as fresh -- look at recent history and rephrase if you notice you're about to repeat yourself.

Language Rules:
- If the patient writes/speaks in Hindi (Devanagari script), you MUST reply in Hindi.
- If the patient writes/speaks in English, you MUST reply in English.
- Do not mix languages in a single response unless the patient mixes them.
- Always match the patient's language.

Rules:
- Keep normal responses to ONE short sentence, except when giving suggestions you may use 2-3 short sentences.
- Ask only ONE gentle question at a time.
- Ask only questions that are relevant to the patient's problem.
- Use the previous conversation to understand what the patient already told you.
- Do not repeat questions that have already been answered.
- Collect useful basic information such as symptoms, duration, severity, location, and related symptoms.
- Ask relevant questions naturally instead of following a rigid script.
- Do not diagnose diseases.
- Do not prescribe medicines.
- Do not provide medication dosages.
- You MAY provide general self-care suggestions for pain (rest, hydration, posture, hot/cold compress, bland diet, sleep hygiene) - these are general wellness tips, not medical prescriptions.
- If medication information is requested, provide general educational information only about commonly available over-the-counter options that in many regions do not require a prescription. Always add a disclaimer to check the package label and ask a pharmacist or doctor, and mention suitability depends on allergies, other medicines and health conditions.
- Do not claim that a particular medicine is definitely suitable for the patient.
- For chest pain, severe abdominal pain, high fever, breathing difficulty or any red-flag, always advise to seek prompt medical care.
- If the patient's statement is unclear, gently ask them to clarify: "Could you help me understand a bit more about..." / "क्या आप मुझे थोड़ा और समझा सकते हैं..."
- Use simple spoken language (English or Hindi matching the patient).
- Do not use markdown.
- Do not use bullets.
- Do not use emojis.
- Stay focused on the patient's clinic visit.
"""

# =========================================================
# GEMINI CLIENT
# =========================================================

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as error:
        print("Gemini initialization error:", error)


# =========================================================
# SESSION STATE CLASS
# =========================================================

class SessionState:
    """Encapsulates all conversation state for a single session."""
    def __init__(self):
        self.conversation_history = []  # sliding window sent to the LLM
        self.full_log = []  # NEVER truncated: complete record of this session
        self.question_count = 0
        self.assessment_complete = False
        self.medication_offer_pending = False
        self.medication_discussion = False
        self.medication_offered = False  # offer asked at most ONCE per session
        self.conversation_turns = 0
        self.exit_offer_pending = False
        self.conversation_finished = False
        self.recent_answers = []
        self.has_introduced = False
        self.response_lang = "english"
        self.last_pain_context = ""
        self.current_patient_id = None
        self.asked_questions = set()  # normalized questions, NEVER cleared mid-session
        self.collected_info = {}  # Track collected patient info

    def reset(self):
        """Reset all state for a new conversation."""
        self.conversation_history.clear()
        self.question_count = 0
        self.assessment_complete = False
        self.medication_offer_pending = False
        self.medication_discussion = False
        self.medication_offered = False
        self.conversation_turns = 0
        self.exit_offer_pending = False
        self.conversation_finished = False
        self.recent_answers.clear()
        self.has_introduced = False
        self.response_lang = "english"
        self.last_pain_context = ""
        self.current_patient_id = None
        self.asked_questions.clear()
        self.collected_info.clear()
        # NOTE: full_log is intentionally kept as the permanent record


# Session storage: {session_id: ConversationState}
_session_states = {}


def _get_state(session_id):
    """Get or create ConversationState for a session."""
    if session_id not in _session_states:
        _session_states[session_id] = SessionState()
    return _session_states[session_id]


def reset_session(session_id):
    """Reset all conversation state for a session."""
    _session_states[session_id] = SessionState()


# NOTE: Hindi/Hinglish detection (is_hindi, is_hinglish,
# get_response_language, get_intro_text) is defined once near the top.


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _get_state_or_default(session_id):
    """Get state for session, creating if needed."""
    if session_id:
        return _get_state(session_id)
    # Fallback for backward compatibility
    return _get_state("_default")


def _persist_log(session_id, role, text):
    """Append one line to the permanent per-session log file (never truncated)."""
    try:
        import os as _os
        base = _os.path.join(_os.path.dirname(__file__), "..", "media", "chat_logs")
        _os.makedirs(base, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(session_id))[:64]
        path = _os.path.join(base, f"{safe or '_default'}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"role": role, "content": text}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def add_to_history(state, role, text, session_id=None):
    """Add message to sliding window + permanent full log."""
    state.conversation_history.append({"role": role, "content": text})
    if len(state.conversation_history) > MAX_HISTORY:
        del state.conversation_history[:-MAX_HISTORY]
    # permanent record: never truncated, never cleared mid-session
    state.full_log.append({"role": role, "content": text})
    if session_id is not None:
        _persist_log(session_id, role, text)
    if role == "assistant" and text:
        state.recent_answers.append(text.strip().lower())
        if len(state.recent_answers) > 12:
            del state.recent_answers[:-12]


def is_yes(text):
    """Check if text indicates yes/agreement."""
    if not text:
        return False
    text = text.lower().strip()
    yes_patterns = [
        r"\byes\b", r"\byeah\b", r"\byep\b", r"\bsure\b", r"\bokay\b", r"\bok\b",
        r"\bplease\b.*\byes\b", r"^please$", r"\bi want it\b", r"\bi do\b",
        r"^\s*yes\s+please\s*$", r"tell me.*more", r"give me.*info", r"\bhaan\b", r"\bji\b"
    ]
    if re.search(r"\byesterday\b", text):
        pass
    return any(re.search(pattern, text) for pattern in yes_patterns)


def is_no(text):
    """Check if text indicates no/disagreement."""
    if not text:
        return False
    text = text.lower().strip()
    no_patterns = [
        r"\bno\b", r"\bnope\b", r"\bnah\b", r"\bnot now\b", r"\bno thanks\b",
        r"\bno thank you\b", r"\bi don'?t\b", r"\bi do not\b", r"\bnot interested\b", r"\bskip\b",
        r"\bnahi\b", r"\bnahin\b"
    ]
    return any(re.search(pattern, text) for pattern in no_patterns)


def wants_to_exit(text):
    """Check if user wants to exit."""
    if not text:
        return False
    text = text.lower().strip()
    exit_patterns = [
        "quit", "exit", "end conversation", "end the conversation", "stop conversation",
        "stop chatting", "i want to leave", "i want to stop", "that's all", "that is all",
        "i'm done", "im done", "done", "goodbye", "bye", "बंद करो", "रुको"
    ]
    return any(phrase in text for phrase in exit_patterns)


def response_is_question(text):
    """Check if text is a question."""
    if not text:
        return False
    return "?" in text.strip()


def _is_repeating(state, new_text):
    """Check if new_text is too similar to recent answers."""
    if not new_text or not state.recent_answers:
        return False
    low = new_text.strip().lower()
    if low in state.recent_answers:
        return True
    new_words = set(low.split())
    for prev in state.recent_answers:
        prev_words = set(prev.split())
        if not new_words or not prev_words:
            continue
        overlap = len(new_words & prev_words) / max(len(new_words), len(prev_words))
        if overlap > 0.85:
            return True
    return False


def _is_question_asked(state, question):
    """Check if a similar question was already asked."""
    if not question:
        return False
    q_lower = question.lower().strip()
    # Normalize by removing question marks and extra whitespace
    q_normalized = re.sub(r'[?।\s]+', ' ', q_lower).strip()
    for asked in state.asked_questions:
        asked_norm = re.sub(r'[?।\s]+', ' ', asked).strip()
        # Check word overlap
        q_words = set(q_normalized.split())
        a_words = set(asked_norm.split())
        if q_words and a_words:
            overlap = len(q_words & a_words) / max(len(q_words), len(a_words))
            if overlap > 0.75:
                return True
    return False


def mark_question_asked(state, question):
    """Mark a question as asked."""
    if question:
        q_lower = question.lower().strip()
        q_normalized = re.sub(r'[?।\s]+', ' ', q_lower).strip()
        state.asked_questions.add(q_normalized)


# =========================================================
# CONVERSATION INSTRUCTION
# =========================================================

def get_conversation_instruction(state):
    """Get the conversation instruction for the current state."""
    # First turn - must introduce
    if not state.has_introduced and not state.conversation_history:
        return """
This is the very first turn. You MUST start with exactly this introduction: "Hello, I'm MediKiosk, your clinic assistant. I'm here to listen and help -- how are you feeling today?" (or Hindi equivalent)
This is MANDATORY. Do not skip it. Do not say anything else first.
After the introduction, gently ask how you can help using polite phrasing like "Could you share..." instead of "Tell me...".
"""

    if state.conversation_finished:
        return """
The conversation has ended. Do not continue the medical conversation. Give only a short polite closing.
"""

    if state.exit_offer_pending:
        return """
The patient has been asked whether they want to end the conversation.
If the patient wants to end: give a short polite closing.
If the patient wants to continue: continue the conversation naturally.
Do not repeat the exit question.
"""

    if state.medication_offer_pending:
        return """
The patient has been asked whether they want general self-care suggestions and general OTC medication information for their pain.
If YES: first give 2-3 short self-care suggestions tailored to the pain, then brief general educational info about OTC options (paracetamol, ibuprofen). Always add disclaimer to check label and ask pharmacist/doctor. Do not give dosage. Do not prescribe.
If NO: continue conversation naturally. Do not repeat the medication question.
"""

    if state.medication_discussion:
        return """
The patient is currently discussing self-care suggestions and general medication information.
Provide 2-3 short general self-care suggestions relevant to the pain, then brief general educational information about commonly available OTC options.
Do not diagnose. Do not prescribe. Do not give a specific dosage. Do not claim a medication is definitely appropriate.
Always add a short disclaimer to consult a pharmacist or doctor and follow the package label.
For chest pain or red-flag symptoms advise prompt medical care.
After answering, continue naturally if the patient asks something else.
"""

    if state.assessment_complete:
        return """
The basic assessment is done. Do NOT ask another assessment question and do NOT repeat any offer or paragraph already said.
Chat casually and warmly like a friendly clinic assistant. Answer whatever the patient asks, keep it short and easy, and keep the conversation comfortable.
If the patient asks for medicine or relief options, give brief general educational information with a short disclaimer.
Never repeat a sentence or question already used in this session.
"""

    avoid = ""
    if state.asked_questions:
        asked_list = sorted(state.asked_questions)[:30]
        avoid = "\nQuestions already asked in this session (NEVER repeat these unless the patient explicitly asks to revisit):\n- " + "\n- ".join(asked_list) + "\n"
    known = ""
    if state.collected_info:
        known = "\nInformation the patient already gave (NEVER ask for this again): " + ", ".join(
            f"{k}={v}" for k, v in state.collected_info.items()
        ) + "\n"
    return """
Continue the patient's clinic conversation naturally.
Ask one relevant question if more information is useful.
Do not repeat information already provided by the patient.
Do not repeat questions that have already been asked.
If enough basic information has been collected, the assessment can be considered complete.
""" + avoid + known


def clean_response(text):
    """Clean up response text."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"[*_#>`~]+", "", text)
    text = re.sub(r"^\s*[-–•]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _remember_pain_context(text, state):
    """Keep last explicit pain mention so it survives history trimming."""
    lower = text.lower()
    pain_keywords = ["headache", "chest pain", "back pain", "stomach pain", "abdominal pain",
                     "joint pain", "muscle pain", "tooth", "throat pain", "knee pain", "shoulder pain",
                     "सिरदर्द", "सीने", "कमर", "पेट", "दांत", "गले"]
    for kw in pain_keywords:
        if kw in lower:
            state.last_pain_context = lower
            break
    if "pain" in lower and len(lower) < 200:
        state.last_pain_context = lower
    _update_collected_info(text, state)


def _update_collected_info(text, state):
    """Record what the patient already told us so we never re-ask for it."""
    low = text.lower()
    if re.search(r"\b\d+\s*(day|days|week|weeks|month|hour|hours)\b|कल|आज|हफ्त|दिन", low):
        state.collected_info["duration"] = text.strip()[:80]
    if re.search(r"severe|mild|moderate|sharp|dull|बहुत|तेज|हल्क|गंभीर", low):
        state.collected_info["severity"] = text.strip()[:80]
    if re.search(r"left|right|back|chest|head|stomach|बाईं|दाईं|सिर|सीने|कमर|पेट", low):
        state.collected_info["location"] = text.strip()[:80]
    if re.search(r"pain|ache|hurt|fever|cough|दर्द", low):
        state.collected_info.setdefault("symptom", text.strip()[:120])


def _build_suggestions_impl(state):
    """Build deterministic self-care suggestions + general OTC educational note."""
    if state.last_pain_context:
        combined = state.last_pain_context.lower()
        try:
            last_user = next(m["content"] for m in reversed(state.conversation_history) if m["role"] == "user")
            if last_user.lower() not in combined:
                combined += " " + last_user.lower()
        except StopIteration:
            pass
    else:
        combined = " ".join(
            m["content"] for m in state.conversation_history if m["role"] == "user"
        ).lower()

    is_chest = any(k in combined for k in ["chest pain", "chest tight", "pressure in chest"])
    is_headache = "headache" in combined or "head pain" in combined
    is_back = "back pain" in combined or "lower back" in combined
    is_stomach = any(k in combined for k in ["stomach pain", "abdominal pain", "belly pain"])
    is_joint = any(k in combined for k in ["joint pain", "knee pain", "shoulder pain", "arthritis"])
    is_muscle = any(k in combined for k in ["muscle pain", "body ache", "muscle ache"])
    is_tooth = "tooth" in combined
    is_throat = "throat pain" in combined or "sore throat" in combined

    suggestions = []
    otc_note = ""
    lang = getattr(state, "response_lang", "english")
    if lang == "hindi":
        disclaimer = " यह केवल सामान्य जानकारी है -- कृपया पैकेज लेबल देखें और उपयोग से पहले फार्मासिस्ट या डॉक्टर से पूछें।"
        if is_chest:
            return ([
                "सीने में दर्द गंभीर हो सकता है, कृपया दबाव, जकड़न, हाथ या जबड़े तक फैलता दर्द, सांस फूलना या पसीना होने पर तुरंत चिकित्सा सहायता लें।",
                "भारी मेहनत से बचें, जांच में देरी न करें और जल्दी क्लिनिक जाएं।",
            ], "सीने के दर्द में डॉक्टर की जांच से पहले खुद दवा न लें।" + disclaimer)
        if is_headache:
            return ([
                "शांत, हल्के अंधेरे कमरे में आराम करें और कुछ देर स्क्रीन से दूरी रखें।",
                "पानी पीते रहें और माथे पर ठंडी सिकाई आजमा सकते हैं।",
                "नींद नियमित रखें और लगातार काम से छोटे ब्रेक लें।",
            ], "सिरदर्द में सामान्यतः पैरासिटामोल और आइबुप्रोफेन जैसी दवाएं बिना पर्चे के मिलती हैं। लेबल देखें और फार्मासिस्ट से पूछें।" + disclaimer)
        if is_back:
            return ([
                "बैठते समय सीधी मुद्रा रखें और भारी वजन उठाने से बचें।",
                "हल्की सैर और हलचल अक्सर लंबे आराम से बेहतर होती है।",
                "मांसपेशियों के दर्द में गुनगुनी सिकाई आराम दे सकती है।",
            ], "कमर या मांसपेशी दर्द में सामान्यतः पैरासिटामोल और आइबुप्रोफेन पर विचार किया जाता है। लेबल का पालन करें।" + disclaimer)
        if is_stomach:
            return ([
                "पानी पिएं और हल्का, सुपाच्य भोजन लें। मसालेदार, तैलीय भोजन से बचें।",
                "आराम करें और खाने के तुरंत बाद न लेटें।",
                "बुखार, उल्टी, खून या तेज दर्द हो तो तुरंत देखभाल लें।",
            ], "पेट की परेशानी में एसिडिटी के लिए एंटासिड पर विचार किया जाता है, लगातार दर्द में डॉक्टर से मिलें।" + disclaimer)
        if is_joint or is_muscle:
            return ([
                "प्रभावित हिस्से को आराम दें और 1-2 दिन भारी काम से बचें।",
                "हल्का खिंचाव और ठंडी या गुनगुनी सिकाई आराम दे सकती है।",
                "पानी पिएं और हल्की गतिविधि जारी रखें।",
            ], "जोड़ या मांसपेशी दर्द में पैरासिटामोल और आइबुप्रोफेन सामान्य विकल्प हैं। लेबल देखें।" + disclaimer)
        return ([
            "आराम करें, पानी पिएं और दर्द बढ़ाने वाली गतिविधियों से बचें।",
            "दर्द कब शुरू हुआ, कितना तेज है और क्या कारण हो सकता है, यह डॉक्टर को बताएं।",
            "तेज, बढ़ता दर्द, बुखार या सूजन हो तो तुरंत देखभाल लें।",
        ], "बिना पर्चे के मिलने वाले सामान्य विकल्पों में पैरासिटामोल और आइबुप्रोफेन शामिल हैं। लेबल देखें और डॉक्टर से पूछें।" + disclaimer)

    disclaimer = " This is general information only -- please check the package label and ask a pharmacist or doctor before use. Suitability depends on allergies, other medicines and health conditions."

    if is_chest:
        suggestions = [
            "Chest pain can be serious, please seek prompt medical care if you have pressure, tightness, pain spreading to arm or jaw, breathlessness or sweating.",
            "Avoid strenuous activity, do not delay evaluation, and consider contacting emergency services or visiting the clinic quickly.",
        ]
        otc_note = "For chest pain self-medication is not advised until evaluated by a clinician." + disclaimer
    elif is_headache:
        suggestions = [
            "Rest in a quiet, dim room and limit screen time for a while.",
            "Drink water regularly and try a cold compress on the forehead if it feels soothing.",
            "Keep a regular sleep schedule and take short breaks from continuous work.",
        ]
        otc_note = "For headache, general options that in many places are available without prescription include paracetamol (acetaminophen) and ibuprofen. Follow the label and ask a pharmacist if unsure." + disclaimer
    elif is_back:
        suggestions = [
            "Try to keep a good posture while sitting and avoid heavy lifting for now.",
            "Gentle movement and short walks are often better than prolonged bed rest.",
            "A warm compress may feel soothing for muscle-type back pain.",
        ]
        otc_note = "For back or muscle-type pain, general over-the-counter options often considered include paracetamol and ibuprofen, following the label." + disclaimer
    elif is_stomach:
        suggestions = [
            "Sip water and prefer light, bland meals; avoid spicy, oily or very heavy food for now.",
            "Rest and avoid lying flat immediately after eating.",
            "Note any fever, vomiting, blood or severe pain and seek care promptly if present.",
        ]
        otc_note = "For stomach discomfort, people sometimes consider antacids for acidity where available, but for ongoing pain it is best to consult a clinician." + disclaimer
    elif is_joint or is_muscle:
        suggestions = [
            "Rest the affected area and avoid strenuous or repetitive strain for a day or two.",
            "Gentle stretching and a cold or warm compress may feel soothing.",
            "Keep hydrated and maintain light activity as tolerated.",
        ]
        otc_note = "For joint or muscle ache, general over-the-counter options commonly available include paracetamol and ibuprofen; check the label." + disclaimer
    elif is_tooth:
        suggestions = [
            "Rinse gently with lukewarm water and keep the area clean.",
            "Avoid very hot, cold or sugary foods that may aggravate pain.",
            "Seek dental evaluation soon, especially with swelling or fever.",
        ]
        otc_note = "For tooth pain, general over-the-counter pain relief options like paracetamol or ibuprofen are sometimes used short-term, following the label, until dental review." + disclaimer
    elif is_throat:
        suggestions = [
            "Keep warm fluids and rest your voice.",
            "Gargling with lukewarm saline may feel soothing for sore throat.",
            "Avoid smoking and very dry air.",
        ]
        otc_note = "For sore throat, general options like paracetamol or sore-throat lozenges are sometimes used where available, following the label." + disclaimer
    else:
        suggestions = [
            "Rest and keep hydrated, and avoid activities that worsen the pain.",
            "Note when the pain started, its severity and any triggers to share with the clinician.",
            "Seek care promptly if pain is severe, worsening or accompanied by fever, swelling or breathing difficulty.",
        ]
        otc_note = "General over-the-counter options that in many places do not require a prescription include paracetamol (acetaminophen) and ibuprofen. Follow the label and ask a pharmacist or doctor." + disclaimer

    return suggestions, otc_note


def format_suggestions_response(suggestions, otc_note):
    """Combine suggestions + OTC into a single short spoken answer (2-4 sentences)."""
    part1 = " ".join(suggestions[:3])
    return f"{part1} {otc_note}".strip()


# =========================================================
# OLLAMA
# =========================================================

def ask_ollama(text, state):
    response_lang = get_response_language(text)
    state.response_lang = response_lang

    lang_directive = (
        "IMPORTANT: The patient's latest message is in Hindi. Reply ONLY in Hindi (Devanagari script)."
        if response_lang == "hindi" else
        "IMPORTANT: The patient's latest message is in English. Reply ONLY in English."
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n" + get_conversation_instruction(state) + "\n" + lang_directive
        }
    ]
    messages.extend(state.conversation_history)
    messages.append({"role": "user", "content": text})

    response = chat(
        model=OLLAMA_MODEL,
        messages=messages,
        options={
            "temperature": 0.45,
            "num_predict": 80,
            "num_ctx": 2048,
        },
        keep_alive="10m"
    )

    answer = clean_response(response.message.content)

    if response_lang == 'english':
        if re.match(r"^\s*Tell me\b", answer, re.IGNORECASE):
            answer = re.sub(r"^\s*Tell me\b", "Could you share", answer, flags=re.IGNORECASE)
        if re.match(r"^\s*Describe\b", answer, re.IGNORECASE):
            answer = re.sub(r"^\s*Describe\b", "Would you mind describing", answer, flags=re.IGNORECASE)
    else:
        answer = re.sub(r"^\s*बताओ\b", "क्या आप बता सकते हैं", answer)
        answer = re.sub(r"^\s*बताइए\b", "क्या आप बता सकते हैं", answer)

    # Force intro on first turn if AI didn't include it
    if not state.has_introduced and not state.conversation_history:
        intro_text = get_intro_text(response_lang)
        if intro_text.lower() not in answer.lower():
            answer = intro_text + " " + answer

    return answer


def ask_gemini(text, state):
    if gemini_client is None:
        raise RuntimeError("Gemini API key not available")

    response_lang = get_response_language(text)
    state.response_lang = response_lang

    history_text = ""
    for m in state.conversation_history:
        role = "Patient" if m["role"] == "user" else "MediKiosk"
        history_text += f"{role}: {m['content']}\n"

    lang_directive = (
        "IMPORTANT: The patient's latest message is in Hindi. Reply ONLY in Hindi (Devanagari script)."
        if response_lang == "hindi" else
        "IMPORTANT: The patient's latest message is in English. Reply ONLY in English."
    )

    prompt = f"""
{SYSTEM_PROMPT}

Conversation control:
{get_conversation_instruction(state)}

{lang_directive}

Previous conversation:
{history_text}

Patient:
{text}

MediKiosk:
"""

    response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    answer = clean_response(response.text)

    if response_lang == 'english':
        if re.match(r"^\s*Tell me\b", answer, re.IGNORECASE):
            answer = re.sub(r"^\s*Tell me\b", "Could you share", answer, flags=re.IGNORECASE)
        if re.match(r"^\s*Describe\b", answer, re.IGNORECASE):
            answer = re.sub(r"^\s*Describe\b", "Would you mind describing", answer, flags=re.IGNORECASE)
    else:
        answer = re.sub(r"^\s*बताओ\b", "क्या आप बता सकते हैं", answer)
        answer = re.sub(r"^\s*बताइए\b", "क्या आप बता सकते हैं", answer)

    if not state.has_introduced and not state.conversation_history:
        intro_text = get_intro_text(response_lang)
        if intro_text.lower() not in answer.lower():
            answer = intro_text + " " + answer

    return answer


def _ask_ai_internal(text, session_id):
    """Internal ask_ai that uses session state."""
    state = _get_state(session_id)
    state.response_lang = get_response_language(text)
    _remember_pain_context(text, state)

    if not text or not text.strip():
        return "Could you please repeat that?" if state.response_lang == "english" else "कृपया दोहरा सकते हैं?"
    text = text.strip()

    if state.conversation_finished:
        return "The conversation has ended, so please start a new chat if you need further help."

    state.conversation_turns += 1

    # Exit offer handling
    if state.exit_offer_pending:
        exit_response = handle_exit_response(text, state)
        if exit_response:
            add_to_history(state, "user", text, session_id)
            add_to_history(state, "assistant", exit_response, session_id)
            return exit_response

    # Medication offer handling
    if state.medication_offer_pending:
        med_response = handle_medication_response(text, state)
        if med_response:
            add_to_history(state, "user", text, session_id)
            add_to_history(state, "assistant", med_response, session_id)
            return med_response

    # Direct suggestion/medicine request (English + Hindi keywords).
    # Catches: "what medicine can I take", "which tablet", "suggest medicine",
    # "need pain relief", "paracetamol", "दवा", "सुझाव", etc.
    _low = text.lower()
    _wants_meds = bool(re.search(
        r"(what|which|give|tell|suggest|recommend|need|want|can i|should i|name|list).{0,20}(medicine|tablet|tablets|capsule|drug|dawa|दवा)"
        r"|(medicine|tablet|tablets|capsule).{0,20}(take|take\?|for|name|list|suggest|recommend)"
        r"|\b(otc|paracetamol|ibuprofen|acetaminophen|dose|dosage|pain.*relief|relief.*pain)\b"
        r"|(दवा|सुझाव|उपाय|दर्द.*कम)",
        _low))
    if _wants_meds:
        suggestions, otc = _build_suggestions_impl(state)
        answer = format_suggestions_response(suggestions, otc)
        add_to_history(state, "user", text, session_id)
        add_to_history(state, "assistant", answer, session_id)
        state.has_introduced = True
        return answer

    # Long conversation check
    if state.medication_offer_pending and state.conversation_turns >= MAX_CONVERSATION_TURNS:
        state.medication_offer_pending = False
        state.medication_offered = True

    if state.conversation_turns >= MAX_CONVERSATION_TURNS and not state.exit_offer_pending:
        state.exit_offer_pending = True
        answer = "We have discussed quite a bit, would you like to end the conversation?"
        add_to_history(state, "user", text, session_id)
        add_to_history(state, "assistant", answer, session_id)
        return answer

    # Medication offer: asked ONCE per session, kept short (never repeated).
    if (state.assessment_complete and not state.medication_offered
            and not state.medication_offer_pending and not state.medication_discussion):
        state.medication_offer_pending = True
        state.medication_offered = True
        if state.response_lang == "hindi":
            answer = "मैंने आपकी जानकारी ले ली है। अब आप बेझिझक कुछ भी पूछ सकते हैं।"
        else:
            answer = "I've taken your info. Now feel free to ask me anything."
        add_to_history(state, "user", text, session_id)
        add_to_history(state, "assistant", answer, session_id)
        return answer

    # Get AI response
    try:
        answer = ask_ollama(text, state)
    except Exception as error:
        print(f"Ollama unavailable: {error}")
        try:
            answer = ask_gemini(text, state)
        except Exception as error:
            print(f"Gemini unavailable: {error}")
            return "I'm having trouble responding right now. Could you please repeat that?"

    # Post-process answer: intro once per session only
    if not state.has_introduced and not state.conversation_history:
        intro_text = get_intro_text(state.response_lang)
        if intro_text.lower() not in answer.lower():
            answer = intro_text + " " + answer

    # Repetition guard: exact/near duplicate OR already-asked question
    if _is_repeating(state, answer) or (response_is_question(answer) and _is_question_asked(state, answer)):
        try:
            avoid = sorted(state.asked_questions)[:15]
            retry_text = text + " [please ask a DIFFERENT question, avoid: " + "; ".join(avoid) + "]"
            retry_answer = ask_ollama(retry_text, state)
            if not (_is_repeating(state, retry_answer) or (response_is_question(retry_answer) and _is_question_asked(state, retry_answer))):
                answer = retry_answer
        except Exception:
            pass

    # Mark questions asked (never cleared mid-session)
    if response_is_question(answer):
        mark_question_asked(state, answer)
        state.question_count += 1
        if state.question_count >= MAX_QUESTIONS:
            state.assessment_complete = True

    add_to_history(state, "user", text, session_id)
    add_to_history(state, "assistant", answer, session_id)
    state.has_introduced = True

    return answer


def handle_exit_response(text, state):
    if is_yes(text):
        state.exit_offer_pending = False
        state.conversation_finished = True
        return "Thank you for speaking with MediKiosk, and please follow up with the clinic for further care."
    if is_no(text):
        state.exit_offer_pending = False
        return "Okay, we can continue."
    return None


def handle_medication_response(text, state):
    if is_yes(text) and not is_no(text):
        state.medication_offer_pending = False
        state.medication_discussion = True
        state.medication_offered = True
        suggestions, otc = _build_suggestions_impl(state)
        return format_suggestions_response(suggestions, otc)
    if is_no(text):
        state.medication_offer_pending = False
        state.medication_discussion = False
        state.medication_offered = True
        # Stay in casual chat mode; do NOT restart assessment or re-offer.
        if state.response_lang == "hindi":
            return "ठीक है, कोई बात नहीं। आप आराम से कुछ भी पूछ सकते हैं।"
        return "Okay, no problem. Feel free to ask me anything."
    # Ambiguous reply (user just kept talking): clear pending, mark offered
    # so the offer never repeats, and let normal chat continue.
    state.medication_offer_pending = False
    state.medication_offered = True
    return None


def ask_ai(text, session_id=None):
    """Main entry point - handles session management and delegates to internal logic."""
    if session_id is None:
        session_id = "_default"
    return _ask_ai_internal(text, session_id)


def build_suggestions_and_otc(session_id=None):
    """Public wrapper: accepts a session_id string (used by views)."""
    state = _get_state(session_id or "_default")
    return _build_suggestions_impl(state)


# Backward-compatible shims (old code/tests used globals)
def reset_conversation(session_id=None):
    _get_state(session_id or "_default").reset()


def reset_chat(session_id=None):
    return reset_conversation(session_id)


def reset_patient(session_id=None):
    st = _get_state(session_id or "_default")
    st.current_patient_id = None


def reset_session(session_id):
    """Reset all conversation state for a session."""
    _get_state(session_id).reset()


def get_full_log(session_id=None):
    """Return the complete untruncated record of a session."""
    return list(_get_state(session_id or "_default").full_log)