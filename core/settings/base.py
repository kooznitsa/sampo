from datetime import timedelta
import os
from pathlib import Path

# BASE

ENV = 'local'
VERSION = 'v0'
APP_NAME = 'sampo'

CORE_DIR = Path(__file__).resolve().parent
BASE_DIR = CORE_DIR.parent.parent

SECRET_KEY = ''
DEBUG = True
ALLOWED_HOSTS = '0.0.0.0,127.0.0.1,localhost'

ROOT_URLCONF = 'core.urls'

WSGI_APPLICATION = 'core.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# INSTALLED APPS

DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

EXTERNAL_APPS = (
    'corsheaders',
    'rest_framework',
    'djmoney',
    'drf_spectacular',
    'drf_standardized_errors',
    'django_filters',
    'rest_framework_simplejwt',
)

CUSTOM_APPS = (
    'restaurant',
    'authentication',
)

INSTALLED_APPS = DJANGO_APPS + EXTERNAL_APPS + CUSTOM_APPS


# MIDDLEWARE

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# PATHS

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_ROOT = (
    BASE_DIR
)
MEDIA_URL = '/media/'


# DATABASES

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': '',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        },
    }
}


# AUTH

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# LOCALIZATION

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = ''

USE_I18N = True

USE_TZ = True


# CORS / CSRF

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = tuple('http{}://{}'.format('' if ENV == 'local' else 's', x) for x in ALLOWED_HOSTS)
BACK_URL = CSRF_TRUSTED_ORIGINS[0]


# LOGGING

LOG_DIR = os.path.join(BASE_DIR, 'logs')

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} - {asctime} - {module}:{lineno:d} - {process:d} - {thread:d} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'error_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'delay': True,
            'filename': LOG_DIR + '/error_logs.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 10,
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'delay': True,
            'filename': LOG_DIR + '/info_logs.log',
            'maxBytes': 1024*1024*5,
            'backupCount': 10,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'error_logger': {
            'handlers': ['error_file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'info_logger': {
            'handlers': ['info_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


# DRF

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_standardized_errors.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'EXCEPTION_HANDLER': 'drf_standardized_errors.handler.exception_handler',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
}


# JWT

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(weeks=4),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# SWAGGER

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sampo API',
    'DESCRIPTION': 'Endpoints for Sampo API',
    'VERSION': 'v1',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'kooznitsa',
        'url': 't.me/kooznitsa',
    },
    'LICENSE': {'name': 'BSD License'},
    'SERVE_PUBLIC': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SCHEMA_PATH_PREFIX': r'/api/v\d+/',
    'SCHEMA_PATH_PREFIX_TRIM': False,
    'CAMELIZE_NAMES': True,
    'ENUM_NAME_OVERRIDES': {
        'ValidationErrorEnum': 'drf_standardized_errors.openapi_serializers.ValidationErrorEnum.choices',
        'ClientErrorEnum': 'drf_standardized_errors.openapi_serializers.ClientErrorEnum.choices',
        'ServerErrorEnum': 'drf_standardized_errors.openapi_serializers.ServerErrorEnum.choices',
        'ErrorCode401Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode401Enum.choices',
        'ErrorCode403Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode403Enum.choices',
        'ErrorCode404Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode404Enum.choices',
        'ErrorCode405Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode405Enum.choices',
        'ErrorCode406Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode406Enum.choices',
        'ErrorCode415Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode415Enum.choices',
        'ErrorCode429Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode429Enum.choices',
        'ErrorCode500Enum': 'drf_standardized_errors.openapi_serializers.ErrorCode500Enum.choices',
    },
}
