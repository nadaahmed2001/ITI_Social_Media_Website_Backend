import functools
import logging
from django.db import connection, transaction
from django.conf import settings

logger = logging.getLogger(__name__)

def with_query_timeout(func):
    """Decorator to set query timeout for database operations"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Set a statement timeout for this view's operations
        timeout_ms = getattr(settings, 'DB_QUERY_TIMEOUT_MS', 3000)  # Default 3s
        
        # Set timeout at the database level
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(f"SET statement_timeout = {timeout_ms}")
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Query timeout or error in {func.__name__}: {str(e)}")
                    raise
                finally:
                    # Reset the timeout to default
                    cursor.execute("SET statement_timeout = 0")
    
    return wrapper
