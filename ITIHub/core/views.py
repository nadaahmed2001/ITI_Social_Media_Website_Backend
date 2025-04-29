from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import time  # Add time module import

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_config(request):
    """
    Return WebSocket configuration for the frontend
    """
    # Get the protocol and host from the request
    protocol = request.is_secure() and 'https' or 'http'
    host = request.get_host()
    
    # Determine WS protocol based on HTTP protocol
    ws_protocol = 'wss' if protocol == 'https' else 'ws'
    
    # Get WebSocket host from environment or use request host
    ws_host = os.environ.get('WS_HOST', host)
    enable_websocket = os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true'
    
    # Check Redis connection
    redis_status = "Unknown"
    redis_url = os.environ.get("REDIS_URL", "")
    
    try:
        if redis_url:
            # Only attempt to check Redis if URL is configured
            import redis
            # Just show part of the URL for security
            masked_url = f"{redis_url[:8]}..." if len(redis_url) > 8 else "Not set"
            
            # Try to parse the Redis URL to get host/port
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            password = parsed.password
            
            # Create a minimal Redis connection just to check status
            if password:
                r = redis.Redis(host=host, port=port, password=password, socket_connect_timeout=2.0)
            else:
                r = redis.Redis(host=host, port=port, socket_connect_timeout=2.0)
                
            r.ping()  # Will raise exception if connection fails
            redis_status = "Connected"
    except ImportError:
        redis_status = "Redis package not installed"
        logger.warning("Redis package not installed, WebSockets may not work properly")
    except Exception as e:
        redis_status = f"Error: {str(e)}"
        logger.error(f"Redis connection error: {str(e)}")
    
    # Log WebSocket configuration for debugging
    logger.info(f"WebSocket configuration: host={ws_host}, protocol={ws_protocol}, enabled={enable_websocket}")
    
    # Return configuration with more debug information
    response_data = {
        'wsHost': ws_host,
        'wsProtocol': ws_protocol,
        'enableWebsocket': enable_websocket,
        'request_host': request.get_host(),
        'env_variables_set': {
            'WS_HOST': 'WS_HOST' in os.environ,
            'ENABLE_WEBSOCKET': 'ENABLE_WEBSOCKET' in os.environ,
            'REDIS_URL': 'REDIS_URL' in os.environ
        },
        'redis_status': redis_status,
        # Add a timestamp to prevent caching issues
        'timestamp': time.time()  # Fixed: using time.time() directly
    }
    
    # Ensure we return valid JSON
    return JsonResponse(response_data)
