import os
import django
import logging
import json
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

logger = logging.getLogger(__name__)

class TokenAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using a token.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        try:
            # Parse the query string to extract the token
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if not token:
                logger.warning("No token provided in WebSocket connection")
                # Send a proper close code for authentication failure
                await send({
                    'type': 'websocket.close',
                    'code': 4003,  # Custom close code for no token
                })
                return
            
            # Try to authenticate with the token
            scope['user'] = await self.get_user_from_token(token)
            
            # If authentication failed, close the connection
            if scope['user'].is_anonymous:
                logger.warning(f"WebSocket authentication failed with token starting with: {token[:10] if token else 'None'}...")
                await send({
                    'type': 'websocket.close',
                    'code': 4001,  # Custom close code for auth failure
                })
                return
            
            # Authentication successful, continue
            logger.debug(f"WebSocket authenticated as: {scope['user'].username}")
            return await self.inner(scope, receive, send)
        
        except Exception as e:
            logger.error(f"WebSocket middleware error: {str(e)}")
            # Close connection with error message
            try:
                await send({
                    'type': 'websocket.close',
                    'code': 4500,  # Custom close code for server error
                })
            except:
                pass  # If even the error handler fails, just let it go
            return

    @database_sync_to_async
    def get_user_from_token(self, token):
        # IMPORT ALL DJANGO COMPONENTS INSIDE THE ASYNC-SAFE METHOD
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser

        try:
            access_token = AccessToken(token)
            User = get_user_model()
            user = User.objects.get(id=access_token['user_id'])
            logger.debug(f"Authenticated user: {user.username} (ID: {user.id})")
            return user
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token validation error: {str(e)}")
            return AnonymousUser()
        except User.DoesNotExist as e:
            logger.warning(f"User not found for token: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error in token authentication: {str(e)}")
            return AnonymousUser()

    @database_sync_to_async
    def get_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))