export function initializeVoiceInput(voiceBtn, textInputElement, callback) {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.lang = 'en-US';

    voiceBtn.addEventListener('click', () => {
        recognition.start();
        voiceBtn.textContent = '🔴 Listening...';
        voiceBtn.classList.add('btn-danger');
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        textInputElement.value = transcript;
        voiceBtn.textContent = '🎤 Voice Input';
        voiceBtn.classList.remove('btn-danger');
        callback(transcript);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        voiceBtn.textContent = '🎤 Voice Input';
        voiceBtn.classList.remove('btn-danger');
    };

    recognition.onend = () => {
        voiceBtn.textContent = '🎤 Voice Input';
        voiceBtn.classList.remove('btn-danger');
    };
}