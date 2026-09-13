document.addEventListener("DOMContentLoaded", function () {
    console.log("Patient medical history loaded.");

    const aiButton = document.getElementById("aiButton");
    if (aiButton) {
        aiButton.addEventListener("click", function () {
            const patientId = window.location.pathname.split("/").filter(Boolean).pop();
            askAIAboutPatient(patientId);
        });
    }
});

function askAIAboutPatient(patientId) {
    const query = prompt("Enter your medical question about this patient:");
    if (!query || !query.trim()) {
        return;
    }

    const aiButton = document.getElementById("aiButton");
    const originalText = aiButton.textContent;
    aiButton.disabled = true;
    aiButton.textContent = "⏳ Thinking...";

    fetch(`/api/doctor/ask-ai/${patientId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ query: query.trim() }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                showAIResponse(data.reply);
            } else {
                alert("Error: " + (data.error || "Unknown error"));
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("Failed to get AI response. Please try again.");
        })
        .finally(() => {
            aiButton.disabled = false;
            aiButton.textContent = originalText;
        });
}

function showAIResponse(response) {
    const modal = document.createElement("div");
    modal.className = "ai-modal";
    modal.innerHTML = `
        <div class="ai-modal-content">
            <div class="ai-modal-header">
                <h3>✨ AI Medical Assistant</h3>
                <button class="ai-modal-close">&times;</button>
            </div>
            <div class="ai-modal-body">
                <pre>${escapeHtml(response)}</pre>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector(".ai-modal-close").addEventListener("click", () => {
        modal.remove();
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}