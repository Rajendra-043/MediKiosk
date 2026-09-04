import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


# -------------------------
# LOAD ENVIRONMENT
# -------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)


# -------------------------
# API KEY
# -------------------------

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Check your .env file."
    )


# -------------------------
# GEMINI CLIENT
# -------------------------

client = genai.Client(
    api_key=API_KEY,
    http_options={
        "timeout": 10000
    }
)

MODEL_NAME = "gemini-3.5-flash-lite"


# -------------------------
# MEDIKIOSK SYSTEM PROMPT
# -------------------------

SYSTEM_PROMPT = """
You are MediKiosk, an AI patient assistance system.

Your purpose is to help collect and organize basic information
from patients before they meet a healthcare professional.

You are NOT a doctor and must not claim to diagnose diseases.

Rules:

1. Ask short, clear questions.
2. Ask only one or two questions at a time.
3. Remember information the patient already provided.
4. Do not repeatedly ask for information you already know.
5. Ask relevant follow-up questions based on the symptoms.
6. Do not prescribe medication.
7. Do not provide a definitive diagnosis.
8. If symptoms could indicate an emergency, clearly advise
   the patient to seek immediate medical attention.
9. Keep responses concise because the responses may be spoken
   through a voice interface.
10. Be calm, respectful, and easy for a patient to understand.

The goal is patient information collection and assistance,
not medical diagnosis.
"""


# -------------------------
# CREATE CHAT SESSION
# -------------------------

def create_chat():
    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,
            max_output_tokens=150,
        ),
    )


chat = create_chat()


def reset_chat():
    global chat
    chat = create_chat()

# -------------------------
# ASK AI
# -------------------------

def ask_ai(question):
    response = chat.send_message(question)

    return response.text.strip()