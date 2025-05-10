import asyncio
import logging
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

def with_timeout(app):
    """
    Middleware that adds a timeout to ASGI applications.
    If the application takes longer than the specified timeout, 
    it will be cancelled.
    """
    @wraps(app)
    async def timeout_middleware(scope, receive, send):
        try:
            # Default timeout of 15 seconds if not specified in settings
            timeout = getattr(settings, 'ASGI_REQUEST_TIMEOUT', 15)
            if scope['type'] == 'http':
                # HTTP requests can have a different timeout
                timeout = getattr(settings, 'HTTP_REQUEST_TIMEOUT', timeout)
            
            try:
                await asyncio.wait_for(app(scope, receive, send), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Request to {scope.get('path', 'unknown')} timed out after {timeout} seconds")
                if scope['type'] == 'http':
                    # Send a 504 Gateway Timeout response for HTTP requests
                    await send({
                        'type': 'http.response.start',
                        'status': 504,
                        'headers': [
                            [b'content-type', b'text/plain'],
                        ]
                    })
                    await send({
                        'type': 'http.response.body',
                        'body': b'Request timed out',
                    })
                elif scope['type'] == 'websocket':
                    # Close WebSocket connections that time out
                    await send({
                        'type': 'websocket.close',
                        'code': 1001,
                        'reason': 'Request timed out',
                    })
        except Exception as e:
            logger.exception(f"Error in timeout middleware: {e}")
            # Re-raise any other exceptions
            raise
    
    return timeout_middleware
