const aiButton = document.getElementById('openAIPopup');
const aiWindow = document.getElementById('aiPopup');
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