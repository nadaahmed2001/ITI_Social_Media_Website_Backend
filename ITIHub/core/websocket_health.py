from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import os
import socket
import requests
from django.conf import settings
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

@csrf_exempt
def websocket_health(request):
    """
    Comprehensive WebSocket health check endpoint for debugging connection issues
    """
    try:
        # Get environment info
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        # Get WebSocket configuration
        ws_protocol = getattr(settings, 'WS_PROTOCOL', 'auto-detect')
        if ws_protocol == 'auto-detect':
            ws_protocol = 'wss' if request.is_secure() else 'ws'
            
        ws_host = getattr(settings, 'WS_HOST', request.get_host())
        
        # Check for Redis connection
        redis_url = os.environ.get('REDIS_URL', '')
        redis_status = 'Not configured'
        
        if redis_url:
            try:
                import redis
                from urllib.parse import urlparse
                parsed = urlparse(redis_url)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 6379
                password = parsed.password
                
                start_time = time.time()
                r = redis.Redis(
                    host=host, 
                    port=port, 
                    password=password,
                    socket_connect_timeout=2.0
                )
                ping_result = r.ping()
                ping_latency = time.time() - start_time
                
                if ping_result:
                    redis_status = f'Connected (latency: {ping_latency:.3f}s)'
                    
                    # Test pub/sub functionality
                    pubsub = r.pubsub()
                    pubsub.subscribe('test_channel')
                    r.publish('test_channel', 'test')
                    message = pubsub.get_message(timeout=1)
                    if message:
                        redis_status += ', PubSub working'
                    else:
                        redis_status += ', PubSub not responding'
                    pubsub.unsubscribe('test_channel')
            except ImportError:
                redis_status = 'Redis package not installed'
            except Exception as e:
                redis_status = f'Error: {str(e)}'
        
        # Check if Channels is properly installed and configured
        channels_status = 'Not installed'
        try:
            import channels
            channels_version = channels.__version__
            
            # Check for channel layers
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                channels_status = f'Installed (v{channels_version}), channel layer available'
                
                # Test sending a message through the channel layer
                try:
                    from asgiref.sync import async_to_sync
                    group_name = f'test_group_{int(time.time())}'
                    
                    # Need to wrap these calls in async_to_sync
                    async_to_sync(channel_layer.group_add)(group_name, 'test_channel')
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {'type': 'test.message', 'text': 'hello'}
                    )
                    async_to_sync(channel_layer.group_discard)(group_name, 'test_channel')
                    
                    channels_status += ', message sending works'
                except Exception as e:
                    channels_status += f', message sending failed: {str(e)}'
            else:
                channels_status = f'Installed (v{channels_version}), but no channel layer'
        except ImportError:
            channels_status = 'Not installed'
        except Exception as e:
            channels_status = f'Error: {str(e)}'
        
        # Check if port is open for WebSocket connections
        port_status = 'Unknown'
        try:
            port = 443 if ws_protocol == 'wss' else 80
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ws_host, port))
            if result == 0:
                port_status = f'Port {port} is open'
            else:
                port_status = f'Port {port} is closed (code: {result})'
            sock.close()
        except Exception as e:
            port_status = f'Error checking port: {str(e)}'
            
        # CORS check
        cors_status = 'Unknown'
        try:
            cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            cors_allow_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
            if cors_allow_all:
                cors_status = 'All origins allowed'
            elif cors_origins:
                cors_status = f'{len(cors_origins)} origins allowed'
            else:
                cors_status = 'No origins explicitly allowed'
        except Exception as e:
            cors_status = f'Error: {str(e)}'
        
        # Create response data
        response_data = {
            'timestamp': time.time(),
            'server_info': {
                'hostname': hostname,
                'ip_address': ip_address,
                'django_version': settings.get_version(),
                'debug_mode': settings.DEBUG,
            },
            'websocket_config': {
                'protocol': ws_protocol,
                'host': ws_host,
                'websocket_url': f'{ws_protocol}://{ws_host}/ws/',
                'port_status': port_status,
            },
            'cors_setup': {
                'status': cors_status,
                'credentials_allowed': getattr(settings, 'CORS_ALLOW_CREDENTIALS', False),
            },
            'redis_status': redis_status,
            'channels_status': channels_status,
            'client_info': {
                'ip': request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'is_secure': request.is_secure(),
            },
            'request_headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
            'environment_variables': {
                'WS_HOST': os.environ.get('WS_HOST', 'not set'),
                'WS_PROTOCOL': os.environ.get('WS_PROTOCOL', 'not set'),
                'ENABLE_WEBSOCKET': os.environ.get('ENABLE_WEBSOCKET', 'not set'),
                'REDIS_URL': bool(os.environ.get('REDIS_URL', '')),  # Don't show actual URL for security
                'DEBUG': os.environ.get('DEBUG', 'not set'),
            }
        }
        
        return JsonResponse(response_data, json_dumps_params={'indent': 2})
    
    except Exception as e:
        logger.exception("Error in websocket health check")
        return JsonResponse({'error': str(e), 'traceback': str(e.__traceback__)}, status=500)
