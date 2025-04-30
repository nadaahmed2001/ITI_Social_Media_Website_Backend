from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import time
import traceback
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_config(request):
    """
    Return WebSocket configuration for the frontend
    """
    # Get the protocol and host from the request
    protocol = request.is_secure() and 'https' or 'http'
    host = request.get_host()
    
    # Get client IP for debugging
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    # Determine WS protocol based on HTTP protocol or environment variable
    ws_protocol = os.environ.get('WS_PROTOCOL', None)
    if not ws_protocol:
        ws_protocol = 'wss' if protocol == 'https' else 'ws'
    
    # Get WebSocket host from environment or use request host
    ws_host = os.environ.get('WS_HOST', host)
    enable_websocket = os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true'
    
    # Get WebSocket max retry from environment or default to 5
    ws_max_retry = int(os.environ.get('WEBSOCKET_MAX_RETRY', '5'))
    
    # Log connection attempt with details
    logger.info(f"WebSocket config requested from {client_ip}, using protocol={ws_protocol}, host={ws_host}")
    
    # Check for ports in host
    ws_port = None
    if ':' in ws_host and ws_host.split(':')[1].isdigit():
        ws_port = ws_host.split(':')[1]
    else:
        # No explicit port, use default for protocol
        ws_port = '443' if ws_protocol == 'wss' else '80'
    
    # Check Redis connection
    redis_status = "Unknown"
    redis_url = os.environ.get("REDIS_URL", "")
    redis_details = {}
    
    try:
        if redis_url:
            # Only attempt to check Redis if URL is configured
            import redis
            # Just show part of the URL for security
            masked_url = f"{redis_url[:8]}..." if len(redis_url) > 8 else "Not set"
            redis_details['masked_url'] = masked_url
            
            # Try to parse the Redis URL to get host/port
            parsed = urlparse(redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            password = parsed.password
            db = int(parsed.path.lstrip('/')) if parsed.path and parsed.path != '/' else 0
            
            redis_details['host'] = host
            redis_details['port'] = port
            redis_details['db'] = db
            
            # Create a minimal Redis connection just to check status
            if password:
                r = redis.Redis(host=host, port=port, password=password, socket_connect_timeout=2.0)
            else:
                r = redis.Redis(host=host, port=port, socket_connect_timeout=2.0)
                
            start_time = time.time()
            r.ping()  # Will raise exception if connection fails
            latency = time.time() - start_time
            redis_status = f"Connected (latency: {latency:.3f}s)"
            redis_details['latency'] = f"{latency:.3f}s"
            
            # Check if Channels is using Redis
            try:
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                if channel_layer:
                    redis_details['channel_layer_type'] = str(type(channel_layer).__name__)
            except Exception as e:
                redis_details['channel_layer_error'] = str(e)
    except ImportError:
        redis_status = "Redis package not installed"
        redis_details['error'] = "Package not installed"
        logger.warning("Redis package not installed, WebSockets may not work properly")
    except Exception as e:
        redis_status = f"Error: {str(e)}"
        redis_details['error'] = str(e)
        logger.error(f"Redis connection error: {str(e)}")
        logger.debug(traceback.format_exc())
    
    # Log WebSocket configuration for debugging
    logger.info(f"WebSocket configuration: host={ws_host}, protocol={ws_protocol}, enabled={enable_websocket}")
    
    # Test if the WebSocket port is actually open
    port_open = False
    try:
        # Extract the hostname without port
        hostname = ws_host.split(':')[0]
        port = int(ws_port)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((hostname, port))
        port_open = (result == 0)
        sock.close()
    except Exception as e:
        logger.warning(f"Failed to check if port {ws_port} is open: {str(e)}")
    
    # Return configuration with more debug information
    response_data = {
        'wsHost': ws_host,
        'wsProtocol': ws_protocol,
        'wsPort': ws_port,
        'enableWebsocket': enable_websocket,
        'wsMaxRetry': ws_max_retry,
        'ws_url': f"{ws_protocol}://{ws_host}/ws/",
        'request_host': request.get_host(),
        'request_is_secure': request.is_secure(),
        'client_ip': client_ip,
        'env_variables_set': {
            'WS_HOST': 'WS_HOST' in os.environ,
            'WS_PROTOCOL': 'WS_PROTOCOL' in os.environ,
            'ENABLE_WEBSOCKET': 'ENABLE_WEBSOCKET' in os.environ,
            'REDIS_URL': 'REDIS_URL' in os.environ,
            'WEBSOCKET_MAX_RETRY': 'WEBSOCKET_MAX_RETRY' in os.environ
        },
        'port_check': {
            'port': ws_port,
            'open': port_open
        },
        'redis_status': redis_status,
        'redis_details': redis_details,
        # Add a timestamp to prevent caching issues
        'timestamp': time.time()
    }
    
    # Ensure we return valid JSON with CORS headers
    response = JsonResponse(response_data)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def health_check(request):
    """
    Simple health check endpoint that returns OK to indicate the service is running.
    Matches the path expected by the frontend.
    """
    from django.db import connection
    
    # Test database connection
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception as e:
        db_ok = False
    
    status = {
        "status": "healthy" if db_ok else "unhealthy",
        "db_connection": "ok" if db_ok else "failed",
        # Add WebSocket status
        "websocket_enabled": os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true',
        "using_daphne": True,
        "redis_url_set": bool(os.environ.get('REDIS_URL')),
    }
    
    status_code = 200 if db_ok else 500
    response = JsonResponse(status, status=status_code)
    response['Access-Control-Allow-Origin'] = '*'
    return response

def index(request):
    """Root path handler - provides basic API information or redirects"""
    from django.http import JsonResponse
    return JsonResponse({
        "status": "online",
        "message": "ITI Social Media Website API is running",
        "endpoints": {
            "health_check": "/health-check/",
            "websocket_config": "/websocket-config/"
        }
    })
