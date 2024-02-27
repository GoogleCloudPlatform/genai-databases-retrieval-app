/**
 * Copyright 2023 Google, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the `License`);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an `AS IS` BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Submit chat message via click
$('.btn-group span').click(async (e) => {
    await submitMessage();
});

// Submit chat message via enter
$(document).on("keypress",async (e) => {
    if (e.which == 13) {
        await submitMessage();
    }
});

// Reset current user via click
$('#resetButton').click(async (e) => {
    await reset();
});

async function submitMessage() {
    let msg = $('.chat-bar input').val();
    // Add message to UI
    log("human", msg)
    // Clear message
    $('.chat-bar input').val('');
    $('.mdl-progress').show()
    try {
        // Prompt LLM
        let answer = await askQuestion(msg);
        $('.mdl-progress').hide();
        // Add response to UI
        log("ai", answer)
    } catch (err) {
        window.alert(`Error when submitting question: ${err}`);
    }
}

// Send request to backend
async function askQuestion(prompt) {
    const response = await fetch('chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt }),
    });
    if (response.ok) {
        const text = await response.text();
        return text
    } else {
        console.error(await response.text())
        return "Sorry, we couldn't answer your question 😢"
    }
}

async function reset() {
    await fetch('reset', {
        method: 'POST',
    }).then(()=>{
        window.location.reload()
    })
}

// Helper function to print to chatroom
function log(name, msg) {
    let message = `<div class="chat-bubble ${name}">
        <div class="sender-icon"><img src="static/logo.png"></div>
        <span>${msg}</span></div>`;
    $('.chat-content').append(message);
    $('.chat-content').scrollTop($('.chat-content').prop("scrollHeight"));
}
