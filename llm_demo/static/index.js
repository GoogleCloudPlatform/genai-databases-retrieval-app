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

confirmations = {}

// Submit chat message via click
$('.btn-group span').click(async (e) => {
    await submitMessage();
});

// Submit chat message via enter
$(document).on("keypress", async (e) => {
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
    logMessage("human", msg)
    // Clear message
    $('.chat-bar input').val('');
    window.setTimeout(()=>{$('#loader-container').show()},400);
    try {
        // Prompt LLM
        let answer = await askQuestion(msg);
        $('#loader-container').hide();
        // Add response to UI
        if (answer.type === "message") {
            logMessage("ai", answer.content)
        } else if (answer.type === "confirmation") {
            messageId = generateRandomID(10);
            buildConfirmation(answer.content, messageId)
        }
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
        const text_response = await response.text();
        return JSON.parse(text_response)
    } else {
        console.error(await response.text())
        return { type: "message", content: "Sorry, we couldn't answer your question 😢" }
    }
}

async function reset() {
    await fetch('reset', {
        method: 'POST',
    }).then(() => {
        window.location.reload()
    })
}

async function signout() {
    await fetch('logout/google', {
        method: 'POST',
    }).then(() => {
        window.location.reload()
    })
}

function buildMessage(name, msg) {
    let message = `<div class="chat-bubble ${name}">
    <div class="sender-icon"><img src="static/logo.png"></div>
    <span>${msg}</span></div>`;
    return message;
}

// Helper function to print to chatroom
function logMessage(name, msg) {
    let message = buildMessage(name, msg);
    $('.inner-content').append(message);
    $('.chat-content').scrollTop($('.chat-content').prop("scrollHeight"));
}

function buildConfirmation(confirmation, messageId) {
    if (confirmation.tool === "Insert Ticket") {
        params = confirmation.params;
        confirmations[messageId] = params
        from = params.departure_airport;
        to = params.arrival_airport;
        flight = `${params.airline} ${params.flight_number}`;
        airline = params.airline;
        flight_number = params.flight_number;
        departure_time = params.departure_time;
        arrival_time = params.arrival_time;
        userName = $('#user-name').first().text();
        let message = `<div class="chat-bubble ai" id="${messageId}">
        <div class="sender-icon"><img src="static/logo.png"></div>
        <div class="ticket-confirmation">
            Please confirm the details below to complete your booking
            <div class="ticket-header"></div>
            <div class="ticket">
                <div class="from">${from}</div>
                <div class="material-symbols-outlined plane">travel</div>
                <div class="to">${to}</div>
            </div>
            ${buildBox('left', 133, 35, 15, "Departure", departure_time.replace('T', ' '))}
            ${buildBox('right', 133, 35, 15, "Arrival", arrival_time.replace('T', ' '))}
            ${buildBox('left', 205, 35, 15, "Flight", flight)}
            ${buildBox('left', 265, 35, 15, "Passenger", userName, "")}
            ${buildButton("Looks good to me. Book it!", 342, "#FFF", "#1b980f", "confirmTicket('" + messageId + "')")}
            ${buildButton("I changed my mind.", 395, "#FFF", "#181a23", "cancelTicket('" + messageId + "')")}
        </div></div>`;
        $('.inner-content').append(message);
        $('.chat-content').scrollTop($('.chat-content').prop("scrollHeight"));
    }
}

function buildBox(place, top, left, size, type, value) {
    let box = `<div style="top: ${top}px;position: absolute;${place}: ${left}px;font-size: ${size}px;">
        <div style="font-size: 15px;margin-top: 0px;margin-left: 0px;margin-bottom: 3px;font-weight: bold;">
            ${type}
        </div>
        ${value}
        </div>`;
    return box;
}

function buildButton(text, top, bg, color, link) {
    let button = `<div class="button" onclick="${link}" style="border-radius: 5px;top: ${top}px;position: absolute;left: 10px;font-size: 15px;
    background: ${bg};font-weight: bold;color: ${color};padding: 11px;width: calc(100% - 42px);
    text-indent: 10px;box-shadow: rgba(99, 99, 99, 0.2) 0px 2px 8px 0px;cursor: pointer;">
    ${text}
    </div>`
    return button;
}

function removeTicketChoices(id) {
    $(`#${id}`).find('.button').remove();
    $(`#${id}`).find('.ticket-confirmation').height(325);
}

async function cancelTicket(id) {
    const response = await fetch('book/flight/decline', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    if (response.ok) {
        logMessage("human", "I changed my mind.")
        removeTicketChoices(id);
        logMessage("ai", 'Booking declined. What else can I help you with?');
    }
}

async function confirmTicket(id) {
    logMessage("human", "Looks good to me.")
    params = JSON.stringify(confirmations[id]);
    const response = await fetch('book/flight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ params }),
    });
    if (response.ok) {
        const text_response = await response.text();
        removeTicketChoices(id);
        logMessage("ai", "Your flight has been successfully booked.")
    } else {
        console.error(await response.text())
        removeTicketChoices(id);
        logMessage("ai", "Sorry, flight booking failed. 😢")
    }
}

function generateRandomID(length) {
    return Math.random().toString(36).substring(2, 2 + length);
}