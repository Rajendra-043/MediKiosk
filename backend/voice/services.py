import os
import time

import sounddevice as sd
import speech_recognition as sr
import pyttsx3
from google import genai


# =========================================================
# AUDIO SETTINGS
# =========================================================

SAMPLE_RATE = 16000
CHANNELS = 1

# Your tested microphone
MIC_DEVICE = 1

# Maximum recording duration
MAX_RECORDING_TIME = 5

# Silence required after speech
SILENCE_DURATION = 0.45

# Microphone sensitivity
ENERGY_THRESHOLD = 350


# =========================================================
# GEMINI
# =========================================================

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Set your Gemini API key before running the program."
    )

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.6-flash"


SYSTEM_PROMPT = """
You are MediKiosk, a voice assistant in a healthcare clinic.

Your job is to collect basic information from the patient before
they see a healthcare professional.

Rules:
- Speak naturally and clearly.
- Keep responses short, usually 1 or 2 sentences.
- Ask one useful question at a time.
- Do not diagnose diseases.
- Do not prescribe medication.
- Gather symptoms, duration, severity, and other basic information.
- If the patient gives incomplete information, politely ask them
  to continue.
- Your response will be spoken aloud, so use plain sentences.
"""


# =========================================================
# CONVERSATION MEMORY
# =========================================================

conversation = []


def reset_conversation():
    conversation.clear()


# =========================================================
# TEXT TO SPEECH
# =========================================================

class SpeechEngine:

    def __init__(self):

        self.engine = pyttsx3.init()

        self.engine.setProperty(
            "rate",
            190
        )

    def speak(self, text):

        try:

            self.engine.say(text)

            self.engine.runAndWait()

        except Exception as error:

            print(
                "TTS error:",
                error
            )


speech_engine = SpeechEngine()


# =========================================================
# AUDIO LEVEL
# =========================================================

def audio_is_loud(data):

    if data.size == 0:
        return False

    level = abs(data).mean()

    return level > ENERGY_THRESHOLD


# =========================================================
# LISTEN AND RECORD PATIENT
# =========================================================

def listen_for_speech():

    print("\nListening...")

    recognizer = sr.Recognizer()

    audio_chunks = []

    started_speaking = False

    silence_start = None

    start_time = time.time()

    block_duration = 0.1

    block_size = int(
        SAMPLE_RATE * block_duration
    )

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=MIC_DEVICE,
            blocksize=block_size
        ) as stream:

            while True:

                data, overflowed = stream.read(
                    block_size
                )

                data = data.copy()

                audio_chunks.append(data)

                speaking = audio_is_loud(data)

                # -------------------------------
                # SPEECH STARTED
                # -------------------------------

                if speaking:

                    if not started_speaking:

                        print(
                            "Speech detected..."
                        )

                    started_speaking = True

                    silence_start = None

                # -------------------------------
                # SPEECH ENDED
                # -------------------------------

                elif started_speaking:

                    if silence_start is None:

                        silence_start = time.time()

                    elif (
                        time.time() - silence_start
                        >= SILENCE_DURATION
                    ):

                        print(
                            "Speech ended."
                        )

                        break

                # -------------------------------
                # MAX TIME
                # -------------------------------

                if (
                    time.time() - start_time
                    >= MAX_RECORDING_TIME
                ):

                    print(
                        "Maximum recording time reached."
                    )

                    break

    except KeyboardInterrupt:

        print(
            "\nListening stopped."
        )

        return None

    except Exception as error:

        print(
            "Microphone error:",
            error
        )

        return None

    # =====================================================
    # NO SPEECH
    # =====================================================

    if not started_speaking:

        print(
            "No speech detected."
        )

        return None

    # =====================================================
    # COMBINE AUDIO
    # =====================================================

    import numpy as np

    recording = np.concatenate(
        audio_chunks,
        axis=0
    )

    audio = sr.AudioData(
        recording.tobytes(),
        SAMPLE_RATE,
        2
    )

    # =====================================================
    # GOOGLE SPEECH TO TEXT
    # =====================================================

    try:

        start = time.time()

        text = recognizer.recognize_google(
            audio
        )

        print(
            f"STT time: "
            f"{time.time() - start:.2f} seconds"
        )

        return text.strip()

    except sr.UnknownValueError:

        print(
            "I could not understand the audio."
        )

        return None

    except sr.RequestError as error:

        print(
            "Speech recognition error:",
            error
        )

        return None


# =========================================================
# GEMINI AI
# =========================================================

def ask_ai(patient_text):

    conversation.append(
        {
            "role": "user",
            "content": patient_text
        }
    )

    # Keep conversation small
    if len(conversation) > 12:

        del conversation[:-12]

    prompt = SYSTEM_PROMPT + "\n\n"

    for message in conversation:

        prompt += (
            message["role"]
            + ": "
            + message["content"]
            + "\n"
        )

    prompt += "\nassistant:"

    try:

        start = time.time()

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        print(
            f"AI time: "
            f"{time.time() - start:.2f} seconds"
        )

        answer = response.text.strip()

        conversation.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer

    except Exception as error:

        print(
            "AI error:",
            error
        )

        return (
            "I'm sorry, I had trouble "
            "understanding that. Could you "
            "please repeat it?"
        )


# =========================================================
# MAIN VOICE LOOP
# =========================================================

def listen_and_ask():

    print(
        "\n================================="
    )

    print(
        "       MediKiosk Voice Mode"
    )

    print(
        "================================="
    )

    reset_conversation()

    while True:

        # -----------------------------------------
        # PATIENT SPEAKS
        # -----------------------------------------

        start = time.time()

        text = listen_for_speech()

        print(
            f"Recording/STT total: "
            f"{time.time() - start:.2f} seconds"
        )

        if not text:

            continue

        print(
            "You:",
            text
        )

        # -----------------------------------------
        # STOP COMMAND
        # -----------------------------------------

        if text.lower().strip() in [
            "stop",
            "exit",
            "quit"
        ]:

            print(
                "Conversation ended."
            )

            break

        # -----------------------------------------
        # GEMINI
        # -----------------------------------------

        answer = ask_ai(text)

        print(
            "AI:",
            answer
        )

        # -----------------------------------------
        # SPEAK AI RESPONSE
        # -----------------------------------------

        print(
            "AI speaking..."
        )

        speech_engine.speak(
            answer
        )

        print(
            "Ready for patient input."
        )