import os
import django
import logging
import json
import traceback
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
            # Log connection attempt with details
            client_host = scope.get('client', ['unknown', 0])[0]
            logger.info(f"WebSocket connection attempt from {client_host}")
            
            # Parse the query string to extract the token
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if not token:
                logger.warning(f"No token provided in WebSocket connection from {client_host}")
                # Send a proper close code for authentication failure
                await send({
                    'type': 'websocket.close',
                    'code': 4003,  # Custom close code for no token
                    'reason': 'No authentication token provided',
                })
                return
            
            # Debug token - mask most of it but show structure
            safe_token_prefix = token[:10] if token else 'None'
            token_parts = token.split('.') if token else []
            token_structure = f"{len(token_parts)} parts" if token else "invalid structure"
            logger.debug(f"Token received: starts with {safe_token_prefix}..., structure: {token_structure}")
            
            # Try to authenticate with the token
            scope['user'] = await self.get_user_from_token(token)
            
            # If authentication failed, close the connection
            if scope['user'].is_anonymous:
                logger.warning(f"WebSocket authentication failed with token starting with: {safe_token_prefix}...")
                await send({
                    'type': 'websocket.close',
                    'code': 4001,  # Custom close code for auth failure
                    'reason': 'Authentication failed - Invalid token',
                })
                return
            
            # Authentication successful, continue
            logger.info(f"WebSocket authenticated as: {scope['user'].username} (ID: {scope['user'].id})")
            return await self.inner(scope, receive, send)
        
        except Exception as e:
            # More detailed error logging with traceback
            logger.error(f"WebSocket middleware error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Close connection with error message
            try:
                await send({
                    'type': 'websocket.close',
                    'code': 4500,  # Custom close code for server error
                    'reason': f'Server error: {str(e)[:100]}',
                })
            except Exception as close_err:
                logger.error(f"Error even during connection close: {str(close_err)}")
            return

    @database_sync_to_async
    def get_user_from_token(self, token):
        # IMPORT ALL DJANGO COMPONENTS INSIDE THE ASYNC-SAFE METHOD
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser
        from rest_framework_simplejwt.settings import api_settings
        from django.conf import settings
        import jwt

        try:
            # First, try to decode the token manually to provide better debugging
            try:
                # Get JWT settings
                secret_key = settings.JWT_SECRET_KEY if hasattr(settings, 'JWT_SECRET_KEY') else settings.SECRET_KEY
                algorithm = api_settings.ALGORITHM
                
                # Attempt basic decode without verification first to inspect payload
                decoded_token_unsafe = jwt.decode(
                    token, 
                    options={"verify_signature": False},
                    algorithms=[algorithm]
                )
                
                # Log some info about the token (without sensitive data)
                exp = decoded_token_unsafe.get('exp', 'missing')
                iat = decoded_token_unsafe.get('iat', 'missing')
                user_id = decoded_token_unsafe.get('user_id', 'missing')
                
                logger.debug(f"Token inspection - exp: {exp}, iat: {iat}, has user_id: {'yes' if user_id != 'missing' else 'no'}")
                
                # If we're missing required claims, fail early
                if user_id == 'missing':
                    logger.warning("Token is missing 'user_id' claim")
                    return AnonymousUser()
                
            except Exception as decode_error:
                logger.warning(f"Could not decode token for inspection: {str(decode_error)}")
                # Continue to the standard verification anyway
            
            # Now use SimpleJWT to validate the token properly
            access_token = AccessToken(token)
            User = get_user_model()
            user_id = access_token['user_id']
            logger.debug(f"Found valid token with user_id: {user_id}")
            
            user = User.objects.get(id=user_id)
            logger.info(f"Authenticated user: {user.username} (ID: {user.id})")
            return user
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token validation error: {str(e)}")
            return AnonymousUser()
        except User.DoesNotExist as e:
            logger.warning(f"User not found for token: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error in token authentication: {str(e)}")
            logger.error(traceback.format_exc())
            return AnonymousUser()

    @database_sync_to_async
    def get_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))