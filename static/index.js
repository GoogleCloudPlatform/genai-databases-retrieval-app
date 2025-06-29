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

import {create_trace} from './trace.js';

// Records and keep track of the confirmation blocks (e.g. ticket booking confirmation)
let confirmations = {}
// Records and keep track of traces associated with each message
let traces = {}

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

// Event delegation for dynamic elements
document.addEventListener('click', function(event) {
    const event_id = event.target.id;
    
    if (event_id === 'chatuserImg') {
        showSignOut();
    }
    if (event_id === 'signoutButton') {
        signout();
    }
    if (event_id.startsWith('traceButton')) {
        const trace_id = event_id.replace("traceButton", "");
        showTrace(event, trace_id);
    }
    if (event_id.startsWith('confirmTicket')) {
        const message_id = event_id.replace("confirmTicket", "");
        confirmTicket(message_id);
    }
    if (event_id.startsWith('cancelTicket')) {
        const message_id = event_id.replace("cancelTicket", "");
        cancelTicket(message_id);
    }
});

async function submitMessage() {
    let msg = $('.chat-bar input').val();
    // Add message to UI
    logMessage("human", msg)
    // Clear message
    $('.chat-bar input').val('');
    window.setTimeout(() => {
        $('#loader-container').show();
        $('.chat-content').scrollTop($('.chat-content').prop("scrollHeight"));
    }, 400);
    try {
        // Prompt LLM
        let answer = await askQuestion(msg);
        $('#loader-container').hide();
        // Add response to UI
        if (answer.type === "message") {
            logMessage("ai", answer.content, answer.trace)
        } else if (answer.type === "confirmation") {
            const messageId = generateRandomID(10);
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

function buildMessage(name, msg, trace_html) {
    let traceobj = ""
    if (!!trace_html) {
        let traceid = generateRandomID(10);
        traces[traceid] = trace_html
        traceobj = `<div id="traceButton${traceid}" class="material-symbols-outlined info-icon">info</div>`
    }
    let image = ''
    if (name === "ai"){
        image = '<div class="sender-icon"><img src="static/logo.png"></div>'
    } else if(name === "human" && $('.chat-user-image').first().attr('src')){
        image = `<div class="sender-icon"><img src="${$('.chat-user-image').first().attr('src')}"></div>`
    }
    let message = `<div class="chat-bubble ${name}">
    ${image}
    <span><div class="innermsg">${msg}</div>${traceobj}</span>
    </div>`;
    return message;
}

// Helper function to print to chatroom
function logMessage(name, msg, trace) {
    let trace_html = undefined;
    if (trace != null) {
        trace_html = create_trace(trace);
    }
    let message = buildMessage(name, msg, trace_html);
    $('.inner-content').append(message);
    $('.chat-content').scrollTop($('.chat-content').prop("scrollHeight"));
}

function buildConfirmation(confirmation, messageId) {
    if (["Insert Ticket","insert_ticket"].includes(confirmation.tool)) {
        const params = confirmation.params;
        const output = confirmation.output;
        const message_id = messageId;
        confirmations[message_id] = params
        const from = params.departure_airport;
        const to = params.arrival_airport;
        const flight = `${params.airline} ${params.flight_number}`;
        const airline = params.airline;
        const flight_number = params.flight_number;
        const departure_time = params.departure_time;
        const arrival_time = params.arrival_time;
        const userName = $('#user-name').first().text();
        const message = `<div class="chat-bubble ai" id="${message_id}">
        <div class="sender-icon"><img src="static/logo.png"></div>
        <div class="ticket-confirmation">
            ${output}
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
            ${buildButton("Looks good to me. Book it!", 342, "#805e9d", "#FFF", "confirmTicket" + message_id)}
            ${buildButton("I changed my mind.", 395, "#f8f8f8", "#181a23", "cancelTicket" + message_id)}
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

function buildButton(text, top, bg, color, element_id) {
    let button = `<div class="button" id="${element_id}" style="border-radius: 5px;top: ${top}px;position: absolute;left: 10px;font-size: 15px;
    background: ${bg};font-weight: bold;color: ${color};padding: 11px;width: calc(100% - 42px);
    text-indent: 10px;box-shadow: rgba(99, 99, 99, 0.2) 0px 2px 8px 0px;cursor: pointer;">
    ${text}
    </div>`
    return button;
}

function showTrace(event, id) {
    const trace = traces[id];
    const rect = event.target.getBoundingClientRect();

    let leftPosition = rect.left + window.scrollX;
    let topPosition = rect.bottom + window.scrollY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    if (leftPosition + 500 > windowWidth) {
        leftPosition = windowWidth - 500;
    }
    if (topPosition + 500 > windowHeight) {
        topPosition = windowHeight - 500;
    }

    const tooltip = document.createElement('div');
    tooltip.id = "trace"
    tooltip.innerHTML = trace;
    tooltip.style.left = `${leftPosition}px`;
    tooltip.style.top = `${topPosition}px`;

    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';

    overlay.addEventListener('click', function() {
        if (tooltip.parentNode) {
          tooltip.parentNode.removeChild(tooltip);
        }
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      });

    document.body.appendChild(overlay);
    document.body.appendChild(tooltip);
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
    logMessage("human", "I changed my mind.")
    removeTicketChoices(id);

    if (response.ok) {
        logMessage("ai", await response.text());
    } else {
        console.error(await response.text())
        logMessage("ai", "Sorry, something went wrong. 😢")
    }
}

async function confirmTicket(id) {
    logMessage("human", "Looks good to me.")
    const params = JSON.stringify(confirmations[id]);
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
        logMessage("ai", "<p>Your flight has been successfully booked.</p>")
    } else {
        console.error(await response.text())
        removeTicketChoices(id);
        logMessage("ai", "Sorry, flight booking failed. 😢")
    }
}

function generateRandomID(length) {
    return Math.random().toString(36).substring(2, 2 + length);
}

function showSignOut(){

    $('.popup-signout').show()

    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';

    overlay.addEventListener('click', function() {
        $('.popup-signout').hide()
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      });

    document.body.appendChild(overlay);
}
