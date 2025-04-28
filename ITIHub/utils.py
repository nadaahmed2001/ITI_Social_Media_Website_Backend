from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it means the exception was not handled
    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}")
        return None

    # Add detailed logging for permission and authentication errors
    if response.status_code == 401:
        logger.error(f"Authentication error: {str(exc)}")
        request = context.get('request')
        if request:
            logger.debug(f"Auth header: {request.META.get('HTTP_AUTHORIZATION', 'Not provided')}")
            logger.debug(f"User: {request.user}")
            
    elif response.status_code == 403:
        logger.error(f"Permission denied: {str(exc)}")
        request = context.get('request')
        if request:
            logger.debug(f"User authenticated: {request.user.is_authenticated}")
            logger.debug(f"User: {request.user}")

    return response
