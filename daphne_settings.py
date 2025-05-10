import os

# WebSocket close timeout (how long to wait for WebSocket to close gracefully)
os.environ.setdefault('DAPHNE_WS_PROTOCOL_DISCONNECT_DELAY', '2')  # seconds

# How long to wait for writes on a WebSocket
os.environ.setdefault('DAPHNE_WEBSOCKET_WRITE_TIMEOUT', '5')  # seconds

# Default timeout for disconnect handlers
os.environ.setdefault('DAPHNE_DISCONNECT_TIMEOUT', '3')  # seconds
