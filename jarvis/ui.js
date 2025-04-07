import { socket } from './main.js';
import { setFinished } from './shared_var.js';

let container, jarvisElem;

function addTextLetterByLetter(text, index = 0, role) {
    if (!container) container = document.getElementById('scrollable-container');

    if (index < text.length) {
        if (text[index] === '\n') {
            container.innerHTML += '<br>';
        } else {
            container.innerHTML += text[index];
        }


        setTimeout(() => {
            addTextLetterByLetter(text, index + 1, role);
            if (container.scrollHeight > container.clientHeight) {
                scrollToBottom();
            }
        }, 30);

        if (index === text.length - 1 && role === 'assistant') {
            setFinished(true);
        }
    }
}

function scrollToBottom() {
    if (!container) container = document.getElementById('scrollable-container');
    container.scrollTop = container.scrollHeight;
}

function updateClock() {
    const now = new Date();
    document.getElementById('current').innerText =
        `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    document.getElementById('seconds').innerText = now.getSeconds().toString().padStart(2, '0');
}

function initUI() {
    container = document.getElementById('scrollable-container');
    jarvisElem = document.getElementById('jarvis');

    const hermaContainer = document.getElementById('herma-container');
    const percentage = document.getElementById('percentage');
    const day = document.getElementById('day');
    const month = document.getElementById('month');

    const date = new Date();
    month.innerText = date.toLocaleString('default', { month: 'long' });
    day.innerText = date.getDate().toString();

    percentage.innerText = Math.ceil((Math.random() * 10) + 90) + '%';

    setTimeout(() => {
        hermaContainer.classList.replace('herma', 'final');
        jarvisElem.classList.replace('hidden', 'jarvis');
    }, 3000);

    updateClock();
    setInterval(updateClock, 1000);

    scrollToBottom();
}

socket.on('prompt_response', (data) => {
    const prefix = data['role'] === 'user' ? 'You: ' : 'JARVIS: ';
    addTextLetterByLetter(`${prefix}${data['content']}\n`, 0, data['role']);
});

document.addEventListener('DOMContentLoaded', initUI);