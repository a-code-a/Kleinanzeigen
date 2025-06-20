document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    // Early exit if chat elements are not on the current page
    if (!chatContainer) {
        // console.log('Chat container not found, chat script not initializing for this page.');
        return;
    }

    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');

    // If any essential chat element is missing after confirming container, then log error.
    if (!chatBox || !chatInput || !sendChatBtn) {
        console.error('One or more essential chat elements (chat-box, chat-input, send-chat-btn) are missing.');
        return;
    }

    const adId = chatContainer.dataset.adId;

    if (!adId) {
        console.error('Ad ID not found in chat-container data attribute.');
        // Optionally, disable chat input and button here
        chatInput.disabled = true;
        sendChatBtn.disabled = true;
        displayMessage('Could not initialize chat: Ad ID is missing.', 'error-message');
        return;
    }

    // Scroll chat box to bottom on initial load
    chatBox.scrollTop = chatBox.scrollHeight;

    function displayMessage(text, sender, isHtml = false) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('chat-message', `${sender}-message`);
        
        // Create a container for the sender label and the message content
        const messageContentDiv = document.createElement('div');

        if (sender === 'user') {
            // User messages align right
            messageWrapper.style.textAlign = 'right';
            const senderLabel = document.createElement('div');
            senderLabel.className = 'sender-label';
            senderLabel.textContent = 'You:';
            messageContentDiv.appendChild(senderLabel);

            const textNode = document.createElement('div');
            textNode.textContent = text;
            messageContentDiv.appendChild(textNode);

        } else if (sender === 'assistant') {
            const senderLabel = document.createElement('div');
            senderLabel.className = 'sender-label';
            senderLabel.textContent = 'Assistant:';
            messageContentDiv.appendChild(senderLabel);

            const textNode = document.createElement('div');
            if (isHtml) {
                textNode.innerHTML = text; // Assuming text is safe, pre-rendered Markdown
            } else {
                textNode.textContent = text; // Display as plain text
            }
            messageContentDiv.appendChild(textNode);
        } else { // error or loading messages
            messageContentDiv.textContent = text;
        }
        
        messageWrapper.appendChild(messageContentDiv);
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    let isLoading = false;

    async function sendMessage() {
        if (isLoading) return;

        const userMessageText = chatInput.value.trim();
        if (userMessageText === '') {
            return;
        }

        displayMessage(userMessageText, 'user');
        chatInput.value = '';
        isLoading = true;
        
        const loadingMessageDiv = document.createElement('div');
        loadingMessageDiv.classList.add('chat-message', 'loading-message');
        loadingMessageDiv.textContent = 'Assistant is thinking...';
        chatBox.appendChild(loadingMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const response = await fetch(`/chat/${adId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessageText }),
            });

            chatBox.removeChild(loadingMessageDiv);

            if (response.ok) {
                const responseData = await response.json();
                if (responseData.success && responseData.answer) {
                    // The initial analysis in HTML is rendered via |markdown filter.
                    // Here, if responseData.answer is Markdown, we need to handle it.
                    // For now, displaying as text. To render Markdown, a library or specific handling is needed.
                    // Let's assume the server sends plain text for chat for now, or HTML if markdown is processed server-side for chat.
                    // The displayMessage function has an isHtml flag. If server sends HTML for markdown, set it to true.
                    displayMessage(responseData.answer, 'assistant');
                } else {
                    const errorMsg = responseData.error || responseData.details?.error || 'Unknown error from AI';
                    displayMessage(`Error: ${errorMsg}`, 'error-message');
                    console.error("AI Error:", responseData);
                }
            } else {
                const errorText = await response.text(); // Get more details for non-OK HTTP responses
                console.error('Server error:', response.status, errorText);
                displayMessage(`Error: Could not reach the server (status ${response.status}). Please try again. Details: ${errorText}`, 'error-message');
            }
        } catch (error) {
            if (chatBox.contains(loadingMessageDiv)) { // Check if still there
                chatBox.removeChild(loadingMessageDiv);
            }
            console.error('Fetch error:', error);
            displayMessage('Error: Could not send message. Check your connection or view console for details.', 'error-message');
        } finally {
            isLoading = false;
            chatInput.focus();
        }
    }

    sendChatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });
});
