"""
MediKiosk AI Services

Primary AI  : Ollama / llama3.2:1b
Fallback AI : Gemini

Ollama is preferred because it runs locally and can be very fast.
Gemini is used only when Ollama is unavailable.
"""

import os
import re
import time

from ollama import chat
from google import genai


from database.patient_service import (
    create_patient,
    update_patient,
)

# =========================================================
# CONFIG
# =========================================================

OLLAMA_MODEL = "llama3.2:1b"

GEMINI_MODEL = "gemini-3.6-flash"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Keep this short so a failed Ollama request does not freeze
# the voice assistant for a long time.
OLLAMA_TIMEOUT = 5


# =========================================================
# AI BEHAVIOR
# =========================================================

SYSTEM_PROMPT = """
You are MediKiosk, a voice assistant in a healthcare clinic.

Speak naturally like a calm clinic assistant.

Rules:

- Keep every response to ONE short sentence.
- Ask only ONE question at a time.
- Ask only questions that are relevant to the patient's problem.
- Collect only the basic information needed to understand the patient's complaint.
- Important information may include symptoms, duration, severity, location, and relevant associated symptoms.
- Do not ask unnecessary or repetitive questions.
- Ask a maximum of FOUR questions during one patient assessment.
- If you already have enough information before four questions, STOP asking questions.
- After you have enough information, give the patient a short helpful final response instead of asking another question.
- The final response should briefly summarize what the patient told you and provide appropriate general guidance.
- Do not diagnose diseases.
- Do not prescribe medicines.
- Do not use markdown, bullets, symbols, or emojis.
- Use simple spoken English.
- If the patient's statement is unclear, ask them to repeat or clarify it.
- Stay focused on the patient's clinic visit.
"""


# =========================================================
# GEMINI CLIENT
# =========================================================

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception as error:
        print("Gemini initialization error:", error)


# =========================================================
# CONVERSATION MEMORY
# =========================================================
conversation_history = []

MAX_HISTORY = 8

MAX_QUESTIONS = 4

question_count = 0
assessment_complete = False


# =========================================================
# CURRENT PATIENT STORAGE
# =========================================================

current_patient_id = None


def reset_patient():
    global current_patient_id
    current_patient_id = None


def reset_conversation():
    """Clear memory for a new patient."""

    global question_count
    global assessment_complete

    conversation_history.clear()

    question_count = 0
    assessment_complete = False


def add_to_history(role, text):

    conversation_history.append({
        "role": role,
        "content": text
    })

    if len(conversation_history) > MAX_HISTORY:
        del conversation_history[:-MAX_HISTORY]


# =========================================================
# ASSESSMENT CONTROL
# =========================================================

def get_assessment_instruction():
    global question_count

    if question_count >= MAX_QUESTIONS:
        return """
This is the end of the patient assessment.
Do NOT ask another question.
Give a short final response based on the information collected.
Summarize the patient's main complaint and give appropriate general guidance.
Do not diagnose or prescribe.
"""

    remaining = MAX_QUESTIONS - question_count

    return f"""
You may ask ONE more relevant question.
This is question {question_count + 1} of {MAX_QUESTIONS}.
After asking this question, do not ask additional questions unless another turn is allowed.
Keep the question short and relevant.
"""


def response_is_question(text):
    """Check whether the AI response is asking the patient a question."""

    if not text:
        return False

    return "?" in text.strip()


# =========================================================
# RESPONSE CLEANUP
# =========================================================

def clean_response(text):

    if not text:
        return ""

    text = str(text)

    # Remove code blocks
    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove markdown characters
    text = re.sub(
        r"[*_#>`~]+",
        "",
        text
    )

    # Remove bullets
    text = re.sub(
        r"^\s*[-•]\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove numbered lists
    text = re.sub(
        r"^\s*\d+[.)]\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove excessive whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# OLLAMA
# =========================================================

def ask_ollama(text):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + get_assessment_instruction()
        }
    ]

    messages.extend(conversation_history)

    messages.append({
        "role": "user",
        "content": text
    })

    response = chat(
        model=OLLAMA_MODEL,
        messages=messages,
        options={
            "temperature": 0.1,

            # Short output = faster response
            "num_predict": 21,

            # Smaller context = faster processing
            "num_ctx": 2048,

            # Keep model loaded in memory
        },
        keep_alive="10m"
    )

    answer = response.message.content

    return clean_response(answer)


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(text):

    if gemini_client is None:
        raise RuntimeError(
            "Gemini API key not available"
        )

    history_text = ""

    for message in conversation_history:

        if message["role"] == "user":

            history_text += (
                f"Patient: {message['content']}\n"
            )

        elif message["role"] == "assistant":

            history_text += (
                f"MediKiosk: {message['content']}\n"
            )

    prompt = f"""
{SYSTEM_PROMPT}

Previous conversation:
{history_text}

Patient:
{text}

MediKiosk:
"""

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    answer = response.text

    return clean_response(answer)



# =========================================================
# PATIENT DATA EXTRACTION
# =========================================================

def extract_patient_data(text):
    """
    Extract simple patient information from spoken/text input.

    This does not replace the AI model.
    It only converts obvious information into
    fields supported by database.models.Patient.
    """

    data = {}

    text_lower = text.lower().strip()


    # -------------------------
    # NAME
    # -------------------------

    name_match = re.search(
        r"(?:my name is|i am|i'm|name is)\s+([a-zA-Z ]{2,50})",
        text,
        re.IGNORECASE
    )

    if name_match:
        name = name_match.group(1).strip()

        # Remove common trailing phrases
        name = re.split(
            r"\b(?:and|i have|with|my age|i am)\b",
            name,
            flags=re.IGNORECASE
        )[0].strip()

        if name:
            data["name"] = name


    # -------------------------
    # AGE
    # -------------------------

    age_match = re.search(
        r"(?:i am|i'm|age is|my age is)\s*(\d{1,3})\s*(?:years?|yrs?)?",
        text,
        re.IGNORECASE
    )

    if age_match:
        data["age"] = int(age_match.group(1))


    # -------------------------
    # GENDER
    # -------------------------

    if re.search(r"\b(male|man|boy)\b", text_lower):
        data["gender"] = "Male"

    elif re.search(r"\b(female|woman|girl)\b", text_lower):
        data["gender"] = "Female"


    # -------------------------
    # DURATION
    # -------------------------

    duration_match = re.search(
        r"\b(?:for|since)\s+(\d+)\s*(day|days|week|weeks|month|months|year|years)\b",
        text,
        re.IGNORECASE
    )

    if duration_match:
        data["duration"] = (
            f"{duration_match.group(1)} "
            f"{duration_match.group(2)}"
        )


    # -------------------------
    # SEVERITY
    # -------------------------

    severity_words = [
        "mild",
        "moderate",
        "severe",
        "very severe",
        "slight"
    ]

    for severity in severity_words:
        if severity in text_lower:
            data["severity"] = severity.title()
            break


    # -------------------------
    # SYMPTOMS
    # -------------------------

    symptom_match = re.search(
        r"(?:i have|i'm having|i am having|suffering from|symptoms? (?:are|is))\s+(.+)",
        text,
        re.IGNORECASE
    )

    if symptom_match:
        symptoms = symptom_match.group(1).strip()

        # Don't store an entire long conversation as symptoms
        if len(symptoms) <= 200:
            data["symptoms"] = symptoms


    return data

# =========================================================
# SAVE PATIENT DATA
# =========================================================

def save_patient_data(text):
    """
    Save information extracted from AI/voice input
    using the existing SQLAlchemy storage system.
    """

    global current_patient_id

    data = extract_patient_data(text)

    if not data:
        return None


    # =====================================================
    # CREATE NEW PATIENT
    # =====================================================

    if current_patient_id is None:

        patient = create_patient(
            name=data.get("name"),
            age=data.get("age"),
            gender=data.get("gender"),
            symptoms=data.get("symptoms"),
            duration=data.get("duration"),
            severity=data.get("severity"),
        )

        current_patient_id = patient.patient_id

        print(
            f"Patient data saved. "
            f"Patient ID: {current_patient_id}"
        )

        return patient


    # =====================================================
    # UPDATE EXISTING PATIENT
    # =====================================================

    patient = update_patient(
        current_patient_id,
        **data
    )

    if patient:
        print(
            f"Patient data updated. "
            f"Patient ID: {current_patient_id}"
        )

    return patient

# =========================================================
# MAIN AI FUNCTION
# =========================================================

def ask_ai(text):

    global question_count
    global assessment_complete

    if not text:
        return "Could you please repeat that?"

    text = text.strip()

    if not text:
        return "Could you please repeat that?"


    if assessment_complete:
        return "Thank you. I have collected enough information. Please wait while the clinic reviews your information."


        # Save structured patient information
    # using the existing database storage system.
    try:
        save_patient_data(text)
    except Exception as error:
        print(
            "Patient storage error:",
            error
        )

    # =====================================================
    # OLLAMA FIRST
    # =====================================================

    try:

        start = time.time()

        answer = ask_ollama(text)

        elapsed = time.time() - start

        if answer:

            print(
                f"Ollama AI time: {elapsed:.2f}s"
            )

            print(
                "AI provider: Ollama"
            )

            add_to_history(
                "user",
                text
            )

            add_to_history(
                "assistant",
                answer
            )


            if response_is_question(answer):
                question_count
                question_count += 1

                print(
                    f"Assessment question count: "
                    f"{question_count}/{MAX_QUESTIONS}"
                )

            if question_count >= MAX_QUESTIONS:
                assessment_complete = True    



            return answer

    except Exception as error:

        elapsed = time.time() - start

        print(
            f"Ollama unavailable after "
            f"{elapsed:.2f}s:",
            error
        )


    # =====================================================
    # GEMINI FALLBACK
    # =====================================================

    try:

        start = time.time()

        answer = ask_gemini(text)

        elapsed = time.time() - start

        if answer:

            print(
                f"Gemini AI time: {elapsed:.2f}s"
            )

            print(
                "AI provider: Gemini"
            )

            add_to_history(
                "user",
                text
            )

            add_to_history(
                "assistant",
                answer
            )

            if response_is_question(answer):
                question_count
                question_count += 1

                print(
                    f"Assessment question count: "
                    f"{question_count}/{MAX_QUESTIONS}"
                )


            if question_count >= MAX_QUESTIONS:
                assessment_complete = True


            return answer

    except Exception as error:

        print(
            "Gemini unavailable:",
            error
        )


    # =====================================================
    # BOTH FAILED
    # =====================================================

    return (
        "I'm having trouble responding right now. "
        "Could you please repeat that?"
    )