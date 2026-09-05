/* =========================================
   LIVE SPEECH
========================================= */

let speechRecognition = null;
let liveSpeechActive = false;


/* =========================================
   GET ELEMENTS
========================================= */

const liveSpeechButton =
    document.getElementById("liveSpeechButton");

const liveSpeechOverlay =
    document.getElementById("liveSpeechOverlay");

const closeLiveSpeech =
    document.getElementById("closeLiveSpeech");

const stopLiveSpeech =
    document.getElementById("stopLiveSpeech");

const liveTranscript =
    document.getElementById("liveTranscript");

const messageInput =
    document.getElementById("messageInput");


/* =========================================
   BROWSER SUPPORT
========================================= */

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


/* =========================================
   START LIVE SPEECH
========================================= */

if (SpeechRecognition) {

    speechRecognition =
        new SpeechRecognition();

    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = "en-IN";


    liveSpeechButton.addEventListener(
        "click",
        function () {

            liveSpeechOverlay.style.display = "flex";

            liveSpeechButton.classList.add("active");

            liveSpeechActive = true;

            liveTranscript.textContent =
                "Listening...";


            try {

                speechRecognition.start();

            } catch (error) {

                console.log(
                    "Speech recognition already running."
                );

            }

        }
    );


    /* =====================================
       SPEECH RESULTS
    ===================================== */

    speechRecognition.onresult =
        function (event) {

            let finalText = "";
            let interimText = "";


            for (
                let i = event.resultIndex;
                i < event.results.length;
                i++
            ) {

                const transcript =
                    event.results[i][0].transcript;


                if (event.results[i].isFinal) {

                    finalText +=
                        transcript + " ";

                } else {

                    interimText += transcript;

                }

            }


            if (finalText || interimText) {

                liveTranscript.textContent =
                    finalText + interimText;

            }

        };


    /* =====================================
       SPEECH ERROR
    ===================================== */

    speechRecognition.onerror =
        function (event) {

            console.error(
                "Speech recognition error:",
                event.error
            );


            if (event.error === "not-allowed") {

                liveTranscript.textContent =
                    "Microphone permission was denied.";

            }

            else if (event.error === "no-speech") {

                liveTranscript.textContent =
                    "No speech detected. Please speak again.";

            }

        };


    /* =====================================
       SPEECH ENDS
    ===================================== */

    speechRecognition.onend =
        function () {

            if (liveSpeechActive) {

                try {

                    speechRecognition.start();

                } catch (error) {

                    console.log(
                        "Unable to restart speech."
                    );

                }

            }

        };

}


/* =========================================
   BROWSER NOT SUPPORTED
========================================= */

else {

    liveSpeechButton.addEventListener(
        "click",
        function () {

            alert(
                "Live Speech is not supported in this browser. Please use Google Chrome or Microsoft Edge."
            );

        }
    );

}


/* =========================================
   STOP LIVE SPEECH
========================================= */
function stopLiveSpeechRecording() {

    liveSpeechActive = false;

    if (speechRecognition) {
        try {
            speechRecognition.stop();
        } catch (error) {
            console.log("Speech stop error:", error);
        }
    }

    liveSpeechButton.classList.remove("active");

    const spokenText =
        liveTranscript.textContent.trim();

    /* Close the Live Speech window */
    liveSpeechOverlay.style.display = "none";

    /* Ignore empty or error messages */
    if (
        !spokenText ||
        spokenText === "Listening..." ||
        spokenText.includes("Microphone permission was denied") ||
        spokenText.includes("No speech detected")
    ) {
        return;
    }

    /* Put speech text into chat input */
    messageInput.value = spokenText;

    messageInput.style.height = "auto";
    messageInput.style.height =
        messageInput.scrollHeight + "px";

    /* Automatically send to AI */
    chatForm.requestSubmit();
}


/* =========================================
   STOP BUTTON
========================================= */

stopLiveSpeech.addEventListener(
    "click",
    stopLiveSpeechRecording
);


/* =========================================
   CLOSE BUTTON
========================================= */

closeLiveSpeech.addEventListener(
    "click",
    stopLiveSpeechRecording
);

/* =========================================
   AI CHAT FORM
========================================= */

const chatForm = document.getElementById("chatForm");
const messages = document.getElementById("messages");
const welcomeMessage = document.getElementById("welcomeMessage");


chatForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const question = messageInput.value.trim();

    if (!question) {
        return;
    }


    /* =====================================
       SHOW PATIENT MESSAGE
    ===================================== */

    const patientMessage = document.createElement("div");

    patientMessage.className =
        "message user-message";

    patientMessage.innerHTML = `
        <div class="message-content">
            <span class="message-name">
                You
            </span>

            <div class="message-bubble">
                ${question}
            </div>
        </div>
    `;

    messages.appendChild(patientMessage);


    /* Hide welcome message */

    if (welcomeMessage) {
        welcomeMessage.style.display = "none";
    }


    /* Clear input */

    messageInput.value = "";

    messageInput.style.height = "auto";


    /* =====================================
       SEND TO DJANGO
    ===================================== */

    try {

        const response = await fetch(
            "/api/ai/chat/",
            {
                method: "POST",

                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },

                body: new URLSearchParams({
                    question: question
                })
            }
        );


        const data = await response.json();


        /* =================================
           SHOW AI RESPONSE
        ================================= */

        if (data.answer) {

            const aiMessage =
                document.createElement("div");

            aiMessage.className =
                "message ai-message";

            aiMessage.innerHTML = `
                <div class="message-avatar">
                    +
                </div>

                <div class="message-content">

                    <span class="message-name">
                        MediKiosk AI
                    </span>

                    <div class="message-bubble">
                        ${data.answer}
                    </div>

                </div>
            `;

            messages.appendChild(aiMessage);

        }

        else {

            console.error(
                "AI error:",
                data.error
            );

        }


    } catch (error) {

        console.error(
            "Connection error:",
            error
        );

    }


    /* Scroll to latest message */

    messages.scrollTop =
        messages.scrollHeight;

});

