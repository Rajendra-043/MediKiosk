"""
MediKiosk Voice Services

Whisper       -> Speech to Text
Ollama/Gemini -> AI response
pyttsx3       -> Text to Speech

Designed for continuous voice conversation.
"""

import time
import speech_recognition as sr
import pyttsx3

from faster_whisper import WhisperModel
from ai.services import ask_ai


# =========================================================
# SETTINGS
# =========================================================

PHRASE_TIME_LIMIT = 5
LISTEN_TIMEOUT = 3

ENERGY_THRESHOLD = 180
PAUSE_THRESHOLD = 0.5

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
recognizer.dynamic_energy_threshold = True

recognizer.pause_threshold = PAUSE_THRESHOLD
recognizer.non_speaking_duration = 0.3


# =========================================================
# TTS
# =========================================================

def speak(text):

    if not text:
        return

    print("AI speaking...")

    try:

        # Create a NEW engine every time.
        # This prevents pyttsx3 from getting stuck
        # after the first response.

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            TTS_RATE
        )

        engine.setProperty(
            "volume",
            TTS_VOLUME
        )

        engine.say(text)

        engine.runAndWait()

        engine.stop()

        del engine

    except Exception as error:

        print(
            "TTS error:",
            error
        )


# =========================================================
# LISTEN
# =========================================================

def listen_for_speech():

    print("\nListening...")
    print("Ready...")

    start_time = time.time()

    try:

        with sr.Microphone() as source:

            try:

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
    # WHISPER STT
    # =====================================================

    try:

        stt_start = time.time()

        # SpeechRecognition AudioData
        # -> raw PCM bytes
        # -> Whisper accepts numpy/audio data

        import numpy as np

        raw_audio = audio.get_raw_data(
            convert_rate=16000,
            convert_width=2
        )

        audio_array = np.frombuffer(
            raw_audio,
            dtype=np.int16
        ).astype(np.float32) / 32768.0


        segments, info = whisper_model.transcribe(
            audio_array,
            language="en",
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


        if not text:

            print(
                "I could not understand the audio."
            )

            return None


        print(
            "You:",
            text
        )

        return text


    except Exception as error:

        print(
            "Whisper STT error:",
            error
        )

        return None


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

    while True:

        # =================================================
        # LISTEN
        # =================================================

        text = listen_for_speech()

        if not text:
            continue


        # =================================================
        # EXIT
        # =================================================

        command = text.lower().strip()

        if command in [
            "exit",
            "quit",
            "stop",
            "goodbye",
            "end session"
        ]:

            speak(
                "Thank you. Your session has ended. Goodbye."
            )

            print(
                "\nConversation ended."
            )

            break


        # =================================================
        # AI
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
        # SPEAK
        # =================================================

        speak(answer)


        print(
            "Ready for patient input."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    listen_and_ask()