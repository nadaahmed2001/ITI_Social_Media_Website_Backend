from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async

class TokenAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using a token.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse the query string to extract the token
        query_string = scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            print("No token provided in the query string.")
            scope['user'] = await self.get_anonymous_user()
        else:
            scope['user'] = await self.get_user_from_token(token)

        return await self.inner(scope, receive, send)

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
            print(f"Authenticated user: {user}")
            return user
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            print(f"Authentication error: {e}")
            return AnonymousUser()

    @database_sync_to_async
    def get_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))