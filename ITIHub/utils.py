from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging
import traceback
import json

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that logs and handles authentication errors more gracefully.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it means the exception was not handled
    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}")
        logger.debug(f"Exception traceback: {traceback.format_exc()}")
        return None

    # Add detailed logging for permission and authentication errors
    if response.status_code == 401:
        logger.error(f"Authentication error: {str(exc)}")
        request = context.get('request')
        if request:
            auth_header = request.META.get('HTTP_AUTHORIZATION', 'Not provided')
            # Only log the first few chars of the auth header, if it exists
            if auth_header and auth_header != 'Not provided':
                masked_header = f"{auth_header[:15]}..." if len(auth_header) > 18 else auth_header
                logger.debug(f"Auth header: {masked_header}")
            logger.debug(f"User: {request.user}")
            
    elif response.status_code == 403:
        logger.error(f"Permission denied: {str(exc)}")
        request = context.get('request')
        if request:
            logger.debug(f"User authenticated: {request.user.is_authenticated}")
            logger.debug(f"User: {request.user}")

    # For module not found errors
    elif isinstance(exc, ModuleNotFoundError):
        logger.error(f"Module not found: {str(exc)}")
        response = Response(
            {"error": f"Configuration error: {str(exc)}"},
            status=500
        )

    # Generic JWT token or authentication errors
    elif hasattr(exc, 'detail') and getattr(exc, 'auth_header', None) is not None:
        logger.error(f"JWT Authentication error: {str(exc)}")
        token_parts = getattr(exc, 'auth_header', '').split(' ')
        if len(token_parts) > 1:
            token = token_parts[1]
            if token:
                logger.debug(f"Token starts with: {token[:10]}...")
                # Additional check to help diagnose WebSocket auth issues
                try:
                    import jwt
                    from django.conf import settings
                    secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                    # Log token details without verification for debugging
                    decoded = jwt.decode(token, options={"verify_signature": False}, algorithms=['HS256'])
                    logger.debug(f"Token payload inspection: user_id={decoded.get('user_id', 'missing')}, exp={decoded.get('exp', 'missing')}")
                except Exception as token_err:
                    logger.debug(f"Could not decode token for inspection: {token_err}")

    # WebSocket connection errors (enhanced for better debugging)
    elif "websocket" in str(exc).lower() or "channel" in str(exc).lower():
        logger.error(f"WebSocket error: {str(exc)}")
        logger.debug(f"WebSocket error traceback: {traceback.format_exc()}")
        
        # Return JSON response for WebSocket errors instead of HTML
        if context.get('request') and ('ws' in context.get('request').path or 'websocket' in context.get('request').path):
            return Response(
                {"error": "WebSocket configuration error", "detail": str(exc)},
                status=500,
                content_type='application/json'
            )
        
    return response
