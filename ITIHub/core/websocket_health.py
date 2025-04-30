from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import os
import socket
import requests
import traceback
from django.conf import settings
from urllib.parse import urlparse
import time
import sys

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
        
        # Check for ASGI configuration
        asgi_setup = {
            'asgi_application': getattr(settings, 'ASGI_APPLICATION', 'Not configured'),
            'daphne_installed': 'daphne' in sys.modules,
        }
        
        # Test WebSocket route availability
        ws_path_test = {
            'paths': ['/ws/', '/ws/chat/'],
            'status': 'Not tested'
        }
        
        # Check for Redis connection with more details
        redis_url = os.environ.get('REDIS_URL', '')
        redis_status = 'Not configured'
        redis_details = {}
        
        if redis_url:
            try:
                import redis
                from urllib.parse import urlparse
                parsed = urlparse(redis_url)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 6379
                password = parsed.password
                db = int(parsed.path.lstrip('/')) if parsed.path and parsed.path != '/' else 0
                
                redis_details = {
                    'host': host,
                    'port': port,
                    'db': db,
                    'has_password': bool(password),
                    'use_ssl': parsed.scheme == 'rediss'
                }
                
                start_time = time.time()
                r = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db,
                    password=password,
                    socket_connect_timeout=3.0,
                    socket_keepalive=True
                )
                ping_result = r.ping()
                ping_latency = time.time() - start_time
                
                if ping_result:
                    redis_status = f'Connected (latency: {ping_latency:.3f}s)'
                    
                    # Test basic operations
                    start = time.time()
                    r.set('websocket_health_check', 'test_value')
                    get_result = r.get('websocket_health_check')
                    r.delete('websocket_health_check')
                    end = time.time()
                    
                    if get_result == b'test_value':
                        redis_details['basic_ops_test'] = 'Success'
                        redis_details['basic_ops_latency'] = f'{(end - start):.3f}s'
                    else:
                        redis_details['basic_ops_test'] = f'Failed: got {get_result}'
                    
                    # Test pub/sub functionality
                    pubsub = r.pubsub()
                    pubsub.subscribe('test_channel')
                    r.publish('test_channel', 'test')
                    message = pubsub.get_message(timeout=2)
                    pubsub_success = False
                    
                    # First message is usually the subscription confirmation, get the actual message
                    if message:
                        message = pubsub.get_message(timeout=2)
                        
                    if message and message.get('data') == b'test':
                        redis_status += ', PubSub working'
                        redis_details['pubsub_test'] = 'Success'
                        pubsub_success = True
                    else:
                        redis_status += ', PubSub not responding'
                        redis_details['pubsub_test'] = f'Failed: got {message}'
                    
                    pubsub.unsubscribe('test_channel')
                    
                    # Check max memory policy which can affect behavior
                    try:
                        info = r.info()
                        redis_details['max_memory_policy'] = info.get('maxmemory_policy', 'unknown')
                        redis_details['redis_version'] = info.get('redis_version', 'unknown')
                        redis_details['connected_clients'] = info.get('connected_clients', 'unknown')
                    except:
                        redis_details['info_fetch_failed'] = True
                        
                    # If pubsub isn't working, try to diagnose further
                    if not pubsub_success:
                        try:
                            # Check if Redis server has keyspace notifications enabled
                            config = r.config_get('notify-keyspace-events')
                            redis_details['notify_keyspace_events'] = config.get('notify-keyspace-events', '')
                        except:
                            redis_details['config_fetch_failed'] = True
            except ImportError:
                redis_status = 'Redis package not installed'
                redis_details['error'] = 'Missing redis package'
            except Exception as e:
                redis_status = f'Error: {str(e)}'
                redis_details['error'] = str(e)
                redis_details['traceback'] = traceback.format_exc()
        
        # Check if Channels is properly installed with detailed diagnostics
        channels_status = 'Not installed'
        channels_details = {}
        try:
            import channels
            channels_version = channels.__version__
            channels_details['version'] = channels_version
            
            # Check for channel layers
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                channels_status = f'Installed (v{channels_version}), channel layer available'
                channels_details['layer_type'] = str(type(channel_layer).__name__)
                
                # Check channel layer backend
                if hasattr(settings, 'CHANNEL_LAYERS'):
                    backend = settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', 'not set')
                    channels_details['backend'] = backend
                    channels_details['config'] = settings.CHANNEL_LAYERS.get('default', {})
                
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
                    channels_details['message_test'] = 'Success'
                except Exception as e:
                    channels_status += f', message sending failed: {str(e)}'
                    channels_details['message_test'] = 'Failed'
                    channels_details['message_error'] = str(e)
            else:
                channels_status = f'Installed (v{channels_version}), but no channel layer'
                channels_details['error'] = 'No channel layer available'
        except ImportError:
            channels_status = 'Not installed'
            channels_details['error'] = 'ImportError - package missing'
        except Exception as e:
            channels_status = f'Error: {str(e)}'
            channels_details['error'] = str(e)
            channels_details['traceback'] = traceback.format_exc()
        
        # Check if port is open for WebSocket connections with more reliable method
        port_status = 'Unknown'
        try:
            # Check both explicit and standard ports
            ports_to_check = []
            
            # Add standard ports
            if ws_protocol == 'wss':
                ports_to_check.append(('443 (standard HTTPS/WSS)', 443))
            else:
                ports_to_check.append(('80 (standard HTTP/WS)', 80))
            
            # Add custom port if specified in host
            if ':' in ws_host:
                host_part, port_part = ws_host.rsplit(':', 1)
                try:
                    custom_port = int(port_part)
                    if custom_port not in [80, 443]:
                        ports_to_check.append((f'{custom_port} (from host config)', custom_port))
                except ValueError:
                    pass
            
            port_results = []
            for port_name, port in ports_to_check:
                try:
                    host_to_check = ws_host.split(':')[0] if ':' in ws_host else ws_host
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    start_time = time.time()
                    result = sock.connect_ex((host_to_check, port))
                    connect_time = time.time() - start_time
                    
                    if result == 0:
                        port_results.append(f'Port {port_name} is open (connected in {connect_time:.3f}s)')
                    else:
                        port_results.append(f'Port {port_name} is closed (code: {result})')
                    sock.close()
                except Exception as e:
                    port_results.append(f'Error checking port {port_name}: {str(e)}')
            
            port_status = "; ".join(port_results)
        except Exception as e:
            port_status = f'Error checking ports: {str(e)}'
            
        # CORS check with more details
        cors_status = 'Unknown'
        cors_details = {}
        try:
            cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            cors_allow_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
            cors_details['CORS_ALLOWED_ORIGINS'] = cors_origins
            cors_details['CORS_ALLOW_ALL_ORIGINS'] = cors_allow_all
            cors_details['CORS_ALLOW_CREDENTIALS'] = getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)
            
            if cors_allow_all:
                cors_status = 'All origins allowed'
            elif cors_origins:
                cors_status = f'{len(cors_origins)} origins allowed'
                # Check if specific client origin is in CORS settings
                client_origin = request.META.get('HTTP_ORIGIN')
                cors_details['client_origin'] = client_origin
                if client_origin:
                    cors_details['client_origin_allowed'] = client_origin in cors_origins
            else:
                cors_status = 'No origins explicitly allowed'
                
            # Check CORS middleware is installed
            from django.conf import settings
            middleware = settings.MIDDLEWARE
            cors_middleware = 'corsheaders.middleware.CorsMiddleware'
            cors_details['middleware_installed'] = cors_middleware in middleware
            if cors_middleware in middleware:
                cors_details['middleware_position'] = middleware.index(cors_middleware)
                if cors_details['middleware_position'] > 0:
                    cors_details['middleware_warning'] = 'CORS middleware should be at or near the top of MIDDLEWARE'
        except Exception as e:
            cors_status = f'Error: {str(e)}'
            cors_details['error'] = str(e)
        
        # Create response data
        response_data = {
            'timestamp': time.time(),
            'server_info': {
                'hostname': hostname,
                'ip_address': ip_address,
                'django_version': settings.get_version(),
                'debug_mode': settings.DEBUG,
                'python_version': sys.version,
            },
            'websocket_config': {
                'protocol': ws_protocol,
                'host': ws_host,
                'websocket_url': f'{ws_protocol}://{ws_host}/ws/',
                'port_status': port_status,
                'asgi_setup': asgi_setup,
            },
            'cors_setup': {
                'status': cors_status,
                'credentials_allowed': getattr(settings, 'CORS_ALLOW_CREDENTIALS', False),
                'details': cors_details,
            },
            'redis_status': redis_status,
            'redis_details': redis_details,
            'channels_status': channels_status,
            'channels_details': channels_details,
            'client_info': {
                'ip': request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                'is_secure': request.is_secure(),
                'origin': request.META.get('HTTP_ORIGIN', 'unknown'),
            },
            'request_headers': {k: v for k, v in request.META.items() if k.startswith('HTTP_')},
            'environment_variables': {
                'WS_HOST': os.environ.get('WS_HOST', 'not set'),
                'WS_PROTOCOL': os.environ.get('WS_PROTOCOL', 'not set'),
                'ENABLE_WEBSOCKET': os.environ.get('ENABLE_WEBSOCKET', 'not set'),
                'REDIS_URL': bool(os.environ.get('REDIS_URL', '')),  # Don't show actual URL for security
                'DEBUG': os.environ.get('DEBUG', 'not set'),
                'RAILWAY_STATIC_URL': os.environ.get('RAILWAY_STATIC_URL', 'not set'),
                'PORT': os.environ.get('PORT', 'not set'),
                'WEBSOCKET_MAX_RETRY': os.environ.get('WEBSOCKET_MAX_RETRY', 'not set'),
            }
        }
        
        return JsonResponse(response_data, json_dumps_params={'indent': 2})
    
    except Exception as e:
        logger.exception("Error in websocket health check")
        error_data = {
            'error': str(e), 
            'traceback': traceback.format_exc()
        }
        return JsonResponse(error_data, status=500, json_dumps_params={'indent': 2})
