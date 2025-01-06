// Chat functionality
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const messagesDiv = document.getElementById('messages');
    
    // Function to send a message
    async function sendMessage() {
        const content = messageInput.value.trim();
        if (!content) return;
        
        try {
            const response = await fetch('/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Clear input after successful send
            messageInput.value = '';
            
            // Immediately fetch messages to show the new one
            await fetchMessages();
            
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        }
    }
    
    // Function to fetch and display messages
    async function fetchMessages() {
        try {
            const response = await fetch('/messages');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const messages = await response.json();
            
            // Clear current messages
            messagesDiv.innerHTML = '';
            
            // Display messages in reverse chronological order (newest first)
            messages.forEach(msg => {
                const messageElement = document.createElement('div');
                messageElement.className = 'message';
                
                const timestamp = new Date(msg.timestamp).toLocaleString();
                
                messageElement.innerHTML = `
                    <div class="message-content">${escapeHtml(msg.content)}</div>
                    <div class="message-timestamp">${timestamp}</div>
                `;
                
                messagesDiv.appendChild(messageElement);
            });
            
        } catch (error) {
            console.error('Error fetching messages:', error);
        }
    }
    
    // Helper function to escape HTML and prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Fetch messages immediately and then every 5 seconds
    fetchMessages();
    setInterval(fetchMessages, 5000);
});
