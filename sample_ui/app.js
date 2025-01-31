import { initializeVoiceInput } from './voice-input.js';
import { processQuery } from './query-processor.js';

document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    const textResponse = document.getElementById('textResponse');
    const imageResponse = document.getElementById('imageResponse');
    const exampleButtons = document.querySelectorAll('.example-btn');

    // Text Input Event
    textInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const query = textInput.value;
            await processQuery(query, textResponse, imageResponse);
        }
    });

    // Example Query Buttons
    exampleButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const query = btn.getAttribute('data-query');
            textInput.value = query;
            await processQuery(query, textResponse, imageResponse);
        });
    });

    // Voice Input Setup
    initializeVoiceInput(voiceInputBtn, textInput, async (transcribedText) => {
        await processQuery(transcribedText, textResponse, imageResponse);
    });
});