from pathlib import Path
import os
from dotenv import load_dotenv # Optional: if you want settings.py to also load .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Optional: Load .env file if present (Docker Compose also injects env vars)
# DOTENV_PATH = BASE_DIR / '.env'
# if os.path.exists(DOTENV_PATH):
#     load_dotenv(DOTENV_PATH)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'insecure-default-key-for-dev-change-in-env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1' # '1' for True, '0' for False

ALLOWED_HOSTS_STRING = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost 127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STRING.split(' ') if host.strip()]
if not ALLOWED_HOSTS and DEBUG: # Add localhost if ALLOWED_HOSTS is empty and DEBUG is True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    # Local apps
    'appointments.apps.AppointmentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dentaclinic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Add if you have a project-level 'templates' folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dentaclinic.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DATABASE_DB'),
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}
# Ensure 'psycopg2-binary' is in your requirements.txt for PostgreSQL


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # For collectstatic
STATICFILES_DIRS = [
   BASE_DIR / "static", # If you have project-level static files here
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles' # Align with docker-compose volume path /app/mediafiles

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'appointments.CustomUser'

# CSRF Protection Settings
# Add the origins your Nginx server is accessible from on your host machine
CSRF_TRUSTED_ORIGINS = []

# For development, you might be accessing via localhost or 127.0.0.1
# If your Nginx is on host port 8080:
CSRF_TRUSTED_ORIGINS.append('http://localhost:8080')
CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1:8080')

# If your Nginx is on host port 80 (the default):
# CSRF_TRUSTED_ORIGINS.append('http://localhost')
# CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1')

# If, for some reason, the Origin header is literally coming through as 0.0.0.0
# (which is unusual for a browser but might appear in logs due to proxying)
# you could add it, but prefer localhost or 127.0.0.1 for browser access.
CSRF_TRUSTED_ORIGINS.append('http://0.0.0.0:8080') # Add this based on your error message

# In production, you would add your actual domain(s):
# CSRF_TRUSTED_ORIGINS.append('https://yourdomain.com')
# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication', # Consider if BasicAuth is needed for all API access
        # For API access from a separate frontend, you might use TokenAuthentication or JWT
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# Login/Logout URLs
LOGIN_URL = 'login' # Refers to the URL name
LOGIN_REDIRECT_URL = 'home' # Refers to the URL name
LOGOUT_REDIRECT_URL = 'login' # Refers to the URL name

# Optional: For Nginx proxy setups if it's handling HTTPS
# USE_X_FORWARDED_HOST = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
