from pathlib import Path
from dotenv import load_dotenv
import os
import dj_database_url

# Load environment variables early
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev-only-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Use environment variables for allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.up.railway.app').split(',')

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
    "groups",
    "posts",
    "notifications",
    "projects",
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

# Database Configuration
# Use Railway's DATABASE_URL if available
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '300')),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.environ.get('DB_SSLMODE', 'prefer'),
                'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '10')),
                'client_encoding': 'UTF8',
                'default_transaction_isolation': 'read committed',
                'statement_timeout': int(os.environ.get('DB_STATEMENT_TIMEOUT', '30000')),
                'timezone': 'UTC',
                'application_name': 'itihub',
            },
        }
    }

# Redis configuration for channels (update to use Railway's REDIS_URL if available)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")],
        },
    },
}

# Static files configuration for production
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add whitenoise for static files serving in production
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

# Configure whitenoise
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ROOT_URLCONF = "ITIHub.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "ITIHub.wsgi.application"
# ASGI_APPLICATION = 'ITIHub.asgi.application'

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("127.0.0.1", 6379)],
#         },
#     },
# }
default_app_config = 'ITIHub.apps.ITIHubConfig'



# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'prefer'),  # Changed from 'verify-full' to 'prefer' for development
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '10')),
            'client_encoding': 'UTF8',
            'default_transaction_isolation': 'read committed',
            'statement_timeout': int(os.environ.get('DB_STATEMENT_TIMEOUT', '30000')),
            'timezone': 'UTC',
            'application_name': 'itihub',
        },
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '300')),
        'CONN_HEALTH_CHECKS': True,
        'TEST': {
            'NAME': 'test_itihub',
        },
    }
}

# Add SSL certificate paths if using verify-ca or verify-full in production
if os.environ.get('DB_SSLMODE') in ['verify-ca', 'verify-full']:
    if os.environ.get('DB_SSLROOTCERT'):
        DATABASES['default']['OPTIONS']['sslrootcert'] = os.environ.get('DB_SSLROOTCERT')
    if os.environ.get('DB_SSLCERT'):
        DATABASES['default']['OPTIONS']['sslcert'] = os.environ.get('DB_SSLCERT')
    if os.environ.get('DB_SSLKEY'):
        DATABASES['default']['OPTIONS']['sslkey'] = os.environ.get('DB_SSLKEY')

# Cloudinary configuration from environment variables - this is the active configuration
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

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-csrftoken',
    'x-requested-with',
    'accept',
    'withcredentials'
]
# In production, this should be False and specific origins should be set
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'

# Rest of settings remain unchanged

# =============================================== Cloudinary Configuration ===============================================
# !! Use Environment Variables in production for keys/secrets !!
# CLOUDINARY_STORAGE = {
#     'CLOUD_NAME': 'dsaznefnt', 
#     'API_KEY': '974213622245136',       
#     'API_SECRET': 'Q1bg9XZJVRD6gTVad7lfPouOow0',
#     'SECURE': True, # Use HTTPS
#     
#     #  ============ To be used in production ================================
#     # 'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'YOUR_CLOUD_NAME'), # Replace default with yours or set env var
#     # 'API_KEY': os.environ.get('CLOUDINARY_API_KEY', 'YOUR_API_KEY'),        # Replace default with yours or set env var
#     # 'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'YOUR_API_SECRET'), # Replace default with yours or set env var
#     # 'SECURE': True, # Use HTTPS
#     # Optional settings:
#     # 'FOLDER': 'your_app_media', # Organize uploads in a specific Cloudinary folder
#     # 'RESOURCE_TYPE': 'image', # Default, can be 'video', 'raw', 'auto'
#     # 'OVERWRITE': False, # Prevent overwriting files with same name? Default is usually true.
#     # 'TAGS': ['app_media'], # Add tags to uploaded assets
# }

# --- Default File Storage ---
# Tell Django to use Cloudinary for all media file uploads

# ----- Static Files Storage (Optional - you can also use Cloudinary for static files) -----
# If you want Cloudinary for static files too (requires collectstatic):
# STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
# STATIC_URL = '/static/' # Keep this for local dev, Cloudinary URL used in prod
# STATIC_ROOT = BASE_DIR / 'staticfiles_collected' # For collectstatic

# --------------------------------------- Media Files --------------------------------------
# MEDIA_URL is now effectively handled by Cloudinary, but define for consistency / local fallback if needed
# MEDIA_URL = '/media/' # This might not be used directly if Cloudinary serves all media
# MEDIA_ROOT is no longer needed for cloud storage, Django won't store media locally
# MEDIA_ROOT = BASE_DIR / 'mediafiles' # <-- Can remove or ignore this
# ----------------------------------------- Site ID ----------------------------------------
SITE_ID = 1

# The email configuration is already defined above; removing duplicates
EMAIL_CHANGE_EXPIRATION_HOURS = 0.01