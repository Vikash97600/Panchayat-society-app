// Chat functionality for Panchayat Housing Society
// Uses polling (every 3 seconds) to fetch new messages

let currentRoomId = null;
let chatPollInterval = null;

// Initialize chat when tab is shown
window.initChat = function() {
    console.log('[CHAT] initChat called');
    loadChatRooms();
    startPolling();
    console.log('[CHAT] Chat initialized, polling started');
};

// Load all chat rooms
let lastRoomsCount = 0;

async function loadChatRooms() {
    const container = document.getElementById('chat-rooms-list');
    const loading = document.getElementById('chat-rooms-loading');
    
    if (!container) return;
    if (loading) loading.classList.remove('d-none');
    
    try {
        const token = localStorage.getItem('panchayat_token');
        if (!token) {
            container.innerHTML = '<div class="text-center text-danger py-4"><p>Please login first</p></div>';
            return;
        }
        
        const res = await fetch('/api/chat/rooms/', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) {
            if (loading) loading.classList.add('d-none');
            return;
        }
        
        const data = await res.json();
        
        // Handle different response formats
        let roomsData = [];
        if (Array.isArray(data)) {
            roomsData = data;
        } else if (data && data.results && Array.isArray(data.results)) {
            roomsData = data.results;
        }
        
        // Only update if count changed (new room added or first load)
        if (roomsData.length !== lastRoomsCount || (roomsData.length > 0 && container.innerHTML === '')) {
            lastRoomsCount = roomsData.length;
            
            if (loading) loading.classList.add('d-none');
            
            if (roomsData && roomsData.length > 0) {
                container.innerHTML = roomsData.map(room => {
                    const otherUser = room.other_user || {};
                    const lastMsg = room.last_message || {};
                    const unread = room.unread_count || 0;
                    const isActive = currentRoomId === room.id ? 'active' : '';
                    
                    return `
                        <div class="chat-room-item ${isActive}" onclick="selectRoom(${room.id}, '${otherUser.name || ''}', '${otherUser.role || ''}')" 
                             style="padding: 12px; border-bottom: 1px solid var(--border); cursor: pointer;">
                            <div class="d-flex align-items-center">
                                <div class="avatar avatar-sm me-2" style="background: var(--brand-primary); color: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                    ${(otherUser.name || 'U').charAt(0).toUpperCase()}
                                </div>
                                <div class="flex-grow-1 overflow-hidden">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong class="text-truncate">${otherUser.name || 'Unknown'}</strong>
                                        ${unread > 0 ? `<span class="badge bg-danger">${unread}</span>` : ''}
                                    </div>
                                    <small class="text-muted text-truncate d-block">
                                        ${lastMsg.content ? (lastMsg.content.substring(0, 25) + (lastMsg.content.length > 25 ? '...' : '')) : 'No messages yet'}
                                    </small>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div class="text-center text-muted py-4"><p>No conversations yet</p></div>';
            }
        } else {
            if (loading) loading.classList.add('d-none');
        }
    } catch (error) {
        console.error('Error loading chat rooms:', error);
        if (loading) loading.classList.add('d-none');
    }
}

// Select a chat room
window.selectRoom = function(roomId, userName, userRole) {
    currentRoomId = roomId;
    lastMessageCount = 0; // Reset message count for new room
    
    // Update UI
    document.getElementById('chat-with-name').textContent = userName || 'Chat';
    document.getElementById('chat-with-role').textContent = userRole ? userRole.charAt(0).toUpperCase() + userRole.slice(1) : '';
    document.getElementById('chat-empty').classList.add('d-none');
    
    // Highlight selected room - remove from all, add to current
    document.querySelectorAll('.chat-room-item').forEach(item => {
        item.classList.remove('active');
        item.style.background = '';
    });
    const clickedItem = window.event ? window.event.target.closest('.chat-room-item') : null;
    if (clickedItem) {
        clickedItem.classList.add('active');
        clickedItem.style.setProperty('background', 'var(--brand-light)', 'important');
    }
    
    // Load messages for this room
    loadMessages(roomId);
    
    // Mark messages as read
    markMessagesRead(roomId);
};

// Load messages for a room
let lastMessageCount = 0;

async function loadMessages(roomId) {
    console.log('[CHAT] loadMessages called for room:', roomId);
    
    const container = document.getElementById('chat-messages-list');
    const emptyMsg = document.getElementById('chat-empty');
    
    if (!container) {
        console.error('[CHAT] chat-messages-list container not found');
        return;
    }
    
    try {
        const res = await fetch(`/api/chat/rooms/${roomId}/messages/`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('panchayat_token')
            }
        });
        
        console.log('[CHAT] Messages response status:', res.status);
        
        const data = await res.json();
        
        // Handle different response formats
        let messagesData = [];
        if (Array.isArray(data)) {
            messagesData = data;
        } else if (data && data.results && Array.isArray(data.results)) {
            messagesData = data.results;
        }
        console.log('[CHAT] Messages array:', messagesData);
        
        // Only update DOM if message count changed or first load
        if (messagesData.length !== lastMessageCount || (messagesData.length > 0 && container.innerHTML === '')) {
            lastMessageCount = messagesData.length;
            
            if (messagesData && messagesData.length > 0) {
                if (emptyMsg) emptyMsg.classList.add('d-none');
                container.innerHTML = messagesData.map(msg => {
                    const isMe = msg.is_me;
                    const time = formatMessageTime(msg.created_at);
                    
                    return `
                        <div class="message-item mb-3 ${isMe ? 'text-end' : ''}">
                            <div class="d-flex ${isMe ? 'justify-content-end' : ''}">
                                <div class="message-bubble ${isMe ? 'bg-primary text-white' : 'bg-light'}" 
                                     style="max-width: 70%; padding: 10px 15px; border-radius: 15px; ${isMe ? 'border-bottom-right-radius: 3px;' : 'border-bottom-left-radius: 3px;'}">
                                    <div class="message-content">${escapeHtml(msg.content)}</div>
                                    <div class="message-time" style="font-size: 11px; ${isMe ? 'color: rgba(255,255,255,0.7);' : 'color: var(--text-muted);'} margin-top: 4px;">
                                        ${time} ${msg.is_read && isMe ? '<i class="fas fa-check-double ms-1"></i>' : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Scroll to bottom
                scrollToBottom();
            } else {
                if (emptyMsg) emptyMsg.classList.remove('d-none');
                container.innerHTML = '';
            }
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Send a message
window.sendMessage = async function() {
    console.log('[CHAT] sendMessage called, currentRoomId:', currentRoomId);
    
    if (!currentRoomId) {
        alert('Please select a conversation first');
        return;
    }
    
    const input = document.getElementById('message-input');
    if (!input) {
        alert('Message input not found');
        return;
    }
    
    const content = input.value.trim();
    if (!content) return;
    
    console.log('[CHAT] Sending message:', content);
    
    try {
        const res = await fetch(`/api/chat/rooms/${currentRoomId}/messages/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('panchayat_token')
            },
            body: JSON.stringify({ content })
        });
        
        console.log('[CHAT] Send response status:', res.status);
        
        const data = await res.json();
        console.log('[CHAT] Send response data:', data);
        
        if (data.success) {
            input.value = '';
            loadMessages(currentRoomId);
            loadChatRooms(); // Update room list with last message
        } else {
            alert(data.message || 'Failed to send message');
        }
    } catch (error) {
        console.error('[CHAT] Error sending message:', error);
        alert('Failed to send message: ' + error.message);
    }
};

// Handle Enter key in message input
window.handleMessageKeyPress = function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        window.sendMessage();
    }
};

// Mark messages as read
async function markMessagesRead(roomId) {
    try {
        await fetch(`/api/chat/rooms/${roomId}/mark-read/`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('panchayat_token')
            }
        });
    } catch (error) {
        console.error('Error marking messages as read:', error);
    }
}

// Open new chat modal
window.openNewChatModal = async function() {
    try {
        const res = await fetch('/api/chat/users/', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('panchayat_token')
            }
        });
        
        const data = await res.json();
        
        if (data.success && data.data && data.data.length > 0) {
            let usersHtml = data.data.map(user => `
                <div class="user-option p-2 border-bottom" style="cursor: pointer;" onclick="startNewChat(${user.id}, '${user.full_name || user.email}')">
                    <div class="d-flex align-items-center">
                        <div class="avatar avatar-sm me-2" style="background: var(--brand-primary); color: white;">
                            ${(user.full_name || user.email || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <strong>${user.full_name || user.email}</strong>
                            <br><small class="text-muted">${user.role}</small>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Create modal if not exists
            let modal = document.getElementById('newChatModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'newChatModal';
                modal.className = 'modal fade';
                modal.innerHTML = `
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Start New Chat</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-0" id="chat-users-list">
                                ${usersHtml}
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            } else {
                document.getElementById('chat-users-list').innerHTML = usersHtml;
            }
            
            new bootstrap.Modal(modal).show();
        } else {
            showToast('No users available to chat with', 'info');
        }
    } catch (error) {
        console.error('Error loading chat users:', error);
        showToast('Failed to load users', 'error');
    }
};

// Start a new chat
window.startNewChat = async function(userId, userName) {
    try {
        const res = await fetch('/api/chat/rooms/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('panchayat_token')
            },
            body: JSON.stringify({ other_user_id: userId })
        });
        
        const data = await res.json();
        
        if (data.success) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('newChatModal')).hide();
            
            // Select the new room
            selectRoom(data.data.id, userName, 'resident');
            loadChatRooms();
        } else {
            showToast(data.message || 'Failed to create chat', 'error');
        }
    } catch (error) {
        console.error('Error creating chat:', error);
        showToast('Failed to create chat', 'error');
    }
};

// Format message time
function formatMessageTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    if (diff < 86400000) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// Scroll to bottom of chat
function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start polling for new messages
let isPollingStarted = false;

function startPolling() {
    if (isPollingStarted) return; // Prevent duplicate polling
    isPollingStarted = true;
    
    chatPollInterval = setInterval(() => {
        if (currentRoomId) {
            loadMessages(currentRoomId);
        }
        loadChatRooms();
    }, 3000); // Poll every 3 seconds
}

// Stop polling
function stopPolling() {
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
    }
}

// Export functions to window
window.initChat = initChat;
window.selectRoom = selectRoom;
window.sendMessage = sendMessage;
window.handleMessageKeyPress = handleMessageKeyPress;
window.openNewChatModal = openNewChatModal;
window.startNewChat = startNewChat;
window.stopPolling = stopPolling;

console.log('[CHAT] Chat JS loaded');