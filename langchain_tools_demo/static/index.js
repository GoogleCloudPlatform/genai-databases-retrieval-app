// Submit chat message
$('.btn-group span').click(async (e) => {
    let msg = $('.chat-bar input').val();
    // Add message to UI
    log("user", msg)
    // Clear message
    $('.chat-bar input').val('');
    try {
        // Prompt LLM
        let answer = await askQuestion(msg);
        // Add response to UI
        log("assistant", answer)
    } catch (err) {
        window.alert(`Error when submitting question: ${err}`);
    }
});

// Send request to backend
async function askQuestion(prompt) {
    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt }),
    });
    if (response.ok) {
        const text = await response.text();
        console.log(text)
        return text
    } else {
        console.error(await response.text())
        return "Sorry, we couldn't answer your question 😢"
    }
}

// Helper function to print to chatroom
function log(name, msg) {
    let message = `<span class="chat-bubble ${name}">${msg}</span>`;
    $('.chat-content').append(message);
    window.scrollTo(0, document.body.scrollHeight);
}
