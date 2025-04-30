from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import os
from django.conf import settings

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_diagnostics(request):
    """
    Debug endpoint to diagnose WebSocket issues
    """
    try:
        # Basic system information
        import sys
        import django
        import channels

        # Create diagnostic information
        diagnostics = {
            "system_info": {
                "django_version": django.__version__,
                "channels_version": channels.__version__,
                "python_version": sys.version,
            },
            
            # Django settings
            "django_settings": {
                "debug_mode": settings.DEBUG,
                "allowed_hosts": settings.ALLOWED_HOSTS,
                "websocket_enabled": getattr(settings, 'ENABLE_WEBSOCKET', 'not set'),
            },
            
            # WebSocket configuration
            "websocket_config": {
                "ws_protocol": getattr(settings, 'WS_PROTOCOL', 'auto-detect'),
                "ws_host": getattr(settings, 'WS_HOST', 'auto-detect'),
            },
            
            # Request information for debugging
            "request_info": {
                "host": request.get_host(),
                "is_secure": request.is_secure(),
                "x_forwarded_proto": request.META.get('HTTP_X_FORWARDED_PROTO', 'not set'),
                "x_forwarded_host": request.META.get('HTTP_X_FORWARDED_HOST', 'not set'),
            },
            
            # Redis configuration (masked for security)
            "redis_config": {
                "redis_url_set": bool(os.environ.get("REDIS_URL")),
            }
        }
        
        # Check if we have channel layers configured
        if hasattr(settings, 'CHANNEL_LAYERS'):
            backend = settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', 'not set')
            diagnostics["redis_config"]["channel_layer_backend"] = backend
            diagnostics["redis_config"]["using_redis"] = "redis" in backend.lower()
        
        # Try to check if Redis/Channels is working
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                diagnostics["redis_check"] = {
                    "channel_layer_type": str(type(channel_layer)),
                    "status": "obtained channel layer successfully"
                }
                
                # Try a simple capacity check
                capacity = getattr(channel_layer, 'capacity', 'unknown')
                diagnostics["redis_check"]["capacity"] = capacity
        except Exception as e:
            diagnostics["redis_check"] = {
                "error": str(e),
                "status": "failed to get channel layer"
            }
        
        return JsonResponse(diagnostics, json_dumps_params={'indent': 2})
    
    except Exception as e:
        logger.exception("Error in websocket diagnostics")
        return JsonResponse({"error": str(e)}, status=500)
