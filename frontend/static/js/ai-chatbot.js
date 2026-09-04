/* =========================================
   LIVE SPEECH
========================================= */

let speechRecognition = null;

let liveSpeechActive = false;


/*
 * Check browser support
 */

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


if (SpeechRecognition) {

    speechRecognition =
        new SpeechRecognition();


    speechRecognition.continuous = true;

    speechRecognition.interimResults = true;

    speechRecognition.lang = "en-IN";


    /* =====================================
       START LIVE SPEECH
    ===================================== */

    liveSpeechButton.addEventListener(
        "click",
        function () {

            liveSpeechOverlay.style.display =
                "flex";

            liveSpeechButton.classList.add(
                "active"
            );

            liveSpeechActive = true;

            liveTranscript.textContent =
                "Listening...";


            try {

                speechRecognition.start();

            }

            catch (error) {

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


                if (
                    event.results[i].isFinal
                ) {

                    finalText +=
                        transcript + " ";

                }

                else {

                    interimText +=
                        transcript;

                }

            }


            if (
                finalText ||
                interimText
            ) {

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

            if (
                event.error ===
                "not-allowed"
            ) {

                liveTranscript.textContent =
                    "Microphone permission was denied.";

            }

        };


    /* =====================================
       SPEECH ENDS
    ===================================== */

    speechRecognition.onend =
        function () {

            /*
             * Automatically restart while
             * Live Speech is active.
             */

            if (liveSpeechActive) {

                try {

                    speechRecognition.start();

                }

                catch (error) {

                    console.log(
                        "Unable to restart speech."
                    );

                }

            }

        };

}
else {

    /*
     * Browser does not support
     * Speech Recognition.
     */

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

        }

        catch (error) {

            console.log(error);

        }

    }


    liveSpeechButton.classList.remove(
        "active"
    );


    /*
     * Put recognized speech into
     * the normal chat input.
     */

    const spokenText =
        liveTranscript.textContent;


    if (
        spokenText &&
        spokenText !== "Listening..."
    ) {

        messageInput.value =
            spokenText.trim();


        messageInput.style.height =
            "auto";


        messageInput.style.height =
            messageInput.scrollHeight +
            "px";

    }


    liveSpeechOverlay.style.display =
        "none";

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