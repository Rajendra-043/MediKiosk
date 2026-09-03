import sounddevice as sd
import speech_recognition as sr
import pyttsx3
import time

from ai.services import ask_ai


def listen_and_ask():
    recognizer = sr.Recognizer()

    while True:
        print("\nSpeak...")

        # -------------------------
        # RECORDING
        # -------------------------

        start = time.time()

        duration = 5
        sample_rate = 16000

        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        print(
            f"Recording time: "
            f"{time.time() - start:.2f} seconds"
        )

        audio = sr.AudioData(
            recording.tobytes(),
            sample_rate,
            2
        )

        try:
            # -------------------------
            # STT
            # -------------------------

            start = time.time()

            text = recognizer.recognize_google(audio)

            print(
                f"STT time: "
                f"{time.time() - start:.2f} seconds"
            )

            print("You:", text)

            # -------------------------
            # STOP COMMAND
            # -------------------------

            if text.lower().strip() in [
                "stop",
                "exit",
                "quit"
            ]:
                print("Conversation ended.")
                break

            # -------------------------
            # AI
            # -------------------------

            start = time.time()

            answer = ask_ai(text)

            print(
                f"AI time: "
                f"{time.time() - start:.2f} seconds"
            )

            print("AI:", answer)

            # -------------------------
            # TTS
            # -------------------------

            start = time.time()

            speak_text(answer)

            print(
                f"TTS time: "
                f"{time.time() - start:.2f} seconds"
            )

        except sr.UnknownValueError:
            print("I could not understand the audio.")

        except sr.RequestError as error:
            print(
                "Speech recognition error:",
                error
            )


def speak_text(text):
    engine = pyttsx3.init()

    engine.setProperty("rate", 220)

    engine.say(text)
    engine.runAndWait()