document.addEventListener("DOMContentLoaded", function () {

    const generateButton =
        document.getElementById("generateSummary");


    if (!generateButton) {
        return;
    }


    generateButton.addEventListener(
        "click",
        function () {

            generateButton.disabled = true;

            generateButton.textContent =
                "Generating Summary...";


            /*
             * AI generation will be connected
             * to the Django backend here.
             *
             * Do NOT put the OpenAI/API key
             * inside this JavaScript file.
             */

        }
    );

});