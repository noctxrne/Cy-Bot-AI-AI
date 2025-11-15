async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<div class='message user'><span>🧑 ${message}</span></div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    const response = await fetch("/get_response", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message})
    });

    const data = await response.json();
    setTimeout(() => {
        chatBox.innerHTML += `<div class='message bot'><span>🤖 ${data.bot}</span></div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 300);
}