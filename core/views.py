from django.http import JsonResponse
import os

def websocket_config(request):
    return JsonResponse({
        'wsHost': os.environ.get('WS_HOST', request.get_host()),
        'enableWebsocket': os.environ.get('ENABLE_WEBSOCKET', 'false').lower() == 'true'
    })