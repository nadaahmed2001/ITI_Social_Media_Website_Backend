from pathlib import Path
from dotenv import load_dotenv
import os
import sys
from urllib.parse import urlparse
from datetime import timedelta

# Load environment variables early
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Print database URL for debugging (remove in production)
db_url = os.environ.get('DATABASE_URL', '')
print(f"DATABASE_URL is {'set' if db_url else 'NOT SET'}")
if db_url:
    print(f"Database URL first few chars: {db_url[:15]}...")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev-only-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Use environment variables for allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.up.railway.app,.neon.tech').split(',')
# Add healthcheck.railway.app if not already present
if 'healthcheck.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('healthcheck.railway.app')

# Proxy configuration for Railway and other deployment platforms
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# User model configuration
AUTH_USER_MODEL = "users.User"
LOGIN_URL = '/users/student/login/'
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# Authentication configuration
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # "users.backends.CustomAuthBackend",  # If using custom backend
]

# Media configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Application definition
INSTALLED_APPS = [
    "users",  # Custom User Model App (Must be before auth)
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "batches",
    "posts",
    "notifications",
    "projects",
    "core",  # Add core app to installed apps
    'django_extensions',
    "rest_framework", 
    "chat",
    "rest_framework.authtoken",
    'rest_framework_simplejwt',
    'corsheaders',
]

MIDDLEWARE = [ 
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Add whitenoise middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ITIHub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ITIHub.wsgi.application"
ASGI_APPLICATION = 'ITIHub.asgi.application'

# Database Configuration for Neon PostgreSQL
try:
    tmpPostgres = urlparse(os.getenv("DATABASE_URL"))
    print(f"Parsed database: host={tmpPostgres.hostname}, db={tmpPostgres.path.replace('/', '')}")
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': tmpPostgres.path.replace('/', ''),
            'USER': tmpPostgres.username,
            'PASSWORD': tmpPostgres.password,
            'HOST': tmpPostgres.hostname,
            'PORT': tmpPostgres.port or 5432,
            'OPTIONS': {
                'sslmode': 'require',
            }
        }
    }
except Exception as e:
    print(f"Error setting up database: {str(e)}")
    # Fallback to local database if DATABASE_URL parsing fails
    print("WARNING: Using local database configuration!")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'itihub'),
            'USER': os.environ.get('DB_USER', 'itihubuser'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Redis configuration for channels
redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
print(f"Using REDIS_URL: {redis_url[:10]}...")  # Debug info
try:
    # Parse the URL to ensure it's valid and log more details
    import urllib.parse
    parsed_redis = urllib.parse.urlparse(redis_url)
    redis_host = parsed_redis.hostname or "localhost"
    redis_port = parsed_redis.port or 6379
    redis_password = parsed_redis.password or None
    print(f"Redis connection details: {redis_host}:{redis_port}")
    
    # Configure channel layers with the parsed URL and improved reliability settings
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [redis_url],
                # Connection pool settings for better reliability
                "capacity": 1500,
                "expiry": 60,  # Message expiry in seconds
                # Symmetric encryption keys for session security
                "symmetric_encryption_keys": [SECRET_KEY],
                # Retry settings for Redis connections
                "connect_timeout": 20,
                "ping_interval": 60,
                "ping_timeout": 30,
                "reconnect_scheme": [1, 2, 5, 10, 30, 60],  # Backoff scheme in seconds
            },
        },
    }
except Exception as e:
    print(f"Error configuring Redis: {e}")
    # Fallback to in-memory channel layer for development/testing
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

# Static files configuration
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure whitenoise for static files in production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary configuration from environment variables
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'dsaznefnt'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '974213622245136'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'Q1bg9XZJVRD6gTVad7lfPouOow0'),
    'SECURE': True,
    # Optional production settings:
    'FOLDER': os.environ.get('CLOUDINARY_FOLDER', 'itihub_media'),  # Organize uploads in a specific folder
    'RESOURCE_TYPE': os.environ.get('CLOUDINARY_RESOURCE_TYPE', 'auto'),  # 'image', 'video', 'raw', 'auto'
    'OVERWRITE': os.environ.get('CLOUDINARY_OVERWRITE', 'False').lower() == 'true',  # Prevent overwriting files with same name
}

# Tell Django to use Cloudinary for media file storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Optionally, for static files in production:
if not DEBUG:
    STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
    STATIC_ROOT = BASE_DIR / 'staticfiles_collected'  # For collectstatic

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'testiticommunity@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'pzsquwhzxdpxjjzd')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'testiticommunity@gmail.com')

# Site configuration
SITE_NAME = os.environ.get('SITE_NAME', 'ITIHub')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'testiticommunity@gmail.com')
FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:5173')
BACKEND_BASE_URL = os.environ.get('BACKEND_BASE_URL', 'http://localhost:8000')
LOGO_URL = os.environ.get('LOGO_URL', "https://eib.eg/wp-content/uploads/2018/09/iti_logo.5b9a0fd125be-300x133.png")

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 

# Ensure CORS settings allow frontend to communicate with backend
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-csrftoken',
    'x-requested-with',
    'accept',
    'withcredentials',
    'origin',  # Add origin header which is important for CORS
    'access-control-allow-origin'  # Allow this header to be processed
]
# In production, this should be False and specific origins should be set
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'

# Add to ensure JWT works properly in production
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Add exception handler to debug authentication issues
    'EXCEPTION_HANDLER': 'ITIHub.utils.custom_exception_handler',
}

# JWT settings - ensure these are properly configured
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # Set to 24 hours for better debugging
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Set to 30 days for better debugging
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),  # Add this to ensure Bearer prefix is accepted
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',  # Standardize the header name
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Site ID
SITE_ID = 1

# Email change expiration time
EMAIL_CHANGE_EXPIRATION_HOURS = 0.01

# Default app config
default_app_config = 'ITIHub.apps.ITIHubConfig'

# Add this at the end of the file or with other Django settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# WebSocket configuration
WS_PROTOCOL = "wss://" if not DEBUG else "ws://"
WS_HOST = os.environ.get('WS_HOST', ALLOWED_HOSTS[0] if ALLOWED_HOSTS else 'localhost:8000')

# Make these available to templates
WEBSOCKET_URL = f"{WS_PROTOCOL}{WS_HOST}"