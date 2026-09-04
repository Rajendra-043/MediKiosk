"""
MediKiosk Voice Services

Microphone     -> SpeechRecognition
Whisper        -> Speech to Text
Ollama/Gemini  -> AI response
pyttsx3        -> Text to Speech

Designed for continuous voice conversation.
"""

import time
import numpy as np
import speech_recognition as sr
import pyttsx3

from faster_whisper import WhisperModel
from ai.services import ask_ai


# =========================================================
# SETTINGS
# =========================================================

PHRASE_TIME_LIMIT = 10
LISTEN_TIMEOUT = 5

ENERGY_THRESHOLD = 180
PAUSE_THRESHOLD = 0.8
NON_SPEAKING_DURATION = 0.3

TTS_RATE = 175
TTS_VOLUME = 1.0

WHISPER_MODEL = "base"


# =========================================================
# WHISPER
# =========================================================

print("Loading Whisper STT...")

whisper_model = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8"
)

print("Whisper ready.")


# =========================================================
# SPEECH RECOGNITION
# =========================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = ENERGY_THRESHOLD
recognizer.dynamic_energy_threshold = False

recognizer.pause_threshold = PAUSE_THRESHOLD
recognizer.non_speaking_duration = NON_SPEAKING_DURATION


# =========================================================
# MICROPHONE CALIBRATION
# =========================================================

def calibrate_microphone():

    print("\nCalibrating microphone...")
    print("Please remain quiet for 1 second.")

    try:

        with sr.Microphone() as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

        print(
            f"Microphone calibrated. "
            f"Energy threshold: {recognizer.energy_threshold:.0f}"
        )

        return True

    except Exception as error:

        print(
            "Microphone calibration error:",
            error
        )

        return False


# =========================================================
# TEXT TO SPEECH
# =========================================================

def speak(text):

    if not text:
        return

    print("AI speaking...")

    engine = None

    try:

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            TTS_RATE
        )

        engine.setProperty(
            "volume",
            TTS_VOLUME
        )

        engine.say(str(text))

        engine.runAndWait()

    except Exception as error:

        print(
            "TTS error:",
            error
        )

    finally:

        if engine is not None:

            try:
                engine.stop()
            except Exception:
                pass

            del engine


# =========================================================
# SPEECH TO TEXT
# =========================================================

def listen_for_speech():

    print("\nListening...")
    print("Ready for patient input.")

    start_time = time.time()

    try:

        with sr.Microphone() as source:

            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )

    except sr.WaitTimeoutError:

        print("No speech detected.")

        return None

    except KeyboardInterrupt:

        print("\nListening stopped.")

        return None

    except Exception as error:

        print(
            "Microphone error:",
            error
        )

        return None


    recording_time = time.time() - start_time

    print(
        f"Recording time: {recording_time:.2f}s"
    )


    # =====================================================
    # CONVERT AUDIO
    # =====================================================

    try:

        raw_audio = audio.get_raw_data(
            convert_rate=16000,
            convert_width=2
        )

        audio_array = (
            np.frombuffer(
                raw_audio,
                dtype=np.int16
            )
            .astype(np.float32)
            / 32768.0
        )

    except Exception as error:

        print(
            "Audio conversion error:",
            error
        )

        return None


    # =====================================================
    # WHISPER STT
    # =====================================================

    try:

        print("Transcribing...")

        stt_start = time.time()

        segments, info = whisper_model.transcribe(
            audio_array,
            beam_size=1,
            best_of=1,
            temperature=0,
            vad_filter=True
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        stt_time = time.time() - stt_start

        print(
            f"Whisper STT time: {stt_time:.2f}s"
        )

    except Exception as error:

        print(
            "Whisper STT error:",
            error
        )

        return None


    # =====================================================
    # EMPTY RESULT
    # =====================================================

    if not text:

        print(
            "I could not understand the audio."
        )

        return None


    print(
        "You:",
        text
    )

    if hasattr(info, "language"):

        print(
            f"Detected language: {info.language}"
        )

    return text


# =========================================================
# MAIN VOICE LOOP
# =========================================================

def listen_and_ask():

    print(
        """
=================================
       MediKiosk Voice Mode
=================================
"""
    )


    # =====================================================
    # CALIBRATE MICROPHONE
    # =====================================================

    if not calibrate_microphone():

        print(
            "Unable to initialize microphone."
        )

        return


    # =====================================================
    # CONVERSATION LOOP
    # =====================================================

    while True:

        text = listen_for_speech()

        if not text:

            continue


        # =================================================
        # EXIT COMMAND
        # =================================================

        command = text.lower().strip()

        exit_commands = {
            "exit",
            "quit",
            "stop",
            "goodbye",
            "end session"
        }

        if command in exit_commands:

            speak(
                "Thank you. "
                "Your session has ended. "
                "Goodbye."
            )

            print(
                "\nConversation ended."
            )

            break


        # =================================================
        # AI PROCESSING
        # =================================================

        print("\nAI processing...")

        ai_start = time.time()

        try:

            answer = ask_ai(text)

        except Exception as error:

            print(
                "AI error:",
                error
            )

            answer = (
                "I'm sorry, I'm having trouble "
                "responding right now. "
                "Could you please repeat that?"
            )


        ai_time = time.time() - ai_start

        print(
            f"AI time: {ai_time:.2f}s"
        )

        print(
            "AI:",
            answer
        )


        # =================================================
        # SPEAK AI RESPONSE
        # =================================================

        speak(answer)

        print(
            "\nReady for patient input."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    listen_and_ask()