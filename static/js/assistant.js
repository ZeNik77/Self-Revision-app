const aiButton = document.getElementById('aiButton');
const aiWindow = document.getElementById('aiWindow');
const aiClose = document.getElementById('aiClose');
const aiInput = document.getElementById('aiInput');
const aiSend = document.getElementById('aiSend');
const messagesContainer = document.getElementById('messagesContainer');

aiButton.addEventListener('click', () => {
    aiWindow.classList.toggle('active');
})

aiClose.addEventListener('click', () => {
    aiWindow.classList.remove('active');
})