from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import time
import os
import json
import traceback
import socket
from django.conf import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@csrf_exempt
def test_websocket_connection(request):
    """
    Test WebSocket connection from the server side to help diagnose issues.
    This endpoint simulates a WebSocket client connection from the server.
    """
    try:
        # Get WebSocket URL from request or fallback to configuration
        ws_url = request.GET.get('url')
        token = request.GET.get('token')
        
        if not ws_url:
            # Construct URL from available settings
            ws_protocol = getattr(settings, 'WS_PROTOCOL', None) or ('wss' if request.is_secure() else 'ws')
            ws_host = getattr(settings, 'WS_HOST', None) or request.get_host()
            ws_url = f"{ws_protocol}://{ws_host}/ws/"
        
        # Parse URL to get components
        parsed_url = urlparse(ws_url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'wss' else 80)
        path = parsed_url.path
        if parsed_url.query:
            path = f"{path}?{parsed_url.query}"
            
        # If token provided but not in URL, add it
        if token and 'token=' not in ws_url:
            separator = '&' if '?' in ws_url else '?'
            ws_url = f"{ws_url}{separator}token={token}"
            
        results = {
            'timestamp': time.time(),
            'ws_url': ws_url,
            'host': host,
            'port': port,
            'path': path,
            'tests': []
        }
        
        # Test 1: DNS resolution
        try:
            start_time = time.time()
            ip_address = socket.gethostbyname(host)
            dns_time = time.time() - start_time
            results['tests'].append({
                'name': 'DNS resolution',
                'status': 'success',
                'details': f"Resolved {host} to {ip_address} in {dns_time:.3f}s"
            })
        except Exception as e:
            results['tests'].append({
                'name': 'DNS resolution',
                'status': 'failed',
                'details': f"Failed to resolve {host}: {str(e)}"
            })
            return JsonResponse(results)

        # Test 2: TCP connection to the WebSocket port
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            connect_time = time.time() - start_time
            sock.close()
            results['tests'].append({
                'name': 'TCP connection',
                'status': 'success',
                'details': f"Connected to {host}:{port} in {connect_time:.3f}s"
            })
        except Exception as e:
            results['tests'].append({
                'name': 'TCP connection',
                'status': 'failed',
                'details': f"Failed to connect to {host}:{port}: {str(e)}"
            })
            return JsonResponse(results)

        # Test 3: WebSocket handshake simulation
        try:
            import ssl
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Wrap with SSL if using wss://
            if parsed_url.scheme == 'wss':
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)
                
            # Connect
            start_time = time.time()
            sock.connect((host, port))
            
            # Send WebSocket handshake request
            headers = [
                f"GET {path} HTTP/1.1",
                f"Host: {host}",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==",
                "Sec-WebSocket-Version: 13",
                "Origin: https://example.com",
                "",
                ""
            ]
            request_data = "\r\n".join(headers).encode()
            sock.send(request_data)
            
            # Receive response
            response = b""
            start_read_time = time.time()
            while True:
                try:
                    if time.time() - start_read_time > 5:
                        raise TimeoutError("Handshake response timeout")
                    part = sock.recv(4096)
                    if not part:
                        break
                    response += part
                    if b"\r\n\r\n" in response:
                        break
                except socket.timeout:
                    break
            
            handshake_time = time.time() - start_time
            sock.close()
            
            # Parse response
            response_str = response.decode('utf-8', errors='ignore')
            response_lines = response_str.split('\r\n')
            status_line = response_lines[0] if response_lines else 'No response'
            
            if "101 Switching Protocols" in status_line:
                results['tests'].append({
                    'name': 'WebSocket handshake',
                    'status': 'success',
                    'details': f"Handshake successful in {handshake_time:.3f}s: {status_line}"
                })
            else:
                results['tests'].append({
                    'name': 'WebSocket handshake',
                    'status': 'failed',
                    'details': f"Handshake failed in {handshake_time:.3f}s: {status_line}",
                    'response': response_str[:500] + ('...' if len(response_str) > 500 else '')
                })
        except Exception as e:
            results['tests'].append({
                'name': 'WebSocket handshake',
                'status': 'failed',
                'details': f"Error during handshake: {str(e)}",
                'traceback': traceback.format_exc()
            })

        # Return results
        return JsonResponse(results, json_dumps_params={'indent': 2})

    except Exception as e:
        logger.exception("Error in WebSocket connection test")
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
def html_websocket_tester(request):
    """
    Provides an HTML form to test WebSocket connections from the browser
    """
    # Get WebSocket URL from available settings
    ws_protocol = getattr(settings, 'WS_PROTOCOL', None) or ('wss' if request.is_secure() else 'ws')
    ws_host = getattr(settings, 'WS_HOST', None) or request.get_host()
    default_ws_url = f"{ws_protocol}://{ws_host}/ws/chat/"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Tester</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            label {{ display: block; margin: 10px 0 5px; }}
            input[type="text"] {{ width: 100%; padding: 8px; box-sizing: border-box; }}
            button {{ margin-top: 10px; padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }}
            button:hover {{ background: #45a049; }}
            #log {{ 
                margin-top: 20px; 
                padding: 10px; 
                border: 1px solid #ddd; 
                background-color: #f9f9f9; 
                height: 300px; 
                overflow-y: auto; 
                font-family: monospace;
            }}
            .error {{ color: red; }}
            .success {{ color: green; }}
            .info {{ color: blue; }}
        </style>
    </head>
    <body>
        <h1>WebSocket Connection Tester</h1>
        
        <label for="wsUrl">WebSocket URL:</label>
        <input type="text" id="wsUrl" value="{default_ws_url}">
        
        <label for="token">Authentication Token (optional):</label>
        <input type="text" id="token" placeholder="Your JWT token">
        
        <div>
            <button id="connectBtn">Connect</button>
            <button id="disconnectBtn" disabled>Disconnect</button>
            <button id="sendBtn" disabled>Send Test Message</button>
        </div>
        
        <div id="log"></div>
        
        <script>
            let socket = null;
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 3;
            const reconnectInterval = 2000; // 2 seconds
            
            function log(message, type = 'info') {{
                const logElem = document.getElementById('log');
                const entry = document.createElement('div');
                entry.classList.add(type);
                entry.textContent = `[${{new Date().toLocaleTimeString()}}] ${{message}}`;
                logElem.appendChild(entry);
                logElem.scrollTop = logElem.scrollHeight;
            }}
            
            function updateButtons(connected) {{
                document.getElementById('connectBtn').disabled = connected;
                document.getElementById('disconnectBtn').disabled = !connected;
                document.getElementById('sendBtn').disabled = !connected;
            }}
            
            function connect() {{
                try {{
                    log('Attempting to connect...');
                    
                    let wsUrl = document.getElementById('wsUrl').value;
                    const token = document.getElementById('token').value;
                    
                    // Add token to URL if provided
                    if (token && !wsUrl.includes('token=')) {{
                        const separator = wsUrl.includes('?') ? '&' : '?';
                        wsUrl += `${{separator}}token=${{token}}`;
                    }}
                    
                    log(`Connecting to: ${{wsUrl}}`);
                    socket = new WebSocket(wsUrl);
                    
                    socket.onopen = function(event) {{
                        log('Connection established!', 'success');
                        reconnectAttempts = 0;
                        updateButtons(true);
                        
                        // Send an initial ping
                        setTimeout(() => {{
                            if (socket && socket.readyState === WebSocket.OPEN) {{
                                socket.send(JSON.stringify({{ type: 'ping', data: {{ timestamp: Date.now() }} }}));
                                log('Sent initial ping');
                            }}
                        }}, 500);
                    }};
                    
                    socket.onmessage = function(event) {{
                        log(`Received message: ${{event.data}}`, 'success');
                        try {{
                            const data = JSON.parse(event.data);
                            log(`Parsed data: ${{JSON.stringify(data, null, 2)}}`, 'info');
                        }} catch (e) {{
                            // Not JSON, that's fine
                        }}
                    }};
                    
                    socket.onclose = function(event) {{
                        const reason = event.reason ? `Reason: ${{event.reason}}` : '';
                        log(`Connection closed. Code: ${{event.code}}. ${{reason}}`, 'error');
                        updateButtons(false);
                        
                        // Attempt to reconnect
                        if (reconnectAttempts < maxReconnectAttempts) {{
                            reconnectAttempts++;
                            log(`Attempting to reconnect (${{reconnectAttempts}}/${{maxReconnectAttempts}})...`);
                            setTimeout(connect, reconnectInterval);
                        }}
                    }};
                    
                    socket.onerror = function(error) {{
                        log(`WebSocket error: ${{error}}`, 'error');
                        console.error('WebSocket error:', error);
                    }};
                }} catch (e) {{
                    log(`Error creating WebSocket: ${{e.message}}`, 'error');
                    console.error('Error:', e);
                }}
            }}
            
            function disconnect() {{
                if (socket) {{
                    log('Disconnecting...');
                    socket.close(1000, 'User initiated disconnect');
                    socket = null;
                    updateButtons(false);
                }}
            }}
            
            function sendTestMessage() {{
                if (socket && socket.readyState === WebSocket.OPEN) {{
                    const message = {{
                        type: 'test_message',
                        data: {{
                            text: 'Hello from WebSocket tester!',
                            timestamp: Date.now()
                        }}
                    }};
                    
                    socket.send(JSON.stringify(message));
                    log(`Sent test message: ${{JSON.stringify(message)}}`, 'info');
                }} else {{
                    log('Cannot send message - socket is not connected', 'error');
                }}
            }}
            
            document.getElementById('connectBtn').addEventListener('click', connect);
            document.getElementById('disconnectBtn').addEventListener('click', disconnect);
            document.getElementById('sendBtn').addEventListener('click', sendTestMessage);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content)
