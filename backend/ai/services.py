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

OLLAMA_TIMEOUT = 5

MAX_HISTORY = 8

# Number of user turns before offering to end a long conversation.
MAX_CONVERSATION_TURNS = 15

# Number of assessment questions before offering medication information.
MAX_QUESTIONS = 4


# =========================================================
# AI BEHAVIOR
# =========================================================

SYSTEM_PROMPT = """
You are MediKiosk, a voice assistant in a healthcare clinic.

Speak naturally like a calm clinic assistant.

Rules:

- Keep normal responses to ONE short sentence.
- Ask only ONE question at a time.
- Ask only questions that are relevant to the patient's problem.
- Use the previous conversation to understand what the patient already told you.
- Do not repeat questions that have already been answered.
- Collect useful basic information such as symptoms, duration, severity, location, and related symptoms.
- Ask relevant questions naturally instead of following a rigid script.
- Do not diagnose diseases.
- Do not prescribe medicines.
- Do not provide medication dosages.
- If medication information is requested, provide general educational information only.
- Do not claim that a particular medicine is definitely suitable for the patient.
- If the patient's statement is unclear, ask them to clarify it.
- Use simple spoken English.
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
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception as error:
        print(
            "Gemini initialization error:",
            error
        )


# =========================================================
# CONVERSATION MEMORY
# =========================================================

conversation_history = []

question_count = 0
assessment_complete = False

medication_offer_pending = False
medication_discussion = False

conversation_turns = 0

exit_offer_pending = False
conversation_finished = False


# =========================================================
# CURRENT PATIENT STORAGE
# =========================================================

current_patient_id = None


# =========================================================
# RESET PATIENT
# =========================================================

def reset_patient():

    global current_patient_id

    current_patient_id = None


# =========================================================
# RESET CONVERSATION
# =========================================================

def reset_conversation():
    """
    Clear all conversation state for a new patient.
    """

    global question_count
    global assessment_complete
    global medication_offer_pending
    global medication_discussion
    global conversation_turns
    global exit_offer_pending
    global conversation_finished

    conversation_history.clear()

    question_count = 0
    assessment_complete = False

    medication_offer_pending = False
    medication_discussion = False

    conversation_turns = 0

    exit_offer_pending = False
    conversation_finished = False


# =========================================================
# HISTORY
# =========================================================

def add_to_history(role, text):

    conversation_history.append({
        "role": role,
        "content": text
    })

    if len(conversation_history) > MAX_HISTORY:
        del conversation_history[:-MAX_HISTORY]


# =========================================================
# YES / NO DETECTION
# =========================================================

def is_yes(text):

    text = text.lower().strip()

    yes_patterns = [
        r"^yes$",
        r"^yeah$",
        r"^yep$",
        r"^sure$",
        r"^okay$",
        r"^ok$",
        r"^please$",
        r"^yes please$",
        r"^yeah please$",
        r"^sure please$",
        r"^i want it$",
        r"^i do$",
    ]

    return any(
        re.search(pattern, text)
        for pattern in yes_patterns
    )


def is_no(text):

    text = text.lower().strip()

    no_patterns = [
        r"^no$",
        r"^nope$",
        r"^nah$",
        r"^not now$",
        r"^no thanks$",
        r"^no thank you$",
        r"^i don't$",
        r"^i do not$",
    ]

    return any(
        re.search(pattern, text)
        for pattern in no_patterns
    )


# =========================================================
# EXIT DETECTION
# =========================================================

def wants_to_exit(text):

    text = text.lower().strip()

    exit_patterns = [
        "quit",
        "exit",
        "end conversation",
        "end the conversation",
        "stop conversation",
        "stop chatting",
        "i want to leave",
        "i want to stop",
        "that's all",
        "that is all",
        "i'm done",
        "im done",
        "done",
        "goodbye",
        "bye",
    ]

    return any(
        phrase in text
        for phrase in exit_patterns
    )


# =========================================================
# RESPONSE QUESTION CHECK
# =========================================================

def response_is_question(text):

    if not text:
        return False

    return "?" in text.strip()


# =========================================================
# CONVERSATION INSTRUCTION
# =========================================================

def get_conversation_instruction():

    if conversation_finished:

        return """
The conversation has ended.

Do not continue the medical conversation.
Give only a short polite closing.
"""


    if exit_offer_pending:

        return """
The patient has been asked whether they want to end the conversation.

If the patient wants to end:
give a short polite closing.

If the patient wants to continue:
continue the conversation naturally.

Do not repeat the exit question.
"""


    if medication_offer_pending:

        return """
The patient has been asked whether they want general medication information.

If the patient says YES:
provide brief general educational information about medication options that may commonly be used for the symptoms discussed.

Do not prescribe.
Do not give a dosage.
Do not say the patient definitely needs a medicine.

If the patient says NO:
continue the conversation naturally.

Do not repeat the medication question.
"""


    if medication_discussion:

        return """
The patient is currently discussing medication information.

Provide general educational information only.

Do not diagnose.
Do not prescribe.
Do not give a specific dosage.
Do not claim that a medication is definitely appropriate.

After answering, continue naturally if the patient asks something else.
"""


    if assessment_complete:

        return """
The basic assessment has been completed.

Do not ask another medical assessment question.

Ask the patient whether they would like general information about medication options.

Ask only that one question.
"""


    return """
Continue the patient's clinic conversation naturally.

Ask one relevant question if more information is useful.

Do not repeat information already provided by the patient.

If enough basic information has been collected, the assessment can be considered complete.
"""


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
            "content": (
                SYSTEM_PROMPT
                + "\n"
                + get_conversation_instruction()
            )
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

            # Short responses keep the assistant fast.
            "num_predict": 50,

            # Context size.
            "num_ctx": 2048,
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

Conversation control:
{get_conversation_instruction()}

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

        data["age"] = int(
            age_match.group(1)
        )


    # -------------------------
    # GENDER
    # -------------------------

    if re.search(
        r"\b(male|man|boy)\b",
        text_lower
    ):

        data["gender"] = "Male"

    elif re.search(
        r"\b(female|woman|girl)\b",
        text_lower
    ):

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
        "very severe",
        "severe",
        "moderate",
        "mild",
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
# HANDLE MEDICATION RESPONSE
# =========================================================

def handle_medication_response(text):

    global medication_offer_pending
    global medication_discussion
    global assessment_complete

    if is_yes(text):

        medication_offer_pending = False
        medication_discussion = True

        return (
            "I can give you general information about medication options "
            "that are commonly used for symptoms like these."
        )

    if is_no(text):

        medication_offer_pending = False
        medication_discussion = False

        assessment_complete = False

        return (
            "Okay, we can continue discussing your concerns."
        )

    return None


# =========================================================
# HANDLE EXIT RESPONSE
# =========================================================

def handle_exit_response(text):

    global exit_offer_pending
    global conversation_finished

    if is_yes(text):

        exit_offer_pending = False
        conversation_finished = True

        return (
            "Thank you for speaking with MediKiosk, and please follow up with the clinic for further care."
        )

    if is_no(text):

        exit_offer_pending = False

        return (
            "Okay, we can continue."
        )

    return None


# =========================================================
# MAIN AI FUNCTION
# =========================================================

def ask_ai(text):

    global question_count
    global assessment_complete
    global medication_offer_pending
    global medication_discussion
    global conversation_turns
    global exit_offer_pending
    global conversation_finished


    # =====================================================
    # EMPTY INPUT
    # =====================================================

    if not text:

        return "Could you please repeat that?"


    text = text.strip()


    if not text:

        return "Could you please repeat that?"


    # =====================================================
    # CONVERSATION ALREADY FINISHED
    # =====================================================

    if conversation_finished:

        return (
            "The conversation has ended, so please start a new chat if you need further help."
        )


    # =====================================================
    # COUNT USER TURN
    # =====================================================

    conversation_turns += 1

    print(
        f"Conversation turn: "
        f"{conversation_turns}/{MAX_CONVERSATION_TURNS}"
    )


    # =====================================================
    # SAVE PATIENT INFORMATION
    # =====================================================

    try:

        save_patient_data(text)

    except Exception as error:

        print(
            "Patient storage error:",
            error
        )


    # =====================================================
    # EXIT OFFER RESPONSE
    # =====================================================

    if exit_offer_pending:

        exit_response = handle_exit_response(text)

        if exit_response:

            add_to_history(
                "user",
                text
            )

            add_to_history(
                "assistant",
                exit_response
            )

            return exit_response


    # =====================================================
    # MEDICATION OFFER RESPONSE
    # =====================================================

    if medication_offer_pending:

        medication_response = handle_medication_response(text)

        if medication_response:

            add_to_history(
                "user",
                text
            )

            add_to_history(
                "assistant",
                medication_response
            )

            return medication_response


    # =====================================================
    # IF MEDICATION DISCUSSION IS ACTIVE
    # =====================================================

    if medication_discussion:

        # Allow the patient to continue asking questions.
        # The AI receives the medication-discussion instruction.

        pass


    # =====================================================
    # LONG CONVERSATION CHECK
    # =====================================================

    if (
        conversation_turns >= MAX_CONVERSATION_TURNS
        and not exit_offer_pending
        and not medication_offer_pending
    ):

        exit_offer_pending = True

        answer = (
            "We have discussed quite a bit, would you like to end the conversation?"
        )

        add_to_history(
            "user",
            text
        )

        add_to_history(
            "assistant",
            answer
        )

        return answer


    # =====================================================
    # MEDICATION OFFER
    # =====================================================

    if (
        assessment_complete
        and not medication_offer_pending
        and not medication_discussion
    ):

        medication_offer_pending = True

        answer = (
            "I have enough information about your symptoms, would you like general information about medication options?"
        )

        add_to_history(
            "user",
            text
        )

        add_to_history(
            "assistant",
            answer
        )

        return answer


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


            # ---------------------------------------------
            # QUESTION COUNT
            # ---------------------------------------------

            if response_is_question(answer):

                question_count += 1

                print(
                    f"Assessment question count: "
                    f"{question_count}/{MAX_QUESTIONS}"
                )


            # ---------------------------------------------
            # ASSESSMENT COMPLETE
            # ---------------------------------------------

            if question_count >= MAX_QUESTIONS:

                assessment_complete = True

                print(
                    "Assessment complete."
                )


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


            # ---------------------------------------------
            # QUESTION COUNT
            # ---------------------------------------------

            if response_is_question(answer):

                question_count += 1

                print(
                    f"Assessment question count: "
                    f"{question_count}/{MAX_QUESTIONS}"
                )


            # ---------------------------------------------
            # ASSESSMENT COMPLETE
            # ---------------------------------------------

            if question_count >= MAX_QUESTIONS:

                assessment_complete = True

                print(
                    "Assessment complete."
                )


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