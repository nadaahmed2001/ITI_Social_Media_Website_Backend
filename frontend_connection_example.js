// WebSocket Connection URLs for Frontend
// Note: Replace BASE_URL with your actual websocket server URL (e.g., wss://your-domain.com or ws://localhost:8000)

// For group chat connections:
const groupChatSocket = new WebSocket(`${BASE_URL}/ws/chat/group/${groupId}/?token=${authToken}`);

// For private chat connections:
const privateChatSocket = new WebSocket(`${BASE_URL}/ws/chat/private/${userId}/?token=${authToken}`);

// Example event handlers
groupChatSocket.onopen = () => {
  console.log('Group chat WebSocket connection established');
};

groupChatSocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message received:', data);
};

groupChatSocket.onclose = () => {
  console.log('Group chat WebSocket connection closed');
};
