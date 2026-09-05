document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =========================================
           GET ELEMENTS
        ========================================= */

        const liveSpeechButton =
            document.getElementById(
                "liveSpeechButton"
            );

        const liveSpeechOverlay =
            document.getElementById(
                "liveSpeechOverlay"
            );

        const closeLiveSpeech =
            document.getElementById(
                "closeLiveSpeech"
            );

        const stopLiveSpeech =
            document.getElementById(
                "stopLiveSpeech"
            );

        const liveTranscript =
            document.getElementById(
                "liveTranscript"
            );

        const messageInput =
            document.getElementById(
                "messageInput"
            );

        const chatForm =
            document.getElementById(
                "chatForm"
            );

        const messages =
            document.getElementById(
                "messages"
            );

        const welcomeMessage =
            document.getElementById(
                "welcomeMessage"
            );


        /* =========================================
           CHECK REQUIRED ELEMENTS
        ========================================= */

        if (!liveSpeechButton) {
            console.error(
                "liveSpeechButton not found"
            );
            return;
        }

        if (!liveSpeechOverlay) {
            console.error(
                "liveSpeechOverlay not found"
            );
            return;
        }

        if (!messageInput) {
            console.error(
                "messageInput not found"
            );
            return;
        }

        if (!chatForm) {
            console.error(
                "chatForm not found"
            );
            return;
        }

        if (!messages) {
            console.error(
                "messages not found"
            );
            return;
        }


        /* =========================================
           LIVE SPEECH VARIABLES
        ========================================= */

        let speechRecognition = null;

        let liveSpeechActive = false;

        let finalTranscript = "";

        let processingSpeech = false;


        let speechPauseTimer = null;


        /* =========================================
           BROWSER SPEECH RECOGNITION SUPPORT
        ========================================= */

        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;


        /* =========================================
           AI VOICE RESPONSE
        ========================================= */

        function speakAIResponse(text) {

            if (!text) {
                return;
            }


            if (
                !(
                    "speechSynthesis"
                    in window
                )
            ) {

                console.error(
                    "Speech synthesis is not supported."
                );

                return;
            }


            /*
             * Stop any previous AI speech
             */

            window.speechSynthesis.cancel();


            const speech =
                new SpeechSynthesisUtterance(
                    String(text)
                );


            speech.lang = "en-IN";

            speech.rate = 0.95;

            speech.pitch = 1;

            speech.volume = 1;


            console.log(
                "AI speaking:",
                text
            );


            window.speechSynthesis.speak(
                speech
            );

        }


        /* =========================================
           ADD MESSAGE TO CHAT
        ========================================= */

        function addMessage(
            text,
            type
        ) {

            const message =
                document.createElement(
                    "div"
                );


            if (type === "user") {

                message.className =
                    "message user-message";

            }

            else {

                message.className =
                    "message ai-message";

            }


            const messageContent =
                document.createElement(
                    "div"
                );

            messageContent.className =
                "message-content";


            const messageName =
                document.createElement(
                    "span"
                );

            messageName.className =
                "message-name";


            if (type === "user") {

                messageName.textContent =
                    "You";

            }

            else {

                messageName.textContent =
                    "MediKiosk AI";

            }


            const messageBubble =
                document.createElement(
                    "div"
                );

            messageBubble.className =
                "message-bubble";


            messageBubble.textContent =
                text;


            messageContent.appendChild(
                messageName
            );

            messageContent.appendChild(
                messageBubble
            );


            /*
             * Add AI avatar
             */

            if (type === "ai") {

                const avatar =
                    document.createElement(
                        "div"
                    );

                avatar.className =
                    "message-avatar";

                avatar.textContent =
                    "+";


                message.appendChild(
                    avatar
                );

            }


            message.appendChild(
                messageContent
            );


            messages.appendChild(
                message
            );


            /*
             * Scroll to latest message
             */

            messages.scrollTop =
                messages.scrollHeight;

        }


        /* =========================================
           LIVE SPEECH SETUP
        ========================================= */

        if (SpeechRecognition) {


            speechRecognition =
                new SpeechRecognition();


            speechRecognition.continuous =
                true;


            speechRecognition.interimResults =
                true;


            speechRecognition.lang =
                "en-IN";


            /* =====================================
               LIVE SPEECH BUTTON
            ===================================== */

            liveSpeechButton.addEventListener(
                "click",
                function () {

                    console.log(
                        "LIVE SPEECH BUTTON CLICKED"
                    );


                    /*
                     * Open live speech window
                     */

                    liveSpeechOverlay.style.display =
                        "flex";


                    liveSpeechButton.classList.add(
                        "active"
                    );


                    liveSpeechActive =
                        true;


                    finalTranscript =
                        "";


                    clearTimeout(
                        speechPauseTimer
                    );


                    liveTranscript.textContent =
                        "Listening...";


                    try {

                        speechRecognition.start();


                        console.log(
                            "Speech recognition started"
                        );

                    }

                    catch (error) {

                        console.log(
                            "Speech recognition already running."
                        );

                    }

                }
            );


            /* =====================================
               SPEECH START
            ===================================== */

            speechRecognition.onstart =
                function () {

                    console.log(
                        "Microphone listening started"
                    );


                    liveTranscript.textContent =
                        finalTranscript ||
                        "Listening...";

                };


            /* =====================================
               SPEECH RESULTS
            ===================================== */

            speechRecognition.onresult =
                function (event) {

                    let interimText =
                        "";


                    for (
                        let i =
                            event.resultIndex;

                        i <
                        event.results.length;

                        i++
                    ) {


                        const transcript =
                            event.results[i][0]
                                .transcript;


                        if (
                            event.results[i]
                                .isFinal
                        ) {

                            finalTranscript +=
                                transcript + " ";

                        }

                        else {

                            interimText +=
                                transcript;

                        }

                    }


                    const displayedText =
                        finalTranscript +
                        interimText;


                    if (
                        displayedText.trim()
                    ) {

                        liveTranscript.textContent =
                            displayedText;


                        console.log(
                            "Speech result:",
                            displayedText
                        );

                    }


                    /* =================================
                         DETECT USER STOPPING SPEECH
                    ================================= */

                    clearTimeout(speechPauseTimer);

                    speechPauseTimer = setTimeout(
                        function () {

                            if (
                                liveSpeechActive &&
                                finalTranscript.trim() &&
                                !processingSpeech
                            ) {

                                console.log(
                                    "User stopped speaking."
                                );

                                sendLiveSpeechToAI();

                            }

                        },

                        500
                    );

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

                    else if (
                        event.error ===
                        "no-speech"
                    ) {

                        liveTranscript.textContent =
                            "No speech detected. Please speak again.";

                    }

                    else if (
                        event.error ===
                        "audio-capture"
                    ) {

                        liveTranscript.textContent =
                            "Microphone could not be accessed.";

                    }

                };


            /* =====================================
               SPEECH ENDS
            ===================================== */

            speechRecognition.onend =
                function () {

                    console.log(
                        "Speech recognition ended"
                    );


                    /*
                     * Only restart if the user
                     * has NOT intentionally stopped.
                     */

                    if (
                        liveSpeechActive &&
                        !processingSpeech
                    ) {

                        try {

                            speechRecognition.start();


                            console.log(
                                "Speech recognition restarted"
                            );

                        }

                        catch (error) {

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
SEND LIVE SPEECH TO AI
========================================= */

        async function sendLiveSpeechToAI() {

            const spokenText =
                finalTranscript.trim();


            if (
                !spokenText ||
                processingSpeech ||
                !liveSpeechActive
            ) {

                return;

            }


            console.log(
                "Sending speech to AI..."
            );

            console.log(
                "Sending question:",
                spokenText
            );


            processingSpeech = true;


            /*
             * Stop current speech recognition
             * temporarily.
             */

            try {

                speechRecognition.stop();

            }

            catch (error) {

                console.log(
                    "Speech stop error:",
                    error
                );

            }


            /*
             * Clear transcript for the
             * next sentence.
             */

            finalTranscript = "";

            liveTranscript.textContent =
                "AI is thinking...";


            try {

                const csrfToken =
                    document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    );


                const response =
                    await fetch(
                        "/api/ai/chat/",
                        {
                            method: "POST",

                            headers: {

                                "X-CSRFToken":
                                    csrfToken.value,

                                "Content-Type":
                                    "application/x-www-form-urlencoded"

                            },

                            body:
                                new URLSearchParams({
                                    question:
                                        spokenText
                                })
                        }
                    );


                console.log(
                    "AI response status:",
                    response.status
                );


                const data =
                    await response.json();


                console.log(
                    "AI response:",
                    data
                );


                /* =================================
                   SHOW AI RESPONSE
                ================================= */

                if (data.answer) {

                    const aiMessage =
                        document.createElement(
                            "div"
                        );


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


                    messages.appendChild(
                        aiMessage
                    );


                    messages.scrollTop =
                        messages.scrollHeight;


                    /*
                     * Speak AI response.
                     */

                    console.log(
                        "AI speaking:",
                        data.answer
                    );


                    const utterance =
                        new SpeechSynthesisUtterance(
                            data.answer
                        );


                    utterance.lang =
                        "en-IN";


                    utterance.rate =
                        1;


                    utterance.volume =
                        1;


                    utterance.onend =
                        function () {

                            console.log(
                                "AI finished speaking."
                            );


                            processingSpeech = false;


                            if (
                                liveSpeechActive
                            ) {

                                liveTranscript.textContent =
                                    "Listening...";


                                try {

                                    speechRecognition.start();

                                    console.log(
                                        "Live Speech resumed."
                                    );

                                }

                                catch (error) {

                                    console.log(
                                        "Unable to resume speech."
                                    );

                                }

                            }

                        };


                    utterance.onerror =
                        function (error) {

                            console.error(
                                "Speech synthesis error:",
                                error
                            );


                            processingSpeech = false;


                            if (
                                liveSpeechActive
                            ) {

                                try {

                                    speechRecognition.start();

                                }

                                catch (error) {

                                    console.log(
                                        "Unable to resume speech."
                                    );

                                }

                            }

                        };


                    window.speechSynthesis.cancel();

                    window.speechSynthesis.speak(
                        utterance
                    );

                }

                else {

                    console.error(
                        "AI returned an error:",
                        data.error
                    );


                    processingSpeech = false;


                    if (
                        liveSpeechActive
                    ) {

                        liveTranscript.textContent =
                            "Listening...";


                        try {

                            speechRecognition.start();

                        }

                        catch (error) {

                            console.log(
                                "Unable to resume speech."
                            );

                        }

                    }

                }

            }

            catch (error) {

                console.error(
                    "AI request failed:",
                    error
                );


                processingSpeech = false;


                if (
                    liveSpeechActive
                ) {

                    liveTranscript.textContent =
                        "Connection error. Listening again...";


                    try {

                        speechRecognition.start();

                    }

                    catch (error) {

                        console.log(
                            "Unable to resume speech."
                        );

                    }

                }

            }

        }


        /* =========================================
           STOP LIVE SPEECH
        ========================================= */

        function stopLiveSpeechRecording() {

            console.log(
                "STOP LIVE SPEECH"
            );


            /*
             * Tell onend NOT to restart.
             */

            liveSpeechActive =
                false;


            /*
             * Cancel automatic silence timer.
             */

            clearTimeout(
                speechPauseTimer
            );


            /*
             * Stop browser speech recognition.
             */

            if (
                speechRecognition
            ) {

                try {

                    speechRecognition.stop();

                }

                catch (error) {

                    console.log(
                        "Speech stop error:",
                        error
                    );

                }

            }


            /*
             * Remove active button state.
             */

            liveSpeechButton.classList.remove(
                "active"
            );


            /*
             * Get final speech.
             */

            const spokenText =
                finalTranscript.trim();


            console.log(
                "FINAL SPEECH TEXT:",
                spokenText
            );


            /*
             * Close live speech window.
             */

            liveSpeechOverlay.style.display =
                "none";


            /*
             * Ignore empty speech.
             */

            if (!spokenText) {

                return;

            }


            /*
             * Put speech into input.
             */

            messageInput.value =
                spokenText;


            messageInput.style.height =
                "auto";


            messageInput.style.height =
                messageInput.scrollHeight +
                "px";


            /*
             * Automatically submit.
             */

            console.log(
                "Sending speech to AI..."
            );


            chatForm.requestSubmit();

        }


        /* =========================================
           STOP BUTTON
        ========================================= */

        if (stopLiveSpeech) {

            stopLiveSpeech.addEventListener(
                "click",
                stopLiveSpeechRecording
            );

        }


        /* =========================================
           CLOSE BUTTON
        ========================================= */

        if (closeLiveSpeech) {

            closeLiveSpeech.addEventListener(
                "click",
                stopLiveSpeechRecording
            );

        }


        /* =========================================
           AI CHAT FORM
        ========================================= */

        chatForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const question =
                    messageInput.value.trim();


                if (!question) {

                    return;

                }


                console.log(
                    "Sending question:",
                    question
                );


                /* =================================
                   SHOW PATIENT MESSAGE
                ================================= */

                addMessage(
                    question,
                    "user"
                );


                /* =================================
                   HIDE WELCOME MESSAGE
                ================================= */

                if (
                    welcomeMessage
                ) {

                    welcomeMessage.style.display =
                        "none";

                }


                /* =================================
                   CLEAR INPUT
                ================================= */

                messageInput.value =
                    "";

                messageInput.style.height =
                    "auto";


                /* =================================
                   GET CSRF TOKEN
                ================================= */

                const csrfToken =
                    document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    );


                if (!csrfToken) {

                    console.error(
                        "CSRF token not found."
                    );

                    addMessage(
                        "Security token not found. Please refresh the page and try again.",
                        "ai"
                    );

                    return;

                }


                /* =================================
                   SEND TO DJANGO
                ================================= */

                try {

                    const response =
                        await fetch(
                            "/api/ai/chat/",
                            {
                                method:
                                    "POST",

                                headers: {

                                    "X-CSRFToken":
                                        csrfToken.value,

                                    "Content-Type":
                                        "application/x-www-form-urlencoded"

                                },

                                body:
                                    new URLSearchParams(
                                        {
                                            question:
                                                question
                                        }
                                    )

                            }
                        );


                    console.log(
                        "AI response status:",
                        response.status
                    );


                    const data =
                        await response.json();


                    console.log(
                        "AI response:",
                        data
                    );


                    /* =================================
                       CHECK RESPONSE
                    ================================= */

                    if (
                        !response.ok
                    ) {

                        throw new Error(
                            data.error ||
                            "AI request failed."
                        );

                    }


                    /* =================================
                       SHOW AI RESPONSE
                    ================================= */

                    if (
                        data.answer
                    ) {


                        addMessage(
                            data.answer,
                            "ai"
                        );


                        /* =============================
                           SPEAK AI RESPONSE
                        ============================= */

                        speakAIResponse(
                            data.answer
                        );

                    }

                    else {

                        console.error(
                            "AI returned an error:",
                            data.error
                        );


                        addMessage(
                            "I'm sorry, I could not generate a response.",
                            "ai"
                        );

                    }

                }


                catch (error) {

                    console.error(
                        "AI chat error:",
                        error
                    );


                    addMessage(
                        "I'm having trouble responding right now. Please try again.",
                        "ai"
                    );

                }


                /* =================================
                   SCROLL TO LATEST MESSAGE
                ================================= */

                messages.scrollTop =
                    messages.scrollHeight;

            }
        );


    }
);