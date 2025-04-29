from django.http import JsonResponse
import os
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def websocket_config(request):
    """
    Return WebSocket configuration for the frontend
    """
    ws_host = os.environ.get('WS_HOST', request.get_host())
    enable_websocket = os.environ.get('ENABLE_WEBSOCKET', 'false').lower() == 'true'
    
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
            
            # Create a minimal Redis connection just to check status
            r = redis.Redis(host=host, port=port, socket_connect_timeout=2.0)
            r.ping()  # Will raise exception if connection fails
            redis_status = "Connected"
    except Exception as e:
        redis_status = f"Error: {str(e)}"
    
    # Return debug information for troubleshooting
    return JsonResponse({
        'wsHost': ws_host,
        'enableWebsocket': enable_websocket,
        'request_host': request.get_host(),
        'env_variables_set': {
            'WS_HOST': 'WS_HOST' in os.environ,
            'ENABLE_WEBSOCKET': 'ENABLE_WEBSOCKET' in os.environ,
            'REDIS_URL': 'REDIS_URL' in os.environ
        },
        'redis_status': redis_status
    })
