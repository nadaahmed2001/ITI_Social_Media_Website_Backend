from django.http import JsonResponse
import os

def websocket_config(request):
    ws_host = os.environ.get('WS_HOST', request.get_host())
    enable_websocket = os.environ.get('ENABLE_WEBSOCKET', 'false').lower() == 'true'
    
    # Add more debugging information
    return JsonResponse({
        'wsHost': ws_host,
        'enableWebsocket': enable_websocket,
        'request_host': request.get_host(),
        'env_variables_set': {
            'WS_HOST': 'WS_HOST' in os.environ,
            'ENABLE_WEBSOCKET': 'ENABLE_WEBSOCKET' in os.environ
        }
    })