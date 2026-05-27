const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChat");
const sampleButtons = document.querySelectorAll(".sample-question");

let chatHistory = JSON.parse(localStorage.getItem("tnea_chat_history")) || [];

function saveHistory() {
    localStorage.setItem("tnea_chat_history", JSON.stringify(chatHistory));
}

function appendMessage(sender, text, save = true) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");

    if (sender === "user") {
        messageDiv.classList.add("user-message");
    } else {
        messageDiv.classList.add("bot-message");
    }

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = sender === "user" ? "👩‍🎓" : "🤖";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.innerText = text;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (save) {
        chatHistory.push({ sender, text });
        saveHistory();
    }
}

function showTyping() {
    const typingDiv = document.createElement("div");
    typingDiv.classList.add("message", "bot-message");
    typingDiv.id = "typingIndicator";

    typingDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typingIndicator");
    if (typing) {
        typing.remove();
    }
}

async function sendMessage() {
    const question = userInput.value.trim();

    if (!question) return;

    appendMessage("user", question);

    userInput.value = "";
    userInput.style.height = "auto";

    sendBtn.disabled = true;
    showTyping();

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        removeTyping();

        if (data.success) {
            appendMessage("bot", data.answer);
        } else {
            appendMessage("bot", data.answer || "Sorry, something went wrong.");
        }

    } catch (error) {
        removeTyping();
        appendMessage("bot", "Backend is not connected. Please check Flask server.");
    }

    sendBtn.disabled = false;
    userInput.focus();
}

function loadHistory() {
    if (chatHistory.length === 0) return;

    chatHistory.forEach(item => {
        appendMessage(item.sender, item.text, false);
    });
}

sendBtn.addEventListener("click", sendMessage);

userInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

userInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = this.scrollHeight + "px";
});

clearChatBtn.addEventListener("click", function () {
    const confirmClear = confirm("Do you want to clear chat history?");

    if (confirmClear) {
        localStorage.removeItem("tnea_chat_history");
        chatHistory = [];

        chatBox.innerHTML = `
            <div class="message bot-message">
                <div class="avatar">🤖</div>
                <div class="bubble">
                    <strong>Hello!</strong><br>
                    I am your TNEA counselling assistant. Ask me about cutoff prediction, college details, branches, eligibility, reservation, or counselling process.
                </div>
            </div>
        `;
    }
});

sampleButtons.forEach(button => {
    button.addEventListener("click", function () {
        userInput.value = this.innerText;
        userInput.focus();
    });
});

loadHistory();