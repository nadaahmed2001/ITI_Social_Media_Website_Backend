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
    
    # Return debug information for troubleshooting
    return JsonResponse({
        'wsHost': ws_host,
        'enableWebsocket': enable_websocket,
        'request_host': request.get_host(),
        'env_variables_set': {
            'WS_HOST': 'WS_HOST' in os.environ,
            'ENABLE_WEBSOCKET': 'ENABLE_WEBSOCKET' in os.environ
        }
    })
