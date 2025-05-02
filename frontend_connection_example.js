// WebSocket Connection URLs for Frontend
const BASE_URL = window.location.protocol === 'https:' 
  ? 'wss://your-domain.com' 
  : 'ws://localhost:8000';

const encodedToken = encodeURIComponent(authToken); // Always encode the token

// For group chat connections:
const groupChatSocket = new WebSocket(`${BASE_URL}/ws/chat/group/${groupId}?token=${encodedToken}`);

// For private chat connections:
const privateChatSocket = new WebSocket(`${BASE_URL}/ws/chat/private/${userId}?token=${encodedToken}`);

// Example event handlers with error handling
groupChatSocket.onopen = () => {
  console.log('Group chat WebSocket connection established');
};

groupChatSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message received:', data);
};

groupChatSocket.onerror = (error) => {
  console.error('WebSocket Error:', error);
};

groupChatSocket.onclose = () => {
  console.log('Group chat WebSocket connection closed');
};