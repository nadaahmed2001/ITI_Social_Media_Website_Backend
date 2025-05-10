import os
import django
import logging
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async

# Configure logging
logger = logging.getLogger(__name__)

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

class TokenAuthMiddleware:
    """
    Custom middleware that combines JWT and SimpleJWT token authentication for WebSockets
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse the query string to extract the token
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            # Try authenticating with SimpleJWT first, then fallback to regular JWT
            scope['user'] = await self.get_user_from_token(token)
            logger.info(f"WebSocket authenticated: {scope['user'].username if not scope['user'].is_anonymous else 'Anonymous'}")
        else:
            scope['user'] = await self.get_anonymous_user()
            logger.warning("No token provided for WebSocket connection")
        
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Authenticate user from token - tries SimpleJWT first, then falls back to regular JWT
        """
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser
        User = get_user_model()
        
        # First try with SimpleJWT (newer approach)
        try:
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            from rest_framework_simplejwt.tokens import AccessToken
            
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.get(id=user_id)
            logger.info(f"Authenticated via SimpleJWT: {user.username}")
            return user
        except ImportError:
            # SimpleJWT not installed, try regular JWT
            logger.info("SimpleJWT not available, falling back to regular JWT")
            pass
        except (InvalidToken, TokenError) as e:
            logger.warning(f"SimpleJWT authentication failed: {str(e)}")
            # Fall back to regular JWT
            pass
        except User.DoesNotExist as e:
            logger.warning(f"User from SimpleJWT token not found: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error in SimpleJWT authentication: {str(e)}")
            # Fall back to regular JWT
            pass
        
        # Fallback: Try with regular JWT
        try:
            import jwt
            from django.conf import settings
            
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.warning("No user_id found in JWT token")
                return AnonymousUser()
            
            user = User.objects.get(pk=user_id)
            logger.info(f"Authenticated via regular JWT: {user.username}")
            return user
        
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return AnonymousUser()
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return AnonymousUser()
        except User.DoesNotExist:
            logger.warning(f"User from JWT token not found")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Error authenticating JWT token: {str(e)}")
            return AnonymousUser()

    @database_sync_to_async
    def get_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

def TokenAuthMiddlewareStack(inner):
    """
    Wrapper function for the TokenAuthMiddleware that includes the AuthMiddlewareStack
    """
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))